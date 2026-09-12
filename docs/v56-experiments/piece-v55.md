# Direct published-v55 comparison for prepared phases and ZA carry4

Job **1584490**, cn20483 06:25:47–06:34:26, succeeded. Published v55 is commit
0a39770 / source 489948af…2d61; accepted local v56 is 8629457 / source
1d3f5071…871a. Original benchmark SHA-256 2548861a…e927, original compile
command, 38 threads, CPU node 1. DDR uses the problem placement; HBM preferred
is measured separately and is not explicitly authorized by the saved statement.

Six alternating AB/BA rounds, five timings per process, four shapes and two
placements produce **96 full-reference PASS checks, all maximum errors zero**.
All three snapshot hashes are checked by the parser. Median of six process-average
GFLOPS yields these direct net changes (no historical percentages are added):

| KH | DDR v56/v55 | HBM v56/v55 |
| --- | ---: | ---: |
| 39 | +1.64% | -0.25% |
| 41 | +4.14% | +0.89% |
| 55 | +1.37% | +1.14% |
| 81 | +2.43% | +2.52% |

All four DDR shapes improve in all six paired rounds. HBM KH39 regresses in
all six (-0.49% to -0.07%); the other HBM shapes improve in all six. Observed
paired ranges are not confidence intervals. No observations are discarded.
[Full summary](../../results/v56/experiments/piece-v55/summary.md),
[snapshots](../../results/v56/experiments/piece-v55/sources.sha256).

The prior bb82ce3b/v55 checkpoint was a different job and cannot be compounded
with the same-job bb82ce3b/1d3f5071 acceptance to invent a current net result.
Its DDR KH41 +4.72% and the current +4.14% do not constitute a direct comparison
between the two v56 sources. That comparison is documented separately in
[piece-carry](piece-carry.md), including its limitations and HBM regressions.
Historical v55 retains known bounds/output-ownership defects outside these four
checks. Passing this benchmark does not make it generally safe or compliant.
No root code change or push is made by this measurement.
