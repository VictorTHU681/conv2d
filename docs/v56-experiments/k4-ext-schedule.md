# K4 EXT window-advance scheduling

Accepted root remains 8b6b295 / bb82ce3b…6819. No push.
The [register-only probe](ext-throughput.md) finds no extra matrix throughput
cost for four/eight EXT per four FMOPA. It cannot account for real loads or
copies; the previously rejected EXT implementation remains unadopted.

Generator rebases only the validated bounded K4 EXT macros/function onto the
accepted K5-short-chunk source. K9 alignment and upstream coefficient sharing
are excluded. Three variants: accepted baseline, blocked EXT, interleaved EXT.

Blocked does four plane FMOPA groups followed by four window advances. Interleaved
does each plane's FMOPA then its boundary load and four EXT before the next
plane's FMOPA. Both copy-overlap and pure loops change, while the final partial
iteration remains unchanged. The FMOPA order and count are identical, as are
all addresses and pointer increments. No copy prefix, group, worker, claim,
preparation or output-dependency function changes. The bounded per-plane padding
from the earlier EXT audit is retained.

Job **1584148**, cn20481 06:02:50–06:07:07, succeeded. The interleaved
candidate passes five-mode state, plain/NaN-ring guards, NaN-ring state and
runtime output ownership: 2,014 state/guard cases and 54 ownership cases,
zero observed active conflicts. All three variants pass 720 timed hashes in
six permutations, four shapes and both placements.

[Results](../../results/v56/experiments/k4-ext-schedule/summary.md): interleaved
versus blocked recovers KH55 +0.07% DDR / +0.17% HBM, but versus accepted
baseline remains **-0.39% / -0.15%**. Other interleaved/base changes range
-0.47% to +0.12%, including changes in shapes without K4 execution. The blocked
rebased EXT control also regresses KH55 -0.46% / -0.32%. Neither is adopted.

The synthetic matrix/EXT overlap budget does not guarantee a real kernel gain.
Moving boundary loads earlier is insufficient here; whole-worker compiler
layout, loads, copies and output handling remain possible influences. No
single physical bottleneck or complete causal explanation is established by
these timings. Root accepted source and packages remain unchanged.
