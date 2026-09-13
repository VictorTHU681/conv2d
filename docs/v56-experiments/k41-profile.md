# v56 investigation — K41 first-copy cost and worker hotspots

Baseline is current local v56 `93163b4:conv2d.c`, SHA-256
`595d7f7d88dd9bfe2ddbbff6fb50251ade05692ad876a88926999ca194102339`.
`previous` is the earlier v56 checkpoint `72b10c2`, before its first-copy
boundary correction. Main was pulled at the start and remained published
v55 `8ce8af2`; no push. This round does not change production or archives.

## Questions and measurement separation

The previous official comparison found a 0.87% DDR / 0.35% HBM K41 regression
from the first-copy correction. The changed helper runs once per resumed
row block, whereas the K33/K8 inner loops execute many times. Measure the
helper directly before assuming its unaligned first-row loads cause the
whole regression, and inspect instruction placement as an independent factor.

`tools/gen_v56_k41_profile.py` produces separate phase builds. It times host
preparation, per-call coefficient packing and worker work using actual
CNTFRQ. Thread-local counters time the first-copy helper and count bytes;
per-thread counters are saved after worker completion. These diagnostic
builds change layout and add timer/counter overhead. Their timings are useful
for cost scale and phase distribution, not as uninstrumented speed claims.

## Sampling failure and correction

Job **1582107**, cn20483, 2026-09-13 01:03:08–01:08:40, completes DDR phase
measurements but the old FIFO enable/disable sampling protocol inflates an
approximately 6-ms call to **1,695.408 ms average**. Its raw sample file grows
to over 600 MiB. The job was deliberately terminated after this concrete
measurement artifact was observed; scheduler status is FAILED. The sampling
result is rejected, not counted as a performance result or silently retried.
Raw samples remain on the server; the useful phase log is retained locally.

Replacement **1582153**, cn20483, 01:09:08–01:10:12, SUCCEEDED. It reruns
three alternating phase processes per version/memory, then samples separate
uninstrumented binaries at **99 Hz**, continuously over a 200-call steady-
allocation workload. It also runs an unsampled steady control. This sampling
covers initialization/warmup and worker waiting as well as convolution;
it is not the official allocation/timing protocol. Sampling adds about
4.96–5.92% runtime in the observed controls, so it is used for broad hotspots,
not to measure sub-percent speed differences. All reports have zero lost
samples. The 60 timed hashes in the phase processes pass.

## Measured phase costs

Medians of the five timed calls in each of three diagnostic processes (15
samples per cell), excluding each process's validation and warmup calls:

| Memory | Variant | Prepare us | Host pack us | Workers us | Mean first copy us/thread | First copy % |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| DDR | previous | 6.8400 | 25.9800 | 6061.8200 | 3.6750 | 0.0613 |
| DDR | baseline | 6.6700 | 26.2800 | 6072.3600 | 3.2880 | 0.0543 |
| HBM | previous | 6.7100 | 24.4100 | 5843.9800 | 2.8410 | 0.0490 |
| HBM | baseline | 6.4400 | 24.6500 | 5843.0100 | 2.4780 | 0.0427 |

Sampling overhead control (steady allocation; not official timings):
DDR previous: 6.1266 -> 6.4890 ms (+5.92% with 99-Hz sampling)
DDR baseline: 6.1533 -> 6.4583 ms (+4.96% with 99-Hz sampling)
HBM previous: 5.8858 -> 6.2299 ms (+5.85% with 99-Hz sampling)
HBM baseline: 5.9147 -> 6.2227 ms (+5.21% with 99-Hz sampling)

The corrected source's first-copy helper accounts for only **0.0543% DDR /
0.0427% HBM** of accumulated worker time. Both variants make 3,053 helper
calls per convolution; correcting the span reduces aggregate copied bytes
from 1,165,488 to 1,115,424. In these instrumented controls the helper gets
slightly cheaper, not more expensive. There is no evidence here that the
helper's own copy work explains the prior whole-call regression.

Host packing is about 25–26 us against approximately 5.84–6.07 ms workers.
Within timed kernels, the K33 paired kernel accounts for about **78.5–78.8%**
and K8 about **21.2–21.5%**. The printed legacy cycle counts are normalized
to 1.55 GHz; the cost shares and first-copy microseconds use actual timer
frequency and are the evidence used here.

## Uninstrumented sample distribution

For corrected v56, `roll_worker` receives **96.60% DDR / 97.00% HBM** of
sampled periods; `pool_worker` receives 3.10% / 2.82%, and
`fill_args.constprop.0` 0.20% / 0.10%. Within roll_worker, the largest sample
locations are K33's second input-vector load and first packed-coefficient
load: 40.13% + 14.47% DDR; 43.06% + 12.19% HBM of roll_worker sample periods.
The previous source shows the same broad pattern. These locations do not
mean those individual instructions themselves consume that fraction of
runtime; they identify a region for controlled load/scheduling experiments.

Disassembly shows that the 17-instruction K33 loop shifts from offset **96**
to **112 modulo 128** between previous and corrected sources. The opcodes
and arithmetic within that loop are unchanged. This motivates a placement
control but does not alone prove a front-end bottleneck. See
[k33-align.md](k33-align.md) and [k33-schedule.md](k33-schedule.md).

## Decision and next direction

Keep the input-boundary correction. Do not spend further optimization effort
on this tiny first-copy phase as the main K41 bottleneck. The repeated K33
input/coefficient load and multiply-add loop is the dominant measured region.
Alignment and early scalar-coefficient controls below yield insufficient
benefit, so none is promoted. The next concrete hypothesis is reuse of
aligned input windows across KW steps, replacing repeated shifted vector
loads with register rearrangement while preserving FMA order and exact input
bounds. This is a proposed experiment, not an implemented speedup or a claim
that the precise microarchitectural cause is already established.

Evidence: `results/v56/experiments/k41-profile/`; summarize with
`python3 tools/summarize_v56_k41_profile.py`. Full raw disassembly/perf data
remain on the server; local reports, annotations and K33 excerpts are retained.
