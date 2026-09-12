# Local v56 integrated boundary-correction candidate

Combines local K9 register reuse with upstream b9591de packing/copy overlap.
Bounds K8/K9/K4 input copies and removes duplicate concurrent pack writers.
Each call rebuilds coefficients and computes all outputs in FP32.

Original build: gcc -O3 bench_conv.c conv2d.c -o conv2d_test -lm -fopenmp
Original placement: OMP_NUM_THREADS=38 numactl -N 1 ./conv2d_test H W KH KW 5
run.sh retains its existing optional HBM preferred placement; CONV_HBM=0 disables it.
The problem statement does not explicitly authorize that additional placement.

conv.zip is the normal candidate; conv_nf3.zip is a three-chain control.
conv_diag.zip contains call-stage and environment probes, for diagnostics only.
This local candidate is still undergoing formal acceptance and has not been pushed.
The audit does not prove absence of all undefined behavior or concurrent-call safety.
