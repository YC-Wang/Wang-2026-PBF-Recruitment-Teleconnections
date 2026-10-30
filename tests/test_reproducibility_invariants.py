"""Non-destructive workflow invariants; no model fitting or data reruns."""
from pathlib import Path
import numpy as np, pandas as pd
from src.pbf.observational import PREDICTORS, RF_CONFIG
from scripts.verify_observational_inputs import load_config
ROOT = Path(__file__).resolve().parents[1]

def test_configuration_preserves_observational_contract():
    config=load_config(ROOT/"configs"/"observational_paths.toml")
    assert config["execution"]["fold_count"] == 40
    assert config["execution"]["train_years_per_fold"] == 39
    assert tuple(config["execution"]["predictors"]) == PREDICTORS
    assert config["execution"]["response_transform"] == "log10(recruitment)"
    assert config["execution"]["rf_random_state"] == RF_CONFIG["random_state"]

def test_fold_predictor_structure_and_no_held_out_recruitment_leakage():
    heldout=pd.read_csv(ROOT/"data/processed/obs_SVD_LOOCV_raw_1981_2020.csv")
    assert len(heldout)==40 and heldout["Year"].tolist()==list(range(1981,2021))
    assert list(heldout.columns[1:])==list(PREDICTORS)
    assert heldout[list(PREDICTORS)].apply(np.isfinite).all().all()
    assert "recruitment" not in [c.lower() for c in heldout.columns]

def test_archived_output_schemas_and_uncertainty_separation():
    holdout=pd.read_csv(ROOT/"results/observational/holdout_svd_evaluation/heldout_predictions.csv")
    intervals=pd.read_csv(ROOT/"results/observational/figure4_corrected_loocv/annual_predictions_uncertainty.csv")
    sampled=pd.read_csv(ROOT/"results/observational/recruitment_uncertainty/skill_metrics_500.csv")
    assert len(holdout)==len(intervals)==40
    assert {"GAM_log10_prediction","RF_log10_prediction"}.issubset(holdout.columns)
    assert {"GAM_PI_lower","GAM_PI_upper","RF_PI_lower","RF_PI_upper"}.issubset(intervals.columns)
    assert {"correlation_sampled","rmse_sampled","Sim_ID"}.issubset(sampled.columns)
    assert not {"GAM_PI_lower","RF_PI_lower"}.intersection(sampled.columns)
    assert sorted(sampled.Sim_ID.unique())==list(range(1,501))
