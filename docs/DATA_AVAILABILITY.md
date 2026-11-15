# Data availability

## Included

The repository includes archived observational predictor tables, derived observational predictions, figures, tables, diagnostics, environment specifications, and the approved derived DCPP predictor CSVs required for Table S3.

## External or restricted

Original SST NetCDF data, observed recruitment extracted from the ISC assessment source, saved GAM/RF model artifacts, exact xMCA dependencies, and upstream DCPP source data may require separate acquisition or permission. The final CV-based realization input and derived outputs are included as approved archived artifacts; the earlier seed-123 Monte Carlo input and outputs are excluded.

Table S3 uses archived derived DCPP predictor CSVs. It does not reproduce or redistribute raw DCPP SST through the Table S3 workflow.

## Recruitment source

Observed recruitment is sourced from ISC (2022), Stock assessment of Pacific bluefin tuna in the Pacific Ocean in 2022, Figure 5-14, page 135. Source page: https://meetings.wcpfc.int/node/16246. Public accessibility does not establish redistribution permission.

## Licensing

See LICENSE and CITATION.cff. Third-party climate, SST, recruitment, and DCPP data retain their original terms. No repository license overrides upstream restrictions. Confirm redistribution rights before packaging external data or model artifacts.

## Reproducibility implications

Archived figures and derived tables do not imply that all upstream data are publicly available. Figure 4 distinguishes GAM conditional-mean uncertainty, RF IJ estimation uncertainty, and cross-validated residual/data variability. The final recruitment-assessment uncertainty experiment is a separate CV-based lognormal workflow with its own archived realizations and summaries. See docs/REPRODUCE.md.
