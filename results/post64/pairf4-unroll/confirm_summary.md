96 original full-reference checks PASS; maximum errors zero.
Independent fixed sources, no runtime layout knob. Six alternating orders, five timings/process; median process-average GFLOPS. Baseline is published v64 3f8c8c2/0136da05. These ratios compare short pairf4 compute unrolling directly to v64; no gains are added from earlier experiments.

| Memory | KH | v64 | U4 | U4/v64 |
| --- | ---: | ---: | ---: | ---: |
| DDR | 39 | 14136.0 | 14208.2 | +0.51% |
| DDR | 41 | 14437.2 | 14458.7 | +0.15% |
| DDR | 55 | 14452.4 | 14468.9 | +0.11% |
| DDR | 81 | 15481.4 | 15490.5 | +0.06% |
| HBM | 39 | 14220.8 | 14329.3 | +0.76% |
| HBM | 41 | 14498.0 | 14483.9 | -0.10% |
| HBM | 55 | 14503.7 | 14508.9 | +0.04% |
| HBM | 81 | 15507.7 | 15477.8 | -0.19% |

All paired outliers retained; observed ranges are not confidence intervals.
DDR KH39 u4: paired median +0.30%, range -1.74..+0.90%, positive 4/6
DDR KH41 u4: paired median +0.17%, range -0.06..+0.40%, positive 5/6
DDR KH55 u4: paired median +0.15%, range -0.08..+0.57%, positive 5/6
DDR KH81 u4: paired median +0.07%, range -0.49..+0.58%, positive 4/6
HBM KH39 u4: paired median +0.69%, range -1.45..+1.05%, positive 5/6
HBM KH41 u4: paired median -0.17%, range -3.41..+0.43%, positive 2/6
HBM KH55 u4: paired median +0.08%, range -0.19..+0.15%, positive 4/6
HBM KH81 u4: paired median -0.19%, range -0.56..+0.46%, positive 2/6
