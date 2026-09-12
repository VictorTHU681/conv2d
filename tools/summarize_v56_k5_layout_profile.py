#!/usr/bin/env python3
"""Compare full phase records under the matched K5/F4 profiling controls."""
from pathlib import Path
from statistics import median
from itertools import permutations
from collections import defaultdict
import re,sys
s=Path(sys.argv[1]).read_text()
assert 'K5_LAYOUT_PROFILE_DONE' in s and 'FAIL' not in s
placement=re.search(r'^PLACEMENT cpu_node=\d+ hbm_node=(-?\d+)$',s,re.M);assert placement
memories=['DDR'] if int(placement[1])<0 else ['DDR','HBM']
variants=['baseline','triplet','triplet_out'];phase={};cost={};steps={};counts=defaultdict(int);order=defaultdict(list);key=None
for line in s.splitlines():
    m=re.match(r'PROFILE memory=(\w+) round=(\d+) variant=(\w+) shape=(\d+) (\d+) (\d+) (\d+)$',line)
    if m:
        kh=int(m[6]);assert (int(m[4]),int(m[5]),int(m[7]))=={39:(4096,6144,39),41:(6144,4096,41)}[kh]
        key=m[1],int(m[2]),m[3],kh;order[key[0],key[1],key[3]].append(key[2])
    m=re.match(r'K5_PHASE call=(\d+) prepare_us=([\d.]+) dispatch_us=([\d.]+) workers_us=([\d.]+) pack_mean_us=([\d.]+) pack_max_us=([\d.]+)',line)
    if m:
        assert key is not None;k=key+(int(m[1]),);assert k not in phase
        phase[k]=tuple(float(m[i]) for i in [2,3,4,5,6])
    m=re.match(r'K5_COST call=(\d+) bucket=(\d+) tile_steps=(\d+) kernel_mean_us=([\d.]+) ns_per_tile_step=([\d.]+)',line)
    if m:
        assert key is not None;k=key+(int(m[1]),int(m[2]));assert k not in cost
        cost[k]=float(m[4]),float(m[5]);steps[k]=int(m[3]);assert steps[k]>0
    if re.search(r' run\d+\s+.* GFLOPS PASS$',line):
        assert key is not None;counts[key]+=1
blocks={(m,r,v,k) for m in memories for r in range(6) for v in variants for k in [39,41]}
assert set(phase)=={x+(c,) for x in blocks for c in range(1,8)}
assert set(cost)=={x+(c,b) for x in blocks for c in range(1,8) for b in [0,2 if x[2]=='baseline' and x[3]==41 else 3]}
assert set(counts)==blocks and set(counts.values())=={5}
for m in memories:
    for kh in [39,41]: assert {tuple(order[m,r,kh]) for r in range(6)}==set(permutations(variants))
print(f'{len(blocks)} profiled processes, {len(phase)} call records and {sum(counts.values())} timed hashes PASS.')
print('Median of six process medians, each from timed calls 3–7. Calls 1/2 excluded. CNTFRQ scales ticks.')
print('Profiling changes code layout and adds instrumentation. These are amortized kernel-region costs, not official performance or instruction latency.')
print('\n| Memory | KH | Variant | Prepare us | Pack mean us | Workers us | Main ns/tile | Tail ns/tile | Main mean us | Tail mean us | Total tile steps |')
print('| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |')
for mem in memories:
    for kh in [39,41]:
        for v in variants:
            tail=2 if v=='baseline' and kh==41 else 3
            def ph(i): return median(median(phase[mem,r,v,kh,c][i] for c in range(3,8)) for r in range(6))
            def co(b,i): return median(median(cost[mem,r,v,kh,c,b][i] for c in range(3,8)) for r in range(6))
            totals={sum(steps[mem,r,v,kh,c,b] for b in [0,tail]) for r in range(6) for c in range(1,8)};assert len(totals)==1
            vals=[ph(0),ph(3),ph(2),co(0,1),co(tail,1),co(0,0),co(tail,0)]
            print(f'| {mem} | {kh} | {v} | '+' | '.join(f'{x:.4f}' for x in vals)+f' | {totals.pop()} |')
