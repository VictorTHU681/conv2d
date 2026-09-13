#!/usr/bin/env python3
"""Keep thread-start allocation covered by the shared piece capacity."""
from pathlib import Path
import hashlib, subprocess
root = Path('build/v56/experiments/plan-capacity')
root.mkdir(parents=True, exist_ok=True)
base = subprocess.check_output(['git', 'show', '8629457:conv2d.c'], text=True)
assert hashlib.sha256(base.encode()).hexdigest() == '1d3f5071d51cd4f8c88720b8d4fa91983515ffd83bdeb4983377a991df2b871a'
old = 'P->pstart = malloc((nth + 1) * sizeof(int));'
new = 'P->pstart = malloc(need * sizeof(int));'
assert base.count(old) == 1
fixed = base.replace(old, new)
for name, data in [('baseline.c', base.encode()), ('capacity.c', fixed.encode()),
                   ('v55.c', subprocess.check_output(['git', 'show', '0a39770:conv2d.c'])),
                   ('bench_conv.c', subprocess.check_output(['git', 'show', 'd2b65c4:bench_conv.c']))]:
    p = root / name
    p.write_bytes(data)
    print(hashlib.sha256(data).hexdigest(), p)
