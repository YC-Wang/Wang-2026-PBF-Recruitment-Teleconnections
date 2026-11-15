"""Descriptive comparison of input recruitment and Experiment B prediction variability."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import pearsonr, spearmanr

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"results/observational/recruitment_uncertainty/cv_lognormal_2026"
OUT=BASE/"propagation_diagnostics"
YEARS=np.arange(1981,2021)

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    sim_path=ROOT/"data/raw/Y_sim_500_samples.csv"
    sim=pd.read_csv(sim_path)
    sim_ids=sim.Sim_ID.to_numpy(int)
    sim_years=np.array([int(c) for c in sim.columns[1:]])
    yrec=sim.iloc[:,1:].to_numpy(float)
    files=sorted((BASE/"checkpoints").glob("sample_*.npz"))
    ids=np.array([int(f.stem.split("_")[1]) for f in files])
    valid_ids=np.arange(1,501)
    if not np.array_equal(sim_ids,valid_ids): raise ValueError("Recruitment realization IDs are not exactly 1-500")
    if not np.array_equal(ids,valid_ids): raise ValueError("Prediction checkpoint IDs are not exactly 1-500")
    if not np.array_equal(sim_years,YEARS): raise ValueError("Recruitment years do not equal 1981-2020")
    pred_gam=np.empty((500,40)); pred_rf=np.empty((500,40))
    for i,f in enumerate(files):
        z=np.load(f)
        if z["gam"].shape!=(40,) or z["rf"].shape!=(40,): raise ValueError(f"Invalid checkpoint shape: {f.name}")
        pred_gam[i]=z["gam"]; pred_rf[i]=z["rf"]
    if not np.isfinite(yrec).all() or not np.isfinite(pred_gam).all() or not np.isfinite(pred_rf).all(): raise ValueError("Non-finite realization values")
    if sim_ids.tolist()!=ids.tolist(): raise ValueError("Recruitment and prediction realization IDs are mismatched")
    # All values here are log10 recruitment; no transformation is applied.
    rec_sd=yrec.std(axis=0,ddof=1); gam_sd=pred_gam.std(axis=0,ddof=1); rf_sd=pred_rf.std(axis=0,ddof=1)
    rec_w=np.percentile(yrec,97.5,axis=0)-np.percentile(yrec,2.5,axis=0)
    gam_w=np.percentile(pred_gam,97.5,axis=0)-np.percentile(pred_gam,2.5,axis=0)
    rf_w=np.percentile(pred_rf,97.5,axis=0)-np.percentile(pred_rf,2.5,axis=0)
    eps=1e-12; ratio_g=np.divide(gam_sd,rec_sd,out=np.full(40,np.nan),where=rec_sd>eps); ratio_r=np.divide(rf_sd,rec_sd,out=np.full(40,np.nan),where=rec_sd>eps)
    diag=pd.DataFrame({"year":YEARS,"sigma_recruitment":rec_sd,"sigma_prediction_GAM":gam_sd,"sigma_prediction_RF":rf_sd,"ratio_GAM":ratio_g,"ratio_RF":ratio_r,"width95_recruitment":rec_w,"width95_GAM":gam_w,"width95_RF":rf_w})
    diag.to_csv(OUT/"annual_uncertainty_diagnostics.csv",index=False)
    corr=[]
    for m,x in (("GAM",gam_sd),("RF",rf_sd)):
        corr.append((m,"prediction_sd",pearsonr(rec_sd,x).statistic,spearmanr(rec_sd,x).statistic))
    summary=[]
    for m,col,rat in (("GAM","sigma_prediction_GAM",ratio_g),("RF","sigma_prediction_RF",ratio_r)):
        q=diag.loc[diag[col].idxmax()]; lo=diag.loc[diag[col].idxmin()]
        summary.append(f"- {m}: mean SD {diag[col].mean():.4f}, median SD {diag[col].median():.4f}; largest {int(q.year)} ({q[col]:.4f}), smallest {int(lo.year)} ({lo[col]:.4f}); mean ratio {np.nanmean(rat):.4f}, median ratio {np.nanmedian(rat):.4f}.")
    corr_text="\n".join(f"- {m}: Pearson r={p:.3f}; Spearman rho={s:.3f}." for m,_,p,s in corr)
    top_g=diag.loc[diag.ratio_GAM.idxmax()]; top_r=diag.loc[diag.ratio_RF.idxmax()]
    report=f'''# Recruitment uncertainty propagation diagnostics\n\n## Inventory and validation\n\n- Recruitment input: `data/raw/Y_sim_500_samples.csv`; SHA-256 `{sha256(sim_path)}`.\n- Recruitment realizations: 500 IDs, each covering 1981–2020 exactly once.\n- Prediction checkpoints: 500 IDs, each containing 40 GAM and 40 RF held-out LOOCV predictions.\n- Prediction records: 20,000 per model (40,000 model-level values).\n- Recruitment realizations and checkpoint predictions are on the log10 recruitment scale. The convenience file `predictions_500.csv` stores back-transformed recruitment units and was not used for these SD calculations.\n- No missing, duplicate, or mismatched sample-year records were found.\n- Checkpoint generation uses each sampled response vector consistently across folds and excludes the held-out year from each fold's training response.\n\n## Diagnostics\n\nThe ratios are descriptive `prediction SD / recruitment SD` comparisons, not causal amplification coefficients.\n\n{chr(10).join(summary)}\n\nAcross years, correlations between input recruitment SD and propagated prediction SD were:\n{corr_text}\n\nLargest ratio years were GAM {int(top_g.year)} ({top_g.ratio_GAM:.4f}) and RF {int(top_r.year)} ({top_r.ratio_RF:.4f}).\n\n## Interpretation and limitation\n\nPrediction variability varies among years and differs between GAM-SVD and RF-SVD. The annual associations quantify co-variation across the 40 years, but do not show that uncertainty in year t's recruitment causes uncertainty in its year-t prediction. The held-out prediction for year t is trained on the other 39 sampled recruitment values; the sampled recruitment value for year t is excluded from that fit. Therefore, these are descriptive sensitivity diagnostics. The independent annual sampling in the supplied assessment realizations may also omit temporal covariance.\n\nThese diagnostics add a complementary view beyond Figure S2.1 and Table S2.1 by comparing input-response variability with propagated held-out prediction variability, while preserving the distinction from model-only and residual prediction intervals.\n'''
    (OUT/"uncertainty_propagation_summary.md").write_text(report,encoding="utf-8")
    inventory=f'''# Data inventory\n\n- `Y_sim_500_samples.csv`: 500 complete log10 recruitment vectors, columns 1981-2020, IDs 1-500.\n- `checkpoints/sample_0001.npz` through `sample_0500.npz`: one atomic checkpoint per realization, each with `gam` and `rf` arrays of length 40. These are held-out LOOCV predictions on the log10 scale.\n- `predictions_500.csv`: long-form output with 20,000 rows and both GAM/RF columns on the original recruitment scale; retained unchanged and not used for log-scale diagnostics.\n- `heldout_predictions.csv`: original baseline held-out GAM/RF predictions used for the primary Experiment B validation.\n\nValidation completed: 500 matching IDs, 40 matching years, finite values, no duplicate sample-year records, and complete GAM/RF prediction vectors. The workflow uses fold-specific predictors and excludes each held-out year's sampled recruitment from its corresponding training fold.\n'''
    (OUT/"data_inventory.md").write_text(inventory,encoding="utf-8")
    plt.style.use("seaborn-v0_8-whitegrid"); fig,ax=plt.subplots(figsize=(11,5.5)); ax.plot(YEARS,rec_sd,"k-o",ms=3,label="Recruitment realizations"); ax.plot(YEARS,gam_sd,"#2459A6",lw=2,label="GAM-SVD predictions"); ax.plot(YEARS,rf_sd,"#C9343A",lw=2,label="RF-SVD predictions"); ax.set(xlabel="Year",ylabel="SD (log10 recruitment)",title="Annual input and propagated prediction variability"); ax.legend(); fig.tight_layout(); fig.savefig(OUT/"annual_uncertainty_comparison.png",dpi=300); fig.savefig(OUT/"annual_uncertainty_comparison.pdf"); plt.close(fig)
    fig,ax=plt.subplots(figsize=(11,4.8)); ax.axhline(1,color="0.25",ls="--",lw=1); ax.plot(YEARS,ratio_g,"#2459A6",lw=2,label="GAM-SVD"); ax.plot(YEARS,ratio_r,"#C9343A",lw=2,label="RF-SVD"); ax.set(xlabel="Year",ylabel="Prediction-to-recruitment SD ratio",title="Relative prediction variability"); ax.legend(); fig.tight_layout(); fig.savefig(OUT/"prediction_recruitment_sd_ratio.png",dpi=300); fig.savefig(OUT/"prediction_recruitment_sd_ratio.pdf"); plt.close(fig)
    print(json.dumps({"rows":len(diag),"realizations":500,"output":str(OUT)},indent=2))
if __name__=="__main__": main()
