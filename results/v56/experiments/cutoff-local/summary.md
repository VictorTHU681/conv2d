1,790 state/guard cases, 78 runtime output-ownership cases (24 long cases confirm both large and small chunks) and 720 timed hashes PASS; zero observed active conflicts.
All six permutations, five timings per process. Median process-average GFLOPS; screening only. Baseline is local 8629457 / 1d3f5071, not published v55.

| Memory | KH | Baseline | Global cutoff | Local check first | Cutoff/base | Local/base |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | 14165.5 | 14172.5 | 14237.4 | +0.05% | +0.51% |
| DDR | 41 | 14159.5 | 14086.5 | 14152.5 | -0.52% | -0.05% |
| DDR | 55 | 14540.2 | 14556.1 | 14589.6 | +0.11% | +0.34% |
| DDR | 81 | 15465.3 | 15502.6 | 15461.0 | +0.24% | -0.03% |
| HBM | 39 | 14286.1 | 14275.8 | 14323.9 | -0.07% | +0.26% |
| HBM | 41 | 14252.5 | 14393.2 | 14426.4 | +0.99% | +1.22% |
| HBM | 55 | 14573.2 | 14585.1 | 14620.5 | +0.08% | +0.32% |
| HBM | 81 | 15466.0 | 15477.5 | 15477.5 | +0.07% | +0.07% |
