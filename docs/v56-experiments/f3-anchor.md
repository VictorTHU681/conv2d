# Matched inline F3 layout anchors

Accepted root remains 8b6b295 / bb82ce3b…6819. No push.
The [outlining control](f3-outline.md) largely removes the KH55 phase/base
regression when both use identical F3 machine code, but outlining itself hurts
other cases. This follow-up keeps the F3 function inlined.

Four variants: baseline, phase, baseline_anchor, phase_anchor. Anchored variants
add one branch over a 128-byte alignment directive plus 20 NOPs before F3's
assembly argument loads. The branch executes once per kernel invocation; the
padding never executes. That anchors the two F3 hot-loop starts at offsets
48/80 modulo 128, matching the accepted baseline. Source arithmetic, coefficient
phases, input copies, packing and output dependencies remain unchanged apart
from the already isolated phase rewrite in phase/phase_anchor. No public-shape
or call-stage dispatch is introduced.

The 20-NOP count is derived from a compile-only zero-NOP probe, whose loop
offsets are 96/0: (48-96) mod128 = 80 bytes. This is a code-layout constraint
for the current assembly body/toolchain, not a universal optimal alignment.
The disassembly checker requires actual anchored offsets 48/80; future changes
that break them require renewed analysis. Padding/body address effects on other
inlined kernels remain possible and require the full four-shape comparison.
See [derivation](../../results/v56/experiments/f3-anchor/derivation.txt).

Job **1583890**, cn20481 05:36:44–05:39:40, succeeded: all 1,044 signed
state cases and 640 timed hashes pass. [Disassembly](../../results/v56/experiments/f3-anchor/f3_code.txt)
confirms both anchored sources have the intended 48/80 offsets and unchanged
F3 arithmetic words. Phase_anchor's two arithmetic blocks even have the same
absolute addresses as the accepted baseline in these screening binaries; this
does not hold the whole worker fixed.

[Screen](../../results/v56/experiments/f3-anchor/summary.md): phase_anchor/base
still changes KH55 -0.15% DDR / -0.19% HBM, and KH41 -0.04% / -0.16%.
KH39 changes +0.19% / -0.28%; KH81 +0.04% / -0.02%. The matched
phase_anchor/baseline_anchor KH55 comparison is -0.27% / -0.16%.
Anchoring recovers part of phase's larger KH55 regression but does not yield
a consistent overall improvement; **neither anchored variant is adopted**.
This control never establishes one alignment as the sole cause or a universal
optimum. Full worker layout, setup code and remaining kernels still differ.

The coarse 32/64/96-byte padding sweep did not test accepted 48/80 positions;
this matched follow-up does, with the limited outcome reported above. Further
work moves from layout probes to [per-piece phase preparation](piece-phases.md),
which avoids recomputing phases during each continuation chunk.
