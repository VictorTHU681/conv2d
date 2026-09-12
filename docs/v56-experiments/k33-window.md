# v56 K33 input-window experiment

Status: all controls are rejected for adoption after screening, PMU diagnostics
and the balanced original-benchmark comparison. Current accepted root source
and packages remain `54dc05d`, SHA-256 `695c449c…`; no push.

## Question and controls

Earlier K41 profiling showed most work in the K33 kernel and many cycle samples
near its input loads. Those sample locations did not prove that the loads were
the throughput limiter. This experiment directly trades repeated input loads
for in-register byte windows while retaining coefficient loads and FMA order.

All candidates derive from immutable `54dc05d:conv2d.c`, including the accepted
input-boundary and packing-race fixes and upstream copy/compute overlap.
Only the pure-compute suffix of `OVL_LOOP(PAIRF_STEP)` changes; its initial
copy-overlap steps, tail copy, coefficient order and state handoff stay intact.

- `baseline`: accepted source, byte-identical.
- `outline`: unchanged K33 computation moved to a noinline function aligned to
  128 bytes; the worker is also aligned to 128 bytes. This measures the cost of
  the experimental isolation itself.
- `unroll4`: outline plus four-way unrolling of the original loads/arithmetic.
- `ext4`: four-step input reuse, using copies plus destructive SVE EXT.
- `tbl4`, `tbl8`: four/eight-step input reuse using SVE2 two-register TBL and
  byte-index vectors prepared once per K33 invocation.

Each outlined candidate fixes the worker's start alignment; generated machine
code still needs inspection before claiming that every other kernel is entirely
unchanged. The enlarged register clobber set can also affect call prologues.
Do not attribute an outline-versus-baseline difference solely to input reuse.

## Bounds and instruction tradeoff

A complete U-step block needs input indices 0 through U+30: two full 16-float
vectors and exactly U-1 floats of a third vector. The third load uses a predicate
with U-1 lanes. Only enter that block if at least U kernel columns remain; the
remainder uses the original two loads per step. No extra input lookahead beyond
the live ring interval is introduced, and no kernel coefficient is skipped.

The block reduces input-vector loads from 2U to 3. It advances the input pointer
once per block while preserving every scalar/coefficient pointer increment.
EXT needs two register copies and two extracts for each shifted window because
SVE EXT is destructive. TBL needs two table operations instead, but consumes
additional index registers and permutation throughput. Reduced memory access is
therefore a hypothesis, not a guarantee of faster convolution.

The previously unsubmitted draft used the old pre-integration source and an
invalid non-destructive EXT form. It was replaced before server execution;
none of its source files or proposed variants are performance evidence.
The final assembler probe accepted both the corrected EXT sequence and two-
register TBL under the server's existing armv9-a+sme+sve2 toolchain.

## Validation scope

Each of five changed candidates runs the 261-case state sweep and 122 extended
K33-family cases: KH 33/41/49/57/65/105/233, odd/even KW around unroll boundaries,
KW 399/400, multi-chunk resumption, and inaccessible pages immediately after
input, kernel and output buffers. Expected total is **1,915** bitwise cases.

Screening uses six variants, four official shapes, three alternating rounds,
DDR/HBM separately, and five timings per process: **720** timed hashes if both
memory placements are available. Full official acceptance is only warranted
if a candidate shows a meaningful benefit without unresolved correctness issues.
Sources, hashes, logs and machine-code evidence live in
`results/v56/experiments/k33-window/` and the ignored build directory.

```bash
python3 tools/gen_v56_k33_window.py
```

## Completed results

**1582563**, cn20483, 02:05:52–02:11:31: all 1,915 bitwise cases and 720 timed
hashes passed. K41 screening changes versus accepted source:

| Candidate | DDR | HBM |
| --- | ---: | ---: |
| outline | +0.69% | +0.09% |
| unroll4 | +1.09% | +0.10% |
| ext4 | +0.00% | +0.07% |
| tbl4 | -0.86% | +0.21% |
| tbl8 | +0.77% | +0.20% |

Machine-code inspection finds all five outlined workers have 2,199 instructions
and identical normalized instruction text (annotated relocated addresses removed).
Their starts and outlined K33 entries are aligned to 128 bytes; absolute
addresses still differ. The accepted baseline worker has 2,363 instructions and
start offset 112 modulo 128. The outlined control therefore matters. Evidence:
`machine_code.txt`, K33 disassembly excerpts, and `tools/inspect_v56_k33_window.py`.
Full worker disassembly is retained remotely and in the ignored build directory.

**1582619**, cn20481, 02:12:25–02:15:26: 24 PMU runs, 200 steady calls per run,
two alternating rounds in DDR/HBM. All four events have >=99.9% scheduling
coverage. Relative to outline, ext4/tbl4/tbl8 reduce L1-load events about 15–17%.
TBL reduces retired instructions up to 8%; tbl4 reduces L1-load-miss events about
10–11%. However, DDR latency changes are +0.17%/+0.49%/+0.42%, and HBM changes
are approximately 0.00%/-0.08%/+0.16%. The memory-event reduction is real but
does not translate into a consistent convolution speedup. Counters include
initialization, warmup and pool spinning; they do not measure only K33 or DRAM
bytes. Full comparison: `pmu_summary.md`.

Unroll4 gets a 0.72% DDR steady-latency reduction versus outline, but only 0.04%
in HBM. It advances alone to original-benchmark testing alongside baseline and
outline, without adopting any window instructions.

**1582685** DDR cn20481 02:21:20–02:27:16 and **1582686** HBM cn20483
02:21:20–02:27:12: all six permutations of the three programs, each shape/memory,
five timed calls per process. All **144** complete-reference checks have maximum
error zero. This balances both position and ordered predecessor pairs.

| KH=KW | Unroll4 vs accepted, DDR | Unroll4 vs accepted, HBM |
| --- | ---: | ---: |
| 39 | -0.00% | +0.02% |
| 41 | -0.09% | +0.14% |
| 55 | +0.06% | +0.07% |
| 81 | +0.03% | -0.01% |

Unroll4 improves K41 versus the outlined control by 0.40% DDR / 0.15% HBM,
but does not establish a useful improvement versus the accepted inline source.
Do not promote it or reinterpret the initial +1.09% screening result as a
validated gain. `official_summary.md` retains all three variants' values.

The follow-up [mixed-arithmetic probe](mixed-throughput.md) tests the arithmetic
budget directly. Its results motivate improving matrix occupancy/grouping;
they do not establish a physical execution-port diagram or eliminate all
memory-related costs in the real convolution.
