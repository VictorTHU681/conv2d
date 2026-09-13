3,058 state/guard cases, 108 output-ownership cases and 720 timed hashes PASS; zero observed active conflicts.
Six permutations, five timings/process. Median process-average GFLOPS, screening only. Baseline is published v61 b3140af / 2c406547.

| Memory | KH | Baseline | Clear before store | Defer clears | Clearfirst/base | Deferclear/base |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | 14133.0 | 14158.0 | 14098.0 | +0.18% | -0.25% |
| DDR | 41 | 14209.6 | 14180.0 | 14171.2 | -0.21% | -0.27% |
| DDR | 55 | 14513.5 | 14521.2 | 14511.8 | +0.05% | -0.01% |
| DDR | 81 | 15503.0 | 15490.8 | 15487.8 | -0.08% | -0.10% |
| HBM | 39 | 14246.5 | 14273.7 | 14248.2 | +0.19% | +0.01% |
| HBM | 41 | 14286.0 | 14261.6 | 14266.2 | -0.17% | -0.14% |
| HBM | 55 | 14555.0 | 14559.0 | 14559.4 | +0.03% | +0.03% |
| HBM | 81 | 15486.1 | 15485.3 | 15465.6 | -0.01% | -0.13% |

Observed paired ranges retain all outliers and are not confidence intervals.
DDR KH39 clearfirst: paired median +0.17%, range -2.87..+0.61%, positive 4/6
DDR KH39 deferclear: paired median -0.18%, range -0.83..+0.59%, positive 1/6
DDR KH41 clearfirst: paired median -0.18%, range -0.36..+1.64%, positive 1/6
DDR KH41 deferclear: paired median -0.31%, range -10.82..+1.62%, positive 1/6
DDR KH55 clearfirst: paired median +0.06%, range -0.03..+1.28%, positive 4/6
DDR KH55 deferclear: paired median +0.00%, range -0.08..+1.05%, positive 3/6
DDR KH81 clearfirst: paired median -0.04%, range -0.40..+0.08%, positive 3/6
DDR KH81 deferclear: paired median -0.18%, range -0.77..+0.21%, positive 2/6
HBM KH39 clearfirst: paired median +0.17%, range -0.23..+0.62%, positive 4/6
HBM KH39 deferclear: paired median -0.15%, range -2.42..+0.33%, positive 3/6
HBM KH41 clearfirst: paired median -0.09%, range -5.37..+0.08%, positive 2/6
HBM KH41 deferclear: paired median -0.04%, range -1.11..+0.17%, positive 1/6
HBM KH55 clearfirst: paired median +0.03%, range -0.04..+0.13%, positive 5/6
HBM KH55 deferclear: paired median +0.03%, range -0.08..+0.10%, positive 4/6
HBM KH81 clearfirst: paired median +0.07%, range -0.29..+1.16%, positive 4/6
HBM KH81 deferclear: paired median -0.14%, range -0.37..+1.39%, positive 1/6
