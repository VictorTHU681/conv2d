36 processes, 9576 phase records, 180 timed hashes PASS. Saves equal resumes; every call processes 916936 rows across 186 pieces.
Timed calls 3–7: median of six process medians of per-call worker means. Extra counter reads perturb execution; timings include boundary instrumentation and are attribution only.
Restore includes first-chunk ZA zeroing. Publish includes existing diagnostic accounting, ZA save and release. Setup excludes kernel-internal ring initialization; kernel includes that initialization and vector carry.

| Memory | Step | Chunks/thread | Steals/thread | Claim us | Setup us | ZA restore/zero us | Kernel us | Save/publish us | Last end us |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | s8 | 75.368 | 1.105 | 17.486 | 17.560 | 22.004 | 5694.427 | 18.592 | 5925.180 |
| DDR | s2 | 295.342 | 3.974 | 22.474 | 64.806 | 34.128 | 5629.490 | 53.226 | 5888.160 |
| DDR | s4 | 149.711 | 2.382 | 18.215 | 32.700 | 24.415 | 5655.831 | 28.957 | 5888.915 |
| HBM | s8 | 75.368 | 1.276 | 14.517 | 15.819 | 19.419 | 5631.449 | 17.284 | 5811.775 |
| HBM | s2 | 295.342 | 3.882 | 21.018 | 63.044 | 33.369 | 5620.235 | 51.905 | 5858.670 |
| HBM | s4 | 149.711 | 2.553 | 16.189 | 31.077 | 23.038 | 5624.886 | 27.707 | 5806.890 |
