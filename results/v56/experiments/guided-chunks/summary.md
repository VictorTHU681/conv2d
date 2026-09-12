3,580 state/guard cases, 156 runtime output-ownership cases (48 long cases confirm both large and small chunks) and 720 timed hashes PASS; zero observed active conflicts.
All six permutations, five timings per process. Median process-average GFLOPS; screening only. Baseline is local 8629457 / 1d3f5071, not published v55.

| Memory | KH | Baseline | Grow by two | Grow by four | Grow2/base | Grow4/base |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | 14117.4 | 14107.5 | 14136.2 | -0.07% | +0.13% |
| DDR | 41 | 14148.3 | 14067.6 | 13821.0 | -0.57% | -2.31% |
| DDR | 55 | 14514.4 | 14473.0 | 14471.9 | -0.29% | -0.29% |
| DDR | 81 | 15450.1 | 15484.5 | 15480.8 | +0.22% | +0.20% |
| HBM | 39 | 14249.2 | 14246.0 | 14229.7 | -0.02% | -0.14% |
| HBM | 41 | 14242.5 | 14346.7 | 14329.7 | +0.73% | +0.61% |
| HBM | 55 | 14556.0 | 14503.5 | 14501.3 | -0.36% | -0.38% |
| HBM | 81 | 15429.0 | 15439.3 | 15483.1 | +0.07% | +0.35% |
