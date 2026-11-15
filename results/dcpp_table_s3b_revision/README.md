# Table S3 reproduction

## Methodology

Table S3 reports Pearson correlations between observational held-out SVD predictors and archived DCPP predictor ensembles for 1981–2010. Lead 1 and Lead 2 use annual means of 117 member predictors. Lead 3–5 pools 351 member predictors per year. Predictors are PO_PC1, AO_PC1, PO_PC2, AO_PC2, PO_PC3, and AO_PC3. The historical paired percentile bootstrap uses 1,000 resamples with seed 42; additional BCa intervals use 5,000 paired resamples with seed 20261107. No rescaling, sign adjustment, SVD refitting, or DCPP preprocessing occurs here.

Reproduction begins from archived DCPP predictor CSVs, not raw DCPP SST.

## Inputs and command

Required inputs are the five Lead 1–5 files under data/processed/dcpp data/all_member_predictor_obs_aligned_v1/ and the existing observational reference data/processed/obs_SVD_LOOCV_raw_1981_2020.csv.

    python scripts/recalculate_table_s3b.py --output-dir <isolated-directory>

An optional historical reference may be supplied with --historical-reference. If absent, revised statistics run and only the original-versus-revised comparison is skipped.

## Results and interpretation

The frozen reference is table_s3b_revised.csv. The pooled Lead 3–5 results show the strongest positive associations for AO_PC1 and PO_PC1; remaining mode correlations are weaker. These are predictor-correlation summaries, not recruitment predictions or calibrated uncertainty intervals.

## Validation and limitations

The five inputs match approved SHA-256 checksums and contain 30 years with 117 members per year. The observational reference is reused unchanged. Isolated reproduction matches the frozen reference byte-for-byte. This workflow does not reproduce DCPP SST preprocessing or observational SVD projection; upstream provenance, licensing, and compatibility require separate documentation.
