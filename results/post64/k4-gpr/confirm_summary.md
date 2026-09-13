96 original full-reference checks PASS; maximum errors zero.
Independent fixed sources, no runtime layout knob. Six alternating orders, five timings/process; median process-average GFLOPS. Baseline is current upstream b6ea996/138dcac source 08400a76. These ratios compare K4 integer scalar loop directly to that baseline; no gains are added from earlier experiments.

| Memory | KH | Upstream | GPR loop | GPR loop/upstream |
| --- | ---: | ---: | ---: | ---: |
| DDR | 39 | 14141.1 | 14132.6 | -0.06% |
| DDR | 41 | 14415.4 | 14425.4 | +0.07% |
| DDR | 55 | 14503.1 | 14497.1 | -0.04% |
| DDR | 81 | 15491.7 | 15472.2 | -0.13% |
| HBM | 39 | 14237.2 | 14234.4 | -0.02% |
| HBM | 41 | 14474.5 | 14473.8 | -0.01% |
| HBM | 55 | 14529.1 | 14536.8 | +0.05% |
| HBM | 81 | 15475.7 | 15467.0 | -0.06% |

All paired outliers retained; observed ranges are not confidence intervals.
DDR KH39 gpr_loop: paired median +0.02%, range -0.47..+0.67%, positive 3/6
DDR KH41 gpr_loop: paired median +0.09%, range -0.18..+9.76%, positive 4/6
DDR KH55 gpr_loop: paired median -0.05%, range -0.82..+0.07%, positive 2/6
DDR KH81 gpr_loop: paired median -0.13%, range -0.31..-0.04%, positive 0/6
HBM KH39 gpr_loop: paired median -0.08%, range -0.22..+0.11%, positive 1/6
HBM KH41 gpr_loop: paired median +0.04%, range -0.20..+3.78%, positive 4/6
HBM KH55 gpr_loop: paired median +0.07%, range -0.03..+0.11%, positive 4/6
HBM KH81 gpr_loop: paired median -0.02%, range -0.36..+0.08%, positive 3/6
