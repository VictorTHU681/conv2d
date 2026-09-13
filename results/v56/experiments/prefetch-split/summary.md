1,044 state cases, 896 guard cases and 640 timed hashes PASS.
One diagnostic split-prefetch executable; four Williams orders, five timings/process. Median process-average GFLOPS. Settings vary CONV_ROLL_PDIN and CONV_ROLL_PDOUT; baseline is input3/output3. Screening, not original-reference acceptance.

| Memory | KH | Input3/output3 GFLOPS | Input1/output3 | Input3/output1 | Input1/output1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | 14136.6 | -21.80% | -0.42% | -21.94% |
| DDR | 41 | 14254.0 | -34.33% | +0.41% | -34.43% |
| DDR | 55 | 14469.1 | -34.43% | -0.00% | -34.07% |
| DDR | 81 | 15501.4 | -29.88% | -0.01% | -29.82% |
| HBM | 39 | 14281.2 | -20.53% | +0.17% | -20.91% |
| HBM | 41 | 14391.9 | -32.55% | +0.07% | -33.01% |
| HBM | 55 | 14511.9 | -31.76% | -0.00% | -31.78% |
| HBM | 81 | 15458.5 | -28.08% | -0.10% | -28.18% |

All paired outliers retained; observed ranges are not confidence intervals.
DDR KH39 i1o3: paired median -21.73%, range -22.72..-21.10%, positive 0/4
DDR KH39 i3o1: paired median -0.42%, range -3.33..+1.01%, positive 1/4
DDR KH39 i1o1: paired median -21.94%, range -22.33..-21.27%, positive 0/4
DDR KH41 i1o3: paired median -34.34%, range -35.10..-33.75%, positive 0/4
DDR KH41 i3o1: paired median +0.55%, range -0.09..+0.60%, positive 3/4
DDR KH41 i1o1: paired median -34.56%, range -34.69..-34.23%, positive 0/4
DDR KH55 i1o3: paired median -34.37%, range -34.48..-34.07%, positive 0/4
DDR KH55 i3o1: paired median -0.00%, range -0.11..+0.42%, positive 2/4
DDR KH55 i1o1: paired median -34.08%, range -34.10..-33.85%, positive 0/4
DDR KH81 i1o3: paired median -29.84%, range -29.93..-29.58%, positive 0/4
DDR KH81 i3o1: paired median -0.00%, range -0.62..+0.47%, positive 2/4
DDR KH81 i1o1: paired median -29.81%, range -29.97..-29.70%, positive 0/4
HBM KH39 i1o3: paired median -20.52%, range -21.17..-19.71%, positive 0/4
HBM KH39 i3o1: paired median +0.21%, range +0.01..+0.28%, positive 4/4
HBM KH39 i1o1: paired median -20.96%, range -21.52..-20.21%, positive 0/4
HBM KH41 i1o3: paired median -32.52%, range -32.99..-30.29%, positive 0/4
HBM KH41 i3o1: paired median +0.10%, range -0.34..+3.42%, positive 3/4
HBM KH41 i1o1: paired median -33.12%, range -34.99..-30.57%, positive 0/4
HBM KH55 i1o3: paired median -31.77%, range -31.85..-31.49%, positive 0/4
HBM KH55 i3o1: paired median -0.01%, range -0.02..+0.03%, positive 2/4
HBM KH55 i1o1: paired median -31.79%, range -31.98..-31.53%, positive 0/4
HBM KH81 i1o3: paired median -28.08%, range -28.29..-27.94%, positive 0/4
HBM KH81 i3o1: paired median -0.21%, range -0.37..+0.06%, positive 1/4
HBM KH81 i1o1: paired median -28.31%, range -28.58..-27.97%, positive 0/4
