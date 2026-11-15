# Recruitment-assessment uncertainty

## Scientific question

This workflow evaluates propagation of recruitment-assessment uncertainty into recruitment predictions and model skill.

## Methodology

Recruitment realizations use the documented CV-based lognormal procedure. GAM and Random Forest models are refit over the leave-one-year-out workflow for each realization. The full experiment uses preserved 500-realization products; smaller runs are smoke tests or convergence checks. This is distinct from Figure 4 prediction intervals and Figure R1 complexity diagnostics.

## Outputs and results

Outputs include Figure R2 products, Table S2.1 summaries, predictions_500.csv, annual_uncertainty_summary.csv, skill_metrics_500.csv, convergence diagnostics, and run metadata. The archived products summarize spread and skill variability across sampled assessments; they are not DCPP forecasts or calibrated prediction intervals.

The release retains the authoritative archived Figure R2 log10 PNG/PDF and caption, plus `monte_carlo_convergence.csv` and `skill_uncertainty_summary.csv` supporting the Table S2.1 uncertainty-validation record. These files preserve the manuscript evidence even though regeneration is blocked by external observed-recruitment and realization inputs. The retained products must not be described as a fresh rerun of the 500-realization fitting experiment.

## Reproduction

    python scripts/run_recruitment_uncertainty_portable.py --n-samples 5 --output-dir <isolated-directory>
    python scripts/plot_recruitment_uncertainty_log10.py

The full experiment requires approved external recruitment input and realization provenance. Do not overwrite archived products.

## Validation and limitations

The five-realization smoke test was checked. The full 500-realization workflow was not independently rerun in the publication environment. Fixed realization inputs, observed recruitment, model artifacts, and permissions may be external or restricted. See docs/SCIENTIFIC_PROVENANCE.md and docs/DATA_AVAILABILITY.md.

The preserved methodology records positive log10 recruitment realization inputs, independent annual normal draws with year-specific standard deviations, and seed 123 in the source procedure. The workflow fits the supplied values directly and back-transforms predictions; it does not apply a second log transform. Annual independence and unknown joint assessment-error structure are limitations.
