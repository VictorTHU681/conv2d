# K5 three-way folding: correct prototype, no stable speedup yet

The [design](k5-triplet-design.md) is implemented as an isolated experiment on
accepted commit **68f0276**, source `43933469…09d121`. Root source and packages
remain unchanged. All work stays within local v56; nothing has been pushed.

## Implemented mapping and boundaries

For groups containing kind 33 and an eight-row kind-8 tail, output widths at
least 192 now select a four-FMLA-row pair plus a five-row, three-way tail.
This includes KH 41/57/.../249 and does not branch on public exact shapes.
The K9 family's existing folded-row indices are preserved. Packed K5 columns
use `c=3*r+ic`; column 15 is masked. K5 computes exactly KW+2 input steps;
the R row is padded to a multiple of three steps. Four ZA tiles cover 192
output columns, emitted with ST3W while preserving each output's FMA order.

The initial K5 source copies KW+191 live floats into three internal planes,
with zero prefix/padding. Later copies use complete LD3W groups, a floor-divided
predicated tail and 0–2 scalar loads. Each plane reserves an extra vector for
internal zero stores. Output row-chunk dependencies from 68f0276 are retained.

Reproducible variants from `tools/gen_v56_k5_triplet.py`:

| Variant | Source SHA-256 prefix | Change |
| --- | --- | --- |
| baseline | 43933469 | Accepted operator |
| triplet | 126a9a86 | Initial K5, serial next-row copy |
| prefetch | e0a89b97 | Adds conditional output prefetch |
| overlap | c1edf4ae | Overlaps complete next-row copies with matrix steps |
| both | ff1257e3 | Combines output prefetch and copy overlap |

## Correctness and ownership evidence

- **1583030**, cn20481, 03:18:10–03:19:12: initial candidate passes 261 signed
  bitwise state cases and 240 timed screening output hashes in DDR/HBM.
- **1583042**, cn20483, 03:19:04–03:20:23: 574 extended cases pass, including
  all 14 affected kernel heights and 16 input alignments each, widths around
  192, all KW remainders modulo three including 3/399/400, long resumed work,
  and 48 cases with input/kernel/output tail guard pages. The interval audit
  checks 4,100,461 source-copy ranges and records zero outside the input object.
  This instruments the computed copy intervals, not every assembly load.
  Four explicit packing modes at chunk factor 1 add 1,044 bitwise state cases.
- The extracted dependency/claim test on the actual K5 source passes 21,802
  plans, 657,325 dependency edges, 5,843,705 claims and 771,872 resumes.
  It also verifies that distinct groups cover every output-row residue exactly
  once, and checks seven chunk sizes. ASan/UBSan cover this host scheduler test,
  not SME machine instructions.
- **1583083**, cn20481, 03:26:13–03:28:58: the three copy/prefetch controls each
  pass 261 bitwise state cases. Initial triplet's runtime ownership audit passes
  54 cases and 7,747 kernel invocations with zero active output conflicts.
  The five variants pass 300 timed output hashes in DDR. HBM is unavailable in
  this allocation (`hbm_node=-1`) and is skipped without overriding permissions.

The copy/prefetch controls have not received the full 574-case input audit or
official/package acceptance; they were not advanced after the negative screen.

## Measured performance and diagnosis

The initial three-round screen gives KH 41 **+0.37% DDR / +0.16% HBM**, but KH 39
**-1.29% / -0.52%**. Those are screening results, not formal benchmark acceptance.
The second DDR screen does not reproduce the small KH 41 gain:

| Variant | KH 39 | KH 41 | KH 55 | KH 81 |
| --- | ---: | ---: | ---: | ---: |
| triplet | -0.73% | -0.19% | +0.23% | -0.11% |
| prefetch | -0.07% | -0.07% | +0.13% | -0.08% |
| overlap | -0.35% | -0.99% | +0.25% | +0.03% |
| both | -0.22% | -1.22% | +0.16% | -0.06% |

Each screen uses three alternating rounds, five timings per process, and the
median process-average GFLOPS. The second table has **no HBM result**. Full
values and strict completeness checks are in `smoke_summary.md` and
`copy_summary.md` under `results/v56/experiments/k5-triplet/`.

**1583056**, cn20481, 03:21:37–03:22:11, profiles 24 instrumented processes:
168 call records and 120 timed output hashes pass. The summary excludes the
validation/warmup calls and converts timer ticks using actual CNTFRQ. Counts
use executed KW+2 steps for K5 and KW+3 for K4, not their padded R row lengths.
The previous generic `roll` diagnostic's packed-step denominator must not be
silently treated as exact executed FMOPA work for these tail kinds.

KH 41 executes 161,241,376 tile steps in the baseline versus 151,461,088 in K5
per call, including row-partition startup: **6.066% less matrix work**. This
does not translate directly to speedup. The K5 tail costs about 1.720 ns per
executed tile step in DDR and 1.687 ns in HBM, versus K8's 1.456/1.389 ns.
These are amortized kernel-region costs, including copy and output events,
not individual instruction latency. The tail's per-thread mean region time
falls about 1,267→1,055 us DDR and 1,209→1,034 us HBM. The HBM main pair grows
about 4,549→4,622 us. Host preparation remains roughly 8–11 us and average
worker packing around 18–21 us, too small to explain the entire gap.

The instrumented worker-time comparison looks better than the uninstrumented
screen, especially DDR. Instrumentation and source changes alter code layout
and scheduling, so the profile is evidence about costs, not a replacement for
actual performance measurements. Serial copying was a plausible contributor,
but its overlap control regresses; this experiment does not establish that
overlap improves throughput or that a particular hardware port is responsible.

## Decision and next investigation

**Do not adopt any K5 variant yet.** The accepted root and all three packages
remain `43933469…09d121`. No official acceptance or archive run is warranted
for the current variants without a stable uninstrumented gain.

Next isolate code-layout sensitivity of the four-chain pair with matched
outlining/alignment controls on both baseline and K5, then inspect the main
loop and tail cost under the same controls. Reassess K5 scheduling weights
from executed, rather than padded, work if the matrix saving remains useful.
The subsequent pull found upstream **87fa5d7**, which changes F4's long-row
copy path; [review and validate its integration first](upstream-gate.md) before
duplicating controls on an outdated base.
Any later improvement must retain input boundaries and output ownership and
pass the full acceptance sequence before replacing the root operator.
