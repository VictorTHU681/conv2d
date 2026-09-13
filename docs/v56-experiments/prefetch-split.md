# Separate input and output prefetch lead

The accepted-source sweep 1585771 finds large distance1 losses but jointly
changes input/output prefetch. This diagnostic separates the two parameters.
Accepted root remains **3df5c69 / ebf36923**; the split source is not a proposed
release optimization or a replacement for the original benchmark.

`tools/gen_v56_prefetch_split.py` makes only five asserted replacements from the
immutable accepted source, then reverses them to require exact source equality.
Two configuration values are read once with existing `read_knobs`: input distance
feeds `A.pf`; output distance feeds both `A.pfo` and `A.PD`. The latter controls
the existing output-prefetch event condition. All assembly text, arithmetic,
coefficient rebuilding, scheduling, ownership and capacity repair stay unchanged.
Configuration caching stores no tensor contents or results. All four settings
use one executable: input/output 3/3, 1/3, 3/1 and 1/1. This binary differs from
accepted root and only within-binary comparisons are used for attribution.

## Completed phase attribution

Job **1585839**, cn20481, **08:22:56–08:23:50**, succeeds. **96** processes,
**25,536** worker records and **480** timed hashes validate. Four Williams orders,
three shapes, DDR/HBM, five timings per process; seven calls and all 38 threads
must be present. Work/table counts are invariant for each shape across settings,
thread step totals match aggregate buckets, and per-thread region times agree
with those buckets. Medians use timed calls 3–7 and then process medians.
[Complete phase summary](../../results/v56/experiments/prefetch-split/profile_summary.md).

DDR pair-region us/thread, input/output 3/3 → 1/3 versus 3/1:
- KH41: **4664.208 → 6829.239**, versus **4665.733**.
- KH55: **6590.298 → 9743.895**, versus **6587.793**.
- KH81: **19254.046 → 27733.670**, versus **19252.039**.

Other kernel regions also slow with input1. KH41's worker-end spread grows from
70.5 to 236.6 us under input1/output3; changing only output to1 gives 73.2 us.
HBM shows the same direction. Input1/output1 largely reproduces input1/output3.
This locates the observed distance1 degradation in the input-prefetch change,
not a comparably large output-prefetch effect. It does not prove a particular
cache level, physical stall event, memory bandwidth limit, or that the accepted
distance3 setting still loses this amount of time. Region timers include setup
and ZA restore, and instrumentation changes source/layout/scheduling.

## Completed uninstrumented factorial screen

Job **1585838**, cn20483, **08:22:56–08:28:03**, succeeds. Each setting runs 261
signed state and 224 guard cases: all **1,940** checks pass, followed by four
Williams orders on four shapes in DDR/HBM with five timings/process: all **640**
timed hashes pass.
The parser requires all source hashes, the logged one-binary hash, settings,
orders, dimensions, complete timing rows and completion marker before reporting.
No partial log is treated as completed screening, and no split setting is adopted.
[Full screen and paired ranges](../../results/v56/experiments/prefetch-split/summary.md).
Post-run downloaded screen/profile executables independently match their logged
pre-run hashes; [binary audit](../../results/v56/experiments/prefetch-split/binary_audit.txt).

| Memory | KH | Input1/output3 vs 3/3 | Input3/output1 vs 3/3 | Input1/output1 vs 3/3 |
| --- | ---: | ---: | ---: | ---: |
| DDR | 39 | -21.80% | -0.42% | -21.94% |
| DDR | 41 | -34.33% | +0.41% | -34.43% |
| DDR | 55 | -34.43% | -0.00% | -34.07% |
| DDR | 81 | -29.88% | -0.01% | -29.82% |
| HBM | 39 | -20.53% | +0.17% | -20.91% |
| HBM | 41 | -32.55% | +0.07% | -33.01% |
| HBM | 55 | -31.76% | -0.00% | -31.78% |
| HBM | 81 | -28.08% | -0.10% | -28.18% |

Input1 alone consistently reproduces the large joint-distance loss, including
every paired round. Output1 alone has small mixed effects; its DDR39 paired range
includes -3.33%, and all such outliers are retained. This corroborates the phase
attribution without making the diagnostic source a production candidate. The
output-only KH41 gain is not broad enough to adopt here. Normal default3 remains;
[distances 4/5](prefetch-mid.md) are separately checked around the accepted setting.
These data locate the cause of the induced short-lead loss, not a measured
22–34% recoverable deficit at the current default.

The source, driver, profile and logs have separate hashes. Original compile and
release files remain unchanged. HBM is separate from the saved problem's default
placement; fixed SVL/external concurrency/allocation-failure limitations remain.
No push.
