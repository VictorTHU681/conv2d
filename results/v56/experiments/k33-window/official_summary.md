All 144 complete-reference checks PASS, maximum errors zero. All six process permutations occur once per shape/memory.
Each value is the median of six process-average GFLOPS values, five timed calls per process.

| Memory | KH=KW | Baseline | Outline | Unroll4 | Outline vs baseline | Unroll4 vs baseline | Unroll4 vs outline |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | 14269.0 | 14236.1 | 14268.5 | -0.23% | -0.00% | +0.23% |
| DDR | 41 | 13719.3 | 13651.6 | 13706.7 | -0.49% | -0.09% | +0.40% |
| DDR | 55 | 14487.8 | 14497.2 | 14497.1 | +0.06% | +0.06% | -0.00% |
| DDR | 81 | 15415.3 | 15434.9 | 15420.2 | +0.13% | +0.03% | -0.10% |
| HBM | 39 | 14332.3 | 14308.9 | 14334.8 | -0.16% | +0.02% | +0.18% |
| HBM | 41 | 14204.6 | 14202.7 | 14224.4 | -0.01% | +0.14% | +0.15% |
| HBM | 55 | 14531.1 | 14540.8 | 14540.8 | +0.07% | +0.07% | +0.00% |
| HBM | 81 | 15420.8 | 15424.0 | 15419.6 | +0.02% | -0.01% | -0.03% |
