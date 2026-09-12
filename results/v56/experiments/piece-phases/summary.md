2,051 state/guard cases, 54 runtime output-ownership cases and 720 timed hashes PASS; zero observed active conflicts.
All six permutations, five timings per process. Median process-average GFLOPS; screening only. Baseline is local 8b6b295, not published v55.

| Memory | KH | Baseline | Phase setup | Prepared piece phases | Phase/base | Prepared/base |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | 14126.3 | 14215.2 | 14130.8 | +0.63% | +0.03% |
| DDR | 41 | 14187.3 | 14157.0 | 14070.2 | -0.21% | -0.83% |
| DDR | 55 | 14545.3 | 14501.4 | 14506.2 | -0.30% | -0.27% |
| DDR | 81 | 15472.9 | 15482.5 | 15501.3 | +0.06% | +0.18% |
| HBM | 39 | 14303.4 | 14297.2 | 14279.8 | -0.04% | -0.16% |
| HBM | 41 | 14217.9 | 14265.6 | 14164.9 | +0.34% | -0.37% |
| HBM | 55 | 14582.4 | 14523.5 | 14544.2 | -0.40% | -0.26% |
| HBM | 81 | 15436.7 | 15491.5 | 15487.5 | +0.35% | +0.33% |
