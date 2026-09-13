#!/usr/bin/env python3
"""Verify final linked instruction permutations without changing any other code."""
from pathlib import Path
from collections import Counter
import hashlib,re
root=Path('build/post63/k5-copy-order')
def read(name):
    raw=(root/(name+'.dis')).read_bytes()
    print(name,'disassembly SHA256',hashlib.sha256(raw).hexdigest())
    rows={};owners={};symbol=None
    for line in raw.decode().splitlines():
        m=re.match(r'^[0-9a-f]+ <([^>]+)>:$',line)
        if m:symbol=m[1]
        m=re.match(r'^\s*([0-9a-f]+):\s+([0-9a-f]{8})\s+(.+)$',line)
        if m:
            a=int(m[1],16);rows[a]=(m[2],re.sub(r'\s+',' ',m[3]).strip());owners[a]=symbol
    assert len(rows)>10000
    return rows,owners
base,owners=read('baseline')
for name in ['early','spread']:
    rows,symbols=read(name)
    assert rows.keys()==base.keys() and symbols==owners
    changed=[a for a in base if rows[a]!=base[a]]
    assert 0<len(changed)<=45 and all(owners[a]=='k5' for a in changed)
    assert Counter(base[a] for a in changed)==Counter(rows[a] for a in changed)
    old_fma=[row for a,row in base.items() if owners[a]=='k5' and row[1].startswith('fmopa ')]
    new_fma=[row for a,row in rows.items() if owners[a]=='k5' and row[1].startswith('fmopa ')]
    assert old_fma and new_fma==old_fma
    print(f'{name}: all {len(base)} instruction addresses match; {len(changed)} changed positions exclusively inside K5, same opcode/operand multiset. All remaining instructions match.')
    print(f'{name}: all {len(old_fma)} K5 FMOPA instructions retain identical opcode/operand sequence; addresses within the permuted loop can move.')
    print(f'{name}: changed region 0x{min(changed):x}..0x{max(changed):x}.')
print('This proves linked instruction identity/order properties, not absence of every possible memory or concurrency fault; live correctness and performance are validated separately.')
