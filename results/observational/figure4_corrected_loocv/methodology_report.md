# Corrected Figure 4 observational LOOCV

The original visual reference was `data/code/original_draft/GAM_RF_predicted.ipynb`. Its alternative `JP_TROLL_CPUE` branch was not used. The response here is `log10(recruitment)` from the existing observational recruitment series.

Point predictions reuse the saved 40 GAM and 40 RF fold models under `results/observational/training/models`; no models were refit for point prediction. Each target uses its matching raw six-predictor held-out SVD row and a 39-year training fold.

GAM model variance uses `gam.confidence_intervals(..., width=0.95)` converted to variance via half-width/1.96. RF model variance uses 500 training-only bootstrap refits because `forestci` is unavailable; tree-to-tree spread was not used as a confidence interval. Data variance is the residual variance from inner five-fold CV within each outer 39-year training fold, conditional on the existing outer-fold SVD representation rather than a nested SVD recomputation.

Combined variance is `model variance + data variance`; bounds are an approximate Gaussian 95% prediction interval. Fisher-z correlation intervals are reported separately and are not prediction intervals. No recruitment-assessment uncertainty or 500 simulated recruitment realizations were included.

See `annual_predictions_uncertainty.csv`, `performance_metrics.csv`, and `validation_audit.csv`.
