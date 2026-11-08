"""Reproduce the Figure 4 forestci IJ core without modifying authoritative outputs.

The original notebook calls forestci.random_forest_error with default calibrate=True.
The installed environment lacks forestci, so this script reproduces calc_inbag,
the IJ core, and forestci's finite-tree bias correction. Calibration is reported
as unavailable rather than silently approximated.
"""
from pathlib import Path
import json
import pickle
import platform

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble._forest import _generate_sample_indices, _get_n_samples_bootstrap

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/observational/rf_ij_uncertainty"
OUT.mkdir(parents=True, exist_ok=True)
MODELS = ROOT / "results/observational/training/models"
TRAIN = ROOT / "data/raw/all_40folds_39years_PO_AO_PCs_1981_2020.csv"
HOLD = ROOT / "data/processed/obs_SVD_LOOCV_raw_1981_2020.csv"
BOOT = ROOT / "results/observational/figure4_corrected_loocv/annual_predictions_uncertainty.csv"
PRED = ["PO_PC1", "AO_PC1", "PO_PC2", "AO_PC2", "PO_PC3", "AO_PC3"]


def reconstructed_inbag(n_samples, forest):
    if not forest.bootstrap:
        raise ValueError("Saved forest has bootstrap=False")
    n_boot = _get_n_samples_bootstrap(n_samples, forest.max_samples)
    out = np.zeros((n_samples, forest.n_estimators), dtype=float)
    for j, tree in enumerate(forest.estimators_):
        idx = _generate_sample_indices(tree.random_state, n_samples, n_boot)
        out[:, j] = np.bincount(idx, minlength=n_samples)
    return out


def ij_raw_and_bias_corrected(forest, x_test, inbag):
    tree_pred = np.asarray([tree.predict(x_test) for tree in forest.estimators_], float)
    centered = (tree_pred - tree_pred.mean(axis=0)).T
    n_trees = forest.n_estimators
    raw = np.sum((np.dot(inbag - 1, centered.T) / n_trees) ** 2, axis=0)
    n_var = np.mean((inbag ** 2).mean(axis=1) - inbag.mean(axis=1) ** 2)
    boot_var = (centered ** 2).sum(axis=1) / n_trees
    correction = inbag.shape[0] * n_var * boot_var / n_trees
    return raw, raw - correction


train = pd.read_csv(TRAIN)
hold = pd.read_csv(HOLD).rename(columns={"Year": "year"}).sort_values("year")
boot = pd.read_csv(BOOT).sort_values("year")
rows = []
inbag_audit = []
for fold in range(1, 41):
    tr = train[train.Fold == fold].sort_values("Train_Year")
    left = int(tr.Left_Out_Year.iloc[0])
    xt = hold.loc[hold.year == left, PRED].to_numpy(float)
    with (MODELS / f"rf_fold_{fold:02d}.pkl").open("rb") as f:
        rf = pickle.load(f)
    assert len(tr) == 39 and rf.n_estimators == 1000 and rf.bootstrap
    pred = float(rf.predict(xt)[0])
    tree_mean = float(np.mean([tree.predict(xt)[0] for tree in rf.estimators_]))
    inbag = reconstructed_inbag(len(tr), rf)
    raw, ij = ij_raw_and_bias_corrected(rf, xt, inbag)
    rows.append({
        "Fold": fold, "year": left, "RF_log10_prediction": pred,
        "RF_tree_mean_prediction": tree_mean,
        "IJ_raw_variance": float(raw[0]),
        "IJ_bias_corrected_variance": float(ij[0]),
        "bootstrap_RF_model_variance": float(boot.loc[boot.year == left, "RF_model_variance"].iloc[0]),
        "RF_data_variance": float(boot.loc[boot.year == left, "RF_data_variance"].iloc[0]),
        "IJ_total_variance_unclipped": float(ij[0] + boot.loc[boot.year == left, "RF_data_variance"].iloc[0]),
    })
    inbag_audit.append({"Fold": fold, "year": left, "n_train": len(tr),
                        "n_trees": rf.n_estimators, "inbag_shape": str(inbag.shape),
                        "inbag_column_sums_all_1000": bool(np.all(inbag.sum(axis=0) == len(tr))),
                        "point_prediction_abs_tree_mean_difference": abs(pred-tree_mean),
                        "min_raw_ij": float(raw.min()), "min_bias_corrected_ij": float(ij.min()),
                        "finite": bool(np.isfinite(inbag).all() and np.isfinite(raw).all() and np.isfinite(ij).all())})

