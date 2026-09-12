# Next v56 candidate: five residual rows with three-way folding

Status: an isolated K5 implementation now exists and passes extended correctness
checks, but has no stable uninstrumented speedup. It is not adopted; see the
[implementation, profiles and rejected controls](k5-triplet.md).
The accepted operator now uses source `4689e38f…015319`, integrating the
upstream F4 gate while retaining the output write-order correction. Historical
K5 candidates and their results remain based on immutable `68f0276` / `43933469`;
they have not been rebased or adopted.
The indexed-FMLA follow-up 1582779 has now independently confirmed the same
eight-FMLA arithmetic-only budget. The [output overlap race](output-ownership.md)
has been corrected; all K5 experiments preserve row-chunk dependencies.

## Why change the grouping

The K33 input-window experiment reduces L1 load events by roughly 15–17% and
instructions by up to 8%, without a stable throughput gain. The synthetic
probe measures four FMOPA plus up to eight FMLA at eight normalized cycles;
ten or more FMLA increase the step cost. This supports trying to use the spare
FMLA capacity while reducing matrix work, rather than adding more than four
folded rows to a 32-column pair (two FMLA instructions per folded row).

For the family currently grouped as `pair+1 FMLA` and an eight-row residual
group, fold four rows into the pair and leave five rows. A three-way folded
five-row kernel uses 15 of the 16 ZA columns, with four tiles covering 192
output columns. The grouping becomes 36+5 for KH 41. This is a structural
family, also applicable to KH 57/73/... when the existing plan contains that
pair/tail combination, and only when the output is wide enough for 192 columns.
Narrow outputs retain the existing plan. Do not branch on the public exact size.

## Lane mapping and accumulation order

For residual index r in [0,5) and subcolumn ic in [0,3), ZA column c=3*r+ic.
Column 15 is inactive. Tile t and vector lane q correspond to output column
`base + 48*t + 3*q + ic`. At step X, load input `base + 48*t + 3*q + X` and
coefficient `k[(y-r) mod KH][X-ic]`, with zeros when X-ic is outside [0,KW).
Thus each output receives kernel columns 0..KW-1 in order, with the same
kernel-row rotation used by the existing rolling family.

At an output event, extract columns 3*r, 3*r+1, 3*r+2 with MOVA and interleave
using ST3W, then clear those three ZA columns. Group state remains the complete
ZA save/restore already used by the worker; the existing four-chain pair keeps
its own FMLA carry. The folded pair covers the final four residuals, and K5
covers the first five tail residuals, so there is neither a gap nor overlap.

## Packing and bounds requirements

- Add kind 5 to R packing with `sidx=c/3`, `ic=c%3`, and explicitly mask c=15.
  Build all rows and coefficients on every call; no content cache.
- K5 has width 192 and packed steps `ceil((KW+2)/3)*3`. Execute exactly KW+2
  input steps: full triples plus 0–2 tail steps, advancing over padded R entries.
- Input planes use LD3W/ST1W; three plane pointers serve the three substeps.
  First-row initialization uses the accepted bounded `roll_first_planes` helper
  with three planes. Later-row copy spans only KW+191 live floats plus the
  existing aligned prefix. Use floor-divided triplets and 0–2 scalar tail loads;
  initialize padding inside the ring, never read rounded-up external input.
- Reserve an extra vector per plane for zero-padding stores. Keep the current
  last-row self-copy behavior and validate every source interval.
- Convert only a matching kind-33 pair and kind-8 tail with eight residuals;
  update pair kind, tail width/steps/RSB, packing dispatch, kernel dispatch and
  the small-fold scheduling weight. Do not disturb the K9 family's custom sf.

## Work estimate, not a speedup claim

For W=4096, KW=41, output width is 4056. Ignoring row-partition startup work:

- Current pair: ceil(4056/32)*4*41 = 20,828 FMOPA instructions per input row.
- Current K8: ceil(4056/128)*4*42 = 5,376; total 26,204.
- Proposed K5: ceil(4056/192)*4*43 = 3,784; with the unchanged pair matrix work,
  total 24,612, about 6.08% fewer FMOPA instructions.

For arbitrarily wide outputs and large KW, the reduction tends to 6.67%.
This excludes first-row preparation, copy/deinterleave cost, coefficient-cache
pressure, output events, load imbalance and extra pair FMLA instructions. The
four-chain pair reaches the measured mixed-arithmetic budget, so a real gain
must be demonstrated, not inferred from matrix counts alone.

Required first checks: independent signed bitwise reference, KW remainders
0/1/2 modulo three including KW 3 and 400, all input alignments, input/kernel/
output end guards, output widths around 192, multi-chunk resume and changed
inputs/coefficients. Then profile K5 cost and screen all four official shapes.
