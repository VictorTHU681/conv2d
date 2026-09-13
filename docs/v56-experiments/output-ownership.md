# v56 output ownership audit: overlapping writers found in 54dc05d

Source under review: `54dc05d:conv2d.c`, SHA-256
`695c449ccdc0b234ae16812a49b26afc7a7d0153d5d0b33983c7b3a281f3530b`.
This historical finding concerns the source before the output-order correction.
Current accepted source `43933469…09d121` incorporates the validated
[row-chunk dependency fix](output-order.md).

## Finding

`roll_prepare` clamps the final strip base to `outW - width`, so a nonmultiple
output width causes that strip to overlap its predecessor. Each strip has its
own items, pieces, carry and ready flags. `resume_claim` excludes simultaneous
owners of the same piece, but does not order different overlapping items.
The kernels store their complete strip width with the full predicate.
Consequently different workers can issue unsynchronized writes to the same
output elements. Bitwise-equal values do not make those writes race-free.

For the official 41x41 shape, the two final pair strips cover [4000,4032) and
[4024,4056), sharing eight columns. The K8 group shares 40 columns. All four
official shapes have at least one affected group; this is also a general
nonmultiple-width issue, not an exact-shape optimization.

`tools/audit_v56_output_ownership.py` extracts the actual grouping and claim
functions from the immutable revision and compiles them on the host. Its two
synthetic pieces cover the same output rows in the adjacent final strips;
both claims succeed before either publishes completion. The diagnostic proves
the lack of cross-item exclusion. It does not claim to have observed two SME
stores at the same instant, an incorrect output, or a ThreadSanitizer report.
The source's clamping rule and full-width stores complete the static finding.

Results: [ownership/claim table](../../results/v56/experiments/output-ownership/summary.md).

## Status and repair requirements

**Fixed by the adopted row-chunk dependency candidate.** Earlier
input-copy and coefficient-packing fixes do not address output ownership.
Existing reference/guard tests passing does not disprove this issue.
The [ordering candidates](output-order.md) have completed acceptance. Runtime
controls confirm active conflicts in the baseline and zero in both fixes.
The first candidate's large performance regression motivated ordering only
the intersecting row chunks, which is the adopted implementation.

Prefer giving each output column a single writer, including masked final-strip
stores for every rolling kernel family and folded FMLA output. Alternatively,
order overlapping output pieces explicitly using acquire/release completion,
without introducing claim deadlocks or overlooking split/resumed pieces.
The repair required an ownership-specific check plus signed bitwise, boundary,
multi-chunk, all packing modes and official performance validation before
replacing the accepted source. Those checks and archive validation now pass.

Separately, `roll_worker` forms `c->out + (ja-KH+1)*outW + base` before the output
object during initial warmup rows. Assembly selects scratch for those rows,
but that does not make the preceding C pointer arithmetic valid. This is a
separate language-level defect, not evidence that warmup stores hit external
memory. The accepted fix changes the warmup cursor to integer address arithmetic;
that specific invalid C pointer formation is corrected and the output checks pass.
