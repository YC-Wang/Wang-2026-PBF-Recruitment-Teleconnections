"""Generate Figure R1 from saved pyGAM LOOCV objects and diagnostics."""
from pathlib import Path
import json, pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DIAG = ROOT / "results/observational/diagnostics"
MODELS = ROOT / "results/observational/training/models"
OUT = DIAG / "figure_R1"
OUT.mkdir(parents=True, exist_ok=True)

TERMS = ["PO_PC1", "AO_PC1", "PO_PC2", "AO_PC2", "PO_PC3", "AO_PC3"]
COLORS = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7", "#56B4E9"]

source = pd.read_csv(DIAG / "gam_complexity_by_fold.csv")
assert len(source) == 40 and source["Left_Out_Year"].tolist() == list(range(1981, 2021))
assert source["n_train"].eq(39).all()

rows = []
for i, rec in source.iterrows():
    fold = int(rec["Fold"])
    with open(MODELS / f"gam_fold_{fold:02d}.pkl", "rb") as f:
        gam = pickle.load(f)
    edof = np.asarray(gam.statistics_["edof_per_coef"], dtype=float)
    assert len(edof) == 19, f"Unexpected coefficient count in fold {fold}: {len(edof)}"
    term_edf = [float(edof[j:j+3].sum()) for j in range(0, 18, 3)]
    intercept = float(edof[18])
    total = float(gam.statistics_["edof"])
    assert np.isclose(sum(term_edf) + intercept, total, atol=1e-8)
    rows.append({"Fold": fold, "Held_out_year": int(rec["Left_Out_Year"]),
                 "n_train": int(rec["n_train"]), **dict(zip(TERMS, term_edf)),
                 "Intercept_EDF": intercept, "Total_model_EDF": total,
                 "Residual_EDF": 39.0 - total})

df = pd.DataFrame(rows)
long = df.melt(id_vars=["Fold", "Held_out_year", "n_train"], value_vars=TERMS,
               var_name="Variable", value_name="EDF")
summary = []
for name in TERMS + ["Total_model_EDF", "Residual_EDF"]:
    v = df[name]
    summary.append({"Variable": name, "Mean EDF": v.mean(), "Median EDF": v.median(),
                    "SD": v.std(ddof=1), "Minimum": v.min(), "Maximum": v.max()})
pd.DataFrame(summary).to_csv(OUT / "Figure_R1_GAM_EDF_summary.csv", index=False, float_format="%.8f")
df.to_csv(OUT / "Figure_R1_GAM_EDF_by_fold.csv", index=False, float_format="%.8f")

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

caption = ("Figure R1. Effective degrees of freedom (EDF) across the 40 leave-one-year-out GAM fits. "
           "(a) EDF for the six SVD-derived smooth terms (PO_PC1, AO_PC1, PO_PC2, AO_PC2, PO_PC3, AO_PC3) by held-out recruitment year. (b) Total model EDF, "
           "including the intercept, and residual EDF (= 39 − total model EDF); dashed lines indicate medians. "
           "(c) Distributions of term-specific EDF across folds. Each fit used 39 training observations. "
           "Term EDF was extracted by summing pyGAM edof_per_coef within each three-coefficient smooth term; "
           "the extracted term EDF plus intercept EDF equals the reported total EDF in every fold.")
(OUT / "Figure_R1_GAM_EDF_caption.txt").write_text(caption + "\n", encoding="utf-8")

print(f"Wrote outputs to {OUT}")
print(f"Total EDF median/range: {df.Total_model_EDF.median():.4f} / {df.Total_model_EDF.min():.4f}–{df.Total_model_EDF.max():.4f}")
print(f"Residual EDF median/range: {df.Residual_EDF.median():.4f} / {df.Residual_EDF.min():.4f}–{df.Residual_EDF.max():.4f}")
