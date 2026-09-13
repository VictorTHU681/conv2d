1,455 state/guard checks; 60 processes, 15960 per-thread PMU records and 300 timed hashes PASS. Work/table totals invariant.
PMU running/enabled ratios: min 1.000000000, median 1.000000000. Counts below are raw, not scaled; reduced ratios must not be hidden.
One executable and shared indirect dispatch, 128-byte-aligned K5 alternatives. PMU scope is the entire SME worker loop, including claims, state transfers, pair and K5 kernels; it is not K5-only. All counter syscalls are outside streaming mode. Timings are diagnostic, not acceptance results.

| Memory | Mode | Instrumented GFLOPS | Pair us/thread | K5 us/thread | PMU scope us/thread | User cycles/thread | User instructions/thread | Aggregate CPI |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | baseline | 12100.6 | 4706.735 | 943.756 | 5732.812 | 8879633.105 | 23187171.421 | 0.383 |
| DDR | early | 12051.8 | 4703.038 | 948.163 | 5731.722 | 8881132.526 | 23187752.211 | 0.383 |
| DDR | spread | 12078.0 | 4706.972 | 963.995 | 5752.339 | 8912461.118 | 23187521.053 | 0.384 |
| HBM | baseline | 12101.7 | 4678.060 | 920.467 | 5677.140 | 8797618.961 | 23186653.421 | 0.379 |
| HBM | early | 11983.1 | 4676.777 | 927.410 | 5684.408 | 8806495.539 | 23186719.750 | 0.380 |
| HBM | spread | 12003.0 | 4678.666 | 933.570 | 5689.567 | 8817406.882 | 23188765.711 | 0.380 |

Observer overhead, same executable and baseline mode; six alternating on/off orders. These changes include counter setup, ioctls, reads and scheduling disturbance, not just event counting.
DDR: PMU off 12273.9, on 12149.2 GFLOPS; on/off -1.02%, paired range -3.76..+1.64%.
HBM: PMU off 12281.4, on 12295.0 GFLOPS; on/off +0.11%, paired range -2.23..+1.49%.
Neither CPI nor elapsed region time identifies a physical issue port. No fixed noise threshold or universal speedup follows from these diagnostic samples.
