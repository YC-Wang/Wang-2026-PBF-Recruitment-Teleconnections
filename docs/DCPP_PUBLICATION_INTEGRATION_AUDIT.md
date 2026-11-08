# DCPP Publication Integration Audit

Date: 2026-11-09

This is a read-only audit of the DCPP scientific pipeline in
`paper-tuna-revision/`. No DCPP publication files, figures, tables, or inputs
were modified. The public checkout is on branch `integrate-dcpp-evaluation`; the
validated RF IJ changes were committed separately as `5abebb8`.

## 1. Dependency graph

```text
DCPP lead-specific SST NetCDF (117 members, OND 1981–2010)
        + observational_svd_basis_40fold/fold_YYYY.nc
        + observational_svd_basis.py::project_anomalies
        + observed recruitment 1981–2020
        + saved 40-fold observational GAM/RF models
        -> lead1/lead2/lead3/lead4/lead5 member predictors
        -> member GAM/RF recruitment predictions
        -> annual ensemble summaries and individual-lead skill
        -> pooled Leads 3–5 (351 members/year)
        -> Table 2 and ensemble annual/aggregate/CRPS metrics
```

Before the current integration, the public repository had no DCPP scripts or DCPP results directory;
so no existing public DCPP workflow can be updated in place yet.

## 2. Lead-specific workflow audit

### Lead 1

Source: `scripts/process_dcpp_lead1_ensemble_pooled_loyo.py`.

- Input: `data/processed/dcpp data/dcpp_sst/1981_2010_predict_sst_lead1_all_member_lead1.nc`.
- Requires 30 years, 117 unique members, October–December fields, and the
  archived fold-specific observational bases.
- Builds an ensemble-pooled leave-one-verification-year-out climatology by
  excluding all 117 members from the target year and pooling the remaining
  29×117 year-member fields with valid-value counts.
- Projects Pacific and Atlantic anomalies onto the archived fold-specific basis
  using linear interpolation and `project_anomalies()`.
- Produces 3,510 predictor records: 30 years × 117 members.
- The script records `initialization_year` as unknown/unverified and omits it.
- Its validation report says no additional scaling or sign adjustment was used.
- It then uses the saved observational fold models for member-level GAM/RF
  predictions and writes annual ensemble summaries and skill diagnostics.

### Lead 2

Source: `scripts/process_dcpp_lead2_pipeline.py`.

- Input: `data/processed/dcpp data/dcpp_sst/1981_2010_predict_sst_lead1_all_member_lead2.nc`.
- Uses the same 30-year, 117-member, pooled LOYO and fold-specific basis
  projection framework as Lead 1.
- Loads `gam_fold_01.pkl`–`gam_fold_30.pkl` and
  `rf_fold_01.pkl`–`rf_fold_30.pkl` from the external observational model archive.
- Produces 3,510 member-level predictor/prediction records and annual summaries.
- Uses `numpy.random.default_rng(20261106)` for its 5,000 correlation-bootstrap
  diagnostic; this does not alter member predictions.

### Leads 3–5

Sources: `scripts/process_dcpp_lead3_pipeline.py`,
`process_dcpp_lead4_pipeline.py`, and `process_dcpp_lead5_pipeline.py`.

These are thin wrappers around the Lead 2 implementation, replacing the lead
identifier and source/output paths. They therefore inherit the same 117-member
handling, 30 verification years, fold-specific observational basis projection,
saved-model dependency, and model-prediction procedure. The wrapper approach is
reproducible but should be reviewed before publication because it relies on
source-text substitution rather than a shared callable pipeline.

Aggregation source: `scripts/combine_leads3_5_predictions.py`.

- Reads the saved member-prediction CSVs for Leads 3, 4, and 5.
- Requires 3,510 records per lead and 351 predictions per verification year
  after pooling.
- Produces annual pooled means, medians, standard deviations, 5th and 95th
  percentiles, and detrended skill diagnostics for 1981–2010.
- The 351-member envelope is empirical ensemble spread, not a calibrated
  prediction interval.

## 3. Table 2 audit

Producer: `scripts/audit_table2_and_ensemble_metrics.py`.

Inputs are the archived member-level prediction CSVs for Leads 1–5 plus the
observed recruitment series. Table 2 evaluates 30 annual verification values:

- Lead 1: 117-member ensemble distribution, evaluated on annual ensemble means.
- Lead 2: 117-member ensemble distribution, evaluated on annual ensemble means.
- Leads 3–5: pooled 351-member distribution, evaluated on annual pooled means.
- Models: GAM and RF.
- Correlation: Pearson correlation between observed and annual ensemble-mean
  log10 recruitment.
- Correlation intervals: paired BCa bootstrap over the 30 verification years,
  with 5,000 resamples in the revised producer.
- MSSS: `1 - model_MSE / observed-mean-climatology_MSE`.

Archived revised rows are in
`results/dcpp_table2_revision/table2_revised.csv`:

