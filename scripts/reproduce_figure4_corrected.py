from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, norm
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/observational/figure4_corrected_loocv"
OUT.mkdir(parents=True, exist_ok=True)
TRAIN = ROOT / "data/raw/all_40folds_39years_PO_AO_PCs_1981_2020.csv"
HOLD = ROOT / "data/processed/obs_SVD_LOOCV_raw_1981_2020.csv"
REC = ROOT / "data/raw/observed_recruitment_1981_2020.csv"
IJ = ROOT / "results/observational/figure4_corrected_loocv/annual_ij_vs_bootstrap.csv"
PRED = ["PO_PC1", "AO_PC1", "PO_PC2", "AO_PC2", "PO_PC3", "AO_PC3"]
pred = pd.read_csv(OUT / "annual_predictions_uncertainty.csv").sort_values("year").reset_index(drop=True)
ij = pd.read_csv(IJ).sort_values("year").reset_index(drop=True)
assert pred.year.tolist() == list(range(1981, 2021))
assert ij.year.tolist() == pred.year.tolist() and len(ij) == 40
for col in ("RF_log10_prediction", "RF_data_variance", "observed_log10_recruitment"):
    assert np.allclose(pred[col].to_numpy(), ij[col if col != "RF_data_variance" else col].to_numpy(), rtol=0, atol=1e-12)
# Keep the historical bootstrap estimate available for comparison. The IJ
# validation table is the authoritative archived source for both estimators;
# do not derive or overwrite the bootstrap column from IJ values.
pred["RF_bootstrap_model_variance"] = ij["bootstrap_RF_model_variance"]
pred["RF_model_variance"] = ij["IJ_bias_corrected_variance"]
pred["RF_total_variance"] = pred["RF_model_variance"] + pred["RF_data_variance"]
pred["RF_model_lower"] = pred["RF_log10_prediction"] - 1.96 * np.sqrt(pred["RF_model_variance"])
pred["RF_model_upper"] = pred["RF_log10_prediction"] + 1.96 * np.sqrt(pred["RF_model_variance"])
pred["RF_PI_lower"] = pred["RF_log10_prediction"] - 1.96 * np.sqrt(pred["RF_total_variance"])
pred["RF_PI_upper"] = pred["RF_log10_prediction"] + 1.96 * np.sqrt(pred["RF_total_variance"])
existing = pd.read_csv(OUT / "annual_predictions_uncertainty.csv").sort_values("year").reset_index(drop=True)
same = list(existing.columns) == list(pred.columns) and len(existing) == len(pred)
if same:
    for col in pred.columns:
        if pd.api.types.is_numeric_dtype(pred[col]):
            same = same and np.allclose(existing[col].to_numpy(), pred[col].to_numpy(), rtol=0, atol=1e-12)
        else:
            same = same and existing[col].equals(pred[col])
if not same:
    pred.to_csv(OUT / "annual_predictions_uncertainty.csv", index=False)

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

The original visual reference was `data/code/original_draft/GAM_RF_predicted.ipynb`. Its alternative `JP_TROLL_CPUE` branch was not used. This public reproduction consumes the archived annual prediction table and archived IJ variance table; it does not require the external fitted models for ordinary figure regeneration.

Point predictions reuse the saved 40 GAM and 40 RF fold models under `results/observational/training/models`; no models were refit for point prediction. Each target uses its matching raw six-predictor held-out SVD row and a 39-year training fold.

GAM model variance is retained from the archived corrected workflow. RF model-estimation variance is the validated uncalibrated forestci IJ core with finite-tree bias correction, archived by year in `annual_ij_vs_bootstrap.csv`; stochastic forestci `calibrate=True` calibration was not reproduced. RF data variance is retained from the existing inner five-fold CV results.

Combined variance is `model variance + data variance`; bounds are an approximate Gaussian 95% prediction interval. Fisher-z correlation intervals are reported separately and are not prediction intervals. No recruitment-assessment uncertainty or 500 simulated recruitment realizations were included.

See `annual_predictions_uncertainty.csv`, `annual_ij_vs_bootstrap.csv`, `rf_ij_validation_summary.json`, `performance_metrics.csv`, and `validation_audit.csv`.
"""
(OUT / "methodology_report.md").write_text(report, encoding="utf-8")
print(metrics_df.to_string(index=False))
