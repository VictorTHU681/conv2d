4,587 state/guard cases, 1,722 extended cases, 162 output-ownership cases and 720 timed hashes PASS; zero observed active conflicts.
Six permutations, five timings/process. Median process-average GFLOPS, screening only. One executable derived from v61 b3140af; baseline selects the original alignment policy. Runtime control overhead is shared. This is not an unchanged-v61 binary.

| Memory | KH | Baseline | Zero prefix | Triples prefix | Exact/base | Triples/base |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | 11094.9 | 11082.1 | 11089.0 | -0.11% | -0.05% |
| DDR | 41 | 11071.5 | 11153.3 | 11169.2 | +0.74% | +0.88% |
| DDR | 55 | 11342.6 | 11340.7 | 11340.6 | -0.02% | -0.02% |
| DDR | 81 | 12068.4 | 12058.8 | 12045.3 | -0.08% | -0.19% |
| HBM | 39 | 11112.5 | 11103.3 | 11101.7 | -0.08% | -0.10% |
| HBM | 41 | 11074.1 | 11149.5 | 11154.2 | +0.68% | +0.72% |
| HBM | 55 | 11335.3 | 11328.8 | 11332.9 | -0.06% | -0.02% |
| HBM | 81 | 12054.4 | 12063.2 | 12041.5 | +0.07% | -0.11% |

Observed paired ranges retain all outliers and are not confidence intervals.
DDR KH39 exact: paired median -0.03%, range -0.53..+0.18%, positive 2/6
DDR KH39 triples: paired median -0.10%, range -1.25..+0.65%, positive 1/6
DDR KH41 exact: paired median +0.84%, range +0.34..+0.97%, positive 6/6
DDR KH41 triples: paired median +0.89%, range +0.58..+1.10%, positive 6/6
DDR KH55 exact: paired median -0.03%, range -0.06..+0.07%, positive 1/6
DDR KH55 triples: paired median -0.02%, range -0.09..+0.10%, positive 2/6
DDR KH81 exact: paired median -0.02%, range -0.24..+0.16%, positive 2/6
DDR KH81 triples: paired median -0.14%, range -0.22..-0.04%, positive 0/6
HBM KH39 exact: paired median -0.09%, range -0.16..+0.70%, positive 2/6
HBM KH39 triples: paired median -0.04%, range -0.22..+0.58%, positive 2/6
HBM KH41 exact: paired median +0.52%, range +0.49..+0.87%, positive 6/6
HBM KH41 triples: paired median +0.77%, range -0.20..+0.89%, positive 5/6
HBM KH55 exact: paired median -0.06%, range -0.12..+0.06%, positive 1/6
HBM KH55 triples: paired median -0.02%, range -0.06..+0.11%, positive 2/6
HBM KH81 exact: paired median -0.04%, range -0.45..+0.47%, positive 3/6
HBM KH81 triples: paired median -0.11%, range -0.38..+0.21%, positive 3/6
