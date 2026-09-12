#!/usr/bin/env python3
"""Stage the upstream-gate integration without replacing accepted archives."""
from pathlib import Path
import shutil
import subprocess
import argparse

parser=argparse.ArgumentParser()
parser.add_argument('--experiment',choices=['upstream-gate','kf-share','k5-layout','k5-default','piece-carry'],default='upstream-gate')
args=parser.parse_args()
root=Path('build/v56/experiments')/args.experiment;stage=root/'package'
(stage/'tools').mkdir(parents=True,exist_ok=True)
(stage/'submissions').mkdir(exist_ok=True)
shutil.copyfile(root/({'k5-layout':'triplet.c','k5-default':'short2.c','piece-carry':'combined.c'}.get(args.experiment,'merged.c')),stage/'conv2d.c')
for name in ['bench_conv.c','run.sh','run_diag.sh','tools/mkdiag.py','tools/package_v56.py']:
    shutil.copyfile(name,stage/name)
readme='''# Local v56 upstream F4 gate integration candidate

Integrates upstream 87fa5d7's long-row F4 copy overlap and alignment gate.
Retains local K9 reuse, bounded input copies, unique coefficient-pack writers,
row-chunk output dependencies, and integer warmup output-address arithmetic.
Each call rebuilds coefficients and computes complete FP32 outputs.

Original build: gcc -O3 bench_conv.c conv2d.c -o conv2d_test -lm -fopenmp
Original placement: OMP_NUM_THREADS=38 numactl -N 1 ./conv2d_test H W KH KW 5
run.sh retains optional HBM preferred placement; CONV_HBM=0 disables it.
That extra placement is not explicitly authorized in the saved problem statement.
conv.zip is the normal candidate; conv_nf3.zip is a three-chain control.
conv_diag.zip contains call-stage/environment probes and is diagnostic-only.
This unpublished integration is undergoing acceptance, not yet adopted.
External concurrent callers, allocation failures and other SVL hardware remain
outside the validated scope. K5 experiments are not included.
'''
if args.experiment=='kf-share':
    readme=readme.replace('upstream F4 gate integration candidate','shared folded coefficient tables candidate').replace(
        "Integrates upstream 87fa5d7's long-row F4 copy overlap and alignment gate.",
        "Integrates upstream 76ec03d's within-call sharing of equal folded coefficient tables.\nOnly each table owner writes; consumers wait for its group to publish completion.\nThe accepted F4 gate remains in place; the K9 weight default stays 140.")
elif args.experiment in ('k5-layout','k5-default'):
    readme=readme.replace('upstream F4 gate integration candidate','K5 residual folding candidate').replace(
        "Integrates upstream 87fa5d7's long-row F4 copy overlap and alignment gate.",
        "Retains the accepted F4 gate and adds a structural 36+5 residual grouping.\nFive-row tails use three interleaved column classes and exact KW+2 execution.\nThis selects the ordinary K5 source; F4 outlining and cost controls are excluded.")
    readme=readme.replace('outside the validated scope. K5 experiments are not included.',
                         'outside the validated scope. Rejected kf sharing is not included.')
if args.experiment=='k5-default':
    readme=readme.replace('K5 residual folding candidate','K5 short continuation candidate').replace(
        'This selects the ordinary K5 source; F4 outlining and cost controls are excluded.',
        'Only prepared plans containing K5 select continuation step 2; other plans retain 8.\nCONV_ROLL_STEP overrides remain available. No memory-placement detection is added.\nDDR KH41 benefits; HBM KH41 regresses slightly. Both are reported separately.')
if args.experiment=='piece-carry':
    readme='''# Local v56 prepared phases and four-slice ZA candidate

Retains the accepted K5-only short continuation default, K5/F4/K9 kernels,
bounded input copies, unique coefficient writers and output-row dependencies.
Each call prepares four shape-only phase bytes per piece in former padding;
piece size and scheduler field offsets stay unchanged. All coefficients and
outputs are recomputed each call. ZA save/restore advances four 64-byte slices
per iteration, preserving all 64 slices and acquire/release publication.

Original build: gcc -O3 bench_conv.c conv2d.c -o conv2d_test -lm -fopenmp
Original placement: OMP_NUM_THREADS=38 numactl -N 1 ./conv2d_test H W KH KW 5
run.sh retains optional HBM preferred placement; CONV_HBM=0 disables it.
That extra placement is not explicitly authorized in the saved problem statement.
conv.zip is the normal candidate; conv_nf3.zip is a three-chain control.
conv_diag.zip contains call-stage/environment probes and is diagnostic-only.
This unpublished candidate is undergoing acceptance, not yet adopted.
External concurrent callers, allocation failures and other SVL hardware remain
outside the validated scope. No F3/F4 outlining, layout padding or K4 EXT change.
'''
(stage/'README.md').write_text(readme)
subprocess.run(['python3',str(stage/'tools/package_v56.py')],check=True)
