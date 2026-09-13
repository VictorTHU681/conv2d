# Upstream folded coefficient sharing over local v56

Candidate only: the accepted root is still 4817eff / source
`4689e38fbabc93a453541052b2260d9092473d0d2552311ddbb9126118015319`.
The main checkout pulled upstream CJ 4507658 and 76ec03d, whose historical
v58 filenames remain upstream provenance. This branch remains local v56;
no push or new publication has occurred.

`tools/gen_v56_kf_share.py` merges immutable baseline 4817eff, common 87fa5d7
and upstream 76ec03d, producing
`e05df5a10a1197aa661ae11b6c040ac18e1ce590e80c8cb8842b78842c0dc304`.
Source merge has no conflict. The first-copy functions, unique chunk packer,
output dependency builder and entire roll_worker remain byte-identical to
baseline. The claim function adds the shared kf owner's release/acquire gate.
K9 weight becomes configurable but retains its prior default 140.

The table depends on the current call's kernel and kind/steps, not the folded
row's starting residue. Only matching groups share, and only the selected owner
writes; consumers check both R and kf owner completion before using the tables.
Every invocation still rebuilds from that invocation's kernel. This is within-call
sharing, not content caching across calls or reuse of benchmark answers.

## Targeted evidence

The acceptance job **1583288**, cn20481, 03:57:53–04:05:22, succeeded:

- 288 preparation/packing cases over 12 heights, six widths (including 63/64/65),
  changed kernel values and serial reverse-order / seven-thread dynamic packing.
  144 shared-group occurrences, 23,184 nonowner row requests leaving poisoned
  shared tables untouched, and 26,023,296 table values checked against direct
  kernel indexing. The test calls actual merged preparation/packing functions.
- Actual claim function blocks a consumer when only its kf owner is unfinished,
  then admits it once the owner is published. This isolates kf ownership from
  R ownership in a synthetic plan; it does not claim to observe every hardware
  interleaving. The deliberately removed-gate control detects premature admission.
- 1,305 signed bitwise state cases across five packing modes, 272 guard cases,
  and 54 runtime output-ownership cases (7,861 kernel calls, zero active conflicts).
- Host extracted scheduler: 21,802 plans, 656,969 dependency edges,
  5,848,227 claims and 771,692 resumes. Existing output guarantees survive.

Official four-round alternating comparison against 4817eff completes all 64
original-reference checks with maximum error zero. Each process times five calls;
the median of four process-average GFLOPS gives:

| KH | DDR change | HBM change |
| --- | ---: | ---: |
| 39 | +0.02% | +0.14% |
| 41 | -0.12% | -0.05% |
| 55 | -0.25% | -0.39% |
| 81 | -0.18% | -0.21% |

**Do not adopt this candidate now.** It does not reproduce upstream's reported
KH 81 gains on the corrected local source. Preserve the complete result; do not
substitute profile timing or sum upstream/historical percentages.
Archive job **1583299**, cn20483, 04:00:22–04:02:40, succeeded: all three
archives and 12 complete original-reference checks pass with zero maximum error.
Archive hashes match the staged manifest. Candidate archives are
isolated under build/v56/experiments/kf-share/package; root packages are unchanged.

## Phase profile

**1583294**, cn20483, 03:59:26–04:00:05, succeeds: 24 processes, 168 calls and
120 timed output hashes. Six alternating rounds per memory placement, five timed
calls per process. Exclude validation/warmup calls and convert ticks with CNTFRQ.
The reused profiler retains historical K5_PHASE/K5_COST record names; this job
contains baseline and merged F4/K9 implementations, not the rejected K5 kernel.

| Memory | Variant | Prepare us | Worker phase us | Mean pack us | Max pack us | Main ns/tile | K9 ns/tile |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DDR | baseline | 14.740 | 22305.320 | 3.692 | 103.785 | 1.348657 | 1.505621 |
| DDR | merged | 11.310 | 22293.555 | 2.939 | 95.555 | 1.349287 | 1.492633 |
| HBM | baseline | 14.755 | 22297.135 | 3.646 | 103.850 | 1.349813 | 1.494838 |
| HBM | merged | 11.440 | 22314.635 | 2.998 | 95.650 | 1.349545 | 1.497209 |

These are medians of six process medians, not official throughput results.
The per-call kf payload is 209,952 -> 104,976 bytes, with unique R payload
unchanged at 844,992 bytes. Counts describe logical table writes; they are not
PMU-measured cache traffic, physical DRAM traffic, or total allocation sizes.
No assumption that a halved table doubles operator speed is justified.

Main-group mean region time remains about 19.29 ms per worker, versus roughly
2.72–2.75 ms for K9: approximately 88% of kernel time is still in main F4 groups.
The roughly 8 us reduction in maximum packing time is small beside 22.3 ms of
worker wall time, and packing can overlap computation. Preparation also measures
3 us lower, but this experiment alone cannot attribute that difference to a
particular source operation or exclude layout effects. The profiled wall-time
change is small and inconsistent between DDR/HBM; the completed official
comparison above likewise provides no measured gain supporting adoption.

All logs, source hashes and strict summaries live under
`results/v56/experiments/kf-share/`. Profiling controls and source generators are
reproducible; extending the profiler preserves previous default K5 source hashes.

## Instruction placement and same-executable control

Both official binaries contain three identical 21-word F4 steps. Short, overlap
and long-pure loops retain mod128 positions 120, 32 and 0 respectively; all three
merged addresses move by +128 bytes. This rules out a change in those arithmetic
words and mod128 placements, not all binary-layout effects or cache interactions.
There is no evidence here that the regression is caused by alignment.

`toggle.c` is an isolated source adding CONV_KF_SHARE to enable/disable sharing
within the same executable. Both settings pay the environment read and branch;
it is a diagnostic comparison and not an adopted production knob. Job **1583338**,
cn20481, 04:08:24–04:09:37, succeeds with 522 signed bitwise state cases and
360 timed output hashes. Six alternating pairs per shape and memory give:

| KH | DDR sharing on/off | HBM sharing on/off |
| --- | ---: | ---: |
| 39 | -0.05% | -0.12% |
| 55 | +0.01% | +0.04% |
| 81 | +0.17% | -0.13% |

This also fails to establish a consistent KH 81 improvement across placements.
Do not adopt the sharing change or attribute the prior negative result solely
to differing binary layout. The diagnostic source hash is recorded separately.
The aim is to distinguish a benefit of table sharing from differences between
compiled binaries. It does not eliminate memory placement or run-to-run noise.
