#!/usr/bin/env python3
"""Stage one fixed K5 policy for archive acceptance without changing root files."""
from pathlib import Path
import argparse
import hashlib
import shutil
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--variant', choices=['exact', 'triples'], required=True)
args = parser.parse_args()
root = Path('build/post61/k5-copy-fixed')
stage = root/('package_'+args.variant)
digests = {'exact':'ae525112d6b1b22f9508d5edb862ba923547527012e3477630ff89bc3b5d33c8',
           'triples':'5eede8939a0486c0f740296481e86d4fe8ac387ac1e6a810f019e49e3a815090'}
source = (root/(args.variant+'.c')).read_bytes()
assert hashlib.sha256(source).hexdigest() == digests[args.variant]
assert hashlib.sha256(Path('bench_conv.c').read_bytes()).hexdigest() == '2548861ae7e29826e454b4c0b098d682f7f04996222e664cd1ea9bc92dd2e927'
(stage/'tools').mkdir(parents=True, exist_ok=True)
(stage/'submissions').mkdir(exist_ok=True)
(stage/'conv2d.c').write_bytes(source)
for name in ['bench_conv.c', 'run.sh', 'run_diag.sh', 'tools/mkdiag.py', 'tools/package_v56.py']:
    shutil.copyfile(name, stage/name)
(stage/'README.md').write_text(f'''# Local post-v61 K5 {args.variant} prefix candidate

Source SHA256: {digests[args.variant]}
Only K5 input-plane prefix selection changes from upstream v61. All prior
input bounds, output dependencies, coefficient ownership, capacity repairs,
dependency retry and per-call metadata/coefficient construction are retained.
The runtime layout experiment knob is absent. Floating-point accumulation order
and logical input/output mapping remain unchanged. No result cache is added.

Original build: gcc -O3 bench_conv.c conv2d.c -o conv2d_test -lm -fopenmp
The original benchmark and existing run scripts are unchanged. DDR/HBM are
reported separately; run.sh retains optional static-topology HBM placement.
conv.zip is the normal candidate; conv_nf3.zip is a three-chain control.
conv_diag.zip has diagnostic probes and is diagnostic-only.
This is a local acceptance candidate, not yet a published version.
External concurrent callers, unchecked allocation failures and other SVL values
remain outside the validated scope. No blanket safety/compliance claim is made.
''')
report = subprocess.check_output(['python3', str(stage/'tools/package_v56.py')], text=True)
for line in report.splitlines():
    digest, relative = line.split(maxsplit=1)
    assert len(digest) == 64 and Path(relative).parent == Path('submissions')
    print(digest, stage/relative)
