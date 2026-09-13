#!/usr/bin/env python3
"""Require identical linked text layout and only intended arithmetic permutations."""
from pathlib import Path
from collections import Counter
import hashlib,re
root=Path('build/v56/experiments/fold-schedule')
def instructions(name):
    raw=(root/(name+'.dis')).read_bytes()
    print(name+'.dis SHA256 '+hashlib.sha256(raw).hexdigest())
    rows={}
    for line in raw.decode().splitlines():
        m=re.match(r'^\s*([0-9a-f]+):\s+([0-9a-f]{8})\s+(.+)$',line)
        if m: rows[int(m[1],16)]=(m[2],m[3])
    assert len(rows)>10000
    return rows
base=instructions('baseline')
for name,expected in [('f4',3),('f34',5)]:
    changed=instructions(name)
    assert changed.keys()==base.keys(), 'instruction addresses changed'
    diffs=[addr for addr in base if base[addr]!=changed[addr]]
    assert diffs
    # Each macro expansion has exactly one contiguous arithmetic region. Group
    # changed rows allowing unchanged arithmetic rows within the same region.
    groups=[]
    for addr in diffs:
        if not groups or addr-groups[-1][-1]>16: groups.append([])
        groups[-1].append(addr)
    assert len(groups)==expected,(name,len(groups))
    for group in groups:
        addresses=range(group[0],group[-1]+4,4)
        old=[base[a] for a in addresses];new=[changed[a] for a in addresses]
        assert Counter(old)==Counter(new)
        assert all(op.split()[0] in ('fmopa','fmla') for _,op in old)
        for opcode in ('fmopa','fmla'):
            assert [x for x in old if x[1].startswith(opcode+'\t') or x[1].startswith(opcode+' ')]==[x for x in new if x[1].startswith(opcode+'\t') or x[1].startswith(opcode+' ')]
        print(f'{name} permutation {group[0]:x}..{group[-1]:x}: {len(group)} changed instruction positions')
    print(f'{name}: {len(base)} linked instruction positions identical; {len(diffs)} positions differ only by checked arithmetic permutations. All other opcode words and operand text unchanged.')
print('This controls emitted text layout; it does not prove a physical execution-port cause or runtime speedup.')
