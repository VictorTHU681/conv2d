# Larger early chunks with fine completion granularity

Baseline is accepted local v56 **8629457 / 1d3f5071…871a**. No push.
Earlier K5 profiling showed short chunks reduce the last-worker gap but increase
parameter and carry overhead. Transfer-width and restore-placement controls do
not improve throughput. These candidates test fewer early chunk boundaries.

Only actual prepared plans containing K5 and no explicit CONV_ROLL_STEP override
enable guidance. Other plans and every explicit override retain fixed behavior.
Base step remains 2*KH. grow2 uses 2*step while remaining rows exceed 4*step;
grow4 uses 4*step while remaining rows exceed 8*step. Near completion both return
to base step, with the final chunk clamped to remaining rows. No public complete
shape, memory-placement or call-stage selection is introduced.

One exact roll_chunk_rows helper determines both dependency wait ranges in
resume_claim and the executed worker range. Nonfinal chunks remain KH multiples,
so existing prepared phases remain valid. Input copy bounds, ZA/FMLA carry,
release publication, coefficient packing and FP32 kernels are unchanged. No
input/weight/result cache. Existing external concurrent-caller, allocation and
SVL limitations remain. Compiler layout also changes, so actual throughput must
be measured rather than inferred from the lower boundary count.

Host ASan/UBSan checks extract the candidates' actual types, grouping, dependency
builder, helper and claim code. Both pass **21,802 plans**: grow2 has 657,024 edges,
5,834,803 claims and 763,108 resumed claims; grow4 has 657,362 edges, 5,841,085
claims and 768,157 resumes. Checks cover grouping ownership, overlapping active
chunk rows, non-stuck completion and KH-aligned continuation offsets, across
KH16..256, width boundaries and step1..64. This simulation is finite and does not
execute SME instructions or prove all possible concurrent interleavings.

Screening job **1584781**, cn20481, started 06:46:30. Planned checks: both candidates
in five default-step signed state packing modes; separate explicit step1 override;
guards; standard output ownership; and long K5 ownership cases with actual large
and small chunk counters. The long diagnostic uses OMP=3, KH41/57/249, widths
193/257, output heights 4099/4113, and default/parallel packing, 48 cases across
two candidates. Counters are diagnostic-only and never used for timing. Default
sweeps must unset CONV_ROLL_STEP, otherwise they would disable the new policy.
Then six permutations, five timings/process, four shapes and separate DDR/HBM.
Planned 3,580 state/guard, 156 ownership cases, 720 timed hashes. Still running.

Profile job **1584806**, cn20483 06:47:50–06:48:39, succeeded. All six orders,
five timed calls/process for KH41 DDR/HBM: 36 processes, 9,576 phase records and
180 timed hashes validate. Saves equal resumes; every call processes 916,936
row work units and 186 pieces. [Profile summary](../../results/v56/experiments/guided-chunks/profile_summary.md).

Chunks per worker fall 295.3 -> 155.4 / 98.4. DDR restore/zero falls 45.6 ->
14.6 / 13.3 us; save/publish falls 53.5 -> 31.6 / 24.2 us. But the last-minus-mean
worker end gap rises 42.0 -> 79.7 / 128.8 us. Last completion is 5863.6 ->
5864.9 / 5951.5 us, so the measured savings do not improve DDR completion.
HBM last completion improves 5832.2 -> 5757.5 / 5765.4 us in this instrumented
run. Timers and layout perturb execution; no accepted end-to-end gain is inferred.
Screening 1584781 is still running and remains decisive before any next acceptance.
Root and archives unchanged.

## Matched-binary follow-up

Job **1584858**, cn20483 06:51:33–06:51:57, succeeds using one grow2
instrumented binary. For KH41 explicit CONV_ROLL_STEP=2 disables guidance while
retaining base step; unset enables guidance. Six alternating AB/BA rounds,
five timings/process, separate DDR/HBM: 24 processes, 6,384 phase records,
120 timed hashes validate. Saves equal resumes and work/piece counts are unchanged.
[Matched summary](../../results/v56/experiments/guided-chunks/same_binary_summary.md).

DDR fixed/guided mean end is 5795.4/5789.0 us, while last end is 5845.6/5898.0 us.
The paired per-call end spread increases 47.8 -> 106.9 us. Guided setup, restore
and publish save roughly 28.6 + 10.5 + 23.5 us/thread, but kernel-region time rises
62.9 us and the longer tail costs another ~59 us. HBM last end improves
5808.9 -> 5756.1 us, with spread 28.0 -> 34.3 us. These within-job results remove
binary-layout differences as the sole explanation for the DDR tail, while keeping
all instrumentation limitations. The kernel-region difference is not yet assigned
to a specific cache or hardware event. Parameter parsing remains inside the call.

This attribution does not replace accepted-root uninstrumented screening 1584781,
which remains running. No candidate is adopted from profile data. Root and archives
remain 1d3f5071.

## Completed uninstrumented screening

Job **1584781**, cn20481 06:46:30–06:53:34, succeeded. All 3,580 state/guard,
156 ownership cases and 720 timed hashes pass. Each of the four long diagnostic
processes observes both large and small chunks, with zero active output conflicts.
[Screen summary](../../results/v56/experiments/guided-chunks/summary.md).

| KH | DDR grow2/base | DDR grow4/base | HBM grow2/base | HBM grow4/base |
| --- | ---: | ---: | ---: | ---: |
| 39 | -0.07% | +0.13% | -0.02% | -0.14% |
| 41 | -0.57% | -2.31% | +0.73% | +0.61% |
| 55 | -0.29% | -0.29% | -0.36% | -0.38% |
| 81 | +0.22% | +0.20% | +0.07% | +0.35% |

**Both rejected** for the DDR target. The HBM gain does not justify selecting by
memory-placement or hiding DDR regressions. Non-K5 code does not enable guidance,
but source/layout changes can still affect those shapes. Original full-reference
performance and archive acceptance are not claimed for these rejected controls.
All preceding pending screening statements describe the earlier checkpoint;
this completed outcome supersedes them. Root remains 1d3f5071, no push.

## Further matched-binary attribution

PMU job **1584918**, cn20483, is submitted using one uninstrumented grow2 binary,
fixed step2 versus guidance in six alternating rounds, separate DDR/HBM, 200 timed
calls/process. Immutable steady driver is staged beside source. Events are user
cycles, instructions, L1 loads and L1 load misses. Counters cover the whole process,
including setup, two initial calls, and spinning; the driver's output sample is
not complete correctness validation. They are not operator-only counts or the
original allocation/timing protocol. Full correctness evidence is the completed
screen above. This measurement is pending; no hardware-event cause is claimed yet.

PMU job **1584918**, cn20483 06:55:57–06:56:53, is now complete. All 24
steady-allocation processes and four counters validate at 100% running time.
[Summary](../../results/v56/experiments/guided-chunks/pmu_summary.md).
Guidance reduces L1 load misses by 12.25% DDR / 12.01% HBM, yet DDR steady time
increases 0.75% (5.8363 -> 5.8803 ms). HBM steady time falls 0.34%
(5.7819 -> 5.7623 ms). Instructions increase from 183.236 to 184.394 billion
per process in DDR, and 182.927 to 183.854 billion in HBM. These totals include
spinning and setup, so they cannot be called arithmetic-kernel instruction counts.
Fewer L1 misses do not explain an improvement in DDR; its measured regression
remains. No particular cache-miss latency or hardware-stall mechanism is proven.

The next [global tail cutoff](tail-cutoff.md) stops guidance when few pieces remain,
targeting the independently observed completion spread. No source is adopted
from these diagnostic measurements.
