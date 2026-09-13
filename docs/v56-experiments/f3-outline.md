# Matched F3 outlining controls

Accepted source remains local v56 8b6b295 / bb82ce3b…6819. Main was pulled on
this continuation and no newer upstream commit was found; no push.

The phase-setup rewrite saves measured setup work and improves official KH41
+0.50% DDR / +0.60% HBM, but official KH55 regresses -0.40% / -0.46%. F3
padding recovers only a small part in a separate screen, while inserting timing
code hides the regression. Root operator is unchanged; no padded source adopted.

Four variants isolate function boundaries:
- baseline: accepted 8b6b295;
- phase: the unadopted modular phase rewrite;
- baseline_out: accepted source with only k16pairf3 marked noinline;
- phase_out: phase rewrite with the same noinline attribute.

F3 arithmetic, copies, grouping, packing and output dependencies are unchanged.
No call-stage or exact-shape selection is added. Compare phase/base with
phase_out/baseline_out to study the interaction; outlining itself can change
call overhead, compiler scaffolding and remaining worker layout. Inspect actual
compiled instructions before claiming that the F3 body has been held fixed.
Earlier rejected F4 outlining is a different control and is not silently adopted.

Job **1583843**, cn20481 05:30:34–05:33:37, succeeded: 1,044 signed
state cases at continuation step1 and all 640 timed hashes pass. Four balanced
Williams orders cover all four full shapes and both placements.

[Machine-code inspection](../../results/v56/experiments/f3-outline/f3_code.txt)
confirms the outlined F3 functions have **identical full instruction addresses
and words** between baseline_out and phase_out. Their hot-loop offsets are
48/80 modulo 128, matching accepted baseline; inline phase instead has 0/32.

[Results](../../results/v56/experiments/f3-outline/summary.md): phase/base at
KH55 is -0.58% DDR / -0.44% HBM. With the same outlined F3 body,
phase_out/baseline_out shrinks to -0.05% / +0.06%. This is stronger evidence
of interaction with inlined code layout, but outlining also changes the rest
of the worker and is not proof of one microarchitectural cause.

Outlining itself costs KH55 -0.21% DDR / -0.13% HBM against baseline. Phase_out
versus accepted baseline regresses DDR KH39 by 0.78% and DDR KH41 by 0.27%,
so **neither outlined source is adopted**. Inline phase KH41 is also -0.15% DDR
in this screen, unlike its +0.50% official result; retain that variability.
No original-benchmark or package acceptance is claimed for the outlined sources.

Next [matched inline F3 layout anchors](f3-anchor.md) retain inlining while
holding the two F3 loop offsets at the accepted 48/80 positions. This is a
separate candidate requiring its own results, not adoption of diagnostic pads.
