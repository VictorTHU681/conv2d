3,442 state/guard/boundary cases and 720 timed hashes PASS.
Six permutations, five timings/process. Median process-average GFLOPS, screening only. Fixed current upstream b6ea996/08400a76; outlined PAIRF4 alone and outlined PAIRF4 plus U4. Ratios are direct within this job; no historical gains added.

| Memory | KH | Baseline | Outlined | Outlined U4 | Outlined/base | Outlined U4/base |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | 14174.5 | 14098.4 | 14166.5 | -0.54% | -0.06% |
| DDR | 41 | 14391.2 | 14418.2 | 14479.3 | +0.19% | +0.61% |
| DDR | 55 | 14481.7 | 14455.0 | 14461.3 | -0.18% | -0.14% |
| DDR | 81 | 15469.0 | 15490.1 | 15387.8 | +0.14% | -0.53% |
| HBM | 39 | 14231.0 | 14255.0 | 14364.8 | +0.17% | +0.94% |
| HBM | 41 | 14499.5 | 14477.6 | 14531.7 | -0.15% | +0.22% |
| HBM | 55 | 14520.6 | 14500.7 | 14496.4 | -0.14% | -0.17% |
| HBM | 81 | 15490.0 | 15496.2 | 15368.0 | +0.04% | -0.79% |

Observed paired ranges retain all outliers and are not confidence intervals.
DDR KH39 outlined: paired median -0.59%, range -2.09..-0.13%, positive 0/6
DDR KH39 outlined_u4: paired median -0.11%, range -0.84..+0.40%, positive 2/6
DDR KH41 outlined: paired median +0.15%, range -0.08..+10.06%, positive 4/6
DDR KH41 outlined_u4: paired median +0.65%, range +0.23..+10.30%, positive 6/6
DDR KH55 outlined: paired median -0.19%, range -0.26..-0.10%, positive 0/6
DDR KH55 outlined_u4: paired median -0.13%, range -0.24..-0.09%, positive 0/6
DDR KH81 outlined: paired median +0.15%, range -0.05..+0.29%, positive 5/6
DDR KH81 outlined_u4: paired median -0.57%, range -0.82..-0.31%, positive 0/6
HBM KH39 outlined: paired median +0.22%, range -0.01..+0.59%, positive 5/6
HBM KH39 outlined_u4: paired median +0.96%, range -6.40..+1.02%, positive 5/6
HBM KH41 outlined: paired median -0.16%, range -0.41..+0.80%, positive 2/6
HBM KH41 outlined_u4: paired median +0.20%, range +0.08..+1.17%, positive 6/6
HBM KH55 outlined: paired median -0.19%, range -0.24..-0.07%, positive 0/6
HBM KH55 outlined_u4: paired median -0.14%, range -0.25..-0.04%, positive 0/6
HBM KH81 outlined: paired median +0.05%, range -0.32..+0.51%, positive 4/6
HBM KH81 outlined_u4: paired median -0.71%, range -1.10..-0.60%, positive 0/6
