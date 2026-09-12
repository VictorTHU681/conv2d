# K5 scheduling cost from executed steps

Rejected cost controls over the K5 experiment; ordinary K5 source 4b35b3d5
is now accepted after [official and archive validation](k5-layout.md).
The cost experiment baseline remains immutable 4817eff. No push.

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

Job **1583403**, cn20481, 04:24:19–04:27:43, succeeded: 1,044 signed
bitwise state cases, 108 runtime output-ownership cases with zero active conflicts,
and 640 timed output hashes. Four Williams-design orders balance process position
and immediate predecessor, with separate DDR/HBM comparisons.

The result rejects these cost changes for adoption. Against ordinary K5,
k5cost changes KH 41 by -0.42% DDR / -0.60% HBM; tailcost changes it by
-0.40% / -0.62%. Tailcost additionally regresses KH 39 by 1.12% DDR and
1.41% HBM. The mathematically smaller step count does not produce a better
end-to-end schedule under the existing empirical weights and chunking scheme.
Do not claim the padded-step discrepancy caused the observed imbalance.

The three K5 variants' entire k5 and roll_worker functions have identical
instruction addresses and words in these binaries, not just identical F4
arithmetic bodies. Cost changes still alter host planning and piece boundaries,
and other code/data layout or noise remain possible influences. Full results
and machine-code checks are in results/v56/experiments/k5-cost/.

Ordinary K5's independent original-benchmark and archive comparisons are complete;
it is adopted with the original scheduling costs.
Further scheduling investigation should identify the longest-duration workers'
actual main/tail workloads before changing weights again.

Thread-detail job **1583419**, cn20481, 04:34:26–04:35:11, succeeded: 36
processes, 9,576 thread records and 180 timed output hashes. Thread step totals
match aggregate kernel counts. Records use the first worker start as a common
origin, allowing absolute-relative end-time comparisons instead of durations only.
Printing happens after join and can perturb the benchmark; reported GFLOPS is
not production performance evidence.

For ordinary K5 the last worker is tail-majority in only 3/30 timed calls in
each memory placement. Its median last-worker main/tail region times are
5,964/0 us DDR and 5,751/0 us HBM. Thus the usual last worker is main-F4-heavy,
not K5-tail-heavy. Its last-end-minus-mean-end gap is about 199 us DDR / 85 us HBM.
The rejected k5cost shifts the DDR critical worker to tail-majority in 20/30
calls, but the HBM last worker remains usually main-heavy. This complicates a
single throughput-ratio explanation and does not overturn the negative ordinary
screening result. Full per-memory values are in thread_summary.md.

Next compare continuation chunk lengths in the same uninstrumented executable,
using the existing CONV_ROLL_STEP knob. This tests whether remaining main-group
work can be distributed with less end-of-call delay, balanced against additional
carry saves/restores. It does not assume that a K5 kernel instruction is solely
responsible for the critical path. See [chunk controls](k5-chunks.md).
