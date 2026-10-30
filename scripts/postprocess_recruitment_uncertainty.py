"""Postprocess completed Experiment B checkpoints without refitting models."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import pearsonr
from sklearn.metrics import mean_squared_error

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"results/observational/recruitment_uncertainty"; YEARS=np.arange(1981,2021)

def plot_annotated_skill(metrics, figdir):
    """Plot sampled-response skill distributions with compact empirical summaries."""
    expected=np.arange(1,501)
    if set(metrics.model)!= {"GAM","RF"}: raise ValueError("Skill metrics must contain GAM and RF")
    for model in ("GAM","RF"):
        ids=np.sort(metrics.loc[metrics.model==model,"Sim_ID"].unique())
        if len(ids)!=500 or not np.array_equal(ids,expected): raise ValueError(f"{model} does not contain realization IDs 1-500")
    if not np.array_equal(np.sort(metrics.loc[metrics.model=="GAM","Sim_ID"].to_numpy()),np.sort(metrics.loc[metrics.model=="RF","Sim_ID"].to_numpy())): raise ValueError("GAM/RF realization IDs differ")
    metrics=metrics.sort_values(["model","Sim_ID"])
    colors={"GAM":"#2459A6","RF":"#C9343A"}
    specs=[("correlation_sampled","Pearson r","(a) Pearson correlation"),("rmse_sampled","RMSE (log10 recruitment)","(b) RMSE")]
    stats=[]
    fig,axes=plt.subplots(1,2,figsize=(11,4.7))
    for ax,(column,xlabel,title) in zip(axes,specs):
        values={m:metrics.loc[metrics.model==m,column].to_numpy(float) for m in ("GAM","RF")}
        if any(len(v)!=500 or not np.isfinite(v).all() for v in values.values()): raise ValueError(f"Invalid values in {column}")
        lo=min(v.min() for v in values.values()); hi=max(v.max() for v in values.values()); pad=max((hi-lo)*.08,0.01)
        edges=np.linspace(lo-pad,hi+pad,25)
        for m in ("GAM","RF"):
            v=values[m]; c=colors[m]; mean=float(v.mean()); median=float(np.median(v)); q025=float(np.percentile(v,2.5)); q975=float(np.percentile(v,97.5))
            ax.hist(v,bins=edges,color=c,alpha=.43,label=m,edgecolor="white",linewidth=.35)
            ymax=ax.get_ylim()[1]
            ax.axvline(mean,color=c,linestyle="-",linewidth=1.1)
            ax.axvline(median,color=c,linestyle="--",linewidth=1.8)
            y=.035 if m=="GAM" else .105
            ax.plot([q025,q975],[y*ymax,y*ymax],color=c,linewidth=2.0,clip_on=False)
            ax.plot([q025,q025],[y*ymax-.018*ymax,y*ymax+.018*ymax],color=c,linewidth=1.2,clip_on=False)
            ax.plot([q975,q975],[y*ymax-.018*ymax,y*ymax+.018*ymax],color=c,linewidth=1.2,clip_on=False)
            ax.plot(median,y*ymax,"o",color=c,markersize=4,clip_on=False)
            stats.append({"model":m,"metric":column,"mean":mean,"median":median,"q025":q025,"q975":q975,"n":500})
        ax.set_title(title,loc="left",fontweight="bold")
        ax.set_xlabel(xlabel); ax.set_ylabel("Number of realizations")
        ax.grid(axis="y",linestyle=":",alpha=.45); ax.set_axisbelow(True)
        summary=pd.DataFrame(stats)
        lines=[]
        for m in ("GAM","RF"):
            row=summary[(summary.metric==column)&(summary.model==m)].iloc[0]
            lines.append(f"{m}   {row['mean']:.3f}   {row['median']:.3f}   [{row['q025']:.3f}, {row['q975']:.3f}]")
        ax.text(.98,1.20,"Model   Mean   Median   2.5–97.5%\n"+"\n".join(lines),transform=ax.transAxes,ha="right",va="top",fontsize=8.5, family="DejaVu Sans",bbox=dict(boxstyle="round,pad=.35",facecolor="white",edgecolor="0.75",alpha=.92),clip_on=False)
    handles=[plt.Line2D([0],[0],color=colors[m],linewidth=7,alpha=.43,label=m) for m in ("GAM","RF")]
    fig.legend(handles=handles,loc="lower center",ncol=2,frameon=False,bbox_to_anchor=(.5,-.025))
    fig.subplots_adjust(bottom=.19,wspace=.26,left=.07,right=.98,top=.78)
    fig.savefig(figdir/"skill_uncertainty_annotated.png",dpi=300,bbox_inches="tight")
    fig.savefig(figdir/"skill_uncertainty_annotated.pdf",bbox_inches="tight")
    pd.DataFrame(stats).to_csv(OUT/"skill_uncertainty_summary.csv",index=False)
def main():
    ck=OUT/"checkpoints"; files=sorted(ck.glob("sample_*.npz")); ids=[int(f.stem.split('_')[1]) for f in files]
    if ids != list(range(1,501)): raise ValueError(f"Expected complete sample IDs 1-500, found {len(ids)}")
    gam=np.empty((500,40)); rf=np.empty((500,40))
    for i,f in enumerate(files):
        z=np.load(f)
        if z["gam"].shape!=(40,) or z["rf"].shape!=(40,) or not np.isfinite(z["gam"]).all() or not np.isfinite(z["rf"]).all(): raise ValueError(f"Invalid checkpoint {f}")
        gam[i]=z["gam"]; rf[i]=z["rf"]
    obs=pd.read_csv(ROOT/"data/raw/observed_recruitment_1981_2020.csv").sort_values("year").recruitment.to_numpy(float); obslog=np.log10(obs)
    base=pd.read_csv(ROOT/"results/observational/holdout_svd_evaluation/heldout_predictions.csv").sort_values("year")
    baseline={"GAM":base.GAM_log10_prediction.to_numpy(),"RF":base.RF_log10_prediction.to_numpy()}; pred={"GAM":gam,"RF":rf}
    rows=[]
    for m in pred:
        raw=10**pred[m]; b=10**baseline[m]
        for j,y in enumerate(YEARS): rows.append({"model":m,"year":int(y),"baseline_prediction":b[j],"ensemble_mean":raw[:,j].mean(),"ensemble_median":np.median(raw[:,j]),"std":raw[:,j].std(ddof=1),"variance":raw[:,j].var(ddof=1),"q025":np.percentile(raw[:,j],2.5),"q975":np.percentile(raw[:,j],97.5),"interval_width":np.percentile(raw[:,j],97.5)-np.percentile(raw[:,j],2.5),"baseline_minus_median":b[j]-np.median(raw[:,j])})
    annual=pd.DataFrame(rows); annual.to_csv(OUT/"annual_uncertainty_summary.csv",index=False)
    metric=[]
    for i in range(500):
        for m in pred:
            metric.append({"Sim_ID":i+1,"model":m,"correlation_sampled":pearsonr(np.loadtxt(ROOT/"data/raw/Y_sim_500_samples.csv",delimiter=',',skiprows=1,usecols=range(1,41))[i],pred[m][i]).statistic,"rmse_sampled":np.sqrt(mean_squared_error(np.loadtxt(ROOT/"data/raw/Y_sim_500_samples.csv",delimiter=',',skiprows=1,usecols=range(1,41))[i],pred[m][i])),"correlation_original":pearsonr(obslog,pred[m][i]).statistic,"rmse_original":np.sqrt(mean_squared_error(obslog,pred[m][i]))})
    metrics=pd.DataFrame(metric); metrics.to_csv(OUT/"skill_metrics_500.csv",index=False)
    conv=[]
    for n in (100,200,300,500):
        for m in pred:
            a=10**pred[m][:n]
            for j,y in enumerate(YEARS): conv.append({"n_realizations":n,"model":m,"year":int(y),"median":np.median(a[:,j]),"std":a[:,j].std(ddof=1),"q025":np.percentile(a[:,j],2.5),"q975":np.percentile(a[:,j],97.5)})
    pd.DataFrame(conv).to_csv(OUT/"monte_carlo_convergence.csv",index=False)
    figdir=OUT/"figures"; figdir.mkdir(exist_ok=True); plt.style.use("seaborn-v0_8-whitegrid")
    fig,ax=plt.subplots(2,1,figsize=(12,8),sharex=True)
    for a,m,c in zip(ax,("GAM","RF"),("#0072B2","#D55E00")):
        q=annual[annual.model==m]; a.plot(YEARS,obs,"k-",label="Assessment estimate"); a.plot(YEARS,q.baseline_prediction,"--",color="0.35",label="Original LOOCV"); a.plot(YEARS,q.ensemble_median,color=c,label="Propagation median"); a.fill_between(YEARS,q.q025,q.q975,color=c,alpha=.22,label="2.5–97.5% response-uncertainty interval"); a.set_ylabel("Recruitment"); a.set_title(m); a.legend(fontsize=8)
    ax[-1].set_xlabel("Year"); fig.tight_layout(); fig.savefig(figdir/"recruitment_uncertainty_timeseries.png",dpi=240); fig.savefig(figdir/"recruitment_uncertainty_timeseries.pdf"); plt.close(fig)
    fig,ax=plt.subplots(1,2,figsize=(11,4));
    for m,c in zip(("GAM","RF"),("#0072B2","#D55E00")):
        q=metrics[metrics.model==m]; ax[0].hist(q.correlation_sampled,bins=25,alpha=.45,color=c,label=m); ax[1].hist(q.rmse_sampled,bins=25,alpha=.45,color=c,label=m)
    ax[0].set_xlabel("Pearson r (sampled response)"); ax[1].set_xlabel("RMSE (sampled response)"); ax[0].legend(); fig.tight_layout(); fig.savefig(figdir/"skill_uncertainty.png",dpi=240); fig.savefig(figdir/"skill_uncertainty.pdf"); plt.close(fig)
    fig,ax=plt.subplots(figsize=(11,4));
    for m,c in zip(("GAM","RF"),("#0072B2","#D55E00")):
        q=annual[annual.model==m]; ax.plot(YEARS,q["std"].to_numpy(),color=c,label=m)
    ax.set(xlabel="Year",ylabel="Prediction SD (recruitment units)"); ax.legend(); fig.tight_layout(); fig.savefig(figdir/"annual_sensitivity.png",dpi=240); fig.savefig(figdir/"annual_sensitivity.pdf"); plt.close(fig)
    fig,ax=plt.subplots(1,2,figsize=(11,4));
    for m,c in zip(("GAM","RF"),("#0072B2","#D55E00")):
        q=pd.DataFrame(conv); q=q[q.model==m];
        for n,ls in zip((100,200,300,500),(":","--","-.","-")):
            sub=q[q.n_realizations==n]
            ax[0].plot(YEARS,sub["median"].to_numpy(),color=c,ls=ls,label=f"{m} n={n}")
            ax[1].plot(YEARS,sub["std"].to_numpy(),color=c,ls=ls)
    ax[0].set_title("Annual median"); ax[1].set_title("Annual SD"); ax[0].legend(fontsize=7,ncol=2); fig.tight_layout(); fig.savefig(figdir/"monte_carlo_convergence.png",dpi=240); fig.savefig(figdir/"monte_carlo_convergence.pdf"); plt.close(fig)
    plot_annotated_skill(metrics,figdir)
    print(json.dumps({"checkpoints":500,"prediction_rows":40000,"outputs":str(OUT)},indent=2))
if __name__=="__main__": main()
