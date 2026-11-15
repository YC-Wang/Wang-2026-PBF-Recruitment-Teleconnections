from pathlib import Path
import argparse
import numpy as np, pandas as pd
from scipy.stats import pearsonr, bootstrap
R=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--output-dir', type=Path, default=R/'results/dcpp_table_s3b_revision')
parser.add_argument('--historical-reference', type=Path, default=None)
args=parser.parse_args()
O=args.output_dir; O.mkdir(parents=True,exist_ok=True); years=np.arange(1981,2011); P=['PO_PC1','AO_PC1','PO_PC2','AO_PC2','PO_PC3','AO_PC3']
obs=pd.read_csv(R/'data/processed/obs_SVD_LOOCV_raw_1981_2020.csv').set_index('Year').loc[years]
groups={}
for l in [1,2]: groups[f'Lead {l}']=pd.read_csv(R/f'data/processed/dcpp data/all_member_predictor_obs_aligned_v1/lead{l}/dcpp_lead{l}_ensemble_pooled_loyo_predictors.csv').groupby('verification_year')[P].mean().loc[years]
groups['Lead 3-5']=pd.concat([pd.read_csv(R/f'data/processed/dcpp data/all_member_predictor_obs_aligned_v1/lead{l}/dcpp_lead{l}_ensemble_pooled_loyo_predictors.csv') for l in [3,4,5]],ignore_index=True).groupby('verification_year')[P].mean().loc[years]
def pct(a,b):
 rng=np.random.default_rng(42); rs=[]
 for _ in range(1000):
  ix=rng.integers(0,30,30); rs.append(pearsonr(a[ix],b[ix]).statistic)
 return np.quantile(rs,[.025,.975])
def bca(a,b):
 def f(x,y,axis=-1):
  x=x-x.mean(axis=axis,keepdims=True); y=y-y.mean(axis=axis,keepdims=True); return (x*y).sum(axis=axis)/np.sqrt((x*x).sum(axis=axis)*(y*y).sum(axis=axis))
 z=bootstrap((a,b),f,paired=True,vectorized=True,method='BCa',n_resamples=5000,random_state=20261107).confidence_interval; return z.low,z.high
table=[]; det=[]; orig=[]
for g,d in groups.items():
 for p in P:
  a=obs[p].to_numpy(); b=d[p].to_numpy(); r=pearsonr(a,b).statistic; lo,hi=pct(a,b); blo,bhi=bca(a,b); table.append({'Lead':g,'Predictor':p,'r':r,'CI_low_percentile_1000':lo,'CI_high_percentile_1000':hi,'CI_low_BCa_5000':blo,'CI_high_BCa_5000':bhi,'formatted_original_CI':f'{r:.2f} ({lo:.2f}, {hi:.2f})','formatted_BCa_CI':f'{r:.2f} ({blo:.2f}, {bhi:.2f})','n_years':30})
  ta=a-np.polyval(np.polyfit(years,a,1),years); tb=b-np.polyval(np.polyfit(years,b,1),years); det.append({'Lead':g,'Predictor':p,'detrended_r':pearsonr(ta,tb).statistic})
pd.DataFrame(table).to_csv(O/'table_s3b_revised.csv',index=False); pd.DataFrame(det).to_csv(O/'table_s3b_detrended_correlations.csv',index=False)
if args.historical_reference is not None and args.historical_reference.exists():
 hist=pd.read_csv(args.historical_reference); h=hist.set_index('lead').stack().reset_index(); h.columns=['historical_lead','predictor','historical_formatted']; h['Lead']=h.historical_lead.map({'lead1':'Lead 1','lead2':'Lead 2','Lead3-10':'Lead 3-10'}); h['Predictor']=h.predictor.map({'PO1':'PO_PC1','AO1':'AO_PC1','PO2':'PO_PC2','AO2':'AO_PC2','PO3':'PO_PC3','AO3':'AO_PC3'}); cur=pd.DataFrame(table)[['Lead','Predictor','formatted_original_CI']].rename(columns={'formatted_original_CI':'revised_formatted_CI'}); h.merge(cur,on=['Lead','Predictor'],how='outer').to_csv(O/'table_s3b_original_vs_revised.csv',index=False)
else:
 (O/'table_s3b_original_vs_revised_SKIPPED.md').write_text('Optional historical comparison skipped: no historical reference CSV was supplied. Revised Table S3 statistics were calculated normally; no historical values were fabricated or replaced.',encoding='utf8')
(O/'original_s3b_pipeline_audit.md').write_text('''# Historical Table S3b pipeline audit\n\nThe historical producer used an earlier observational SVD predictor table and DCPP lead files. It averaged the historical lead range by verification year, used 30 annual pairs, and applied a paired percentile bootstrap with 1,000 resamples and seed 42. Historical source files are external and are not distributed here.\n\nThe revised pipeline uses the current observational-basis-aligned predictors, ensemble-pooled LOYO climatologies, annual ensemble means for Leads 1–2, and pooled 351-member annual means for Leads 3–5.\n''',encoding='utf8')
(O/'table_s3b_methodology.md').write_text('''Revised correlations use 30 annual verification pairs. The historical percentile-bootstrap CI is retained for comparability; BCa intervals with 5,000 paired year resamples are also reported. No predictor rescaling, sign adjustment, SVD refitting, or DCPP preprocessing was performed.\n''',encoding='utf8'); print(pd.DataFrame(table).query("Lead=='Lead 3-5'")[['Predictor','r','formatted_original_CI','formatted_BCa_CI']].to_string(index=False))
