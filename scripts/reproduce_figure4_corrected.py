from pathlib import Path
import pickle
import shutil

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, norm
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold
from pygam import LinearGAM, s

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/observational/figure4_corrected_loocv"
OUT.mkdir(parents=True, exist_ok=True)
TRAIN = ROOT / "data/raw/all_40folds_39years_PO_AO_PCs_1981_2020.csv"
HOLD = ROOT / "data/processed/obs_SVD_LOOCV_raw_1981_2020.csv"
REC = ROOT / "data/raw/observed_recruitment_1981_2020.csv"
MODELS = ROOT / "results/observational/training/models"
PRED = ["PO_PC1", "AO_PC1", "PO_PC2", "AO_PC2", "PO_PC3", "AO_PC3"]
GAM_CONFIG = {"n_splines": 3, "spline_order": 2}
RF_CONFIG = {"n_estimators": 1000, "max_depth": 5, "max_features": "sqrt", "random_state": 1, "n_jobs": 1}
RF_BOOT_CONFIG = {**RF_CONFIG, "n_estimators": 5}
BOOTSTRAPS = 500

def terms():
    t = s(0, **GAM_CONFIG)
    for j in range(1, 6): t += s(j, **GAM_CONFIG)
    return t

def fit_gam(x, y): return LinearGAM(terms()).fit(x, y)
def fit_rf(x, y): return RandomForestRegressor(**RF_CONFIG).fit(x, y)
def fit_rf_boot(x, y, seed):
    config = {**RF_BOOT_CONFIG, "random_state": int(seed)}
    return RandomForestRegressor(**config).fit(x, y)

train = pd.read_csv(TRAIN)
hold = pd.read_csv(HOLD).rename(columns={"Year": "year"}).sort_values("year")
rec = pd.read_csv(REC).sort_values("year")
assert train.groupby("Fold").size().eq(39).all()
assert (train.Train_Year != train.Left_Out_Year).all()
assert hold.year.tolist() == list(range(1981, 2021)) and hold[PRED].notna().all().all()
assert rec.year.tolist() == list(range(1981, 2021))

