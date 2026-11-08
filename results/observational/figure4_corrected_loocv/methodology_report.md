# Corrected Figure 4 observational LOOCV

The original visual reference was `data/code/original_draft/GAM_RF_predicted.ipynb`. Its alternative `JP_TROLL_CPUE` branch was not used. This public reproduction consumes the archived annual prediction table and archived IJ variance table; it does not require the external fitted models for ordinary figure regeneration.

Point predictions reuse the saved 40 GAM and 40 RF fold models under `results/observational/training/models`; no models were refit for point prediction. Each target uses its matching raw six-predictor held-out SVD row and a 39-year training fold.

GAM model variance is retained from the archived corrected workflow. RF model-estimation variance is the validated uncalibrated forestci IJ core with finite-tree bias correction, archived by year in `annual_ij_vs_bootstrap.csv`; stochastic forestci `calibrate=True` calibration was not reproduced. RF data variance is retained from the existing inner five-fold CV results.

Combined variance is `model variance + data variance`; bounds are an approximate Gaussian 95% prediction interval. Fisher-z correlation intervals are reported separately and are not prediction intervals. No recruitment-assessment uncertainty or 500 simulated recruitment realizations were included.

See `annual_predictions_uncertainty.csv`, `annual_ij_vs_bootstrap.csv`, `rf_ij_validation_summary.json`, `performance_metrics.csv`, and `validation_audit.csv`.
