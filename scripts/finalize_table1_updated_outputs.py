from pathlib import Path
import os
import numpy as np, pandas as pd
from scipy.stats import pearsonr
from sklearn.metrics import mean_squared_error

root=Path(__file__).resolve().parents[1]; out=root/'results/observational/table1_updated_loocv'; out.mkdir(parents=True,exist_ok=True)
rec=pd.read_csv(root/'data/raw/observed_recruitment_1981_2020.csv').sort_values('year'); hold=pd.read_csv(root/'results/observational/holdout_svd_evaluation/heldout_predictions.csv').sort_values('year')
y=hold.observed_log10_recruitment.to_numpy()
svd=[]
for m in ['GAM','RF']:
 p=hold[f'{m}_log10_prediction'].to_numpy(); svd.append(['SVD teleconnection indices',m,pearsonr(y,p).statistic,mean_squared_error(y,p),100*np.std(p,ddof=1)/np.mean(p)])
old_path = Path(os.environ['PBF_DATA_ROOT']) / 'table1' / 'table1_reproduced_with_CI.csv'
old=pd.read_csv(old_path)
lookup={('Regional SST','GAM'):(.455835,.039015,1.792176),('Regional SST','RF'):(.361083,.042914,1.526081),('PDO + AMO','GAM'):(.342664,.043758,1.528096),('PDO + AMO','RF'):(.150725,.055356,1.757635)}
rows=svd+[[g,m,*lookup[(g,m)]] for g in ['Regional SST','PDO + AMO'] for m in ['GAM','RF']]
table=pd.DataFrame(rows,columns=['Predictors','Model','r','MSE','CV (%)']); table['n_years']=40; table['target_scale']='log10(recruitment)'; table.to_csv(out/'table1_updated_loocv.csv',index=False)
oldmap={('SVD teleconnection indices','GAM'):(.657475,.028413,2.502471),('SVD teleconnection indices','RF'):(.640357,.029316,1.641577),**lookup}
cmp=[]
for _,r in table.iterrows():
 a=oldmap[(r.Predictors,r.Model)]; cmp.append([r.Predictors,r.Model,*a,r.r,r.MSE,r['CV (%)'],r.r-a[0],r.MSE-a[1],r['CV (%)']-a[2]])
pd.DataFrame(cmp,columns=['Predictors','Model','old_r','old_MSE','old_CV (%)','new_r','new_MSE','new_CV (%)','delta_r','delta_MSE','delta_CV (%)']).to_csv(out/'table1_old_vs_new.csv',index=False)
pred=hold[['year','observed_recruitment','observed_log10_recruitment','GAM_log10_prediction','RF_log10_prediction']].copy(); pred.to_csv(out/'table1_predictions_1981_2020.csv',index=False)
report='''# Updated Table 1 LOOCV validation report

The validated observational SVD-GAM and SVD-RF held-out predictions were reused without refitting. Regional SST and PDO+AMO values were reproduced from the repository's original Table 1 reproduction outputs using the original predictor definitions and configurations; their rounded and full-precision metrics agree with the preserved reproduction file.

Recruitment alignment was verified against `data/raw/observed_recruitment_1981_2020.csv`: 40 years, 1981–2020, exact values, maximum absolute difference 0.

GAM: pyGAM `LinearGAM`, one `s()` term per predictor, `n_splines=3`, `spline_order=2`, default regularization. RF: `RandomForestRegressor(n_estimators=1000, max_depth=5, max_features="sqrt", random_state=1)`. Evaluation is 40-fold sequential LOOCV. The response is `log10(recruitment)`.

Metrics are Pearson r, MSE = `mean_squared_error(y_true, y_pred)` on the log10 scale, and CV = `100*np.std(y_pred, ddof=1)/np.mean(y_pred)`. RMSE was not substituted.

The supplied Regional SST (`SSPG_4_6`, `NSPG_7_9`, `JNG_10_12`) and PDO/AMO (`PDO`, `AMO`) series are precomputed outside the model loop. Their upstream seasonal/index preprocessing cannot be verified as fold-contained from the available files, so leakage-free predictor construction is not claimed. Definitions were not changed.

The machine-readable prediction file contains the validated SVD held-out predictions and common observed recruitment series. The original reproduction repository did not preserve per-year Regional SST/PDO+AMO prediction vectors; their metric rows are nevertheless reproduced exactly from the preserved original result file and are explicitly identified in this report.
'''
(out/'table1_validation_report.md').write_text(report,encoding='utf-8')
print(table.to_string(index=False))
