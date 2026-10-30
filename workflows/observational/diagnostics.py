"""Internal complexity and stability diagnostics for the new observational pipeline."""
from __future__ import annotations

import argparse, json, time, warnings
from pathlib import Path
import numpy as np
import pandas as pd

from src.pbf.observational import (
    PREDICTORS, RF_CONFIG, GAM_CONFIG, fit_gam, fit_rf, load_fold_data,
    predict_rf, validate_folds,
)

TREE_COUNTS = (100, 200, 500, 1000)

def gam_diagnostics(model, X, y, fold, left_out, warnings_text):
    fitted = np.asarray(model.predict(X), dtype=float)
    edof = np.asarray(model.statistics_["edof"], dtype=float)
    # pyGAM's edof vector is per fitted coefficient and includes the intercept.
    term_edf = {}
    for term_index, name in enumerate((*PREDICTORS, "intercept")):
        try:
            indices = model.terms.get_coef_indices(term_index)
            term_edf[name] = float(edof[indices].sum())
        except Exception:
            term_edf[name] = np.nan
    return {
        "Fold": int(fold), "Left_Out_Year": int(left_out), "n_train": len(y),
        "total_edf_including_intercept": float(edof.sum()),
        "effective_residual_df": float(len(y) - edof.sum()),
        "intercept_edf": term_edf["intercept"],
        "term_edf_json": json.dumps({k: term_edf[k] for k in PREDICTORS}),
        "smoothing_parameters_json": json.dumps(np.asarray(model.lam).tolist()),
        "training_rmse_log10": float(np.sqrt(np.mean((y - fitted) ** 2))),
        "warnings": " | ".join(warnings_text),
    }

def run_gam_diagnostics(data, output):
    rows = []
    for fold, group in data.groupby("Fold", sort=True):
        X = group.loc[:, PREDICTORS].to_numpy(float); y = np.log10(group.recruitment.to_numpy(float))
        model, captured = fit_gam(X, y)
        rows.append(gam_diagnostics(model, X, y, fold, group.Left_Out_Year.iloc[0], captured))
    result = pd.DataFrame(rows)
    result.to_csv(output / "gam_complexity_by_fold.csv", index=False)
    return result

def run_rf_sensitivity(data, output):
    all_rows, importance_rows = [], []
    predictions = {}
    for trees in TREE_COUNTS:
        predictions[trees] = {}
        for fold, group in data.groupby("Fold", sort=True):
            X = group.loc[:, PREDICTORS].to_numpy(float); y = np.log10(group.recruitment.to_numpy(float))
            config = dict(RF_CONFIG); config["n_estimators"] = trees
            start = time.perf_counter()
            with warnings.catch_warnings(record=True) as captured:
                warnings.simplefilter("always")
                from sklearn.ensemble import RandomForestRegressor
                model = RandomForestRegressor(**config).fit(X, y)
            elapsed = time.perf_counter() - start
            fitted = predict_rf(model, X); predictions[trees][int(fold)] = fitted
            all_rows.append({"Fold": int(fold), "Left_Out_Year": int(group.Left_Out_Year.iloc[0]), "n_estimators": trees, "runtime_seconds": elapsed, "training_rmse_log10": float(np.sqrt(np.mean((y-fitted)**2))), "warnings": " | ".join(str(w.message) for w in captured)})
            for predictor, importance in zip(PREDICTORS, model.feature_importances_):
                importance_rows.append({"Fold": int(fold), "n_estimators": trees, "Predictor": predictor, "importance": float(importance), "rank": int(1 + np.argsort(-model.feature_importances_).tolist().index(PREDICTORS.index(predictor)))})
    rows = pd.DataFrame(all_rows); rows["rmse_difference_vs_1000"] = rows.apply(lambda r: r.training_rmse_log10 - rows[(rows.Fold == r.Fold) & (rows.n_estimators == 1000)].training_rmse_log10.iloc[0], axis=1)
    rows.to_csv(output / "rf_tree_count_by_fold.csv", index=False)
    imp = pd.DataFrame(importance_rows); imp.to_csv(output / "rf_feature_importance_by_fold.csv", index=False)
    diffs=[]
    for trees in TREE_COUNTS:
        if trees == 1000: continue
        for fold in predictions[trees]:
            delta = predictions[trees][fold] - predictions[1000][fold]
            diffs.append({"Fold": fold, "n_estimators": trees, "prediction_rmse_difference_vs_1000": float(np.sqrt(np.mean(delta**2))), "prediction_mae_difference_vs_1000": float(np.mean(np.abs(delta)))})
    pd.DataFrame(diffs).to_csv(output / "rf_prediction_difference_vs_1000.csv", index=False)
    return rows, imp

def make_figures(gam, rf, imp, output):
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 1, figsize=(10, 8), constrained_layout=True)
    axes[0].plot(gam.Fold, gam.total_edf_including_intercept, "o-"); axes[0].set(xlabel="Fold", ylabel="Total EDF (including intercept)")
    axes[1].plot(gam.Fold, gam.effective_residual_df, "o-", color="tab:orange"); axes[1].set(xlabel="Fold", ylabel="Effective residual df")
    fig.savefig(output / "gam_edf_residual_df.png", dpi=180); plt.close(fig)
    fig, ax = plt.subplots(figsize=(10, 5))
    for trees, group in rf.groupby("n_estimators"):
        ax.plot(group.Fold, group.training_rmse_log10, "o-", label=str(trees))
    ax.set(xlabel="Fold", ylabel="Training RMSE (log10 recruitment)"); ax.legend(title="Trees"); fig.tight_layout(); fig.savefig(output / "rf_training_rmse_tree_counts.png", dpi=180); plt.close(fig)
    summary = imp.groupby(["n_estimators", "Predictor"], as_index=False).importance.mean()
    fig, ax = plt.subplots(figsize=(10, 5)); summary.pivot(index="Predictor", columns="n_estimators", values="importance").plot.bar(ax=ax); ax.set_ylabel("Mean feature importance"); fig.tight_layout(); fig.savefig(output / "rf_feature_importance_tree_counts.png", dpi=180); plt.close(fig)

def run(svd_csv, recruitment_csv, output_dir):
    output = Path(output_dir); output.mkdir(parents=True, exist_ok=True)
    data = load_fold_data(svd_csv, recruitment_csv); validate_folds(data)
    gam = run_gam_diagnostics(data, output); rf, imp = run_rf_sensitivity(data, output); make_figures(gam, rf, imp, output)
    checks = {"folds": int(data.Fold.nunique()), "rows_per_fold": sorted(data.groupby("Fold").size().unique().tolist()), "predictor_order": list(PREDICTORS), "target": "log10(recruitment)", "svd_leakage_verified": False, "svd_leakage_note": "Fold-level SVD fitting and preprocessing records are unavailable."}
    (output / "validation_checks.json").write_text(json.dumps(checks, indent=2), encoding="utf-8")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--svd-csv", required=True); parser.add_argument("--recruitment-csv", required=True); parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(); run(args.svd_csv, args.recruitment_csv, args.output_dir)
