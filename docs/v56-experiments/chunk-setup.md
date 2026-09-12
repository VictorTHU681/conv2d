# Modular phase setup and ZA carry controls

Unpublished local v56 experiment based on accepted 8b6b295 / bb82ce3b…6819.
Root operator and accepted packages remain unchanged. No push.

[Phase attribution](chunk-overhead.md) measures ~63–65 us/thread parameter
setup at short2 versus ~16–18 us at step8. The generated GCC worker contains
repeated signed divisions for adjacent normalized phases. ZA state transfer
also becomes more frequent with short chunks.

Four isolated candidates:
- baseline: accepted source;
- phase: compute ja % KH once, derive neighboring row counters and folded
  coefficient phases through bounded subtraction/addition;
- carry4: transfer four adjacent 64-byte ZA slices per iteration with immediate
  slice/address offsets, advancing base/index by 256 bytes/four rows;
- both: combine the two changes.

The phase helper takes a,b in [0,KH), returns (a-b) modulo KH using at most one
addition. The B phase is A-16 modulo KH; rolling selection guarantees KH>=16.
All arithmetic kernels, group planning, packing, claim and output dependencies
remain byte-identical. Every coefficient is still rebuilt each call; no exact
public-shape or call-stage selection is added. ZA still transfers all 64 slices
with the existing acquire/release publication ordering. Target SVL remains 64
bytes, the same previously documented limitation.

Host UBSan equivalence test passes **22,495,904** cases: KH16..256, all normalized
row/group phases, four row quotients including 65,537. The helper in the host
test is asserted byte-identical to the generated candidate. This proves the
sampled modular identities; it does not replace server integration checks.
The combined source compiles with server GCC12.3.1/binutils2.41; no compute-node
execution was attempted on the login node.

Job **1583712**, cn20481 05:09:21–05:15:38, succeeded. All 2,984 signed
state/guard cases, 54 runtime output-ownership cases and 640 timed hashes pass;
zero observed active conflicts. Correctness uses step1 to stress continuation;
performance uses the accepted structural default. Four Williams orders balance
position and predecessor. [Full screen](../../results/v56/experiments/chunk-setup/summary.md).

Against 8b6b295, phase improves KH41 DDR 0.66%, but regresses KH55 0.44% DDR /
0.55% HBM. Carry4 gains 0.11–0.36% in all DDR shapes, but loses 0.22% at HBM
KH41 and 0.38% at HBM KH81. Both is inferior to phase at KH41 and retains
KH55 regression. **No variant adopted.** Original-benchmark three-way job
**1583757**, cn20483, started 05:17:05 and is running (baseline/phase/carry4).
No official result is yet claimed.

Job **1583738**, cn20483 05:14:03–05:15:02, profiles all four variants in four
balanced orders. 8,512 phase records and 160 timed hashes pass; every call
preserves 916,936 row work units and 186 pieces, saves equal resumes.
[Phase results](../../results/v56/experiments/chunk-setup/profile_summary.md):
phase reduces setup from 72.9 to 45.3 us DDR and 73.2 to 44.0 us HBM.
Carry4 reduces restore/zero from 34.1 to 21.2 us DDR and 33.5 to 21.0 us HBM;
save/publish changes little. Both does not add the two effects linearly, and
carry-only also changes measured setup. Counter boundaries, compiler register
allocation and code layout perturb attribution; these are not production timings.
Do not use the instrumented worker-end improvements to overrule the screening
regressions.

Static code audit counts 25 signed divisions in the baseline worker across all
branches versus two in phase; this is not a dynamic per-chunk count. K5's full
instruction addresses and words are identical across all four binaries. The
three F4 arithmetic blocks also preserve words and offsets modulo 128, although
phase moves them by 128 bytes. F3's two identical arithmetic blocks instead move
from baseline offsets 48/80 to phase 0/32, carry4 80/112, both 32/64 modulo 128.
This motivates [diagnostic skipped-padding controls](f3-padding.md); it does not
establish code alignment as the cause of KH55's regression.

Additional ASan/UBSan host audit of the actual grouping functions passes 34,704
plans / 192,096 groups: KH16..256, four kernel widths, nine output-width boundaries
and NF overrides -1/0/3/4. Every group base/fold phase lies in [0,KH), validating
the subtraction helper's preconditions for these actual group configurations.

[Source hashes](../../results/v56/experiments/chunk-setup/sources.sha256),
[host equivalence](../../results/v56/experiments/chunk-setup/phase_check.txt).

The F3 padding diagnostic 1583770 is complete: all correctness hashes pass,
but KH55 gains at most 0.20% DDR / 0.14% HBM against the unadopted phase source,
with changes in non-F3 shapes too. It does not establish alignment as the whole
regression cause; no padding adoption. Job **1583794**, requested cn20481,
profiles KH55's phase and main/tail regions with the already compiled immutable
four instrumentation binaries. It succeeded 05:23:14–05:23:30: 8,512 phase records
and 160 timed hashes pass, with 1,372,376 row work units / 358 pieces per call,
and saves equal resumes. [KH55 profile](../../results/v56/experiments/chunk-setup/profile55_summary.md)
shows only 0.7–0.8 us/thread setup savings for phase, versus 27–29 us at KH41.
Carry4 reduces ZA restore/zero by 15.6 us DDR / 17.2 us HBM. F3 and single-16
region timings change little; this instrumented binary **does not reproduce**
the uninstrumented phase regression at KH55. It cannot identify that regression's
cause or justify disregarding it. Compiler layout and timing-boundary effects
remain unresolved; wait for the original benchmark comparison before adoption.
