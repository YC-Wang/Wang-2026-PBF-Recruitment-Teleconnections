import numpy as np
import pytest
import xarray as xr
from src.pbf.svd_projection import ProjectionBasis, project_scores, load_fold_basis

def test_projection_order_and_math():
    basis = ProjectionBasis(np.ones((3,2,2)), np.full((3,2,2),2.), np.array([1,2]), np.array([1,2]), 1, "training", "coslat", "unit")
    result = project_scores(np.ones((2,2)), np.ones((2,2)), basis, po_mean=np.zeros((2,2)), ao_mean=np.zeros((2,2)), weights=np.ones((2,2)))
    assert result.shape == (6,); assert np.allclose(result, [4,8,4,8,4,8])

def test_projection_rejects_missing_metadata(tmp_path):
    ds = xr.Dataset({"basis": (("basin","mode","lat","lon"), np.ones((2,3,2,2)))}, coords={"basin":["PO","AO"],"mode":[1,2,3],"lat":[1,2],"lon":[1,2],"fold":[1]})
    path=tmp_path/"basis.nc"; ds.to_netcdf(path)
    with pytest.raises(ValueError, match="metadata missing"): load_fold_basis(path, 1)
