906 state/boundary cases and 720 timed hashes PASS.
Six permutations, five timings/process. Median process-average GFLOPS, screening only. Current upstream b6ea996/08400a76; short loop aligned by hoisted NOP padding, with and without U4. Ratios are direct within this job; no historical gains added.

| Memory | KH | Baseline | Aligned | Aligned U4 | Aligned/base | Aligned U4/base |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | 14138.9 | 14217.5 | 14020.8 | +0.56% | -0.84% |
| DDR | 41 | 14399.2 | 14459.9 | 14428.5 | +0.42% | +0.20% |
| DDR | 55 | 14478.6 | 14476.5 | 14487.0 | -0.01% | +0.06% |
| DDR | 81 | 15478.2 | 15494.7 | 15486.5 | +0.11% | +0.05% |
| HBM | 39 | 14254.7 | 14288.4 | 14278.5 | +0.24% | +0.17% |
| HBM | 41 | 14465.8 | 14485.6 | 14495.2 | +0.14% | +0.20% |
| HBM | 55 | 14512.9 | 14514.8 | 14522.5 | +0.01% | +0.07% |
| HBM | 81 | 15493.2 | 15498.9 | 15497.5 | +0.04% | +0.03% |

Observed paired ranges retain all outliers and are not confidence intervals.
DDR KH39 aligned: paired median +0.52%, range -0.09..+0.78%, positive 5/6
DDR KH39 aligned_u4: paired median -0.87%, range -1.69..-0.45%, positive 0/6
DDR KH41 aligned: paired median +0.39%, range +0.22..+0.56%, positive 6/6
DDR KH41 aligned_u4: paired median +0.21%, range +0.02..+0.30%, positive 6/6
DDR KH55 aligned: paired median +0.05%, range -0.79..+0.08%, positive 4/6
DDR KH55 aligned_u4: paired median +0.08%, range -0.12..+0.15%, positive 5/6
DDR KH81 aligned: paired median +0.14%, range -0.16..+2.81%, positive 5/6
DDR KH81 aligned_u4: paired median +0.01%, range -0.13..+3.09%, positive 3/6
HBM KH39 aligned: paired median +0.18%, range +0.05..+0.60%, positive 6/6
HBM KH39 aligned_u4: paired median +0.13%, range +0.02..+0.40%, positive 6/6
HBM KH41 aligned: paired median +0.10%, range +0.00..+0.43%, positive 6/6
HBM KH41 aligned_u4: paired median +0.15%, range +0.01..+0.40%, positive 6/6
HBM KH55 aligned: paired median +0.04%, range -0.04..+0.06%, positive 4/6
HBM KH55 aligned_u4: paired median +0.08%, range +0.03..+0.14%, positive 6/6
HBM KH81 aligned: paired median +0.06%, range -0.21..+0.50%, positive 4/6
HBM KH81 aligned_u4: paired median +0.08%, range -0.45..+0.16%, positive 4/6
