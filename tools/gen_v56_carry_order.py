#!/usr/bin/env python3
"""Test ZA restore placement around scalar parameter construction."""
from pathlib import Path
import hashlib
import subprocess

root = Path('build/v56/experiments/carry-order')
root.mkdir(parents=True, exist_ok=True)
source = subprocess.check_output(['git', 'show', '8629457:conv2d.c'], text=True)
assert hashlib.sha256(source.encode()).hexdigest() == '1d3f5071d51cd4f8c88720b8d4fa91983515ffd83bdeb4983377a991df2b871a'
a = source.index('static void roll_worker(')
b = source.index('\nstatic void roll_diag_print(', a)
worker = source[a:b]
restore = '        if (off) carry_load_za(state); else sme_zero_za();'
stamp = '        uint64_t t0 = g_roll_diag ? cyc() : 0;'
anchor = '        float* state = P->carry + (size_t)pi * 1152;'
assert all(worker.count(x) == 1 for x in [restore, stamp, anchor])
for name in ['baseline', 'early', 'load_early']:
    candidate = source
    if name != 'baseline':
        w = worker.replace(stamp + '\n', '')
        if name == 'early':
            w = w.replace(restore + '\n', '')
            before = restore
        else:
            w = w.replace(restore, '        if (!off) sme_zero_za();')
            before = '        if (off) carry_load_za(state);'
        # The diagnostic kernel region retains restore/zero and setup costs.
        # No other ZA-writing operation occurs during scalar argument setup.
        w = w.replace(anchor, anchor + '\n' + stamp + '\n' + before)
        assert w.count('carry_load_za(state)') == 1
        assert w.count('sme_zero_za()') == 1
        assert w.index('carry_load_za(state)') < w.index('kp_t K =')
        candidate = source[:a] + w + source[b:]
        assert candidate[:a] == source[:a] and candidate.endswith(source[b:])
    p = root / f'{name}.c'
    p.write_text(candidate)
    print(hashlib.sha256(p.read_bytes()).hexdigest(), p)
p = root / 'fbench.c'
p.write_bytes(subprocess.check_output(['git', 'show', '8b6b295:tools/fbench.c']))
assert hashlib.sha256(p.read_bytes()).hexdigest() == 'e5e52c8d666584cc49ca6f11162be4868b240e2cc99a3c3ef0a2f8ac292c65ad'
print(hashlib.sha256(p.read_bytes()).hexdigest(), p)
