# Reproduction guide

## Principles

Use the checked environment, approved external snapshots, isolated outputs, and frozen references. Never overwrite archived results. VERIFIED means an execution or numerical consistency check is recorded; PARTIAL means only a limited pathway is validated; BLOCKED means a required input or dependency is unavailable.

## Environment

    conda env create -f environment.yml
    conda activate pbf-recruitment-prediction

The original SVD notebook additionally requires the original xMCA API/version, which is not fully recorded.

## Observational commands

    python scripts/verify_observational_inputs.py --include-tracked
    python scripts/verify_table1_svd_rows.py
    python scripts/evaluate_observational_portable.py --output-dir <isolated-directory>
    python scripts/run_observational_portable.py --output-dir <isolated-directory>

The evaluation and fitting pathways require approved external recruitment, fold predictors, and model artifacts.

## Figures

    python scripts/improve_supplementary_prediction_intervals.py
    python scripts/plot_figure_R1_GAM_EDF_archived.py

## Final recruitment uncertainty

The retained experiment uses 500 mean-preserving lognormal recruitment realizations, seed `20261102`, and year-specific ISC period-average CVs: 0.21 for 1981–1993, 0.08 for 1994–2016, and 0.325 for 2017–2020.

    python scripts/reconstruct_recruitment_cv_lognormal.py

The approved final prediction, Figure R2, and Table S2.1 products are under `results/observational/recruitment_uncertainty/cv_lognormal_2026/`. Full repeated GAM/RF refitting requires the external model artifacts and approved inputs documented there; do not confuse these products with the superseded seed-123 normal-draw experiment, which is not included.

These pathways do not regenerate raw SST, recruitment realizations, fitted models, or prediction intervals.

## Table S3

Table S3 starts from archived DCPP predictor CSVs, not raw DCPP SST:

    python scripts/recalculate_table_s3b.py --output-dir <isolated-directory>

Required inputs are the five obs-aligned Lead 1–5 CSVs and data/processed/obs_SVD_LOOCV_raw_1981_2020.csv. The optional historical comparison needs a separately supplied reference CSV; without it revised statistics run normally and the comparison is skipped.

## Model and checksum records

The saved observational SVD-family model inventory and per-file checksums are retained in PHASE7A_MODEL_INVENTORY.md and PHASE7A_MODEL_CHECKSUMS.csv. These records describe external model artifacts; they are not a substitute for distributing the models or their restricted inputs. Do not claim a fresh saved-model evaluation unless the approved model snapshot is available.

## Verification boundaries

Archived-output Figure 4 and Figure R1 pathways, archived Table 1 SVD rows, Table S2.1/CV-based recruitment-uncertainty products, and the Table S3 isolated reproduction have recorded validation evidence. Raw SST/SVD preprocessing and workflows requiring external model or recruitment files remain PARTIAL, BLOCKED, or NOT TESTED. The earlier seed-123 recruitment Monte Carlo experiment is excluded.
