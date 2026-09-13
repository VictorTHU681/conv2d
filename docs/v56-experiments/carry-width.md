# ZA transfer width after prepared phases

Baseline is accepted local v56 **8629457**, source **1d3f5071…871a**. No push.
The matched combined profile retains ~57 us/thread in restore/zero and ~67 us in
save/publish at the observed ~1.20 GHz. Those boundaries include instrumentation
and other operations; they motivate a control, not a predicted speedup.

The current loop transfers four adjacent 64-byte slices per iteration, repeating
16 times. Candidates u8/u16 transfer 8/16 slices and repeat 8/4 times. Both still
transfer every one of the 64 ZA slices (4096 bytes), retain acquire/release, and
change only carry_load_za/carry_store_za. Generator reverses those replacements
and requires exact equality with accepted source. No input/weight/output cache,
coefficient packing, task claim, phase preparation or FP32 arithmetic changes.
Fixed SVL=64 remains a prerequisite.

All three sources compile on the target toolchain. Emitted-machine-code audit
verifies adjacent ZA and memory offsets, loop initial value, both increments,
limit and backedge, not merely source counts. [Audit](../../results/v56/experiments/carry-width/machine_code.txt).
Larger inline sequences can also change surrounding compiler layout; a timing
change cannot automatically be attributed only to loop-control instructions.

Job **1584556**, cn20481 06:30:26–06:35:58, succeeded. Both candidates pass
five signed state packing modes with step1, guards, and runtime output ownership:
3,058 state/guard cases and 108 ownership cases with zero active conflicts.
All 720 timed hashes pass in six permutations, five timings/process, four shapes
and separate DDR/HBM. [Screen summary](../../results/v56/experiments/carry-width/summary.md).

Eight/base KH39/41/55/81: DDR +0.04%/-0.03%/+0.08%/+0.05%; HBM
-0.04%/-0.43%/+0.13%/-0.32%. Sixteen/base: DDR -1.18%/-0.27%/-0.51%/-0.16%;
HBM -0.04%/-0.56%/-0.52%/-0.19%. **Both are rejected**: eight offers no clear
DDR gain and has HBM regressions; sixteen regresses all measured combinations.
Neither source nor archive is adopted, and these screening checks are not an
original full-reference performance acceptance.

Fewer loop-control instructions alone do not establish a better convolution.
Code layout and surrounding instruction scheduling remain confounders, especially
for u16 whose compiler placement changes. [Restore placement](carry-order.md)
is the next independent control, motivated by the observed restore-region increase
following prepared scalar parameters. It does not assume a specific hardware stall
has already been proven.
