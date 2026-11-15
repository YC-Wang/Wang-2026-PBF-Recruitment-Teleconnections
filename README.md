# Pacific Bluefin Tuna Recruitment

## Study objective

This repository supports reproducible analysis of Pacific bluefin tuna recruitment variability and its relationships with large-scale ocean–atmosphere teleconnections.

## Scientific methodology

The observational workflow uses October–December SST from fixed Pacific and Atlantic domains. For each held-out year in 1981–2020, anomalies and a coupled SVD basis are fitted using training years only; the held-out year is projected onto that fold-specific basis. The six predictors are PO_PC1, AO_PC1, PO_PC2, AO_PC2, PO_PC3, and AO_PC3.

Recruitment prediction uses GAM and Random Forest models with leave-one-year-out cross-validation. Prediction uncertainty combines model-estimation uncertainty with cross-validated residual variability. GAM conditional-mean uncertainty, RF infinitesimal-jackknife estimation uncertainty, cross-validated residual/data variability, and the final CV-based recruitment-assessment uncertainty experiment are separate quantities.

Table S3 calculates correlations between observational held-out SVD predictors and archived DCPP predictor CSVs. Table S3 reproduction starts from archived DCPP predictor CSVs, not raw DCPP SST, and does not reproduce DCPP SST preprocessing.

## Repository navigation

- [configs](configs/): observational configuration.
- [data](data/): notebooks, predictors, and processed inputs.
- [docs](docs/): reproduction, provenance, data, and diagnostics.
- [results](results/): retained figures, tables, and diagnostics.
- [Figure 1 notebook](jupyternotebook/Fig1_PBF_correlation.ipynb), [Figure 2 notebook](jupyternotebook/Fig2_LOOCV_SVD_40fold.ipynb), [Figure 3 notebook](jupyternotebook/Fig3_SVD_SST_CHL_correlation.ipynb), and [Table 1 notebook](jupyternotebook/Table1_PDOAMO_region.ipynb): original manuscript entry points.
- [results/observational](results/observational/): observational outputs.
- [results/dcpp_table_s3b_revision](results/dcpp_table_s3b_revision/): Table S3.
- [scripts](scripts/): verification and reproduction entry points.
- [src](src/): reusable code.
- [tests](tests/): lightweight checks.

## Environment and reproduction

Read [docs/REPRODUCE.md](docs/REPRODUCE.md) before running workflows.

    conda env create -f environment.yml
    conda activate pbf-recruitment-prediction

    python scripts/verify_observational_inputs.py --include-tracked
    python scripts/verify_table1_svd_rows.py
    python scripts/evaluate_observational_portable.py --output-dir <isolated-directory>
    python scripts/reconstruct_recruitment_cv_lognormal.py
    python scripts/recalculate_table_s3b.py --output-dir <isolated-directory>

Use isolated output directories and never overwrite archived references.

## Figures and tables

See [results/observational/README.md](results/observational/README.md) for observational outputs, [results/observational/recruitment_uncertainty/cv_lognormal_2026](results/observational/recruitment_uncertainty/cv_lognormal_2026) for the final CV-based uncertainty experiment, and [results/dcpp_table_s3b_revision/README.md](results/dcpp_table_s3b_revision/README.md) for Table S3.

Complete DCPP recruitment prediction, Table 2, CRPS/CRPSS verification, Figure S3.1, and unrelated DCPP experiments are outside this publication workflow.

## Data availability

Archived derived predictors and reference outputs are included where permitted. Original SST, observed recruitment, saved model artifacts, and some DCPP source data may require separate acquisition or permission. The final recruitment-uncertainty experiment uses ISC period-average CVs with mean-preserving lognormal sampling; earlier Monte Carlo artifacts are excluded. See [docs/DATA_AVAILABILITY.md](docs/DATA_AVAILABILITY.md).

## Citation and license

See [CITATION.cff](CITATION.cff) and [LICENSE](LICENSE). Third-party data retain their original terms. Repository DOI and final manuscript citation should be added when available.
