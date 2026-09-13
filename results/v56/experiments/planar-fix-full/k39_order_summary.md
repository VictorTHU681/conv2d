36 uninstrumented full-reference checks and 6 diagnostic full-reference checks PASS, all maximum errors 0.
All process positions and all 30 ordered predecessor pairs are balanced.

| Variant | Median GFLOPS | vs baseline | Min GFLOPS | Max GFLOPS |
| --- | ---: | ---: | ---: | ---: |
| baseline | 14347.2 | +0.00% | 14327.4 | 14375.3 |
| upstream | 14326.4 | -0.15% | 14313.5 | 14366.8 |
| mergedfixed_p3 | 14354.4 | +0.05% | 14123.2 | 14364.2 |
| mergedfixed | 14323.0 | -0.17% | 14288.0 | 14378.5 |
| mergedfixed_p2 | 14356.7 | +0.07% | 14338.8 | 14362.4 |
| mergedfixed_p1 | 14344.1 | -0.02% | 14326.9 | 14397.1 |

Runtime-profile medians of the final two timed calls; validation and warmup excluded.
Cycles are the existing counter normalization at 1.55 GHz, not per-instruction latency or IPC.
| Variant | Pair cycles/tile-step | K4 cycles/tile-step | Pair work time % | K4 work time % |
| --- | ---: | ---: | ---: | ---: |
| baseline | 2.13 | 2.52 | 85.60 | 14.40 |
| upstream | 2.13 | 2.41 | 86.20 | 13.80 |
| mergedfixed | 2.12 | 2.44 | 86.00 | 14.00 |
| mergedfixed_p1 | 2.13 | 2.45 | 86.00 | 14.00 |
| mergedfixed_p2 | 2.13 | 2.44 | 86.00 | 14.00 |
| mergedfixed_p3 | 2.13 | 2.44 | 86.05 | 13.95 |
