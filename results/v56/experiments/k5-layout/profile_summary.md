72 profiled processes, 504 call records and 360 timed hashes PASS.
Median of six process medians, each from timed calls 3–7. Calls 1/2 excluded. CNTFRQ scales ticks.
Profiling changes code layout and adds instrumentation. These are amortized kernel-region costs, not official performance or instruction latency.

| Memory | KH | Variant | Prepare us | Pack mean us | Workers us | Main ns/tile | Tail ns/tile | Main mean us | Tail mean us | Total tile steps |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | 39 | baseline | 9.9950 | 18.5270 | 5279.3300 | 1.3845 | 1.6909 | 4453.2790 | 736.0325 | 138768792 |
| DDR | 39 | triplet | 9.6250 | 19.7135 | 5283.5800 | 1.3825 | 1.6931 | 4446.7650 | 736.9670 | 138768792 |
| DDR | 39 | triplet_out | 9.6650 | 18.2570 | 5325.4150 | 1.3832 | 1.7248 | 4449.0530 | 750.7635 | 138768792 |
| DDR | 41 | baseline | 7.9500 | 17.7210 | 6039.4600 | 1.3772 | 1.4384 | 4644.7165 | 1252.3310 | 161241376 |
| DDR | 41 | triplet | 8.4450 | 21.6815 | 6040.7400 | 1.3952 | 1.7608 | 4705.5800 | 1079.5070 | 151461088 |
| DDR | 41 | triplet_out | 8.0300 | 20.5715 | 6001.8800 | 1.3899 | 1.7461 | 4687.6390 | 1070.5090 | 151461088 |
| HBM | 39 | baseline | 9.4900 | 17.5745 | 5242.1400 | 1.3774 | 1.6444 | 4430.4400 | 715.7730 | 138768792 |
| HBM | 39 | triplet | 9.4850 | 19.0090 | 5244.9600 | 1.3776 | 1.6578 | 4431.1190 | 721.6200 | 138768792 |
| HBM | 39 | triplet_out | 9.4100 | 18.9115 | 5242.5150 | 1.3762 | 1.6797 | 4426.6375 | 731.1235 | 138768792 |
| HBM | 41 | baseline | 7.9750 | 20.6870 | 5850.9150 | 1.3489 | 1.3872 | 4549.3255 | 1207.7735 | 161241376 |
| HBM | 41 | triplet | 8.4700 | 21.7945 | 5817.6900 | 1.3736 | 1.6901 | 4632.8190 | 1036.1535 | 151461088 |
| HBM | 41 | triplet_out | 8.4400 | 20.7320 | 5803.2100 | 1.3712 | 1.6874 | 4624.6140 | 1034.5040 | 151461088 |

Worker-duration statistics (us), including packing and scheduling. These are per-thread durations, not absolute finish timestamps.

| Memory | KH | Variant | Minimum | Mean | Maximum | Max minus mean |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| DDR | 39 | baseline | 5249.0 | 5257.0 | 5274.5 | 17.5 |
| DDR | 39 | triplet | 5238.0 | 5248.5 | 5279.0 | 30.5 |
| DDR | 39 | triplet_out | 5256.5 | 5265.0 | 5319.5 | 54.5 |
| DDR | 41 | baseline | 5930.5 | 5960.0 | 6034.5 | 74.5 |
| DDR | 41 | triplet | 5818.0 | 5852.0 | 6034.0 | 182.0 |
| DDR | 41 | triplet_out | 5789.5 | 5822.0 | 5995.0 | 173.0 |
| HBM | 39 | baseline | 5186.0 | 5204.0 | 5237.0 | 33.0 |
| HBM | 39 | triplet | 5199.5 | 5211.0 | 5239.0 | 28.0 |
| HBM | 39 | triplet_out | 5208.5 | 5219.5 | 5237.5 | 18.0 |
| HBM | 41 | baseline | 5785.5 | 5814.0 | 5845.5 | 31.5 |
| HBM | 41 | triplet | 5704.5 | 5727.5 | 5812.5 | 85.0 |
| HBM | 41 | triplet_out | 5691.5 | 5715.5 | 5799.0 | 83.5 |
