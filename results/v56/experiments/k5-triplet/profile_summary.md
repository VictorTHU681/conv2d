24 instrumented processes, 168 call profiles and 120 timed hashes PASS. Calls 1/2 are validation/warmup and excluded below.
Median of three process medians, each from five timed calls. Actual CNTFRQ converts ticks to time.
Tile-step counts use executed KW+2 for K5 and KW+3 for K4; packing padding is not counted as executed FMOPA.
Kernel timings include preparation/copy/output work inside the measured region; ns/tile-step is amortized cost, not instruction latency.
Instrumentation changes code layout and timing; use uninstrumented screening to decide performance.

| Memory | KH | Variant | Prepare us | Pack mean us | Workers us | Main ns/tile-step | Tail ns/tile-step | Main mean us | Tail mean us |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | baseline | 12.0500 | 18.1920 | 5277.5500 | 1.3814 | 1.6785 | 4443.4370 | 730.6150 |
| DDR | 39 | triplet | 9.6600 | 19.6470 | 5261.7200 | 1.3787 | 1.6958 | 4434.7810 | 738.1290 |
| DDR | 41 | baseline | 10.7900 | 18.4180 | 6081.7500 | 1.3823 | 1.4556 | 4661.8920 | 1267.3280 |
| DDR | 41 | triplet | 8.2300 | 20.8440 | 5903.9600 | 1.3825 | 1.7203 | 4662.9700 | 1054.7030 |
| HBM | 39 | baseline | 12.0400 | 18.0680 | 5236.3100 | 1.3761 | 1.6368 | 4426.3690 | 712.4650 |
| HBM | 39 | triplet | 9.3200 | 18.2880 | 5239.6400 | 1.3753 | 1.6503 | 4423.5800 | 718.3240 |
| HBM | 41 | baseline | 11.1200 | 19.5590 | 5849.7300 | 1.3487 | 1.3892 | 4548.7110 | 1209.4730 |
| HBM | 41 | triplet | 7.8300 | 20.0260 | 5802.0800 | 1.3703 | 1.6867 | 4621.7480 | 1034.1110 |
