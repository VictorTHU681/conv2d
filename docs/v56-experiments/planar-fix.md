# v56 rolling-copy correction and upstream integration

Status: correctness and package acceptance passed, but K39 HBM performance is
unstable in the formal comparison. Promotion is deferred while profiling that
result. Root source and release programs remain `595d7f7d…`. No push.

## Changes

`tools/gen_v56_planar_fix.py` combines immutable local `93163b4` with upstream
`b9591de`, using `8ce8af2` as the common base. The one source conflict is the
first-copy setup: retain the local bounded helper copy and upstream overlap
counters. Local K9 load reuse remains present. Upstream group-release packing,
row-copy overlap and K4 scheduling remain present.

Both correction-only and integrated candidates then:

- Initialize K9/K4 first-row planes from the real input start, explicitly zeroing
  unused prefix and padding inside the ring. Later assembly rows retain their
  aligned layout. The first-row preparation does not read before the input.
- Give K4 an exact `KW + 255` live span. Full `ld4w` groups and a floor-divided
  tail read complete groups; 0–3 remaining floats use scalar loads. Zero-padded
  vector stores fill the internal tail, with an extra 64 bytes per plane to
  contain those stores. The upstream overlap-tail sequence receives the same fix.
- Replace speculative duplicate packing with waits on each uniquely claimed
  chunk's release-published completion flag. No thread rewrites another owner's
  chunk in `CONV_PACKSER=0`.

The `--k8` extension also bounds K8 input copies to `KW + 127`. Even KW needs
one padded input element internally; both ring slots now initialize that element
to zero and reserve space for it. The matrix arithmetic and coefficient order
remain unchanged. This is a source-level boundary correction, not a claim that
all possible undefined behavior elsewhere has been eliminated.

## Two isolated validation jobs

- **1582361**, cn20481: initial K9/K4 and packing correction. It intentionally
  does not include the later K8 fix, so cannot become the final implementation.
  Sources and raw log: `results/v56/experiments/planar-fix/`.
- **1582381**, cn20483: complete K8/K9/K4 candidate, generated with `--k8`.
  Sources and raw log: `results/v56/experiments/planar-fix-full/`.

Source hashes for the complete candidates:

- Correction-only: `4d1c2c4cedbfc463917a08560c70563753fd0ec4fcc17893d0cbe109db439847`.
- Integrated: `695c449ccdc0b234ae16812a49b26afc7a7d0153d5d0b33983c7b3a281f3530b`.

The complete audit checks the initial helper/planar intervals and enumerates
later-row copy intervals from the actual runtime arguments and the assembly's
row progression. This is not instruction-by-instruction memory instrumentation.
For 96 alignment cases, the old implementation requests 317 out-of-input spans:
8 ordinary/K8 subsequent copies, 30 K9, 279 K4. Each complete candidate requests
zero out-of-input spans; all 96 outputs remain bitwise equal. There are 362,912
audited intervals per variant. The positive control's `PASS` means that the
expected defect was observed, not that the old source is memory safe.

The complete job also has 224 end-guard-page cases per candidate, covering
KH 19/25/39/41/55/81/113/231, fourteen odd/even KW values including 399/400,
and output widths 256/257. Local fixed runs the 261-case state sweep in default,
0 and 1 packing modes; integrated runs it in default, 0, 1, 2 and 3 modes.
Expected total is 288 audit cases + 448 guard cases + 2,088 state cases = 2,824.

After correctness, each job screens baseline, upstream, correction-only and
integrated sources in three alternating process rounds, four official shapes,
DDR/HBM separately and five timings per process (480 timed hashes if both
memory modes are permitted). These are screening measurements using `fbench`;
formal acceptance uses untouched `bench_conv.c` and the original compile command.
`jobs/v56_planar_official_job.sh` prepares that three-way formal comparison.

## Reproduction

```bash
python3 tools/gen_v56_planar_fix.py
python3 tools/gen_v56_planar_fix_audit.py
python3 tools/gen_v56_planar_fix.py --k8
python3 tools/gen_v56_planar_fix_audit.py --full
```

Only the first two commands regenerate the initial job's sources; the latter
two use a separate directory and preserve the earlier experiment's provenance.

## Completed acceptance and unresolved performance

Both screening jobs succeeded: 1582361 ended 01:42:10, and 1582381 ended
01:43:38. The initial job passes 2,712 audit/guard/state checks and 480 timed
hashes; the complete job passes 2,824 and 480 respectively. These totals include
the 96-case positive control which must demonstrate the old boundary defect.
Both corrected candidates have zero audited out-of-input intervals.

**1582422**, cn20481, 01:43:10–01:49:01: original compiler command and untouched
official benchmark; all 72 complete-reference checks have maximum error zero.
All source variants use the same node within each DDR/HBM comparison. Medians
of three process-average GFLOPS values (five timings per process):

| KH=KW | Integrated vs local, DDR | Integrated vs local, HBM | Integrated vs upstream, DDR | Integrated vs upstream, HBM |
| --- | ---: | ---: | ---: | ---: |
| 39 | +1.90% | -2.21% | +0.25% | -1.96% |
| 41 | +0.44% | +0.54% | +0.43% | -0.10% |
| 55 | +1.05% | +0.73% | +0.35% | +0.00% |
| 81 | -0.03% | +0.05% | +1.92% | +1.90% |

These replace neither the earlier v55 comparison nor other-node screening
numbers; no percentages from different jobs are added. Full values and strict
validation are in `planar-fix-full/official_summary.md` and
`tools/summarize_v56_planar_official.py`.

**1582430**, cn20483, 01:44:26–01:46:37: all three staged archives successfully
run their bundled scripts, with four full-reference PASS checks each. Archive
hashes and exact candidate README are retained under `planar-fix-full/`.
`conv_diag.zip` remains a diagnostic build, not a formal submission recommendation.

K39 HBM integrated GFLOPS by official round are 14047.4, 14343.6, 14038.4.
The high round runs the integrated program first, while the low rounds run it
after upstream. That association does not establish causality. The two source
versions and memory placement were unchanged; finer frequency/time histories
were not captured for every run, so neither frequency nor scheduling is assumed
to explain the gap.

**1582487** requests the same cn20481 for a six-row Williams-design comparison:
baseline, upstream, integrated default, and integrated packing modes 1/2/3.
Each variant occupies every process position once; all 30 ordered predecessor
pairs occur exactly once. Explicit mode 3 is an unchanged-program control for
the integrated default. Each process runs the original benchmark with five
timings; separate subsequent runs enable existing per-kernel/per-thread counters.
The earlier cyclic-order job 1582481 was deliberately cancelled before using
its data because it did not balance predecessor pairs. No result from that job
is evidence of gain or loss. Follow-up log: `planar-fix-full/k39_order_balanced.log`.
