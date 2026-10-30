# Observational diagnostics results

These results are from the current new-pipeline SVD training inputs only. No original-pipeline comparison or held-out predictive skill was calculated.

## GAM

All 40 folds fitted successfully with zero warnings. Total EDF including the intercept ranged from 7.3089 to 7.3655 (mean 7.3414; median 7.3426). Effective residual degrees of freedom ranged from 31.6345 to 31.6911 (mean 31.6586). Training RMSE and all six smoothing parameters are in `results/observational/diagnostics/gam_complexity_by_fold.csv`.

## RF tree-count sensitivity

All 160 RF fits completed successfully. Mean training runtime and mean training RMSE were:

| Trees | Mean runtime (s) | Mean training RMSE |
|---:|---:|---:|
| 100 | 0.145 | 0.073784 |
| 200 | 0.239 | 0.072015 |
| 500 | 0.601 | 0.071464 |
| 1,000 | 1.353 | 0.071293 |

Relative to the 1,000-tree baseline, mean fitted-prediction RMSE differences were 0.012102 for 100 trees, 0.007513 for 200 trees, and 0.004095 for 500 trees, all in log10 recruitment units.

At 1,000 trees, the most frequent fold-level top-ranked predictor was `PO_PC1` (25/40 folds), followed by `AO_PC2` (11/40), `AO_PC3` (3/40), and `AO_PC1` (1/40). Feature importances and rankings for every tree count are saved in `rf_feature_importance_by_fold.csv`.

## Validation and reproducibility

The fold checks passed: 40 folds, 39 training years per fold, no excluded-year overlap, correct six-predictor ordering, positive finite recruitment, and deterministic RF fitting. Automated tests: 3 passed.

These checks do not prove that the SVD calculations were leakage-free because fold-specific SVD fitting and preprocessing records are unavailable.
