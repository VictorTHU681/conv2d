48 processes, 12768 worker records and 240 timed hashes validate; work/table totals invariant across all variants per shape.
Six alternating AB/BA rounds, five timings/process; timed calls 3–7, median of process medians. Instrumentation changes code and is attribution only.

| Memory | KH | Variant | Prepare us | Pair region us/thread | Other regions us/thread | Last end us | Last-minus-mean end us |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | baseline | 18.145 | 4455.716 | 727.122 | 5285.225 | 32.192 |
| DDR | 39 | u4 | 17.745 | 4448.826 | 722.276 | 5266.580 | 28.288 |
| DDR | 41 | baseline | 17.155 | 4662.448 | 931.077 | 5741.765 | 39.994 |
| DDR | 41 | u4 | 16.355 | 4648.834 | 924.024 | 5717.595 | 37.289 |
| HBM | 39 | baseline | 18.480 | 4441.581 | 701.468 | 5253.435 | 47.963 |
| HBM | 39 | u4 | 17.770 | 4414.385 | 700.880 | 5219.545 | 41.685 |
| HBM | 41 | baseline | 17.030 | 4658.297 | 919.882 | 5725.560 | 38.086 |
| HBM | 41 | u4 | 16.025 | 4643.120 | 919.060 | 5708.030 | 41.582 |

Regions include argument setup and ZA restore, not arithmetic-only timings. Per-worker means are not serialized stages; counters cannot identify a physical issue-port cause.
