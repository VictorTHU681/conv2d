96 original full-reference checks PASS; maximum errors zero.
Independent fixed sources, no runtime layout knob. Six alternating orders, five timings/process; median process-average GFLOPS. Baseline is unchanged published v62/v63 cf42580/5a423250. These ratios compare the scalar-tail-unrolled candidate directly to the current production kernel; no gains are added from earlier v62/v63 experiments.

| Memory | KH | v62/v63 | Unroll | Unroll/v62/v63 |
| --- | ---: | ---: | ---: | ---: |
| DDR | 39 | 14154.4 | 14149.6 | -0.03% |
| DDR | 41 | 14363.2 | 14487.4 | +0.86% |
| DDR | 55 | 14480.7 | 14475.9 | -0.03% |
| DDR | 81 | 15509.7 | 15520.1 | +0.07% |
| HBM | 39 | 14245.9 | 14284.2 | +0.27% |
| HBM | 41 | 14440.9 | 14529.9 | +0.62% |
| HBM | 55 | 14526.4 | 14540.0 | +0.09% |
| HBM | 81 | 15481.4 | 15475.4 | -0.04% |

All paired outliers retained; observed ranges are not confidence intervals.
DDR KH39 unroll: paired median +0.10%, range -0.47..+0.70%, positive 3/6
DDR KH41 unroll: paired median +0.89%, range +0.64..+1.09%, positive 6/6
DDR KH55 unroll: paired median +0.01%, range -0.56..+0.12%, positive 3/6
DDR KH81 unroll: paired median +0.03%, range -0.41..+0.38%, positive 4/6
HBM KH39 unroll: paired median +0.25%, range -7.77..+0.66%, positive 4/6
HBM KH41 unroll: paired median +0.66%, range -3.31..+0.83%, positive 5/6
HBM KH55 unroll: paired median +0.08%, range +0.04..+0.32%, positive 6/6
HBM KH81 unroll: paired median -0.01%, range -0.09..+0.11%, positive 3/6
