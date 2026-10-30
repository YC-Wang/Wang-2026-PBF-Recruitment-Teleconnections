# Experiment B: recruitment-response uncertainty propagation

This optional workflow refits the existing observational 40-fold LOOCV GAM and RF models for each assessment-derived recruitment realization. It reuses the saved fold-specific six-component SVD predictors and never recomputes SVD or uses the held-out response in training.

## Verified configuration

- Years: 1981–2020; 40 folds; 39 training years per fold.
- Predictors: `PO_PC1, AO_PC1, PO_PC2, AO_PC2, PO_PC3, AO_PC3`, passed as raw saved values with no additional scaler.
- GAM: `pygam.LinearGAM`, six quadratic spline terms, `n_splines=3`, default `lam`, direct `.fit()`.
- RF: `RandomForestRegressor(n_estimators=1000, max_depth=5, max_features='sqrt', random_state=1, n_jobs=1)`.

`data/raw/Y_sim_500_samples.csv` contains 500 complete 1981–2020 vectors already expressed as positive log10 recruitment values. The source notebook documents independent annual normal draws with year-specific standard deviations and seed 123. The propagation workflow therefore fits these values directly and back-transforms predictions with `10**prediction`; it does not apply a second log transform. The annual independence and unknown joint assessment-error structure are limitations.

## Validation and smoke test

Baseline reproduction is in `baseline_validation/reproduction_metrics.csv`. All 80 refitted model predictions agree with the saved-model predictions exactly at the recorded floating-point precision (max absolute difference 0.0; 0 mismatches).

The 5-realization smoke test completed 400 refits (200 GAM and 200 RF), with one 40-year prediction vector per model and realization. Runtime was 215.0 seconds on one worker, implying approximately 6 hours for 500 realizations before parallel speedup. The full run was not launched because a practical multi-worker benchmark and machine-occupancy decision are still required.

## Interpretation

The empirical annual quantiles produced by the full run will describe uncertainty in fitted held-out predictions induced by uncertain training recruitment responses. They are not complete predictive intervals and should not be combined with the existing model-only or combined intervals without a justified dependence model.

## Execution

```powershell
python scripts/run_recruitment_uncertainty_loocv.py --n-samples 500 --n-workers 8 --resume
```

Completed realizations are stored atomically under `checkpoints/`; valid checkpoints are reused on resume. Existing model artifacts and existing observational outputs are not overwritten.
