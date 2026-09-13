Both downloaded binaries match their pre-execution SHA-256 records.
96 original full-reference checks PASS; maximum errors zero.
Fixed binaries from job 1592972, repeated on a separate node without recompiling; no runtime layout knob. Six alternating orders, five timings/process; median process-average GFLOPS. Baseline is current upstream b6ea996/138dcac source 08400a76. These ratios compare PAIRF3 compute suffix unrolls directly to that baseline; no gains are added from earlier experiments.

| Memory | KH | Upstream | U4 | U4/upstream |
| --- | ---: | ---: | ---: | ---: |
| DDR | 39 | 14168.1 | 14206.3 | +0.27% |
| DDR | 41 | 14442.0 | 14509.3 | +0.47% |
| DDR | 55 | 14502.1 | 14573.9 | +0.49% |
| DDR | 81 | 15484.1 | 15488.4 | +0.03% |
| HBM | 39 | 14254.5 | 14273.5 | +0.13% |
| HBM | 41 | 14514.4 | 14565.0 | +0.35% |
| HBM | 55 | 14548.7 | 14607.1 | +0.40% |
| HBM | 81 | 15504.0 | 15472.5 | -0.20% |

All paired outliers retained; observed ranges are not confidence intervals.
DDR KH39 u4: paired median +0.28%, range -0.26..+0.48%, positive 4/6
DDR KH41 u4: paired median +0.41%, range +0.29..+0.64%, positive 6/6
DDR KH55 u4: paired median +0.53%, range +0.43..+0.58%, positive 6/6
DDR KH81 u4: paired median +0.10%, range -0.31..+0.34%, positive 3/6
HBM KH39 u4: paired median +0.19%, range -0.18..+0.63%, positive 4/6
HBM KH41 u4: paired median +0.39%, range +0.04..+0.78%, positive 6/6
HBM KH55 u4: paired median +0.40%, range +0.30..+0.54%, positive 6/6
HBM KH81 u4: paired median -0.22%, range -0.71..+0.23%, positive 2/6
