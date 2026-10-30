"""Five-realization smoke verifier using the fixed snapshot input and saved models."""
from __future__ import annotations
import argparse, os, pickle, time, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from scipy.stats import pearsonr
from sklearn.metrics import mean_squared_error
from src.pbf.observational import PREDICTORS, fit_gam, fit_rf
from scripts.verify_observational_inputs import load_config, verify

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument('--config',type=Path,default=Path('configs/observational_paths.toml')); ap.add_argument('--repo-root',type=Path,default=Path.cwd()); ap.add_argument('--output-dir',type=Path,required=True); ap.add_argument('--n-samples',type=int,default=5); args=ap.parse_args(); t=time.perf_counter(); cfg=load_config(args.config.resolve()); root=args.repo_root.resolve()
    if args.n_samples!=5: raise SystemExit('This portable verifier is restricted to exactly five saved realizations.')
    if verify(args.config.resolve(),root)!=0: return 2
    data_root=Path(os.environ['PBF_DATA_ROOT']); fold_data=pd.read_csv(data_root/cfg['inputs']['fold_predictors']); rec=pd.read_csv(data_root/cfg['inputs']['observed_recruitment']).sort_values('year'); sim=pd.read_csv(data_root/cfg['inputs']['recruitment_realizations_500']); hold=pd.read_csv(root/'data/processed/obs_SVD_LOOCV_raw_1981_2020.csv').rename(columns={'Year':'year'}).sort_values('year'); models=data_root/'results/observational/training/models'; out=args.output_dir.resolve(); out.mkdir(parents=True,exist_ok=True)
    assert sim.shape[0]>=5 and sim.shape[1]>=41; years=rec.year.to_numpy(); responses=sim.iloc[:5,1:41].to_numpy(float); rows=[]
    for sid,response in enumerate(responses,1):
        gam_pred=[]; rf_pred=[]
        for fold in range(1,41):
            tr=fold_data[fold_data.Fold==fold].sort_values('Train_Year'); left=int(tr.Left_Out_Year.iloc[0]); xtr=tr[list(PREDICTORS)].to_numpy(float); ytr=response[[int(np.where(years==y)[0][0]) for y in tr.Train_Year]]; xt=hold.loc[hold.year==left,list(PREDICTORS)].to_numpy(float)
            with (models/f'gam_fold_{fold:02d}.pkl').open('rb') as f: gam_ref=pickle.load(f)
            with (models/f'rf_fold_{fold:02d}.pkl').open('rb') as f: rf_ref=pickle.load(f)
            gam,_=fit_gam(xtr,ytr); rf,_=fit_rf(xtr,ytr); gam_pred.append(float(gam.predict(xt)[0])); rf_pred.append(float(rf.predict(xt)[0]))
        for model,pred in [('GAM',np.array(gam_pred)),('RF',np.array(rf_pred))]: rows.append({'Sim_ID':sid,'model':model,'correlation_sampled':pearsonr(response,pred).statistic,'rmse_sampled':mean_squared_error(response,pred)**0.5})
    result=pd.DataFrame(rows); result.to_csv(out/'smoke_metrics.csv',index=False); print(result.to_string(index=False)); print(f'elapsed_seconds={time.perf_counter()-t:.3f} output={out}'); return 0
if __name__=='__main__': raise SystemExit(main())
