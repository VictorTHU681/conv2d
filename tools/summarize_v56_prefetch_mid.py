#!/usr/bin/env python3
"""Validate one-binary prefetch-mid screening and balanced process orders."""
from pathlib import Path
from statistics import median
from collections import defaultdict,Counter
import re,sys
s=Path(sys.argv[1]).read_text();assert 'PREFETCH_MID_DONE' in s and 'FAIL' not in s
for line in Path('results/v56/experiments/prefetch-mid/sources.sha256').read_text().splitlines():
    digest,path=line.split();assert re.search(r'^'+digest+r'\s+'+re.escape(path)+r'$',s,re.M)
assert re.search(r'^[0-9a-f]{64}\s+build/v56/experiments/prefetch-mid/bench$',s,re.M)
assert s.count('STATE_SWEEP PASS cases=261')==3 and s.count('PLANAR_GUARD_PASS cases=224')==3
for kind in ['STATE','GUARD']:assert re.findall(r'^PREFETCH_MID_'+kind+r' pd=(\d+)$',s,re.M)==['3','4','5']
m=re.search(r'^PLACEMENT cpu_node=\d+ hbm_node=(-?\d+)$',s,re.M);assert m
memories=['DDR'] if int(m[1])<0 else ['DDR','HBM'];settings=[3,4,5]
shapes={39:(4096,6144,39,39),41:(6144,4096,41,41),55:(4256,6390,55,55),81:(6390,4256,81,81)}
expected_orders=[[3,4,5],[4,5,3],[5,3,4],[5,4,3],[3,5,4],[4,3,5]]
data={};counts=defaultdict(int);orders=defaultdict(list);key=None
for line in s.splitlines():
    m=re.match(r'PREFETCH_MID memory=(\w+) round=(\d+) pd=(\d+) shape=(\d+) (\d+) (\d+) (\d+)$',line)
    if m:
        assert key is None;kh=int(m[6]);assert tuple(map(int,m.groups()[3:]))==shapes[kh]
        key=m[1],int(m[2]),int(m[3]),kh;orders[key[0],key[1],kh].append(key[2])
    if re.search(r' run\d+\s+.* GFLOPS PASS$',line):
        assert key is not None;counts[key]+=1
    m=re.search(r'\| avg\s+[\d.]+ ms\s+([\d.]+) GFLOPS\s+PASS',line)
    if m:
        assert key is not None and key not in data and counts[key]==5
        data[key]=float(m[1]);key=None
assert key is None and set(data)=={(m,r,p,k) for m in memories for r in range(6) for p in settings for k in shapes}
for m in memories:
    for k in shapes:
        for r in range(6):assert orders[m,r,k]==expected_orders[r]
        for pos in range(3):assert Counter(orders[m,r,k][pos] for r in range(6))==Counter({3:2,4:2,5:2})
        pairs=Counter((order[i],order[i+1]) for order in expected_orders for i in range(2))
        assert set(pairs)=={(a,b) for a in settings for b in settings if a!=b} and set(pairs.values())=={2}
print(f'783 state cases, 672 guard cases and {len(data)*5} timed hashes PASS.')
print('One accepted-source executable; six complete permutations, five timings/process. Median process-average GFLOPS. Settings change only CONV_ROLL_PD; baseline is explicit default 3. Screening, not original-reference acceptance.')
print('\n| Memory | KH | Default 3 GFLOPS | Distance 4 | Distance 5 |')
print('| --- | ---: | ---: | ---: | ---: |')
for m in memories:
    for k in shapes:
        a=median(data[m,r,3,k] for r in range(6))
        changes=[100*(median(data[m,r,p,k] for r in range(6))/a-1) for p in [4,5]]
        print(f'| {m} | {k} | {a:.1f} | '+' | '.join(f'{v:+.2f}%' for v in changes)+' |')
print('\nAll paired outliers retained; observed ranges are not confidence intervals.')
for m in memories:
    for k in shapes:
        for p in [4,5]:
            xs=[100*(data[m,r,p,k]/data[m,r,3,k]-1) for r in range(6)]
            print(f'{m} KH{k} pd{p}: paired median {median(xs):+.2f}%, range {min(xs):+.2f}..{max(xs):+.2f}%, positive {sum(x>0 for x in xs)}/6')
