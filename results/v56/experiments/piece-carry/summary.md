Combined candidate: 1,529 state/guard cases and 54 runtime output-ownership cases PASS. All four variants: 640 timed hashes PASS; zero observed active conflicts.
Four Williams-design rounds, five timings per process. Median process-average GFLOPS; screening only. Baseline is local 8b6b295, not published v55.

| Memory | KH | Baseline | Prepared phases | ZA carry4 | Combined | Prepared/base | Carry/base | Combined/base |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | 14161.8 | 14053.1 | 14168.2 | 14157.2 | -0.77% | +0.05% | -0.03% |
| DDR | 41 | 14130.6 | 14073.5 | 14149.3 | 14179.1 | -0.40% | +0.13% | +0.34% |
| DDR | 55 | 14517.0 | 14494.1 | 14557.6 | 14531.8 | -0.16% | +0.28% | +0.10% |
| DDR | 81 | 15455.5 | 15492.0 | 15468.0 | 15494.2 | +0.24% | +0.08% | +0.25% |
| HBM | 39 | 14232.7 | 14262.2 | 14265.0 | 14248.0 | +0.21% | +0.23% | +0.11% |
| HBM | 41 | 14184.0 | 14131.2 | 14197.3 | 14222.5 | -0.37% | +0.09% | +0.27% |
| HBM | 55 | 14571.5 | 14534.0 | 14588.0 | 14554.8 | -0.26% | +0.11% | -0.11% |
| HBM | 81 | 15475.1 | 15447.7 | 15418.4 | 15480.6 | -0.18% | -0.37% | +0.04% |
