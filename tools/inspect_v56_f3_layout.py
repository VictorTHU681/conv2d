#!/usr/bin/env python3
"""Verify identical F3 arithmetic and record actual compiled loop positions."""
from pathlib import Path
import argparse,re,hashlib
p=argparse.ArgumentParser();p.add_argument('--experiment',choices=['chunk-setup','f3-padding','f3-outline','f3-anchor'],default='chunk-setup');args=p.parse_args()
variants=['baseline','phase','carry4','both'] if args.experiment=='chunk-setup' else ['phase','p32','p64','p96']
if args.experiment=='f3-outline':variants=['baseline','phase','baseline_out','phase_out']
if args.experiment=='f3-anchor':variants=['baseline','phase','baseline_anchor','phase_anchor']
out=[];ref=None;functions={}
for v in variants:
    s=Path(f'build/v56/experiments/{args.experiment}/disassembly/{v}.txt').read_text();rows=[];sym=''
    for line in s.splitlines():
        m=re.match(r'^\s*[0-9a-f]+ <(.+)>:$',line)
        if m:sym=m[1]
        m=re.match(r'\s*([0-9a-f]+):\s+([0-9a-f]{8})\s+(.*)',line)
        if m:rows.append((int(m[1],16),m[2],re.sub(r'\s+',' ',m[3]),sym))
    functions[v]=[(x[0],x[1]) for x in rows if x[3].startswith('k16pairf3')]
    hits=[]
    for i,x in enumerate(rows):
        if (x[3]=='roll_worker' or x[3].startswith('k16pairf3')) and x[2].startswith('ld1rqw') and sum(y[2].startswith('fmla ') for y in rows[i+1:i+13])==6:
            b=rows[i-4:i+15];assert len(b)==19 and sum(y[2].startswith('fmopa ') for y in b)==4
            if args.experiment=='f3-outline':
                assert x[3].startswith('k16pairf3') if v.endswith('_out') else x[3]=='roll_worker'
            words=[y[1] for y in b]
            if ref is None:ref=words
            assert ref==words;hits.append(b[0][0]);out.append(f'{v} F3_step_{len(hits)} address=0x{b[0][0]:x} mod128={b[0][0]%128} words_sha256={hashlib.sha256(" ".join(words).encode()).hexdigest()}')
    assert len(hits)==2,(v,hits)
    if args.experiment=='f3-anchor' and v.endswith('_anchor'):assert [x%128 for x in hits]==[48,80],(v,hits)
if args.experiment=='f3-outline':
    assert functions['baseline_out'] and functions['phase_out']
    out.append(f'Outlined F3 full_instruction_addresses_and_words_identical={functions["baseline_out"]==functions["phase_out"]}')
out.append('All eight extracted F3 arithmetic blocks have identical words; address/alignment varies as listed. This is not proof that alignment causes the measured KH55 regression.')
Path(f'results/v56/experiments/{args.experiment}/f3_code.txt').write_text('\n'.join(out)+'\n');print('\n'.join(out))
