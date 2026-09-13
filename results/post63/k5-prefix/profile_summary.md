36 processes, 9576 worker records and 180 timed hashes validate; work/table totals invariant across all variants per shape.
Six complete permutations, five timings/process; timed calls 3–7, median of process medians. Instrumentation changes code and is attribution only.

| Memory | KH | Variant | Prepare us | Pair region us/thread | Other regions us/thread | Last end us | Last-minus-mean end us |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| DDR | 41 | baseline | 17.305 | 4669.996 | 977.742 | 5780.185 | 25.757 |
| DDR | 41 | exact | 16.380 | 4669.862 | 968.216 | 5777.035 | 26.365 |
| DDR | 41 | legacy | 16.720 | 4653.676 | 1016.111 | 5814.050 | 41.894 |
| HBM | 41 | baseline | 17.315 | 4656.776 | 963.250 | 5754.100 | 29.496 |
| HBM | 41 | exact | 16.925 | 4655.511 | 957.159 | 5760.690 | 36.061 |
| HBM | 41 | legacy | 16.180 | 4639.682 | 994.598 | 5770.390 | 27.054 |

Regions include argument setup and ZA restore, not arithmetic-only timings. Per-worker means are not serialized stages; counters cannot identify a physical issue-port cause.
