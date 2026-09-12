# ZA restore placement around scalar parameter setup

Accepted baseline is local v56 **8629457**, source **1d3f5071…871a**. No push.
The four-way instrumented profile shows prepared parameters reduce setup but
increase the subsequent restore region. Wider transfer loops do not improve
end-to-end results. The next control tests ordering rather than another width.

Candidates retain four-slice ZA loops. `early` moves restore/first-chunk zeroing
before scalar kp_t construction; `load_early` moves restore only and leaves
first-chunk zeroing in the original position. Both remain after a successful
acquire claim and before the arithmetic kernel. Saving state, release publishing,
output dependencies, shape metadata, coefficient packing, arithmetic order and
input bounds remain unchanged. Diagnostic t0 moves with restore so its region
still includes both restore and parameter setup. These are diagnostic candidates,
not an assertion that store-buffer pressure or a particular hardware stall exists.

Generator modifies only roll_worker, verifies single restore/zero sites and
records immutable source and driver hashes. All three compile successfully with
the target toolchain. No ZA-writing operation is introduced in scalar parameter
setup. Runtime correctness and actual timing are still required; source ordering
alone does not establish the emitted schedule or a speedup.

Job **1584675**, requested on cn20481, is submitted for both candidates' five
signed state packing modes with step1, guards and runtime output ownership,
then six permutations of baseline/early/load_early, five timings/process, all
four shapes and separate DDR/HBM. Planned 3,058 state/guard cases, 108 ownership
cases and 720 timed hashes. Log: `results/v56/experiments/carry-order/screen.log`.
No correctness/performance acceptance yet claimed. Root source and packages remain
1d3f5071; latest archives only refresh the verified direct-v55 measurement README.
