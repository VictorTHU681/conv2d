#!/usr/bin/env python3
"""Build and statically audit isolated v62 plus zero-prefix acceptance archives."""
from pathlib import Path
import hashlib
import shutil
import subprocess
import zipfile

root = Path('build/post63/k5-prefix')
stage = root/'package_exact'
out = Path('results/post63/k5-prefix')
source = (root/'exact.c').read_bytes()
digest = '4770f22802002d38dc66f54e0d829a2363aaa171534d1d9964561291b6310156'
assert hashlib.sha256(source).hexdigest() == digest
assert hashlib.sha256(Path('bench_conv.c').read_bytes()).hexdigest() == '2548861ae7e29826e454b4c0b098d682f7f04996222e664cd1ea9bc92dd2e927'
(stage/'tools').mkdir(parents=True, exist_ok=True)
(stage/'submissions').mkdir(exist_ok=True)
(stage/'conv2d.c').write_bytes(source)
for name in ['bench_conv.c','run.sh','run_diag.sh','tools/mkdiag.py','tools/package_v56.py']:
    shutil.copyfile(name, stage/name)
(stage/'README.md').write_text(f'''# Local K5 zero-prefix composition candidate

Source SHA256: {digest}
The published v62/v63 K5 copy-interleave and output-prefetch kernel is retained;
only the K5 input-plane prefix becomes zero. Inline assembly, coefficient
construction, accumulation order and logical input/output mapping are unchanged.
There is no runtime experiment knob or new result cache.

Original build: gcc -O3 bench_conv.c conv2d.c -o conv2d_test -lm -fopenmp
Original benchmark and existing run scripts are unchanged. run.sh retains
optional static-topology HBM placement. DDR/HBM are reported separately.
conv.zip is the normal candidate; conv_nf3.zip is a three-chain control;
conv_diag.zip contains probes and is diagnostic-only.
This isolated archive is for local acceptance, not a published release.
External concurrent callers, unchecked allocation failures and other SVL values
remain outside the validated scope; no blanket safety/compliance claim is made.
''')
report = subprocess.check_output(['python3', str(stage/'tools/package_v56.py')], text=True)
manifest = []
for line in report.splitlines():
    h, relative = line.split(maxsplit=1)
    assert len(h)==64 and Path(relative).parent==Path('submissions')
    manifest.append(f'{h}  {stage/relative}\n')
(out/'packages_candidate.sha256').write_text(''.join(manifest))
variants = {'conv': (source,'run.sh'),
            'conv_nf3': (source.replace(b'#define CONV_NF_REM7 0',b'#define CONV_NF_REM7 3'),'run.sh'),
            'conv_diag': ((stage/'build/v56/release_diag.c').read_bytes(),'run_diag.sh')}
checks = []
for name,(operator,script) in variants.items():
    expected = {'conv/conv2d.c':operator,'conv/bench_conv.c':(stage/'bench_conv.c').read_bytes(),
                'conv/run.sh':(stage/script).read_bytes(),'conv/README.md':(stage/'README.md').read_bytes()}
    with zipfile.ZipFile(stage/'submissions'/f'{name}.zip') as z:
        assert len(z.namelist())==4 and set(z.namelist())==set(expected)
        for member,data in expected.items(): assert z.read(member)==data,(name,member)
    checks.append(f'{name}: all four members match intended source, original benchmark, existing script and candidate README.')
(out/'package_static_audit.txt').write_text('\n'.join(checks)+'\n')
print(''.join(manifest),end='')
print('\n'.join(checks))
