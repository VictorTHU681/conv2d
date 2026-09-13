#!/usr/bin/env python3
"""Require complete phase records; exclude validation and warmup calls."""
from pathlib import Path
from statistics import median
import re,sys
s=Path(sys.argv[1]).read_text()
assert 'KF_PROFILE_DONE' in s and 'FAIL' not in s
placement=re.search(r'^PLACEMENT cpu_node=\d+ hbm_node=(-?\d+)$',s,re.M);assert placement
memories=['DDR'] if int(placement[1])<0 else ['DDR','HBM']
phase={};cost={};table={};timings={};key=None;order={}
for line in s.splitlines():
    m=re.match(r'PROFILE memory=(\w+) round=(\d+) variant=(\w+) shape=6390 4256 81 81$',line)
    if m:
        key=(m[1],int(m[2]),m[3]);assert key not in phase
        phase[key]={};cost[key]={};table[key]={};timings[key]=0
        order.setdefault(key[:2],[]).append(key[2])
    if line.startswith(('K5_PHASE ','K5_COST ','TABLE_WORK ')):
        assert key is not None
        fields=dict(re.findall(r'(\w+)=([\d.]+)',line));call=int(fields.pop('call'))
        if line.startswith('K5_PHASE '):
            assert call not in phase[key];phase[key][call]={k:float(v) for k,v in fields.items()}
        elif line.startswith('TABLE_WORK '):
            assert call not in table[key];table[key][call]={k:int(v) for k,v in fields.items()}
        else:
            bucket=int(fields.pop('bucket'));idx=(call,bucket)
            assert idx not in cost[key];cost[key][idx]={k:float(v) for k,v in fields.items()}
    if re.search(r' run\d+\s+.* GFLOPS PASS$',line):
        assert key is not None;timings[key]+=1
expected={(m,r,v) for m in memories for r in range(1,7) for v in ['baseline','merged']}
assert set(phase)==expected
for key in expected:
    assert set(phase[key])==set(table[key])==set(range(1,8)) and timings[key]==5
    assert set(cost[key])=={(c,b) for c in range(1,8) for b in [0,2]}
    assert order[key[:2]]==(['baseline','merged'] if key[1]%2 else ['merged','baseline'])
    for c in range(1,8):
        assert table[key][c]=={'r_bytes':844992,'kf_bytes':209952 if key[2]=='baseline' else 104976,'logical_kf_bytes':209952}
        assert cost[key][c,0]['tile_steps']==543263760
        assert cost[key][c,2]['tile_steps']==69296560
print(f'{len(expected)} profiled processes, {len(expected)*7} calls, {len(expected)*5} timed output hashes PASS.')
print('Median of six process medians, each taking only timed calls 3–7. CNTFRQ converts ticks to time.')
print('Instrumented timings support attribution, not official performance acceptance.')
print('Per-call kf bytes: 209,952 -> 104,976; unique R bytes remain 844,992. This counts logical written payload, not PMU cache traffic.')
print('\n| Memory | Variant | Prepare us | Dispatch us | Workers us | Pack mean us | Pack max us | Main ns/tile | K9 ns/tile |')
print('| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |')
for mem in memories:
    for v in ['baseline','merged']:
        def pval(field):return median(median(phase[mem,r,v][c][field] for c in range(3,8)) for r in range(1,7))
        def cval(bucket,field):return median(median(cost[mem,r,v][c,bucket][field] for c in range(3,8)) for r in range(1,7))
        p=[pval(f) for f in ['prepare_us','dispatch_us','workers_us','pack_mean_us','pack_max_us']]
        print(f'| {mem} | {v} | '+ ' | '.join(f'{x:.3f}' for x in p)+f' | {cval(0,"ns_per_tile_step"):.6f} | {cval(2,"ns_per_tile_step"):.6f} |')
        print(f'<!-- {mem} {v}: main mean {cval(0,"kernel_mean_us"):.3f} us, K9 mean {cval(2,"kernel_mean_us"):.3f} us -->')
