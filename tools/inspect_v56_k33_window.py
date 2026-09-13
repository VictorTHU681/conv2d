#!/usr/bin/env python3
"""Validate outlined-worker equivalence after normalizing relocated addresses."""
from pathlib import Path
import re,hashlib
root=Path('build/v56/experiments/k33-window/raw-disassembly')
out=Path('results/v56/experiments/k33-window')
workers={};report=[]
for v in ['baseline','outline','unroll4','ext4','tbl4','tbl8']:
    s=(root/('disas_'+v+'.txt')).read_text()
    m=re.search(r'^([0-9a-f]+) <roll_worker>:',s,re.M);assert m
    instructions=[];raw=[]
    for line in s.splitlines():
        m2=re.match(r'\s*[0-9a-f]+:\s+[0-9a-f]{8}\s+(.*)',line)
        if m2:
            op=re.sub(r'\b[0-9a-f]+ (<[^>]+>)',r'\1',m2[1])
            instructions.append(re.sub(r'//.*','',op).strip());raw.append(line)
    assert len(instructions)>2000
    digest=hashlib.sha256('\n'.join(instructions).encode()).hexdigest()
    report.append(f'{v} worker start={m[1]} mod128={int(m[1],16)%128} instructions={len(instructions)} normalized_sha256={digest}')
    if v!='baseline':
        assert int(m[1],16)%128==0
        workers[v]=instructions
        p=(root/('pairf_'+v+'.txt')).read_text()
        h=re.search(r'^([0-9a-f]+) <k16pairf>:',p,re.M);assert h and int(h[1],16)%128==0
        (out/(v+'.pairf.txt')).write_text(p)
    else:
        hits=[i for i,line in enumerate(raw) if re.search(r'fmla\s+z10.s, p0/m, z0.s, z4.s',line)]
        assert len(hits)==2
        (out/'baseline.k33_loops.txt').write_text('\n\n'.join('\n'.join(raw[max(0,i-10):i+8]) for i in hits)+'\n')
assert all(v==workers['outline'] for v in workers.values())
report.append('All five outlined workers have identical instruction text after normalizing annotated relocated addresses; raw bytes and absolute addresses may differ.')
(out/'machine_code.txt').write_text('\n'.join(report)+'\n')
print('\n'.join(report))
