#!/usr/bin/env python3
"""Identify actual F4 step bytes and loop alignment in the original binaries."""
from pathlib import Path
import hashlib,re,argparse

parser=argparse.ArgumentParser()
parser.add_argument('--experiment',choices=['upstream-gate','kf-share'],default='upstream-gate')
args=parser.parse_args()
root=Path('build/v56/experiments')/args.experiment/'disassembly'
out=Path('results/v56/experiments')/args.experiment
reference=None;report=[]
for v in ['baseline','merged']:
    rows=[]
    for line in (root/(v+'.txt')).read_text().splitlines():
        m=re.match(r'\s*([0-9a-f]+):\s+([0-9a-f]{8})\s+(.*)',line)
        if m: rows.append((int(m[1],16),m[2],re.sub(r'\s+',' ',m[3].strip()),line))
    hits=[]
    for i,x in enumerate(rows):
        if (x[2].startswith('ld1rqw') and i+16<len(rows) and
            sum(y[2].startswith('fmla ') for y in rows[i+1:i+13])==8):
            block=rows[i-4:i+17]
            assert len(block)==21 and sum(y[2].startswith('fmopa ') for y in block)==4
            words=[y[1] for y in block]
            if reference is None:reference=words
            assert words==reference,(v,hex(block[0][0]))
            hits.append(block[0][0])
            report.append(f'{v} F4_step_{len(hits)} start=0x{block[0][0]:x} mod128={block[0][0]%128} words_sha256={hashlib.sha256(" ".join(words).encode()).hexdigest()}')
            (out/f'{v}.f4_step{len(hits)}.txt').write_text('\n'.join(y[3] for y in rows[i-7:i+20])+'\n')
    assert len(hits)==(1 if v=='baseline' and args.experiment=='upstream-gate' else 3)
    if args.experiment=='upstream-gate':
        assert [x%128 for x in hits]==([0] if v=='baseline' else [120,32,0])
report.append('All F4 arithmetic step bodies have identical 21 instruction words (5 loads, 4 FMOPA, 8 FMLA, 4 pointer increments).')
if args.experiment=='upstream-gate':
    report.append('Baseline short loop is mod128=0; merged short loop is mod128=120. Merged overlap step is mod128=32 and long pure loop mod128=0.')
report.append('Instruction equality is limited to these step bodies, not the entire short path or all function bytes.')
(out/'machine_code.txt').write_text('\n'.join(report)+'\n')
print('\n'.join(report))
