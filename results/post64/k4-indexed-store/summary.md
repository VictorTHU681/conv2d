3,058 state/guard cases and 720 timed hashes PASS.
Six permutations, five timings/process. Median process-average GFLOPS, screening only. Current upstream 138dcac/08400a76; K4 indexed stores in interleaved full copies only or all three vector-copy sites. Ratios are direct within this job; no historical gains added.

| Memory | KH | Baseline | Full-copy | All-copy | Full-copy/base | All-copy/base |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | 14165.5 | 14153.6 | 14225.4 | -0.08% | +0.42% |
| DDR | 41 | 14425.7 | 14433.6 | 14468.9 | +0.06% | +0.30% |
| DDR | 55 | 14494.0 | 14497.2 | 14515.4 | +0.02% | +0.15% |
| DDR | 81 | 15492.1 | 15481.4 | 15534.0 | -0.07% | +0.27% |
| HBM | 39 | 14254.8 | 14287.7 | 14314.0 | +0.23% | +0.42% |
| HBM | 41 | 14487.5 | 14485.5 | 14475.2 | -0.01% | -0.08% |
| HBM | 55 | 14537.6 | 14533.5 | 14555.7 | -0.03% | +0.12% |
| HBM | 81 | 15487.6 | 15480.5 | 15509.8 | -0.05% | +0.14% |

Observed paired ranges retain all outliers and are not confidence intervals.
DDR KH39 full: paired median +0.04%, range -0.35..+6.51%, positive 3/6
DDR KH39 all: paired median +0.40%, range +0.23..+8.05%, positive 6/6
DDR KH41 full: paired median +0.06%, range -0.08..+0.18%, positive 4/6
DDR KH41 all: paired median +0.33%, range +0.11..+0.45%, positive 6/6
DDR KH55 full: paired median +0.02%, range -0.03..+0.09%, positive 3/6
DDR KH55 all: paired median +0.13%, range +0.06..+0.17%, positive 6/6
DDR KH81 full: paired median -0.08%, range -0.13..+0.07%, positive 1/6
DDR KH81 all: paired median +0.18%, range -0.23..+0.52%, positive 5/6
HBM KH39 full: paired median +0.14%, range -0.02..+0.40%, positive 5/6
HBM KH39 all: paired median +0.34%, range +0.24..+0.69%, positive 6/6
HBM KH41 full: paired median -0.02%, range -0.11..+0.06%, positive 2/6
HBM KH41 all: paired median -0.11%, range -10.20..+0.53%, positive 3/6
HBM KH55 full: paired median -0.06%, range -0.71..+0.04%, positive 2/6
HBM KH55 all: paired median +0.14%, range +0.05..+0.23%, positive 6/6
HBM KH81 full: paired median -0.15%, range -0.39..+0.24%, positive 1/6
HBM KH81 all: paired median +0.01%, range -0.34..+0.34%, positive 3/6
