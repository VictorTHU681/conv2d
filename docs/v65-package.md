# conv2d v65 — PAIRF3 compute-loop unroll

This release is based on upstream 138dcac and keeps the v64 K5 optimization.
Normal operator SHA-256:
f88b3f90295fd5ad5a749016343b266535857b53d2588801f65e18e6c7f2d499

The F3 compute-only suffix runs four ordered steps per full loop block,
reducing pointer and branch overhead. Coefficient packing, overlap copies,
FMA order, leftover steps and per-call state handling remain unchanged.

Build:
    gcc -O3 bench_conv.c conv2d.c -o conv2d_test -lm -fopenmp
Run all four cases:
    bash run.sh

In three original-benchmark comparisons against upstream, KH55 improved
0.10% to 0.49% in DDR and 0.08% to 0.40% in HBM. Other cases fluctuated,
including HBM41 -0.24% and HBM81 -0.20% in individual comparisons.
This is not a claim that every case is faster on every node.
The accepted source passed 1953 state/guard cases; 144 direct full-reference
runs of u4 passed, plus 12 full-reference checks across three package variants.

conv.zip is normal. conv_nf3.zip uses the existing three-chain override.
conv_diag.zip contains diagnostic probes and is for diagnosis only.
The three program files match the server-qualified archives; this README
is the only changed member. The run script retains static NUMA/HBM placement.
Existing limitations include 64-byte streaming vector length, unsupported
external concurrent callers, and incomplete allocation-failure handling.
