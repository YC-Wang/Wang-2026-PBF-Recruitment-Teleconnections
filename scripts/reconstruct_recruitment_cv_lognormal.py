"""Generate the final CV-based lognormal recruitment input."""
from pathlib import Path
import hashlib, json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/observational/recruitment_uncertainty/cv_lognormal_sampling"
RECRUITMENT = ROOT / "data/raw/observed_recruitment_1981_2020.csv"
YEARS = np.arange(1981, 2021)
SEED, N = 20261102, 500

def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()

def main():
    if not RECRUITMENT.exists():
        raise FileNotFoundError(f"Missing approved external input: {RECRUITMENT}")
    rec = pd.read_csv(RECRUITMENT)
    if list(rec.columns) != ["year", "recruitment"]:
        raise ValueError("Expected columns: year,recruitment")
    rec = rec.set_index("year").reindex(YEARS)
    if rec.recruitment.isna().any() or (rec.recruitment <= 0).any():
        raise ValueError("Recruitment input must contain positive values for 1981-2020")
    cv = np.select([YEARS <= 1993, YEARS <= 2016], [0.21, 0.08], default=0.325)
    s2 = np.log1p(cv ** 2); s = np.sqrt(s2)
    mu = np.log(rec.recruitment.to_numpy()) - s2 / 2
    rng = np.random.default_rng(SEED)
    samples = np.exp(mu[None, :] + s[None, :] * rng.standard_normal((N, len(YEARS))))
    output = pd.DataFrame(np.log10(samples), columns=YEARS.astype(str))
    output.insert(0, "Sim_ID", np.arange(1, N + 1))
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / "Y_sim_500_samples_cv_lognormal_log10.csv"
    output.to_csv(target, index=False, float_format="%.15g")
    pd.DataFrame({"year": YEARS, "cv": cv, "s2": s2, "s": s, "mu": mu,
                  "target_mean": rec.recruitment.to_numpy(),
                  "theoretical_mean": np.exp(mu + s2 / 2)}).to_csv(OUT / "parameters.csv", index=False)
    validation = {"years": 40, "realizations": N, "seed": SEED,
                  "finite": bool(np.isfinite(samples).all()), "positive": bool((samples > 0).all()),
                  "cv_assignment": {"1981-1993": 0.21, "1994-2016": 0.08, "2017-2020": 0.325},
                  "output_sha256": sha256(target), "format": "Sim_ID plus 1981-2020 log10 recruitment columns"}
    (OUT / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    (OUT / "methodology.md").write_text(
        "# Final CV-based lognormal recruitment sampling\n\n"
        "The 500 realizations use seed `20261102`, year-specific CVs of 0.21 "
        "(1981–1993), 0.08 (1994–2016), and 0.325 (2017–2020), with a "
        "mean-preserving lognormal model on the original recruitment scale. "
        "Output is log10 recruitment for the retained LOOCV reader. This is "
        "distinct from Figure 4 RF IJ uncertainty.\n\n"
        "Run `python scripts/reconstruct_recruitment_cv_lognormal.py` after "
        "supplying the approved external annual recruitment input. Original "
        "assessment bootstrap trajectories and annual CV series are not redistributed.\n",
        encoding="utf-8")
    print(json.dumps(validation, indent=2))

if __name__ == "__main__": main()
