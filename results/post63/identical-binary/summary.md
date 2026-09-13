720 timed hashes PASS. All three executable hashes equal the validated local baseline; control0/control1 share an inode and control2 has a distinct inode with identical bytes.
Six permutations, five timings/process; ratios of median process-average GFLOPS. Same-length executable paths. Every reported difference is a negative-control observation, not a code improvement or a universal noise bound.

| Memory | KH | Control0 | Same-inode control1 | Copy control2 | Control1/0 | Control2/0 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | 14149.8 | 14154.3 | 14189.5 | +0.03% | +0.28% |
| DDR | 41 | 14491.9 | 14485.5 | 14506.1 | -0.04% | +0.10% |
| DDR | 55 | 14524.2 | 14530.4 | 14525.4 | +0.04% | +0.01% |
| DDR | 81 | 15493.0 | 15496.2 | 15506.6 | +0.02% | +0.09% |
| HBM | 39 | 14309.4 | 14295.6 | 14319.4 | -0.10% | +0.07% |
| HBM | 41 | 14560.2 | 14534.5 | 14560.5 | -0.18% | +0.00% |
| HBM | 55 | 14557.8 | 14556.0 | 14570.0 | -0.01% | +0.08% |
| HBM | 81 | 15532.4 | 15476.9 | 15489.5 | -0.36% | -0.28% |

All paired outliers retained; ranges are not confidence intervals.
DDR KH39 control1: paired median -0.23%, range -0.49..+0.62%, positive 2/6
DDR KH39 control2: paired median +0.20%, range -0.53..+0.73%, positive 4/6
DDR KH41 control1: paired median -0.06%, range -4.88..+0.18%, positive 1/6
DDR KH41 control2: paired median +0.10%, range -0.10..+0.16%, positive 5/6
DDR KH55 control1: paired median +0.03%, range -0.02..+0.10%, positive 4/6
DDR KH55 control2: paired median +0.02%, range -0.04..+0.10%, positive 4/6
DDR KH81 control1: paired median +0.11%, range -0.22..+0.49%, positive 4/6
DDR KH81 control2: paired median +0.04%, range -0.11..+0.49%, positive 3/6
HBM KH39 control1: paired median -0.15%, range -2.38..+0.16%, positive 2/6
HBM KH39 control2: paired median +0.10%, range -0.10..+0.38%, positive 4/6
HBM KH41 control1: paired median -0.22%, range -6.37..+0.19%, positive 1/6
HBM KH41 control2: paired median -0.01%, range -0.05..+0.35%, positive 1/6
HBM KH55 control1: paired median +0.01%, range -0.13..+0.19%, positive 3/6
HBM KH55 control2: paired median +0.05%, range -0.02..+0.21%, positive 5/6
HBM KH81 control1: paired median -0.20%, range -0.65..+0.10%, positive 2/6
HBM KH81 control2: paired median -0.18%, range -0.52..+0.46%, positive 3/6

Allocated-node PMU permission probe: PMU_PROBE_AVAILABLE. A successful true command would only establish access, not useful kernel counters.
