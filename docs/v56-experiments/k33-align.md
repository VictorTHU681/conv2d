# v56 control — K33 loop alignment

Baseline is corrected v56 `93163b4` (SHA-256 595d7f7d…102339). `previous`
is pre-correction v56 `72b10c2`. These are local experimental controls,
not new published versions. Production source and archives remain unchanged.

Generator `tools/gen_v56_k33_align.py` counts ROW_HEAD_COMMON instructions
and places padding before the row loop so the inner KW loop begins on a
64- or 128-byte boundary. Padding executes once per kernel invocation,
not per input row. Both use ten explicit NOPs after the outer alignment.
FMA order, instruction body, coefficient rebuilding and input bounds are
unchanged. `prior128` applies the same alignment to the old source, solely
as a diagnostic control; its known old input-prefix read is not restored.

Job **1582116** SUCCEEDED on cn20481, 2026-09-13 01:04:07–01:06:17.
Both corrected variants pass 261 signed state cases each (**522 checks**),
and all **600 timed hashes** pass. Three alternating rounds, five timings
per process. Throughput is relative to corrected v56:

DDR
| Variant | k39 | k41 | k55 | k81 |
|---|---:|---:|---:|---:|
| baseline | 13904.2 (+0.00%, n=3) | 13528.7 (+0.00%, n=3) | 14326.4 (+0.00%, n=3) | 15399.3 (+0.00%, n=3) |
| previous | 13913.0 (+0.06%, n=3) | 13557.3 (+0.21%, n=3) | 14334.5 (+0.06%, n=3) | 15370.1 (-0.19%, n=3) |
| align64 | 13924.3 (+0.14%, n=3) | 13581.4 (+0.39%, n=3) | 14328.7 (+0.02%, n=3) | 15398.4 (-0.01%, n=3) |
| align128 | 13890.2 (-0.10%, n=3) | 13544.0 (+0.11%, n=3) | 14314.1 (-0.09%, n=3) | 15451.2 (+0.34%, n=3) |
| prior128 | 13886.6 (-0.13%, n=3) | 13446.0 (-0.61%, n=3) | 14328.5 (+0.01%, n=3) | 15397.1 (-0.01%, n=3) |
HBM
| Variant | k39 | k41 | k55 | k81 |
|---|---:|---:|---:|---:|
| baseline | 14328.2 (+0.00%, n=3) | 14085.0 (+0.00%, n=3) | 14425.6 (+0.00%, n=3) | 15400.0 (+0.00%, n=3) |
| previous | 14299.6 (-0.20%, n=3) | 14087.2 (+0.02%, n=3) | 14416.9 (-0.06%, n=3) | 15379.8 (-0.13%, n=3) |
| align64 | 14298.9 (-0.20%, n=3) | 14108.6 (+0.17%, n=3) | 14403.8 (-0.15%, n=3) | 15395.2 (-0.03%, n=3) |
| align128 | 14265.3 (-0.44%, n=3) | 14114.5 (+0.21%, n=3) | 14406.5 (-0.13%, n=3) | 15380.1 (-0.13%, n=3) |
| prior128 | 14288.7 (-0.28%, n=3) | 14085.6 (+0.00%, n=3) | 14396.1 (-0.20%, n=3) | 15394.1 (-0.04%, n=3) |

Disassembly confirms 17 instructions per KW loop. Modulo-128 start offsets
are baseline 112, previous 96, align64 64, align128 0, prior128 0.
The within-job baseline/previous difference is only 0.21% DDR / 0.02% HBM
for K41, smaller than the earlier official result; run variation remains
material at this scale. Align64 improves K41 0.39% DDR / 0.17% HBM but has
small regressions elsewhere; align128 yields 0.11% / 0.21% with a 0.44% k39
HBM regression. Matching alignment in the old source does not consistently
improve it. This is not evidence for attributing the full earlier regression
to the loop's start address.

**Decision:** do not promote either alignment control. Small mixed changes
do not justify another implementation change. Preserve the verified source.
Job script: `jobs/v56_k33_align_job.sh`. Raw log, source hashes, measured
summary and extracted K33 loops: `results/v56/experiments/k33-align/`.
Full disassembly remains in the remote results directory and local ignored
`build/v56/experiments/k33-align/raw-disassembly/`.
