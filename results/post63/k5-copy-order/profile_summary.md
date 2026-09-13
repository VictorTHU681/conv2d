36 processes, 9576 worker records and 180 timed hashes validate; work/table totals invariant across all variants per shape.
Six complete permutations, five timings/process; timed calls 3–7, median of process medians. Instrumentation changes code and is attribution only.

| Memory | KH | Variant | Prepare us | Pair region us/thread | Other regions us/thread | Last end us | Last-minus-mean end us |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| DDR | 41 | baseline | 13.030 | 4657.534 | 932.346 | 5738.140 | 39.704 |
| DDR | 41 | early | 15.275 | 4664.614 | 958.200 | 5764.500 | 28.792 |
| DDR | 41 | spread | 13.205 | 4660.687 | 955.946 | 5755.905 | 30.370 |
| HBM | 41 | baseline | 12.975 | 4655.761 | 919.712 | 5716.820 | 41.919 |
| HBM | 41 | early | 14.715 | 4659.573 | 934.872 | 5741.660 | 38.442 |
| HBM | 41 | spread | 13.000 | 4655.694 | 935.137 | 5736.320 | 38.539 |

Regions include argument setup and ZA restore, not arithmetic-only timings. Per-worker means are not serialized stages; counters cannot identify a physical issue-port cause.
