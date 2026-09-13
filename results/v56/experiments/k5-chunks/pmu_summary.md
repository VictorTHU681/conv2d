36 steady-allocation PMU processes, 200 timed calls each; all four events >=99% running. Six balanced process permutations.
Counters span the entire process, including allocation, two initial calls and spinning. This is not the official allocation/timing protocol or a complete correctness check.
Median of six processes. Counter totals below are billions of events per process, not exact events per timed call.

| Memory | Step | Steady mean ms | Time change vs 8 | Cycles G | Instructions G | L1 loads G | L1 misses G | Miss change vs 8 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | 8 | 6.0436 | +0.00% | 72.7028 | 187.8527 | 46.3326 | 1.2339 | +0.00% |
| DDR | 2 | 5.8839 | -2.64% | 70.7343 | 184.7935 | 45.7009 | 1.4261 | +15.57% |
| DDR | 4 | 5.9162 | -2.11% | 71.5282 | 186.7483 | 46.1002 | 1.2967 | +5.09% |
| HBM | 8 | 5.8346 | +0.00% | 70.1659 | 184.2137 | 45.4213 | 1.2274 | +0.00% |
| HBM | 2 | 5.8530 | +0.32% | 70.9389 | 186.6429 | 46.1579 | 1.4278 | +16.32% |
| HBM | 4 | 5.8414 | +0.12% | 70.7582 | 186.4760 | 46.0301 | 1.2958 | +5.57% |
