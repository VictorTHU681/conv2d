# K5 matched F4 outlining controls after accepted upstream gate

The earlier K5 candidate executes 6.066% fewer matrix tile steps for KH 41 but
has no stable uninstrumented speedup. Its instrumented phase times look better
than end-to-end screening, so test sensitivity to F4 function placement on both
baseline and K5. This is a controlled hypothesis, not an established explanation.

The accepted root remains local v56 commit 4817eff / source 4689e38f. The later
[kf sharing experiment](kf-share.md) is not adopted after a negative official
comparison and inconsistent same-executable control. No push.

`tools/gen_v56_k5_layout.py` merges immutable accepted 4817eff with the original
K5 triplet 126a9a86, using 68f0276 as the common source. It retains the accepted
F4 short/long gate and all input/output ownership fixes. Both outlined variants
change only the F4 function declaration to add `noinline`; K5's own function
was already outlined. The baseline receives the same declaration change so
its effect can be distinguished from changing the residual grouping.

| Variant | Source SHA-256 |
| --- | --- |
| baseline | 4689e38fbabc93a453541052b2260d9092473d0d2552311ddbb9126118015319 |
| triplet | 4b35b3d5af1d85c8d6cf2ddc54073c0ccc75467cdc185229e0bbd906b355f905 |
| baseline_out | 7248165a4329b860daf89cf28233ea36f5107c730d8434f3bee8c7b38ba1fcbb |
| triplet_out | 4c82ab4e7b47723e31c637fe71c3cc28a9f87a7473a915e0ec5639fb32b639f4 |

Job **1583357**, cn20483, 04:10:38–04:13:37, succeeded: 1,044 signed
bitwise state cases and 640 timed hashes. Four Williams-design rounds balance
position and immediate predecessor, with separate DDR/HBM results. Four variants
all use identical 21-word F4 arithmetic steps, at mod128 positions 120/32/0.
The outlined variants actually execute those steps in k16pairf4; inline variants
execute them within roll_worker. See machine_code.txt and instruction excerpts.

Plain K5 changes KH 39/41/55/81 by -0.55/+0.99/-0.01/-0.27% DDR and
-0.45/+0.82/-0.05/-0.08% HBM. Outlined K5 changes the same cases versus the
accepted baseline by -1.10/+1.06/-0.43/-0.02% DDR and
-0.23/+1.09/-0.35/-0.15% HBM. Against its matched outlined baseline, K5's
KH 41 benefit is +0.68% DDR / +1.07% HBM. Thus outlining alone does not
explain away the current KH 41 improvement, but the other-shape regressions
prevent a claim of universal improvement. These are screening results, not
original benchmark acceptance. Full values remain in summary.md.

**1583386**, cn20481, 04:16:17–04:19:17, succeeded for both K5 candidates.
Each passes 574 extended cases, 1,044 state cases across modes 0/1/2/3 with
one-period chunks, and 54 output-ownership cases (7,747 calls, zero active
conflicts). Each input audit checks 4,100,461 calculated copy intervals with
zero outside; it does not instrument every assembly memory instruction.
The grouping and output dependency/claim functions are byte-identical to the
historical K5 source's host-tested extracted functions; hashes record that
limited equivalence rather than claim a new full-operator host execution.

**1583387**, cn20483, runs the three-way original benchmark comparison over
all six permutations, four shapes and allowed memory placements. It is pending.
**1583390**, cn20481, 04:19:18–04:20:12, succeeded: 72 profiled processes,
504 call records and 360 timed hashes. Baseline/plain K5/outlined K5 use all
six permutations on KH 39 and 41. Full phase results are in profile_summary.md.
For KH 41 DDR, K5 reduces the tail mean from 1,252 to 1,080 us but raises the
main mean from 4,645 to 4,706 us. Worker-duration maximum minus mean grows from
74.5 to 182.0 us (HBM 31.5 to 85.0 us). These are per-thread durations, not
absolute finish timestamps, but they point to additional work-distribution
imbalance as a concrete cost worth testing. Profiling does not establish that
scheduler weighting is the cause or replace the official comparison.
**1583398**, cn20481, 04:20:14–04:20:52, succeeded at KW 63/64/65 across every
K5-family height: each candidate passes 756 alignment/guard cases and 4,029,774
calculated copy intervals with zero outside. These gate-transition cases were
absent from the historical K5 extended driver; no old acceptance was assumed.
The [executed-step cost control](k5-cost.md) now tests the specific discrepancy
between padded packing steps and actual kernel work.

None of these candidates is adopted. Existing K5 guards from the historical
source are useful background, not acceptance of this rebased/outlined source.
Any candidate with a measured benefit still needs relevant extended checks,
original benchmark comparison and package acceptance before replacing the root.
