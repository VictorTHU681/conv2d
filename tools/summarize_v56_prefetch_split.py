#!/usr/bin/env python3
"""Validate one-binary prefetch-split screening and balanced process orders."""
from pathlib import Path
from statistics import median
from collections import defaultdict,Counter
import re,sys
s=Path(sys.argv[1]).read_text();assert 'SPLIT_DONE' in s and 'FAIL' not in s
for line in Path('results/v56/experiments/prefetch-split/sources.sha256').read_text().splitlines():
    digest,path=line.split();assert re.search(r'^'+digest+r'\s+'+re.escape(path)+r'$',s,re.M)
assert re.search(r'^[0-9a-f]{64}\s+build/v56/experiments/prefetch-split/bench$',s,re.M)
assert s.count('STATE_SWEEP PASS cases=261')==4 and s.count('PLANAR_GUARD_PASS cases=224')==4
for kind in ['STATE','GUARD']:assert re.findall(r'^SPLIT_'+kind+r' cfg=(\w+)$',s,re.M)==['i3o3','i1o3','i3o1','i1o1']
m=re.search(r'^PLACEMENT cpu_node=\d+ hbm_node=(-?\d+)$',s,re.M);assert m
memories=['DDR'] if int(m[1])<0 else ['DDR','HBM'];settings=['i3o3','i1o3','i3o1','i1o1']
shapes={39:(4096,6144,39,39),41:(6144,4096,41,41),55:(4256,6390,55,55),81:(6390,4256,81,81)}
expected_orders=[['i3o3','i1o3','i1o1','i3o1'],['i1o3','i3o1','i3o3','i1o1'],['i3o1','i1o1','i1o3','i3o3'],['i1o1','i3o3','i3o1','i1o3']]
data={};counts=defaultdict(int);orders=defaultdict(list);key=None
for line in s.splitlines():
    m=re.match(r'SPLIT memory=(\w+) round=(\d+) cfg=(\w+) shape=(\d+) (\d+) (\d+) (\d+)$',line)
    if m:
        assert key is None;kh=int(m[6]);assert tuple(map(int,m.groups()[3:]))==shapes[kh]
        key=m[1],int(m[2]),m[3],kh;orders[key[0],key[1],kh].append(key[2])
    if re.search(r' run\d+\s+.* GFLOPS PASS$',line):
        assert key is not None;counts[key]+=1
    m=re.search(r'\| avg\s+[\d.]+ ms\s+([\d.]+) GFLOPS\s+PASS',line)
    if m:
        assert key is not None and key not in data and counts[key]==5
        data[key]=float(m[1]);key=None
assert key is None and set(data)=={(m,r,p,k) for m in memories for r in range(4) for p in settings for k in shapes}
for m in memories:
    for k in shapes:
        for r in range(4):assert orders[m,r,k]==expected_orders[r]
        for pos in range(4):assert set(orders[m,r,k][pos] for r in range(4))==set(settings)
        pairs=Counter((order[i],order[i+1]) for order in expected_orders for i in range(3))
        assert set(pairs)=={(a,b) for a in settings for b in settings if a!=b} and set(pairs.values())=={1}
print(f'1,044 state cases, 896 guard cases and {len(data)*5} timed hashes PASS.')
print('One diagnostic split-prefetch executable; four Williams orders, five timings/process. Median process-average GFLOPS. Settings vary CONV_ROLL_PDIN and CONV_ROLL_PDOUT; baseline is input3/output3. Screening, not original-reference acceptance.')
print('\n| Memory | KH | Input3/output3 GFLOPS | Input1/output3 | Input3/output1 | Input1/output1 |')
print('| --- | ---: | ---: | ---: | ---: | ---: |')
for m in memories:
    for k in shapes:
        a=median(data[m,r,'i3o3',k] for r in range(4))
        changes=[100*(median(data[m,r,p,k] for r in range(4))/a-1) for p in ['i1o3','i3o1','i1o1']]
        print(f'| {m} | {k} | {a:.1f} | '+' | '.join(f'{v:+.2f}%' for v in changes)+' |')
print('\nAll paired outliers retained; observed ranges are not confidence intervals.')
for m in memories:
    for k in shapes:
        for p in ['i1o3','i3o1','i1o1']:
            xs=[100*(data[m,r,p,k]/data[m,r,'i3o3',k]-1) for r in range(4)]
            print(f'{m} KH{k} {p}: paired median {median(xs):+.2f}%, range {min(xs):+.2f}..{max(xs):+.2f}%, positive {sum(x>0 for x in xs)}/4')
