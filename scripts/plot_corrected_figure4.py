from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import t

root = Path(__file__).resolve().parents[1]
out = root / 'results/observational/figure4_corrected_loocv'
d = pd.read_csv(out / 'annual_predictions_uncertainty.csv')
x = d.observed_log10_recruitment.to_numpy()
fig, ax = plt.subplots(figsize=(12, 6))
for method, color, marker in (('GAM','#0072B2','o'),('RF','#D55E00','s')):
    y = d[f'{method}_log10_prediction'].to_numpy(); n=len(x)
    slope, intercept = np.polyfit(x, y, 1); xx=np.linspace(x.min(),x.max(),100); fit=intercept+slope*xx
    resid=y-(intercept+slope*x); s_err=np.sqrt(np.sum(resid**2)/(n-2)); xbar=x.mean(); sxx=np.sum((x-xbar)**2)
    band=t.ppf(.975,n-2)*s_err*np.sqrt(1/n+(xx-xbar)**2/sxx)
    ax.scatter(x,y,color=color,marker=marker,alpha=.8,label=method)
    ax.plot(xx,fit,color=color,lw=2,label=f'{method} regression')
    ax.fill_between(xx,fit-band,fit+band,color=color,alpha=.14,label=f'{method} regression 95% CI')
ax.plot([x.min(),x.max()],[x.min(),x.max()],'k--',lw=1,label='1:1')
ax.set(xlabel='Observed log10 recruitment',ylabel='Predicted log10 recruitment',title='Figure 4: corrected observational LOOCV')
ax.legend(fontsize=9,ncol=2); fig.tight_layout()
for ext in ('png','svg','pdf'): fig.savefig(out/f'fig4_diagnostic.{ext}',dpi=220 if ext=='png' else None)
plt.close(fig)
