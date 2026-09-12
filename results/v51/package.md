# v51 final package verification

Donau job `1579170` succeeded on cn20481 on 2026-09-12.
The archive was extracted into a fresh temporary directory and its own
`bash run.sh` compiled and ran all four full official-reference cases.
All four passed with maximum absolute error zero.

- Production source commit: `19849bf`.
- Archive SHA-256: `6d524bf08a1f3ee2d411bbaacf4a8d83e8f6ab429578bb00cf355ccda1e4122f`.
- Source SHA-256: `e8e6b3f08c50c4e5cfd50906a99e171ade548a56097f7151ffb9f2aaa5056315`.
- Actual entry-point placement: `[run.sh] host=cn20481 node=5 cpus=38 threads=38 run='numactl -N 5 --preferred=21 ./conv2d_test'`.
- Raw log: [zip.log](zip.log).

The one-run package GFLOPS were 13674.8890 / 14177.2174 /
14555.4633 / 14550.6379. This run validates the delivered entry point;
use the controlled alternating NUMA-1 comparison in [accept.log](accept.log)
for the reported optimization gains, rather than comparing different nodes.

Reproduce the official comparison summary:

```sh
python3 tools/summarize_v51.py --official results/v51/accept.log
```
