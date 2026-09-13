3,198 state/guard cases (including NaN-ring controls), 54 runtime output-ownership cases and 640 timed hashes PASS; zero observed active conflicts.
Four Williams-design rounds, five timings per process. Median process-average GFLOPS; screening only. Baseline is local 113d3d6, not published v55.

| Memory | KH | Baseline | K4 EXT | K9 align | Both | EXT/base | Align/base | Both/base |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | 14100.2 | 14165.1 | 14078.6 | 14167.0 | +0.46% | -0.15% | +0.47% |
| DDR | 41 | 13636.3 | 13731.0 | 13635.4 | 13711.5 | +0.69% | -0.01% | +0.55% |
| DDR | 55 | 14526.2 | 14466.5 | 14525.1 | 14463.1 | -0.41% | -0.01% | -0.43% |
| DDR | 81 | 15475.6 | 15446.3 | 15472.2 | 15497.8 | -0.19% | -0.02% | +0.14% |
| HBM | 39 | 14268.8 | 14268.0 | 14228.0 | 14258.9 | -0.00% | -0.29% | -0.07% |
| HBM | 41 | 14209.6 | 14213.2 | 14208.7 | 14191.0 | +0.02% | -0.01% | -0.13% |
| HBM | 55 | 14563.7 | 14530.8 | 14564.2 | 14520.8 | -0.23% | +0.00% | -0.29% |
| HBM | 81 | 15445.2 | 15447.3 | 15421.1 | 15447.2 | +0.01% | -0.16% | +0.01% |
