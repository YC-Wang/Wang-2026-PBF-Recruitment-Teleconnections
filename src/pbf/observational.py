from __future__ import annotations

import json, logging, pickle, platform, sys, warnings
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import numpy as np
import pandas as pd

PREDICTORS = ("PO_PC1", "AO_PC1", "PO_PC2", "AO_PC2", "PO_PC3", "AO_PC3")
GAM_CONFIG = {"n_splines": 3, "spline_order": 2}
RF_CONFIG = {"n_estimators": 1000, "max_depth": 5, "max_features": "sqrt", "random_state": 1}

def load_fold_data(svd_csv: str | Path, recruitment_csv: str | Path) -> pd.DataFrame:
    fold = pd.read_csv(svd_csv); rec = pd.read_csv(recruitment_csv)
    fold.columns = fold.columns.str.strip(); rec.columns = rec.columns.str.strip()
    if not {"year", "recruitment"}.issubset(rec.columns): raise ValueError("Recruitment input requires year and recruitment")
    rec = rec.rename(columns={"year": "Train_Year"})[["Train_Year", "recruitment"]]
    return fold.merge(rec, on="Train_Year", how="left", validate="many_to_one")

def validate_folds(df: pd.DataFrame) -> None:
    required = {"Fold", "Left_Out_Year", "Train_Year", *PREDICTORS, "recruitment"}
    missing = required - set(df.columns)
    if missing: raise ValueError(f"Missing columns: {sorted(missing)}")
    if df.Fold.nunique() != 40: raise ValueError("Expected exactly 40 folds")
    for fold, group in df.groupby("Fold"):
        if len(group) != 39 or group.Train_Year.nunique() != 39: raise ValueError(f"Fold {fold} must contain 39 unique training years")
        if group.Left_Out_Year.nunique() != 1 or int(group.Left_Out_Year.iloc[0]) in set(group.Train_Year): raise ValueError(f"Fold {fold} contains its excluded year")
    values = df[list(PREDICTORS) + ["recruitment"]].to_numpy(float)
    if not np.isfinite(values).all(): raise ValueError("Predictors and recruitment must be finite")
    if (df.recruitment <= 0).any(): raise ValueError("Recruitment must be positive")

def gam_terms():
    from pygam import s
    terms = s(0, **GAM_CONFIG)
    for index in range(1, len(PREDICTORS)): terms += s(index, **GAM_CONFIG)
    return terms

def fit_gam(X, y):
    from pygam import LinearGAM
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always"); model = LinearGAM(gam_terms()).fit(X, y)
    return model, [str(w.message) for w in captured]

def fit_rf(X, y):
    from sklearn.ensemble import RandomForestRegressor
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always"); model = RandomForestRegressor(**RF_CONFIG).fit(X, y)
    return model, [str(w.message) for w in captured]

def predict_gam(model, X): return np.asarray(model.predict(np.asarray(X, dtype=float)))
def predict_rf(model, X): return np.asarray(model.predict(np.asarray(X, dtype=float)))

def save_model(model, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as stream: pickle.dump(model, stream, protocol=pickle.HIGHEST_PROTOCOL)

def diagnostics(model, X, y, method, fold, left_out, captured):
    pred = predict_gam(model, X) if method == "GAM" else predict_rf(model, X)
    residual = y - pred
    result = {"Fold": int(fold), "Left_Out_Year": int(left_out), "Model": method, "n_train": len(y), "train_mse": float(np.mean(residual**2)), "train_rmse": float(np.sqrt(np.mean(residual**2))), "warnings": " | ".join(captured)}
    if method == "GAM":
        edof = np.asarray(model.statistics_.get("edof", []), dtype=float)
        result.update(total_edf=float(edof.sum()), residual_df=float(len(y) - edof.sum()), term_edf=json.dumps(edof.tolist()), smoothing_parameters=json.dumps(np.asarray(model.lam).tolist()), scale=float(model.statistics_.get("scale", np.nan)))
    else:
        result.update({f"importance_{name}": float(value) for name, value in zip(PREDICTORS, model.feature_importances_)}, parameters=json.dumps(model.get_params(), sort_keys=True))
    return result, pred, residual

def dependency_versions():
    found = {}
    for package in ("numpy", "pandas", "scipy", "scikit-learn", "pygam"):
        try: found[package] = version(package)
        except PackageNotFoundError: found[package] = "not installed"
    return found

def run_training(svd_csv, recruitment_csv, output_dir):
    output = Path(output_dir); (output / "models").mkdir(parents=True, exist_ok=True); (output / "logs").mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=output / "logs" / "execution.log", level=logging.INFO, force=True)
    data = load_fold_data(svd_csv, recruitment_csv); validate_folds(data); data["log10_recruitment"] = np.log10(data.recruitment)
    summaries, predictions = [], []
    for fold, group in data.groupby("Fold", sort=True):
        X = group.loc[:, PREDICTORS].to_numpy(float); y = group.log10_recruitment.to_numpy(float); left = int(group.Left_Out_Year.iloc[0])
        for method, fitter in (("GAM", fit_gam), ("RF", fit_rf)):
            model, captured = fitter(X, y); save_model(model, output / "models" / f"{method.lower()}_fold_{int(fold):02d}.pkl")
            summary, pred, residual = diagnostics(model, X, y, method, fold, left, captured); summaries.append(summary)
            for year, observed, fitted, error in zip(group.Train_Year, y, pred, residual): predictions.append({"Fold": int(fold), "Left_Out_Year": left, "Train_Year": int(year), "Model": method, "observed_log10_recruitment": float(observed), "fitted": float(fitted), "residual": float(error)})
    pd.DataFrame(summaries).to_csv(output / "model_summary.csv", index=False); pd.DataFrame(predictions).to_csv(output / "training_predictions_residuals.csv", index=False)
    config = {"predictors": PREDICTORS, "gam": GAM_CONFIG, "gam_regularization": "pygam LinearGAM default; no grid search; default lam retained", "rf": RF_CONFIG, "python": sys.version, "platform": platform.platform(), "dependencies": dependency_versions()}
    (output / "model_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
