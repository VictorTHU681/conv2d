54 processes, 14364 worker records and 270 timed hashes validate; work/table totals invariant across all variants per shape.
Three cyclic orders, five timings/process; timed calls 3–7, median of process medians. Instrumentation changes code and is attribution only.

| Memory | KH | Variant | Prepare us | Pair region us/thread | Other regions us/thread | Last end us | Last-minus-mean end us |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| DDR | 41 | baseline | 10.070 | 4651.394 | 1042.361 | 5857.200 | 57.664 |
| DDR | 41 | cf4 | 10.630 | 4656.350 | 1041.442 | 5877.380 | 74.037 |
| DDR | 41 | cf34 | 10.310 | 4650.203 | 1043.551 | 5846.080 | 44.456 |
| DDR | 55 | baseline | 15.530 | 6560.069 | 4308.350 | 11020.810 | 50.403 |
| DDR | 55 | cf4 | 15.210 | 6560.486 | 4311.486 | 11021.220 | 47.094 |
| DDR | 55 | cf34 | 15.410 | 6559.715 | 4311.742 | 11022.590 | 50.206 |
| DDR | 81 | baseline | 13.490 | 19226.643 | 2717.424 | 22227.280 | 140.840 |
| DDR | 81 | cf4 | 13.560 | 19252.653 | 2712.743 | 22218.260 | 106.617 |
| DDR | 81 | cf34 | 13.240 | 19248.132 | 2708.548 | 22221.410 | 124.946 |
| HBM | 41 | baseline | 9.920 | 4636.691 | 1032.998 | 5801.750 | 29.094 |
| HBM | 41 | cf4 | 10.540 | 4639.687 | 1031.691 | 5803.870 | 36.940 |
| HBM | 41 | cf34 | 10.530 | 4632.497 | 1034.397 | 5815.260 | 40.771 |
| HBM | 55 | baseline | 15.440 | 6549.642 | 4306.456 | 10986.020 | 46.083 |
| HBM | 55 | cf4 | 15.450 | 6548.754 | 4305.421 | 10989.570 | 47.233 |
| HBM | 55 | cf34 | 15.560 | 6547.675 | 4309.454 | 10987.910 | 46.382 |
| HBM | 81 | baseline | 13.650 | 19299.899 | 2707.595 | 22280.460 | 134.293 |
| HBM | 81 | cf4 | 13.370 | 19278.266 | 2711.588 | 22230.380 | 143.794 |
| HBM | 81 | cf34 | 13.490 | 19269.837 | 2733.317 | 22252.950 | 126.371 |

Regions include argument setup and ZA restore, not arithmetic-only timings. Per-worker means are not serialized stages; counters cannot identify a physical issue-port cause.
