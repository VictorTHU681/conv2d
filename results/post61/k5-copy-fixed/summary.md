1,148 fixed-candidate extended checks and 144 original full-reference checks PASS; zero out-of-input spans and maximum errors zero.
Independent fixed sources, no runtime layout knob. Six complete permutations, five timings/process; median process-average GFLOPS. Baseline is unchanged published v61 b3140af/2c406547. These ratios are not added to the prior runtime-control screen.

| Memory | KH | v61 | Exact | Triples | Exact/v61 | Triples/v61 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | 11120.3 | 11157.2 | 11118.4 | +0.33% | -0.02% |
| DDR | 41 | 11097.9 | 11206.5 | 11214.3 | +0.98% | +1.05% |
| DDR | 55 | 11348.1 | 11377.9 | 11351.8 | +0.26% | +0.03% |
| DDR | 81 | 12067.7 | 12071.9 | 12064.3 | +0.04% | -0.03% |
| HBM | 39 | 11114.3 | 11156.3 | 11127.6 | +0.38% | +0.12% |
| HBM | 41 | 11128.5 | 11196.4 | 11213.2 | +0.61% | +0.76% |
| HBM | 55 | 11333.2 | 11370.1 | 11338.5 | +0.33% | +0.05% |
| HBM | 81 | 12037.4 | 12047.7 | 12048.8 | +0.09% | +0.10% |

All paired outliers retained; observed ranges are not confidence intervals.
DDR KH39 exact: paired median +0.37%, range -0.21..+0.65%, positive 4/6
DDR KH39 triples: paired median -0.07%, range -0.25..+0.57%, positive 3/6
DDR KH41 exact: paired median +0.95%, range -1.12..+1.26%, positive 5/6
DDR KH41 triples: paired median +0.96%, range +0.75..+1.39%, positive 6/6
DDR KH55 exact: paired median +0.25%, range +0.18..+0.33%, positive 6/6
DDR KH55 triples: paired median +0.04%, range -0.06..+0.13%, positive 4/6
DDR KH81 exact: paired median +0.04%, range -0.12..+0.32%, positive 4/6
DDR KH81 triples: paired median +0.05%, range -0.16..+0.30%, positive 4/6
HBM KH39 exact: paired median +0.40%, range +0.14..+0.74%, positive 6/6
HBM KH39 triples: paired median +0.13%, range -0.12..+0.42%, positive 4/6
HBM KH41 exact: paired median +0.61%, range +0.27..+0.93%, positive 6/6
HBM KH41 triples: paired median +0.76%, range +0.44..+1.13%, positive 6/6
HBM KH55 exact: paired median +0.31%, range +0.27..+0.45%, positive 6/6
HBM KH55 triples: paired median +0.05%, range -0.02..+0.18%, positive 4/6
HBM KH81 exact: paired median +0.06%, range -0.46..+0.28%, positive 4/6
HBM KH81 triples: paired median +0.00%, range -0.34..+0.27%, positive 3/6
