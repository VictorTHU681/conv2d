#!/usr/bin/env python3
"""Isolate K5 output/clear ordering without altering work or linked code size."""
from pathlib import Path
from collections import Counter
import hashlib
import subprocess

root = Path('build/post61/k5-events')
root.mkdir(parents=True, exist_ok=True)
base = subprocess.check_output(['git', 'show', 'b3140af:conv2d.c'], text=True)
assert hashlib.sha256(base.encode()).hexdigest() == '2c4065478f8d40c194c996ede4fcdbd65f80c0a1c5e9b057b32889035d788ada'
def asm(ops):
    return ''.join('        "' + op + '\\n\\t"\n' for op in ops)

reads = [[f'mova z{j}.s, p0/m, za{t}v.s[w12, {j}]' for j in range(3)] for t in range(4)]
clears = [[f'mova za{t}v.s[w12, {j}], p0/m, z31.s' for j in range(3)] for t in range(4)]
stores = [[f'st3w {{z0.s, z1.s, z2.s}}, p0, [x20, #{3*t}, mul vl]'] for t in range(4)]
original = sum([reads[t] + stores[t] + clears[t] for t in range(4)], [])
clear_first = sum([reads[t] + clears[t] + stores[t] for t in range(4)], [])
defer_clear = sum([reads[t] + stores[t] for t in range(4)], []) + sum(clears, [])
assert base.count(asm(original)) == 1
for name, ops in [('baseline', original), ('clearfirst', clear_first), ('deferclear', defer_clear)]:
    assert len(ops) == 28 and Counter(ops) == Counter(original)
    # Every tile is read before it is cleared, and stored before z0..2 are reused.
    for t in range(4):
        assert max(ops.index(x) for x in reads[t]) < min(ops.index(x) for x in clears[t])
        assert max(ops.index(x) for x in reads[t]) < ops.index(stores[t][0])
        if t < 3:
            assert ops.index(stores[t][0]) < min(ops.index(x) for x in reads[t+1])
    s = base.replace(asm(original), asm(ops))
    assert s.replace(asm(ops), asm(original)) == base
    p = root / (name + '.c')
    p.write_text(s)
    print(hashlib.sha256(p.read_bytes()).hexdigest(), p)
(root/'fbench.c').write_bytes(subprocess.check_output(['git', 'show', '8b6b295:tools/fbench.c']))
assert hashlib.sha256((root/'fbench.c').read_bytes()).hexdigest() == 'e5e52c8d666584cc49ca6f11162be4868b240e2cc99a3c3ef0a2f8ac292c65ad'
dest = Path('results/post61/k5-events')
dest.mkdir(parents=True, exist_ok=True)
sources = [root/(name+'.c') for name in ['baseline', 'clearfirst', 'deferclear', 'fbench']]
(dest/'sources.sha256').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p}\n' for p in sources))
print('Only the 28 K5 output-event instructions are permuted; dataflow and instruction multiset validate. No arithmetic, source/output addresses, branches, scheduling, packing or other kernel changes.')
