1953 state/input-output guard cases PASS, including 200 F3 suffix boundary cases.
All six downloaded binaries match their pre-execution SHA-256 records.
144 original full-reference checks PASS; maximum errors zero.
Three fixed sources; all six permutations, five timings/process. Original upstream 138dcac source 08400a76; u4 and island compared directly in this job. Medians of process-average GFLOPS. No historical ratios added.

| Memory | KH | Upstream | U4 | Island | U4/upstream | Island/upstream | Island/U4 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | 14177.3 | 14154.2 | 14189.9 | -0.16% | +0.09% | +0.25% |
| DDR | 41 | 14452.8 | 14466.5 | 14477.7 | +0.09% | +0.17% | +0.08% |
| DDR | 55 | 14526.4 | 14541.5 | 14535.7 | +0.10% | +0.06% | -0.04% |
| DDR | 81 | 15467.0 | 15465.8 | 15511.2 | -0.01% | +0.29% | +0.29% |
| HBM | 39 | 14273.8 | 14255.4 | 14264.6 | -0.13% | -0.06% | +0.06% |
| HBM | 41 | 14523.4 | 14489.2 | 14519.9 | -0.24% | -0.02% | +0.21% |
| HBM | 55 | 14563.1 | 14574.9 | 14579.4 | +0.08% | +0.11% | +0.03% |
| HBM | 81 | 15465.0 | 15502.9 | 15482.3 | +0.24% | +0.11% | -0.13% |

All outliers retained; observed ranges are not confidence intervals.
DDR KH39 u4/baseline: paired median -0.20%, range -0.76..+0.08%, positive 1/6
DDR KH39 island/baseline: paired median +0.02%, range -0.50..+0.35%, positive 4/6
DDR KH39 island/u4: paired median +0.27%, range -0.24..+0.42%, positive 5/6
DDR KH41 u4/baseline: paired median +0.11%, range -0.53..+1.87%, positive 3/6
DDR KH41 island/baseline: paired median +0.00%, range -0.11..+1.97%, positive 3/6
DDR KH41 island/u4: paired median +0.08%, range -0.36..+0.51%, positive 4/6
DDR KH55 u4/baseline: paired median +0.08%, range -0.05..+0.39%, positive 5/6
DDR KH55 island/baseline: paired median +0.11%, range +0.00..+0.28%, positive 6/6
DDR KH55 island/u4: paired median -0.01%, range -0.20..+0.08%, positive 3/6
DDR KH81 u4/baseline: paired median +0.03%, range -0.66..+0.38%, positive 3/6
DDR KH81 island/baseline: paired median +0.20%, range -0.35..+0.61%, positive 4/6
DDR KH81 island/u4: paired median +0.33%, range -0.20..+0.63%, positive 5/6
HBM KH39 u4/baseline: paired median -0.19%, range -0.51..+0.18%, positive 2/6
HBM KH39 island/baseline: paired median +0.01%, range -0.49..+0.40%, positive 3/6
HBM KH39 island/u4: paired median +0.06%, range -0.10..+0.76%, positive 5/6
HBM KH41 u4/baseline: paired median -0.24%, range -0.46..+0.18%, positive 2/6
HBM KH41 island/baseline: paired median -0.04%, range -0.22..+0.08%, positive 1/6
HBM KH41 island/u4: paired median +0.18%, range -0.21..+0.37%, positive 5/6
HBM KH55 u4/baseline: paired median +0.07%, range +0.02..+0.36%, positive 6/6
HBM KH55 island/baseline: paired median +0.12%, range +0.09..+0.23%, positive 6/6
HBM KH55 island/u4: paired median +0.02%, range -0.13..+0.11%, positive 4/6
HBM KH81 u4/baseline: paired median +0.09%, range -0.32..+0.49%, positive 5/6
HBM KH81 island/baseline: paired median +0.13%, range -0.22..+0.23%, positive 5/6
HBM KH81 island/u4: paired median -0.14%, range -0.34..+0.41%, positive 3/6
