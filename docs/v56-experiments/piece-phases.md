# Prepare piece phases once per call

Accepted baseline remains 8b6b295 / bb82ce3b…6819; no push. The previous
per-chunk normalized-phase rewrite saves work but has unresolved cross-shape
regressions. Outlining and layout-anchor controls are not adopted.

For a nonfinal continuation chunk, rows = max(1,CONV_ROLL_STEP)*KH. Starting
from off=0, every subsequent claim therefore has off divisible by KH. The
coefficient/event phases computed from ja=piece.ja+off are identical to phases
computed from piece.ja. The scheduler and row-size calculation are unchanged.

Candidate cached fills four unsigned-byte phases (ya,yb,folded-row,folded-event)
once per piece in roll_prepare on **every call**. KH<=256 bounds every normalized
phase to 0..255. These four bytes occupy the old padding after rpiece_t.item:
size stays 32 bytes, ja stays at offset 8, dependencies stay at 24. Static assertions
verify that layout. The two piece constructors use designated fields so the new
members cannot absorb old positional initializer values. No new allocation or
larger scheduler record is introduced.

Workers load these phases and derive adjacent event counters with comparisons;
the legacy kind17 two-fold branch retains its original extra formulas. Grouping,
claims, output dependencies, arithmetic kernels and bounded input copies remain
byte-identical. The prepared values depend only on current shape and piece
boundaries; no input, coefficient contents or results are reused between calls.
R/kf are still completely rebuilt each call. Existing external concurrent-caller,
allocation-failure and fixed-SVL limitations are unchanged.

Host ASan/UBSan check extracts the actual grouping, helper, assignment statements
and record type, then compares against the original per-chunk modular expressions:
**14,407,200 cases across 34,704 plans PASS**. It covers KH16..256, four kernel
widths, nine output-width boundaries, NF -1/0/3/4, five piece starts, five chunk
sizes and three continuation offsets. It also checks exact record size/offsets.
This is finite equivalence evidence, not a proof of every memory access.

Job **1583947**, cn20481 05:43:21–05:48:35, succeeded: 2,051 state/guard
cases, 54 output-ownership cases and 720 timed hashes pass, with zero observed
active conflicts. Six permutations compare accepted baseline, rejected normalized
phase, and prepared phases; correctness stresses step1 and five packing modes.

[Screen](../../results/v56/experiments/piece-phases/summary.md) rejects adoption:
prepared phases change KH41 -0.83% DDR / -0.37% HBM and KH55 -0.27% / -0.26%.
KH39 is +0.03% / -0.16%, KH81 +0.18% / +0.33%. Correct equivalence and fewer
repeated calculations do not establish an end-to-end optimization. No original
full-reference performance acceptance or package adoption is claimed.

Job **1584012**, cn20481 05:50:43–05:51:28, succeeded. All 9,576 phase records
and 180 timed hashes pass; saves equal resumes, each call preserves 916,936 row
work units and 186 pieces. [Phase summary](../../results/v56/experiments/piece-phases/profile_summary.md)
shows prepared metadata reduces setup from 69.6 to 25.3 us/thread DDR and 68.2
to 23.4 us HBM. ZA restore/zero grows from about 34 to 52 us/thread. Serial host
preparation adds only ~2 us (8.5 to 10.5 us DDR / 8.6 to 10.6 us HBM), insufficient
to explain the uninstrumented KH41 regression by itself.

Instrumented worker end times improve, so this diagnostic again does not reproduce
the actual screening regression. Timers/compiler layout and execution ordering
remain confounders; do not infer that the restore increase is the whole cause.
The observed setup saving does not overrule the negative uninstrumented result.
No candidate adoption. Root accepted source remains
bb82ce3b…6819. All metadata/cache language here means freshly prepared shape-only
values within one call, not input/weight/output caching across calls.

[Sources](../../results/v56/experiments/piece-phases/sources.sha256),
[host equivalence](../../results/v56/experiments/piece-phases/metadata_check.txt).
