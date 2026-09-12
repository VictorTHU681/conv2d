# Continuation chunk controls on adopted K5

Accepted operator: 113d3d6 / source
`4b35b3d5af1d85c8d6cf2ddc54073c0ccc75467cdc185229e0bbd906b355f905`.
No code or package change is proposed yet; no push.

The [worker-level profile](k5-cost.md) finds that ordinary K5's last worker is
main-F4-heavy in 27/30 timed calls in both memory placements. Its end-time gap
above the mean is about 199 us DDR / 85 us HBM. Test whether continuation chunk
length affects this tail, rather than assume the five-row tail kernel is the
last worker or change empirical scheduling weights again.

Job **1583450**, requested on cn20481, compares existing CONV_ROLL_STEP values
2, 4, 8 (accepted default) and 16 in the same executable. A chunk is step*KH
input rows, with existing carry and output dependencies unchanged. Four Williams
orders balance position and predecessor across all four benchmark shapes and
allowed memory placements. Each step also receives 54 signed bitwise runtime
output-ownership cases. Job 1583450 succeeded on cn20481, 04:40:11–04:41:41. All 216 ownership cases and 640 timed hashes passed, with zero observed active conflicts.

Both candidate.c and the screening fbench.c are immutable exports of 113d3d6,
with their hashes recorded. FBENCH_FORCE is explicitly unset. The fbench source
is staged beside the candidate so the build does not depend on an older shared
server copy. Any future comparison to older logs must account for that driver
provenance; this experiment's four controls all use the same binary.

Reproduce the source staging with git show 113d3d6:conv2d.c and
113d3d6:tools/fbench.c into build/v56/experiments/k5-chunks/candidate.c and
fbench.c, then run tools/gen_v56_output_overlap_audit.py with
--root build/v56/experiments/k5-chunks --variants candidate. Run the job script
only on an allocated SME compute node. Screening does not replace official
full-reference validation if a different default is proposed later.

## Completed screening and attribution

[Screen results](../../results/v56/experiments/k5-chunks/summary.md): step 2
improves DDR KH41 by 3.53%, but is -0.05% in HBM and regresses KH81 by
2.02% DDR / 1.92% HBM. Do not change the global default to 2.

Job **1583578**, cn20481 04:48:38–04:50:09, succeeded. Thread instrumentation
uses the same executable for steps 8/2/4, all six orders, both placements,
five calls per process. All 180 timed hashes and 9,576 worker records validate.
DDR step 2 reduces the median last-worker completion from 6058 to 5880 us,
and its gap above the mean worker end from 202 to 44 us. HBM gap also shrinks
84 to 33 us, but last completion increases from 5818 to 5841 us. Thread
instrumentation perturbs execution; these are attribution measurements, not
production timing. The last worker remains predominantly main-F4-heavy.

Separate same-binary steady-allocation PMU measurements use 200 calls per
process and six permutations (36 processes). All four events report 100%
running time. DDR step 2 decreases steady time by 2.64%, while HBM increases
0.32%. **L1 data load misses increase 15.57% DDR / 16.32% HBM.** Thus the
improvement cannot be attributed to fewer L1 misses. Counters cover the whole
process, including allocation, two initial calls and spinning; they are not
operator-only instruction counts or official benchmark validation.

Raw logs and strict summaries: [thread](../../results/v56/experiments/k5-chunks/thread_summary.md),
[PMU](../../results/v56/experiments/k5-chunks/pmu_summary.md),
[profile log](../../results/v56/experiments/k5-chunks/profile.log).
A structural K5-only default is tested separately in [k5-default.md](k5-default.md).
