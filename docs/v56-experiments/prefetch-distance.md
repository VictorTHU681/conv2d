# Recheck prefetch distance after K5 and short-chunk adoption

Accepted source is **3df5c69 / ebf36923**, unchanged. Prior parameter scans
(`jobs/v55_diag_sweep_job.sh`) covered distances 2/6 before the ordinary K5
implementation, K5-specific short chunks and four-slice carry changes. Their
results should not be assumed to select the best distance for the current
stream/chunk pattern. The recent instruction-order and phase-register controls
did not show broad gains; this control returns to data supply using the current
source and identical machine code in every treatment.

`tools/stage_v56_prefetch.py` exports immutable current source and the hash-checking
fbench driver. One executable is compiled once. Each process selects existing
`CONV_ROLL_PD` values 1, 2, 3 or 6; explicit 3 is the accepted default control.
The knob feeds input-prefetch byte advance, output-prefetch byte advance, and
the existing output-prefetch timing condition. Thus this is a joint prefetch
distance control, not an isolated proof about input reads alone. Kernel math,
coefficient packing, chunk-size selection and instruction layout are unchanged.
The rejected arithmetic/phase-register candidate sources are not used.

Job **1585771**, cn20481, **08:16:21–08:20:20**, succeeds. Four settings each receive the full signed
state sweep and guard cases: all **1,044** state plus **896** guard cases pass.
Four-treatment Williams orders put each setting in each process position once
and cover every ordered adjacent treatment pair once. Four shapes, separate
DDR/HBM, four orders and five timings/process yield **640** passing timed hashes.
The parser verifies source hashes, requires the logged executable hash, and checks
all settings/positions, dimensions, completed rows and completion marker. Source/binary
identity does not eliminate normal execution noise or guarantee better caching.

The downloaded post-run executable matches the hash logged before all settings;
[binary audit](../../results/v56/experiments/prefetch-distance/binary_audit.txt).
[Complete summary and paired ranges](../../results/v56/experiments/prefetch-distance/summary.md).

| Memory | KH | Distance 1 / 3 | Distance 2 / 3 | Distance 6 / 3 |
| --- | ---: | ---: | ---: | ---: |
| DDR | 39 | -22.18% | -1.84% | -0.33% |
| DDR | 41 | -33.96% | -3.25% | -3.08% |
| DDR | 55 | -34.39% | -5.09% | -0.51% |
| DDR | 81 | -29.91% | -0.19% | -3.08% |
| HBM | 39 | -19.85% | +0.01% | -0.17% |
| HBM | 41 | -32.24% | -0.63% | -3.43% |
| HBM | 55 | -32.19% | -2.71% | -0.74% |
| HBM | 81 | -28.24% | +0.23% | -2.97% |

**Default remains 3.** None of the alternatives improves broadly; distance1 is
negative in all four paired rounds for every shape/memory combination. The small
HBM81 distance2 gain coexists with DDR and other-shape regressions. Every outlier
is retained; observed paired ranges are not confidence intervals. This sweep
does not establish that 3 is globally optimal: distances 4/5 remain unmeasured
in this initial scan and are tested separately in [the middle-distance scan](prefetch-mid.md),
which completes as 1585891 and rejects both. Default3 remains among the tested 1–6.

Because this knob changes input and output hints together, the large distance1
loss is further isolated in [the split diagnostic](prefetch-split.md). A loss
caused by shortening the distance does not imply equivalent remaining speedup
at the already accepted distance3 setting.

No default, root source or release archive changes. A positive screen would
require an independent original-reference comparison before changing defaults.
HBM is still a separately reported extra placement, and no broad rules-compliance
or general memory-access proof is implied by these finite checks. No push.
