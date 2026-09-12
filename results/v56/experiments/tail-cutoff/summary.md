3,580 state/guard cases, 156 runtime output-ownership cases (48 long cases confirm both large and small chunks) and 640 timed hashes PASS; zero observed active conflicts.
Four Williams orders, five timings per process. Median process-average GFLOPS; screening only. Baseline is local 8629457 / 1d3f5071, not published v55.

| Memory | KH | Baseline | Unguarded guidance | Cutoff 2*threads | Cutoff 4*threads | Guided/base | Cut2/base | Cut4/base |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | 14178.4 | 14187.7 | 14208.8 | 14208.0 | +0.07% | +0.21% | +0.21% |
| DDR | 41 | 14153.0 | 14048.2 | 14177.1 | 14125.1 | -0.74% | +0.17% | -0.20% |
| DDR | 55 | 14542.6 | 14495.9 | 14567.7 | 14569.8 | -0.32% | +0.17% | +0.19% |
| DDR | 81 | 15495.5 | 15516.8 | 15500.4 | 15420.4 | +0.14% | +0.03% | -0.48% |
| HBM | 39 | 14265.8 | 14277.9 | 14291.2 | 14287.3 | +0.09% | +0.18% | +0.15% |
| HBM | 41 | 14253.9 | 14379.2 | 14433.0 | 14374.9 | +0.88% | +1.26% | +0.85% |
| HBM | 55 | 14576.6 | 14533.0 | 14596.3 | 14606.7 | -0.30% | +0.14% | +0.21% |
| HBM | 81 | 15450.8 | 15468.8 | 15443.0 | 15467.2 | +0.12% | -0.05% | +0.11% |
