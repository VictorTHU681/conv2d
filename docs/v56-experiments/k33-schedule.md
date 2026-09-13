# v56 control — K33 scalar-coefficient scheduling

Baseline is corrected v56 `93163b4`. Move the scalar coefficient LD1RW to
the start of each KW iteration (`early`); also interleave its two vector
FMLAs after the first two independent FMOPAs (`weave`). Each accumulator
receives the same contributions in the same order. The generator asserts
that the loop's instruction-line multiset is unchanged. This tests whether
making that coefficient available earlier helps the measured hot loop.

Job **1582160** SUCCEEDED on cn20481, 2026-09-13 01:10:02–01:11:42.
Both variants pass 261 signed state cases each (**522 checks**), and all
**360 timed hashes** pass. Disassembly verifies all three variants retain
17 instructions and the same loop start (offset 112 modulo 128), removing
loop-size/start-placement changes from this particular control.
Three alternating process rounds, five timings per process:

DDR
| Variant | k39 | k41 | k55 | k81 |
|---|---:|---:|---:|---:|
| baseline | 13921.0 (+0.00%, n=3) | 13593.0 (+0.00%, n=3) | 14340.1 (+0.00%, n=3) | 15430.3 (+0.00%, n=3) |
| early | 13881.1 (-0.29%, n=3) | 13498.7 (-0.69%, n=3) | 14330.8 (-0.06%, n=3) | 15394.8 (-0.23%, n=3) |
| weave | 13942.3 (+0.15%, n=3) | 13601.2 (+0.06%, n=3) | 14341.1 (+0.01%, n=3) | 15415.6 (-0.10%, n=3) |
HBM
| Variant | k39 | k41 | k55 | k81 |
|---|---:|---:|---:|---:|
| baseline | 14314.0 (+0.00%, n=3) | 14123.3 (+0.00%, n=3) | 14429.5 (+0.00%, n=3) | 15416.8 (+0.00%, n=3) |
| early | 14263.9 (-0.35%, n=3) | 14085.1 (-0.27%, n=3) | 14406.2 (-0.16%, n=3) | 15398.5 (-0.12%, n=3) |
| weave | 14315.2 (+0.01%, n=3) | 14107.2 (-0.11%, n=3) | 14413.6 (-0.11%, n=3) | 15391.5 (-0.16%, n=3) |

**Decision:** reject both controls. Early coefficient loading regresses K41
0.69% DDR / 0.27% HBM. Interleaving changes it +0.06% / -0.11%, with small
regressions elsewhere. This does not support the scalar coefficient's late
placement as an actionable bottleneck. No production or archive change.

Generator: `tools/gen_v56_k33_schedule.py`; job:
`jobs/v56_k33_schedule_job.sh`. Evidence and loop excerpts are under
`results/v56/experiments/k33-schedule/`. Full remote disassembly is retained;
its local copy is in ignored build storage.
