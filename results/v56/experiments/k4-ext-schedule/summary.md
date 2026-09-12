Interleaved candidate: 2,014 state/guard cases (including NaN-ring controls), 54 runtime output-ownership cases and 720 timed hashes PASS; zero observed active conflicts.
All six permutations, five timings per process. Median process-average GFLOPS; screening only. Baseline is local 8b6b295, not published v55.

| Memory | KH | Baseline | Blocked EXT | Interleaved EXT | Blocked/base | Interleaved/base | Interleaved/blocked |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | 14197.9 | 14193.9 | 14180.7 | -0.03% | -0.12% | -0.09% |
| DDR | 41 | 14122.0 | 14081.5 | 14116.8 | -0.29% | -0.04% | +0.25% |
| DDR | 55 | 14545.2 | 14477.9 | 14488.5 | -0.46% | -0.39% | +0.07% |
| DDR | 81 | 15474.6 | 15483.1 | 15457.5 | +0.05% | -0.11% | -0.17% |
| HBM | 39 | 14280.4 | 14280.5 | 14297.9 | +0.00% | +0.12% | +0.12% |
| HBM | 41 | 14218.2 | 14178.3 | 14150.9 | -0.28% | -0.47% | -0.19% |
| HBM | 55 | 14577.0 | 14530.3 | 14555.0 | -0.32% | -0.15% | +0.17% |
| HBM | 81 | 15470.1 | 15470.0 | 15477.4 | -0.00% | +0.05% | +0.05% |
