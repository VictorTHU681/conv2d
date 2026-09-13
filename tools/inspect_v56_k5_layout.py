#!/usr/bin/env python3
"""Identify F4 bodies and actual inlining in all matched screening binaries."""
from pathlib import Path
from collections import Counter
import hashlib,re,argparse
parser=argparse.ArgumentParser()
parser.add_argument('--experiment',choices=['k5-layout','k5-cost','chunk-setup'],default='k5-layout')
args=parser.parse_args()
root=Path('build/v56/experiments')/args.experiment/'disassembly'
out=Path('results/v56/experiments')/args.experiment
report=[];reference=None;functions={}
variants=['baseline','triplet','k5cost','tailcost'] if args.experiment=='k5-cost' else ['baseline','triplet','baseline_out','triplet_out']
if args.experiment=='chunk-setup':variants=['baseline','phase','carry4','both']
for v in variants:
    rows=[];symbol=None
    for line in (root/(v+'.txt')).read_text().splitlines():
        m=re.match(r'^\s*[0-9a-f]+ <(.+)>:$',line)
        if m:symbol=m[1]
        m=re.match(r'\s*([0-9a-f]+):\s+([0-9a-f]{8})\s+(.*)',line)
        if m:rows.append((int(m[1],16),m[2],re.sub(r'\s+',' ',m[3].strip()),symbol,line))
    counts=Counter(r[3] for r in rows);hits=[]
    functions[v]={name:[(r[0],r[1]) for r in rows if r[3]==name] for name in ['k5','roll_worker']}
    for i,x in enumerate(rows):
        if x[3]!='roll_worker' and not x[3].startswith('k16pairf4'): continue
        if (x[2].startswith('ld1rqw') and i+16<len(rows) and
            sum(y[2].startswith('fmla ') for y in rows[i+1:i+13])==8):
            block=rows[i-4:i+17];assert len(block)==21 and sum(y[2].startswith('fmopa ') for y in block)==4
            words=[y[1] for y in block]
            if reference is None:reference=words
            assert words==reference,(v,hex(block[0][0]))
            symbol=block[0][3];assert all(y[3]==symbol for y in block)
            assert symbol.startswith('k16pairf4') if v.endswith('_out') else symbol=='roll_worker'
            hits.append(block[0][0])
            report.append(f'{v} F4_step_{len(hits)} function={symbol} start=0x{block[0][0]:x} mod128={block[0][0]%128} words_sha256={hashlib.sha256(" ".join(words).encode()).hexdigest()}')
            (out/f'{v}.f4_step{len(hits)}.txt').write_text('\n'.join(y[4] for y in rows[i-7:i+20])+'\n')
    assert len(hits)==3,(v,len(hits))
    for symbol,n in counts.items():
        if symbol=='roll_worker' or symbol.startswith(('k16pairf4','k5.')) or symbol=='k5':
            report.append(f'{v} function={symbol} disassembled_instruction_count={n}')
report.append('All 12 extracted F4 steps have identical arithmetic instruction words. Counts include compiler scaffolding and padding, not dynamic execution counts.')
if args.experiment=='chunk-setup':
    for v in variants[1:]:
        report.append(f'{v} k5 full_instruction_addresses_and_words_identical_to_baseline={functions[v]["k5"]==functions["baseline"]["k5"]}')
if args.experiment=='k5-cost':
    for name in ['k5','roll_worker']:
        same=all(functions[v][name]==functions['triplet'][name] for v in ['k5cost','tailcost'])
        report.append(f'K5 cost variants function={name} full_instruction_addresses_and_words_identical={same}')
(out/('arithmetic_code.txt' if args.experiment=='chunk-setup' else 'machine_code.txt')).write_text('\n'.join(report)+'\n')
print('\n'.join(report))
