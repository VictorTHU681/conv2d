54 processes, 14364 worker records and 270 timed hashes validate; work/table totals invariant across all variants per shape.
Three cyclic orders, five timings/process; timed calls 3–7, median of process medians. Instrumentation changes code and is attribution only.

| Memory | KH | Variant | Prepare us | Pair region us/thread | Other regions us/thread | Last end us | Last-minus-mean end us |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| DDR | 41 | baseline | 10.590 | 4642.034 | 1041.177 | 5838.410 | 59.529 |
| DDR | 41 | f4 | 10.830 | 4637.015 | 1036.298 | 5814.160 | 41.222 |
| DDR | 41 | f34 | 10.290 | 4639.691 | 1035.919 | 5827.390 | 49.438 |
| DDR | 55 | baseline | 15.390 | 6560.423 | 4311.270 | 11019.870 | 50.233 |
| DDR | 55 | f4 | 15.480 | 6558.109 | 4309.587 | 11013.230 | 47.262 |
| DDR | 55 | f34 | 15.170 | 6551.693 | 4309.159 | 11007.040 | 47.659 |
| DDR | 81 | baseline | 13.780 | 19254.336 | 2704.754 | 22303.810 | 134.848 |
| DDR | 81 | f4 | 13.520 | 19266.064 | 2718.113 | 22264.990 | 133.744 |
| DDR | 81 | f34 | 13.460 | 19243.199 | 2702.028 | 22207.950 | 122.319 |
| HBM | 41 | baseline | 10.330 | 4633.472 | 1031.538 | 5801.540 | 29.095 |
| HBM | 41 | f4 | 10.140 | 4630.866 | 1032.896 | 5800.130 | 41.974 |
| HBM | 41 | f34 | 10.020 | 4627.290 | 1029.908 | 5795.070 | 36.011 |
| HBM | 55 | baseline | 15.270 | 6546.131 | 4306.465 | 10983.770 | 46.476 |
| HBM | 55 | f4 | 15.450 | 6548.211 | 4306.901 | 10986.590 | 46.598 |
| HBM | 55 | f34 | 15.360 | 6541.800 | 4304.073 | 10978.990 | 45.355 |
| HBM | 81 | baseline | 13.680 | 19274.545 | 2727.866 | 22290.300 | 116.447 |
| HBM | 81 | f4 | 13.910 | 19245.075 | 2721.364 | 22250.640 | 139.991 |
| HBM | 81 | f34 | 13.420 | 19268.407 | 2725.610 | 22239.140 | 146.419 |

Regions include argument setup and ZA restore, not arithmetic-only timings. Per-worker means are not serialized stages; counters cannot identify a physical issue-port cause.
