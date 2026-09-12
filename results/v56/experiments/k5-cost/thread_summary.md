36 processes, 9576 thread records and 180 timed output hashes PASS; thread step sums match aggregate kernel counts.
Timed calls 3–7 only. Median of six process medians. End times are relative to the first worker start in each call.
Detailed printing happens after workers join and perturbs benchmark wall time; these records characterize workers, not production speed.

| Memory | Variant | Last end us | End spread us | Last end minus mean us | Last worker start us | Last worker main us | Last worker tail us | Tail-majority last workers | Most frequent last IDs |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| DDR | baseline | 6040.800 | 102.830 | 73.141 | 4.020 | 5622.505 | 307.390 | 12/30 | 36:5, 29:5, 37:4, 21:2 |
| DDR | triplet | 6049.055 | 236.985 | 199.394 | 3.545 | 5963.625 | 0.000 | 3/30 | 30:5, 26:3, 5:2, 1:2 |
| DDR | k5cost | 6010.180 | 181.205 | 136.247 | 4.725 | 293.010 | 5663.450 | 20/30 | 31:8, 35:4, 36:2, 34:2 |
| HBM | baseline | 5849.175 | 58.335 | 29.685 | 3.735 | 5662.095 | 127.025 | 10/30 | 29:8, 34:3, 6:3, 37:2 |
| HBM | triplet | 5816.420 | 108.970 | 84.851 | 2.450 | 5751.455 | 0.000 | 3/30 | 17:3, 0:2, 2:2, 10:2 |
| HBM | k5cost | 5861.270 | 159.355 | 131.347 | 4.480 | 5797.195 | 0.000 | 4/30 | 30:15, 31:3, 11:2, 5:2 |
