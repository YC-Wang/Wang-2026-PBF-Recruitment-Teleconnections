# Baseline validation

Re-fitted each saved fold with the original observed log10 responses and raw held-out SVD predictors. Tolerance for mismatch count: 1e-10 log10 units. GAM uses direct `.fit()` with default pyGAM lam; RF uses the repository RF configuration.

model  max_abs  mean_abs  rmse  mismatched_folds
  GAM      0.0       0.0   0.0                 0
   RF      0.0       0.0   0.0                 0