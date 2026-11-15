# Phase 7A — Observational Model Inventory for a Planned Zenodo Archive

## Scope and source workspaces

This audit inspected a read-only scientific development workspace and the publication workspace. No model was loaded, refit, modified, copied, or uploaded. The publication workspace contains no saved model pickles; the verified model artifacts remain external to this release.

## Executive finding

Only the SVD teleconnection model family has saved fitted GAM/RF objects. There are 40 GAM and 40 RF pickles, 80 files total, under:

`external observational-model archive/results/observational/training/models`

The 80 files occupy 102,654,265 bytes. Exact per-file sizes and SHA-256 values are recorded in `PHASE7A_MODEL_CHECKSUMS.csv` in Workspace B.

No saved GAM/RF model objects for Regional SST (RegSST) or PDO/AMO were found in either inspected workspace. Their Table 1 rows are archived numerical results produced/reproduced by `scripts/generate_table1_updated_loocv.py` and `scripts/finalize_table1_updated_outputs.py`, using precomputed predictor series, rather than an archived model-pickle collection.

## Family inventory

| Family | Saved GAM models | Saved RF models | Predictor order | Training/validation evidence | Published result |
|---|---:|---:|---|---|---|
| SVD teleconnection indices | 40, `gam_fold_01.pkl`–`gam_fold_40.pkl` | 40, `rf_fold_01.pkl`–`rf_fold_40.pkl` | `PO_PC1, AO_PC1, PO_PC2, AO_PC2, PO_PC3, AO_PC3` | 40 held-out years, one fold per 1981–2020; 39 training years per fold | Yes; Table 1 SVD GAM/RF rows |
| Regional SST (RegSST) | None found | None found | `SSPG_4_6, NSPG_7_9, JNG_10_12` | Script documents sequential 40-fold LOOCV/KFold with `shuffle=False`, but upstream preprocessing and fitted objects are not archived | Yes; Table 1 RegSST rows are archived/reproduced metrics |
| PDO/AMO | None found | None found | `PDO, AMO` | Script documents sequential 40-fold LOOCV/KFold with `shuffle=False`, but upstream preprocessing and fitted objects are not archived | Yes; Table 1 PDO/AMO rows are archived/reproduced metrics |

The RegSST and PDO/AMO rows must not be represented as having the same saved-model provenance as SVD. Their code path fits models inside a 40-iteration loop when recomputation is requested, but no corresponding pickle files, fold-level model archive, or independent preprocessing provenance was located.

## SVD model configuration

The authoritative `results/observational/training/model_config.json` records:

- Response: `log10(recruitment)`.
- Years: 1981–2020, outer leave-one-year-out; each fold trains on 39 years and holds out one year.
- GAM: `pygam.LinearGAM`; one spline term per predictor; `n_splines=3`, `spline_order=2`; default regularization with no grid search; recorded smoothing value `0.6` per term in the model summary.
- RF: `RandomForestRegressor(n_estimators=1000, max_depth=5, max_features="sqrt", random_state=1)`; the model summary records the standard default settings including bootstrap.
- Environment recorded in the configuration: Python 3.10.14; NumPy 2.2.6; pandas 2.3.3; SciPy 1.15.3; scikit-learn 1.7.2; pyGAM 0.12.0; Windows 10.
- Required preprocessing: validated fold-specific six-predictor SVD CSV, recruitment response, and the fold/year mapping. No additional normalization is applied by the saved-model evaluation beyond the recorded response log transformation; SVD predictor construction is upstream and separately documented.

The saved models correspond to the SVD Table 1 family. They are not RegSST or PDO/AMO models.

## RegSST and PDO/AMO configuration evidence

The Table 1 generation script identifies the precomputed inputs and predictor names as:

- RegSST: `SST_regional_timeseries_1981_2020.csv`; columns `SSPG_4_6`, `NSPG_7_9`, `JNG_10_12`.
- PDO/AMO: `SVD_mode_recruitment_normalize.csv`; columns `PDO`, `AMO`.
- Recruitment: 1981–2020, transformed to `log10(recruitment)`.
- GAM/RF parameter definitions match the SVD configuration in the script: GAM `n_splines=3`, `spline_order=2`, default regularization; RF 1000 trees, depth 5, `sqrt` features, seed 1.
- The script's stated framework is 40 sequential folds (`KFold(n_splits=40, shuffle=False)` in its validation report). However, the available files do not establish that these predictor series were constructed fold-contained, and no fitted models are saved.

These are verified code/configuration claims, not evidence that independent RegSST/PDO/AMO model pickles exist.

## Proposed Zenodo structure

```text
zenodo-observational-models/
├── README.md
├── LICENSE-or-data-terms.md
├── environment.yml
├── model_inventory.csv
├── checksums/
│   └── PHASE7A_MODEL_CHECKSUMS.csv
└── models/
    └── svd_teleconnection_indices/
        ├── gam_fold_01.pkl ... gam_fold_40.pkl
        └── rf_fold_01.pkl  ... rf_fold_40.pkl
```

RegSST and PDO/AMO should not be placed in the model directory unless the missing fitted objects and provenance are located and validated. They can be represented in a separate metadata section as published metric families with no saved-model archive currently available.

Pickle files must be distributed only with trusted-source warnings and compatible Python/package-version documentation. The archive should include the exact checksum file, model configuration, fold mapping, and a clear statement that the files are observational SVD models only.

## Missing requirements and inconsistencies

1. No RegSST or PDO/AMO GAM/RF pickles were found; their Table 1 metrics are not sufficient to reconstruct fitted model objects.
2. RegSST/PDO/AMO upstream preprocessing files and provenance are external or incomplete, and fold-contained preprocessing cannot be confirmed.
3. The scientific Table 1 generation script retains legacy absolute paths and is not an appropriate public model-archive entry point without further documentation cleanup.
4. The saved-model environment is recorded, but pickle loading still requires compatible package builds and trusted files.
5. No Zenodo deposit or public model archive exists yet.

## Recommendation

Proceed with a Zenodo archive of the verified SVD model family only, unless the missing RegSST/PDO/AMO fitted objects are located and independently audited. Do not label the three-family archive as complete until those artifacts and their fold/provenance metadata are available.
