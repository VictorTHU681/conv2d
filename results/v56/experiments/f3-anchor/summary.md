1,044 state cases and 640 timed hashes PASS.
Four Williams-design rounds, five timings per process. Median process-average GFLOPS; screening only. Baseline is accepted local 8b6b295, not published v55. Inline F3 layout anchoring is isolated from phase setup.

| Memory | KH | Baseline | Phase | Baseline F3 anchored | Phase F3 anchored | Phase/base | Phase anchor/base anchor | Base anchor/base | Phase anchor/base |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | 14086.4 | 14102.9 | 14140.5 | 14113.3 | +0.12% | -0.19% | +0.38% | +0.19% |
| DDR | 41 | 14115.5 | 14121.0 | 14115.8 | 14109.2 | +0.04% | -0.05% | +0.00% | -0.04% |
| DDR | 55 | 14521.0 | 14464.1 | 14538.4 | 14499.1 | -0.39% | -0.27% | +0.12% | -0.15% |
| DDR | 81 | 15437.5 | 15481.6 | 15468.5 | 15444.2 | +0.29% | -0.16% | +0.20% | +0.04% |
| HBM | 39 | 14272.5 | 14226.5 | 14257.3 | 14232.9 | -0.32% | -0.17% | -0.11% | -0.28% |
| HBM | 41 | 14225.3 | 14183.4 | 14236.8 | 14202.8 | -0.29% | -0.24% | +0.08% | -0.16% |
| HBM | 55 | 14571.8 | 14492.5 | 14568.5 | 14544.6 | -0.54% | -0.16% | -0.02% | -0.19% |
| HBM | 81 | 15448.2 | 15465.4 | 15375.9 | 15444.4 | +0.11% | +0.45% | -0.47% | -0.02% |
