"""Evaluate saved observational models from PBF_DATA_ROOT into an isolated directory."""
from __future__ import annotations
import argparse, pickle, time, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from scipy.stats import pearsonr
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from src.pbf.observational import PREDICTORS
from scripts.verify_observational_inputs import load_config, resolve, verify

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument('--config',type=Path,default=Path('configs/observational_paths.toml')); ap.add_argument('--repo-root',type=Path,default=Path.cwd()); ap.add_argument('--output-dir',type=Path,required=True); args=ap.parse_args(); t=time.perf_counter()
    cfg=load_config(args.config.resolve()); root=args.repo_root.resolve()
    if verify(args.config.resolve(),root)!=0: return 2
    data_root=Path(__import__('os').environ['PBF_DATA_ROOT']); train=pd.read_csv(data_root/cfg['inputs']['fold_predictors']); rec=pd.read_csv(data_root/cfg['inputs']['observed_recruitment']); hold=pd.read_csv(root/'data/processed/obs_SVD_LOOCV_raw_1981_2020.csv').rename(columns={'Year':'year'}); models=data_root/'results/observational/training/models'; out=args.output_dir.resolve(); out.mkdir(parents=True,exist_ok=True)
    assert len(train)==1560 and train.Fold.nunique()==40 and train.groupby('Fold').size().eq(39).all() and (train.Train_Year!=train.Left_Out_Year).all()
    assert hold.year.tolist()==list(range(1981,2021)) and list(hold.columns[1:])==list(PREDICTORS)
    rec=rec.set_index('year'); rows=[]
    for fold in range(1,41):
        left=int(train.loc[train.Fold==fold,'Left_Out_Year'].iloc[0]); x=hold.loc[hold.year==left,list(PREDICTORS)].to_numpy(float); y=float(rec.loc[left,'recruitment']);
        with (models/f'gam_fold_{fold:02d}.pkl').open('rb') as f: gam=pickle.load(f)
        with (models/f'rf_fold_{fold:02d}.pkl').open('rb') as f: rf=pickle.load(f)
        rows.append({'Fold':fold,'year':left,'observed_recruitment':y,'observed_log10_recruitment':float(np.log10(y)),'GAM_log10_prediction':float(gam.predict(x)[0]),'RF_log10_prediction':float(rf.predict(x)[0])})
    pred=pd.DataFrame(rows).sort_values('year').reset_index(drop=True)
    for m in ('GAM','RF'):
        pred[f'{m}_predicted_recruitment']=10**pred[f'{m}_log10_prediction']; pred[f'{m}_residual_log10']=pred[f'{m}_log10_prediction']-pred.observed_log10_recruitment
    pred.to_csv(out/'heldout_predictions.csv',index=False); metrics=[]
    for m in ('GAM','RF'):
        y=pred.observed_log10_recruitment.to_numpy(); p=pred[f'{m}_log10_prediction'].to_numpy(); metrics.append({'model':m,'target_scale':'log10(recruitment)','n_years':40,'pearson_r':pearsonr(y,p).statistic,'RMSE':mean_squared_error(y,p)**0.5,'MAE':mean_absolute_error(y,p),'R2':r2_score(y,p)})
    pd.DataFrame(metrics).to_csv(out/'performance_metrics.csv',index=False); print(pd.DataFrame(metrics).to_string(index=False)); print(f'elapsed_seconds={time.perf_counter()-t:.3f} output={out}'); return 0
if __name__=='__main__': raise SystemExit(main())
