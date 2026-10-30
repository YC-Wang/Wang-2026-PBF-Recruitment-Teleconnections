"""Render Figure R2: recruitment-assessment uncertainty on the log10 scale."""
from pathlib import Path
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"results/observational/recruitment_uncertainty"
FIG=OUT/"figures"
YEARS=np.arange(1981,2021)

def main():
    data_root = Path(os.environ.get("PBF_DATA_ROOT", ROOT))
    obs=pd.read_csv(data_root/"data/raw/observed_recruitment_1981_2020.csv").sort_values("year")
    base=pd.read_csv(ROOT/"results/observational/holdout_svd_evaluation/heldout_predictions.csv").sort_values("year")
    pred=pd.read_csv(OUT/"predictions_500.csv")
    if len(obs)!=40 or obs.year.to_numpy().tolist()!=YEARS.tolist(): raise ValueError("Observed years are not 1981-2020")
    if len(base)!=40 or base.year.to_numpy().tolist()!=YEARS.tolist(): raise ValueError("Baseline years are not 1981-2020")
    if len(pred)!=20000 or pred[["GAM","RF"]].isna().any().any(): raise ValueError("Expected 20,000 sample-year rows containing both model predictions")
    if pred.Sim_ID.nunique()!=500 or pred.year.nunique()!=40: raise ValueError("Invalid sample/year layout")
    if (obs.recruitment<=0).any() or (pred[["GAM","RF"]]<=0).any().any(): raise ValueError("All plotted recruitment values must be positive")
    obslog=np.log10(obs.recruitment.to_numpy(float))
    base_gam=base.GAM_log10_prediction.to_numpy(float); base_rf=base.RF_log10_prediction.to_numpy(float)
    summaries={}
    for m in ("GAM","RF"):
        wide=pred.pivot(index="Sim_ID",columns="year",values=m).loc[:,YEARS]
        logwide=np.log10(wide.to_numpy(float))
        summaries[m]={"median":np.median(logwide,axis=0),"lo":np.percentile(logwide,2.5,axis=0),"hi":np.percentile(logwide,97.5,axis=0)}
        if not np.all((summaries[m]["lo"]<=summaries[m]["median"])&(summaries[m]["median"]<=summaries[m]["hi"])): raise ValueError(f"Interval does not contain median for {m}")
    if not np.allclose(np.log10(10**base_gam),base_gam) or not np.allclose(np.log10(10**base_rf),base_rf): raise ValueError("Baseline transform check failed")
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":11,"axes.labelsize":13,"axes.titlesize":15,"xtick.labelsize":10,"ytick.labelsize":10})
    fig,axes=plt.subplots(1,2,figsize=(12,4.6),sharey=True)
    colors={"GAM":"#2459A6","RF":"#C9343A"}
    for ax,m,basep,panel in zip(axes,("GAM","RF"),(base_gam,base_rf),("(a) GAM-SVD","(b) RF-SVD")):
        s=summaries[m]; c=colors[m]
        ax.fill_between(YEARS,s["lo"],s["hi"],color=c,alpha=.20,linewidth=0,label="Propagated recruitment uncertainty")
        ax.plot(YEARS,obslog,color="black",linewidth=1.7,marker="o",markersize=3.3,label="Observed recruitment",zorder=4)
        ax.plot(YEARS,basep,color=c,linestyle="--",linewidth=1.35,marker="s",markersize=3.0,label="Original LOOCV prediction",zorder=3)
        ax.plot(YEARS,s["median"],color=c,linestyle="-",linewidth=1.9,label="Median prediction (500 refits)",zorder=3)
        ax.set_title(panel,loc="left",fontweight="bold",pad=10)
        ax.set_xlim(1981,2020); ax.set_ylim(6.0,8.0); ax.set_yticks([6.0,6.5,7.0,7.5,8.0]); ax.set_xticks([1981,1991,2001,2011,2020]); ax.grid(axis="both",linestyle=":",alpha=.45)
        ax.spines[["top","right"]].set_visible(True)
    axes[0].set_ylabel("log10 recruitment"); axes[0].set_xlabel("Year"); axes[1].set_xlabel("Year")
    handles,labels=axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc="lower center",ncol=2,frameon=False,bbox_to_anchor=(.5,-.015),columnspacing=1.5,handlelength=2.5)
    fig.subplots_adjust(left=.07,right=.985,bottom=.20,top=.86,wspace=.08)
    FIG.mkdir(parents=True,exist_ok=True)
    fig.savefig(FIG/"recruitment_uncertainty_timeseries_log10.png",dpi=300,bbox_inches="tight")
    fig.savefig(FIG/"recruitment_uncertainty_timeseries_log10.pdf",bbox_inches="tight")
    caption=("Figure R2. Recruitment uncertainty propagated through the observational LOOCV modelling framework for (a) GAM-SVD and (b) RF-SVD. Black lines indicate stock-assessment recruitment estimates, dashed colored lines indicate the original LOOCV predictions, and solid colored lines indicate the median predictions obtained from 500 refitted models using assessment-derived recruitment realizations. Shaded regions represent the 2.5th–97.5th percentile ranges of the refitted predictions, quantifying the sensitivity of predictions to uncertainty in the recruitment estimates used for training. All values are shown on the log10 recruitment scale. These intervals do not represent complete predictive uncertainty or the model/data-error prediction intervals shown in Figure 4.")
    (FIG/"recruitment_uncertainty_timeseries_log10_caption.txt").write_text(caption,encoding="utf-8")
    print({"output_png":str(FIG/"recruitment_uncertainty_timeseries_log10.png"),"output_pdf":str(FIG/"recruitment_uncertainty_timeseries_log10.pdf"),"y_limits":[6.0,8.0],"n_predictions":len(pred)})
if __name__=="__main__": main()