rng = np.random.default_rng(20261027)
rows, audits = [], []
for fold in range(1, 41):
    print(f"fold {fold}/40", flush=True)
    left = int(train.loc[train.Fold == fold, "Left_Out_Year"].iloc[0])
    tr = train[train.Fold == fold].sort_values("Train_Year")
    xtr = tr[PRED].to_numpy(float); ytr = np.log10(rec.set_index("year").loc[tr.Train_Year, "recruitment"].to_numpy(float))
    xt = hold.loc[hold.year == left, PRED].to_numpy(float)
    with (MODELS / f"gam_fold_{fold:02d}.pkl").open("rb") as f: gam = pickle.load(f)
    with (MODELS / f"rf_fold_{fold:02d}.pkl").open("rb") as f: rf = pickle.load(f)
    gp = float(gam.predict(xt)[0]); rp = float(rf.predict(xt)[0])
    # pyGAM's intervals are coefficient-covariance conditional mean intervals.
    gi = np.asarray(gam.confidence_intervals(xt, width=0.95), float)[0]
    gv = max(0.0, float(((gi[1] - gi[0]) / (2 * 1.96)) ** 2))
    # forestci is unavailable; use training-only bootstrap refits as documented alternative.
    boot_r = []
    for b in range(BOOTSTRAPS):
        ix = rng.integers(0, len(xtr), len(xtr))
        boot_r.append(float(fit_rf_boot(xtr[ix], ytr[ix], 20261027 + fold * 1000 + b).predict(xt)[0]))
    rv = float(np.var(boot_r, ddof=1))
    # GAM bootstrap is diagnostic only; the saved-model covariance is used for GAM model variance.
    # Inner five-fold CV estimates unexplained data variance conditional on outer-fold predictors.
    inner = KFold(n_splits=5, shuffle=True, random_state=1)
    g_res, r_res = [], []
    for ii, vv in inner.split(xtr):
        gm = fit_gam(xtr[ii], ytr[ii]); rm = fit_rf(xtr[ii], ytr[ii])
        g_res.extend(ytr[vv] - gm.predict(xtr[vv])); r_res.extend(ytr[vv] - rm.predict(xtr[vv]))
    gd = float(np.var(g_res, ddof=1)); rd = float(np.var(r_res, ddof=1))
    rows.append({"Fold": fold, "year": left, "observed_recruitment": float(10 ** np.log10(rec.set_index("year").loc[left, "recruitment"])),
                 "observed_log10_recruitment": float(np.log10(rec.set_index("year").loc[left, "recruitment"])),
                 "GAM_log10_prediction": gp, "RF_log10_prediction": rp,
                 "GAM_model_variance": gv, "RF_model_variance": rv,
                 "GAM_data_variance": gd, "RF_data_variance": rd,
                 "GAM_total_variance": gv + gd, "RF_total_variance": rv + rd,
                 "GAM_model_lower": gp - 1.96*np.sqrt(gv), "GAM_model_upper": gp + 1.96*np.sqrt(gv),
                 "RF_model_lower": rp - 1.96*np.sqrt(rv), "RF_model_upper": rp + 1.96*np.sqrt(rv),
                 "GAM_PI_lower": gp - 1.96*np.sqrt(gv + gd), "GAM_PI_upper": gp + 1.96*np.sqrt(gv + gd),
                 "RF_PI_lower": rp - 1.96*np.sqrt(rv + rd), "RF_PI_upper": rp + 1.96*np.sqrt(rv + rd)})
    audits.append({"Fold": fold, "target_year": left, "n_train": len(tr), "excluded_year_in_training": bool((tr.Train_Year == left).any()),
                   "six_predictors": len(PRED), "raw_predictors": True})

pred = pd.DataFrame(rows).sort_values("year").reset_index(drop=True)
pred.to_csv(OUT / "annual_predictions_uncertainty.csv", index=False)
pd.DataFrame(audits).to_csv(OUT / "validation_audit.csv", index=False)

metrics = []
for method in ("GAM", "RF"):
    y = pred.observed_log10_recruitment.to_numpy(); p = pred[f"{method}_log10_prediction"].to_numpy()
    r = pearsonr(y, p).statistic; z = np.arctanh(r); se = 1/np.sqrt(len(y)-3)
    lo = pred[f"{method}_PI_lower"].to_numpy(); hi = pred[f"{method}_PI_upper"].to_numpy()
    alpha = 0.05; width = hi - lo
    interval_score = width + (2/alpha) * np.where(y < lo, lo-y, np.where(y > hi, y-hi, 0.0))
    metrics.append({"model": method, "scale": "log10(recruitment)", "n": len(y), "pearson_r": r,
                    "fisher_z_lower": np.tanh(z - 1.96*se), "fisher_z_upper": np.tanh(z + 1.96*se),
                    "RMSE": mean_squared_error(y,p)**0.5, "MAE": mean_absolute_error(y,p),
                    "mean_bias_pred_minus_obs": float(np.mean(p-y)), "R2": r2_score(y,p),
                    "combined_PI_coverage": float(np.mean((y >= lo) & (y <= hi))),
                    "mean_combined_PI_width": float(np.mean(width)),
                    "combined_PI_interval_score": float(np.mean(interval_score))})
metrics_df = pd.DataFrame(metrics); metrics_df.to_csv(OUT / "performance_metrics.csv", index=False)

# Preserve and compare the point predictions from the completed corrected workflow.
previous = ROOT / "results/observational/holdout_svd_evaluation/heldout_predictions.csv"
if previous.exists():
    old = pd.read_csv(previous).sort_values("year").reset_index(drop=True)
    point_compare = pd.DataFrame({
        "model": ["GAM", "RF"],
        "max_abs_log10_prediction_difference": [
            float(np.max(np.abs(pred.GAM_log10_prediction - old.GAM_log10_prediction))),
            float(np.max(np.abs(pred.RF_log10_prediction - old.RF_log10_prediction))),
        ],
    })
    point_compare.to_csv(OUT / "point_prediction_unchanged_comparison.csv", index=False)

