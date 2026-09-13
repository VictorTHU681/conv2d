96 original full-reference checks PASS; maximum errors zero.
Independent fixed sources, no runtime layout knob. Six alternating orders, five timings/process; median process-average GFLOPS. Baseline is current upstream b6ea996/138dcac source 08400a76. These ratios compare short-loop alignment directly to that baseline; no gains are added from earlier experiments.

| Memory | KH | Upstream | Aligned | Aligned/upstream |
| --- | ---: | ---: | ---: | ---: |
| DDR | 39 | 14125.2 | 14152.6 | +0.19% |
| DDR | 41 | 14422.2 | 14413.1 | -0.06% |
| DDR | 55 | 14495.8 | 14501.0 | +0.04% |
| DDR | 81 | 15474.6 | 15482.0 | +0.05% |
| HBM | 39 | 14265.7 | 14241.7 | -0.17% |
| HBM | 41 | 14477.8 | 14472.2 | -0.04% |
| HBM | 55 | 14538.8 | 14538.0 | -0.01% |
| HBM | 81 | 15492.3 | 15461.9 | -0.20% |

All paired outliers retained; observed ranges are not confidence intervals.
DDR KH39 aligned: paired median +0.22%, range -0.52..+1.05%, positive 4/6
DDR KH41 aligned: paired median -0.04%, range -0.40..+4.48%, positive 2/6
DDR KH55 aligned: paired median -0.02%, range -0.78..+0.05%, positive 2/6
DDR KH81 aligned: paired median +0.04%, range -0.22..+0.39%, positive 3/6
HBM KH39 aligned: paired median -0.02%, range -0.61..+1.61%, positive 3/6
HBM KH41 aligned: paired median -0.08%, range -0.22..+0.16%, positive 2/6
HBM KH55 aligned: paired median -0.03%, range -0.12..+0.07%, positive 2/6
HBM KH81 aligned: paired median -0.18%, range -2.79..+0.14%, positive 2/6
