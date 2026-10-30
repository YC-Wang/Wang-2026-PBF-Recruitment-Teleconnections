# Environment setup

Existing metadata records Python 3.10.14, NumPy 2.2.6, pandas 2.3.3, SciPy 1.15.3, scikit-learn 1.7.2, pyGAM 0.12.0, and joblib 1.6.0. The exact xMCA package/version used by the original SVD notebook is not recorded. `tomli==2.0.1` is included for Python 3.10 TOML parsing; Python 3.11+ uses the standard-library `tomllib`.

`environment.yml` pins the recorded core versions and adds Jupyter, xarray, netCDF4, matplotlib, and pytest. It is not a complete lockfile until the xMCA dependency and clean-environment notebook execution are verified.

```powershell
conda env create -f environment.yml
conda activate pbf-recruitment-prediction
```

Do not claim bit-for-bit reproduction until dependency resolution and notebook execution have been tested. Do not run the 500-realization experiment in Phase 2B.
