# DCPP Table 2 reproduction

This workflow reproduces Table 2 from archived member-level DCPP recruitment predictions. It does not regenerate DCPP forecasts from raw SST NetCDF files.

Run in an isolated output directory:

```text
python scripts/audit_table2_and_ensemble_metrics.py --output-dir <isolated-directory>
```

The evaluator uses 30 verification years (1981–2010), 117 members for Leads 1 and 2, and equal pooling of Leads 3–5 to 351 members per year. Predictions are annual ensemble means of log10 recruitment. Correlation intervals are paired BCa bootstrap intervals over the 30 annual values with 5,000 resamples and seed `20261107`. MSSS is `1 - model MSE / observed-mean climatology MSE`. The pooled members and lead-year pairs are not treated as independent verification cases.

Required retained inputs are the five `results/dcpp_predictions/lead*_obs_aligned_pooled_loyo/*_member_recruitment_predictions.csv` files and the approved observed recruitment input referenced by the public configuration. The archived Table 2 and annual/aggregate/CRPS metrics are under `results/dcpp_table2_revision/`.

## Archived predictor provenance

The five observational-SVD-projected predictor files used for the DCPP analysis are archived under `results/dcpp_predictions/svd_predictors/lead1/` through `lead5/`. Each lead contains 3,510 member-year rows for 1981–2010, with 117 members and the six predictors `PO_PC1`, `AO_PC1`, `PO_PC2`, `AO_PC2`, `PO_PC3`, and `AO_PC3`. The final analysis applies no additional predictor sign correction.

These derived files are attributed to the CMIP6 Decadal Climate Prediction Project (DCPP); see the [official CMIP6 DCPP webpage](https://www.wcrp-climate.org/dcpp) and [CMIP6 Terms of Use v6.2](https://pcmdi.llnl.gov/CMIP6/TermsOfUse/TermsOfUse6-2.html). Dataset-specific source identifiers, DOI/version/variant metadata, and current per-model license records were not recovered, so dataset-specific license verification is not independently verified in this archive. The files are included under the current release decision with that provenance limitation; users must confirm applicable upstream terms before further redistribution.

The archived member-level recruitment predictions, archived SVD predictors, and Table 2 evaluation are distinct release components. Generating either the predictors from raw DCPP SST or fresh recruitment forecasts requires external upstream data and model artifacts and is outside this archived-input workflow.

Full DCPP preprocessing and forecast generation require external DCPP SST NetCDF files, fold-specific observational SVD bases, observed recruitment data, and saved GAM/RF model artifacts. No unverified predictor sign correction is applied by this evaluation workflow.
