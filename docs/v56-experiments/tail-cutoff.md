# Stop guidance globally before the worker tail

Accepted root remains local **8629457 / 1d3f5071…871a**, no push. Previous
per-piece guidance reduces L1 misses but regresses DDR, with a larger completion
spread confirmed in one instrumented binary. These controls test switching all
workers back to base chunks when few pieces remain.

Four variants: accepted baseline; prior rejected grow2 guidance; cut2; cut4.
The new controls extend only grow2. An atomic unfinished-piece counter resets to
npieces on every call and decrements once after a piece publishes final completion.
While more than 2*nthreads / 4*nthreads remain, the existing 4*KH early chunks
are allowed; otherwise every new chunk returns to base 2*KH. Local remaining-row
thresholds still apply. Only actual K5 plans without CONV_ROLL_STEP override enable
this policy. No input/weight/output cache or memory-placement dispatch is added.

The dependency check and execution both use roll_chunk_rows. The unfinished count
only decreases within one call. If it crosses the cutoff between those queries,
execution can shrink but cannot enlarge the checked output range; conservative
extra waiting is allowed. Existing acquire/release, input bounds, phase metadata,
ZA/FMLA transfers and FP32 kernels remain. External concurrent callers are still
unsupported. The counter adds shared reads and a completion RMW; its cost must be
included in real throughput, not ignored as scheduler bookkeeping.

Host ASan/UBSan simulations extract actual grouping, dependency builder, helper
and claim code. Active chunk lengths are frozen at claim/execution, rather than
recomputed after the counter changes. Tests also check the cutoff transition is
non-enlarging, counter completion equals outstanding pieces, no stuck work,
KH-aligned resumes, and active output rectangles. Each candidate passes 21,802
plans: cut2 657,378 edges / 5,834,277 claims / 762,385 resumes; cut4 657,137 edges /
5,836,431 claims / 764,361 resumes. These are finite simulations, not SME execution
or exhaustive concurrent-interleaving proof.

Runtime diagnostic sources additionally require the unfinished counter to be zero
after every enabled convolution call. The long output test still requires actual
large and small chunks and zero observed active output conflicts. These assertions
and counters are not in timing binaries or release archives.

Screening **1585009**, cn20481: both new candidates in five default-step signed
state packing modes, explicit step1 override controls, guards, standard and long
output ownership; planned 3,580 state/guard + 156 ownership cases, then four
Williams orders / four shapes / separate DDR-HBM / five timings, 640 timed hashes.
It is pending, with no correctness or performance acceptance claimed.

Profile **1585010**, cn20483: same four variants in four Williams orders for KH41,
five timed calls/process, DDR/HBM. Completed-piece counter updates are inside the
save/publish timing bracket. The previous generator excluded no such update
because prior sources had none; it now handles this new publication suffix.
This job is pending and profiling will not substitute for uninstrumented timing.
Root operator and archives remain unchanged.

## Completed phase profile

Job **1585010**, cn20483 07:04:53–07:07:03, succeeded: 32 processes, 8,512 phase
records and 160 timed hashes validate. Saves equal resumes, with 916,936 row work
units and 186 pieces per call. [Profile summary](../../results/v56/experiments/tail-cutoff/profile_summary.md).

DDR baseline/guided/cut2/cut4 chunks per worker are 295.34/155.37/155.46/205.43.
The cut2 threshold barely changes boundary counts relative to prior guidance;
cut4 changes them materially. Last completion is 5870.1/5882.5/5860.4/5864.1 us,
while median per-call last-minus-mean spread is 55.1/87.1/83.4/80.0 us. Thus both
cutoffs remain worse than baseline in DDR end spread, despite slightly better
instrumented last completion in this run. HBM last completion is
5834.1/5767.5/5758.0/5768.1 us, with spreads 38.4/48.9/36.9/36.2 us.

Counter updates are included in publish measurements. Different binaries and
instrumentation perturb layout/scheduling, and negligible cut2 boundary-count
change limits what can be attributed to the policy itself. These modest timing
changes are not accepted throughput improvements. Runtime screening 1585009 is
still live and no root change is made before its complete result.

## Completed screening and original-benchmark follow-up

Job **1585009**, cn20481 07:04:27–07:12:33, succeeded. All 3,580 state/guard,
156 ownership cases (48 long cases with both chunk sizes), and 640 timed hashes
validate with zero observed active conflicts. Per-call completion-counter checks
in diagnostics pass. [Full screen](../../results/v56/experiments/tail-cutoff/summary.md).

cut2/base KH39/41/55/81: DDR +0.21%/+0.17%/+0.17%/+0.03%; HBM
+0.18%/+1.26%/+0.14%/-0.05%. These modest DDR gains warrant original-reference
confirmation, not immediate adoption. cut4/base DDR is +0.21%/-0.20%/+0.19%/-0.48%,
so cut4 is not advanced. Older pending-screen descriptions above are historical.

Original-benchmark job **1585125**, cn20481, compares accepted baseline and cut2
in six alternating AB/BA rounds, five timings/process, four shapes and separate
DDR/HBM (96 planned complete reference checks). It is pending; root source and
archives stay unchanged. Candidate packages are staged separately under
`build/v56/experiments/tail-cutoff/package` and have not yet been runtime accepted.

Archive job **1585149**, cn20483, is submitted for all three staged cut2 packages,
four original full-reference checks each. Candidate archive hashes are recorded
in `packages_candidate.sha256`; current root package manifests are not replaced.
Package and original-benchmark confirmations remain pending. Current-profile job
1585113 concerns accepted 1d3f5071, not this candidate.

## Original-reference and archive result: not adopted

Job **1585125**, cn20481 07:14:44–07:22:12, succeeded: all 96 original full-reference
checks pass, maximum error zero. Six AB/BA rounds, five timings/process.
[Confirmation](../../results/v56/experiments/tail-cutoff/confirm_summary.md).
cut2/base KH39/41/55/81 is DDR -0.01%/-0.26%/+0.13%/+0.01%, HBM
+0.14%/+1.16%/+0.13%/-0.22%. DDR KH41 has only 3/6 positive paired rounds;
its median paired change is -0.01%, with observed range -0.92% to +0.27%.
Other outliers remain in the raw data (DDR KH39 as low as -12.19%). No data is
discarded and observed ranges are not confidence intervals.

Job **1585149**, cn20483 07:18:27–07:20:40, also succeeds: all three candidate
archives pass 12 complete reference checks, maximum error zero. Local staged
hashes match server logs. Manifest paths were expanded from stage-relative
`submissions/` names to explicit stage paths; archive bytes/hashes did not change.
The staging tool now emits full stage paths directly. [Archive audit](../../results/v56/experiments/tail-cutoff/archive_audit.txt).

**cut2 is not adopted**: original-reference timing does not retain the small DDR
screening gain, despite HBM KH41 benefit. cut4 was not advanced due its screening
regressions. All jobs above are terminal. Root and current archives remain accepted
1d3f5071 and the current direct-v55 table remains valid. No push.

[Local-check-first control](cutoff-local.md) follows the completed rejection.
Compiler output confirms the original helper can load shared cutoff state before
checking that a local piece is too short to grow. The new control changes only
this conditional order; it is isolated and has no accepted result yet.
