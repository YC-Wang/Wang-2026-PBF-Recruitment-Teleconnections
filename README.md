# Wang-2026-PBF-Recruitment-Teleconnections

Pacific Bluefin Tuna Recruitment: Observational SVD and GAM/RF Reproducibility

This repository accompanies a manuscript submitted to *Ecological Informatics* on Pacific bluefin tuna recruitment variability and its relationships with large-scale ocean–atmosphere teleconnections. It provides code and supporting materials for the observational SVD-based recruitment analyses, GAM/RF leave-one-out cross-validation, and associated figures and tables. DCPP hindcast and prediction analyses are not included.

## Repository contents

```text
configs/                         Portable observational path configuration
jupyternotebook/                 Authoritative SST/SVD notebook
data/processed/                  Validated predictors and archived numerical inputs
docs/                           Observational diagnostic documentation
results/observational/           Archived figures, tables, predictions, and uncertainty summaries
scripts/                         Verification, evaluation, plotting, and workflow entry points
src/                             Reusable observational code
tests/                           Lightweight reproducibility tests
```

Important scripts include `scripts/verify_observational_inputs.py`, `scripts/evaluate_observational_portable.py`, `scripts/run_observational_portable.py`, `scripts/improve_supplementary_prediction_intervals.py`, and `scripts/run_recruitment_uncertainty_portable.py`.

## Data requirements and availability

Included in this repository are validated six-predictor SVD CSVs, archived observational predictions and interval inputs, finalized observational figures/tables, and provisionally included derived recruitment-uncertainty summaries.

The following are external or excluded from this release candidate:

- Original SST NetCDF input; obtain it from an appropriately licensed source.
- Observed recruitment input; obtain the permitted source snapshot.
- Fixed `data/raw/Y_sim_500_samples.csv`; included provisionally in this local release pending redistribution/reuse clearance.
- Saved GAM/RF fold models; required for exact saved-model evaluation, but excluded pending distribution approval.
- Exact original xMCA package/version; the authoritative notebook requires `xmca.xarray.xMCA`, but its version is not recorded.
- DCPP hindcast and prediction inputs, scripts, and experiments are outside the scope of this observational-only repository.

Do not infer that archived figures imply that excluded upstream inputs are publicly available.

The fixed realization file is included provisionally for local workflows. Redistribution and public release remain pending final reuse clearance.

## Data and model availability

GitHub contains the observational reproducibility scripts, validated six-predictor SVD predictors, archived numerical outputs, and the relevant manuscript figures and tables. It does not contain the fitted observational model objects.

The planned Zenodo archive is intended to host the 80 saved observational LOOCV models from the internal verified snapshot, subject to redistribution approval:

- 40 GAM files: `gam_fold_01.pkl` through `gam_fold_40.pkl`
- 40 RF files: `rf_fold_01.pkl` through `rf_fold_40.pkl`
- Format: Python pickle (`.pkl`), stored under the snapshot's `results/observational/training/models/` directory.

Each numbered GAM/RF pair corresponds to one of the 40 leave-one-year-out folds covering 1981–2020. Fold `01` holds out 1981, fold `02` holds out 1982, and so on through fold `40`, which holds out 2020. The models are the saved fold-specific fitted objects used by the observational evaluation workflow; they are not 80 independent scientific experiments.

**Future Zenodo DOI:** `TODO — to be assigned after the archive is created and made public.` No Zenodo deposit currently exists, and these model files should not be treated as publicly available until the archive and its reuse terms are confirmed.

Figure R1 does not require downloading the fitted models: `python scripts/plot_figure_R1_GAM_EDF_archived.py` regenerates the figure from the included validated EDF CSV files. Recomputing EDF directly from fitted models requires the planned model archive.

External model-loading instructions must use only trusted model files. Python pickle files can execute arbitrary code when loaded; never load an untrusted `.pkl` file. Reproduction may also require compatible Python, pyGAM, scikit-learn, joblib, NumPy, and related package versions.

## Software

