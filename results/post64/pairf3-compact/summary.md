1753 state/input-output guard cases, 182 actual coefficient-packer cases and 21294 row-final SME load probes PASS.
All five downloaded binaries match their pre-execution SHA-256 records.
96 original full-reference checks PASS; maximum errors zero.
Independent fixed sources, no runtime layout knob. Six alternating orders, five timings/process; median process-average GFLOPS. Baseline is current upstream b6ea996/138dcac source 08400a76. These ratios compare PAIRF3 compact coefficients directly to that baseline; no gains are added from earlier experiments.

| Memory | KH | Upstream | Compact | Compact/upstream |
| --- | ---: | ---: | ---: | ---: |
| DDR | 39 | 14159.4 | 14107.3 | -0.37% |
| DDR | 41 | 14443.7 | 14393.4 | -0.35% |
| DDR | 55 | 14493.9 | 14409.6 | -0.58% |
| DDR | 81 | 15483.3 | 15492.4 | +0.06% |
| HBM | 39 | 14230.2 | 14249.4 | +0.14% |
| HBM | 41 | 14489.2 | 14541.1 | +0.36% |
| HBM | 55 | 14539.7 | 14448.6 | -0.63% |
| HBM | 81 | 15461.9 | 15466.2 | +0.03% |

All paired outliers retained; observed ranges are not confidence intervals.
DDR KH39 compact: paired median -0.42%, range -0.63..+0.01%, positive 1/6
DDR KH41 compact: paired median -0.39%, range -3.88..+0.44%, positive 3/6
DDR KH55 compact: paired median -0.60%, range -0.63..-0.56%, positive 0/6
DDR KH81 compact: paired median -0.02%, range -0.54..+0.20%, positive 3/6
HBM KH39 compact: paired median +0.09%, range +0.04..+0.30%, positive 6/6
HBM KH41 compact: paired median +0.31%, range +0.10..+0.96%, positive 6/6
HBM KH55 compact: paired median -0.60%, range -0.88..-0.54%, positive 0/6
HBM KH81 compact: paired median +0.08%, range -0.26..+0.34%, positive 4/6
