"""Render Figure R1 from the validated archived fold-wise EDF CSV.

This publication-candidate pathway does not load or refit GAM pickle models.
The archived CSV was produced from the validated fitted-model EDF extraction.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/observational/diagnostics/figure_R1"
TERMS = ["PO_PC1", "AO_PC1", "PO_PC2", "AO_PC2", "PO_PC3", "AO_PC3"]
COLORS = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7", "#56B4E9"]

df = pd.read_csv(OUT / "Figure_R1_GAM_EDF_by_fold.csv")
required = ["Fold", "Held_out_year", "n_train", *TERMS, "Intercept_EDF", "Total_model_EDF", "Residual_EDF"]
missing = [c for c in required if c not in df.columns]
if missing:
    raise ValueError(f"Missing EDF columns: {missing}")
if len(df) != 40 or df["Held_out_year"].tolist() != list(range(1981, 2021)):
    raise ValueError("Expected 40 held-out years from 1981 through 2020")
if not df["n_train"].eq(39).all():
    raise ValueError("Expected 39 training observations in every fold")
if not np.allclose(df["Residual_EDF"], 39.0 - df["Total_model_EDF"], atol=1e-8):
    raise ValueError("Residual EDF does not equal 39 minus total model EDF")

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.labelsize": 12,
                     "xtick.labelsize": 10, "ytick.labelsize": 10})
fig = plt.figure(figsize=(13, 9), facecolor="white")
gs = fig.add_gridspec(2, 2, height_ratios=[1.12, 1], hspace=0.38, wspace=0.28)
ax1 = fig.add_subplot(gs[0, :]); ax2 = fig.add_subplot(gs[1, 0]); ax3 = fig.add_subplot(gs[1, 1])
years = df["Held_out_year"]

for term, color in zip(TERMS, COLORS):
    ax1.plot(years, df[term], marker="o", ms=3.2, lw=1.4, color=color, label=term)
ax1.set_ylabel("Effective degrees of freedom (EDF)"); ax1.set_xlabel("Held-out recruitment year")
ax1.set_xlim(1980.5, 2020.5); ax1.set_ylim(0, max(df[TERMS].max()) * 1.18)
ax1.grid(axis="y", color="#dddddd", lw=0.6); ax1.legend(ncol=6, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.18))

for name, label, color in [("Total_model_EDF", "Total model EDF", "#333333"), ("Residual_EDF", "Residual EDF", "#0072B2")]:
    med = df[name].median(); ax2.plot(years, df[name], marker="o", ms=3.2, lw=1.6, color=color, label=f"{label} (median {med:.2f})")
    ax2.axhline(med, color=color, ls="--", lw=1.0, alpha=0.75)
ax2.set_ylabel("Degrees of freedom"); ax2.set_xlabel("Held-out recruitment year")
ax2.set_xlim(1980.5, 2020.5); ax2.text(0.03, 0.06, "N_train = 39", transform=ax2.transAxes)
ax2.grid(axis="y", color="#dddddd", lw=0.6); ax2.legend(frameon=False, loc="best")

bp = ax3.boxplot([df[t] for t in TERMS], patch_artist=True, labels=TERMS, widths=0.62,
                 medianprops={"color": "black", "lw": 1.2}, whiskerprops={"lw": 1.1},
                 capprops={"lw": 1.1}, flierprops={"marker": "o", "ms": 3, "alpha": 0.65})
for patch, color in zip(bp["boxes"], COLORS): patch.set_facecolor(color); patch.set_alpha(0.75)
ax3.set_ylabel("Effective degrees of freedom (EDF)"); ax3.grid(axis="y", color="#dddddd", lw=0.6)
for ax, label in zip([ax1, ax2, ax3], ["(a)", "(b)", "(c)"]): ax.text(-0.06, 1.04, label, transform=ax.transAxes, fontsize=13, fontweight="bold", va="bottom")
fig.savefig(OUT / "Figure_R1_GAM_EDF.png", dpi=300, bbox_inches="tight", facecolor="white")
fig.savefig(OUT / "Figure_R1_GAM_EDF.pdf", bbox_inches="tight")
plt.close(fig)
print(f"Wrote archived-data Figure R1 outputs to {OUT}")
