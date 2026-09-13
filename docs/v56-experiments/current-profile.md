# Current accepted-source phase profile across four cases

Accepted local source **8629457 / 1d3f5071…871a** only; immutable driver e5e52c8d.
No source change or push. Job **1585113**, cn20483 07:13:44–07:14:14, succeeded.
Four rotating shape orders, separate DDR/HBM, five timings/process: 32 processes,
8,512 thread records and 160 timed hashes validate. Thread step totals match
aggregate buckets; executed work and coefficient-table byte totals remain constant
for each shape across calls and placements. [Summary](../../results/v56/experiments/current-profile/summary.md).

Prepare is 10–16 us/call. Mean per-worker packing/wait region is ~19–22 us for
KH39/41 and ~2–3 us for KH55/81; the latter averages include mostly zero-wait
workers and do not mean the serial packing thread takes only 2–3 us. These
measurements remain small relative to total worker completion.

DDR end spread KH39/41/55/81 is 32.8/63.7/49.6/118.0 us, HBM
50.1/39.8/43.2/126.3 us. The last worker is main-pair-region-majority in
18/16/17/18 of 20 timed calls DDR, and 20/16/17/19 of 20 HBM. This does not
identify one slow instruction; it limits claims that only residual kernels or
packing determine completion. Pair regions dominate KH39/41/81; KH55 also spends
~3.31 ms/worker in single-16 and ~1.00 ms in K4, versus ~6.56 ms in pairs.

Region timers include argument setup and ZA restore as well as kernel execution;
the thread tail field combines non-pair buckets. Aggregate buckets are validated
and split in the summary. Instrumentation changes code/layout/scheduling, so
reported times are attribution, not production throughput. Different per-call
medians need not add exactly. Any new optimization still requires uninstrumented
screening and original-reference acceptance before replacing the root source.
