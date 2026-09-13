# Direct published-v55 versus accepted-local-v56 checkpoint

Snapshots are immutable published **0a39770** and accepted local **8b6b295**.
The current local source is bb82ce3b4826514e9ce6f729ef017a23d5aa08d2396f5d0975a512e39da76819.
No speculative phase, outlining or layout-anchor source enters this comparison.
The staged bench_conv.c is byte-identical to original d2b65c4. Build uses the
saved problem command, with source paths redirected only to these snapshots.

Job **1583906**, cn20483 05:39:51–05:48:32, succeeded. All **96** original
full-reference checks pass with zero maximum error. Six alternating AB/BA rounds,
five timings per process; median of six process-average GFLOPS.

[Direct results](../../results/v56/experiments/v55-checkpoint/summary.md):

| KH | DDR v56/v55 | HBM v56/v55 |
| --- | ---: | ---: |
| 39 | +1.72% | -0.13% |
| 41 | +4.72% | +0.63% |
| 55 | +1.42% | +1.13% |
| 81 | +2.17% | +2.22% |

These include the accepted correctness fixes, K9/F4/K5 changes and K5-only short
chunks together. HBM KH39's small negative result is retained explicitly. This measures the net accepted change directly; never
add percentages from experiments with different local baselines.

Historical v55 retains known input-boundary/output-ownership defects outside
these benchmark checks and is used only as a comparison. A successful run
cannot establish its general safety or restore it as the current implementation.
HBM placement remains separate and not explicitly approved by the saved problem.
No push; this is a checkpoint of the overnight local v56 work, not a final
publication claim for an as-yet-unselected future source.
