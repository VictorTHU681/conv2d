# Incoming upstream F4 long-row gate: integration candidate

The main checkout pulled **87fa5d7** from origin, following **7e9f3b6**. Both
are upstream CJ commits, not publications from this local optimization branch.
Their historical v57 filenames are retained as upstream provenance. This
branch remains unpublished local v56; no push has occurred.

The principal operator change adds a per-call gate to `k16pairf4`. Short rows
retain the serial COPY4 path; long rows (steps at least 64) interleave row-copy
work with arithmetic and branch over the 128-byte alignment padding. Event
handling is extracted into a shared macro instantiated in both paths. Upstream
performance reports are motivation to test, not evidence of gains on our
locally corrected source.

`tools/gen_v56_upstream_gate.py` merges immutable sources using common ancestor
`b9591de`. The merge is conflict-free at the source-file level:

| Role | Revision | Source SHA-256 |
| --- | --- | --- |
| Local accepted | 68f0276 | 4393346986d6c0c71c7db9ecd804ed76c22839923f8ed963f07488854809d121 |
| Common | b9591de | 756e11735fc63918ed0c853bb23193a6342c1a232fd9c5479b43878ec4954831 |
| Upstream | 87fa5d7 | c83cc95173ab93542cbda27f5b6dccb5552662c263a5152d0dbbc9ba5ed1dc84 |
| Merged candidate | Not adopted | 4689e38fbabc93a453541052b2260d9092473d0d2552311ddbb9126118015319 |

The generator requires the local first-copy helper, planar first-copy helper,
output dependency builder and claim function to survive byte-for-byte. The
earlier K9 reuse and K8/K9/K4 boundary corrections are retained; K5 experiments
are not included. This is an isolated source candidate, not a completed Git
merge or an adopted package.

**1583171** is submitted to cn20481 for five packing modes, 272 guard cases
(including KW 63/64/65), an instrumented output-ownership check, and four-round
original-benchmark comparisons against the accepted local source. Its terminal
log and archive acceptance are still required. No result is claimed yet.

Upstream also adds `FBENCH_FORCE` to its diagnostic fbench, permitting timing
after an initial validation failure for attribution experiments. This is not
an official benchmark change or evidence of a correct candidate. Our acceptance
job explicitly unsets that variable and uses the unchanged official benchmark
for performance comparisons. Incorrect-result attribution controls and their
numbers cannot be treated as eligible optimized implementations.

Review and validate this integration before continuing K5 F4 layout controls,
since it changes precisely the main kernel under investigation. Keep current
root source/packages at 43933469 until the candidate passes the required checks.
