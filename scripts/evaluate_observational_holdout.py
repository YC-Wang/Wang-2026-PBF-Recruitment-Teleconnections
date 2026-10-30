from pathlib import Path
import pickle
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import pearsonr
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / "data/raw/all_40folds_39years_PO_AO_PCs_1981_2020.csv"
HOLDOUT = ROOT / "data/processed/obs_SVD_LOOCV_raw_1981_2020.csv"
RECRUITMENT = ROOT / "data/raw/observed_recruitment_1981_2020.csv"
MODEL_DIR = ROOT / "results/observational/training/models"
OUT = ROOT / "results/observational/holdout_svd_evaluation"
OUT.mkdir(parents=True, exist_ok=True)

PRED = ["PO_PC1", "AO_PC1", "PO_PC2", "AO_PC2", "PO_PC3", "AO_PC3"]

train = pd.read_csv(TRAIN)
hold = pd.read_csv(HOLDOUT).rename(columns={"Year": "year"})
rec = pd.read_csv(RECRUITMENT)
rec = rec.rename(columns={"year": "year", "recruitment": "recruitment"})

assert len(train) == 1560 and train.Fold.nunique() == 40
assert len(hold) == 40 and hold.year.tolist() == list(range(1981, 2021))
assert hold[PRED].notna().all().all()
assert rec.year.tolist() == list(range(1981, 2021))

fold_year = train.groupby("Fold", sort=True)["Left_Out_Year"].agg(["nunique", "first"])
assert fold_year["nunique"].eq(1).all()
assert (train.Train_Year != train.Left_Out_Year).all()
assert train.groupby("Fold").size().eq(39).all()

audit = []
predictions = []
for fold in range(1, 41):
    left = int(fold_year.loc[fold, "first"])
    gam_path = MODEL_DIR / f"gam_fold_{fold:02d}.pkl"
    rf_path = MODEL_DIR / f"rf_fold_{fold:02d}.pkl"
    if not gam_path.exists() or not rf_path.exists():
        raise FileNotFoundError(f"Missing saved model for fold {fold}")
    with gam_path.open("rb") as f:
        gam = pickle.load(f)
    with rf_path.open("rb") as f:
        rf = pickle.load(f)
    gam_features = getattr(gam.statistics_, "m_features", None)
    if gam_features is None:
        gam_features = gam.statistics_.get("m_features", None)
    rf_features = getattr(rf, "n_features_in_", None)
    gam_scaler = any(k in vars(gam) for k in ("scaler", "preprocessor", "transformer", "x_scaler", "feature_scaler", "_scaler"))
    rf_scaler = any(k in vars(rf) for k in ("scaler", "preprocessor", "transformer", "x_scaler", "feature_scaler", "_scaler"))
    audit.append({"Fold": fold, "Left_Out_Year": left, "n_train": int((train.Fold == fold).sum()),
                  "gam_features": gam_features, "rf_features": rf_features,
                  "gam_scaler_attribute": gam_scaler, "rf_scaler_attribute": rf_scaler,
                  "gam_model": type(gam).__name__, "rf_model": type(rf).__name__})
    x = hold.loc[hold.year == left, PRED].to_numpy(float)
    if x.shape != (1, 6):
        raise ValueError(f"Expected one six-predictor held-out row for {left}")
    predictions.append({"Fold": fold, "year": left,
                        "observed_recruitment": float(rec.loc[rec.year == left, "recruitment"].iloc[0]),
                        "observed_log10_recruitment": float(np.log10(rec.loc[rec.year == left, "recruitment"].iloc[0])),
                        "GAM_log10_prediction": float(gam.predict(x)[0]),
                        "RF_log10_prediction": float(rf.predict(x)[0])})

audit_df = pd.DataFrame(audit)
if not ((audit_df.n_train == 39).all() and (audit_df.gam_features == 6).all() and (audit_df.rf_features == 6).all()):
    raise ValueError("Saved-model audit failed")
audit_df.to_csv(OUT / "model_audit.csv", index=False)

pred = pd.DataFrame(predictions).sort_values("year").reset_index(drop=True)
for method in ("GAM", "RF"):
    pred[f"{method}_predicted_recruitment"] = 10 ** pred[f"{method}_log10_prediction"]
    pred[f"{method}_residual_log10"] = pred[f"{method}_log10_prediction"] - pred.observed_log10_recruitment
