#!/usr/bin/env python3
"""Require identical linked addresses and only K5 event instruction permutations."""
from pathlib import Path
from collections import Counter
import hashlib
import re

root = Path('build/post61/k5-events')
def read(name):
    raw = (root/(name+'.dis')).read_bytes()
    print(name, 'disassembly SHA256', hashlib.sha256(raw).hexdigest())
    rows, owners = {}, {}
    symbol = None
    for line in raw.decode().splitlines():
        m = re.match(r'^[0-9a-f]+ <([^>]+)>:$', line)
        if m:
            symbol = m[1]
        m = re.match(r'^\s*([0-9a-f]+):\s+([0-9a-f]{8})\s+(.+)$', line)
        if m:
            a = int(m[1], 16)
            rows[a] = (m[2], re.sub(r'\s+', ' ', m[3]).strip())
            owners[a] = symbol
    assert len(rows) > 10000
    return rows, owners
base, owners = read('baseline')
for name in ['clearfirst', 'deferclear']:
    rows, symbols = read(name)
    assert rows.keys() == base.keys() and symbols == owners
    changed = [a for a in base if base[a] != rows[a]]
    assert 0 < len(changed) <= 28
    assert all(owners[a] == 'k5' for a in changed)
    assert Counter(base[a] for a in changed) == Counter(rows[a] for a in changed)
    assert all(base[a][1].split()[0] in ['mova', 'mov', 'st3w'] for a in changed)
    for a in changed:
        print(f'{name} {a:x}: {base[a][1]} -> {rows[a][1]}')
    print(f'{name}: all {len(base)} linked instruction addresses match; only {len(changed)} K5 event positions differ, as a pure permutation. All remaining opcode words/operands match.')
