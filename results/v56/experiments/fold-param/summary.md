3,058 state/guard cases, 108 output-ownership cases and 720 timed hashes PASS; zero observed active conflicts.
Six permutations, five timings/process. Median process-average GFLOPS, screening only. Baseline is accepted 3df5c69 / ebf36923, not published v55.

| Memory | KH | Baseline | F4 phase register | F3+F4 phase register | F4/base | F3+F4/base |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | 14152.9 | 14130.1 | 14142.2 | -0.16% | -0.08% |
| DDR | 41 | 14144.5 | 14116.2 | 14110.6 | -0.20% | -0.24% |
| DDR | 55 | 14526.1 | 14518.7 | 14520.6 | -0.05% | -0.04% |
| DDR | 81 | 15459.9 | 15495.3 | 15451.0 | +0.23% | -0.06% |
| HBM | 39 | 14228.5 | 14207.0 | 14220.5 | -0.15% | -0.06% |
| HBM | 41 | 14187.6 | 14190.3 | 14196.9 | +0.02% | +0.07% |
| HBM | 55 | 14554.0 | 14556.7 | 14555.5 | +0.02% | +0.01% |
| HBM | 81 | 15481.0 | 15454.7 | 15464.2 | -0.17% | -0.11% |

Observed paired ranges retain all outliers and are not confidence intervals.
DDR KH39 cf4: paired median -0.09%, range -0.58..+0.72%, positive 2/6
DDR KH39 cf34: paired median +0.18%, range -1.27..+0.67%, positive 3/6
DDR KH41 cf4: paired median -0.18%, range -0.52..+0.20%, positive 3/6
DDR KH41 cf34: paired median -0.22%, range -1.57..+0.35%, positive 2/6
DDR KH55 cf4: paired median -0.04%, range -0.62..+0.06%, positive 2/6
DDR KH55 cf34: paired median -0.02%, range -0.13..+0.04%, positive 3/6
DDR KH81 cf4: paired median +0.28%, range +0.07..+0.63%, positive 6/6
DDR KH81 cf34: paired median +0.12%, range -0.36..+0.46%, positive 5/6
HBM KH39 cf4: paired median -0.15%, range -0.29..+0.27%, positive 2/6
HBM KH39 cf34: paired median -0.01%, range -0.35..+0.52%, positive 2/6
HBM KH41 cf4: paired median -0.04%, range -1.10..+0.26%, positive 3/6
HBM KH41 cf34: paired median -0.09%, range -0.50..+0.34%, positive 2/6
HBM KH55 cf4: paired median +0.00%, range -0.08..+0.09%, positive 3/6
HBM KH55 cf34: paired median +0.05%, range -0.04..+0.08%, positive 4/6
HBM KH81 cf4: paired median -0.21%, range -0.70..+0.40%, positive 2/6
HBM KH81 cf34: paired median -0.06%, range -0.34..+0.53%, positive 1/6
