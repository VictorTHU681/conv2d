36 processes, 9576 worker records and 180 timed hashes validate; work/table totals invariant across all variants per shape.
Six complete permutations, five timings/process; timed calls 3–7, median of process medians. Instrumentation changes code and is attribution only.

| Memory | KH | Variant | Prepare us | Pair region us/thread | Other regions us/thread | Last end us | Last-minus-mean end us |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| DDR | 41 | baseline | 17.600 | 4666.148 | 977.252 | 5780.415 | 25.245 |
| DDR | 41 | guard | 18.355 | 4666.843 | 968.316 | 5773.040 | 24.462 |
| DDR | 41 | unroll | 17.575 | 4667.869 | 935.099 | 5746.870 | 34.705 |
| HBM | 41 | baseline | 17.805 | 4654.447 | 963.027 | 5751.785 | 28.618 |
| HBM | 41 | guard | 18.715 | 4654.172 | 957.058 | 5744.155 | 29.455 |
| HBM | 41 | unroll | 18.020 | 4658.738 | 920.832 | 5725.100 | 41.541 |

Regions include argument setup and ZA restore, not arithmetic-only timings. Per-worker means are not serialized stages; counters cannot identify a physical issue-port cause.
