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

Job **1585771**, cn20481, started **08:16:21**. Four settings each receive the full signed
state sweep and guard cases: **1,044** state plus **896** guard cases planned.
Four-treatment Williams orders put each setting in each process position once
and cover every ordered adjacent treatment pair once. Four shapes, separate
DDR/HBM, four orders and five timings/process yield **640** timed hashes.
The parser verifies source hashes, requires the logged executable hash, and checks
all settings/positions, dimensions, completed rows and completion marker. Source/binary
identity does not eliminate normal execution noise or guarantee better caching.

No default, root source or release archive changes. A positive screen would
require an independent original-reference comparison before changing defaults.
HBM is still a separately reported extra placement, and no broad rules-compliance
or general memory-access proof is implied by these finite checks. No push.
