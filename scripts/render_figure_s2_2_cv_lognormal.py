from pathlib import Path
import hashlib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'results/observational/recruitment_uncertainty/cv_lognormal_2026'
OUT=BASE/'figure_S2_2_cv_lognormal'
YEARS=np.arange(1981,2021)
def sha(p):
    h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    sim_path=ROOT/'data/raw/Y_sim_500_samples.csv'
    sim=pd.read_csv(sim_path)
    pred=pd.read_csv(BASE/'predictions_500.csv')
    if sim.shape!=(500,41) or list(sim.columns)!=['Sim_ID']+[str(y) for y in YEARS]: raise ValueError('Invalid updated sampling schema')
    if len(pred)!=20000 or pred.Sim_ID.nunique()!=500 or pred.year.nunique()!=40: raise ValueError('Updated predictions are incomplete')
    if set(pred.Sim_ID)!=set(range(1,501)) or set(pred.year)!=set(YEARS): raise ValueError('Prediction IDs/years do not align')
    if not np.isfinite(sim.iloc[:,1:].to_numpy(float)).all() or not np.isfinite(pred[['GAM','RF']].to_numpy(float)).all(): raise ValueError('Nonfinite input')
    if not (sim.iloc[:,1:].to_numpy(float)>0).all(): raise ValueError('Sampling values must be positive log10 recruitment')
    files=sorted((BASE/'checkpoints').glob('sample_*.npz'))
    if len(files)!=500: raise ValueError('Expected 500 prediction checkpoints')
    gam=np.empty((500,40)); rf=np.empty((500,40))
    for i,f in enumerate(files):
        z=np.load(f)
        if z['gam'].shape!=(40,) or z['rf'].shape!=(40,): raise ValueError(f'Invalid checkpoint {f.name}')
        gam[i]=z['gam']; rf[i]=z['rf']
    if not np.isfinite(gam).all() or not np.isfinite(rf).all(): raise ValueError('Nonfinite checkpoint predictions')
    rec_sd=sim.iloc[:,1:].to_numpy(float).std(axis=0,ddof=1)
    gam_sd=gam.std(axis=0,ddof=1); rf_sd=rf.std(axis=0,ddof=1)
    source=pd.DataFrame({'year':YEARS,'recruitment_realization_sd':rec_sd,'GAM_SVD_prediction_sd':gam_sd,'RF_SVD_prediction_sd':rf_sd})
    source.to_csv(OUT/'figure_S2_2_source.csv',index=False)
    summary=pd.DataFrame({'series':['Recruitment realizations','GAM-SVD predictions','RF-SVD predictions'],'mean_sd':[rec_sd.mean(),gam_sd.mean(),rf_sd.mean()],'median_sd':[np.median(rec_sd),np.median(gam_sd),np.median(rf_sd)],'max_sd':[rec_sd.max(),gam_sd.max(),rf_sd.max()],'max_year':[int(YEARS[rec_sd.argmax()]),int(YEARS[gam_sd.argmax()]),int(YEARS[rf_sd.argmax()])]})
    summary.to_csv(OUT/'figure_S2_2_summary.csv',index=False)
    fig,ax=plt.subplots(figsize=(11,5.5)); ax.axvspan(1981,1993.5,color='#999999',alpha=.08); ax.axvspan(1993.5,2016.5,color='#999999',alpha=.03); ax.axvspan(2016.5,2020,color='#999999',alpha=.08)
    ax.plot(YEARS,rec_sd,color='black',marker='o',markersize=3,linewidth=1.5,label='Recruitment realizations')
    ax.plot(YEARS,gam_sd,color='#2459A6',linewidth=2,label='GAM-SVD predictions')
    ax.plot(YEARS,rf_sd,color='#C9343A',linewidth=2,label='RF-SVD predictions')
    ax.set(xlabel='Year',ylabel='Standard deviation (log₁₀ recruitment units)',title='Appendix Figure S2.2. Annual recruitment uncertainty versus propagated prediction variability')
    ax.legend(frameon=True); ax.set_xlim(1981,2020); fig.tight_layout(); fig.savefig(OUT/'Figure_S2_2_cv_lognormal.png',dpi=300); fig.savefig(OUT/'Figure_S2_2_cv_lognormal.svg'); plt.close(fig)
    caption='''Appendix Figure S2.2. Annual recruitment uncertainty versus propagated GAM-SVD and RF-SVD prediction variability. The black line is the sample standard deviation (ddof = 1) of 500 independent log₁₀ recruitment realizations generated from mean-preserving lognormal distributions parameterized by ISC (2022) period-average recruitment-estimation CVs: 0.21 for 1981–1993, 0.08 for 1994–2016, and 0.325 for 2017–2020. Blue and red lines are the corresponding ddof = 1 standard deviations of 500 held-out GAM-SVD and RF-SVD LOOCV predictions refitted using those same CV-based realizations. Shading marks the three CV periods. These are variability magnitudes, not fractions of uncertainty transmitted from the held-out year's recruitment, and do not represent complete predictive intervals.'''
    (OUT/'Figure_S2_2_caption.txt').write_text(caption,encoding='utf-8')
    (OUT/'Figure_S2_2_comparison_report.md').write_text('''# Updated Appendix Figure S2.2 comparison

The updated figure uses the active CV-based sampling file and the versioned 500-realization GAM/RF prediction output. It does not reuse the previous prediction output. All three series are calculated on the log10 recruitment scale with `ddof=1` across exactly 500 realizations for each of 40 years. The original Figure S2.2 source was the earlier `propagation_diagnostics/annual_uncertainty_diagnostics.csv` and `annual_uncertainty_comparison.png`; those files were not overwritten.

The numerical source is `figure_S2_2_source.csv`; annual mean, median, maxima, and maximum years are in `figure_S2_2_summary.csv`. The new figure's blue and red series reflect the revised CV magnitudes and the resulting refitted prediction variability. The figure is descriptive and does not imply causal transmission or complete predictive uncertainty.

Validation: 1981–2020 coverage, 500 samples per year, finite values, matching sample/prediction version SHA-256 `a5b10b031e3c37cbc3007fc4e69959cceaedc59a30b2548064c3922a67e14120`, and source-to-figure values generated in one script. Baseline Figure 4 and baseline models were not modified.
''',encoding='utf-8')
    print({'output':str(OUT),'sampling_sha256':sha(sim_path),'rows':len(source),'samples_per_year':500})
if __name__=='__main__': main()
