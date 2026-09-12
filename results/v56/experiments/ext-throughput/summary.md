All 36 timing records complete. Median of three thread-mean measurements; nanoseconds normalized to four FMOPA, using actual CNTFRQ.
Register-only synthetic diagnostic. No memory loads, coefficient packing, output handling or convolution validation; these numbers are not operator speedups.

| Variant | 1 thread ns/4 FMOPA | 38 threads ns/4 FMOPA | 38-thread cycles at 1.55 GHz (normalized) |
| --- | ---: | ---: | ---: |
| mix0 | 5.161295 | 5.161560 | 8.0004 |
| mix4 | 5.161295 | 5.161520 | 8.0004 |
| mix8 | 5.161295 | 5.161574 | 8.0004 |
| mix16 | 10.322585 | 10.323328 | 16.0012 |
| window_block | 5.161291 | 5.161678 | 8.0006 |
| window_interleaved | 5.161292 | 5.161794 | 8.0008 |
