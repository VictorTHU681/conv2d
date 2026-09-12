2,984 state/guard cases, 54 runtime output-ownership cases and 640 timed hashes PASS; zero observed active conflicts.
Four Williams-design rounds, five timings per process. Median process-average GFLOPS; screening only. Baseline is local 8b6b295, not published v55.

| Memory | KH | Baseline | Phase setup | ZA carry4 | Both | Phase/base | Carry/base | Both/base |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | 14189.1 | 14185.3 | 14209.1 | 14190.1 | -0.03% | +0.14% | +0.01% |
| DDR | 41 | 14086.5 | 14179.4 | 14137.0 | 14165.9 | +0.66% | +0.36% | +0.56% |
| DDR | 55 | 14547.2 | 14483.5 | 14581.7 | 14490.4 | -0.44% | +0.24% | -0.39% |
| DDR | 81 | 15468.7 | 15487.3 | 15485.2 | 15504.2 | +0.12% | +0.11% | +0.23% |
| HBM | 39 | 14291.8 | 14294.8 | 14301.5 | 14260.5 | +0.02% | +0.07% | -0.22% |
| HBM | 41 | 14248.0 | 14237.7 | 14216.0 | 14213.8 | -0.07% | -0.22% | -0.24% |
| HBM | 55 | 14600.0 | 14519.4 | 14605.4 | 14522.0 | -0.55% | +0.04% | -0.53% |
| HBM | 81 | 15497.0 | 15495.5 | 15438.3 | 15469.8 | -0.01% | -0.38% | -0.18% |
