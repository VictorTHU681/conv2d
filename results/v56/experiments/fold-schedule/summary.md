3,058 state/guard cases, 108 output-ownership cases and 720 timed hashes PASS; zero observed active conflicts.
Six permutations, five timings/process. Median process-average GFLOPS, screening only. Baseline is accepted 3df5c69 / ebf36923, not published v55.

| Memory | KH | Baseline | F4 weave | F3+F4 weave | F4/base | F3+F4/base |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | 14177.8 | 14209.4 | 14193.0 | +0.22% | +0.11% |
| DDR | 41 | 14179.8 | 14203.1 | 14196.2 | +0.16% | +0.12% |
| DDR | 55 | 14548.5 | 14564.1 | 14552.9 | +0.11% | +0.03% |
| DDR | 81 | 15500.3 | 15518.8 | 15523.6 | +0.12% | +0.15% |
| HBM | 39 | 14269.5 | 14303.8 | 14278.2 | +0.24% | +0.06% |
| HBM | 41 | 14262.2 | 14293.2 | 14268.5 | +0.22% | +0.04% |
| HBM | 55 | 14585.2 | 14596.6 | 14591.3 | +0.08% | +0.04% |
| HBM | 81 | 15499.5 | 15460.0 | 15519.2 | -0.25% | +0.13% |

Observed paired ranges retain all outliers and are not confidence intervals.
DDR KH39 f4: paired median +0.24%, range -0.03..+1.46%, positive 5/6
DDR KH39 f34: paired median +0.15%, range -0.48..+1.60%, positive 5/6
DDR KH41 f4: paired median +0.15%, range -0.84..+0.63%, positive 3/6
DDR KH41 f34: paired median +0.12%, range -0.45..+0.67%, positive 4/6
DDR KH55 f4: paired median +0.10%, range +0.04..+0.78%, positive 6/6
DDR KH55 f34: paired median +0.06%, range -0.14..+0.69%, positive 4/6
DDR KH81 f4: paired median +0.08%, range -0.18..+0.31%, positive 4/6
DDR KH81 f34: paired median +0.11%, range -1.89..+0.42%, positive 4/6
HBM KH39 f4: paired median +0.13%, range -0.45..+0.59%, positive 5/6
HBM KH39 f34: paired median +0.04%, range -7.06..+0.31%, positive 3/6
HBM KH41 f4: paired median +0.26%, range +0.16..+0.64%, positive 6/6
HBM KH41 f34: paired median +0.17%, range -0.13..+0.52%, positive 4/6
HBM KH55 f4: paired median +0.10%, range +0.04..+0.14%, positive 6/6
HBM KH55 f34: paired median +0.04%, range -0.02..+0.17%, positive 5/6
HBM KH81 f4: paired median -0.22%, range -0.84..+0.12%, positive 2/6
HBM KH81 f34: paired median +0.02%, range -0.43..+0.60%, positive 3/6
