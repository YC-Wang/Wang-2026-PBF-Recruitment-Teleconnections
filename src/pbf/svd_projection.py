"""Guarded projection utilities for observational SVD bases.

The supplied LOOCV NetCDF contains averaged teleconnection maps, not singular
vectors. This module therefore refuses to project from it unless a future
basis file explicitly declares the required projection metadata.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import xarray as xr

PREDICTOR_ORDER = ("PO_PC1", "AO_PC1", "PO_PC2", "AO_PC2", "PO_PC3", "AO_PC3")

@dataclass(frozen=True)
class ProjectionBasis:
    po: np.ndarray
    ao: np.ndarray
    lat: np.ndarray
    lon: np.ndarray
    fold: int
    anomaly_reference: str
    weighting: str
    normalization: str

def inspect_basis(path):
    return xr.open_dataset(path)

def _required_metadata(ds):
    required = ("basis_kind", "anomaly_reference", "spatial_weighting", "score_normalization", "grid_definition")
    missing = [key for key in required if key not in ds.attrs]
    if missing: raise ValueError(f"Projection basis metadata missing: {', '.join(missing)}")
    if str(ds.attrs["basis_kind"]).lower() not in {"singular_vector", "svd_pattern"}:
        raise ValueError(f"Dataset declares basis_kind={ds.attrs['basis_kind']!r}; singular vectors are required")

def load_fold_basis(path, fold):
    ds = xr.open_dataset(path); _required_metadata(ds)
    if "fold" not in ds.dims and "fold" not in ds.coords: raise ValueError("Basis must contain a fold dimension or coordinate")
    if fold not in set(np.asarray(ds["fold"].values).tolist()): raise KeyError(f"Fold {fold} is not present")
    if "basin" not in ds.dims or "mode" not in ds.dims: raise ValueError("Basis must have basin and mode dimensions")
    pattern_name = ds.attrs.get("pattern_variable", "basis")
    if pattern_name not in ds: raise ValueError(f"Basis variable {pattern_name!r} not found")
    patterns = ds[pattern_name].sel(fold=fold)
    return ProjectionBasis(
        po=np.asarray(patterns.sel(basin="PO").values), ao=np.asarray(patterns.sel(basin="AO").values),
        lat=np.asarray(ds.lat.values), lon=np.asarray(ds.lon.values), fold=int(fold),
        anomaly_reference=str(ds.attrs["anomaly_reference"]), weighting=str(ds.attrs["spatial_weighting"]), normalization=str(ds.attrs["score_normalization"]),
    )

def project_scores(po_sst, ao_sst, basis: ProjectionBasis, *, po_mean=None, ao_mean=None, weights=None, scale=None):
    po = np.asarray(po_sst, dtype=float); ao = np.asarray(ao_sst, dtype=float)
    if po.shape != basis.po.shape[1:] or ao.shape != basis.ao.shape[1:]: raise ValueError("SST fields must match the basis spatial shape")
    if weights is None: raise ValueError("Spatial weights must be supplied explicitly")
    weights = np.asarray(weights, dtype=float)
    if weights.shape != po.shape: raise ValueError("Spatial weights must match the SST field")
    if po_mean is None or ao_mean is None: raise ValueError("Training-fold anomaly references must be supplied")
    po = po - np.asarray(po_mean); ao = ao - np.asarray(ao_mean)
    po_scores = np.asarray([np.nansum(po * weights * mode) for mode in basis.po])
    ao_scores = np.asarray([np.nansum(ao * weights * mode) for mode in basis.ao])
    scores = np.column_stack([po_scores, ao_scores]).ravel()
    if scale is not None:
        scale = np.asarray(scale, dtype=float)
        if scale.shape != (6,): raise ValueError("scale must contain six values")
        scores = scores / scale
    # Interleave PO/AO by mode, matching PO_PC1, AO_PC1, ... exactly.
    return scores
