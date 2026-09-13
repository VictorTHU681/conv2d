3,058 state/guard cases, 1,148 extended cases, 108 output-ownership cases and 720 timed hashes PASS; zero observed active conflicts.
Six permutations, five timings/process. Median process-average GFLOPS, screening only. Three fixed executables: unchanged v62/v63 baseline cf42580/5a423250, v62 plus zero prefix (exact), and the validated v61 zero-prefix candidate (legacy). No runtime experiment knob. Ratios use this same-job v62 baseline.

| Memory | KH | Baseline | v62 zero prefix | v61 zero prefix | Exact/base | Legacy/base |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | 14104.8 | 14129.5 | 14099.7 | +0.17% | -0.04% |
| DDR | 41 | 14342.9 | 14335.5 | 14152.1 | -0.05% | -1.33% |
| DDR | 55 | 14489.5 | 14538.8 | 14503.6 | +0.34% | +0.10% |
| DDR | 81 | 15503.0 | 15473.5 | 15511.1 | -0.19% | +0.05% |
| HBM | 39 | 14260.2 | 14240.1 | 14258.7 | -0.14% | -0.01% |
| HBM | 41 | 14419.8 | 14407.5 | 14278.5 | -0.08% | -0.98% |
| HBM | 55 | 14521.8 | 14569.8 | 14552.9 | +0.33% | +0.21% |
| HBM | 81 | 15490.8 | 15472.9 | 15520.2 | -0.12% | +0.19% |

Observed paired ranges retain all outliers and are not confidence intervals.
DDR KH39 exact: paired median +0.02%, range -1.06..+0.64%, positive 3/6
DDR KH39 legacy: paired median -0.04%, range -6.14..+0.61%, positive 3/6
DDR KH41 exact: paired median +0.03%, range -0.54..+0.12%, positive 4/6
DDR KH41 legacy: paired median -1.33%, range -1.74..-0.97%, positive 0/6
DDR KH55 exact: paired median +0.32%, range +0.27..+0.50%, positive 6/6
DDR KH55 legacy: paired median +0.11%, range -0.05..+0.16%, positive 5/6
DDR KH81 exact: paired median -0.16%, range -0.46..+0.12%, positive 1/6
DDR KH81 legacy: paired median -0.07%, range -0.29..+0.51%, positive 3/6
HBM KH39 exact: paired median -0.27%, range -0.52..+0.81%, positive 1/6
HBM KH39 legacy: paired median -0.02%, range -0.30..+0.23%, positive 3/6
HBM KH41 exact: paired median -0.16%, range -0.32..+0.17%, positive 2/6
HBM KH41 legacy: paired median -1.07%, range -1.20..-0.88%, positive 0/6
HBM KH55 exact: paired median +0.32%, range +0.13..+1.07%, positive 6/6
HBM KH55 legacy: paired median +0.22%, range -0.89..+0.95%, positive 5/6
HBM KH81 exact: paired median -0.17%, range -0.54..+0.23%, positive 2/6
HBM KH81 legacy: paired median +0.13%, range -0.22..+0.49%, positive 5/6
