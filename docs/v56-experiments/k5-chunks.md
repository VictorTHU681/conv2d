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
output-ownership cases. This job is pending; no performance result is claimed.

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
