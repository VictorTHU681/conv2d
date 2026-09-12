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

Thread-detail job **1583419**, submitted for cn20481, compares baseline 4817eff,
ordinary K5 and k5cost at KH 41. It records per-thread absolute-relative start/end
times, durations, packing time and main/tail work after workers have joined.
It is pending; detailed printing is diagnostic and cannot define production speed.
