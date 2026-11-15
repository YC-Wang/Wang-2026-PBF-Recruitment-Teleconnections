# Appendix Table S2.1. CV-based recruitment uncertainty

Pearson correlation and RMSE were calculated separately for each of 500 matched realization IDs using the sampled log₁₀ recruitment targets and the corresponding 40 held-out predictions. RMSE is on the log₁₀ recruitment scale. Percentiles are empirical 2.5th and 97.5th percentiles.

| Model | Metric | Mean | Median | 2.5th–97.5th percentile | N |
|---|---|---:|---:|---:|---:|
| GAM | pearson_r | 0.6212 | 0.6241 | 0.5122–0.7059 | 500 |
| GAM | RMSE | 0.1853 | 0.1847 | 0.1619–0.2134 | 500 |
| RF | pearson_r | 0.6257 | 0.6286 | 0.5127–0.7272 | 500 |
| RF | RMSE | 0.1823 | 0.1818 | 0.1605–0.2073 | 500 |
