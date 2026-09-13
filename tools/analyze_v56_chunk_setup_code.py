#!/usr/bin/env python3
"""Record complete generated worker code controls after compilation finishes."""
from pathlib import Path
import re,hashlib
root=Path('build/v56/experiments/chunk-setup/disassembly');out=[]
for name in ['baseline','phase','carry4','both']:
    p=root/(name+'.txt');s=p.read_text();m=re.search(r'^([0-9a-f]+) <roll_worker>:\n(.*?)(?=\n\n)',s,re.M|re.S);assert m,name
    instructions=re.findall(r'^\s*([0-9a-f]+):\s+([0-9a-f]{8})\s+(.*)$',m[2],re.M)
    div=[x for x in instructions if re.match(r'[su]div\s',x[2])]
    za=[x for x in instructions if re.match(r'(?:ldr|str)\s+za\[',x[2])]
    out.append(f'{name}: roll_worker entry=0x{m[1]} static_divide_instructions={len(div)} static_ZA_transfers={len(za)} disassembly_sha256={hashlib.sha256(p.read_bytes()).hexdigest()}')
    for addr,word,asm in za:out.append(f'  {addr}: {word} {asm}')
print('Static instructions across all worker branches; not dynamic per-chunk counts or proof of end-to-end benefit.')
print('\n'.join(out))
