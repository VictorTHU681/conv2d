36 processes, 9576 phase records, 180 timed hashes PASS. Saves equal resumes; every call processes 916936 rows across 186 pieces.
Timed calls 3–7: median of six process medians of per-call worker means. Extra counter reads perturb execution; timings include boundary instrumentation and are attribution only.
Restore includes first-chunk ZA zeroing. Publish includes existing diagnostic accounting, ZA save and release. Setup excludes kernel-internal ring initialization; kernel includes that initialization and vector carry.

| Memory | Variant | Chunks/thread | Steals/thread | Claim us | Setup us | ZA restore/zero us | Kernel us | Save/publish us | Last end us |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | baseline | 295.342 | 3.829 | 18.617 | 30.022 | 45.596 | 5636.197 | 53.523 | 5863.635 |
| DDR | grow2 | 155.368 | 4.289 | 20.226 | 34.709 | 14.646 | 5656.876 | 31.622 | 5864.900 |
| DDR | grow4 | 98.368 | 4.289 | 20.001 | 24.504 | 13.304 | 5719.433 | 24.214 | 5951.510 |
| HBM | baseline | 295.342 | 4.053 | 17.962 | 28.527 | 45.977 | 5620.309 | 52.448 | 5832.155 |
| HBM | grow2 | 155.368 | 4.776 | 19.705 | 32.089 | 14.713 | 5592.297 | 31.043 | 5757.530 |
| HBM | grow4 | 98.368 | 5.882 | 19.027 | 21.472 | 12.276 | 5611.265 | 22.867 | 5765.355 |

Host phases are separately timed around preparation/dispatch/join; metadata preparation is included, not hidden outside the measured call.

| Memory | Variant | Prepare us | Dispatch us | Workers us | Mean pack us/thread |
| --- | --- | ---: | ---: | ---: | ---: |
| DDR | baseline | 10.390 | 0.790 | 5865.025 | 21.099 |
| DDR | grow2 | 10.350 | 0.970 | 5866.235 | 19.582 |
| DDR | grow4 | 10.305 | 0.960 | 5952.740 | 19.191 |
| HBM | baseline | 10.465 | 0.875 | 5833.225 | 21.356 |
| HBM | grow2 | 10.175 | 1.060 | 5758.800 | 20.136 |
| HBM | grow4 | 10.515 | 1.075 | 5766.770 | 20.137 |

Worker completion spread; instrumented results, not an accepted score.

| Memory | Variant | Mean end us | Last end us | Last minus mean us |
| --- | --- | ---: | ---: | ---: |
| DDR | baseline | 5819.584 | 5863.635 | 42.045 |
| DDR | grow2 | 5787.525 | 5864.900 | 79.730 |
| DDR | grow4 | 5832.672 | 5951.510 | 128.776 |
| HBM | baseline | 5800.802 | 5832.155 | 35.871 |
| HBM | grow2 | 5719.240 | 5757.530 | 33.811 |
| HBM | grow4 | 5714.455 | 5765.355 | 51.135 |
