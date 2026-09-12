# Modular phase setup and ZA carry controls

Unpublished local v56 experiment based on accepted 8b6b295 / bb82ce3b…6819.
Root operator and accepted packages remain unchanged. No push.

[Phase attribution](chunk-overhead.md) measures ~63–65 us/thread parameter
setup at short2 versus ~16–18 us at step8. The generated GCC worker contains
repeated signed divisions for adjacent normalized phases. ZA state transfer
also becomes more frequent with short chunks.

Four isolated candidates:
- baseline: accepted source;
- phase: compute ja % KH once, derive neighboring row counters and folded
  coefficient phases through bounded subtraction/addition;
- carry4: transfer four adjacent 64-byte ZA slices per iteration with immediate
  slice/address offsets, advancing base/index by 256 bytes/four rows;
- both: combine the two changes.

The phase helper takes a,b in [0,KH), returns (a-b) modulo KH using at most one
addition. The B phase is A-16 modulo KH; rolling selection guarantees KH>=16.
All arithmetic kernels, group planning, packing, claim and output dependencies
remain byte-identical. Every coefficient is still rebuilt each call; no exact
public-shape or call-stage selection is added. ZA still transfers all 64 slices
with the existing acquire/release publication ordering. Target SVL remains 64
bytes, the same previously documented limitation.

Host UBSan equivalence test passes **22,495,904** cases: KH16..256, all normalized
row/group phases, four row quotients including 65,537. The helper in the host
test is asserted byte-identical to the generated candidate. This proves the
sampled modular identities; it does not replace server integration checks.
The combined source compiles with server GCC12.3.1/binutils2.41; no compute-node
execution was attempted on the login node.

Job **1583712**, started on cn20481 at 05:09:21 and is still running. Planned checks are
2,984 signed state/guard cases (four candidates, plus all packing modes for
both), 54 runtime output-ownership cases and 640 timed hashes in four balanced
Williams orders. Correctness uses step1 to stress continuation. Performance
uses the accepted structural default (step2 only for K5). No performance or
integration-correctness result is yet claimed.

[Source hashes](../../results/v56/experiments/chunk-setup/sources.sha256),
[host equivalence](../../results/v56/experiments/chunk-setup/phase_check.txt).
