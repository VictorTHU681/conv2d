48 processes, 12768 worker records and 240 timed hashes validate; work/table totals invariant across all variants per shape.
Six alternating AB/BA rounds, five timings/process; timed calls 3–7, median of process medians. Instrumentation changes code and is attribution only.

| Memory | KH | Variant | Prepare us | K4 region us/thread | Other regions us/thread | Last end us | Last-minus-mean end us |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | baseline | 18.515 | 729.579 | 4451.931 | 5288.680 | 30.518 |
| DDR | 39 | bits | 17.790 | 724.653 | 4455.262 | 5283.705 | 30.743 |
| DDR | 55 | baseline | 23.590 | 1003.855 | 9869.372 | 11022.075 | 25.979 |
| DDR | 55 | bits | 22.885 | 997.235 | 9908.911 | 11053.865 | 25.131 |
| HBM | 39 | baseline | 18.520 | 716.061 | 4428.449 | 5247.330 | 32.614 |
| HBM | 39 | bits | 18.000 | 698.072 | 4421.974 | 5232.420 | 51.076 |
| HBM | 55 | baseline | 23.620 | 1008.592 | 9849.812 | 10991.260 | 24.553 |
| HBM | 55 | bits | 23.385 | 1002.630 | 9887.407 | 11025.060 | 26.101 |

Regions include argument setup and ZA restore, not arithmetic-only timings. Per-worker means are not serialized stages; counters cannot identify a physical issue-port cause.
