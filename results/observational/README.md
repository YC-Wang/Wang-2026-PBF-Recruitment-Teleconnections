# Observational results

## Scope

This directory contains retained observational outputs for the recruitment prediction manuscript: Table 1, Figure 4, Figure R1, archived held-out predictions, diagnostics, and model-configuration summaries.

## Methodology

Predictors use fold-specific SST/SVD processing over 1981–2020. GAM and Random Forest models use 40-fold leave-one-year-out cross-validation. Figure 4 separates GAM conditional-mean uncertainty, RF infinitesimal-jackknife estimation uncertainty, and cross-validated residual/data variability. Figure R1 summarizes GAM effective degrees of freedom. The final recruitment-assessment experiment is a separate CV-based lognormal workflow.

## Results and interpretation

Archived Table 1 SVD rows, Figure 4 uncertainty products, and corrected Figure R1 EDF values are retained in existing result files and reports. These outputs describe the observational workflow and do not establish DCPP prediction skill.

The retained Figure 4 validation artifacts include `annual_ij_vs_bootstrap.csv`, `rf_ij_validation_summary.json`, `performance_metrics.csv`, `point_prediction_unchanged_comparison.csv`, the supplementary GAM/RF interval CSVs, and the methodology report. Together they document the RF infinitesimal-jackknife comparison, combined uncertainty coverage, and unchanged point predictions. They are archived validation evidence; they are not a new numerical result.

## Reproduction

See docs/REPRODUCE.md. Relevant commands are scripts/verify_table1_svd_rows.py, scripts/improve_supplementary_prediction_intervals.py, and scripts/plot_figure_R1_GAM_EDF_archived.py. Saved-model evaluation and fresh fitting require approved external inputs and isolated outputs.

## Validation and limitations

Archived Figure 4 and Figure R1 pathways are validated, and archived Table 1 SVD rows were checked against preserved held-out predictions. Full SST/SVD preprocessing has not been independently rerun with a recorded xMCA environment. Raw recruitment and saved models remain external or restricted.
