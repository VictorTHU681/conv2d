32 processes, 8512 worker records and 160 timed hashes validate. Kernel work and table-byte totals are constant for each shape; all thread step totals match aggregate buckets.
Accepted source 1d3f5071 only. Four rotating shape orders, five timings/process. Timed calls 3–7, median of four process medians. Instrumentation is attribution only, not production throughput or an instruction-level timing proof.

| Memory | KH | Prepare us | Dispatch us | Workers us | Mean pack us/thread | Last end us | Last-minus-mean end us | Critical worker main-majority calls |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | 11.750 | 0.735 | 5280.105 | 18.924 | 5278.755 | 32.784 | 18/20 |
| DDR | 41 | 10.210 | 0.720 | 5849.725 | 20.850 | 5848.535 | 63.673 | 16/20 |
| DDR | 55 | 15.605 | 0.770 | 11023.215 | 1.982 | 11022.090 | 49.615 | 17/20 |
| DDR | 81 | 13.705 | 0.785 | 22268.390 | 3.356 | 22267.370 | 118.001 | 18/20 |
| HBM | 39 | 11.760 | 0.785 | 5239.200 | 18.459 | 5238.025 | 50.117 | 20/20 |
| HBM | 41 | 10.335 | 0.705 | 5803.010 | 21.582 | 5801.880 | 39.799 | 16/20 |
| HBM | 55 | 15.410 | 0.770 | 10989.085 | 1.978 | 10987.785 | 43.219 | 17/20 |
| HBM | 81 | 13.660 | 0.725 | 22268.770 | 3.312 | 22267.680 | 126.340 | 19/20 |

Kernel regions include per-chunk argument setup and ZA restore as well as kernel execution. Main bucket combines pair kernels; other buckets separate single-16, K9/K8, and K4/K5. These are per-worker averages, not serialized stages to add to wall time.

| Memory | KH | Pair region us/thread | Single-16 region us/thread | K9/K8 region us/thread | K4/K5 region us/thread |
| --- | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | 4449.402 | 0.000 | 0.000 | 728.640 |
| DDR | 41 | 4641.325 | 0.000 | 0.000 | 1040.097 |
| DDR | 55 | 6560.209 | 3311.206 | 0.000 | 1000.211 |
| DDR | 81 | 19264.762 | 0.000 | 2728.535 | 0.000 |
| HBM | 39 | 4425.961 | 0.000 | 0.000 | 703.934 |
| HBM | 41 | 4635.890 | 0.000 | 0.000 | 1029.766 |
| HBM | 55 | 6546.034 | 3305.805 | 0.000 | 1004.871 |
| HBM | 81 | 19288.185 | 0.000 | 2716.813 | 0.000 |
