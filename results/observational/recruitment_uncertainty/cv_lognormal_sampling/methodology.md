# CV-based mean-preserving lognormal recruitment sampling

## Source and reported inputs

Annual recruitment estimates for 1981–2020 come from `recruitment.csv` (also matching the repository's observed recruitment file). The uncertainty inputs are period-average recruitment-estimation CVs reported in the ISC (2022) Pacific bluefin tuna stock assessment: 0.21 for 1981–1993, 0.08 for 1994–2016, and 0.325 for 2017–2020 (corresponding to the report's 1980–1993, 1994–2016, and 2017–2020 periods). The report's annual CV trajectories and bootstrap paths were unavailable; these are reconstructed period averages.

## Sampling model

For assessment estimate (R_t) and CV (c_t), (s_t^2=\ln(1+c_t^2)), (\mu_t=\ln(R_t)-s_t^2/2), and (R_t^{(b)}=\exp(\mu_t+s_tZ_t^{(b)})), with independent standard-normal (Z) across years and realizations. The correction makes the *theoretical arithmetic mean* equal to (R_t), rather than making the median equal to it. The output is then transformed to log10 only because the existing LOOCV reader expects positive log10 responses.

Independence across years is an assumption, not a reported property of the assessment. Period-average CVs are used because annual estimation CVs were not available in the supplied materials. The reconstruction does not use digitized Figure 5-14 limits.

This estimation uncertainty is distinct from the stock-assessment recruitment-deviation parameter σ_R=0.6: σ_R describes process/deviation variation in the assessment recruitment dynamics, whereas these CVs represent estimation uncertainty around already estimated annual recruitment.

Reproduce with `python scripts/reconstruct_recruitment_cv_lognormal.py`; seed is 20261102. No GAM/RF models are run.

## Limitations

The experiment lacks the original assessment bootstrap trajectories, any temporal covariance, and any annual CV variation within a period. It is therefore a transparent sensitivity reconstruction, not a recovery of the original assessment uncertainty distribution.
