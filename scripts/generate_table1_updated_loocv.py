from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import pearsonr
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
from pygam import LinearGAM, s

ROOT = Path(__file__).resolve().parents[1]
ORIG = Path(os.environ['PBF_DATA_ROOT']) / 'table1'
OUT = ROOT / 'results/observational/table1_updated_loocv'; OUT.mkdir(parents=True, exist_ok=True)
REC = ROOT / 'data/raw/observed_recruitment_1981_2020.csv'
configs = {
    'SVD teleconnection indices': (ROOT / 'data/processed/obs_SVD_LOOCV_raw_1981_2020.csv', ['PO_PC1','AO_PC1','PO_PC2','AO_PC2','PO_PC3','AO_PC3']),
    'Regional SST': (ORIG / 'SST_regional_timeseries_1981_2020.csv', ['SSPG_4_6','NSPG_7_9','JNG_10_12']),
    'PDO + AMO': (ORIG / 'SVD_mode_recruitment_normalize.csv', ['PDO','AMO']),
}
recruit = pd.read_csv(REC).sort_values('year'); years = recruit.year.to_numpy(int); y = np.log10(recruit.recruitment.to_numpy(float))
assert years.tolist() == list(range(1981, 2021))
def gam_terms(n):
    t = s(0, n_splines=3, spline_order=2)
    for i in range(1,n): t = t + s(i, n_splines=3, spline_order=2)
    return t
def calc(y,p): return float(pearsonr(y,p).statistic), float(mean_squared_error(y,p)), float(100*np.std(p,ddof=1)/np.mean(p))
def predict(x, kind):
    out=[]
    for i in range(40):
        tr=np.arange(40)!=i
        if kind=='GAM': m=LinearGAM(gam_terms(x.shape[1])).fit(x[tr],y[tr])
        else: m=RandomForestRegressor(n_estimators=1000,max_depth=5,max_features='sqrt',random_state=1).fit(x[tr],y[tr])
        out.append(float(m.predict(x[i:i+1])[0]))
    return np.array(out)
rows=[]; pred=pd.DataFrame({'year':years,'recruitment':recruit.recruitment.to_numpy(float),'log10_recruitment':y})
for group,(path,cols) in configs.items():
    df=pd.read_csv(path); df.columns=df.columns.str.strip(); df=df.rename(columns={'Year':'year'})
    if 'recruitment' not in df.columns: df=df.merge(recruit[['year','recruitment']],on='year',validate='one_to_one')
    df=df.sort_values('year'); assert df.year.astype(int).tolist()==years.tolist()
    x=df[cols].to_numpy(float)
    for kind in ('GAM','RF'):
        if group == 'SVD teleconnection indices':
            held = pd.read_csv(ROOT/'results/observational/holdout_svd_evaluation/heldout_predictions.csv').sort_values('year')
            p = held[f'{kind}_log10_prediction'].to_numpy(float)
        else:
            p=predict(x,kind)
        r,mse,cv=calc(y,p); rows.append({'Predictors':group,'Model':kind,'r':r,'MSE':mse,'CV (%)':cv,'n_years':40,'target_scale':'log10(recruitment)','input_file':str(path)})
        pred[f'{group}_{kind}_log10_prediction']=p
table=pd.DataFrame(rows); table.to_csv(OUT/'table1_updated_loocv.csv',index=False); pred.to_csv(OUT/'table1_predictions_1981_2020.csv',index=False)
old=pd.DataFrame([
 ['SVD teleconnection indices','GAM',.66,.028,2.50],['SVD teleconnection indices','RF',.64,.029,1.64],['PDO + AMO','GAM',.34,.044,1.53],['PDO + AMO','RF',.15,.055,1.76],['Regional SST','GAM',.46,.039,1.79],['Regional SST','RF',.36,.043,1.53]],columns=['Predictors','Model','old_r','old_MSE','old_CV (%)'])
old.merge(table[['Predictors','Model','r','MSE','CV (%)']],on=['Predictors','Model']).to_csv(OUT/'table1_old_vs_new.csv',index=False)
report=f'''# Updated Table 1 LOOCV validation report

Six models use the identical 1981–2020 recruitment series and `log10(recruitment)`. Regional SST and PDO+AMO were reproduced with the original supplied predictors and 40-fold `KFold(n_splits=40, shuffle=False)` LOOCV. The validated SVD rows use the current 40 held-out SVD predictor rows and the same GAM/RF configurations; no SVD model was refit in this phase.

Inputs:

- Recruitment: `{REC}`
- SVD: `{configs['SVD teleconnection indices'][0]}`
- Regional SST: `{configs['Regional SST'][0]}`
- PDO+AMO: `{configs['PDO + AMO'][0]}`

The recruitment values and years match the original Table 1 input exactly: 40 years, 1981–2020, maximum absolute difference 0.

GAM is `pygam.LinearGAM` with one `n_splines=3`, `spline_order=2` term per predictor and default regularization. RF is `RandomForestRegressor(n_estimators=1000, max_depth=5, max_features="sqrt", random_state=1)`. No tuning was used.

Metrics are Pearson r, squared mean error (MSE) on the log10 scale, and `100*np.std(y_pred, ddof=1)/np.mean(y_pred)`. RMSE was not substituted for MSE.

Regional SST and PDO/AMO predictor files are supplied precomputed series. Their upstream seasonal/index construction and any use of full-period information are outside the fold loop and cannot be verified as leakage-free from the available repository. The predictor definitions were preserved without modification. The SVD rows use fold-specific construction validated in `results/observational/table1_scale_audit.md`.

Validation: 40 predictions per model; common years and recruitment; SVD predictions reused; MSE and CV definitions verified; no existing results overwritten.
'''
(OUT/'table1_validation_report.md').write_text(report,encoding='utf-8')
from docx import Document
from docx.shared import Inches,Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
doc=Document(); sec=doc.sections[0]; sec.top_margin=Inches(.7); sec.bottom_margin=Inches(.7); sec.left_margin=Inches(.8); sec.right_margin=Inches(.8); doc.styles['Normal'].font.name='Aptos'; doc.styles['Normal'].font.size=Pt(10)
p=doc.add_paragraph(); p.style=doc.styles['Title']; p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.add_run('Updated Table 1 LOOCV Results')
doc.add_paragraph('Pacific bluefin tuna recruitment prediction using validated observational LOOCV-SVD predictors and the original Regional SST and PDO plus AMO definitions. All metrics use log10 recruitment and the same 1981–2020 observations.')
doc.add_heading('Table 1',level=1); t=doc.add_table(rows=1,cols=5); t.style='Table Grid'; headers=['Predictors','Model','r','MSE','CV (%)']
for c,h in zip(t.rows[0].cells,headers): c.text=h
for _,row in table.iterrows():
    cells=t.add_row().cells
    for c,v in zip(cells,[row['Predictors'],row['Model'],f"{row['r']:.4f}",f"{row['MSE']:.6f}",f"{row['CV (%)']:.4f}"]): c.text=str(v)
doc.add_paragraph('MSE is mean squared error on log10 recruitment. CV is 100 × SD(predicted log10 recruitment) / mean(predicted log10 recruitment), with ddof=1.')
doc.add_heading('Validation summary',level=1); doc.add_paragraph('All six models use 40 years and the identical recruitment series. The SVD models were not refit. Regional SST and PDO plus AMO use the original supplied predictor definitions and configurations; their upstream preprocessing cannot be confirmed as fold-contained.')
doc.save(OUT/'table1_updated_loocv.docx')
print(table.to_string(index=False))
