# Portable observational workflow

Set `PBF_DATA_ROOT` to a read-only immutable snapshot containing the paths in `configs/observational_paths.toml`. Verify before calculation:

```powershell
python scripts/verify_observational_inputs.py --include-tracked
```

Level 3 preprocessing retains the reference implementation `jupyternotebook/Fig2_LOOCV_SVD_40fold.ipynb` and remains blocked pending original SST, basis provenance, and xMCA. Level 2 delegates unchanged to `src.pbf.observational.run_training`:

```powershell
python scripts/run_observational_portable.py --output-dir $env:TEMP\pbf-observational-reproduction
```

The command preserves 40 folds, 39 training years, six-predictor order, log10 recruitment, GAM defaults, RF seed 1, and RF configuration. It writes only to the explicitly supplied isolated directory. Level 1 uses archived predictions and existing plotting/export scripts, with new temporary output paths; review those scripts before execution because they were historically notebook-centered.

The saved-model evaluation command is `python scripts/evaluate_observational_holdout.py`; it does not refit models or recalculate SVD, but the legacy script writes to `results/observational/holdout_svd_evaluation`, so isolate or review that output destination before execution. The corrected prediction-interval workflow is `scripts/reproduce_figure4_corrected.py` or the documented Figure 4 notebook; it is computationally substantial and must not target frozen reference outputs without approval.

For the fixed saved realizations, the permitted lightweight command is:

```powershell
python scripts/run_recruitment_uncertainty_loocv.py --n-samples 5 --n-workers 1 --smoke --output-root $env:TEMP\pbf-uncertainty-smoke
```

The complete command is `python scripts/run_recruitment_uncertainty_loocv.py --n-samples 500 --n-workers 8 --resume`, but it is not permitted in Phase 2B. It consumes the saved realization CSV and does not regenerate it. Generation provenance remains pending integration.

The prediction-interval workflow and 500-realization recruitment-assessment uncertainty workflow remain separate. No expensive command was run in Phase 2B.

