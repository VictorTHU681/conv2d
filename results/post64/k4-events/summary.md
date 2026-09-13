3,058 state/guard cases and 720 timed hashes PASS.
Six permutations, five timings/process. Median process-average GFLOPS, screening only. Current upstream 138dcac/08400a76; K4 output extraction/zeroing/store scheduling: clears before store or paired read/clear. Ratios are direct within this job; no historical gains added.

| Memory | KH | Baseline | Clear-first | Paired | Clear-first/base | Paired/base |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | 14173.8 | 14199.5 | 14235.9 | +0.18% | +0.44% |
| DDR | 41 | 14417.2 | 14459.0 | 14488.6 | +0.29% | +0.49% |
| DDR | 55 | 14491.5 | 14505.5 | 14524.0 | +0.10% | +0.22% |
| DDR | 81 | 15477.2 | 15488.6 | 15505.2 | +0.07% | +0.18% |
| HBM | 39 | 14254.2 | 14282.8 | 14315.0 | +0.20% | +0.43% |
| HBM | 41 | 14483.0 | 14493.1 | 14521.7 | +0.07% | +0.27% |
| HBM | 55 | 14530.0 | 14537.2 | 14553.6 | +0.05% | +0.16% |
| HBM | 81 | 15501.3 | 15494.2 | 15483.4 | -0.05% | -0.12% |

Observed paired ranges retain all outliers and are not confidence intervals.
DDR KH39 clearfirst: paired median -0.06%, range -0.19..+0.30%, positive 3/6
DDR KH39 paired: paired median +0.32%, range -0.41..+0.89%, positive 4/6
DDR KH41 clearfirst: paired median +0.28%, range -0.29..+0.54%, positive 4/6
DDR KH41 paired: paired median +0.47%, range +0.27..+0.65%, positive 6/6
DDR KH55 clearfirst: paired median +0.13%, range -0.06..+0.16%, positive 5/6
DDR KH55 paired: paired median +0.25%, range +0.07..+0.29%, positive 6/6
DDR KH81 clearfirst: paired median +0.04%, range -0.21..+2.40%, positive 4/6
DDR KH81 paired: paired median +0.27%, range -0.12..+2.36%, positive 5/6
HBM KH39 clearfirst: paired median +0.30%, range -0.50..+0.76%, positive 4/6
HBM KH39 paired: paired median +0.43%, range -0.12..+0.92%, positive 5/6
HBM KH41 clearfirst: paired median +0.07%, range -0.04..+0.19%, positive 5/6
HBM KH41 paired: paired median +0.32%, range +0.17..+0.55%, positive 6/6
HBM KH55 clearfirst: paired median +0.03%, range -1.48..+0.77%, positive 5/6
HBM KH55 paired: paired median +0.12%, range -1.00..+0.90%, positive 4/6
HBM KH81 clearfirst: paired median -0.11%, range -0.75..+0.28%, positive 3/6
HBM KH81 paired: paired median -0.19%, range -0.37..+0.23%, positive 1/6
