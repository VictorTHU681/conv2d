3,058 state/guard cases and 720 timed hashes PASS.
Six permutations, five timings/process. Median process-average GFLOPS, screening only. Current upstream 138dcac/08400a76; K4 scalar tail integer word loads/stores: original loop or bit-branch unrolling. Ratios are direct within this job; no historical gains added.

| Memory | KH | Baseline | GPR loop | GPR bits | GPR loop/base | GPR bits/base |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | 14197.7 | 14235.2 | 14147.8 | +0.26% | -0.35% |
| DDR | 41 | 14456.8 | 14476.2 | 14423.2 | +0.13% | -0.23% |
| DDR | 55 | 14511.2 | 14525.6 | 14546.1 | +0.10% | +0.24% |
| DDR | 81 | 15481.3 | 15514.1 | 15473.0 | +0.21% | -0.05% |
| HBM | 39 | 14285.5 | 14337.5 | 14255.1 | +0.36% | -0.21% |
| HBM | 41 | 14511.4 | 14534.8 | 14448.1 | +0.16% | -0.44% |
| HBM | 55 | 14544.5 | 14559.0 | 14587.8 | +0.10% | +0.30% |
| HBM | 81 | 15488.8 | 15496.2 | 15472.9 | +0.05% | -0.10% |

Observed paired ranges retain all outliers and are not confidence intervals.
DDR KH39 gpr_loop: paired median +0.29%, range -0.82..+0.67%, positive 5/6
DDR KH39 gpr_bits: paired median -0.33%, range -0.81..-0.09%, positive 0/6
DDR KH41 gpr_loop: paired median +0.11%, range +0.00..+0.33%, positive 6/6
DDR KH41 gpr_bits: paired median -0.24%, range -6.57..-0.10%, positive 0/6
DDR KH55 gpr_loop: paired median +0.09%, range +0.05..+0.18%, positive 6/6
DDR KH55 gpr_bits: paired median +0.25%, range +0.05..+0.31%, positive 6/6
DDR KH81 gpr_loop: paired median +0.22%, range +0.04..+0.66%, positive 6/6
DDR KH81 gpr_bits: paired median +0.01%, range -0.36..+0.41%, positive 3/6
HBM KH39 gpr_loop: paired median +0.45%, range -2.79..+3.80%, positive 5/6
HBM KH39 gpr_bits: paired median -0.22%, range -0.34..+3.43%, positive 2/6
HBM KH41 gpr_loop: paired median +0.16%, range -0.10..+0.49%, positive 4/6
HBM KH41 gpr_bits: paired median -0.42%, range -3.92..+0.05%, positive 1/6
HBM KH55 gpr_loop: paired median +0.10%, range -4.46..+0.51%, positive 5/6
HBM KH55 gpr_bits: paired median +0.36%, range +0.14..+0.80%, positive 6/6
HBM KH81 gpr_loop: paired median +0.03%, range -0.37..+0.15%, positive 3/6
HBM KH81 gpr_bits: paired median -0.09%, range -0.60..+0.20%, positive 1/6
