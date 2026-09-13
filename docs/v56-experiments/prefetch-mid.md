# Check distances 4 and 5 around the accepted default

Sweep 1585771 rejects joint distances1/2/6 for broad adoption and retains 3;
split attribution 1585839 shows that shortening input lead accounts for the
large loss. This does not establish that 3 is optimal among untested settings.
The present control tests distances **3/4/5** on the unchanged accepted source
**3df5c69 / ebf36923**, one executable for all settings. It includes none of the
split diagnostic source changes or rejected arithmetic/phase-register changes.

Job **1585891**, cn20481, **08:27:30–08:30:54**, succeeds. Three signed state sweeps (783 cases),
three guard sweeps (672 cases), all six permutations, four shapes, separate
DDR/HBM and five timings per process: **1,455** state/guard and **720** timed
hashes all pass. Each setting occupies each position twice; every ordered
adjacent pair occurs twice. The parser checks hashes, settings, full balanced
orders and dimensions, all timing rows, and completion marker. The downloaded
post-run executable matches its pre-run logged hash; [binary audit](../../results/v56/experiments/prefetch-mid/binary_audit.txt).
[Summary and all paired ranges](../../results/v56/experiments/prefetch-mid/summary.md).

| Memory | KH | Distance4 / 3 | Distance5 / 3 |
| --- | ---: | ---: | ---: |
| DDR | 39 | -0.48% | -0.95% |
| DDR | 41 | -0.85% | -2.38% |
| DDR | 55 | +0.03% | -0.14% |
| DDR | 81 | -1.43% | -2.24% |
| HBM | 39 | +0.01% | -0.19% |
| HBM | 41 | -1.00% | -1.74% |
| HBM | 55 | -0.13% | -0.35% |
| HBM | 81 | -1.56% | -2.31% |

Both settings lose all six paired rounds on KH41/81 in both placements. The
small DDR55 distance4 change is mixed across pairs and reverses in HBM. **Neither
is adopted.** Together with the prior 1/2/6 scan this supports retaining default3
among the tested settings 1–6 for these four shapes; it is not a global optimum
proof for all valid shapes or memory systems. No original-reference/package
acceptance is warranted for these rejected parameter settings. Raw outliers
remain and their observed ranges are not confidence intervals.

Only the existing joint CONV_ROLL_PD knob changes. Input and output hints both
change, so any benefit still needs independent confirmation and should not be
attributed to a specific cache mechanism solely from these times. Default/source/
packages remain unchanged after completion. No push.
