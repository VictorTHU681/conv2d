# Isolated upstream K4 EXT and K9 alignment review

Main checkout pulled upstream **364b46d**; local v56 does not blindly merge it
or the preceding 76ec03d coefficient-sharing change. Root accepted source is
113d3d6 / 4b35b3d5…f905, with all local bounds and output-order fixes retained.

Generator tools/gen_v56_k4_ext.py isolates four candidates: baseline, K4 EXT
register windows, K9 loop alignment, and both. K4's C setup and bounded copy
prefix are unchanged. K9's aligned loop entry is placed **after** the local
four even-vector preload instructions; placing the branch before them would
skip the preloads. Worker, packing, preparation, output dependencies and K5
functions remain byte-identical. Every call still packs current coefficients.

The K4 candidate retains four input vectors per plane and advances each window
with EXT plus one boundary vector load. Upstream's claim that EXT is free is
not established by these tests. A mathematical audit covers 25,472 KW / input
alignment / column-class combinations and checks initial and last window load
ends against each padded plane. This does not prove that all unused lanes are
excluded from valid outputs. Additional baseline/K4 EXT diagnostic variants
fill internal rings with NaN bytes before execution to expose consumption of
uninitialized padding; these are never used for performance measurements.

Job **1583597**, cn20481, succeeded 04:51:24–04:59:24. All checks passed: six variants (including
two poison controls) times 261 state + 272 guard cases, 54 runtime ownership
cases for the combined candidate, and four Williams-order screening rounds
across four shapes / allowed placements / five timings. The screening driver
is an immutable 113d3d6 export, with FBENCH_FORCE explicitly unset.

[Source hashes](../../results/v56/experiments/k4-ext/sources.sha256),
[bounds](../../results/v56/experiments/k4-ext/bounds.txt).
No root operator or package change; no push.

## Screening result: not adopted

All 3,198 state/guard cases, including both NaN-ring controls, pass. The combined
candidate passes 54 ownership cases with zero observed active conflicts, and
all 640 timed hashes pass. These are finite checks, not proof of every
assembly access or legal shape.

[Balanced screening results](../../results/v56/experiments/k4-ext/summary.md)
show K4 EXT at KH39 +0.46% DDR / -0.00% HBM, but KH55 -0.41% / -0.23%.
K9 alignment alone does not help KH81 (-0.02% DDR / -0.16% HBM). The combined
candidate regresses KH55 -0.43% / -0.29%. KH41's K4-only DDR +0.69% cannot be
attributed to executing K4: its accepted plan uses F4+K5. This is a warning
about code-layout or timing effects, not evidence that K4 arithmetic speeds
that shape. No consistent benefit sufficient to adopt either change has been
established. No merged official acceptance or package adoption is claimed.
