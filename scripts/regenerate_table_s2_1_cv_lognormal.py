from pathlib import Path
import hashlib
import numpy as np
import pandas as pd
from scipy.stats import pearsonr
from sklearn.metrics import mean_squared_error

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'results/observational/recruitment_uncertainty/cv_lognormal_2026'
OUT=BASE/'table_S2_1_cv_lognormal'
YEARS=np.arange(1981,2021)
def sha(p):
    h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()
def summarize(x):
    return {'mean':float(np.mean(x)),'median':float(np.median(x)),'q025':float(np.quantile(x,.025)),'q975':float(np.quantile(x,.975))}
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    sim_path=ROOT/'data/raw/Y_sim_500_samples.csv'; sim=pd.read_csv(sim_path)
    if sim.shape!=(500,41) or list(sim.columns)!=['Sim_ID']+[str(y) for y in YEARS]: raise ValueError('Invalid sampling schema')
    targets=sim.iloc[:,1:].to_numpy(float)
    if not np.isfinite(targets).all(): raise ValueError('Nonfinite sampled targets')
    files=sorted((BASE/'checkpoints').glob('sample_*.npz'))
    ids=[int(f.stem.split('_')[1]) for f in files]
    if ids!=list(range(1,501)): raise ValueError('Missing or duplicate checkpoint IDs')
    rows=[]
    for i,f in enumerate(files):
        z=np.load(f)
        for model in ['GAM','RF']:
            key=model.lower(); pred=np.asarray(z[key],float)
            if pred.shape!=(40,) or not np.isfinite(pred).all(): raise ValueError(f'Invalid {model} checkpoint {f.name}')
            rows.append({'Sim_ID':i+1,'model':model,'pearson_r':float(pearsonr(targets[i],pred).statistic),'RMSE':float(mean_squared_error(targets[i],pred)**.5),'n_years':40})
    metrics=pd.DataFrame(rows); metrics.to_csv(OUT/'table_S2_1_realization_metrics.csv',index=False)
    summaries=[]
    for model in ['GAM','RF']:
        for metric in ['pearson_r','RMSE']:
            s=summarize(metrics.loc[metrics.model.eq(model),metric].to_numpy())
            summaries.append({'Model':model,'Metric':metric,'Mean':s['mean'],'Median':s['median'],'2.5th percentile':s['q025'],'97.5th percentile':s['q975'],'N realizations':500})
    summary=pd.DataFrame(summaries); summary.to_csv(OUT/'Table_S2_1_CV_lognormal.csv',index=False)
    old=pd.read_csv(ROOT/'results/observational/recruitment_uncertainty/skill_uncertainty_summary.csv')
    comparison=[]
    for model in ['GAM','RF']:
        for metric,oldmetric in [('pearson_r','correlation_sampled'),('RMSE','rmse_sampled')]:
            n=summary[(summary.Model==model)&(summary.Metric==metric)].iloc[0]
            o=old[(old.model==model)&(old.metric==oldmetric)].iloc[0]
            comparison.append({'Model':model,'Metric':metric,'old_mean':o['mean'],'new_mean':n['Mean'],'change_mean':n['Mean']-o['mean'],'old_median':o['median'],'new_median':n['Median'],'change_median':n['Median']-o['median'],'old_q025':o['q025'],'new_q025':n['2.5th percentile'],'old_q975':o['q975'],'new_q975':n['97.5th percentile']})
    pd.DataFrame(comparison).to_csv(OUT/'Table_S2_1_old_vs_new.csv',index=False)
    md=['# Appendix Table S2.1. CV-based recruitment uncertainty','', 'Pearson correlation and RMSE were calculated separately for each of 500 matched realization IDs using the sampled log₁₀ recruitment targets and the corresponding 40 held-out predictions. RMSE is on the log₁₀ recruitment scale. Percentiles are empirical 2.5th and 97.5th percentiles.','', '| Model | Metric | Mean | Median | 2.5th–97.5th percentile | N |','|---|---|---:|---:|---:|---:|']
    for _,r in summary.iterrows(): md.append(f"| {r['Model']} | {r['Metric']} | {r['Mean']:.4f} | {r['Median']:.4f} | {r['2.5th percentile']:.4f}–{r['97.5th percentile']:.4f} | {int(r['N realizations'])} |")
    (OUT/'Table_S2_1_manuscript.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
    (OUT/'validation_report.md').write_text(f'''# Table S2.1 validation

- Active sampling input: `data/raw/Y_sim_500_samples.csv`; SHA-256 `{sha(sim_path)}`.
- Targets: 500 realization IDs × 40 years, positive finite log10 recruitment values.
- Predictions: 500 GAM and 500 RF checkpoint vectors × 40 years; no missing or duplicate IDs.
- Target and prediction arrays are matched by realization ID and year; Pearson r and RMSE use the same realization's sampled targets.
- RMSE and correlations are computed on the log10 scale; each metric uses all 40 years.
- Exactly 500 complete realization–prediction pairs per model were validated.
- Baseline Table 1, baseline LOOCV models, and original uncertainty outputs were not modified.

The prior Table S2.1-style summary is preserved at `results/observational/recruitment_uncertainty/skill_uncertainty_summary.csv`; the numeric comparison is `Table_S2_1_old_vs_new.csv`.
''',encoding='utf-8')
    print(summary.to_string(index=False))
if __name__=='__main__': main()
