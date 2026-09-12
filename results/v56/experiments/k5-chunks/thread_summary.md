36 processes, 9576 thread records and 180 timed output hashes PASS; thread step sums match aggregate kernel counts.
Timed calls 3–7 only. Median of six process medians. End times are relative to the first worker start in each call.
Detailed printing happens after workers join and perturbs benchmark wall time; these records characterize workers, not production speed.

| Memory | Variant | Last end us | End spread us | Last end minus mean us | Last worker start us | Last worker main us | Last worker tail us | Tail-majority last workers | Most frequent last IDs |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| DDR | s8 | 6058.085 | 234.900 | 201.758 | 4.225 | 5960.905 | 0.000 | 4/30 | 30:9, 10:3, 37:3, 0:2 |
| DDR | s2 | 5879.810 | 59.390 | 43.933 | 3.475 | 5744.170 | 0.000 | 6/30 | 30:6, 9:3, 37:2, 28:2 |
| DDR | s4 | 5923.770 | 139.785 | 117.015 | 2.160 | 5832.200 | 0.000 | 3/30 | 30:5, 25:2, 7:2, 6:2 |
| HBM | s8 | 5818.360 | 109.330 | 84.201 | 2.595 | 5755.145 | 0.000 | 3/30 | 7:5, 30:3, 8:2, 9:2 |
| HBM | s2 | 5840.935 | 48.100 | 33.461 | 3.230 | 5730.030 | 0.000 | 4/30 | 30:4, 14:3, 10:2, 36:2 |
| HBM | s4 | 5834.705 | 92.985 | 76.268 | 4.195 | 5182.685 | 561.010 | 7/30 | 30:11, 33:3, 2:2, 23:2 |