| Model | Lead 1 r | Lead 1 MSSS | Lead 2 r | Lead 2 MSSS | Leads 3–5 r | Leads 3–5 MSSS |
|---|---:|---:|---:|---:|---:|---:|
| GAM | 0.47225 | 0.21230 | 0.51347 | 0.24660 | 0.53805 | 0.26103 |
| RF | 0.43556 | 0.12346 | 0.41347 | 0.10473 | 0.49593 | 0.12895 |

The table can be reproduced numerically from archived member-prediction files,
but a fresh end-to-end run additionally requires the excluded raw DCPP inputs,
observational recruitment data, fold-specific bases, and saved models.

## 4. Supplementary ensemble verification

The archived files are:

- `ensemble_annual_metrics.csv`: one row per lead group, model, and year,
  containing ensemble mean/median, sample standard deviation, 5th/95th
  percentiles, CRPS, reference CRPS, coverage, and observed value; aggregate
  rows are appended.
- `ensemble_aggregate_metrics.csv`: aggregate rows containing mean CRPS,
  CRPSS, 90% empirical coverage, mean 90% width, Pearson r, RMSE, MSE, bias,
  detrended r, and first-difference r.
- `ensemble_crps_reference.csv`: annual rows retaining the same CRPS and
  reference-forecast fields for auditability.

CRPS is calculated from the sorted ensemble member values using the empirical
sample formula. The reference forecast is a leave-target-year-out observed
climatological distribution, constructed from the other 29 observed years.
CRPSS is `1 - mean_ensemble_CRPS / mean_reference_CRPS`. Annual and aggregate
metrics are aligned to verification years 1981–2010. Lead 1 and Lead 2 use 117
members; pooled Leads 3–5 use 351 members.

## 5. Provenance and scientific limitations

The final lead-specific outputs are observational-basis-aligned: they load
archived observational fold bases and project DCPP anomalies into those bases.
The scripts state that no new SVD, scaling, or sign adjustment is applied.
However:

- The DCPP initialization year is unknown/unverified and is omitted from the
  metadata.
- The source validation status is explicitly
  `no_verified_correction_available` for the fold-consistent predictor audit.
- Available pattern files do not encode fold-specific climatology, spatial
  weighting, normalization, or sign metadata.
- Member predictor files do not carry the complete fold-basis provenance.
- The Lead 3–5 wrappers inherit Lead 2 by text substitution and should be
  independently reviewed before being treated as a publication-grade API.
- Experimental sign-reversal, supplied-sign, and sign-diagnostic scripts must
  not be integrated as corrections. No sign correction is recommended by this
  audit.

Classification: the archived prediction and metric outputs are reproducible
from processed predictions; fresh scientific regeneration requires external
datasets/models; fold-basis and initialization provenance remain scientifically
unresolved.

## 6. Minimal public integration plan

Do not create a parallel DCPP structure. After provenance review, use the
existing public directories:

1. Add only the necessary lead-specific scripts under `scripts/`.
2. Add approved processed member-prediction CSVs under `data/processed/`.
3. Add Table 2 and ensemble metric CSVs under `results/`.
4. Add one public DCPP workflow document under `docs/` describing external
   inputs and the no-sign-correction status.
5. Reuse the existing public `data/processed/recruitment.csv` only after
   confirming it is the approved observational series and compatible with the
   source 1981–2010 log10 values.
6. Do not copy raw DCPP NetCDF files, restricted saved models, or unverified
   sign-correction experiments.

Acceptance tests should include:

- 30 verification years for every lead, 117 members per individual lead, and
  351 members for pooled Leads 3–5.
- No duplicate `(verification_year, member, lead)` records.
- Exact six-predictor order and finite fold-specific projections.
- Exact match to archived member-level predictions before regenerating Table 2.
- Exact Table 2 rows within documented floating-point tolerance.
- CRPS, reference CRPS, CRPSS, coverage, and year alignment match archived
  ensemble metrics.
- No sign transformation is applied unless separately verified and approved.

## 7. Reproduction command shape

The source workflow currently requires external paths under the working
repository and is not directly runnable from the public checkout. The eventual
public workflow should expose repository-relative commands equivalent to:

```powershell
python scripts/process_dcpp_lead1_ensemble_pooled_loyo.py
python scripts/process_dcpp_lead2_pipeline.py
python scripts/process_dcpp_lead3_pipeline.py
python scripts/process_dcpp_lead4_pipeline.py
python scripts/process_dcpp_lead5_pipeline.py
python scripts/combine_leads3_5_predictions.py
python scripts/audit_table2_and_ensemble_metrics.py
python scripts/create_table2_docx.py
```

These commands should not be published as self-contained until the external
input/model manifest and sign/basis provenance are resolved.

## Recommended sequence

1. Review and approve the committed RF IJ branch.
2. Resolve DCPP fold-basis, sign/orientation, and initialization metadata.
3. Obtain approved external-input/model manifests without copying restricted
   data into the public repository.
4. Port only the minimal DCPP scripts and archived outputs into existing public
   directories.
5. Validate predictions, Table 2, and ensemble metrics against the archived
   source outputs in isolated directories.
6. Only then consider a separate DCPP integration commit and pull request.
