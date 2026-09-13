# K5-only short continuation selection

Unpublished local v56 experiment; baseline operator is 113d3d6 /
4b35b3d5af1d85c8d6cf2ddc54073c0ccc75467cdc185229e0bbd906b355f905.

Based on the measured worker imbalance, short2/short4 select default continuation
step 2/4 only when the prepared group list contains kind 5 (K5). Other plans
retain step 8. CONV_ROLL_STEP overrides remain unchanged. Selection uses actual
plan structure, not an exact public shape, call count or memory placement.
Preparation does not read g_roll_step; workers, packing and output dependencies
are byte-identical to the accepted implementation. Each call still rebuilds
coefficients and computes all outputs.

Job **1583561**, cn20481 04:45:52–04:48:37, passed 2,610 signed bitwise state
cases across five packing modes plus 108 default-step output-ownership cases
(4,137 kernel calls, zero observed active conflicts).

Job **1583562**, cn20483 04:46:05–04:57:18, passed all 144 full-reference checks
with zero maximum error. Six permutations, five timings per process; baseline
is 113d3d6, **not published v55**. Short2 improves KH41 DDR by **1.73%**;
HBM regresses **0.30%**. Other public shapes range -0.26% to +0.04%; their
selected continuation default stays 8, so those changes cannot be ascribed
to different chunk counts. Short4 gives +0.97% DDR / -0.17% HBM at KH41.
Do not combine these percentages with older v55-relative measurements.

[Full results](../../results/v56/experiments/k5-default/official_summary.md)
and [source hashes](../../results/v56/experiments/k5-default/sources.sha256).

Short2 is staged for package acceptance because the saved problem's original
placement is DDR. The HBM regression is retained explicitly; this is not an
improvement in both placements. Job **1583642** on cn20483 checks all three
candidate archives; it succeeded 04:58:31–05:00:38, with 12 full-reference checks and zero maximum error.
Short2 is now adopted as root source bb82ce3b4826514e9ce6f729ef017a23d5aa08d2396f5d0975a512e39da76819.
Current archives have identical program members to the tested archives; README is updated separately. Diagnostic archive
contains probes and remains diagnostic-only regardless of numerical PASS.
