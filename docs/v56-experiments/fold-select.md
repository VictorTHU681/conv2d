# v56 experiment — select three-fold copier by grouping structure

The preceding fold/copy experiment improved k39 by up to 1.30% DDR / 1.43% HBM
but regressed k55 by 4.58% / 4.33%. This control separates the two group
structures without dispatching on exact public benchmark dimensions.

Baseline: accepted v56 `72b10c2:conv2d.c`, SHA-256
`472e4bcd213c538e3cc827c6476cee8a61a528f4bb4709d475e961c175339964`.
Published main was pulled and remains v55 `8ce8af2`; no push is performed.

## Controls

- `baseline`: accepted v56, automatic fold count and existing copiers.
- `nf3`: three-fold grouping for the seven-residual family, existing copiers.
- `selectcopy`: nf3 plus a COPY4 clone of the three-fold kernel, used only
  when `KH % 32 == 7`. Such plans have whole paired-16 groups and seven
  residuals; folding three fills the residual K4 group. Plans with an extra
  single-16 group retain the original copier.
- `select128`: same dispatch, plus the previously tested hoisted 128-byte
  inner-loop alignment in the new clone.

This applies to KH 39, 71, 103, 135, 167, 199 and 231 within the supported
rolling range. The condition excludes the different single-16-plus-residual
structure, not a particular benchmark shape. It is an empirical dispatch
hypothesis, not a claim of optimality for every member of the family.
Input/coefficients, FMA order, per-call packing and output semantics remain
the same. Cloning can change code placement even in unchanged kernels, so
all four official shapes are measured again.

## Validation protocol

Generator: `tools/gen_v56_fold_select.py`, which reuses
`tools/gen_v56_fold_copy.py`. Job: `jobs/v56_fold_select_job.sh`.
Job **1581858** completed successfully on cn20487, 2026-09-13.
Production and archives are unchanged; the selective aligned candidate proceeds
to an independent control combined with the first-copy boundary correction.

Each changed variant first runs 261 signed bitwise state cases. The two
selective variants additionally run 98 cases each over the complete KH
family above, odd/even KW through 400, output widths 257/513, and continuation
beyond eight KH periods with changed input and coefficients. Expected total:
783 state cases + 196 focused cases = 979 checks. Three alternating process
rounds, five timings per process, four shapes, DDR/HBM and four variants give
480 timed hashes. These are screening results relative to accepted v56,
not a replacement for the official v55-to-v56 comparison.

Evidence directory: `results/v56/experiments/fold-select/`.

```bash
python3 tools/gen_v56_fold_select.py
python3 tools/summarize_v54.py results/v56/experiments/fold-select/screen.log
```

## Completed screen

All **979 signed bitwise checks** and **480 timed hashes** pass. Median of
three process-median GFLOPS, each process containing five timings:

| Variant | DDR k39 | DDR k41 | DDR k55 | DDR k81 | HBM k39 | HBM k41 | HBM k55 | HBM k81 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| v56 GFLOPS | 13983.4 | 13511.8 | 14363.8 | 15431.1 | 14336.0 | 14142.0 | 14430.4 | 15415.0 |
| nf3 | -6.24% | +0.47% | -0.00% | -0.24% | +0.30% | +0.12% | -0.04% | -0.03% |
| selectcopy | -4.57% | +0.93% | -0.02% | -0.08% | +0.54% | -0.04% | +0.05% | +0.03% |
| select128 | +0.70% | +1.17% | -0.07% | +0.04% | +0.61% | -0.17% | -0.09% | -0.00% |

The selective aligned copier removes the previous approximately 4.5% k55
regression while retaining a smaller k39 gain in both memory modes. The DDR
k41 gain is not reproduced in HBM and does not correspond to an algorithmic
change in that shape; it is not promoted as a confirmed gain. The unaligned
three-fold controls remain vulnerable to substantial k39 DDR regressions.

**Decision:** advance only `select128` to further testing. This screen alone
does not change the accepted implementation or its v55-to-v56 performance
claim. A separately identified first-row overread must be corrected and
measured before promoting another candidate; see [first-copy.md](first-copy.md).

The follow-up combined screen (job 1581929) does not retain the k39 DDR gain
and has a small k55 HBM regression. Neither selective copier is promoted;
only the independent input-boundary correction proceeds to formal acceptance.
