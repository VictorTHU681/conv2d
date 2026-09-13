96 original-benchmark full-reference checks PASS, maximum errors zero. Six alternating rounds, five timings per process.
Independent confirmation: accepted local v56 3df5c69 / ebf36923 versus F4 weave 8433e2d4. Median of six process-average GFLOPS. DDR/HBM are separate; no historical percentages are added.

| Memory | KH | Accepted baseline | F4 weave | F4 weave/base |
| --- | ---: | ---: | ---: | ---: |
| DDR | 39 | 14217.1 | 14225.9 | +0.06% |
| DDR | 41 | 14171.0 | 14196.2 | +0.18% |
| DDR | 55 | 14541.5 | 14545.6 | +0.03% |
| DDR | 81 | 15490.5 | 15485.4 | -0.03% |
| HBM | 39 | 14310.2 | 14287.3 | -0.16% |
| HBM | 41 | 14255.9 | 14299.7 | +0.31% |
| HBM | 55 | 14577.8 | 14581.0 | +0.02% |
| HBM | 81 | 15483.5 | 15458.8 | -0.16% |

Observed within-round ranges are not confidence intervals.

| Memory | KH | Median paired change | Paired range | Positive rounds |
| --- | ---: | ---: | --- | ---: |
| DDR | 39 | +0.06% | -0.11% to +3.35% | 5/6 |
| DDR | 41 | +0.15% | -1.86% to +0.70% | 4/6 |
| DDR | 55 | +0.03% | -0.04% to +0.14% | 5/6 |
| DDR | 81 | +0.15% | -0.83% to +0.26% | 4/6 |
| HBM | 39 | -0.26% | -0.53% to +2.00% | 1/6 |
| HBM | 41 | +0.22% | -0.25% to +0.59% | 5/6 |
| HBM | 55 | +0.01% | -0.04% to +1.46% | 3/6 |
| HBM | 81 | -0.13% | -0.66% to +0.21% | 2/6 |
