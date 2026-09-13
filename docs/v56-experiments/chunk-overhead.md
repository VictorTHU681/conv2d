# Continuation chunk phase attribution

Baseline is accepted local **8b6b295**, source
`bb82ce3b4826514e9ce6f729ef017a23d5aa08d2396f5d0975a512e39da76819`.
The main checkout pulled again and remains at upstream 364b46d. No push.

Job **1583687**, cn20481, succeeded 05:06:24–05:06:50. One instrumented binary
compares CONV_ROLL_STEP 8/2/4 in all six permutations in DDR and HBM. All 180
timed hashes, 9,576 phase records and worker records validate. Every call
processes 916,936 input-row work units across 186 pieces; saves equal resumes.

The additional boundaries measure claim, parameter setup, ZA restore/zero,
kernel invocation, and save/publish. Timings use the architectural counter
with compiler memory barriers, not serialized instruction-level measurements.
Extra counters and changed compiler layout perturb performance; these are
attribution data, not accepted end-to-end timing. Kernel includes its own
initial input-ring copy and vector-state transfers. Publish includes the
existing diagnostic accounting, ZA save and release store.

[Full summary](../../results/v56/experiments/chunk-overhead/summary.md):
short2 averages 295.3 chunks per worker versus 75.4 at step8. Parameter setup
rises from 17.6 to 64.8 us DDR (15.8 to 63.0 us HBM); restore/zero rises
22.0 to 34.1 us DDR and 19.4 to 33.4 us HBM. Save/publish rises 18.6 to
53.2 us DDR and 17.3 to 51.9 us HBM. Claim changes are smaller. This identifies
measurable setup/state overhead but does not prove eliminating it yields an
equal production speedup. It also does not attribute all increased L1 misses.

The immutable baseline roll_worker disassembly confirms repeated SDIV operations
in phase construction and 64-iteration scalar-control ZA load/store loops.
The next [isolated controls](chunk-setup.md) target those two costs separately.
Root operator and accepted packages are unchanged by this diagnostic work.
