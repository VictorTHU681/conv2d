96 processes, 25536 worker records and 480 timed hashes validate; work/table totals invariant across all variants per shape.
Four Williams orders in one split-profile binary, five timings/process; timed calls 3–7, median of process medians. Instrumentation changes code and is attribution only.

| Memory | KH | Variant | Prepare us | Pair region us/thread | Other regions us/thread | Last end us | Last-minus-mean end us |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| DDR | 41 | i3o3 | 14.575 | 4664.208 | 1011.841 | 5851.055 | 70.511 |
| DDR | 41 | i1o3 | 14.440 | 6829.239 | 1534.392 | 8712.310 | 236.563 |
| DDR | 41 | i3o1 | 14.460 | 4665.733 | 1007.822 | 5858.035 | 73.195 |
| DDR | 41 | i1o1 | 14.855 | 6836.638 | 1537.478 | 8735.225 | 271.681 |
| DDR | 55 | i3o3 | 19.680 | 6590.298 | 4316.687 | 11073.925 | 50.991 |
| DDR | 55 | i1o3 | 21.280 | 9743.895 | 6764.340 | 16764.165 | 167.742 |
| DDR | 55 | i3o1 | 19.805 | 6587.793 | 4316.955 | 11068.990 | 51.442 |
| DDR | 55 | i1o1 | 20.885 | 9759.213 | 6750.543 | 16760.650 | 169.733 |
| DDR | 81 | i3o3 | 17.825 | 19254.046 | 2719.207 | 22259.270 | 133.523 |
| DDR | 81 | i1o3 | 17.790 | 27733.670 | 3663.834 | 31741.615 | 136.152 |
| DDR | 81 | i3o1 | 18.405 | 19252.039 | 2721.280 | 22262.140 | 138.902 |
| DDR | 81 | i1o1 | 17.605 | 27759.764 | 3666.936 | 31862.875 | 152.205 |
| HBM | 41 | i3o3 | 15.060 | 4649.429 | 990.087 | 5776.210 | 29.289 |
| HBM | 41 | i1o3 | 14.760 | 6679.560 | 1472.922 | 8477.210 | 198.193 |
| HBM | 41 | i3o1 | 14.885 | 4649.688 | 990.503 | 5773.960 | 32.969 |
| HBM | 41 | i1o1 | 14.815 | 6693.832 | 1461.842 | 8449.085 | 153.651 |
| HBM | 55 | i3o3 | 19.640 | 6580.415 | 4317.254 | 11046.680 | 52.896 |
| HBM | 55 | i1o3 | 20.750 | 9439.295 | 6474.485 | 16200.050 | 190.183 |
| HBM | 55 | i3o1 | 19.750 | 6578.611 | 4317.198 | 11051.020 | 52.798 |
| HBM | 55 | i1o1 | 20.325 | 9440.194 | 6439.615 | 16140.270 | 169.196 |
| HBM | 81 | i3o3 | 17.430 | 19281.542 | 2720.841 | 22271.825 | 127.877 |
| HBM | 81 | i1o3 | 18.315 | 27185.129 | 3563.371 | 31028.000 | 184.263 |
| HBM | 81 | i3o1 | 18.365 | 19259.550 | 2720.721 | 22271.865 | 121.624 |
| HBM | 81 | i1o1 | 18.275 | 27188.248 | 3562.780 | 31150.850 | 177.843 |

Regions include argument setup and ZA restore, not arithmetic-only timings. Per-worker means are not serialized stages; counters cannot identify a physical issue-port cause.
