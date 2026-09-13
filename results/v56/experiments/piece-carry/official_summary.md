144 official full-reference checks PASS, all maximum errors zero. Six permutations; five timings per process.
Median of six process-average GFLOPS. Baseline is accepted local v56 8b6b295, not published v55.

| Memory | KH | Baseline | ZA carry4 | Prepared + carry4 | Carry/base | Combined/base |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | 14200.5 | 14228.9 | 14217.0 | +0.20% | +0.12% |
| DDR | 41 | 14143.0 | 14138.2 | 14180.6 | -0.03% | +0.27% |
| DDR | 55 | 14545.6 | 14557.4 | 14539.7 | +0.08% | -0.04% |
| DDR | 81 | 15470.8 | 15462.9 | 15455.4 | -0.05% | -0.10% |
| HBM | 39 | 14288.7 | 14292.8 | 14290.2 | +0.03% | +0.01% |
| HBM | 41 | 14213.8 | 14225.5 | 14292.9 | +0.08% | +0.56% |
| HBM | 55 | 14584.2 | 14592.5 | 14581.3 | +0.06% | -0.02% |
| HBM | 81 | 15490.5 | 15456.8 | 15477.9 | -0.22% | -0.08% |

Paired within-round consistency; observed ranges are not confidence intervals.

| Memory | KH | Candidate | Median paired change | Paired range | Positive rounds |
| --- | ---: | --- | ---: | --- | ---: |
| DDR | 39 | carry4 | +0.29% | -0.20% to +0.46% | 5/6 |
| DDR | 39 | combined | +0.11% | -0.33% to +0.48% | 3/6 |
| DDR | 41 | carry4 | +0.20% | -0.35% to +0.76% | 4/6 |
| DDR | 41 | combined | +0.48% | -0.49% to +1.01% | 4/6 |
| DDR | 55 | carry4 | +0.09% | -0.72% to +0.16% | 5/6 |
| DDR | 55 | combined | -0.02% | -0.12% to +0.04% | 3/6 |
| DDR | 81 | carry4 | +0.02% | -0.92% to +0.36% | 4/6 |
| DDR | 81 | combined | -0.06% | -0.28% to +0.08% | 2/6 |
| HBM | 39 | carry4 | -0.05% | -0.23% to +0.57% | 3/6 |
| HBM | 39 | combined | -0.01% | -6.95% to +0.50% | 3/6 |
| HBM | 41 | carry4 | +0.09% | -0.25% to +7.80% | 4/6 |
| HBM | 41 | combined | +0.53% | -0.01% to +9.03% | 5/6 |
| HBM | 55 | carry4 | +0.06% | -0.02% to +0.10% | 5/6 |
| HBM | 55 | combined | -0.02% | -0.11% to +0.07% | 2/6 |
| HBM | 81 | carry4 | -0.26% | -0.62% to +0.44% | 2/6 |
| HBM | 81 | combined | -0.05% | -0.71% to +0.53% | 3/6 |
