3,058 state/guard cases and 720 timed hashes PASS.
Six permutations, five timings/process. Median process-average GFLOPS, screening only. Current upstream 138dcac/08400a76; K4 scalar tail bounded by compare branches (direct) or remainder bits (bits). Ratios are direct within this job; no historical gains added.

| Memory | KH | Baseline | Direct | Bits | Direct/base | Bits/base |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | 14192.2 | 14207.5 | 14176.7 | +0.11% | -0.11% |
| DDR | 41 | 14402.5 | 14429.9 | 14435.0 | +0.19% | +0.23% |
| DDR | 55 | 14489.2 | 14518.4 | 14574.3 | +0.20% | +0.59% |
| DDR | 81 | 15489.9 | 15490.1 | 15481.5 | +0.00% | -0.05% |
| HBM | 39 | 14292.0 | 14317.6 | 14291.7 | +0.18% | -0.00% |
| HBM | 41 | 14478.9 | 14500.7 | 14512.1 | +0.15% | +0.23% |
| HBM | 55 | 14527.0 | 14559.0 | 14606.7 | +0.22% | +0.55% |
| HBM | 81 | 15487.9 | 15493.5 | 15484.2 | +0.04% | -0.02% |

Observed paired ranges retain all outliers and are not confidence intervals.
DDR KH39 direct: paired median +0.12%, range -0.26..+0.41%, positive 4/6
DDR KH39 bits: paired median -0.13%, range -7.71..+0.09%, positive 2/6
DDR KH41 direct: paired median +0.17%, range -0.19..+0.52%, positive 5/6
DDR KH41 bits: paired median +0.34%, range -0.10..+0.51%, positive 5/6
DDR KH55 direct: paired median +0.17%, range -2.20..+0.33%, positive 5/6
DDR KH55 bits: paired median +0.58%, range +0.53..+0.75%, positive 6/6
DDR KH81 direct: paired median +0.22%, range -0.39..+1.00%, positive 4/6
DDR KH81 bits: paired median -0.02%, range -0.39..+1.53%, positive 3/6
HBM KH39 direct: paired median +0.21%, range -0.20..+0.65%, positive 5/6
HBM KH39 bits: paired median +0.10%, range -0.08..+0.42%, positive 4/6
HBM KH41 direct: paired median +0.12%, range -0.07..+0.59%, positive 5/6
HBM KH41 bits: paired median +0.31%, range -0.12..+0.47%, positive 5/6
HBM KH55 direct: paired median +0.24%, range +0.09..+2.62%, positive 6/6
HBM KH55 bits: paired median +0.55%, range +0.41..+2.98%, positive 6/6
HBM KH81 direct: paired median +0.02%, range -0.32..+0.53%, positive 3/6
HBM KH81 bits: paired median -0.07%, range -0.31..+0.52%, positive 2/6
