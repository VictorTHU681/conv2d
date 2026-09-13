96 original full-reference checks PASS; maximum errors zero.
Independent fixed sources, no runtime layout knob. Six alternating orders, five timings/process; median process-average GFLOPS. Baseline is current upstream b6ea996/138dcac source 08400a76. These ratios compare K4 paired extraction/clear events directly to that baseline; no gains are added from earlier experiments.

| Memory | KH | Upstream | Paired | Paired/upstream |
| --- | ---: | ---: | ---: | ---: |
| DDR | 39 | 14123.1 | 14143.3 | +0.14% |
| DDR | 41 | 14433.8 | 14425.9 | -0.05% |
| DDR | 55 | 14498.4 | 14495.5 | -0.02% |
| DDR | 81 | 15513.0 | 15484.0 | -0.19% |
| HBM | 39 | 14202.6 | 14235.4 | +0.23% |
| HBM | 41 | 14480.6 | 14467.5 | -0.09% |
| HBM | 55 | 14534.6 | 14541.7 | +0.05% |
| HBM | 81 | 15456.1 | 15466.9 | +0.07% |

All paired outliers retained; observed ranges are not confidence intervals.
DDR KH39 paired: paired median -0.05%, range -0.40..+0.29%, positive 3/6
DDR KH41 paired: paired median +0.06%, range -0.29..+0.17%, positive 4/6
DDR KH55 paired: paired median -0.04%, range -0.05..+0.02%, positive 2/6
DDR KH81 paired: paired median -0.18%, range -0.34..+0.24%, positive 2/6
HBM KH39 paired: paired median +0.29%, range -0.10..+0.48%, positive 5/6
HBM KH41 paired: paired median -0.12%, range -0.20..+0.29%, positive 2/6
HBM KH55 paired: paired median +0.06%, range -0.08..+0.11%, positive 4/6
HBM KH81 paired: paired median +0.01%, range -0.35..+0.60%, positive 4/6
