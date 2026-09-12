24 profiled processes, 168 calls, 120 timed output hashes PASS.
Median of six process medians, each taking only timed calls 3–7. CNTFRQ converts ticks to time.
Instrumented timings support attribution, not official performance acceptance.
Per-call kf bytes: 209,952 -> 104,976; unique R bytes remain 844,992. This counts logical written payload, not PMU cache traffic.

| Memory | Variant | Prepare us | Dispatch us | Workers us | Pack mean us | Pack max us | Main ns/tile | K9 ns/tile |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | baseline | 14.740 | 0.850 | 22305.320 | 3.692 | 103.785 | 1.348657 | 1.505621 |
<!-- DDR baseline: main mean 19280.967 us, K9 mean 2745.641 us -->
| DDR | merged | 11.310 | 0.300 | 22293.555 | 2.939 | 95.555 | 1.349287 | 1.492633 |
<!-- DDR merged: main mean 19289.978 us, K9 mean 2721.956 us -->
| HBM | baseline | 14.755 | 0.850 | 22297.135 | 3.646 | 103.850 | 1.349813 | 1.494838 |
<!-- HBM baseline: main mean 19297.476 us, K9 mean 2725.977 us -->
| HBM | merged | 11.440 | 0.285 | 22314.635 | 2.998 | 95.650 | 1.349545 | 1.497209 |
<!-- HBM merged: main mean 19293.662 us, K9 mean 2730.301 us -->
