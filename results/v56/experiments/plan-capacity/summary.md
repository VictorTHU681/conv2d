48 actual shape/thread-switch cases, 1,305 state cases and 224 guards PASS.
96 original-benchmark full-reference checks PASS, maximum errors zero. Six alternating rounds, five timings per process.
Direct comparison: published v55 0a39770 / 489948af versus capacity repair ebf36923. Median of six process-average GFLOPS. DDR/HBM are separate; no historical percentages are added.

| Memory | KH | Published v55 | Capacity repair | Repair/v55 |
| --- | ---: | ---: | ---: | ---: |
| DDR | 39 | 13998.9 | 14227.7 | +1.63% |
| DDR | 41 | 13543.4 | 14139.4 | +4.40% |
| DDR | 55 | 14339.5 | 14547.6 | +1.45% |
| DDR | 81 | 15137.0 | 15483.6 | +2.29% |
| HBM | 39 | 14344.6 | 14282.3 | -0.43% |
| HBM | 41 | 14126.4 | 14281.6 | +1.10% |
| HBM | 55 | 14431.5 | 14581.7 | +1.04% |
| HBM | 81 | 15100.6 | 15462.5 | +2.40% |

Observed within-round ranges are not confidence intervals.

| Memory | KH | Median paired change | Paired range | Positive rounds |
| --- | ---: | ---: | --- | ---: |
| DDR | 39 | +1.41% | -0.41% to +2.32% | 5/6 |
| DDR | 41 | +4.15% | +0.21% to +5.60% | 6/6 |
| DDR | 55 | +1.44% | +1.37% to +1.54% | 6/6 |
| DDR | 81 | +2.21% | +1.85% to +2.42% | 6/6 |
| HBM | 39 | -0.39% | -0.85% to +0.09% | 1/6 |
| HBM | 41 | +1.15% | +0.87% to +1.43% | 6/6 |
| HBM | 55 | +1.04% | +0.94% to +5.83% | 6/6 |
| HBM | 81 | +2.33% | +1.60% to +2.71% | 6/6 |
