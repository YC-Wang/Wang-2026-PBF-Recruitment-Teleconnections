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
    python scripts/plot_recruitment_uncertainty_log10.py

These pathways do not regenerate raw SST, recruitment realizations, fitted models, or prediction intervals.

## Recruitment uncertainty

    python scripts/run_recruitment_uncertainty_portable.py --n-samples 5 --output-dir <isolated-directory>

The full 500-realization workflow is not independently rerun in this publication environment.

## Table S3

Table S3 starts from archived DCPP predictor CSVs, not raw DCPP SST:

    python scripts/recalculate_table_s3b.py --output-dir <isolated-directory>

Required inputs are the five obs-aligned Lead 1–5 CSVs and data/processed/obs_SVD_LOOCV_raw_1981_2020.csv. The optional historical comparison needs a separately supplied reference CSV; without it revised statistics run normally and the comparison is skipped.

## Model and checksum records

The saved observational SVD-family model inventory and per-file checksums are retained in PHASE7A_MODEL_INVENTORY.md and PHASE7A_MODEL_CHECKSUMS.csv. These records describe external model artifacts; they are not a substitute for distributing the models or their restricted inputs. Do not claim a fresh saved-model evaluation unless the approved model snapshot is available.

## Verification boundaries

Archived-output Figure 4 and Figure R1 pathways, archived Table 1 SVD rows, the Table S3 isolated reproduction, and the documented five-realization smoke test have recorded validation evidence. Raw SST/SVD preprocessing, the complete 500-realization run, and workflows requiring external model or recruitment files remain PARTIAL, BLOCKED, or NOT TESTED as indicated by the relevant result README.
