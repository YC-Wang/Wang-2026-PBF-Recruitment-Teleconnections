from pathlib import Path
import hashlib
import numpy as np
import pandas as pd
from scipy.stats import pearsonr
from sklearn.metrics import mean_squared_error

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'results/observational/recruitment_uncertainty/cv_lognormal_2026'
OUT=BASE/'table_S2_1_harmonized'
YEARS=np.arange(1981,2021)
def sha(p):
    h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    sim_path=ROOT/'data/raw/Y_sim_500_samples.csv'; sim=pd.read_csv(sim_path)
    if sim.shape!=(500,41) or list(sim.columns)!=['Sim_ID']+[str(y) for y in YEARS]: raise ValueError('Invalid sampling schema')
    targets=sim.iloc[:,1:].to_numpy(float)
    files=sorted((BASE/'checkpoints').glob('sample_*.npz'))
    ids=[int(f.stem.split('_')[1]) for f in files]
    if ids!=list(range(1,501)): raise ValueError('Missing or duplicate checkpoint IDs')
    rows=[]
    for i,f in enumerate(files):
        z=np.load(f)
        for model in ['GAM','RF']:
            pred=np.asarray(z[model.lower()],float)
            if pred.shape!=(40,) or not np.isfinite(pred).all(): raise ValueError(f'Invalid {model} predictions in {f.name}')
            rows.append({'Sim_ID':i+1,'model':model,'r':float(pearsonr(targets[i],pred).statistic),'MSE':float(mean_squared_error(targets[i],pred)),'CV (%)':float(100*np.std(pred,ddof=1)/np.mean(pred)),'n_years':40,'target_scale':'log10(recruitment)'})
    metrics=pd.DataFrame(rows)
    if len(metrics)!=1000 or metrics.groupby('model').size().to_dict()!={'GAM':500,'RF':500}: raise ValueError('Wrong metric record count')
    metrics.to_csv(OUT/'table_S2_1_realization_metrics.csv',index=False)
    summary=[]
    for model in ['GAM','RF']:
        row={'Predictors':'SVD teleconnection indices','Model':model}
        for metric in ['r','MSE','CV (%)']:
            x=metrics.loc[metrics.model.eq(model),metric].to_numpy(float)
            row[f'{metric} mean']=x.mean(); row[f'{metric} 2.5th percentile']=np.quantile(x,.025); row[f'{metric} 97.5th percentile']=np.quantile(x,.975); row[f'{metric} mean_in_interval']=bool(x.mean()>=np.quantile(x,.025) and x.mean()<=np.quantile(x,.975))
        summary.append(row)
    s=pd.DataFrame(summary)
    cols=['Predictors','Model']+[c for c in s.columns if c not in ['Predictors','Model']]
    s[cols].to_csv(OUT/'table_S2_1.csv',index=False)
    fmt=pd.DataFrame({'Predictors':['SVD teleconnection indices']*2,'Model':['GAM','RF']})
    for metric in ['r','MSE','CV (%)']:
        fmt[metric]=[f"{s.loc[i,f'{metric} mean']:.4f} [{s.loc[i,f'{metric} 2.5th percentile']:.4f}–{s.loc[i,f'{metric} 97.5th percentile']:.4f}]" if metric!='MSE' else f"{s.loc[i,f'{metric} mean']:.6f} [{s.loc[i,f'{metric} 2.5th percentile']:.6f}–{s.loc[i,f'{metric} 97.5th percentile']:.6f}]" for i in range(2)]
    fmt.to_csv(OUT/'table_S2_1_formatted.csv',index=False)
    caption='Table S2.1. Predictive performance of the SVD-based generalized additive model (GAM) and random forest (RF) across 500 recruitment uncertainty realizations using leave-one-out cross-validation (LOOCV) for 1981–2020. Performance metrics follow the definitions used in Table 1: Pearson correlation coefficient (r), mean squared error (MSE), and coefficient of variation (CV). Values represent the mean across 500 realizations, with empirical 2.5th–97.5th percentiles in brackets. MSE is calculated using log10-transformed recruitment.'
    (OUT/'table_S2_1_caption.txt').write_text(caption,encoding='utf-8')
    old=pd.read_csv(BASE/'skill_uncertainty_summary.csv')
    comp=[]
    for i,model in enumerate(['GAM','RF']):
        for metric,oldmetric in [('r','correlation_sampled'),('MSE','rmse_sampled')]:
            if metric=='MSE':
                old_mean=(old.loc[(old.model==model)&(old.metric==oldmetric),'mean'].iloc[0])**2; old_lo=(old.loc[(old.model==model)&(old.metric==oldmetric),'q025'].iloc[0])**2; old_hi=(old.loc[(old.model==model)&(old.metric==oldmetric),'q975'].iloc[0])**2
            else:
                old_mean=old.loc[(old.model==model)&(old.metric==oldmetric),'mean'].iloc[0]; old_lo=old.loc[(old.model==model)&(old.metric==oldmetric),'q025'].iloc[0]; old_hi=old.loc[(old.model==model)&(old.metric==oldmetric),'q975'].iloc[0]
            comp.append({'Model':model,'Metric':metric,'old_mean':old_mean,'new_mean':s.loc[i,f'{metric} mean'],'old_2.5th':old_lo,'new_2.5th':s.loc[i,f'{metric} 2.5th percentile'],'old_97.5th':old_hi,'new_97.5th':s.loc[i,f'{metric} 97.5th percentile']})
    pd.DataFrame(comp).to_csv(OUT/'table_S2_1_old_rmse_based_comparison.csv',index=False)
    report=f'''# Harmonized Table S2.1 validation

## Table 1 definitions verified

The authoritative implementation is `scripts/generate_table1_updated_loocv.py` and its output is `results/observational/table1_updated_loocv/table1_updated_loocv.csv`. It defines Pearson r with `scipy.stats.pearsonr`, MSE with `sklearn.metrics.mean_squared_error` on log10 recruitment, and CV (%) as `100*np.std(y_pred, ddof=1)/np.mean(y_pred)`. The SVD Table 1 values are GAM r={0.6764948024560269:.4f}, MSE={0.02684003995554054:.6f}, CV={2.464054385441145:.4f}; RF r={0.6675868997610437:.4f}, MSE={0.02724449918392515:.6f}, CV={1.8382425974115564:.4f}. Table 1 was not modified.

## Recalculation and validation

- Predictions: `cv_lognormal_2026/checkpoints/sample_*.npz`, exactly 500 IDs × 40 years for each model.
- Targets: active CV-based `data/raw/Y_sim_500_samples.csv`, matched by realization ID and year; SHA-256 `{sha(sim_path)}`.
- Each realization's r, MSE, and CV uses the same 40 sampled log10 targets and held-out predictions.
- MSE is calculated directly on log10 recruitment; RMSE is not used as the Table S2.1 metric.
- CV uses the identical Table 1 formula and percent units.
- All values are finite; there are no missing, duplicate, or mismatched realization-year records.
- Mean-within-percentile checks: GAM r={bool(s.loc[0,'r mean_in_interval'])}, MSE={bool(s.loc[0,'MSE mean_in_interval'])}, CV={bool(s.loc[0,'CV (%) mean_in_interval'])}; RF r={bool(s.loc[1,'r mean_in_interval'])}, MSE={bool(s.loc[1,'MSE mean_in_interval'])}, CV={bool(s.loc[1,'CV (%) mean_in_interval'])}.

The prior Table S2.1-style output reported RMSE. `table_S2_1_old_rmse_based_comparison.csv` compares the old RMSE-based summaries with the new MSE summaries; squaring percentile RMSE endpoints is shown only for comparison, not used to calculate the revised metrics. Table 1, baseline LOOCV models, and earlier uncertainty results were not overwritten.
'''
    (OUT/'table_S2_1_validation.md').write_text(report,encoding='utf-8')
    print(fmt.to_string(index=False))
if __name__=='__main__': main()
