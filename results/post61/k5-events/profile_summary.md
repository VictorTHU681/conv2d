36 processes, 9576 worker records and 180 timed hashes validate; work/table totals invariant across all variants per shape.
Six complete permutations, five timings/process; timed calls 3–7, median of process medians. Instrumentation changes code and is attribution only.

| Memory | KH | Variant | Prepare us | Pair region us/thread | Other regions us/thread | Last end us | Last-minus-mean end us |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| DDR | 41 | baseline | 13.800 | 4643.485 | 1037.716 | 5835.270 | 52.084 |
| DDR | 41 | clearfirst | 13.695 | 4641.281 | 1043.579 | 5833.325 | 40.746 |
| DDR | 41 | deferclear | 13.610 | 4636.962 | 1037.573 | 5836.085 | 51.994 |
| HBM | 41 | baseline | 14.055 | 4629.246 | 1031.293 | 5801.050 | 34.825 |
| HBM | 41 | clearfirst | 13.580 | 4631.245 | 1035.833 | 5794.840 | 25.127 |
| HBM | 41 | deferclear | 13.470 | 4632.792 | 1030.249 | 5788.775 | 21.999 |

Regions include argument setup and ZA restore, not arithmetic-only timings. Per-worker means are not serialized stages; counters cannot identify a physical issue-port cause.