annual = pd.DataFrame(rows).sort_values("year")
annual["IJ_model_sd"] = np.sqrt(np.maximum(annual.IJ_bias_corrected_variance, 0))
annual["bootstrap_model_sd"] = np.sqrt(annual.bootstrap_RF_model_variance)
annual["IJ_PI_lower"] = annual.RF_log10_prediction - 1.96 * np.sqrt(np.maximum(annual.IJ_total_variance_unclipped, 0))
annual["IJ_PI_upper"] = annual.RF_log10_prediction + 1.96 * np.sqrt(np.maximum(annual.IJ_total_variance_unclipped, 0))
obs = np.log10(pd.read_csv(ROOT / "data/raw/observed_recruitment_1981_2020.csv").sort_values("year").recruitment.to_numpy(float))
annual["observed_log10_recruitment"] = obs
annual["IJ_PI_covered"] = (obs >= annual.IJ_PI_lower.to_numpy()) & (obs <= annual.IJ_PI_upper.to_numpy())
annual["bootstrap_total_variance"] = boot.RF_total_variance.to_numpy()
annual["bootstrap_PI_lower"] = boot.RF_PI_lower.to_numpy()
annual["bootstrap_PI_upper"] = boot.RF_PI_upper.to_numpy()
annual["bootstrap_PI_covered"] = (obs >= annual.bootstrap_PI_lower.to_numpy()) & (obs <= annual.bootstrap_PI_upper.to_numpy())
annual["variance_difference_IJ_minus_bootstrap"] = annual.IJ_bias_corrected_variance - annual.bootstrap_RF_model_variance
annual["variance_ratio_IJ_to_bootstrap"] = annual.IJ_bias_corrected_variance / annual.bootstrap_RF_model_variance.replace(0, np.nan)
annual.to_csv(OUT / "annual_ij_vs_bootstrap.csv", index=False)
pd.DataFrame(inbag_audit).to_csv(OUT / "inbag_reconstruction_audit.csv", index=False)

def score(y, lo, hi):
    a = .05; w = hi-lo
    return float(np.mean(w + (2/a)*np.where(y < lo, lo-y, np.where(y > hi, y-hi, 0))))

metrics = pd.DataFrame([
    {"method":"IJ_bias_corrected_un calibrated", "variance_source":"forestci core + bias correction; calibrate unavailable", "mean_variance":annual.IJ_bias_corrected_variance.mean(), "median_variance":annual.IJ_bias_corrected_variance.median(), "mean_PI_width":(annual.IJ_PI_upper-annual.IJ_PI_lower).mean(), "median_PI_width":(annual.IJ_PI_upper-annual.IJ_PI_lower).median(), "coverage":annual.IJ_PI_covered.mean(), "interval_score":score(obs, annual.IJ_PI_lower, annual.IJ_PI_upper), "negative_model_variances":int((annual.IJ_bias_corrected_variance<0).sum()), "nonfinite_model_variances":int((~np.isfinite(annual.IJ_bias_corrected_variance)).sum())},
    {"method":"500-bootstrap", "variance_source":"existing corrected Figure 4 output", "mean_variance":annual.bootstrap_RF_model_variance.mean(), "median_variance":annual.bootstrap_RF_model_variance.median(), "mean_PI_width":(annual.bootstrap_PI_upper-annual.bootstrap_PI_lower).mean(), "median_PI_width":(annual.bootstrap_PI_upper-annual.bootstrap_PI_lower).median(), "coverage":annual.bootstrap_PI_covered.mean(), "interval_score":score(obs, annual.bootstrap_PI_lower, annual.bootstrap_PI_upper), "negative_model_variances":int((annual.bootstrap_RF_model_variance<0).sum()), "nonfinite_model_variances":int((~np.isfinite(annual.bootstrap_RF_model_variance)).sum())},
])
metrics.to_csv(OUT / "comparison_metrics.csv", index=False)

fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(annual.year, obs, "k-", label="Observed recruitment")
ax.plot(annual.year, annual.RF_log10_prediction, color="#D55E00", label="Authoritative RF LOOCV prediction")
ax.fill_between(annual.year, annual.bootstrap_PI_lower, annual.bootstrap_PI_upper, color="#D55E00", alpha=.18, label="500-bootstrap PI")
ax.fill_between(annual.year, annual.IJ_PI_lower, annual.IJ_PI_upper, color="#0072B2", alpha=.18, label="IJ PI (uncalibrated)")
ax.set(xlabel="Year", ylabel="log10 recruitment", title="Candidate Figure 4: RF model-estimation uncertainty")
ax.legend(); fig.tight_layout(); fig.savefig(OUT / "candidate_figure4_rf_ij.png", dpi=220); plt.close(fig)

validation = {
    "folds": len(annual), "all_n_train_39": bool((pd.DataFrame(inbag_audit).n_train == 39).all()),
    "all_1000_tree_models": bool((pd.DataFrame(inbag_audit).n_trees == 1000).all()),
    "inbag_reconstructed_with_saved_tree_random_states": True,
    "all_inbag_columns_sum_to_39": bool(pd.DataFrame(inbag_audit).inbag_column_sums_all_1000.all()),
    "max_point_prediction_difference_tree_mean": float(pd.DataFrame(inbag_audit).point_prediction_abs_tree_mean_difference.max()),
    "max_point_prediction_difference_vs_existing": float(np.max(np.abs(annual.RF_log10_prediction.to_numpy() - boot.RF_log10_prediction.to_numpy()))),
    "all_ij_finite": bool(np.isfinite(annual.IJ_bias_corrected_variance).all()),
    "negative_ij_count": int((annual.IJ_bias_corrected_variance < 0).sum()),
    "forestci_installed": False, "sklearn_version": sklearn.__version__, "python_version": platform.python_version(),
    "calibrate_true_reproduced": False, "calibration_reason": "forestci unavailable; calibrate=True uses stochastic calibrateEB and was not approximated",
}
(OUT / "validation_summary.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
(OUT / "ij_method_report.md").write_text("""# RF infinitesimal-jackknife uncertainty comparison

The original notebook calls `forestci.calc_inbag(X_train.shape[0], rf)` and `forestci.random_forest_error(rf, X_train, X_test, inbag=inbag)` with the default `calibrate=True`. The saved forests have 1,000 trees, bootstrap sampling, depth 5, square-root feature selection, and random state 1.

This environment has scikit-learn 1.7.2 but no installed `forestci`. The script reconstructs each tree's in-bag counts from the saved tree random states and reproduces the documented IJ core and finite-tree bias correction. The default forestci empirical-Bayes calibration is not silently substituted: exact calibrated results cannot be reproduced here without the package and its version. `annual_ij_vs_bootstrap.csv` reports the uncalibrated IJ comparison with the existing 500-bootstrap, five-tree-per-refit estimates.

The in-bag audit checks 40 folds, 39 training observations, 1,000 trees per model, column sums of 39, finite values, and equality of the RF forest prediction to the mean of its tree predictions. The existing inner shuffled five-fold RF residual variances and authoritative RF point predictions are reused unchanged.
""", encoding="utf-8")
print(json.dumps(validation, indent=2))
print(metrics.to_string(index=False))
