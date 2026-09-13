3,442 state/guard/boundary cases and 720 timed hashes PASS.
Six permutations, five timings/process. Median process-average GFLOPS, screening only. Freshly pulled baseline b6ea996/08400a76, combined U4 and earlier fixed-v64 U4 (legacy). Ratios are direct within this job; no historical gains added.

| Memory | KH | Baseline | Combined U4 | Legacy U4 | Combined/base | Legacy/base |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | 14228.0 | 14213.2 | 14209.6 | -0.10% | -0.13% |
| DDR | 41 | 14474.5 | 14499.9 | 14525.5 | +0.17% | +0.35% |
| DDR | 55 | 14520.9 | 14496.3 | 14531.1 | -0.17% | +0.07% |
| DDR | 81 | 15494.5 | 15489.1 | 15499.2 | -0.03% | +0.03% |
| HBM | 39 | 14298.8 | 14345.2 | 14379.8 | +0.32% | +0.57% |
| HBM | 41 | 14527.2 | 14531.9 | 14547.6 | +0.03% | +0.14% |
| HBM | 55 | 14559.3 | 14539.8 | 14569.7 | -0.13% | +0.07% |
| HBM | 81 | 15497.9 | 15477.2 | 15484.7 | -0.13% | -0.08% |

Observed paired ranges retain all outliers and are not confidence intervals.
DDR KH39 u4: paired median -0.01%, range -2.60..+0.38%, positive 3/6
DDR KH39 legacy: paired median -0.05%, range -0.26..+0.30%, positive 3/6
DDR KH41 u4: paired median +0.13%, range -0.30..+0.54%, positive 5/6
DDR KH41 legacy: paired median +0.31%, range +0.16..+0.46%, positive 6/6
DDR KH55 u4: paired median -0.17%, range -0.26..-0.04%, positive 0/6
DDR KH55 legacy: paired median +0.06%, range +0.04..+0.08%, positive 6/6
DDR KH81 u4: paired median -0.03%, range -0.56..+0.34%, positive 1/6
DDR KH81 legacy: paired median -0.10%, range -0.29..+0.54%, positive 2/6
HBM KH39 u4: paired median +0.31%, range +0.09..+0.42%, positive 6/6
HBM KH39 legacy: paired median +0.54%, range -2.51..+0.82%, positive 5/6
HBM KH41 u4: paired median +0.05%, range -0.14..+0.26%, positive 4/6
HBM KH41 legacy: paired median +0.15%, range +0.08..+0.32%, positive 6/6
HBM KH55 u4: paired median -0.16%, range -0.25..-0.06%, positive 0/6
HBM KH55 legacy: paired median +0.03%, range -0.02..+0.12%, positive 4/6
HBM KH81 u4: paired median -0.09%, range -0.56..+0.20%, positive 1/6
HBM KH81 legacy: paired median -0.01%, range -0.68..+0.54%, positive 3/6
