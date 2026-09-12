# K5 scheduling cost from executed steps

Candidate experiment; accepted local v56 remains source 4689e38f / 4817eff.
No push. The [rebased K5 experiment](k5-layout.md) is still in official comparison.

The phase profile 1583390 finds that K5 reduces average KH 41 kernel-region
work but increases per-thread duration imbalance. In DDR the maximum-minus-mean
duration changes from 74.5 to 182.0 us; HBM changes from 31.5 to 85.0 us.
This is evidence of an additional tail cost, not proof of its cause.

The current plan estimates work using G->steps, which also describes padded R
packing. For KW 41 the K5 R table contains 45 positions, while the kernel executes
43 (KW+2). The cost therefore overcounts this part by 45/43-1 = 4.65% before
relative throughput weighting. The existing K4 family similarly executes KW+3,
which can be smaller than its four-position-rounded packing length. This affects
only how work is divided; it must not alter coefficient storage or execution.

`tools/gen_v56_k5_cost.py` creates four variants:

- baseline: immutable accepted 4817eff.
- triplet: rebased K5 4b35b3d5 from the matched-layout experiment.
- k5cost: same K5 source, but cost uses KW+2 for kind 5 only.
- tailcost: cost uses KW+2 for kind 5 and KW+3 for kind 4.

All weights keep existing defaults; there is no exact-public-shape tuning.
The kernel worker, output dependency/claim functions and group dispatcher are
byte-identical between the three K5 variants. New cost values may change work
piece boundaries, so output ownership gets fresh runtime checks.

Job **1583403**, cn20481, is running: 261 signed bitwise state cases per variant,
54 output ownership cases for each new cost variant, then a four-order Williams
design over four shapes and each allowed memory placement. Disassembly is saved
for code-layout verification. No speedup or correctness result is claimed yet.
