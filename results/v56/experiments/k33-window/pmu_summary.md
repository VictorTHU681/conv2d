All 24 diagnostic runs completed, 200 steady calls each; four counters have >=99.9% scheduling coverage.
Counters include initialization, warmup and pool spinning. Percentages compare against outline; negative latency is faster.

| Memory | Variant | Mean latency ms (median of two) | Latency change | Instructions | L1 loads | L1 load misses |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| DDR | baseline | 6.1115 | -0.26% | +1.46% | +1.12% | -0.04% |
| DDR | outline | 6.1272 | +0.00% | +0.00% | +0.00% | +0.00% |
| DDR | unroll4 | 6.0829 | -0.72% | -4.48% | -0.03% | +19.57% |
| DDR | ext4 | 6.1377 | +0.17% | -0.88% | -14.93% | -8.43% |
| DDR | tbl4 | 6.1572 | +0.49% | -7.75% | -15.68% | -10.36% |
| DDR | tbl8 | 6.1529 | +0.42% | -8.02% | -17.15% | +1.10% |
| HBM | baseline | 5.8647 | +0.20% | -0.05% | -0.05% | +0.08% |
| HBM | outline | 5.8527 | +0.00% | +0.00% | +0.00% | +0.00% |
| HBM | unroll4 | 5.8505 | -0.04% | -5.32% | -0.63% | +20.23% |
| HBM | ext4 | 5.8529 | +0.00% | -2.03% | -15.96% | -8.37% |
| HBM | tbl4 | 5.8483 | -0.08% | -6.50% | -14.81% | -11.12% |
| HBM | tbl8 | 5.8622 | +0.16% | -7.71% | -17.00% | +1.01% |
