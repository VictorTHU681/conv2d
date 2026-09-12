3,058 state/guard cases, 108 runtime output-ownership cases and 720 timed hashes PASS; zero observed active conflicts.
All six permutations, five timings per process. Median process-average GFLOPS; screening only. Baseline is local 8629457 / 1d3f5071, not published v55.

| Memory | KH | Baseline | Early restore and zero | Early restore only | Early/base | Load early/base |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | 14157.5 | 14119.8 | 14140.7 | -0.27% | -0.12% |
| DDR | 41 | 14174.5 | 14152.1 | 14180.0 | -0.16% | +0.04% |
| DDR | 55 | 14527.9 | 14499.8 | 14528.6 | -0.19% | +0.01% |
| DDR | 81 | 15478.9 | 15505.1 | 15457.0 | +0.17% | -0.14% |
| HBM | 39 | 14215.0 | 14236.5 | 14214.2 | +0.15% | -0.01% |
| HBM | 41 | 14220.1 | 14209.4 | 14218.5 | -0.08% | -0.01% |
| HBM | 55 | 14553.2 | 14539.6 | 14564.9 | -0.09% | +0.08% |
| HBM | 81 | 15470.7 | 15466.2 | 15473.5 | -0.03% | +0.02% |
