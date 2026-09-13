3,442 state/guard/boundary cases and 720 timed hashes PASS.
Six permutations, five timings/process. Median process-average GFLOPS, screening only. Fixed published v64 baseline 3f8c8c2/0136da05, short compute loops unrolled by two (u2) or four (u4). Ratios are direct within this job; no historical gains added.

| Memory | KH | Baseline | U2 | U4 | U2/base | U4/base |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | 14193.5 | 14215.9 | 14230.8 | +0.16% | +0.26% |
| DDR | 41 | 14490.8 | 14493.4 | 14505.8 | +0.02% | +0.10% |
| DDR | 55 | 14514.0 | 14522.5 | 14521.4 | +0.06% | +0.05% |
| DDR | 81 | 15531.8 | 15521.2 | 15499.9 | -0.07% | -0.21% |
| HBM | 39 | 14300.8 | 14342.4 | 14376.9 | +0.29% | +0.53% |
| HBM | 41 | 14541.5 | 14529.7 | 14541.1 | -0.08% | -0.00% |
| HBM | 55 | 14554.6 | 14551.1 | 14559.5 | -0.02% | +0.03% |
| HBM | 81 | 15476.0 | 15515.5 | 15496.5 | +0.26% | +0.13% |

Observed paired ranges retain all outliers and are not confidence intervals.
DDR KH39 u2: paired median +0.14%, range -8.31..+0.55%, positive 4/6
DDR KH39 u4: paired median +0.33%, range +0.08..+0.66%, positive 6/6
DDR KH41 u2: paired median +0.03%, range -0.14..+0.17%, positive 4/6
DDR KH41 u4: paired median +0.11%, range -0.06..+0.21%, positive 5/6
DDR KH55 u2: paired median +0.08%, range -0.09..+0.66%, positive 4/6
DDR KH55 u4: paired median +0.05%, range -2.35..+0.76%, positive 4/6
DDR KH81 u2: paired median +0.10%, range -0.29..+0.48%, positive 4/6
DDR KH81 u4: paired median -0.22%, range -0.58..+0.46%, positive 2/6
HBM KH39 u2: paired median +0.29%, range +0.04..+0.93%, positive 6/6
HBM KH39 u4: paired median +0.51%, range -0.03..+1.14%, positive 5/6
HBM KH41 u2: paired median -0.12%, range -0.28..+0.02%, positive 1/6
HBM KH41 u4: paired median -0.03%, range -7.26..+0.22%, positive 2/6
HBM KH55 u2: paired median -0.03%, range -0.28..+0.23%, positive 2/6
HBM KH55 u4: paired median +0.05%, range -0.04..+0.28%, positive 5/6
HBM KH81 u2: paired median +0.26%, range +0.04..+0.45%, positive 6/6
HBM KH81 u4: paired median +0.11%, range -0.02..+0.44%, positive 5/6
