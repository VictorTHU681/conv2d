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

Job **1584675**, cn20481 06:38:29–06:43:56, succeeded. Both candidates pass
five signed state modes with step1, guards and output ownership: 3,058 state/guard
and 108 ownership cases, zero observed active conflicts. All 720 timed hashes
pass in six permutations, five timings/process, four shapes and separate DDR/HBM.
[Screen](../../results/v56/experiments/carry-order/summary.md).

Early restore+zero/base KH39/41/55/81: DDR -0.27%/-0.16%/-0.19%/+0.17%;
HBM +0.15%/-0.08%/-0.09%/-0.03%. Early restore-only/base: DDR
-0.12%/+0.04%/+0.01%/-0.14%; HBM -0.01%/-0.01%/+0.08%/+0.02%.
**Both are rejected**: neither provides consistent benefit or resolves the target
KH41 overhead. No original full-reference performance or package acceptance is
claimed for these controls. Source ordering and a timing boundary do not prove
a hardware stall mechanism; no such cause is concluded from this result.

Accepted root remains 1d3f5071. The next [guided-chunk control](guided-chunks.md)
tests reducing transfer frequency in early work while retaining short final chunks.
