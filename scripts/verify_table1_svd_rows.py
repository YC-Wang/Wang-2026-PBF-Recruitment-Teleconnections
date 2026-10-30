"""Verify archived Table 1 SVD rows without refitting GAM/RF models."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PRED = ROOT / "results/observational/table1_updated_loocv/table1_predictions_1981_2020.csv"
REF = ROOT / "results/observational/table1_updated_loocv/table1_updated_loocv.csv"
df = pd.read_csv(PRED).sort_values("year")
ref = pd.read_csv(REF)
if len(df) != 40 or df["year"].tolist() != list(range(1981, 2021)):
    raise ValueError("Expected 40 held-out years from 1981 through 2020")
y = df["log10_recruitment"].to_numpy(float)
rows = []
for model in ("GAM", "RF"):
    p = df[f"SVD teleconnection indices_{model}_log10_prediction"].to_numpy(float)
    r = float(np.corrcoef(y, p)[0, 1])
    mse = float(np.mean((y - p) ** 2))
    cv = float(100 * np.std(p, ddof=1) / np.mean(p))
    expected = ref[(ref["Predictors"] == "SVD teleconnection indices") & (ref["Model"] == model)].iloc[0]
    if not (np.isclose(r, expected.r, atol=1e-12) and np.isclose(mse, expected.MSE, atol=1e-12) and np.isclose(cv, expected["CV (%)"], atol=1e-12)):
        raise AssertionError(f"Archived metrics disagree for {model}")
    rows.append((model, r, mse, cv))
print("Verified archived SVD Table 1 rows on log10(recruitment) scale")
for row in rows:
    print(f"{row[0]} r={row[1]:.10f} MSE={row[2]:.12f} CV={row[3]:.10f}%")
