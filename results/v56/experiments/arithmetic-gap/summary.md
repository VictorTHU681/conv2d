336 calibration rows; 64 convolution processes, 8512 worker records, 320 timed hashes validate.
Accepted ebf36923 source; one node/job. Four rotating shape orders, alternating plain/profile order. Calibration brackets every round; each bracket has three alternating probe orders. No assumed core frequency. Work totals are source-counted FMOPA tile steps, including chunk warmup and padded execution; they are not hardware instruction-counter readings.

Calibration: median of three per-thread means, ns per four-FMOPA step (mix8 additionally executes eight indexed FMLAs). All probe variants and outliers retained in the log.

| Round | mix0 before ns | mix0 after ns | Drift | mix8 before ns | mix8 after ns | Drift |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 5.161556 | 5.161660 | +0.002% | 5.162268 | 5.161483 | -0.015% |
| 1 | 5.161535 | 5.161782 | +0.005% | 5.161529 | 5.161803 | +0.005% |
| 2 | 5.161889 | 5.161510 | -0.007% | 5.161691 | 5.161539 | -0.003% |
| 3 | 5.161504 | 5.161507 | +0.000% | 5.161506 | 5.161596 | +0.002% |
mix0: all 24 means median=5.161554 range=5.161484..5.163503 ns/step
mix2: all 24 means median=5.161571 range=5.161479..5.165155 ns/step
mix4: all 24 means median=5.161579 range=5.161479..5.163226 ns/step
mix6: all 24 means median=5.161547 range=5.161474..5.166582 ns/step
mix8: all 24 means median=5.161610 range=5.161481..5.163957 ns/step
mix10: all 24 means median=6.451895 range=6.451831..6.470421 ns/step
mix12: all 24 means median=7.742283 range=7.742206..7.743740 ns/step
mix16: all 24 means median=10.323251 range=10.322940..10.347894 ns/step
mix18: all 24 means median=11.613595 range=11.613333..11.639691 ns/step
vec2: all 24 means median=1.692620 range=1.689869..1.694820 ns/step
vec4: all 24 means median=1.886696 range=1.886645..1.890084 ns/step
vec8: all 24 means median=2.580763 range=2.580707..2.584058 ns/step
vec16: all 24 means median=5.161535 range=5.161479..5.189553 ns/step
vec18: all 24 means median=5.806821 range=5.806649..5.810368 ns/step

Register-only reference: sum(tile_steps)/4 * bracket_mean(ns_per_step) / 38 / 1000 us. This projects perfectly balanced independent arithmetic; it is neither a rigorous architectural lower bound nor guaranteed recoverable headroom. Real kernels also perform loads, copies, ZA transfers, output events and scheduling. mix8 is sensitivity, not an exact instruction-mix model for every bucket.

| Memory | KH | Plain wall us | Profile wall us | Profile wall overhead | mix0 reference us | mix8 reference us | Plain wall / mix0 ref | Worker end spread us |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | 5324.500 | 5997.500 | +12.64% | 4712.326 | 4712.333 | 1.130 | 28.838 |
| DDR | 41 | 5890.500 | 6527.000 | +10.81% | 5143.333 | 5143.340 | 1.145 | 41.734 |
| DDR | 55 | 11095.500 | 11737.000 | +5.78% | 10296.150 | 10296.164 | 1.078 | 51.710 |
| DDR | 81 | 22379.500 | 22999.500 | +2.77% | 20801.393 | 20801.422 | 1.076 | 150.224 |
| HBM | 39 | 5296.000 | 5901.500 | +11.43% | 4712.326 | 4712.333 | 1.124 | 43.912 |
| HBM | 41 | 5850.500 | 6555.000 | +12.04% | 5143.333 | 5143.340 | 1.137 | 35.136 |
| HBM | 55 | 11064.500 | 11668.000 | +5.45% | 10296.150 | 10296.164 | 1.075 | 46.922 |
| HBM | 81 | 22342.500 | 23028.500 | +3.07% | 20801.393 | 20801.422 | 1.074 | 120.736 |

Region times: median of four process medians, timed calls 3–7. Per-worker means, not serialized stages. Timers include argument setup and ZA restoration; profile wall also includes diagnostic reporting. Reference differences cannot identify a particular hardware stall or be advertised as speedups.

| Memory | KH | Bucket | Tile steps | Region us/thread | mix0 reference us/thread | Difference us | Region / reference |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | pair | 122228184 | 4449.547 | 4150.639 | 298.908 | 1.072 |
| DDR | 39 | K4/K5 | 16540608 | 733.069 | 561.688 | 171.381 | 1.305 |
| DDR | 41 | pair | 128164032 | 4653.738 | 4352.209 | 301.529 | 1.069 |
| DDR | 41 | K4/K5 | 23297056 | 1040.260 | 791.124 | 249.136 | 1.315 |
| DDR | 55 | pair | 185652720 | 6565.216 | 6304.416 | 260.800 | 1.041 |
| DDR | 55 | single16 | 92826360 | 3315.311 | 3152.208 | 163.103 | 1.052 |
| DDR | 55 | K4/K5 | 24722384 | 999.523 | 839.526 | 159.997 | 1.191 |
| DDR | 81 | pair | 543263760 | 19245.449 | 18448.212 | 797.237 | 1.043 |
| DDR | 81 | K8/K9 | 69296560 | 2719.970 | 2353.180 | 366.789 | 1.156 |
| HBM | 39 | pair | 122228184 | 4431.762 | 4150.639 | 281.123 | 1.068 |
| HBM | 39 | K4/K5 | 16540608 | 704.843 | 561.688 | 143.156 | 1.255 |
| HBM | 41 | pair | 128164032 | 4642.835 | 4352.209 | 290.626 | 1.067 |
| HBM | 41 | K4/K5 | 23297056 | 1032.508 | 791.124 | 241.384 | 1.305 |
| HBM | 55 | pair | 185652720 | 6550.185 | 6304.416 | 245.769 | 1.039 |
| HBM | 55 | single16 | 92826360 | 3304.401 | 3152.208 | 152.193 | 1.048 |
| HBM | 55 | K4/K5 | 24722384 | 1004.774 | 839.526 | 165.248 | 1.197 |
| HBM | 81 | pair | 543263760 | 19287.592 | 18448.212 | 839.380 | 1.045 |
| HBM | 81 | K8/K9 | 69296560 | 2717.981 | 2353.180 | 364.801 | 1.155 |

| Memory | KH | Prepare us | Dispatch us | Workers us | Mean pack us/thread |
| --- | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | 18.750 | 2.055 | 5282.460 | 20.444 |
| DDR | 41 | 17.060 | 2.410 | 5851.895 | 23.904 |
| DDR | 55 | 22.830 | 2.625 | 11039.000 | 3.498 |
| DDR | 81 | 19.180 | 2.685 | 22257.730 | 4.742 |
| HBM | 39 | 18.530 | 1.930 | 5250.000 | 19.677 |
| HBM | 41 | 16.950 | 2.535 | 5816.680 | 23.568 |
| HBM | 55 | 22.735 | 2.585 | 11000.950 | 3.482 |
| HBM | 81 | 19.340 | 2.810 | 22282.100 | 4.572 |
