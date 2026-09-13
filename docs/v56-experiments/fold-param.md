# Keep the folded output phase in an unused register

Accepted source remains **3df5c69 / ebf36923518cb809ae5e65001a700de30b0415956f1d0420a2dffcae45684026**.
The arithmetic-order experiment found only small pair-region changes, motivating
a separate control over per-row scalar work. This candidate derives directly
from accepted source; it does not include the unaccepted arithmetic permutations.

F3/F4 row events load the same `A.nlines` (output phase CF0, offset 216) on every
row. Their shared LOAD_ARGS also loads `A.nvB` into x25 (offset 120), but these
two kernels do not consume x25 afterward. The generator recursively audits all
referenced source macros, allowing x25 only in LOAD_ARGS and its required clobber
declaration. Direct F3/F4 bodies must have no existing x25/w25 use.

`cf4` uses a private LOAD_ARGS clone for F4: load CF0 into x25 instead of unused
nvB, then replace its per-row `ldr x24,[A,#216]` with `mov x24,x25`. `cf34` extends
this to F3. Every kernel invocation reloads its own current phase; nothing is
cached across calls. Arithmetic, predicates, tensor addresses, output events,
chunk boundaries and state publication are unchanged. Instruction count is
unchanged as well: an existing entry load changes source field, and each row
substitutes one register move for one load. The x25 clobber remains declared.

## Linked-code audit

The actual uninstrumented linked benchmarks retain the same **43,640** instruction
addresses. Exactly **three** opcode/operand positions change in cf4 (one entry
load and two row-tail expansions), and exactly **five** in cf34. Every other
opcode word and operand text matches at the same address, including all FMOPA,
FMLA, branches, loads/stores of tensor data and carry operations.
The checker requires the exact 120-to-216 entry-offset change and load-to-move
substitutions; it does not merely count changed instructions.
[Audit](../../results/v56/experiments/fold-param/compiler_audit.txt).

From the previous accepted-baseline runtime profile (1585554, DDR round0,
timed call3), dividing pair tile steps by 4*KW yields 781,488 pair-row iterations
for KH41, 843,876 for KH55 and 1,676,740 for KH81. Those main regions are F4/F3/F4,
respectively. These counts include chunk warmup work and estimate how many phase
loads cf34 removes per convolution call for the observed plan. They are not
measurements of latency, cache misses or DRAM traffic, and do not imply a speedup.

## Completed server tests: neither control adopted

Screening **1585684**, cn20483, **08:07:23–08:12:54**, succeeds. Two changed variants each run
five signed bitwise packing-mode sweeps, 224 guards and 54 active-output ownership
cases: all **3,058** state/guard plus **108** ownership cases pass, zero active
conflicts. Six permutations of
baseline/cf4/cf34, four shapes, DDR/HBM and five timings/process give 720 timed
hashes all pass. The strict parser verifies complete logs, hashes and balanced order.
[Screen and all paired ranges](../../results/v56/experiments/fold-param/summary.md).

| Memory | KH | cf4/base | cf34/base |
| --- | ---: | ---: | ---: |
| DDR | 39 | -0.16% | -0.08% |
| DDR | 41 | -0.20% | -0.24% |
| DDR | 55 | -0.05% | -0.04% |
| DDR | 81 | +0.23% | -0.06% |
| HBM | 39 | -0.15% | -0.06% |
| HBM | 41 | +0.02% | +0.07% |
| HBM | 55 | +0.02% | +0.01% |
| HBM | 81 | -0.17% | -0.11% |

Neither is adopted. All DDR shapes regress with cf34; cf4 regresses three DDR
shapes and HBM39/81. Its DDR81 gain is positive in all six paired rounds but
does not offset this broader result. Raw outliers remain, and observed ranges
are not confidence intervals. There is no reason to advance these sources to
original-reference or package acceptance on this evidence.

Attribution **1585708**, cn20481, **08:09:47–08:10:43**, succeeds. It compares
three variants on KH41/55/81, three cyclic orders and both placements: **54**
processes, **14,364** worker records and **270** timed hashes validate. The parser
checks table/step conservation and agreement of per-thread regions with aggregate
buckets. DDR KH41 pair time baseline/cf4/cf34 is 4651.394/4656.350/4650.203 us;
KH55 is 6560.069/6560.486/6559.715 us. Removing the repeated phase load does not
produce a consistent pair-region decrease. HBM81 has small decreases, alongside
changes in other regions and completion spread.
[Profile summary](../../results/v56/experiments/fold-param/profile_summary.md).
Region clocks include setup and ZA restore and change the instrumented source;
their values are not arithmetic-only instruction timings or production gains.
Together with screening, this does not support the repeated CF0 load as an
actionable large bottleneck. No physical latency-hiding mechanism is inferred.

Root source and release archives remain unchanged. The original compile command,
reference benchmark, complete per-call coefficient packing and prior bounds/
ownership/capacity fixes remain in every candidate. External concurrent callers,
allocation failure and fixed 64-byte SVL limitations still apply. No push.
