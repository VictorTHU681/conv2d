#!/usr/bin/env python3
"""Strict screening/phase summaries; never label these as official benchmarks."""
from pathlib import Path
from collections import defaultdict
from statistics import median
import re,sys

mode=sys.argv[1];s=Path(sys.argv[2]).read_text()
assert 'FAIL' not in s
if mode in ('smoke','copy'):
    variants=['baseline','triplet'] if mode=='smoke' else ['baseline','triplet','prefetch','overlap','both']
    assert ('K5_SMOKE_DONE' if mode=='smoke' else 'K5_COPY_DONE') in s
    assert s.count('STATE_SWEEP PASS cases=261')==(1 if mode=='smoke' else 3)
    if mode=='copy': assert re.search(r'OUTPUT_OVERLAP PASS cases=54 calls=\d+ active_conflicts=0 positive_control=0',s)
    data={};counts=defaultdict(int);key=None
    for line in s.splitlines():
        m=re.match(r'MEASURE memory=(\w+) round=(\d+) variant=(\w+) shape=\d+ \d+ (\d+) (\d+)',line)
        if m:
            assert key is None and m[4]==m[5]
            key=m[1],int(m[2]),m[3],int(m[4])
        if re.search(r' run\d+\s+.* GFLOPS PASS$',line):
            assert key is not None;counts[key]+=1
        m=re.search(r'\| avg\s+[\d.]+ ms\s+([\d.]+) GFLOPS\s+PASS',line)
        if m:
            assert key is not None and key not in data and counts[key]==5
            data[key]=float(m[1]);key=None
    placement=re.search(r'^PLACEMENT cpu_node=\d+ hbm_node=(-?\d+)$',s,re.M)
    assert placement is not None
    memories=['DDR'] if int(placement[1])<0 else ['DDR','HBM']
    expected={(m,r,v,k) for m in memories for r in [1,2,3] for v in variants for k in [39,41,55,81]}
    assert set(data)==expected and key is None
    print(f'{len(expected)*5} timed output hashes PASS; screening with three alternating rounds, not official full-reference acceptance.')
    print('Median of three process-average GFLOPS values; five timed calls per process.')
    if len(memories)==1: print('HBM was unavailable in this allocation and was skipped; no HBM performance conclusion.')
    for memory in memories:
        print('\n'+memory+'\n\n| Variant | KH 39 | KH 41 | KH 55 | KH 81 |\n| --- | ---: | ---: | ---: | ---: |')
        for v in variants:
            cells=[]
            for k in [39,41,55,81]:
                a,b=[median(data[memory,r,x,k] for r in [1,2,3]) for x in ['baseline',v]]
                cells.append(f'{b:.1f} ({100*(b/a-1):+.2f}%)')
            print('| '+v+' | '+' | '.join(cells)+' |')
elif mode=='profile':
    assert 'K5_PROFILE_DONE' in s
    phase={};cost={};key=None
    for line in s.splitlines():
        m=re.match(r'PROFILE memory=(\w+) round=(\d+) variant=(\w+) shape=\d+ \d+ (\d+) (\d+)',line)
        if m:
            assert m[4]==m[5];key=m[1],int(m[2]),m[3],int(m[4])
        m=re.match(r'K5_PHASE call=(\d+) prepare_us=([\d.]+) dispatch_us=([\d.]+) workers_us=([\d.]+) pack_mean_us=([\d.]+) pack_max_us=([\d.]+)',line)
        if m:
            k=key+(int(m[1]),);assert k not in phase
            phase[k]=tuple(float(m[i]) for i in [2,3,4,5,6])
        m=re.match(r'K5_COST call=(\d+) bucket=(\d+) tile_steps=(\d+) kernel_mean_us=([\d.]+) ns_per_tile_step=([\d.]+)',line)
        if m:
            k=key+(int(m[1]),int(m[2]));assert k not in cost and int(m[3])>0
            cost[k]=float(m[4]),float(m[5])
    blocks={(m,r,v,k) for m in ['DDR','HBM'] for r in [1,2,3] for v in ['baseline','triplet'] for k in [39,41]}
    assert set(phase)=={x+(c,) for x in blocks for c in range(1,8)}
    assert set(cost)=={x+(c,b) for x in blocks for c in range(1,8)
                       for b in [0,2 if x[2]=='baseline' and x[3]==41 else 3]}
    assert len(re.findall(r' run\d+\s+.* GFLOPS PASS$',s,re.M))==120
    print('24 instrumented processes, 168 call profiles and 120 timed hashes PASS. Calls 1/2 are validation/warmup and excluded below.')
    print('Median of three process medians, each from five timed calls. Actual CNTFRQ converts ticks to time.')
    print('Tile-step counts use executed KW+2 for K5 and KW+3 for K4; packing padding is not counted as executed FMOPA.')
    print('Kernel timings include preparation/copy/output work inside the measured region; ns/tile-step is amortized cost, not instruction latency.')
    print('Instrumentation changes code layout and timing; use uninstrumented screening to decide performance.')
    print('\n| Memory | KH | Variant | Prepare us | Pack mean us | Workers us | Main ns/tile-step | Tail ns/tile-step | Main mean us | Tail mean us |')
    print('| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |')
    for memory in ['DDR','HBM']:
        for kh in [39,41]:
            for v in ['baseline','triplet']:
                tail=2 if v=='baseline' and kh==41 else 3
                def ph(i): return median(median(phase[memory,r,v,kh,c][i] for c in range(3,8)) for r in [1,2,3])
                def co(b,i): return median(median(cost[memory,r,v,kh,c,b][i] for c in range(3,8)) for r in [1,2,3])
                values=[ph(0),ph(3),ph(2),co(0,1),co(tail,1),co(0,0),co(tail,0)]
                print(f'| {memory} | {kh} | {v} | '+' | '.join(f'{x:.4f}' for x in values)+' |')
else: raise SystemExit('Choose smoke, copy or profile')