plt.style.use("seaborn-v0_8-whitegrid")
fig, ax = plt.subplots(figsize=(12, 6)); x = pred.observed_log10_recruitment
for method, color, marker in (("GAM", "#0072B2", "o"), ("RF", "#D55E00", "s")):
    y = pred[f"{method}_log10_prediction"]; ax.scatter(x, y, color=color, marker=marker, alpha=.8, label=method)
    slope, intercept = np.polyfit(x, y, 1); xx = np.linspace(x.min(), x.max(), 100); ax.plot(xx, intercept+slope*xx, color=color, linewidth=2)
ax.plot([x.min(),x.max()],[x.min(),x.max()],"k--",linewidth=1); ax.set(xlabel="Observed log10 recruitment", ylabel="Predicted log10 recruitment", title="Figure 4: corrected observational LOOCV"); ax.legend(); fig.tight_layout()
for ext in ("png", "svg", "pdf"): fig.savefig(OUT / f"fig4_diagnostic.{ext}", dpi=220 if ext=="png" else None)
plt.close(fig)

fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
for ax, method, color in zip(axes, ("GAM", "RF"), ("#0072B2", "#D55E00")):
    ax.plot(pred.year, pred.observed_log10_recruitment, "k-", label="Observed recruitment")
    ax.plot(pred.year, pred[f"{method}_log10_prediction"], color=color, label=method)
    ax.fill_between(pred.year, pred[f"{method}_model_lower"], pred[f"{method}_model_upper"], color=color, alpha=.18, label="Model-only 95% CI")
    ax.fill_between(pred.year, pred[f"{method}_PI_lower"], pred[f"{method}_PI_upper"], color=color, alpha=.08, label="Combined 95% PI")
    ax.set_ylabel("log10 recruitment"); ax.set_title(method); ax.legend(loc="best")
axes[-1].set_xlabel("Year"); fig.tight_layout(); fig.savefig(OUT / "fig4_diagnostic_intervals.png", dpi=220); plt.close(fig)

report = f"""# Corrected Figure 4 observational LOOCV

The original visual reference was `data/code/original_draft/GAM_RF_predicted.ipynb`. Its alternative `JP_TROLL_CPUE` branch was not used. The response here is `log10(recruitment)` from the existing observational recruitment series.

Point predictions reuse the saved 40 GAM and 40 RF fold models under `results/observational/training/models`; no models were refit for point prediction. Each target uses its matching raw six-predictor held-out SVD row and a 39-year training fold.

GAM model variance uses `gam.confidence_intervals(..., width=0.95)` converted to variance via half-width/1.96. RF model variance uses {BOOTSTRAPS} training-only bootstrap refits because `forestci` is unavailable; tree-to-tree spread was not used as a confidence interval. Data variance is the residual variance from inner five-fold CV within each outer 39-year training fold, conditional on the existing outer-fold SVD representation rather than a nested SVD recomputation.

Combined variance is `model variance + data variance`; bounds are an approximate Gaussian 95% prediction interval. Fisher-z correlation intervals are reported separately and are not prediction intervals. No recruitment-assessment uncertainty or 500 simulated recruitment realizations were included.

See `annual_predictions_uncertainty.csv`, `performance_metrics.csv`, and `validation_audit.csv`.
"""
(OUT / "methodology_report.md").write_text(report, encoding="utf-8")

# Preserve the reference notebook in the new output directory for provenance.
shutil.copy2(ROOT / "data/code/original_draft/GAM_RF_predicted.ipynb", OUT / "GAM_RF_predicted_reference.ipynb")
print(metrics_df.to_string(index=False))
