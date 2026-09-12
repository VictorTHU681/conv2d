#!/usr/bin/env python3
"""Validate current-source whole-shape phase and worker attribution."""
from pathlib import Path
from collections import defaultdict
from statistics import mean,median
import re,sys

s=Path(sys.argv[1]).read_text()
assert 'CURRENT_PROFILE_DONE' in s and 'FAIL' not in s
assert '1d3f5071d51cd4f8c88720b8d4fa91983515ffd83bdeb4983377a991df2b871a' in s
assert 'e5e52c8d666584cc49ca6f11162be4868b240e2cc99a3c3ef0a2f8ac292c65ad' in s
assert '886d018acb8c5e5b673a8fe937b86b6d3398591cc1ce675eba42125b0ec9ba1c' in s
m=re.search(r'^PLACEMENT cpu_node=\d+ hbm_node=(-?\d+)$',s,re.M);assert m
memories=['DDR'] if int(m[1])<0 else ['DDR','HBM']
shapes={39:(4096,6144,39,39),41:(6144,4096,41,41),55:(4256,6390,55,55),81:(6390,4256,81,81)}
buckets={39:[0,3],41:[0,3],55:[0,1,3],81:[0,2]}
hosts={};threads={};costs={};tables={};counts=defaultdict(int);orders=defaultdict(list);key=None
for line in s.splitlines():
    m=re.match(r'CURRENT_PROFILE memory=(\w+) round=(\d+) shape=(\d+) (\d+) (\d+) (\d+)$',line)
    if m:
        kh=int(m[5]);assert tuple(map(int,m.groups()[2:]))==shapes[kh]
        key=m[1],int(m[2]),kh;orders[key[:2]].append(kh)
    for prefix,dest in [('K5_PHASE ',hosts),('K5_THREAD ',threads),('K5_COST ',costs),('TABLE_WORK ',tables)]:
        if line.startswith(prefix):
            assert key is not None
            fields=dict(re.findall(r'(\w+)=([\d.]+)',line))
            call=int(fields.pop('call'));k=key+(call,)
            if prefix=='K5_THREAD ':k+=(int(fields.pop('tid')),)
            if prefix=='K5_COST ':k+=(int(fields.pop('bucket')),)
            assert k not in dest
            dest[k]={n:float(v) for n,v in fields.items()}
    if re.search(r' run\d+\s+.* GFLOPS PASS$',line):
        assert key is not None;counts[key]+=1
blocks={(m,r,kh) for m in memories for r in range(4) for kh in shapes}
assert set(counts)==blocks and set(counts.values())=={5}
calls={k+(c,) for k in blocks for c in range(1,8)}
assert set(hosts)==set(tables)==calls
assert set(threads)=={k+(t,) for k in calls for t in range(38)}
assert set(costs)=={k+(b,) for k in calls for b in buckets[k[2]]}
for m in memories:
    for r in range(4):assert orders[m,r]==list(shapes)[r:]+list(shapes)[:r]
for kh in shapes:
    work=set();storage=set()
    for k in calls:
        if k[2]!=kh:continue
        ts=[threads[k+(t,)] for t in range(38)]
        cs=[costs[k+(b,)] for b in buckets[kh]]
        work.add(tuple(c['tile_steps'] for c in cs))
        storage.add(tuple(sorted(tables[k].items())))
        assert sum(t['main_steps']+t['tail_steps'] for t in ts)==sum(c['tile_steps'] for c in cs)
        assert abs(mean(t['main_us'] for t in ts)-costs[k+(0,)]['kernel_mean_us'])<0.002
        assert abs(mean(t['tail_us'] for t in ts)-sum(costs[k+(b,)]['kernel_mean_us'] for b in buckets[kh] if b!=0))<0.004
        assert all(t['main_us']+t['tail_us']<=t['duration_us']+0.003 for t in ts)
    assert len(work)==len(storage)==1
print(f'{len(blocks)} processes, {len(threads)} worker records and {sum(counts.values())} timed hashes validate. Kernel work and table-byte totals are constant for each shape; all thread step totals match aggregate buckets.')
print('Accepted source 1d3f5071 only. Four rotating shape orders, five timings/process. Timed calls 3–7, median of four process medians. Instrumentation is attribution only, not production throughput or an instruction-level timing proof.')
print('\n| Memory | KH | Prepare us | Dispatch us | Workers us | Mean pack us/thread | Last end us | Last-minus-mean end us | Critical worker main-majority calls |')
print('| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |')
for memory in memories:
    for kh in shapes:
        procs=defaultdict(list);main_majority=0
        for r in range(4):
            samples=defaultdict(list)
            for c in range(3,8):
                k=memory,r,kh,c;ts=[threads[k+(t,)] for t in range(38)]
                for n in ['prepare_us','dispatch_us','workers_us','pack_mean_us']:samples[n].append(hosts[k][n])
                last=max(ts,key=lambda t:t['end_us'])
                main_majority+=last['main_us']>=last['tail_us']
                samples['last'].append(last['end_us'])
                samples['gap'].append(last['end_us']-mean(t['end_us'] for t in ts))
            for n,values in samples.items():procs[n].append(median(values))
        names=['prepare_us','dispatch_us','workers_us','pack_mean_us','last','gap']
        print(f'| {memory} | {kh} | '+' | '.join(f'{median(procs[n]):.3f}' for n in names)+f' | {main_majority}/20 |')
print('\nKernel regions include per-chunk argument setup and ZA restore as well as kernel execution. Main bucket combines pair kernels; other buckets separate single-16, K9/K8, and K4/K5. These are per-worker averages, not serialized stages to add to wall time.')
print('\n| Memory | KH | Pair region us/thread | Single-16 region us/thread | K9/K8 region us/thread | K4/K5 region us/thread |')
print('| --- | ---: | ---: | ---: | ---: | ---: |')
for memory in memories:
    for kh in shapes:
        vals=[]
        for b in range(4):
            value=0 if b not in buckets[kh] else median(median(costs[memory,r,kh,c,b]['kernel_mean_us'] for c in range(3,8)) for r in range(4))
            vals.append(value)
        print(f'| {memory} | {kh} | '+' | '.join(f'{v:.3f}' for v in vals)+' |')
