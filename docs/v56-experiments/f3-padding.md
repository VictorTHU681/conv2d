# Diagnostic F3 code-position controls

Root accepted v56 remains 8b6b295 / bb82ce3b…6819; no push.
The unadopted [phase-setup candidate](chunk-setup.md) saves parameter-setup work
but regresses KH55 about 0.5% in screening. Its F3 arithmetic words are unchanged,
while loop starts move from offsets 48/80 to 0/32 modulo 128. The latter is a
hypothesis for investigation, not an established cause.

Four variants share immutable phase source 0bfdf223: phase, p32, p64, p96.
The three padded variants add one unconditional branch over NOPs immediately
before the F3 assembly argument loads, adding 32/64/96 bytes there. That branch
executes once per kernel invocation, not per inner iteration; the NOPs never
execute. All arithmetic, phases, packing, continuation and output dependencies
remain unchanged. Compile output must be inspected for actual loop positions:
assembler alignment may absorb some padding or move later kernels.

**Diagnostic-only; no padding adoption is proposed.** Differences between
padded and plain variants include the extra entry branch; comparisons among
the three padded variants hold that branch count fixed. If positions explain
the regression, develop a deliberate loop layout and validate it separately.
Do not report gains here as gains over accepted v56.

Job **1583770**, cn20481, succeeded 05:18:54–05:21:52. All 1,044 signed
state cases at continuation step1 plus 640 timed hashes passed in four balanced
Williams orders, four full shapes and DDR/HBM when permitted. Original benchmark
job 1583757 independently tests the actual phase/carry candidates. Results are diagnostic-only.


[Actual loop positions](../../results/v56/experiments/f3-padding/f3_code.txt)
confirm offsets 0/32, 32/64, 64/96 and 96/0 modulo 128, with all F3 arithmetic
words identical. [Screen results](../../results/v56/experiments/f3-padding/summary.md)
show KH55 improvements over unadopted phase of 0.08–0.20% DDR and -0.01–0.14%
HBM. These changes do not recover the entire ~0.5% phase regression seen in the
separate matched baseline screen. Do not subtract percentages across jobs to
claim a measured residual regression. Other shapes also vary, including ones
that never execute F3, so overall code layout and timing variability remain
confounders. No padding is adopted and no single alignment is established as
the explanation. KH55-specific phase profile 1583794 passes but does not reproduce the uninstrumented regression; see the parent experiment record.
