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

Job **1584148**, cn20481, started 06:02:50 and is running. The new interleaved
candidate receives five packing-mode state sweeps, plain/NaN-ring guard checks,
NaN-ring state checks and runtime output-ownership checks: planned 2,014
state/guard cases plus 54 ownership cases. All three variants get six balanced
permutations, four full shapes, allowed DDR/HBM and five timings per process
(720 timed hashes). No runtime/performance result or adoption yet claimed.
