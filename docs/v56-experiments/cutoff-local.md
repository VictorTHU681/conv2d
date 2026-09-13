# Check local remaining work before reading global cutoff state

Accepted root remains **8629457 / 1d3f5071…871a**. The prior global cut2 source
41d1a3a4 is rejected after original-reference DDR KH41 -0.26%, despite HBM benefit.
No push. This is a separate control over that rejected candidate, not adoption.

GCC -O3 verbose assembly for the dependency-claim helper shows the shared
unfinished-count load precedes the local remaining>4*step comparison when guidance
is enabled. Thus even pieces that must use a small chunk can read shared state.
Candidate `local` swaps only those two conjuncts, keeping the guidance flag first:
local length is checked before the relaxed shared counter read. Every other source
byte is identical to cut2; the generator reverses the replacement and checks exact
equality. Counter updates, threshold, dependencies, allocation, phase metadata,
input bounds, carry and FP32 kernels do not change.

The new compiler output has a compare and bypass branch before the shared load
at the inspected dependency-claim site. [Compiler audit](../../results/v56/experiments/cutoff-local/compiler_audit.txt)
records both emitted blocks and verbose-assembly hashes. This is an emitted-code
observation for that call site, not an exhaustive linked-binary audit or a speedup
claim. An avoided relaxed read has no acquire synchronization to preserve; active
write-range safety still depends on the existing monotone-cutoff argument.

Host ASan/UBSan scheduling checks pass 21,802 plans, 657,378 dependency edges,
5,834,277 claims and 762,385 resumes. Counts exactly match cut2 for the deterministic
simulation. Active lengths stay frozen and cutoff transitions cannot enlarge
checked ranges. This does not prove every concurrent interleaving or SME access.

Job **1585247**, cn20481, started 07:27:21. Planned checks: local candidate in five
default-step signed packing modes and explicit step1 override; guards; standard
and long ownership cases with actual large/small chunk counters and per-call
unfinished==0 assertions. Totals planned: 1,790 state/guard, 78 ownership cases
(24 long), then six permutations of accepted baseline/cut2/local, four shapes,
DDR/HBM and five timings, 720 timed hashes. Completed 07:31:43: all checks pass,
zero observed active conflicts. The parser also verifies all four source hashes.
Local/base KH39/41/55/81: DDR +0.51%/-0.05%/+0.34%/-0.03%;
HBM +0.26%/+1.22%/+0.32%/+0.07%. These are median process-average GFLOPS
from the screening harness, not original-reference acceptance or a v55 comparison.
The target DDR KH41 benefit is still absent. Not adopted; follow-up is deferred
while a confirmed plan-array capacity defect is repaired.
See [complete screening](../../results/v56/experiments/cutoff-local/summary.md).
Root source and release archives remain unchanged.
