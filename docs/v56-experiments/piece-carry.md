# Prepared phases with four-slice ZA transfers

Accepted root remains local 8b6b295 / bb82ce3b…6819. No push. Previous metadata
preparation reduces measured worker setup but increases the ZA-restore region
and regresses uninstrumented KH41/55. This matched control tests its interaction
with the separately tested four-slice carry loops.

Four variants: baseline, cached metadata, carry4, combined. Combined differs
from cached only in carry_store_za/carry_load_za, copied exactly from the tested
carry4 control. Worker, preparation, claims and output dependencies remain
byte-identical to cached. No arithmetic, per-call coefficient rebuilding, input
bounds, publication ordering or piece-layout changes beyond those two isolated
components. Previous host metadata equivalence remains applicable; no input,
coefficient or result cache is introduced.

Job **1584060**, cn20481 05:55:48–05:59:24, succeeded. Combined passes 1,305
five-mode signed state cases, 224 guards and 54 runtime output-ownership cases
with zero observed active conflicts. All four variants pass 640 timed hashes
in four balanced Williams orders. [Screen](../../results/v56/experiments/piece-carry/summary.md):
combined/base KH41 is +0.34% DDR / +0.27% HBM; KH39 -0.03% / +0.11%, KH55
+0.10% / -0.11%, KH81 +0.25% / +0.04%. The mixed costs do not combine linearly;
these modest screening gains do not establish an accepted improvement.

Original-benchmark job **1584136**, cn20483, started 06:01:14 and compares baseline/carry4/
combined in all six permutations, five timings per process, four shapes and
permitted DDR/HBM. Planned 144 full-reference checks. It is running;
no original-benchmark or package acceptance yet claimed. Root operator remains
unchanged. The published-v55 checkpoint still refers to accepted bb82ce3b.
