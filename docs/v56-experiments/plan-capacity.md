# Thread-start allocation must match its growth guard

Review found a concrete heap overflow in accepted source **8629457 / 1d3f5071**.
`roll_prepare` jointly reallocates `pieces` and `pstart` when `pcap < need`, where
`need = 2*nit + 2*nth + 4`. However, `pstart` receives only `nth+1` integers.
A later sequential call can increase threads while reducing strip count enough
to keep `need <= pcap`. It then writes `pstart[0..nth]` beyond the old allocation.
This does not require concurrent external callers or allocation failure.
The same allocation is present in published v55 `0a39770`; this is an inherited
defect, not introduced by the current phase/carry optimization.

The host regression extracts actual grouping, dependency linking and the entire
`roll_prepare` from each immutable source. First call: KH41/KW13, OH534/OW8192,
nth1, yielding nit299/pcap604 but only two allocated thread-start entries.
Second call: same KH/KW/OH, OW512, nth38. ASan reports a four-byte heap write
immediately beyond that eight-byte allocation in `roll_prepare`.
[Positive control](../../results/v56/experiments/plan-capacity/host_baseline.txt).
This is not a synthetic reimplementation of the capacity logic; SME instructions
are excluded, allocation alignment is supplied by a host helper, and leak checking
is disabled because the source intentionally retains persistent buffers.

Candidate **ebf36923518cb809ae5e65001a700de30b0415956f1d0420a2dffcae45684026**
changes just `pstart = malloc((nth+1)*sizeof(int))` to allocate `need` integers.
Thus the same `pcap` guard covers both arrays; a reused capacity is at least
the current need, and need is greater than nth+1 for supported positive plans.
No structure layout, kernel, math order, packing, dependencies or scheduling
calculation changes. The extra memory is four bytes per capacity slot, rather
than only per thread. Allocation-failure handling remains a separate limitation.

GCC 12.3.1 `-O3 -fopenmp -S` comparison, after removing only `.file` and inline
assembly source-location comments, differs in one allocation block. The emitted
instruction text elsewhere is identical. [Compiler diff](../../results/v56/experiments/plan-capacity/compiler_diff.txt)
preserves assembly hashes and that complete diff; linked addresses, allocation
placement and runtime effects are not inferred from identical instruction text.

The fixed extracted source passes **482** shape/thread transitions under
ASan/UBSan, including 1/2/3/7/38/64 threads, KH16/39/41/55/57/81/249/256,
changing widths/heights, complete contiguous per-item row coverage and monotone
thread boundaries. [Fixed run](../../results/v56/experiments/plan-capacity/host_capacity.txt).
The old source is required to fail specifically with the expected ASan write.

Actual server acceptance **1585376**, cn20481, started 07:38:10. It tests 24
shape/thread changes in each of OpenMP and pool-enabled modes, five packing-mode
state sweeps (1,305 cases), 224 guards, then six alternating rounds against
published v55 with the unchanged original benchmark: 96 full checks planned.
The fresh direct-v55 comparison prevents reusing the old source's performance
table as if it described this repair. Package job **1585377**, cn20483, started
07:38:11, completes 07:41:27: all three staged archives pass 12 full checks with
zero maximum error. Expected four members and server/local hashes match.
[Archive audit](../../results/v56/experiments/plan-capacity/archive_audit.txt).
Job 1585376 completes 07:47:47: all 48 actual shape/thread transitions, 1,305
state cases, 224 guards and 96 original full-reference checks pass, maximum error
zero. The strict parser checks hashes, dimensions, all rows and 3 AB/3 BA orders.
[Full direct-v55 summary](../../results/v56/experiments/plan-capacity/summary.md).

Fresh direct-v55 KH39/41/55/81: DDR +1.63%/+4.40%/+1.45%/+2.29%; HBM
-0.43%/+1.10%/+1.04%/+2.40%. DDR39 has one negative paired round; HBM39 has
five. Other shape/memory combinations are positive in all six rounds. Observed
ranges retain every outlier and are not confidence intervals. These are direct
comparisons to published v55, not performance attribution to the allocation fix.

**Adopted** as root source ebf36923. Root archive program members match the tested
staged candidates; README is updated. Adoption repairs the demonstrated overflow,
not a claimed incremental speedup over 1d3f5071. No push.

This bug was not exposed by the fixed-38-thread problem commands. Its existence
is a correctness finding, not proof of deliberate benchmark cheating. Existing
HBM/diagnostic-package rule limitations and external-call concurrency limitations
remain. No blanket compliance or all-input safety claim is made.
