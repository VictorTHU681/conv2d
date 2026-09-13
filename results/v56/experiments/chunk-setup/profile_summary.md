32 processes, 8512 phase records, 160 timed hashes PASS. Saves equal resumes; every call processes 916936 rows across 186 pieces.
Timed calls 3–7: median of four process medians of per-call worker means. Extra counter reads perturb execution; timings include boundary instrumentation and are attribution only.
Restore includes first-chunk ZA zeroing. Publish includes existing diagnostic accounting, ZA save and release. Setup excludes kernel-internal ring initialization; kernel includes that initialization and vector carry.

| Memory | Variant | Chunks/thread | Steals/thread | Claim us | Setup us | ZA restore/zero us | Kernel us | Save/publish us | Last end us |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | baseline | 295.342 | 4.158 | 24.454 | 72.863 | 34.142 | 5648.693 | 54.440 | 5924.930 |
| DDR | phase | 295.342 | 3.697 | 20.287 | 45.290 | 35.476 | 5637.867 | 53.089 | 5878.865 |
| DDR | carry4 | 295.342 | 4.132 | 22.066 | 57.028 | 21.202 | 5642.612 | 53.892 | 5869.545 |
| DDR | both | 295.342 | 3.776 | 25.658 | 60.289 | 23.866 | 5643.787 | 53.532 | 5887.550 |
| HBM | baseline | 295.342 | 4.342 | 24.398 | 73.200 | 33.548 | 5632.431 | 54.082 | 5884.870 |
| HBM | phase | 295.342 | 3.868 | 19.049 | 44.001 | 34.484 | 5622.801 | 52.499 | 5826.560 |
| HBM | carry4 | 295.342 | 4.145 | 21.665 | 55.577 | 20.962 | 5626.610 | 53.180 | 5849.860 |
| HBM | both | 295.342 | 4.224 | 25.026 | 59.004 | 23.391 | 5629.866 | 53.162 | 5856.650 |
