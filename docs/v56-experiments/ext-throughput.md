# Matrix and EXT instruction-budget diagnostic

The rejected K4 register-window implementation reduces input loads but has no
consistent end-to-end gain. This standalone probe tests whether vector EXT
instructions inherently exceed the matrix/vector overlap budget, and whether
realistic register dependencies make blocked window advancement worse.

Job **1584092**, cn20483 05:57:47–05:57:59, succeeded with all 36 timing records:
one and 38 threads, six variants, three rounds, 1,000 warmup iterations followed
by 1,000,000 measured iterations. Counter frequency comes from CNTFRQ. Matrix
accumulation remains finite; this is not a convolution correctness test.

[Results](../../results/v56/experiments/ext-throughput/summary.md): four FMOPA
with 0, 4 or 8 independent EXT takes about 5.162 ns (8 normalized cycles at
1.55 GHz); 16 EXT takes about 10.323 ns (16 normalized cycles). One-thread
and 38-thread measurements agree. K4-like four-plane windows use 16 FMOPA and
16 EXT, with updated window registers consumed by the next step. Both grouping
all advancements at the end and advancing after each plane take about 5.162 ns
per four FMOPA. The modeled dependencies do not break the overlap budget here.

These are register-only sequences: no input/coefficient loads, row copies,
output events, cache misses or carry transfers. Do not claim that EXT is free
in every real kernel or that either sequence speeds convolution. The result
rules out a simple instruction-count budget explanation for this synthetic
sequence, not every bottleneck in K4.

The next [actual K4 schedule control](k4-ext-schedule.md) moves each boundary
load and its four EXT directly after the corresponding plane's FMOPA group,
to start that load earlier while other planes compute. It preserves the old
load addresses/counts and all FMOPA ordering; only real-kernel measurement
can establish whether this helps. No root operator change or push.

Compiled-code audit verifies all six timed regions contain the intended FMOPA/
EXT counts, no load/store instructions, and an aligned first FMOPA. Four unrolled
window units contain 64 FMOPA / 64 EXT, while four mix units contain 16 FMOPA
and 0/16/32/64 EXT; normalization accounts for this difference. The skipped
alignment padding is outside the loop body. See
[machine-code record](../../results/v56/experiments/ext-throughput/machine_code.txt).
