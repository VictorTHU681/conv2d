3,058 state/guard cases and 720 timed hashes PASS.
Six permutations, five timings/process. Median process-average GFLOPS, screening only. Baseline is the GPR-loop candidate 490cd8d9 derived from upstream 138dcac, NOT upstream itself. Candidates fold cursor updates into post-index or pre-index loads. Ratios are direct within this job; no historical gains added.

| Memory | KH | Baseline | Post-index | Pre-index | Post-index/base | Pre-index/base |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | 14197.5 | 14159.2 | 14166.2 | -0.27% | -0.22% |
| DDR | 41 | 14407.5 | 14406.5 | 14407.6 | -0.01% | +0.00% |
| DDR | 55 | 14486.3 | 14484.9 | 14480.0 | -0.01% | -0.04% |
| DDR | 81 | 15500.9 | 15463.5 | 15478.4 | -0.24% | -0.15% |
| HBM | 39 | 14241.2 | 14262.1 | 14253.1 | +0.15% | +0.08% |
| HBM | 41 | 14448.3 | 14454.9 | 14452.1 | +0.05% | +0.03% |
| HBM | 55 | 14525.0 | 14522.8 | 14522.7 | -0.02% | -0.02% |
| HBM | 81 | 15483.2 | 15465.2 | 15495.6 | -0.12% | +0.08% |

Observed paired ranges retain all outliers and are not confidence intervals.
DDR KH39 post: paired median -0.12%, range -0.41..+0.20%, positive 2/6
DDR KH39 pre: paired median -0.23%, range -0.33..+0.07%, positive 1/6
DDR KH41 post: paired median +0.06%, range -0.25..+0.21%, positive 3/6
DDR KH41 pre: paired median -0.03%, range -0.15..+0.28%, positive 3/6
DDR KH55 post: paired median +0.02%, range -0.13..+0.08%, positive 4/6
DDR KH55 pre: paired median -0.04%, range -0.10..+0.10%, positive 1/6
DDR KH81 post: paired median -0.28%, range -0.52..+0.10%, positive 1/6
DDR KH81 pre: paired median -0.27%, range -0.92..+0.08%, positive 2/6
HBM KH39 post: paired median +0.19%, range -0.09..+0.78%, positive 5/6
HBM KH39 pre: paired median +0.13%, range -0.29..+0.68%, positive 4/6
HBM KH41 post: paired median +0.04%, range -0.03..+0.22%, positive 4/6
HBM KH41 pre: paired median +0.03%, range -0.23..+0.16%, positive 3/6
HBM KH55 post: paired median -0.07%, range -0.25..+0.37%, positive 2/6
HBM KH55 pre: paired median -0.01%, range -0.12..+0.39%, positive 2/6
HBM KH81 post: paired median -0.07%, range -0.42..+0.01%, positive 1/6
HBM KH81 pre: paired median +0.08%, range -0.28..+0.21%, positive 5/6
