# Folded-chain instruction order with identical linked code placement

Accepted baseline is **3df5c69 / ebf36923518cb809ae5e65001a700de30b0415956f1d0420a2dffcae45684026**,
including the thread-start capacity repair. Main-pair regions dominate the current
four-case profile. The indexed arithmetic-only probe interleaved FMOPA and FMLA,
whereas real F3/F4 steps issue all four FMOPA before the six/eight indexed FMLA.
This control asks whether that grouping is an actionable throughput bottleneck;
the standalone probe does not establish the answer for real memory-fed loops.

`f4` interleaves two indexed FMLA after each of the four FMOPA in PAIRF4_STEP.
`f34` additionally interleaves the first three FMOPA of PAIRF3_STEP with two FMLA
each. Generator assertions require the exact original instruction-line multiset
and preserve both the FMOPA subsequence and the FMLA subsequence. All loads,
addresses, pointer increments, predicates, branches, row events and carry stores
stay unchanged. No coefficient/input cache, benchmark phase selection, shape
dispatch or kernel arithmetic is added. Root source and release archives stay
unchanged until performance and original-reference acceptance justify adoption.

## Linked-code audit

`tools/inspect_v56_fold_schedule.py` checks all **43,640** decoded instruction
addresses in the actual linked uninstrumented benchmarks. Address sets are
identical. The `f4` binary changes only 27 instruction positions in the three
F4 expansions; `f34` changes 45 positions, also covering the two F3 expansions.
Each changed contiguous region is a permutation of exactly the same encoded
arithmetic instructions, with both accumulator subsequences unchanged. Every
other opcode word and operand text matches baseline at the same address.
[Complete audit](../../results/v56/experiments/fold-schedule/compiler_audit.txt).
This eliminates moved loop/code addresses as an explanation for these controls;
it does not identify physical issue ports or guarantee a runtime improvement.

## Completed attribution

Job **1585554**, cn20483, **07:54:51–07:55:51**, succeeds: 54 processes,
**14,364** worker records and **270** timed hashes pass the strict parser.
The parser checks all source/profile hashes, three cyclic orders, all 38 workers
on seven calls per process, executed tile-step conservation, constant per-shape
table storage, and agreement between thread regions and aggregate buckets.
Shapes KH41/55/81 cover short-row F4, F3 and long-row F4. Timed calls 3–7 are
summarized as the median of three process medians.

DDR pair-region us/thread baseline/f4/f34:
- KH41: 4642.034 / 4637.015 / 4639.691.
- KH55: 6560.423 / 6558.109 / 6551.693.
- KH81: 19254.336 / 19266.064 / 19243.199.

HBM pair regions likewise change only slightly. Other regions and worker-end
spread vary as well; there is no large pair-region saving in this diagnostic.
Instrumentation changes source/layout/scheduling, and regions include argument
setup and ZA restore. These small differences are not a production speedup claim
or proof that one class of instructions physically blocks the other.
[Full phase summary](../../results/v56/experiments/fold-schedule/profile_summary.md).

## Completed uninstrumented screen

Job **1585542**, cn20481, **07:53:35–08:00:10**, succeeds. Each changed candidate runs five
signed bitwise state modes, 224 guards and 54 active-output-ownership cases:
**3,058** state/guard and **108** ownership cases all pass, zero active conflicts. Six complete permutations
of baseline/f4/f34, four shapes, DDR/HBM and five timings/process yield **720**
timed hashes all pass. The parser checks all hashes and complete balanced rows.
[Full screening and paired ranges](../../results/v56/experiments/fold-schedule/summary.md).

| Memory | KH | F4/base | F3+F4/base |
| --- | ---: | ---: | ---: |
| DDR | 39 | +0.22% | +0.11% |
| DDR | 41 | +0.16% | +0.12% |
| DDR | 55 | +0.11% | +0.03% |
| DDR | 81 | +0.12% | +0.15% |
| HBM | 39 | +0.24% | +0.06% |
| HBM | 41 | +0.22% | +0.04% |
| HBM | 55 | +0.08% | +0.04% |
| HBM | 81 | -0.25% | +0.13% |

F4 gains are small, and paired signs are mixed: DDR KH41 is positive only 3/6;
HBM KH81 only 2/6. DDR/HBM KH55 and HBM KH41 are positive 6/6. All outliers remain,
including the F3+F4 HBM39 paired -7.06% observation. These ranges are not confidence
intervals. F3+F4 does not show additional consistent benefit in the F3 target
KH55; it is not advanced. Unchanged F3 computation in the F4-only source still
shows a small KH55 change, reinforcing the need for an independent confirmation
rather than attributing every small number to the edited kernel.

## Original-reference confirmation: not adopted

Only F4 weave advances to job **1585635**, cn20481, **08:02:15–08:09:46**: accepted ebf36923 versus
8433e2d4, six AB/BA rounds, four shapes, DDR/HBM, five timings/process. Expected
**96** full reference checks all pass, maximum errors zero, using unchanged
`bench_conv.c`, SHA256 2548861a…e927, with the exact problem compile command.
[Full independent summary](../../results/v56/experiments/fold-schedule/confirm_summary.md).

KH39/41/55/81 independent changes: DDR **+0.06%/+0.18%/+0.03%/-0.03%**;
HBM **-0.16%/+0.31%/+0.02%/-0.16%**. DDR41 is positive in four of six paired
rounds; HBM39 is negative in five, HBM81 in four. The original screen's broader
DDR gains are not consistently retained, and the HBM81 regression recurs.
All raw outliers remain; observed ranges are not confidence intervals.

**Not adopted.** The small KH41 benefit is insufficient to promote this whole-F4
change given the regressions elsewhere and mixed paired signs. F3+F4 was not
advanced. No source or release archive is replaced, and no package acceptance
or fresh v55 claim is needed for these unadopted candidates. This evidence does
not support arithmetic grouping as a large remaining bottleneck. No push.
