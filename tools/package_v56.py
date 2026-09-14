#!/usr/bin/env python3
"""Build reproducible four-file submission archives from the locally validated v56 source (no push)."""
from pathlib import Path
import hashlib
import subprocess
import sys
import zipfile

root = Path(__file__).resolve().parent.parent
build = root / 'build' / 'v56'
build.mkdir(parents=True, exist_ok=True)
source = (root/'conv2d.c').read_bytes()
assert source.count(b'#define CONV_NF_REM7 0') == 1
variants = {
    'conv.zip': (source, 'run.sh'),                       # v66 起默认即 rem7=3 链（nf3）
}
for name, (operator, script) in variants.items():
    files = {'conv2d.c': operator, 'bench_conv.c': (root/'bench_conv.c').read_bytes(),
             'run.sh': (root/script).read_bytes(), 'README.md': (root/'README.md').read_bytes()}
    dest = root / 'submissions' / name
    with zipfile.ZipFile(dest, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for filename, content in sorted(files.items()):
            info = zipfile.ZipInfo('conv/' + filename, date_time=(2026, 9, 12, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (0o100755 if filename == 'run.sh' else 0o100644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, content, compresslevel=9)
    print(hashlib.sha256(dest.read_bytes()).hexdigest(), str(dest.relative_to(root)))
