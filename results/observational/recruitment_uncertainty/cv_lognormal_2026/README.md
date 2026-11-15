# Final CV-based recruitment uncertainty

This directory contains the authoritative final recruitment-assessment uncertainty experiment. It uses 500 mean-preserving lognormal realizations generated with seed `20261102`, year-specific ISC period-average CVs, and the existing 40-fold GAM/RF LOOCV framework.

The active input is `data/raw/Y_sim_500_samples.csv` (500 realization IDs × 40 years, positive finite `log10(recruitment)` values). Final prediction summaries, annual uncertainty results, Figure R2 products, and Table S2.1 products are retained here. The sampling audit and `validation.json` record the CV assignment and reproducibility checks.

Reconstruct the realization input with:

    python scripts/reconstruct_recruitment_cv_lognormal.py

The full repeated refitting experiment requires approved external fitted models and inputs. Archived products do not claim a fresh rerun in this public environment. The earlier seed-123 independent-normal-draw experiment and its reports, inputs, predictions, figures, and diagnostics are excluded.
