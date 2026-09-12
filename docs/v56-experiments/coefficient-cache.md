# v56 experiment — coefficient load cache policy

Part of the unpublished v56 work; the coefficient-packing experiment found no stable throughput gain.
Baseline source: `72b10c2:conv2d.c`, SHA-256
`472e4bcd213c538e3cc827c6476cee8a61a528f4bb4709d475e961c175339964`.

## Hypothesis

Rolling kernels stream packed matrix coefficients while reusing small input
rings inside KW loops. A streaming load hint might reduce L1 pollution, or
might lose useful coefficient cache hits. v55 tested non-temporal source-copy
loads; it did not change these matrix-coefficient loads. This experiment uses
scalar-base contiguous LDNT1W, retaining original addresses and predicates.
It does not change table contents, arithmetic, output ordering or allocation.

## Scope correction and isolated controls

Job **1581486** uses the initial generator, now retained as
`tools/gen_v56_coeff_cache_mixed.py`. Its register-prefix matcher also matched x21/x25,
so only `ntwide` (10 load sites in 16-row pair/single kernels) is a pure
coefficient control. `ntres` (19 sites) and `ntall` (29 sites) include some
residual input loads and are recorded as mixed-load controls. These results
must not be attributed solely to coefficient caching. Existing files and the
live job were preserved; no running source was replaced.

Corrected `tools/gen_v56_coeff_cache.py` requires a delimiter after x2/x3 and asserts the
changed base registers. It writes a separate `build/v56/experiments/coefficient-cache/coeff/` directory:
`coefres` changes exactly 7 coefficient load sites in K8/K9/K4; `coefall`
changes exactly 17 coefficient load sites across all rolling kernels.
Job **1581489** compares these sources against exact v56. Generalized state
checks precede three alternating performance rounds per shape and placement.
Each process has five hash-checked timings. These are screening controls,
not accepted production changes.

Neither experiment changes the production source, benchmark, compile command,
run scripts or submission archives.

## Cache counter diagnostic

After state checks passed, job **1581513** was submitted to compare v56 and
`coefall` using the existing steady-allocation PMU driver. It makes 200 repeated
calls per process, two alternating rounds for k39/k81 in DDR/HBM. This avoids
per-call allocation/copy overhead for diagnosis and is not the official timing
protocol. Counters cover the whole process, including initialization, warmups
and worker waiting. They cannot isolate coefficient loads or establish a
causal cache-pollution explanation. Streaming loads can also change which
cache events are counted; fewer misses alone is not proof of faster execution.
Actual elapsed time and the independent hash-checked screen decide adoption.


## Completed screening

Both performance jobs SUCCEEDED on 2026-09-13. Job **1581486**, cn20481,
00:01:56–00:04:14, passes **783 state cases and 480 timed hashes**.
The pure wide-kernel coefficient control changes DDR k39/k41/k55/k81 by
-0.06/+0.18/-0.24/-0.29%; HBM by -0.39/+0.01/-0.32/-0.56%.
The mixed controls regress k81 about 1.34–1.68% and k55 by up to 2.01%.
These mixed results do not isolate coefficient behavior.

Job **1581489**, cn20484, 00:02:54–00:04:28, passes **522 state cases and
360 timed hashes**. Corrected coefficient-only results, three alternating
process rounds with five timings each:

| Variant | DDR k39 | DDR k41 | DDR k55 | DDR k81 | HBM k39 | HBM k41 | HBM k55 | HBM k81 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| v56 GFLOPS | 13962.7 | 13345.8 | 14368.9 | 15445.7 | 14348.0 | 14146.4 | 14428.8 | 15404.2 |
| coefres | -0.14% | -0.65% | -1.83% | -0.70% | -0.14% | -0.16% | -0.64% | -0.53% |
| coefall | -0.37% | -0.41% | -2.01% | -1.16% | -0.20% | -0.14% | -0.80% | -0.76% |

All corrected controls regress in this run. They are rejected for production;
retain ordinary coefficient LD1W and the validated v56 source. PMU job
1581513 provides the separate cache-counter measurements below.

## Completed PMU diagnostic and decision

Job **1581513** SUCCEEDED on cn20485, 2026-09-13 00:04:10–00:06:32.
All four events report 100% running time for all 16 processes. The following
values average the two alternating process repetitions. Timings use the
steady-allocation workload, not the official timing protocol:

| Shape / memory | v56 ms | coefall ms | Time change | L1 load-miss count change |
| --- | ---: | ---: | ---: | ---: |
| k39 DDR | 5.3872 | 5.4410 | +1.00% | -3.64% |
| k81 DDR | 22.4434 | 22.7214 | +1.24% | -2.64% |
| k39 HBM | 5.2854 | 5.2682 | -0.33% | +1.33% |
| k81 HBM | 22.4628 | 22.6393 | +0.79% | -3.42% |

For k81, miss counts decrease while runtime increases in both memory modes.
This does not prove a specific hardware mechanism, but rules out treating
lower generic L1-miss counts as an optimization success. The small k39 HBM
steady-workload gain does not reproduce the independent allocation/copy-based
screen, where coefall regressed every shape and placement. Raw evidence is
in `results/v56/experiments/coefficient-cache/pmu.log`; the counter summary is `pmu_summary.txt`.

**Decision:** reject all coefficient-cache controls and retain the original LD1W coefficient
loads. No production change or push. The round contributes **1,305 state
checks and 840 timed hash checks**, plus the separate PMU evidence. All three
jobs are terminal. The baseline remains accepted local v56.

Reproduce the historical mixed controls and corrected sources separately:

```bash
python3 tools/gen_v56_coeff_cache_mixed.py > results/v56/experiments/coefficient-cache/sources.sha256
python3 tools/gen_v56_coeff_cache.py > results/v56/experiments/coefficient-cache/coeff_sources.sha256
python3 tools/summarize_v54.py results/v56/experiments/coefficient-cache/coeff.log
python3 tools/summarize_v54.py results/v56/experiments/coefficient-cache/exact_coeff.log
```
