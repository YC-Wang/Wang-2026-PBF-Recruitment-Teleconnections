"""Reproduce archived DCPP Table 2 and ensemble verification metrics."""
from argparse import ArgumentParser
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import bootstrap, linregress, pearsonr

ROOT = Path(__file__).resolve().parents[1]
YEARS = np.arange(1981, 2011)
MODELS = ("GAM", "RF")


def crps(sample, observed):
    x = np.sort(np.asarray(sample, dtype=float))
    n = len(x)
    return np.mean(abs(x - observed)) - np.sum((2 * np.arange(1, n + 1) - n - 1) * x) / n**2


def correlation_ci(observed, prediction):
    def statistic(x, y, axis=-1):
        x = x - x.mean(axis=axis, keepdims=True)
        y = y - y.mean(axis=axis, keepdims=True)
        return (x * y).sum(axis=axis) / np.sqrt((x * x).sum(axis=axis) * (y * y).sum(axis=axis))

    result = bootstrap(
        (observed, prediction), statistic, paired=True, vectorized=True,
        method="BCa", n_resamples=5000, random_state=20261107,
    )
    return result.confidence_interval.low, result.confidence_interval.high


def main(output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    ensemble_dir = output_dir / "ensemble_verification"
    ensemble_dir.mkdir(parents=True, exist_ok=True)

    recruitment = pd.read_csv(ROOT / "data/processed/recruitment.csv").set_index("year")
    observed = np.log10(recruitment.loc[YEARS, "recruitment"].to_numpy(float))
    groups = {}
    for lead in (1, 2):
        path = ROOT / f"results/dcpp_predictions/lead{lead}_obs_aligned_pooled_loyo/lead{lead}_member_recruitment_predictions.csv"
        groups[f"Lead {lead}"] = pd.read_csv(path)
    groups["Lead 3-5"] = pd.concat([
        pd.read_csv(ROOT / f"results/dcpp_predictions/lead{lead}_obs_aligned_pooled_loyo/lead{lead}_member_recruitment_predictions.csv")
        for lead in (3, 4, 5)
    ], ignore_index=True)

    table_rows, ensemble_rows = [], []
    for label, data in groups.items():
        expected_members = 117 if label != "Lead 3-5" else 351
        key = ["verification_year", "member"] if label != "Lead 3-5" else ["verification_year", "lead_year", "member"]
        assert set(data.verification_year) == set(YEARS)
        assert len(data) == 30 * expected_members
        assert data.groupby("verification_year").size().eq(expected_members).all()
        assert data.duplicated(key).sum() == 0
        if label == "Lead 3-5":
            assert sorted(data.lead_year.unique()) == [3, 4, 5]
            assert data.groupby(["verification_year", "lead_year"]).size().eq(117).all()

        for model in MODELS:
            column = f"{model}_pred_log10"
            values = data.pivot_table(index="verification_year", columns="member", values=column, aggfunc="first").loc[YEARS].to_numpy(float)
            mean = values.mean(axis=1)
            lower = np.quantile(values, 0.05, axis=1)
            upper = np.quantile(values, 0.95, axis=1)
            correlation = pearsonr(observed, mean).statistic
            ci_low, ci_high = correlation_ci(observed, mean)
            mse = np.mean((observed - mean) ** 2)
            msss = 1 - mse / np.mean((observed - observed.mean()) ** 2)
            fit = linregress(np.arange(30), mean)
            observed_fit = linregress(np.arange(30), observed)
            residual = mean - (fit.intercept + fit.slope * np.arange(30))
            observed_residual = observed - (observed_fit.intercept + observed_fit.slope * np.arange(30))
            table_rows.append({
                "Fitting method": model, "Lead": label, "r": correlation,
                "r_ci_low": ci_low, "r_ci_high": ci_high,
                "r_95_CI": f"{correlation:.2f} ({ci_low:.2f},{ci_high:.2f})", "MSSS": msss,
            })

            reference = np.array([crps(np.delete(observed, i), observed[i]) for i in range(30)])
            scores = np.array([crps(values[i], observed[i]) for i in range(30)])
            ensemble_rows.extend({
                "lead_group": label, "model": model, "verification_year": int(YEARS[i]),
                "n_members": values.shape[1], "ensemble_mean": mean[i],
                "ensemble_median": np.median(values[i]), "ensemble_sd": values[i].std(ddof=1),
                "p05": lower[i], "p95": upper[i], "crps": scores[i],
                "reference_crps": reference[i], "covered90": lower[i] <= observed[i] <= upper[i],
                "observed": observed[i],
            } for i in range(30))
            ensemble_rows.append({
                "lead_group": label, "model": model, "aggregate": True,
                "mean_crps": scores.mean(), "crpss": 1 - scores.mean() / reference.mean(),
                "coverage90": np.mean((observed >= lower) & (observed <= upper)),
                "mean_width90": np.mean(upper - lower), "pearson_r": correlation,
                "rmse": np.sqrt(mse), "mse": mse, "bias": np.mean(mean - observed),
                "detrended_r": pearsonr(observed_residual, residual).statistic,
                "first_difference_r": pearsonr(np.diff(observed), np.diff(mean)).statistic,
            })

    table = pd.DataFrame(table_rows)
    ensemble = pd.DataFrame(ensemble_rows)
    table.to_csv(output_dir / "table2_revised.csv", index=False)
    ensemble.to_csv(ensemble_dir / "ensemble_annual_metrics.csv", index=False)
    ensemble[ensemble.get("aggregate", False) == True].to_csv(ensemble_dir / "ensemble_aggregate_metrics.csv", index=False)
    ensemble[ensemble.get("aggregate", False) != True].to_csv(ensemble_dir / "ensemble_crps_reference.csv", index=False)
    print(table.to_string(index=False))
    print(f"Wrote {len(table)} Table 2 rows, {len(ensemble[ensemble.get('aggregate', False) != True])} annual rows, and {len(ensemble[ensemble.get('aggregate', False) == True])} aggregate rows to {output_dir}")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results/dcpp_table2_revision")
    main(parser.parse_args().output_dir)
