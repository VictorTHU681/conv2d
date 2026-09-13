3,058 state/guard cases and 720 timed hashes PASS.
Six permutations, five timings/process. Median process-average GFLOPS, screening only. Current upstream 138dcac/08400a76; K4 tail predicated load/scatter versus bit-branch unrolling; baseline source unchanged. Ratios are direct comparisons within this job; no historical gains added.

| Memory | KH | Baseline | Scatter | Bits | Scatter/base | Bits/base |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | 14164.0 | 14144.7 | 14166.8 | -0.14% | +0.02% |
| DDR | 41 | 14381.9 | 14385.5 | 14411.6 | +0.03% | +0.21% |
| DDR | 55 | 14481.8 | 14472.5 | 14551.9 | -0.06% | +0.48% |
| DDR | 81 | 15499.8 | 15481.0 | 15480.0 | -0.12% | -0.13% |
| HBM | 39 | 14265.8 | 14242.8 | 14294.5 | -0.16% | +0.20% |
| HBM | 41 | 14446.1 | 14455.2 | 14475.4 | +0.06% | +0.20% |
| HBM | 55 | 14510.9 | 14515.0 | 14578.8 | +0.03% | +0.47% |
| HBM | 81 | 15476.6 | 15462.8 | 15472.3 | -0.09% | -0.03% |

Observed paired ranges retain all outliers and are not confidence intervals.
DDR KH39 scatter: paired median -0.23%, range -0.53..+0.19%, positive 2/6
DDR KH39 bits: paired median -0.01%, range -0.34..+0.19%, positive 1/6
DDR KH41 scatter: paired median -0.05%, range -0.24..+0.17%, positive 2/6
DDR KH41 bits: paired median +0.20%, range +0.01..+0.30%, positive 6/6
DDR KH55 scatter: paired median -0.11%, range -0.18..+0.04%, positive 1/6
DDR KH55 bits: paired median +0.49%, range +0.17..+0.55%, positive 6/6
DDR KH81 scatter: paired median -0.12%, range -0.57..+0.18%, positive 2/6
DDR KH81 bits: paired median -0.04%, range -0.52..+0.08%, positive 3/6
HBM KH39 scatter: paired median -0.21%, range -0.34..+0.02%, positive 2/6
HBM KH39 bits: paired median +0.20%, range -0.28..+0.47%, positive 5/6
HBM KH41 scatter: paired median +0.06%, range -0.13..+0.24%, positive 4/6
HBM KH41 bits: paired median +0.18%, range +0.00..+0.53%, positive 6/6
HBM KH55 scatter: paired median +0.01%, range -0.07..+0.12%, positive 4/6
HBM KH55 bits: paired median +0.48%, range -0.30..+0.62%, positive 5/6
HBM KH81 scatter: paired median -0.07%, range -0.29..+0.30%, positive 2/6
HBM KH81 bits: paired median +0.00%, range -0.30..+0.36%, positive 3/6
