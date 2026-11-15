# Held-out SVD evaluation validation report

Date: 2026-10-27

## Result

No held-out predictions or performance figures were generated. The requested evaluation cannot be performed validly from the recovered artifacts without inventing a preprocessing transformation or refitting models.

## Model audit

- Found 40/40 GAM pickles and 40/40 RF pickles under `results/observational/training/models`.
- The training table has 40 folds, 39 rows per fold, and each fold excludes its labeled `Left_Out_Year`.
- The model configuration records the required predictor order: `PO_PC1, AO_PC1, PO_PC2, AO_PC2, PO_PC3, AO_PC3`.
- Each loaded model accepts six features. The pickled objects contain fitted model state but no saved scaler, transformer, or fold-specific preprocessing metadata.

## Predictor compatibility audit

The models were fitted using `data/raw/all_40folds_39years_PO_AO_PCs_1981_2020.csv`, whose predictor values are on the original SVD-score scale. The supplied held-out file `obs_SVD_LOOCV_ano_1981_2020-checkpoint.csv` contains six year-level projections renamed to the required order, but on a materially different scale: each predictor is approximately standardized (SD 1), whereas the training SDs are approximately 4.1–9.4. The machine-readable comparison is in `predictor_scale_audit_ano.csv`.

Because the saved training code passes the six training predictors directly to GAM/RF and no scaler was persisted, there is no recoverable, defensible mapping from the supplied held-out values into the model input scale. Applying them directly would be an out-of-distribution substitution; estimating a mapping would violate the evaluation-only requirement.

## Previous results

`results/observational` contains training diagnostics and fold training residuals, but no prior genuine held-out observational skill table. Therefore an evidence-based correlation/RMSE comparison with an earlier held-out evaluation is unavailable. The training residual file must not be treated as held-out performance. The repository documentation also states that the current workflow did not calculate held-out predictive skill.

## Files written

- `model_fold_audit_ano.csv`: fold exclusion and model-file checks.
- `model_preprocessing_audit_ano.csv`: loaded pickle class/feature/preprocessing audit.
- `predictor_scale_audit_ano.csv`: numeric scale comparison.

No model, DCPP pipeline, or previous result was overwritten. Predictions, metrics, and figures are intentionally absent because the required preprocessing object cannot be recovered.