The checked environment specifies Python 3.10.14, NumPy 2.2.6, pandas 2.3.3, SciPy 1.15.3, scikit-learn 1.7.2, joblib 1.6.0, pyGAM 0.12.0, xarray, netCDF4, matplotlib, Jupyter, pytest, and tomli. Create it with:

```powershell
conda env create -f environment.yml
conda activate pbf-recruitment-prediction
```

The original SST/SVD notebook additionally requires the original xMCA package/API. The exact xMCA version and numerical environment are unresolved; no substitute SVD implementation is claimed equivalent.

## Observational SST/SVD predictors

The reference implementation for the observational 40-fold SST–SST SVD analysis is `jupyternotebook/Fig2_LOOCV_SVD_40fold.ipynb`. It is provided for provenance and optional preprocessing reproduction; it is not required to reproduce the downstream GAM/RF results from the archived predictor CSVs. It selects 1981–2020 October–December SST, extracts fixed Pacific and Atlantic domains, computes training-only anomalies for each of 40 held-out years, fits a fold-specific coupled SVD basis, and projects the held-out year onto that training basis. The six predictor order is: `PO_PC1, AO_PC1, PO_PC2, AO_PC2, PO_PC3, AO_PC3`.

The notebook is preserved unchanged and has not been independently rerun in the publication environment. The validated predictor CSVs are provided as archived endpoints. Execution requires separately obtained SST data, the original xMCA environment, and local path configuration.

## Observational GAM/RF and Table 1

Set `PBF_DATA_ROOT` to a read-only snapshot containing the documented external inputs and models. First verify paths without running scientific calculations:

```powershell
$env:PBF_DATA_ROOT = "<path-to-approved-snapshot>"
python scripts/verify_observational_inputs.py --include-tracked
```

Run saved-model evaluation into an isolated output directory:

```powershell
python scripts/evaluate_observational_portable.py --output-dir "$env:TEMP\pbf-observational-evaluation"
```

This requires the external recruitment input, fold predictors, and saved models. The saved-model observational predictions were independently verified in the development workflow. The portable refit workflow is:

```powershell
python scripts/run_observational_portable.py --output-dir "$env:TEMP\pbf-observational-reproduction"
```

This is a model-fitting workflow and may be computationally substantial. Do not write into frozen reference directories.

The archived SVD teleconnection rows of Table 1 are:

| Predictors | Model | r | MSE | CV (%) |
|---|---|---:|---:|---:|
| SVD teleconnection indices | GAM | 0.6765 | 0.026840 | 2.4641 |
| SVD teleconnection indices | RF | 0.6676 | 0.027244 | 1.8382 |

These metrics use `log10(recruitment)` predictions. Pearson `r` and MSE are calculated on paired log10 values. Historical CV is not RMSE or an uncertainty interval; it is:

```text
100 × SD(predictions, ddof=1) / mean(predictions)
```

The archived Table 1 values are included for reference; a fresh calculation still requires excluded recruitment/model inputs.

Verify the archived SVD rows without refitting models:

```powershell
python scripts/verify_table1_svd_rows.py
```

This checks the 40 archived held-out-year predictions and recalculates Pearson `r`, log10-scale MSE, and the historical predicted-series CV against the archived reference rows.

## Reproducing manuscript results

| Manuscript output | Reproduction command | Required inputs | Status |
|---|---|---|---|
| Figure 4 | `python scripts/improve_supplementary_prediction_intervals.py` | Archived `annual_predictions_uncertainty.csv` | Verified; archived PNG content matched exactly |
| Figure R1 | `python scripts/plot_figure_R1_GAM_EDF_archived.py` | Archived fold-wise EDF CSV | Verified; no GAM pickles required |
| Figure R2 | `python scripts/plot_recruitment_uncertainty_log10.py` | Candidate 500-refit predictions plus external observed recruitment via `PBF_DATA_ROOT` | Verified with external snapshot; not self-contained |
| Table 1 — SVD rows | `python scripts/verify_table1_svd_rows.py` | Archived 40 held-out predictions and reference table | Verified at reported precision; no models required |

