# Prepared phases with four-slice ZA transfers

Accepted root is now combined 1d3f5071…871a, local v56. No push. The comparison baseline is 8b6b295 / bb82ce3b…6819. Previous metadata
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

Original-benchmark job **1584136**, cn20483 06:01:14–06:12:29, succeeded.
All six permutations, five timings per process, four shapes and separate DDR/HBM
produce **144 full-reference PASS checks, maximum error zero**. Combined/base
median GFLOPS changes for KH39/41/55/81 are DDR +0.12%/+0.27%/-0.04%/-0.10%
and HBM +0.01%/+0.56%/-0.02%/-0.08%.
[Full summary](../../results/v56/experiments/piece-carry/official_summary.md)
also retains within-round ratios. HBM KH39 ranges -6.95% to +0.50%; HBM KH41
ranges -0.01% to +9.03%. No samples are discarded and these ranges are not
confidence intervals. The modest point estimates warrant independent confirmation.

Candidate archive job **1584311**, cn20483 06:14:59–06:17:08, succeeded:
all three archives pass four original full-reference checks each, maximum error
zero. The candidate hashes are in `packages_candidate.sha256`; this does not
replace the accepted root package manifest or establish diagnostic-package
compliance. Job **1584312**, cn20481 06:14:59–06:22:32, succeeded. Six alternating AB/BA
rounds, five timings per process, four shapes and separate DDR/HBM produce
**96 full-reference PASS checks, maximum error zero**.
[Independent confirmation](../../results/v56/experiments/piece-carry/confirm_summary.md):

| KH | DDR combined/base | HBM combined/base |
| --- | ---: | ---: |
| 39 | +0.06% | -0.24% |
| 41 | +0.83% | +0.55% |
| 55 | -0.02% | -0.05% |
| 81 | +0.01% | -0.13% |

KH41 DDR improves in all six paired rounds (+0.34% to +1.41%). HBM KH39
regresses in all six, so adoption does not claim universal benefit. Combined is
adopted for the saved problem's DDR objective after consistent KH41 benefit in
screening, the original three-way comparison and this independent confirmation.
All raw observations remain, including outliers and regressions.

Root source now matches tested combined SHA-256
`1d3f5071d51cd4f8c88720b8d4fa91983515ffd83bdeb4983377a991df2b871a`.
Regenerated release archives are checked against tested candidate program members;
only README changes. Existing published-v55 measurements belong to the previous
bb82ce3b checkpoint and must not be compounded with these percentages. A fresh
published-v55 comparison for this source is separate work.

Fresh published-v55 comparison submitted as **1584490**, cn20483,
`jobs/v56_piece_v55_job.sh`; immutable snapshots are staged under
`build/v56/experiments/piece-v55`. The original benchmark and six AB/BA rounds
are retained. Log: `results/v56/experiments/piece-v55/official.log`.
This job is pending and no new direct-v55 net result is claimed yet.
Main worktree pull on this checkpoint was already up to date at 364b46d.
Private SSH root operator and all three archives match the local accepted hashes.
