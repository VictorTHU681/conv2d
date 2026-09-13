24 processes, 6384 phase records, 120 timed hashes PASS. Saves equal resumes; every call processes 916936 rows across 186 pieces.
Timed calls 3–7: median of six process medians of per-call worker means. Extra counter reads perturb execution; timings include boundary instrumentation and are attribution only.
Restore includes first-chunk ZA zeroing. Publish includes existing diagnostic accounting, ZA save and release. Setup excludes kernel-internal ring initialization; kernel includes that initialization and vector carry.

| Memory | Variant | Chunks/thread | Steals/thread | Claim us | Setup us | ZA restore/zero us | Kernel us | Save/publish us | Last end us |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | fixed | 295.342 | 5.737 | 24.447 | 64.025 | 25.167 | 5594.634 | 55.133 | 5845.560 |
| DDR | guided | 155.368 | 4.263 | 20.218 | 35.399 | 14.663 | 5657.544 | 31.634 | 5897.985 |
| HBM | fixed | 295.342 | 6.118 | 24.317 | 62.157 | 25.220 | 5582.137 | 54.820 | 5808.870 |
| HBM | guided | 155.368 | 4.855 | 19.704 | 32.275 | 14.561 | 5591.768 | 31.075 | 5756.115 |

Host phases are separately timed around preparation/dispatch/join; metadata preparation is included, not hidden outside the measured call.

| Memory | Variant | Prepare us | Dispatch us | Workers us | Mean pack us/thread |
| --- | --- | ---: | ---: | ---: | ---: |
| DDR | fixed | 10.275 | 0.695 | 5846.775 | 19.885 |
| DDR | guided | 10.150 | 1.045 | 5899.285 | 20.017 |
| HBM | fixed | 10.595 | 0.740 | 5810.240 | 19.288 |
| HBM | guided | 10.395 | 1.050 | 5757.535 | 19.530 |

Worker completion spread; instrumented results, not an accepted score.

| Memory | Variant | Mean end us | Last end us | Last minus mean us |
| --- | --- | ---: | ---: | ---: |
| DDR | fixed | 5795.412 | 5845.560 | 47.758 |
| DDR | guided | 5788.959 | 5897.985 | 106.915 |
| HBM | fixed | 5779.334 | 5808.870 | 28.010 |
| HBM | guided | 5719.669 | 5756.115 | 34.347 |
