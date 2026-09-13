#!/usr/bin/env python3
"""Audit every linked instruction address and the exact parameter substitutions."""
from pathlib import Path
import hashlib,re
root=Path('build/v56/experiments/fold-param')
def instructions(name):
    raw=(root/(name+'.dis')).read_bytes();print(name+'.dis SHA256 '+hashlib.sha256(raw).hexdigest())
    rows={}
    for line in raw.decode().splitlines():
        m=re.match(r'^\s*([0-9a-f]+):\s+([0-9a-f]{8})\s+(.+)$',line)
        if m:rows[int(m[1],16)]=(m[2],re.sub(r'\s+',' ',m[3]).strip())
    assert len(rows)>10000;return rows
base=instructions('baseline')
for name,loads,moves in [('cf4',1,2),('cf34',2,3)]:
    new=instructions(name);assert new.keys()==base.keys()
    changed=[a for a in base if base[a]!=new[a]]
    assert len(changed)==loads+moves,(name,len(changed))
    counts=[0,0]
    for a in changed:
        old_op=base[a][1];new_op=new[a][1]
        m=re.fullmatch(r'ldr x25, \[(x\d+), #120\]',old_op)
        if m:
            assert new_op==f'ldr x25, [{m[1]}, #216]';counts[0]+=1
        else:
            assert re.fullmatch(r'ldr x24, \[x\d+, #216\]',old_op),old_op
            assert new_op=='mov x24, x25',new_op;counts[1]+=1
        print(f'{name} {a:x}: {old_op} -> {new_op}')
    assert counts==[loads,moves]
    print(f'{name}: all {len(base)} linked instruction addresses match; only {len(changed)} checked parameter substitutions differ. All other opcode words and operands match.')
print('No arithmetic, memory addresses of tensor data, branch layout or code size change in inspected binaries; this is not a performance claim.')
