1953 state/input-output guard cases PASS, including 200 F3 suffix boundary cases.
All five downloaded binaries match their pre-execution SHA-256 records.
96 original full-reference checks PASS; maximum errors zero.
Independent fixed sources, no runtime layout knob. Six alternating orders, five timings/process; median process-average GFLOPS. Baseline is current upstream b6ea996/138dcac source 08400a76. These ratios compare PAIRF3 compute suffix unrolls directly to that baseline; no gains are added from earlier experiments.

| Memory | KH | Upstream | U4 | U4/upstream |
| --- | ---: | ---: | ---: | ---: |
| DDR | 39 | 14129.3 | 14128.9 | -0.00% |
| DDR | 41 | 14407.6 | 14447.2 | +0.27% |
| DDR | 55 | 14496.5 | 14548.2 | +0.36% |
| DDR | 81 | 15456.8 | 15471.9 | +0.10% |
| HBM | 39 | 14244.7 | 14244.0 | -0.00% |
| HBM | 41 | 14486.2 | 14513.4 | +0.19% |
| HBM | 55 | 14537.6 | 14580.9 | +0.30% |
| HBM | 81 | 15464.1 | 15462.2 | -0.01% |

All paired outliers retained; observed ranges are not confidence intervals.
DDR KH39 u4: paired median -0.09%, range -0.39..+0.24%, positive 3/6
DDR KH41 u4: paired median +0.14%, range -2.98..+0.49%, positive 3/6
DDR KH55 u4: paired median +0.38%, range +0.32..+0.65%, positive 6/6
DDR KH81 u4: paired median +0.08%, range -0.09..+0.39%, positive 4/6
HBM KH39 u4: paired median -0.00%, range -0.81..+0.28%, positive 2/6
HBM KH41 u4: paired median +0.17%, range -0.07..+0.47%, positive 5/6
HBM KH55 u4: paired median +0.31%, range +0.27..+0.35%, positive 6/6
HBM KH81 u4: paired median -0.02%, range -0.29..+0.10%, positive 3/6
