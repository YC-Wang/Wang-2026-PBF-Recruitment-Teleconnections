# Appendix Table S2.1. CV-based recruitment uncertainty

Pearson correlation and MSE were calculated separately for each of 500 matched realization IDs using the sampled log10 recruitment targets and the corresponding 40 held-out predictions. MSE is calculated on the log10 recruitment scale. Percentiles are empirical 2.5th and 97.5th percentiles.

| Model | Metric | Mean | Median | 2.5th–97.5th percentile | N |
|---|---|---:|---:|---:|---:|
| GAM | pearson_r | 0.6212 | 0.6241 | 0.5122–0.7059 | 500 |
| GAM | MSE | 0.034524 | 0.034111 | 0.026225–0.045537 | 500 |
| RF | pearson_r | 0.6257 | 0.6286 | 0.5127–0.7272 | 500 |
| RF | MSE | 0.033391 | 0.033068 | 0.025751–0.042978 | 500 |
