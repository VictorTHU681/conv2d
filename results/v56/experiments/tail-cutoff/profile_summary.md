32 processes, 8512 phase records, 160 timed hashes PASS. Saves equal resumes; every call processes 916936 rows across 186 pieces.
Timed calls 3–7: median of four process medians of per-call worker means. Extra counter reads perturb execution; timings include boundary instrumentation and are attribution only.
Publish also includes the completed-piece atomic decrement in cutoff variants.
Restore includes first-chunk ZA zeroing. Publish includes existing diagnostic accounting, ZA save and release. Setup excludes kernel-internal ring initialization; kernel includes that initialization and vector carry.

| Memory | Variant | Chunks/thread | Steals/thread | Claim us | Setup us | ZA restore/zero us | Kernel us | Save/publish us | Last end us |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | baseline | 295.342 | 3.842 | 18.931 | 29.723 | 45.095 | 5638.363 | 53.243 | 5870.050 |
| DDR | guided | 155.368 | 4.500 | 20.207 | 34.259 | 14.927 | 5653.511 | 32.063 | 5882.490 |
| DDR | cut2 | 155.461 | 4.421 | 17.538 | 29.801 | 16.311 | 5653.680 | 32.315 | 5860.390 |
| DDR | cut4 | 205.434 | 5.079 | 18.622 | 36.510 | 19.693 | 5652.771 | 40.158 | 5864.060 |
| HBM | baseline | 295.342 | 4.211 | 18.192 | 28.288 | 45.388 | 5621.006 | 52.178 | 5834.075 |
| HBM | guided | 155.368 | 4.947 | 19.772 | 31.694 | 14.416 | 5590.598 | 31.187 | 5767.525 |
| HBM | cut2 | 155.382 | 4.803 | 16.091 | 26.559 | 15.484 | 5600.612 | 31.115 | 5757.960 |
| HBM | cut4 | 204.908 | 5.592 | 17.774 | 33.455 | 18.955 | 5590.370 | 39.360 | 5768.090 |

Host phases are separately timed around preparation/dispatch/join; metadata preparation is included, not hidden outside the measured call.

| Memory | Variant | Prepare us | Dispatch us | Workers us | Mean pack us/thread |
| --- | --- | ---: | ---: | ---: | ---: |
| DDR | baseline | 10.130 | 0.750 | 5871.325 | 20.512 |
| DDR | guided | 10.080 | 0.980 | 5883.660 | 20.212 |
| DDR | cut2 | 10.335 | 1.035 | 5861.550 | 19.366 |
| DDR | cut4 | 10.380 | 1.040 | 5865.345 | 19.862 |
| HBM | baseline | 10.330 | 0.720 | 5835.210 | 21.401 |
| HBM | guided | 10.155 | 1.020 | 5768.670 | 19.187 |
| HBM | cut2 | 10.360 | 1.045 | 5759.180 | 18.859 |
| HBM | cut4 | 10.540 | 0.935 | 5769.455 | 18.459 |

Worker completion spread; instrumented results, not an accepted score.

| Memory | Variant | Mean end us | Last end us | Last minus mean us |
| --- | --- | ---: | ---: | ---: |
| DDR | baseline | 5819.478 | 5870.050 | 55.143 |
| DDR | guided | 5784.329 | 5882.490 | 87.146 |
| DDR | cut2 | 5782.374 | 5860.390 | 83.410 |
| DDR | cut4 | 5799.052 | 5864.060 | 80.016 |
| HBM | baseline | 5798.690 | 5834.075 | 38.429 |
| HBM | guided | 5715.835 | 5767.525 | 48.864 |
| HBM | cut2 | 5718.105 | 5757.960 | 36.885 |
| HBM | cut4 | 5730.589 | 5768.090 | 36.197 |
