from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

root = Path(__file__).resolve().parents[1]
out = root / "results/observational/figure4_corrected_loocv"
d = pd.read_csv(out / "annual_predictions_uncertainty.csv").sort_values("year")

colors = {"GAM": "#1479B8", "RF": "#D97706"}
fig, axes = plt.subplots(2, 1, figsize=(13, 8.5), sharex=True, sharey=True,
                         gridspec_kw={"hspace": 0.16})

all_y = [d.observed_log10_recruitment.to_numpy()]
for method in ("GAM", "RF"):
    pred = d[f"{method}_log10_prediction"].to_numpy()
    model_sd = np.sqrt(d[f"{method}_model_variance"].to_numpy())
    data_sd = np.sqrt(d[f"{method}_data_variance"].to_numpy())
    total_sd = np.sqrt(d[f"{method}_total_variance"].to_numpy())
    model_lo, model_hi = pred - 1.96 * model_sd, pred + 1.96 * model_sd
    data_lo, data_hi = pred - 1.96 * data_sd, pred + 1.96 * data_sd
    pi_lo, pi_hi = pred - 1.96 * total_sd, pred + 1.96 * total_sd
    all_y.extend([model_lo, model_hi, data_lo, data_hi, pi_lo, pi_hi])

ymin = min(np.min(x) for x in all_y); ymax = max(np.max(x) for x in all_y)
pad = 0.04 * (ymax - ymin)

for ax, method in zip(axes, ("GAM", "RF")):
    color = colors[method]
    pred = d[f"{method}_log10_prediction"].to_numpy()
    model_sd = np.sqrt(d[f"{method}_model_variance"].to_numpy())
    data_sd = np.sqrt(d[f"{method}_data_variance"].to_numpy())
    total_sd = np.sqrt(d[f"{method}_total_variance"].to_numpy())
    model_lo, model_hi = pred - 1.96 * model_sd, pred + 1.96 * model_sd
    data_lo, data_hi = pred - 1.96 * data_sd, pred + 1.96 * data_sd
    pi_lo, pi_hi = pred - 1.96 * total_sd, pred + 1.96 * total_sd

    # Light combined PI first; darker model CI remains visible above it.
    ax.fill_between(d.year, pi_lo, pi_hi, color=color, alpha=0.12, linewidth=0,
                    label="Combined 95% PI")
    ax.fill_between(d.year, model_lo, model_hi, color=color, alpha=0.28, linewidth=0,
                    label="Model-only 95% CI")
    # Data-only residual interval is shown only as thin dashed boundaries.
    ax.plot(d.year, data_lo, color=color, linestyle=(0, (3, 2)), linewidth=0.9,
            alpha=0.85, label="Residual variability 95% interval")
    ax.plot(d.year, data_hi, color=color, linestyle=(0, (3, 2)), linewidth=0.9,
            alpha=0.85)

    ax.plot(d.year, d.observed_log10_recruitment, color="black", linewidth=2.1,
            label="Observed recruitment", zorder=5)
    ax.plot(d.year, pred, color=color, linewidth=2.0, label=f"{method} LOOCV prediction",
            zorder=6)
    ax.text(0.5, 1.025, method, transform=ax.transAxes, ha="center", va="bottom",
            fontsize=15, fontweight="bold")
    ax.set_ylabel("log10 recruitment", fontsize=12)
    ax.set_ylim(ymin - pad, ymax + pad)
    ax.grid(True, color="#B8B8B8", linewidth=0.55, alpha=0.28)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(labelsize=10)
    ax.legend(loc="upper left", frameon=True, framealpha=0.9, fontsize=9,
              ncol=2, borderpad=0.55, handlelength=2.5)

axes[-1].set_xlabel("Year", fontsize=12)
axes[-1].set_xticks(np.arange(1981, 2021, 5))
fig.suptitle("Corrected observational LOOCV recruitment predictions", fontsize=17,
             fontweight="bold", y=0.99)
fig.tight_layout(rect=[0, 0, 1, 0.97])
fig.savefig(out / "fig4.png", dpi=300,
            bbox_inches="tight", facecolor="white")
fig.savefig(out / "fig4.svg",
            bbox_inches="tight", facecolor="white")
plt.close(fig)

caption = """Supplementary Figure. Corrected observational LOOCV recruitment predictions for 1981–2020 on the log10(recruitment) scale. The black line is observed recruitment and the colored line is the year-specific outer-LOOCV prediction from the saved GAM (upper panel) or RF (lower panel). The darker band is the model-only 95% confidence interval, defined as prediction ± 1.96 × sqrt(model variance). The lighter band is the approximate combined 95% prediction interval, defined by adding model variance and residual data variance. Thin dashed boundaries show the data-only residual variability interval, prediction ± 1.96 × sqrt(residual variance). Residual data variance represents unexplained recruitment variability estimated by inner five-fold CV within each 39-year outer-training fold; it is not recruitment assessment or measurement uncertainty. The intervals are approximate, conditional on the existing outer-fold SVD representation, and are not fully nested or formally calibrated."""
(out / "fig4_caption.txt").write_text(caption, encoding="utf-8")
print("saved improved supplementary figures and caption")
