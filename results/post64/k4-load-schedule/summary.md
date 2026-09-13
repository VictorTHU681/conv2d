3,058 state/guard cases and 720 timed hashes PASS.
Six permutations, five timings/process. Median process-average GFLOPS, screening only. Current upstream 138dcac/08400a76; K4_STEP coefficient-first or interleaved loads; same memory operands and ordered FMOPAs. Ratios are direct within this job; no historical gains added.

| Memory | KH | Baseline | B-first | Interleave | B-first/base | Interleave/base |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | 14205.2 | 14171.4 | 14075.6 | -0.24% | -0.91% |
| DDR | 41 | 14456.7 | 14434.0 | 14452.9 | -0.16% | -0.03% |
| DDR | 55 | 14510.8 | 14479.7 | 14476.3 | -0.21% | -0.24% |
| DDR | 81 | 15492.8 | 15503.6 | 15497.8 | +0.07% | +0.03% |
| HBM | 39 | 14285.9 | 14263.0 | 14290.3 | -0.16% | +0.03% |
| HBM | 41 | 14510.0 | 14503.0 | 14496.5 | -0.05% | -0.09% |
| HBM | 55 | 14539.4 | 14527.3 | 14529.1 | -0.08% | -0.07% |
| HBM | 81 | 15525.8 | 15481.2 | 15476.5 | -0.29% | -0.32% |

Observed paired ranges retain all outliers and are not confidence intervals.
DDR KH39 bfirst: paired median -0.25%, range -0.52..+0.90%, positive 1/6
DDR KH39 interleave: paired median -1.01%, range -3.66..+0.60%, positive 1/6
DDR KH41 bfirst: paired median -0.09%, range -12.39..+0.29%, positive 1/6
DDR KH41 interleave: paired median +0.01%, range -0.20..+0.45%, positive 3/6
DDR KH55 bfirst: paired median -0.17%, range -0.31..+3.42%, positive 1/6
DDR KH55 interleave: paired median -0.23%, range -0.48..+3.50%, positive 1/6
DDR KH81 bfirst: paired median +0.14%, range -0.51..+0.31%, positive 5/6
DDR KH81 interleave: paired median +0.16%, range -0.37..+0.45%, positive 5/6
HBM KH39 bfirst: paired median -0.03%, range -0.26..+0.27%, positive 3/6
HBM KH39 interleave: paired median +0.05%, range -0.32..+0.41%, positive 3/6
HBM KH41 bfirst: paired median -0.04%, range -0.24..+0.20%, positive 2/6
HBM KH41 interleave: paired median -0.10%, range -0.24..+0.10%, positive 2/6
HBM KH55 bfirst: paired median -0.08%, range -0.71..-0.03%, positive 0/6
HBM KH55 interleave: paired median -0.07%, range -0.22..-0.00%, positive 0/6
HBM KH81 bfirst: paired median -0.29%, range -0.45..-0.02%, positive 0/6
HBM KH81 interleave: paired median -0.26%, range -0.45..+0.23%, positive 2/6
