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

Job **1583357**, cn20483, is running. It compiles and tests each variant's 261
signed bitwise state cases, then screens four public shapes with five timings
per process. Four Williams-design orders balance position and immediate
predecessor, with separate DDR/HBM results when allocation permits. Full binary
disassembly is retained under the ignored build tree for actual code inspection.
The strict summary requires all variants, positions, predecessors and timed hashes.

None of these candidates is adopted. Existing K5 guards from the historical
source are useful background, not acceptance of this rebased/outlined source.
Any candidate with a measured benefit still needs relevant extended checks,
original benchmark comparison and package acceptance before replacing the root.
