# v56 experiment — fold count versus input copy

Completed v56 experiment; none of these controls is promoted to the default implementation.

Baseline is immutable 72b10c2:conv2d.c. The default k39 plan is 36+3; forcing
three folded rows gives 35+4 with the same matrix-step count. The latter fills
the K4 group's unused fourth residual and needs fewer vector FMLA instructions,
but its pairf3 uses ROW_HEAD_COMMON while pairf4 uses ROW_HEAD_COPY4.

Controls from tools/gen_v56_fold_copy.py:
- baseline: exact v56;
- nf3: existing three-chain compile-time control only;
- f3copy: nf3 plus COPY4 only in pairf3;
- f3copy128: f3copy plus hoisted 128-byte inner-loop alignment, using the same
  fixed macro-instruction counting technique validated for pairf4 in v55.

No arithmetic order or coefficient-caching rule changes. The copy macro's
registers are already clobbered by pairf3; its labels do not conflict with event labels.

## Completed measurements and decision

Job **1581686** SUCCEEDED on cn20482, 2026-09-13 00:19:13–00:22:05.
All three changed candidates pass 261 signed bitwise state cases each
(**783 checks**), and all **480 timed hashes** pass. Three alternating
process rounds, five timings per process; median of process-median GFLOPS.
This node runs around 1.2 GHz; use within-job ratios, not raw throughput
comparisons against the approximately 1.55-GHz nodes in other experiments.

| Variant | DDR k39 | DDR k41 | DDR k55 | DDR k81 | HBM k39 | HBM k41 | HBM k55 | HBM k81 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| v56 GFLOPS | 11175.4 | 10956.2 | 11236.2 | 12013.2 | 11186.7 | 11058.1 | 11234.2 | 12000.4 |
| nf3 | -0.15% | +0.01% | +0.01% | -0.10% | +0.71% | -0.28% | +0.06% | -0.05% |
| f3copy | +0.53% | +0.11% | -3.71% | +0.15% | +1.20% | -0.05% | -3.47% | +0.13% |
| f3copy128 | +1.30% | -0.02% | -4.58% | -0.20% | +1.43% | +0.01% | -4.33% | -0.08% |

**Decision:** reject these controls for the default implementation. COPY4
and alignment improve k39 but regress k55 substantially. The nf3-only control
does not provide a consistent gain across memory placements. No isolated
selective-dispatch combination has been measured, so its benefit is not claimed.
The existing `conv_nf3.zip` remains a comparison package, not the default.

Sources: `tools/gen_v56_fold_copy.py`; job: `jobs/v56_fold_copy_job.sh`.
Raw evidence: `results/v56/experiments/fold-copy/fold_copy.log` and
`sources.sha256` in the same directory. The raw log's V60 tag is a historical
experiment identifier, not a released version.

```bash
python3 tools/gen_v56_fold_copy.py
python3 tools/summarize_v54.py results/v56/experiments/fold-copy/fold_copy.log
```
