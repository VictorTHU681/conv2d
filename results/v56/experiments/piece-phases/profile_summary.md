36 processes, 9576 phase records, 180 timed hashes PASS. Saves equal resumes; every call processes 916936 rows across 186 pieces.
Timed calls 3–7: median of six process medians of per-call worker means. Extra counter reads perturb execution; timings include boundary instrumentation and are attribution only.
Restore includes first-chunk ZA zeroing. Publish includes existing diagnostic accounting, ZA save and release. Setup excludes kernel-internal ring initialization; kernel includes that initialization and vector carry.

| Memory | Variant | Chunks/thread | Steals/thread | Claim us | Setup us | ZA restore/zero us | Kernel us | Save/publish us | Last end us |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | baseline | 295.342 | 3.829 | 23.925 | 69.579 | 34.223 | 5626.685 | 54.012 | 5886.965 |
| DDR | phase | 295.342 | 3.539 | 20.169 | 45.875 | 35.639 | 5646.688 | 52.964 | 5882.890 |
| DDR | cached | 295.342 | 3.329 | 18.606 | 25.326 | 52.240 | 5634.199 | 52.493 | 5860.855 |
| HBM | baseline | 295.342 | 3.855 | 22.414 | 68.171 | 33.586 | 5625.193 | 53.056 | 5861.845 |
| HBM | phase | 295.342 | 4.013 | 19.162 | 44.377 | 34.887 | 5621.264 | 52.468 | 5830.020 |
| HBM | cached | 295.342 | 3.947 | 17.691 | 23.410 | 52.317 | 5621.448 | 52.255 | 5835.580 |

Host phases are separately timed around preparation/dispatch/join; metadata preparation is included, not hidden outside the measured call.

| Memory | Variant | Prepare us | Dispatch us | Workers us | Mean pack us/thread |
| --- | --- | ---: | ---: | ---: | ---: |
| DDR | baseline | 8.475 | 0.775 | 5888.035 | 18.702 |
| DDR | phase | 8.370 | 0.840 | 5884.015 | 19.755 |
| DDR | cached | 10.450 | 0.810 | 5861.905 | 21.668 |
| HBM | baseline | 8.640 | 0.775 | 5862.835 | 19.249 |
| HBM | phase | 8.620 | 0.695 | 5831.290 | 19.660 |
| HBM | cached | 10.555 | 0.770 | 5836.710 | 21.181 |
