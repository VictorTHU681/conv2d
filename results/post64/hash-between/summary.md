192 processes completed initial hash validation; 576 timed-output hashes PASS; 384 timed outputs explicitly UNCHECKED (first four in last-only mode). Each process has a checked final timed output.
Eight balanced condition orders; same operator binary used for both hash modes. Driver differs from the official benchmark and changes linked layout. Diagnostic only; no production acceptance or historical adjustment follows from this comparison.

| Memory | KH | Hash mode | Baseline | Indexed all | All/base |
| --- | ---: | --- | ---: | ---: | ---: |
| DDR | 39 | each | 14176.3 | 14153.4 | -0.16% |
| DDR | 39 | last-only | 14174.8 | 14159.5 | -0.11% |
| DDR | 41 | each | 14439.8 | 14467.8 | +0.19% |
| DDR | 41 | last-only | 14447.4 | 14446.3 | -0.01% |
| DDR | 55 | each | 14494.0 | 14505.5 | +0.08% |
| DDR | 55 | last-only | 14484.0 | 14498.6 | +0.10% |
| HBM | 39 | each | 14284.8 | 14289.0 | +0.03% |
| HBM | 39 | last-only | 14234.2 | 14260.9 | +0.19% |
| HBM | 41 | each | 14485.5 | 14481.6 | -0.03% |
| HBM | 41 | last-only | 14464.6 | 14482.5 | +0.12% |
| HBM | 55 | each | 14533.4 | 14536.2 | +0.02% |
| HBM | 55 | last-only | 14530.2 | 14544.5 | +0.10% |

| Memory | KH | Baseline last-only/each | Indexed-all last-only/each |
| --- | ---: | ---: | ---: |
| DDR | 39 | -0.01% | +0.04% |
| DDR | 41 | +0.05% | -0.15% |
| DDR | 55 | -0.07% | -0.05% |
| HBM | 39 | -0.35% | -0.20% |
| HBM | 41 | -0.14% | +0.01% |
| HBM | 55 | -0.02% | +0.06% |

Paired all/base ranges retain every outlier; not confidence intervals.
DDR KH39 each: median -0.14%, range -0.36..+0.47%, positive 2/8
DDR KH39 last-only: median +0.03%, range -0.67..+2.45%, positive 4/8
DDR KH41 each: median +0.16%, range -0.01..+0.43%, positive 7/8
DDR KH41 last-only: median +0.11%, range -0.52..+1.39%, positive 6/8
DDR KH55 each: median +0.08%, range -0.12..+0.18%, positive 6/8
DDR KH55 last-only: median +0.08%, range -0.38..+3.99%, positive 5/8
HBM KH39 each: median +0.08%, range -1.71..+1.09%, positive 5/8
HBM KH39 last-only: median +0.23%, range -0.33..+2.56%, positive 5/8
HBM KH41 each: median -0.03%, range -1.12..+0.37%, positive 4/8
HBM KH41 last-only: median +0.03%, range -4.01..+0.34%, positive 4/8
HBM KH55 each: median +0.04%, range -0.97..+0.14%, positive 6/8
HBM KH55 last-only: median +0.06%, range -0.28..+0.60%, positive 6/8

Paired last-only/each ranges within each operator binary; not confidence intervals.
DDR KH39 baseline: median -0.01%, range -3.02..+0.55%, positive 4/8
DDR KH39 indexed-all: median -0.10%, range -0.45..+0.62%, positive 3/8
DDR KH41 baseline: median -0.01%, range -1.43..+0.36%, positive 4/8
DDR KH41 indexed-all: median -0.22%, range -0.53..+0.47%, positive 2/8
DDR KH55 baseline: median -0.09%, range -3.77..+0.12%, positive 2/8
DDR KH55 indexed-all: median -0.05%, range -0.60..+0.11%, positive 2/8
HBM KH39 baseline: median -0.35%, range -2.63..+0.35%, positive 2/8
HBM KH39 indexed-all: median -0.23%, range -1.06..+1.26%, positive 2/8
HBM KH41 baseline: median -0.11%, range -0.27..+0.17%, positive 2/8
HBM KH41 indexed-all: median +0.02%, range -4.19..+1.11%, positive 4/8
HBM KH55 baseline: median -0.01%, range -0.45..+0.11%, positive 3/8
HBM KH55 indexed-all: median +0.02%, range -0.32..+1.07%, positive 5/8
