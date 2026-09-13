96 original full-reference checks PASS; maximum errors zero.
Independent fixed sources, no runtime layout knob. Six alternating orders, five timings/process; median process-average GFLOPS. Baseline is current upstream b6ea996/138dcac source 08400a76. These ratios compare K4 indexed stores at all three copy sites directly to that baseline; no gains are added from earlier experiments.

| Memory | KH | Upstream | Indexed all | Indexed all/upstream |
| --- | ---: | ---: | ---: | ---: |
| DDR | 39 | 14138.8 | 14139.9 | +0.01% |
| DDR | 41 | 14417.4 | 14418.0 | +0.00% |
| DDR | 55 | 14499.1 | 14485.5 | -0.09% |
| DDR | 81 | 15484.5 | 15467.2 | -0.11% |
| HBM | 39 | 14242.5 | 14231.6 | -0.08% |
| HBM | 41 | 14479.2 | 14497.2 | +0.12% |
| HBM | 55 | 14534.3 | 14529.1 | -0.04% |
| HBM | 81 | 15467.7 | 15469.2 | +0.01% |

All paired outliers retained; observed ranges are not confidence intervals.
DDR KH39 all: paired median +0.15%, range -0.60..+0.19%, positive 4/6
DDR KH41 all: paired median +0.02%, range -0.21..+3.08%, positive 3/6
DDR KH55 all: paired median -0.09%, range -0.20..-0.01%, positive 0/6
DDR KH81 all: paired median -0.07%, range -1.55..+0.01%, positive 1/6
HBM KH39 all: paired median -0.05%, range -3.18..+0.10%, positive 3/6
HBM KH41 all: paired median +0.04%, range -3.78..+0.31%, positive 4/6
HBM KH55 all: paired median -0.02%, range -0.13..+0.07%, positive 2/6
HBM KH81 all: paired median +0.04%, range -0.48..+0.35%, positive 4/6
