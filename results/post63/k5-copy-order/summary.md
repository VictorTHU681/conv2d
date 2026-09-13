3,058 state/guard cases, 1,148 extended cases, 108 output-ownership cases and 720 timed hashes PASS; zero observed active conflicts.
Six permutations, five timings/process. Median process-average GFLOPS, screening only. Three fixed executables: accepted local scalar-unroll baseline ce57939/0136da05, earlier copy load (early), and distributed plane stores (spread). No runtime experiment knob. Ratios use this same-job local baseline; no gains are added from prior v63 comparisons.

| Memory | KH | Baseline | Early load | Spread stores | Early/base | Spread/base |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | 14206.5 | 14171.2 | 14128.6 | -0.25% | -0.55% |
| DDR | 41 | 14524.1 | 14446.5 | 14437.3 | -0.53% | -0.60% |
| DDR | 55 | 14532.2 | 14511.0 | 14525.6 | -0.15% | -0.05% |
| DDR | 81 | 15497.7 | 15487.2 | 15483.5 | -0.07% | -0.09% |
| HBM | 39 | 14343.1 | 14300.2 | 14314.4 | -0.30% | -0.20% |
| HBM | 41 | 14566.5 | 14490.0 | 14524.2 | -0.52% | -0.29% |
| HBM | 55 | 14573.0 | 14556.1 | 14559.2 | -0.12% | -0.09% |
| HBM | 81 | 15522.1 | 15478.5 | 15478.0 | -0.28% | -0.28% |

Observed paired ranges retain all outliers and are not confidence intervals.
DDR KH39 early: paired median -0.08%, range -0.79..+0.51%, positive 2/6
DDR KH39 spread: paired median -0.33%, range -7.98..+0.31%, positive 1/6
DDR KH41 early: paired median -0.61%, range -1.41..-0.22%, positive 0/6
DDR KH41 spread: paired median -0.54%, range -0.88..-0.42%, positive 0/6
DDR KH55 early: paired median -0.13%, range -0.25..+0.58%, positive 1/6
DDR KH55 spread: paired median -0.06%, range -0.93..+0.74%, positive 1/6
DDR KH81 early: paired median -0.12%, range -0.13..+0.46%, positive 2/6
DDR KH81 spread: paired median -0.06%, range -0.24..+0.03%, positive 1/6
HBM KH39 early: paired median -0.26%, range -0.56..-0.14%, positive 0/6
HBM KH39 spread: paired median -0.21%, range -0.43..+0.03%, positive 2/6
HBM KH41 early: paired median -0.56%, range -0.79..-0.51%, positive 0/6
HBM KH41 spread: paired median -0.35%, range -0.53..-0.22%, positive 0/6
HBM KH55 early: paired median -0.14%, range -0.21..-0.10%, positive 0/6
HBM KH55 spread: paired median -0.09%, range -0.66..-0.04%, positive 0/6
HBM KH81 early: paired median -0.36%, range -1.64..-0.20%, positive 0/6
HBM KH81 spread: paired median -0.20%, range -0.63..+0.24%, positive 1/6
