3,058 state/guard cases, 108 runtime output-ownership cases and 720 timed hashes PASS; zero observed active conflicts.
All six permutations, five timings per process. Median process-average GFLOPS; screening only. Baseline is local 8629457 / 1d3f5071, not published v55.

| Memory | KH | Baseline | Eight slices | Sixteen slices | Eight/base | Sixteen/base |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | 14134.9 | 14140.3 | 13967.5 | +0.04% | -1.18% |
| DDR | 41 | 14124.6 | 14120.5 | 14087.1 | -0.03% | -0.27% |
| DDR | 55 | 14525.5 | 14536.4 | 14451.6 | +0.08% | -0.51% |
| DDR | 81 | 15467.8 | 15475.2 | 15443.8 | +0.05% | -0.16% |
| HBM | 39 | 14228.7 | 14223.6 | 14222.7 | -0.04% | -0.04% |
| HBM | 41 | 14243.0 | 14182.4 | 14163.3 | -0.43% | -0.56% |
| HBM | 55 | 14562.8 | 14582.2 | 14487.8 | +0.13% | -0.52% |
| HBM | 81 | 15479.8 | 15430.5 | 15450.7 | -0.32% | -0.19% |
