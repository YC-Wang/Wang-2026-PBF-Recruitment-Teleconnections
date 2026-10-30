# Observational GAM/RF diagnostics

This workflow analyzes only the current 40-fold SVD training dataset. It does not compare with the original repository and does not calculate held-out predictive skill.

Run:

```powershell
python -m workflows.observational.diagnostics --svd-csv data/raw/all_40folds_39years_PO_AO_PCs_1981_2020.csv --recruitment-csv data/raw/observed_recruitment_1981_2020.csv --output-dir results/observational/diagnostics
```

GAM EDF is extracted from pyGAM `statistics_["edof"]`, which is an effective degree of freedom for each fitted coefficient. The reported total includes the intercept; term EDF is aggregated through pyGAM's coefficient-index mapping. Effective residual df is `n - total_EDF`.

RF sensitivity uses 100, 200, 500, and 1,000 trees with all other settings fixed and `random_state=1`. Fits are sequential to avoid nested parallelization. The 1,000-tree configuration remains the baseline.

These diagnostics validate fold structure, numerical inputs, model complexity, stability, and reproducibility. They cannot establish leakage-free SVD fitting because the fold-specific SVD calculation and preprocessing records are not available.
