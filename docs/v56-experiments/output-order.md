# v56 output write ordering candidates

These candidates address the [overlapping-writer finding](output-ownership.md).
The pipelined candidate is now adopted in the root source and packages after
acceptance. This remains local v56, with no push and no new version number.
Accepted SHA-256: `4393346986d6c0c71c7db9ecd804ed76c22839923f8ed963f07488854809d121`.
Immutable baseline is `54dc05d`, source `695c449c…3530b`.

## Changes and ordering argument

`roll_prepare` keeps its existing strip bases and row partition. A new pass
links each final-strip piece to the pieces of the immediately preceding strip
that intersect its output rows. Only the clamped final strip can overlap an
earlier strip; all full strips are disjoint. The pieces are sorted by item and
row, so the dependency range is contiguous and points to smaller item indices.
Groups retain their existing disjoint output-row residues.

The **ordered** candidate (`163ccdf0…77458a`) waits for complete predecessor
pieces using acquire loads of their completion flags. No dependency is added
for disjoint output rectangles. This corrects the race but can delay a large
final strip until a long predecessor piece completes.

The **pipelined** candidate (`43933469…09d121`) instead checks each chunk's
actual output-row interval. It waits only until each predecessor has published
completion through the last overlapping output row. The low bits of a busy
ready flag are the prefix completed before the current claim, not speculative
progress. An acquire read of that flag observes the preceding release through
the intervening compare-exchange RMW release sequence. A later predecessor
chunk writes only later rows, so the two workers can safely remain active.
Every dependency still points to an earlier item; the graph has no cycles.

Both candidates change `kp_t.out_row0` to an integer address. Constructing the
warmup cursor uses unsigned address arithmetic; it no longer forms a C pointer
before the output allocation. The existing assembly selects scratch during
warmup. Kernel FP32 instruction strings, coefficient rebuilds, input-copy
boundaries and the official benchmark/build command remain unchanged.

## Validation and current status

- The extracted **ordered** builder/claim functions pass an ASan/UBSan host
  simulation with 1,990 plans, 47,350 dependency edges, 1,002,725 claims and
  538,115 resumed claims. This checks rectangle ownership and progress, not SME.
- The **pipelined** host simulation covers chunk factors 1/2/4/8/16/32/64 and
  passes 13,906 plans, 331,133 edges, 3,691,095 claims and 479,656 resumes.
  All supported kernel heights, narrow-width fallback conditions, boundaries
  around strip widths, unequal row partitions and the four official shapes
  participate. Unsupported rolling shapes are skipped explicitly.
- Runtime diagnostic **1582889**, cn20481, 02:54:22–02:56:03, succeeds. Each
  variant runs 54 signed bitwise cases and 7,861 actual kernel calls. Baseline
  reports 67 overlapping active output regions; **ordered** reports zero.
  The metadata lock does not cover kernel execution. This checks potentially
  conflicting active regions, not the exact instant of individual stores;
  instrumentation can alter scheduling and is excluded from performance runs.
- **1582878**, cn20483, 02:52:45–02:59:34, succeeds for ordered: 1,305 state
  cases across five packing modes, 224 guards and 64 full-reference official
  checks with zero maximum errors. All four rounds completed in each memory mode.
- **1582930**, cn20481, 02:58:29–03:05:32, succeeds for pipelined: 1,305 state
  cases, 224 guards, 54 signed bitwise runtime overlap checks (7,861 kernel calls,
  zero active conflicts) and 64 official complete-reference checks, errors zero.
- **1582948**, cn20481, 03:05:40–03:07:44, succeeds with all 12 complete checks
  across the normal, three-chain control and diagnostic archives. Its pending
  node preference was changed from cn20483 to cn20481 with `dmod`; the same job
  was retained. Current archives update README only; program members match the
  tested archives byte-for-byte. The diagnostic archive remains diagnostic-only.

The completed **ordered** comparison below explains why it will not replace
the current source. Waiting for complete pieces extends the final critical
path, especially on KH 81. Each entry is a median of four process-average
GFLOPS values, with five timed calls per process and alternating process order.

| KH=KW | DDR change | HBM change |
| --- | ---: | ---: |
| 39 | -3.42% | -0.59% |
| 41 | -2.56% | -0.44% |
| 55 | +0.07% | +0.16% |
| 81 | -9.11% | -9.00% |

Full values: `results/v56/experiments/output-order/summary.md`.

The adopted **pipelined** comparison is a separate same-node job against the
same immutable baseline; do not subtract measurements from different nodes.

| KH=KW | DDR change | HBM change |
| --- | ---: | ---: |
| 39 | -0.25% | -0.31% |
| 41 | -0.25% | -0.02% |
| 55 | -0.09% | -0.18% |
| 81 | -0.24% | -0.18% |

The small measured cost is retained to correct the output race. It is not
reported as a gain or assumed to be zero merely because the percentages are
small. Full values: `results/v56/experiments/output-order/pipeline_summary.md`.

Reproduction: `gen_v56_output_order.py`, `test_v56_output_order.py` (add
`--pipeline` for chunked ownership), `gen_v56_output_overlap_audit.py`, the
output-order/pipeline jobs, and `summarize_v56_output_order.py`. Raw evidence is
under `results/v56/experiments/output-order/`. The standalone instrumented
sources are diagnostic-only and never included in the submission candidates.