These commands use repository-relative paths and write to the documented result directories, except where an isolated output option is provided. Figure 4 and Figure R2 reproduce archived numerical outputs; they do not recompute prediction intervals or regenerate recruitment realizations. Figure R1 reproduces the archived EDF plot; independent EDF recomputation requires external fitted GAM models. The Table 1 verifier recalculates the archived SVD rows on the `log10(recruitment)` scale.

## Figure 4

The authoritative manuscript Figure 4 is `results/observational/figure4_corrected_loocv/fig4.png`; the vector version is `fig4.svg` and the caption is `fig4_caption.txt`. Generate the archived-output rendering with:

```powershell
python scripts/improve_supplementary_prediction_intervals.py
```

This reads `annual_predictions_uncertainty.csv` and writes `fig4.png`, `fig4.svg`, and `fig4_caption.txt` in the Figure 4 results directory. It does not recompute intervals, bootstrap RF models, or refit GAM/RF. The darker shading is the model-only 95% interval, the lighter shading is the approximate combined model-plus-residual-data 95% prediction interval, and dashed boundaries show residual-data variability.

Underlying interval recomputation is a separate, expensive workflow requiring excluded raw inputs/models and is not run here.

## Recruitment assessment uncertainty

The included file contains 500 author-generated recruitment realizations, which are assessment-derived samples rather than 500 independent observations or an official ISC ensemble. They were generated by the authors using uncertainty information from: International Scientific Committee for Tuna and Tuna-like Species in the North Pacific Ocean (ISC). (2022). *Stock assessment of Pacific bluefin tuna in the Pacific Ocean in 2022*. ISC/22/ANNEX/13; WCPFC-SC18-2022/SA-WP-05. Figure 5-14, p. 135. Official source: [WCPFC Meetings](https://meetings.wcpfc.int/node/16246). The original sampling-generation script is not yet available, and no sampling distribution, random seed, or uncertainty-conversion method is inferred here. The fixed file has 500 rows (`Sim_ID` 1–500) and 40 year columns (1981–2020), with no missing values; values are on the log10 recruitment scale. Its SHA-256 is `5be88d200c07bffbd2d08ddd9f545db30f3f31761548180320a78f683234b7e8`. Redistribution/reuse clearance remains pending; inclusion here documents the author’s derived data but does not establish legal clearance.

The documented command shape is:

```powershell
python scripts/run_recruitment_uncertainty_portable.py --n-samples 5 --output-dir "$env:TEMP\pbf-uncertainty-smoke"
```

The full repository-relative workflow invocation is:

```powershell
python scripts/run_recruitment_uncertainty_portable.py --n-samples 500 --output-dir "$env:TEMP\pbf-uncertainty-500"
```

Do not run the 500-realization workflow without the required external input, approval, and isolated output directory. Derived summary outputs in this candidate are provisional and redistribution rights remain unresolved.

## Recruitment assessment uncertainty — Figure R2

The recruitment-assessment uncertainty figure is `results/observational/recruitment_uncertainty/figures/recruitment_uncertainty_timeseries_log10.png` (PDF companion and caption are in the same directory). It is distinct from Figure R1 (GAM effective degrees of freedom) and Figure 4 (GAM/RF model/data-error prediction intervals).

Generate Figure R2 with:

```powershell
python scripts/plot_recruitment_uncertainty_log10.py
```

The script requires the external observed recruitment input and archived `results/observational/recruitment_uncertainty/predictions_500.csv`; the archived prediction summaries are sufficient for this lightweight plotting step. Set `PBF_DATA_ROOT` to a read-only approved snapshot containing `data/raw/observed_recruitment_1981_2020.csv` before running. It writes the PNG, PDF, and caption under `results/observational/recruitment_uncertainty/figures/`. It does not refit GAM/RF models or regenerate the 500 realizations. The included realization file has SHA-256 `5be88d200c07bffbd2d08ddd9f545db30f3f31761548180320a78f683234b7e8`; redistribution approval remains pending.
## Other manuscript outputs

### Figure R1 — GAM effective degrees of freedom

The corrected Figure R1 outputs are under `results/observational/diagnostics/figure_R1/`. The original `scripts/plot_figure_R1_GAM_EDF.py` extracts EDF from saved pyGAM models, but those 40 GAM pickle files are external to this candidate. The release candidate provides the validated `Figure_R1_GAM_EDF_by_fold.csv` and `Figure_R1_GAM_EDF_summary.csv` plus a standalone plotting script that does not require models:

```powershell
python scripts/plot_figure_R1_GAM_EDF_archived.py
```

This command reads the archived fold-wise EDF CSV and regenerates the PNG/PDF using the existing layout, colors, labels, and numerical values. It does not refit GAMs or recompute EDF. EDF term labels are `PO_PC1, AO_PC1, PO_PC2, AO_PC2, PO_PC3, AO_PC3`; total model EDF includes the intercept, and residual EDF is `39 − total model EDF`. Independent EDF recomputation from fitted GAMs still requires the external saved models.

| Output | Available reproduction pathway | Status |
|---|---|---|
| Figure R1 | Archived corrected outputs under `results/observational/diagnostics/figure_R1/`; `scripts/plot_figure_R1_GAM_EDF.py` requires external saved models | Corrected labels validated; fresh regeneration blocked |
| Table R1 and uncertainty figures | Archived derived summaries/figures plus the five-sample command above | Full rerun not independently verified |
| Appendix Figure 3 | Source notebook/input closure is not included in this candidate | Not available from this release candidate |
| DCPP hindcast/prediction analyses | Not included in this repository | Out of scope |

## Reproducibility status

Independently reproduced: downstream saved-model observational predictions and the five-realization recruitment-uncertainty smoke test. Regenerated from archived numerical data: Figure 4, Figure R1, Figure R2, and selected observational tables. Supplied but not independently rerun: original SST/SVD preprocessing and the full 500-realization experiment. Missing or unresolved: raw-data redistribution, saved-model distribution, exact xMCA version, full realization-generation provenance, and Appendix Figure 3 closure. This repository does not claim to reproduce DCPP analyses.

## Citation and license

Manuscript citation: *Pacific bluefin tuna recruitment variability and ocean–atmosphere teleconnections*, submitted to *Ecological Informatics*; final bibliographic details pending.

Code license: see `LICENSE`. Third-party data retain their original licensing terms; no license is assigned to external climate, recruitment, SST, or DCPP datasets. Repository DOI/Zenodo link: pending.

The repository and release candidate are not yet published.



### Recruitment data provenance

The observational recruitment series is sourced from International Scientific Committee for Tuna and Tuna-like Species in the North Pacific Ocean (ISC). (2022). *Stock assessment of Pacific bluefin tuna in the Pacific Ocean in 2022*. ISC/22/ANNEX/13; WCPFC-SC18-2022/SA-WP-05, Figure 5-14, p. 135. The official source page and report download are available from [WCPFC Meetings](https://meetings.wcpfc.int/node/16246).

The validated external file is `observed_recruitment_1981_2020.csv`. It must be placed at `data/raw/observed_recruitment_1981_2020.csv` under the directory named by `PBF_DATA_ROOT`, for example:

```text
<PBF_DATA_ROOT>/data/raw/observed_recruitment_1981_2020.csv
```

If `PBF_DATA_ROOT` is unset, repository-local code that uses the default root expects `data/raw/observed_recruitment_1981_2020.csv`; the file is intentionally absent from this repository. The actual loaders require at least two columns named `year` and `recruitment`, with 40 unique years from 1981 through 2020, finite positive numeric recruitment values, and no missing values. Recruitment is retained in the source assessment count units (no unit conversion is performed); model workflows apply `log10(recruitment)` when constructing the response. The analysis uses the six archived SVD predictors separately from this response CSV.

Its recruitment values match the validated internal analysis input exactly. The CSV is not included because the official page identifies the report but does not state a redistribution licence or permission to republish extracted Figure 5-14 values. Researchers must obtain the report and perform their own extraction or obtain permission before redistribution. This external recruitment CSV is required for fresh saved-model evaluation, Figure R2 plotting, and refitting workflows; it is not required for Figure R1 archived-EDF plotting or the archived-data Table 1 SVD-row check.


