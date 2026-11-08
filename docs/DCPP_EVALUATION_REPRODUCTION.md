# DCPP Table 2 and Ensemble Verification

This public workflow evaluates the archived, validated member-level DCPP
predictions. It does not regenerate DCPP forecasts from raw SST NetCDF files.

## Reproduction

From the repository root:

```powershell
python scripts/audit_table2_and_ensemble_metrics.py
```

For isolated validation, use `--output-dir <temporary-directory>`.

The command reads `data/processed/recruitment.csv` and the five archived files
under `results/dcpp_predictions/`. It writes Table 2 and ensemble verification
outputs under `results/dcpp_table2_revision/`.

## Evaluation definition

- Verification years: 1981–2010 (30 years).
- Individual leads: 117 members per year.
- Leads 3–5: equal member pooling, 351 members per year (117 from each lead).
- Table 2: Pearson correlation of observed and annual ensemble-mean log10
  recruitment; paired BCa bootstrap confidence intervals over the 30 years,
  5,000 resamples, seed `20261107`.
- MSSS: `1 - model_MSE / observed_mean_climatology_MSE`.
- CRPS: empirical member-distribution CRPS for each year.
- Reference CRPS: leave-one-year-out observed log10-recruitment distribution.
- CRPSS: `1 - mean_ensemble_CRPS / mean_reference_CRPS`.
- Ensemble spread: sample standard deviation and empirical 5th–95th percentiles.

## Provenance and limitations

The archived predictions use observational SVD bases without an additional sign
correction. Complete fold-specific SVD/sign metadata and forecast initialization
year provenance remain unresolved. Fresh forecast generation requires external
DCPP SST NetCDF inputs, fold-specific basis files, observed recruitment data,
and saved observational GAM/RF models; this repository does not claim to
regenerate raw DCPP forecasts independently.

The five prediction-file SHA-256 checksums and the full provenance audit are in
`docs/DCPP_PUBLICATION_INTEGRATION_AUDIT.md` in the source audit record.
