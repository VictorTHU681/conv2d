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

Job **1583890**, requested cn20481, is pending/running. Planned 1,044 signed
state cases with step1 plus 640 timed hashes in four Williams orders. No runtime
result or root/package adoption is yet claimed. This matched test is distinct
from adopting the earlier coarse 32/64/96-byte padding sweep, which never tested
the exact accepted 48/80 loop-offset pair.
