"""Experiment B: propagate assessment recruitment-response uncertainty through observational LOOCV.

The supplied Y_sim_500_samples.csv is already on the log10 scale, as documented by
data/code/EDF_500resampling_GAM_RF_.ipynb.  This workflow therefore fits sampled
log10 responses directly and back-transforms predictions to recruitment units.
"""
from __future__ import annotations
import argparse, hashlib, json, os, pickle, platform, shutil, sys, tempfile, time
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path
import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy.stats import pearsonr
from sklearn.metrics import mean_squared_error

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
PRED = ["PO_PC1", "AO_PC1", "PO_PC2", "AO_PC2", "PO_PC3", "AO_PC3"]
YEARS = np.arange(1981, 2021)
OUT = ROOT / "results/observational/recruitment_uncertainty"

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""): h.update(b)
    return h.hexdigest()

def atomic_save_npz(path, **arrays):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.stem + ".", suffix=".npz", dir=path.parent)
    os.close(fd)
    try:
        np.savez_compressed(tmp, **arrays); os.replace(tmp, path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def load_inputs():
    fold = pd.read_csv(ROOT / "data/raw/all_40folds_39years_PO_AO_PCs_1981_2020.csv")
    hold = pd.read_csv(ROOT / "data/processed/obs_SVD_LOOCV_raw_1981_2020.csv").rename(columns={"Year":"year"})
    rec = pd.read_csv(ROOT / "data/raw/observed_recruitment_1981_2020.csv")
    sim_path = ROOT / "data/raw/Y_sim_500_samples.csv"
    sim = pd.read_csv(sim_path)
    if list(sim.columns[1:]) != [str(y) for y in YEARS]: raise ValueError("Simulation columns do not align to 1981-2020")
    if len(sim) != 500 or sim.Sim_ID.nunique() != 500: raise ValueError("Expected 500 unique simulations")
    ys = sim.iloc[:, 1:].to_numpy(float)
    if not np.isfinite(ys).all(): raise ValueError("Simulation values are not finite")
    if (ys <= 0).any(): raise ValueError("Sampled log10 recruitment must be positive in this supplied file")
    if fold.Fold.nunique() != 40 or not fold.groupby("Fold").size().eq(39).all(): raise ValueError("Invalid fold layout")
    fold_map = {}
    x_train, x_test, left_years = [], [], []
    for f, g in fold.groupby("Fold", sort=True):
        g = g.sort_values("Train_Year"); left = int(g.Left_Out_Year.iloc[0])
        if len(g) != 39 or left in set(g.Train_Year): raise ValueError(f"Invalid fold {f}")
        x_train.append(g[PRED].to_numpy(float)); x_test.append(hold.loc[hold.year.eq(left), PRED].to_numpy(float)[0])
        left_years.append(left); fold_map[int(f)] = g.Train_Year.to_numpy(int)
    if list(left_years) != list(YEARS): raise ValueError("Fold years do not cover 1981-2020 in order")
    obs = rec.set_index("year").loc[YEARS, "recruitment"].to_numpy(float)
    if (obs <= 0).any(): raise ValueError("Observed recruitment must be positive")
    return x_train, np.asarray(x_test), np.asarray(left_years), fold_map, ys, obs, sim_path

def fit_predict(X, y, xt, method):
    from src.pbf.observational import gam_terms, RF_CONFIG
    if method == "GAM":
        from pygam import LinearGAM
        return float(LinearGAM(gam_terms()).fit(X, y).predict(xt.reshape(1, -1))[0])
    from sklearn.ensemble import RandomForestRegressor
    cfg = dict(RF_CONFIG); cfg["n_jobs"] = 1
    return float(RandomForestRegressor(**cfg).fit(X, y).predict(xt.reshape(1, -1))[0])

def run_one(sample_id, ysim, xtr, xte, years, fold_map, checkpoint):
    p = checkpoint / f"sample_{sample_id:04d}.npz"
    if p.exists():
        z = np.load(p)
        if set(z.files) == {"gam", "rf"} and z["gam"].shape == (40,) and z["rf"].shape == (40,) and np.isfinite(z["gam"]).all() and np.isfinite(z["rf"]).all():
            return sample_id, z["gam"], z["rf"]
        p.unlink()
    gam, rf = np.empty(40), np.empty(40)
    year_to_pos = {int(y): i for i, y in enumerate(years)}
    for i, train_years in enumerate(fold_map.values()):
        idx = np.array([year_to_pos[int(y)] for y in train_years])
        gam[i] = fit_predict(xtr[i], ysim[idx], xte[i], "GAM")
        rf[i] = fit_predict(xtr[i], ysim[idx], xte[i], "RF")
    atomic_save_npz(p, gam=gam, rf=rf)
    return sample_id, gam, rf

def baseline_validation(xtr, xte, years, fold_map, obs):
    model_dir = ROOT / "results/observational/training/models"
    saved = {m: [] for m in ("GAM", "RF")}; repro = {m: [] for m in ("GAM", "RF")}
    for i, y in enumerate(years, 1):
        for m in saved:
            with open(model_dir / f"{m.lower()}_fold_{i:02d}.pkl", "rb") as f: model = pickle.load(f)
            saved[m].append(float(model.predict(xte[i-1].reshape(1,-1))[0]))
            repro[m].append(fit_predict(xtr[i-1], np.log10(obs[[j for j in range(40) if j != i-1]]), xte[i-1], m))
    rows=[]
    for m in saved:
        d=np.asarray(repro[m])-np.asarray(saved[m]); rows.append({"model":m,"max_abs":np.max(np.abs(d)),"mean_abs":np.mean(np.abs(d)),"rmse":np.sqrt(np.mean(d*d)),"mismatched_folds":int(np.sum(np.abs(d)>1e-10))})
    out=OUT/"baseline_validation"; out.mkdir(parents=True,exist_ok=True); pd.DataFrame(rows).to_csv(out/"reproduction_metrics.csv",index=False)
    (out/"validation_report.md").write_text("# Baseline validation\n\nRe-fitted each saved fold with the original observed log10 responses and raw held-out SVD predictors. Tolerance for mismatch count: 1e-10 log10 units. GAM uses direct `.fit()` with default pyGAM lam; RF uses the repository RF configuration.\n\n"+pd.DataFrame(rows).to_string(index=False),encoding="utf-8")
    if any(r["mismatched_folds"] for r in rows): raise RuntimeError("Baseline reproduction failed; full experiment not started")
    return {m:np.asarray(saved[m]) for m in saved}

def summarize(pred, baseline, obs, sim_y):
    rows=[]
    for m in ("GAM","RF"):
        a=pred[m]; raw=10**a; b=10**baseline[m]
        for i,y in enumerate(YEARS): rows.append({"model":m,"year":int(y),"baseline_prediction":b[i],"ensemble_mean":raw[:,i].mean(),"ensemble_median":np.median(raw[:,i]),"std":raw[:,i].std(ddof=1),"variance":raw[:,i].var(ddof=1),"q025":np.percentile(raw[:,i],2.5),"q975":np.percentile(raw[:,i],97.5),"baseline_minus_median":b[i]-np.median(raw[:,i])})
    pd.DataFrame(rows).to_csv(OUT/"annual_uncertainty_summary.csv",index=False)
    metrics=[]
    for s in range(pred["GAM"].shape[0]):
        for m in ("GAM","RF"):
            p=pred[m][s]; metrics.append({"Sim_ID":s+1,"model":m,"correlation_sampled":pearsonr(sim_y[s],p).statistic,"rmse_sampled":np.sqrt(mean_squared_error(sim_y[s],p)),"correlation_original":pearsonr(np.log10(obs),p).statistic,"rmse_original":np.sqrt(mean_squared_error(np.log10(obs),p))})
    pd.DataFrame(metrics).to_csv(OUT/"skill_metrics_500.csv",index=False)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--n-samples",type=int,default=500); ap.add_argument("--n-workers",type=int,default=1); ap.add_argument("--seed",type=int,default=42); ap.add_argument("--resume",action="store_true"); ap.add_argument("--skip-baseline",action="store_true"); ap.add_argument("--smoke",action="store_true"); ap.add_argument("--output-root",default=None,help="isolated output root for benchmarks or alternate runs"); args=ap.parse_args()
    global OUT
    if args.output_root: OUT = Path(args.output_root).resolve()
    OUT.mkdir(parents=True,exist_ok=True); (OUT/"checkpoints").mkdir(exist_ok=True)
    xtr,xte,years,fold_map,sim_y,obs,sim_path=load_inputs(); n=min(args.n_samples,len(sim_y)); n=5 if args.smoke else n
    baseline=baseline_validation(xtr,xte,years,fold_map,obs) if not args.skip_baseline else {m:np.zeros(40) for m in ("GAM","RF")}
    t=time.time(); results=Parallel(n_jobs=args.n_workers,prefer="processes")([delayed(run_one)(i+1,sim_y[i],xtr,xte,years,fold_map,OUT/"checkpoints") for i in range(n)])
    gam=np.vstack([r[1] for r in results]); rf=np.vstack([r[2] for r in results]); pred={"GAM":gam,"RF":rf}
    pd.DataFrame([{**{"Sim_ID":i+1,"year":int(years[j])},**{m:float(10**pred[m][i,j]) for m in ("GAM","RF")}} for i in range(n) for j in range(40)]).to_csv(OUT/f"predictions_{n}.csv",index=False)
    if n==500: summarize(pred,baseline,obs,sim_y[:n])
    packages={}
    for package in ("numpy", "pandas", "scipy", "scikit-learn", "pygam", "joblib"):
        try: packages[package]=version(package)
        except PackageNotFoundError: packages[package]="not installed"
    meta={"n_samples":n,"n_workers":args.n_workers,"seed":args.seed,"runtime_seconds":time.time()-t,"response_scale":"log10","independent_annual_normal_sampling":True,"input_sha256":sha256(sim_path),"python":sys.version,"platform":platform.platform(),"packages":packages}
    (OUT/"run_metadata.json").write_text(json.dumps(meta,indent=2),encoding="utf-8")
    print(json.dumps({"samples":n,"runtime_seconds":meta["runtime_seconds"],"output":str(OUT)},indent=2))
if __name__ == "__main__": main()
