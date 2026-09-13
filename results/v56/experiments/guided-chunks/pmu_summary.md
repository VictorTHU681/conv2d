24 steady-allocation PMU processes, 200 timed calls each; all four events >=99% running. Six alternating AB/BA rounds of one uninstrumented binary.
Counters span the entire process, including allocation, two initial calls and spinning. This is not the official allocation/timing protocol or a complete correctness check.
Median of six processes. Counter totals below are billions of events per process, not exact events per timed call.

| Memory | Mode | Steady mean ms | Time change vs fixed | Cycles G | Instructions G | L1 loads G | L1 misses G | Miss change vs fixed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | fixed | 5.8363 | +0.00% | 70.0931 | 183.2361 | 45.5420 | 1.5862 | +0.00% |
| DDR | guided | 5.8803 | +0.75% | 70.7262 | 184.3944 | 45.6250 | 1.3920 | -12.25% |
| HBM | fixed | 5.7819 | +0.00% | 69.6856 | 182.9268 | 45.4651 | 1.5843 | +0.00% |
| HBM | guided | 5.7623 | -0.34% | 69.6549 | 183.8540 | 45.4892 | 1.3940 | -12.01% |
