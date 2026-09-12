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
