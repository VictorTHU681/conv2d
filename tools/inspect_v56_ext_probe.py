#!/usr/bin/env python3
"""Verify actual generated throughput loops and absence of timed memory loads."""
from pathlib import Path
import hashlib,re
p=Path('build/v56/experiments/ext-throughput/disassembly.txt');s=p.read_text();out=[]
for v,nf,ne in [('mix0',16,0),('mix4',16,16),('mix8',16,32),('mix16',16,64),('window_block',64,64),('window_interleaved',64,64)]:
    m=re.search(r'^[0-9a-f]+ <'+v+r'>:\n(.*?)(?=\n\n)',s,re.M|re.S);assert m,v
    rows=re.findall(r'^\s*([0-9a-f]+):\s+([0-9a-f]{8})\s+(.+)$',m[1],re.M)
    stamps=[i for i,x in enumerate(rows) if 'cntvct_el0' in x[2]];assert len(stamps)==2
    measured=rows[stamps[0]+1:stamps[1]]
    fmopa=[r for r in measured if r[2].startswith('fmopa')];ext=[r for r in measured if r[2].startswith('ext')]
    assert len(fmopa)==nf and len(ext)==ne,(v,len(fmopa),len(ext))
    assert not any(re.match(r'(?:ld|st)[a-z0-9]*\s',r[2]) for r in measured),v
    first=int(fmopa[0][0],16);assert first%128==0
    words=' '.join(r[1] for r in measured)
    out.append(f'{v}: static_FMOPA={nf} static_EXT={ne} first_fmopa=0x{first:x} modulo128=0 timed_memory_instructions=0 region_sha256={hashlib.sha256(words.encode()).hexdigest()}')
out.append('Counts are for four unrolled units; dependent window units contain four times as many FMOPA as mix units, accounted for in time normalization.')
Path('results/v56/experiments/ext-throughput/machine_code.txt').write_text('\n'.join(out)+'\n');print('\n'.join(out))
