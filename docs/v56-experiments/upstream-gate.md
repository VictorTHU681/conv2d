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

**1583171**, cn20481, 03:37:51–03:46:08, succeeds with 1,305 state cases across
five packing modes, 272 guards including KW 63/64/65, 54 runtime ownership
checks (7,861 kernel calls, zero active conflicts), and 64 complete original
benchmark checks with zero maximum errors. Four alternating rounds use five
timings per process; values below compare median process-average GFLOPS.

| KH=KW | DDR change | HBM change |
| --- | ---: | ---: |
| 39 | +0.03% | -0.21% |
| 41 | -0.33% | -0.12% |
| 55 | +0.46% | +0.57% |
| 81 | +0.70% | +0.09% |

These compare against local 43933469, not published v55. In particular, the
HBM KH 81 result does not reproduce upstream's reported approximately 0.9%
gain. Do not replace the measured result or combine percentages from unrelated
baselines. Raw log and strict summary are under `results/v56/experiments/upstream-gate/`.

**1583190**, cn20483, 03:41:16–03:44:35, validates all three staged archives:
12 complete checks pass. The actual Git merge and root package update follow
this accepted source/package evidence; staged source SHA remains 4689e38f.

Machine-code inspection finds identical 21-word F4 arithmetic steps (5 loads,
4 FMOPA, 8 FMLA, 4 pointer increments). It does **not** establish an unchanged
entire short path: the baseline short loop starts at mod128=0, while the merged
short loop starts at mod128=120. The merged overlap step starts at mod128=32
and its long pure loop at mod128=0. See `machine_code.txt` and instruction excerpts.
An isolated `short128` control restores two NOPs before the short row loop;
**1583215** runs all six process permutations against baseline and merged. It
is still pending completion and is not part of the accepted source.

Upstream also adds `FBENCH_FORCE` to its diagnostic fbench, permitting timing
after an initial validation failure for attribution experiments. This is not
an official benchmark change or evidence of a correct candidate. Our acceptance
job explicitly unsets that variable and uses the unchanged official benchmark
for performance comparisons. Incorrect-result attribution controls and their
numbers cannot be treated as eligible optimized implementations.

Complete this integration before continuing K5 F4 layout controls, since it
changes precisely the main kernel under investigation. Do not adopt short128
without its own measured benefit and relevant validation.
