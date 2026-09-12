32 processes, 8512 phase records, 160 timed hashes PASS. Saves equal resumes; every call processes 1372376 rows across 358 pieces.
Timed calls 3–7: median of four process medians of per-call worker means. Extra counter reads perturb execution; timings include boundary instrumentation and are attribution only.
Restore includes first-chunk ZA zeroing. Publish includes existing diagnostic accounting, ZA save and release. Setup excludes kernel-internal ring initialization; kernel includes that initialization and vector carry.

| Memory | Variant | Chunks/thread | Steals/thread | Claim us | Setup us | ZA restore/zero us | Kernel us | Save/publish us | Last end us |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | baseline | 85.632 | 2.079 | 70.193 | 19.801 | 35.847 | 10865.171 | 32.178 | 11084.230 |
| DDR | phase | 85.632 | 2.053 | 69.862 | 19.027 | 34.828 | 10870.680 | 32.446 | 11087.925 |
| DDR | carry4 | 85.632 | 2.276 | 67.270 | 19.920 | 20.271 | 10875.402 | 30.147 | 11068.115 |
| DDR | both | 85.632 | 2.039 | 70.191 | 19.046 | 25.075 | 10860.670 | 31.404 | 11065.750 |
| HBM | baseline | 85.632 | 1.895 | 61.048 | 18.068 | 32.407 | 10862.155 | 26.892 | 11060.395 |
| HBM | phase | 85.632 | 1.855 | 61.492 | 17.407 | 31.959 | 10865.055 | 27.312 | 11059.980 |
| HBM | carry4 | 85.632 | 2.079 | 57.391 | 19.057 | 15.255 | 10865.034 | 24.475 | 11037.360 |
| HBM | both | 85.632 | 1.908 | 62.926 | 17.130 | 22.946 | 10859.584 | 25.931 | 11045.125 |

KH55 kernel-region detail uses existing diagnostic buckets (setup + restore + kernel, not arithmetic-only). The thread tail field combines single-16 and K4; aggregate bucket counts separate them here.

| Memory | Variant | F3 region us/thread | Single-16 region us/thread | K4 region us/thread |
| --- | --- | ---: | ---: | ---: |
| DDR | baseline | 6587.709 | 3317.200 | 1010.101 |
| DDR | phase | 6589.856 | 3318.836 | 1009.632 |
| DDR | carry4 | 6591.987 | 3314.610 | 999.601 |
| DDR | both | 6578.727 | 3311.845 | 1007.573 |
| HBM | baseline | 6580.737 | 3306.854 | 1019.786 |
| HBM | phase | 6577.141 | 3308.347 | 1023.651 |
| HBM | carry4 | 6579.137 | 3307.294 | 1008.300 |
| HBM | both | 6572.012 | 3303.869 | 1018.160 |
