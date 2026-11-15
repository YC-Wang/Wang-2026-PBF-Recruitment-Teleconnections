# DCPP Table 2 reproduction

This workflow reproduces Table 2 from archived member-level DCPP recruitment predictions. It does not regenerate DCPP forecasts from raw SST NetCDF files.

Run in an isolated output directory:

```text
python scripts/audit_table2_and_ensemble_metrics.py --output-dir <isolated-directory>
```

The evaluator uses 30 verification years (1981–2010), 117 members for Leads 1 and 2, and equal pooling of Leads 3–5 to 351 members per year. Predictions are annual ensemble means of log10 recruitment. Correlation intervals are paired BCa bootstrap intervals over the 30 annual values with 5,000 resamples and seed `20261107`. MSSS is `1 - model MSE / observed-mean climatology MSE`. The pooled members and lead-year pairs are not treated as independent verification cases.

Required retained inputs are the five `results/dcpp_predictions/lead*_obs_aligned_pooled_loyo/*_member_recruitment_predictions.csv` files and the approved observed recruitment input referenced by the public configuration. The archived Table 2 and annual/aggregate/CRPS metrics are under `results/dcpp_table2_revision/`.

Full DCPP preprocessing and forecast generation require external DCPP SST NetCDF files, fold-specific observational SVD bases, observed recruitment data, and saved GAM/RF model artifacts. No unverified predictor sign correction is applied by this evaluation workflow.
