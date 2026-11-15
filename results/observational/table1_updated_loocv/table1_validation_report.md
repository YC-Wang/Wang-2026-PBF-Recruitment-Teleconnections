# Updated Table 1 LOOCV validation report

Six models use the identical 1981–2020 recruitment series and `log10(recruitment)`. Regional SST and PDO+AMO were reproduced with the original supplied predictors and 40-fold `KFold(n_splits=40, shuffle=False)` LOOCV. The validated SVD rows use the current 40 held-out SVD predictor rows and the same GAM/RF configurations; no SVD model was refit in this phase.

Inputs:

- Recruitment: external approved input `observed_recruitment_1981_2020.csv` (not distributed here)
- SVD: archived `data/processed/obs_SVD_LOOCV_raw_1981_2020.csv`
- Regional SST: external approved input `SST_regional_timeseries_1981_2020.csv` (not distributed here)
- PDO+AMO: external approved input `SVD_mode_recruitment_normalize.csv` (not distributed here)

The recruitment values and years match the original Table 1 input exactly: 40 years, 1981–2020, maximum absolute difference 0.

GAM is `pygam.LinearGAM` with one `n_splines=3`, `spline_order=2` term per predictor and default regularization. RF is `RandomForestRegressor(n_estimators=1000, max_depth=5, max_features="sqrt", random_state=1)`. No tuning was used.

Metrics are Pearson r, squared mean error (MSE) on the log10 scale, and `100*np.std(y_pred, ddof=1)/np.mean(y_pred)`. RMSE was not substituted for MSE.

Regional SST and PDO/AMO predictor files are supplied precomputed series. Their upstream seasonal/index construction and any use of full-period information are outside the fold loop and cannot be verified as leakage-free from the available repository. The predictor definitions were preserved without modification. The SVD rows use fold-specific construction validated in `results/observational/table1_scale_audit.md`.

Validation: 40 predictions per model; common years and recruitment; SVD predictions reused; MSE and CV definitions verified; no existing results overwritten.