pred.to_csv(OUT / "heldout_predictions.csv", index=False)

metrics = []
for method in ("GAM", "RF"):
    y = pred.observed_log10_recruitment.to_numpy()
    p = pred[f"{method}_log10_prediction"].to_numpy()
    metrics.append({"model": method, "target_scale": "log10(recruitment)",
                    "n_years": len(y), "pearson_r": pearsonr(y, p).statistic,
                    "RMSE": mean_squared_error(y, p) ** 0.5,
                    "MAE": mean_absolute_error(y, p), "mean_bias_pred_minus_obs": float(np.mean(p-y)),
                    "R2": r2_score(y, p)})
metrics_df = pd.DataFrame(metrics)
metrics_df.to_csv(OUT / "performance_metrics.csv", index=False)

plt.style.use("seaborn-v0_8-whitegrid")
fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(pred.year, pred.observed_log10_recruitment, "ko-", label="Observed", linewidth=2)
ax.plot(pred.year, pred.GAM_log10_prediction, "o-", color="#0072B2", label="GAM")
ax.plot(pred.year, pred.RF_log10_prediction, "s-", color="#D55E00", label="RF")
ax.set(xlabel="Year", ylabel="log10 recruitment", title="Observational held-out LOOCV predictions")
ax.legend(); fig.tight_layout(); fig.savefig(OUT / "observed_vs_predicted_timeseries.png", dpi=200); plt.close(fig)

fig, axes = plt.subplots(1, 2, figsize=(11, 5))
for ax, method, color in zip(axes, ("GAM", "RF"), ("#0072B2", "#D55E00")):
    x = pred.observed_log10_recruitment; y = pred[f"{method}_log10_prediction"]
    ax.scatter(x, y, color=color, edgecolor="white", linewidth=0.5)
    lo, hi = min(x.min(), y.min()), max(x.max(), y.max())
    ax.plot([lo, hi], [lo, hi], "k--", linewidth=1)
    ax.set(xlabel="Observed log10 recruitment", ylabel="Predicted log10 recruitment", title=method)
fig.tight_layout(); fig.savefig(OUT / "predicted_vs_observed_scatter.png", dpi=200); plt.close(fig)

fig, ax = plt.subplots(figsize=(12, 5))
ax.axhline(0, color="black", linewidth=1)
ax.plot(pred.year, pred.GAM_residual_log10, "o-", color="#0072B2", label="GAM residual")
ax.plot(pred.year, pred.RF_residual_log10, "s-", color="#D55E00", label="RF residual")
ax.set(xlabel="Year", ylabel="Prediction − observed (log10 scale)", title="Held-out residuals")
ax.legend(); fig.tight_layout(); fig.savefig(OUT / "residual_timeseries.png", dpi=200); plt.close(fig)

report = f"""# Observational LOOCV held-out SVD evaluation

Predictions were generated by loading the existing 40 saved GAM/RF pickle models. No SVD was recalculated and no model was refit.

## Inputs

- Training predictors: `{TRAIN.relative_to(ROOT)}`
- Held-out predictors: `{HOLDOUT.relative_to(ROOT)}`
- Models: `{MODEL_DIR.relative_to(ROOT)}`
- Observed recruitment: `{RECRUITMENT.relative_to(ROOT)}`

## Model audit

All 40 GAM and 40 RF models were present. Every fold has 39 training rows and excludes its corresponding prediction year. Each saved model accepts six predictors in the original order: `{', '.join(PRED)}`. No scaler/preprocessor attribute was found; the repository training code passes raw SVD predictors directly to the models.

## Evaluation

Each prediction uses the corresponding fold model and that fold's raw six-predictor held-out projection. Metrics are calculated on the complete 40-year series of `log10(recruitment)` values. No 500 recruitment uncertainty realizations were used or found in this saved-model evaluation, so no uncertainty interval is reported.

See `performance_metrics.csv`, `heldout_predictions.csv`, and `model_audit.csv`.

Previous files under `results/observational` contain training diagnostics/residuals; they are not a prior genuine held-out observational evaluation and were not overwritten.
"""
(OUT / "methodology_report.md").write_text(report, encoding="utf-8")
print(metrics_df.to_string(index=False))
