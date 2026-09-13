32 processes, 8512 phase records, 160 timed hashes PASS. Saves equal resumes; every call processes 916936 rows across 186 pieces.
Timed calls 3–7: median of four process medians of per-call worker means. Extra counter reads perturb execution; timings include boundary instrumentation and are attribution only.
Restore includes first-chunk ZA zeroing. Publish includes existing diagnostic accounting, ZA save and release. Setup excludes kernel-internal ring initialization; kernel includes that initialization and vector carry.

| Memory | Variant | Chunks/thread | Steals/thread | Claim us | Setup us | ZA restore/zero us | Kernel us | Save/publish us | Last end us |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | baseline | 295.342 | 5.316 | 27.209 | 78.783 | 42.658 | 7213.610 | 66.842 | 7510.170 |
| DDR | cached | 295.342 | 5.224 | 23.526 | 30.664 | 68.784 | 7208.572 | 66.839 | 7472.005 |
| DDR | carry4 | 295.342 | 5.184 | 27.483 | 68.751 | 26.875 | 7210.207 | 66.977 | 7477.405 |
| DDR | combined | 295.342 | 4.974 | 23.247 | 35.520 | 57.216 | 7212.933 | 66.851 | 7479.295 |
| HBM | baseline | 295.342 | 5.303 | 25.891 | 76.349 | 41.922 | 7212.898 | 66.381 | 7500.110 |
| HBM | cached | 295.342 | 5.342 | 22.722 | 30.090 | 68.028 | 7208.331 | 66.278 | 7478.655 |
| HBM | carry4 | 295.342 | 5.553 | 27.665 | 68.209 | 26.966 | 7215.912 | 66.819 | 7484.415 |
| HBM | combined | 295.342 | 5.618 | 23.669 | 34.578 | 57.107 | 7208.815 | 66.758 | 7466.300 |

Host phases are separately timed around preparation/dispatch/join; metadata preparation is included, not hidden outside the measured call.

| Memory | Variant | Prepare us | Dispatch us | Workers us | Mean pack us/thread |
| --- | --- | ---: | ---: | ---: | ---: |
| DDR | baseline | 9.855 | 0.915 | 7511.405 | 23.552 |
| DDR | cached | 12.600 | 1.030 | 7473.360 | 27.229 |
| DDR | carry4 | 10.035 | 0.845 | 7478.765 | 24.524 |
| DDR | combined | 12.620 | 1.010 | 7480.780 | 26.925 |
| HBM | baseline | 10.090 | 0.915 | 7501.530 | 23.380 |
| HBM | cached | 12.605 | 0.900 | 7479.960 | 26.612 |
| HBM | carry4 | 9.955 | 0.800 | 7485.660 | 23.581 |
| HBM | combined | 12.340 | 0.915 | 7467.910 | 26.485 |
