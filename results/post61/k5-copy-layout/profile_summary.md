36 processes, 9576 worker records and 180 timed hashes validate; work/table totals invariant across all variants per shape.
Six complete permutations, five timings/process; timed calls 3–7, median of process medians. Instrumentation changes code and is attribution only.

| Memory | KH | Variant | Prepare us | Pair region us/thread | Other regions us/thread | Last end us | Last-minus-mean end us |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| DDR | 41 | baseline | 18.975 | 5980.049 | 1307.003 | 7465.160 | 43.554 |
| DDR | 41 | exact | 18.665 | 5985.499 | 1254.321 | 7404.690 | 33.773 |
| DDR | 41 | triples | 19.280 | 5982.271 | 1250.653 | 7401.310 | 34.191 |
| HBM | 41 | baseline | 18.605 | 5982.896 | 1308.563 | 7458.110 | 36.934 |
| HBM | 41 | exact | 19.020 | 5986.879 | 1262.154 | 7414.815 | 33.260 |
| HBM | 41 | triples | 19.065 | 5985.841 | 1251.175 | 7404.560 | 33.103 |

Regions include argument setup and ZA restore, not arithmetic-only timings. Per-worker means are not serialized stages; counters cannot identify a physical issue-port cause.
