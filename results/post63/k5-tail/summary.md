3,058 state/guard cases, 1,148 extended cases, 108 output-ownership cases and 720 timed hashes PASS; zero observed active conflicts.
Six permutations, five timings/process. Median process-average GFLOPS, screening only. Three fixed executables: unchanged v62/v63 baseline cf42580/5a423250, empty-vector-tail bypass (guard), and scalar-tail unrolling (unroll). No runtime experiment knob. Ratios use this same-job v62 baseline.

| Memory | KH | Baseline | Empty-tail guard | Scalar unroll | Guard/base | Unroll/base |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | 14139.7 | 14101.1 | 14133.6 | -0.27% | -0.04% |
| DDR | 41 | 14338.8 | 14378.8 | 14456.7 | +0.28% | +0.82% |
| DDR | 55 | 14497.3 | 14493.8 | 14498.8 | -0.02% | +0.01% |
| DDR | 81 | 15488.0 | 15476.8 | 15483.5 | -0.07% | -0.03% |
| HBM | 39 | 14277.4 | 14259.0 | 14293.0 | -0.13% | +0.11% |
| HBM | 41 | 14438.0 | 14433.7 | 14498.7 | -0.03% | +0.42% |
| HBM | 55 | 14542.0 | 14532.8 | 14536.9 | -0.06% | -0.04% |
| HBM | 81 | 15464.0 | 15474.8 | 15470.2 | +0.07% | +0.04% |

Observed paired ranges retain all outliers and are not confidence intervals.
DDR KH39 guard: paired median -0.12%, range -3.04..+0.06%, positive 3/6
DDR KH39 unroll: paired median +0.08%, range -0.33..+0.26%, positive 3/6
DDR KH41 guard: paired median +0.48%, range +0.00..+2.58%, positive 6/6
DDR KH41 unroll: paired median +0.82%, range +0.64..+3.03%, positive 6/6
DDR KH55 guard: paired median -0.03%, range -0.51..+0.31%, positive 2/6
DDR KH55 unroll: paired median +0.04%, range -0.10..+0.30%, positive 4/6
DDR KH81 guard: paired median -0.05%, range -0.42..+0.67%, positive 3/6
DDR KH81 unroll: paired median -0.04%, range -0.18..+0.08%, positive 3/6
HBM KH39 guard: paired median -0.13%, range -0.42..+0.24%, positive 2/6
HBM KH39 unroll: paired median +0.06%, range -0.52..+0.45%, positive 4/6
HBM KH41 guard: paired median -0.03%, range -3.34..+0.14%, positive 3/6
HBM KH41 unroll: paired median +0.42%, range +0.18..+0.49%, positive 6/6
HBM KH55 guard: paired median -0.06%, range -0.14..-0.01%, positive 0/6
HBM KH55 unroll: paired median -0.05%, range -0.10..+0.11%, positive 1/6
HBM KH81 guard: paired median +0.02%, range -0.13..+0.13%, positive 3/6
HBM KH81 unroll: paired median +0.01%, range -0.30..+0.52%, positive 4/6
