96 original full-reference checks PASS; maximum errors zero.
Independent fixed sources, no runtime layout knob. Six alternating orders, five timings/process; median process-average GFLOPS. Baseline is current upstream b6ea996/138dcac source 08400a76. These ratios compare K4 scalar bit branches directly to that baseline; no gains are added from earlier experiments.

| Memory | KH | Upstream | Bits | Bits/upstream |
| --- | ---: | ---: | ---: | ---: |
| DDR | 39 | 14139.0 | 14148.4 | +0.07% |
| DDR | 41 | 14433.2 | 14454.2 | +0.15% |
| DDR | 55 | 14497.1 | 14553.8 | +0.39% |
| DDR | 81 | 15475.6 | 15476.8 | +0.01% |
| HBM | 39 | 14238.2 | 14255.4 | +0.12% |
| HBM | 41 | 14492.2 | 14500.9 | +0.06% |
| HBM | 55 | 14538.0 | 14589.4 | +0.35% |
| HBM | 81 | 15509.7 | 15465.4 | -0.29% |

All paired outliers retained; observed ranges are not confidence intervals.
DDR KH39 bits: paired median -0.01%, range -0.23..+1.05%, positive 3/6
DDR KH41 bits: paired median +0.09%, range -0.04..+0.47%, positive 5/6
DDR KH55 bits: paired median +0.37%, range +0.34..+0.46%, positive 6/6
DDR KH81 bits: paired median +0.02%, range -0.33..+0.25%, positive 3/6
HBM KH39 bits: paired median +0.10%, range -0.23..+0.39%, positive 4/6
HBM KH41 bits: paired median +0.09%, range -3.83..+0.35%, positive 4/6
HBM KH55 bits: paired median +0.37%, range +0.33..+0.43%, positive 6/6
HBM KH81 bits: paired median -0.26%, range -0.50..+0.47%, positive 1/6
