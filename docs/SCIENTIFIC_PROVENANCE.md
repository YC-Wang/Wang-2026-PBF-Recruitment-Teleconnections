# Scientific provenance

## Observational SVD

The authoritative source is data/code/Fig2_LOOCV_SVD_40fold.ipynb. It uses training-only climatologies and fold-specific SVD for 1981–2020 held-out years. Predictor order is PO_PC1, AO_PC1, PO_PC2, AO_PC2, PO_PC3, AO_PC3. Archived predictor tables are validated downstream references; complete raw SST reproduction remains limited by the unrecorded xMCA version and missing permanent fold-basis metadata.

## Recruitment prediction

GAM and Random Forest models use the six predictors and 40-fold leave-one-year-out evaluation. Archived predictions and selected Table 1 rows were checked against preserved references. External observed recruitment and saved models remain required for some fresh evaluations.

## Uncertainty distinction

Figure 4 prediction intervals combine model-estimation and residual-data uncertainty. GAM conditional-mean uncertainty is derived from the fitted GAM covariance intervals. RF model-estimation uncertainty uses the archived independent implementation of the uncalibrated forestci IJ core with finite-tree bias correction; the intended direct call is `forestci.random_forest_error(..., calibrate=False)`. `calibrate=True` is not used. `forestci==0.9` is now declared and passes an isolated compatibility smoke test with the pinned NumPy/SciPy/scikit-learn stack, but archived values were not overwritten or recalibrated. Direct numerical agreement against the archived values cannot be measured from this public release because fitted RF forests and training matrices are external. Cross-validated residual/data variability is estimated separately by inner five-fold CV. Figure R1 describes GAM effective degrees of freedom. These quantities are distinct from recruitment-assessment Monte Carlo uncertainty, which is outside this release.

## Table S3

Table S3 uses archived observational reference predictors and archived DCPP predictor CSVs. Lead 1 and Lead 2 use annual member means; Lead 3–5 uses pooled member means. Correlations use 30 verification years. Bootstrap settings are retained from the validated revised workflow. The workflow does not refit SVD or preprocess raw DCPP SST.

## Corrections and limitations

Full-period standardization of DCPP ensemble-mean predictors is not accepted as verification because it uses held-out information. Exploratory DCPP sign, climatology, and member-aggregation experiments are not publication baselines. Historical Table S3 comparison values are not fabricated when the optional historical CSV is unavailable. DCPP Table S3 begins from derived predictor CSVs and does not establish raw DCPP SST reproducibility.

## Figure R1 EDF correction

The authoritative term order is PO_PC1, AO_PC1, PO_PC2, AO_PC2, PO_PC3, AO_PC3. The historical Figure R1 reporting path attached labels in a different order; the GAM fits and EDF values were unchanged. The corrected mapping is AO1 to PO_PC1, AO2 to AO_PC1, AO3 to PO_PC2, PO1 to AO_PC2, PO2 to PO_PC3, and PO3 to AO_PC3. The correction affects labels, legends, captions, and term-specific summaries only; total model EDF and residual EDF are unchanged. See the retained PHASE3C_EDF_AUDIT.md and PHASE3D_EDF_CORRECTION_REPORT.md.

## Observational leakage prevention

Each observational fold uses 39 training years. Training climatologies are used for both training and held-out anomalies, and held-out scores are projections onto the corresponding training SVD basis. The raw predictor export does not apply independent held-out standardization. The exact xMCA version and fold-level basis artifacts remain unavailable.

## Model artifacts and configuration

The retained PHASE7A_MODEL_INVENTORY.md and PHASE7A_MODEL_CHECKSUMS.csv are KEEP files. They document 40 saved GAM and 40 saved Random Forest SVD-family models, their predictor order, fold structure, configuration, environment versions, and per-file checksums. No saved RegSST or PDO/AMO model-pickle collections were located; their archived metrics must not be presented as having the same saved-model provenance.

## Final recruitment uncertainty experiment

The authoritative final experiment uses 500 mean-preserving lognormal recruitment realizations generated with `default_rng(20261102)`. Year-specific ISC period-average CVs are 0.21 for 1981–1993, 0.08 for 1994–2016, and 0.325 for 2017–2020. The active realization file is positive finite `log10(recruitment)` data with 500 IDs × 40 years and SHA-256 `A5B10B031E3C37CBC3007FC4E69959CCEAEDC59A30B2548064C3922A67E14120`. Final model-skill summaries, annual uncertainty results, Figure R2, and Table S2.1 are retained under `results/observational/recruitment_uncertainty/cv_lognormal_2026/`.

The earlier seed-123 independent-normal-draw experiment and its reports, input, predictions, figures, and diagnostics are excluded. The final CV-based products are archived scientific results; full repeated refitting remains dependent on external fitted models and approved inputs.
