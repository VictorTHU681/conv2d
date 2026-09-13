#!/usr/bin/env python3
"""Report linked symbol movement; this does not prove instruction equivalence."""
from pathlib import Path
import re

root=Path('build/post63/k5-prefix')
variants=['baseline','exact','legacy']
symbols={}
for v in variants:
    table={}
    for line in (root/f'symbols_{v}.txt').read_text().splitlines():
        m=re.fullmatch(r'([0-9a-f]+) ([0-9a-f]+) [tT] (.+)',line)
        if m: table[m[3]]=(int(m[1],16),int(m[2],16))
    assert 'k5' in table and 'conv2d' in table
    symbols[v]=table
print('Linked screening symbols; address/size only, not a machine-code equivalence audit.')
print('| Function | v62 address/bytes | v62 exact address/bytes | v61 exact address/bytes |')
print('| --- | --- | --- | --- |')
for name in ['roll_first_planes.constprop.0','roll_first_planes.constprop.1','roll_first_planes.constprop.2','k5','k4','k8f','k16pairf4','roll_worker','conv2d']:
    if not all(name in symbols[v] for v in variants): continue
    print('| '+name+' | '+' | '.join(f'0x{symbols[v][name][0]:x} / {symbols[v][name][1]}' for v in variants)+' |')
a,b=symbols['baseline'],symbols['exact']
common=set(a)&set(b)
print(f'\nCommon text symbols: {len(common)}; moved addresses: {sum(a[n][0]!=b[n][0] for n in common)}; changed sizes: {sum(a[n][1]!=b[n][1] for n in common)}.')
print('Compiler-generated constprop suffixes are symbol names, not proof that the same-numbered clones serve the same call sites.')
print('Changes on shapes that do not execute K5 must not be attributed to its copy work. Fixed-source compilation can change layout; original full-reference timing is still required.')
