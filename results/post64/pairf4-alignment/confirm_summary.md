96 original full-reference checks PASS; maximum errors zero.
Independent fixed sources, no runtime layout knob. Six alternating orders, five timings/process; median process-average GFLOPS. Baseline is current upstream b6ea996/138dcac source 08400a76. These ratios compare short-loop alignment directly to that baseline; no gains are added from earlier experiments.

| Memory | KH | Upstream | Aligned | Aligned/upstream |
| --- | ---: | ---: | ---: | ---: |
| DDR | 39 | 14081.2 | 14160.4 | +0.56% |
| DDR | 41 | 14406.9 | 14425.1 | +0.13% |
| DDR | 55 | 14489.7 | 14491.2 | +0.01% |
| DDR | 81 | 15491.9 | 15495.3 | +0.02% |
| HBM | 39 | 14219.7 | 14206.7 | -0.09% |
| HBM | 41 | 14464.4 | 14447.7 | -0.12% |
| HBM | 55 | 14538.0 | 14530.1 | -0.05% |
| HBM | 81 | 15460.2 | 15482.8 | +0.15% |

All paired outliers retained; observed ranges are not confidence intervals.
DDR KH39 aligned: paired median +0.55%, range -0.46..+0.77%, positive 5/6
DDR KH41 aligned: paired median +0.15%, range -0.05..+0.21%, positive 5/6
DDR KH55 aligned: paired median +0.06%, range -0.13..+0.10%, positive 4/6
DDR KH81 aligned: paired median +0.02%, range -0.42..+0.31%, positive 3/6
HBM KH39 aligned: paired median -0.09%, range -2.66..+0.94%, positive 2/6
HBM KH41 aligned: paired median -0.08%, range -0.30..+5.97%, positive 2/6
HBM KH55 aligned: paired median -0.04%, range -0.06..+0.00%, positive 1/6
HBM KH81 aligned: paired median +0.09%, range +0.03..+0.45%, positive 6/6
