#!/usr/bin/env python3
"""Audit shared-image PMU scopes, work conservation and observer overhead."""
from pathlib import Path
from collections import defaultdict
from itertools import permutations
from statistics import mean,median
import re,sys

s=Path(sys.argv[1]).read_text()
assert 'PMU_DONE' in s and 'FAIL' not in s and 'PMU_ERROR' not in s
for line in Path('results/post63/k5-pmu/sources.sha256').read_text().splitlines():
    h,p=line.split();assert re.search(r'^'+h+r'\s+'+re.escape(p)+r'$',s,re.M)
for name in ['bench','state','guard']:
    assert re.search(r'^[0-9a-f]{64}\s+build/post63/k5-pmu/'+name+r'$',s,re.M)
assert re.findall(r'^PMU_STATE mode=(\d)$',s,re.M)==['0','1','2']
assert re.findall(r'^PMU_GUARD mode=(\d)$',s,re.M)==['0','1','2']
assert s.count('STATE_SWEEP PASS cases=261')==3 and s.count('PLANAR_GUARD_PASS cases=224')==3
m=re.search(r'^PLACEMENT cpu_node=\d+ hbm_node=(-?\d+)$',s,re.M);assert m
memories=['DDR'] if int(m[1])<0 else ['DDR','HBM']
procs={(stage,mem,r,v) for stage,vs in [('COMPARE',range(3)),('OVERHEAD',range(2))] for mem in memories for r in range(6) for v in vs}
hosts={};threads={};costs={};tables={};pmu={};counts=defaultdict(int);averages={};orders=defaultdict(list);key=None
for line in s.splitlines():
    m=re.fullmatch(r'PMU_(COMPARE|OVERHEAD) memory=(\w+) round=(\d+) (?:mode|enabled)=(\d) shape=6144 4096 41 41',line)
    if m:
        if key is not None:assert key in averages and counts[key]==5
        key=m[1],m[2],int(m[3]),int(m[4]);assert key in procs and key not in counts
        orders[key[:3]].append(key[3])
    for prefix,dest,index in [('K5_PHASE ',hosts,None),('K5_THREAD ',threads,'tid'),('K5_COST ',costs,'bucket'),('TABLE_WORK ',tables,None),('K5_PMU ',pmu,'tid')]:
        if line.startswith(prefix):
            assert key is not None
            fields=dict(re.findall(r'(\w+)=([\d.]+)',line));call=int(fields.pop('call'));k=key+(call,)
            if index:k+=(int(fields.pop(index)),)
            assert k not in dest
            dest[k]={n:(float(v) if '.' in v else int(v)) for n,v in fields.items()}
    if re.search(r' run\d+\s+.* GFLOPS PASS$',line):
        assert key is not None;counts[key]+=1
    m=re.search(r'\| avg\s+[\d.]+ ms\s+([\d.]+) GFLOPS\s+PASS',line)
    if m:
        assert key is not None and key not in averages and counts[key]==5
        averages[key]=float(m[1])
assert set(counts)==set(averages)==procs and set(counts.values())=={5}
calls={p+(c,) for p in procs for c in range(1,8)}
assert set(hosts)==set(tables)==calls
assert set(threads)==set(pmu)=={c+(t,) for c in calls for t in range(38)}
assert set(costs)=={c+(b,) for c in calls for b in [0,3]}
for mem in memories:
    assert {tuple(orders['COMPARE',mem,r]) for r in range(6)}==set(permutations(range(3)))
    for r in range(6):assert orders['OVERHEAD',mem,r]==([1,0] if r%2 else [0,1])
work=set();storage=set();ratios=[]
for c in calls:
    ts=[threads[c+(t,)] for t in range(38)];ps=[pmu[c+(t,)] for t in range(38)]
    work.add(tuple(costs[c+(b,)]['tile_steps'] for b in [0,3]));storage.add(tuple(sorted(tables[c].items())))
    assert sum(t['main_steps']+t['tail_steps'] for t in ts)==sum(costs[c+(b,)]['tile_steps'] for b in [0,3])
    assert abs(mean(t['main_us'] for t in ts)-costs[c+(0,)]['kernel_mean_us'])<0.002
    assert abs(mean(t['tail_us'] for t in ts)-costs[c+(3,)]['kernel_mean_us'])<0.002
    enabled=1 if c[0]=='COMPARE' else c[3]
    for p in ps:
        assert p['enabled']==enabled
        if enabled:
            assert p['user_cycles']>0 and p['user_instructions']>0 and p['scope_us']>0
            assert 0<p['running_ns']<=p['enabled_ns']
            ratios.append(p['running_ns']/p['enabled_ns'])
        else:assert all(v==0 for v in p.values())
assert len(work)==len(storage)==1
print(f'1,455 state/guard checks; {len(procs)} processes, {len(pmu)} per-thread PMU records and {sum(counts.values())} timed hashes PASS. Work/table totals invariant.')
print(f'PMU running/enabled ratios: min {min(ratios):.9f}, median {median(ratios):.9f}. Counts below are raw, not scaled; reduced ratios must not be hidden.')
print('One executable and shared indirect dispatch, 128-byte-aligned K5 alternatives. PMU scope is the entire SME worker loop, including claims, state transfers, pair and K5 kernels; it is not K5-only. All counter syscalls are outside streaming mode. Timings are diagnostic, not acceptance results.')
print('\n| Memory | Mode | Instrumented GFLOPS | Pair us/thread | K5 us/thread | PMU scope us/thread | User cycles/thread | User instructions/thread | Aggregate CPI |')
print('| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |')
for mem in memories:
    for v,name in enumerate(['baseline','early','spread']):
        buckets=defaultdict(list)
        for r in range(6):
            samples=defaultdict(list)
            for call in range(3,8):
                c='COMPARE',mem,r,v,call
                ps=[pmu[c+(t,)] for t in range(38)]
                cycles=sum(p['user_cycles'] for p in ps);insns=sum(p['user_instructions'] for p in ps)
                for n,x in [('pair',costs[c+(0,)]['kernel_mean_us']),('k5',costs[c+(3,)]['kernel_mean_us']),('scope',mean(p['scope_us'] for p in ps)),('cycles',cycles/38),('instructions',insns/38),('cpi',cycles/insns)]:samples[n].append(x)
            for n,xs in samples.items():buckets[n].append(median(xs))
        vals=[median(buckets[n]) for n in ['pair','k5','scope','cycles','instructions','cpi']]
        g=median(averages['COMPARE',mem,r,v] for r in range(6))
        print(f'| {mem} | {name} | {g:.1f} | '+' | '.join(f'{x:.3f}' for x in vals)+' |')
print('\nObserver overhead, same executable and baseline mode; six alternating on/off orders. These changes include counter setup, ioctls, reads and scheduling disturbance, not just event counting.')
for mem in memories:
    off,on=[median(averages['OVERHEAD',mem,r,v] for r in range(6)) for v in [0,1]]
    pairs=[100*(averages['OVERHEAD',mem,r,1]/averages['OVERHEAD',mem,r,0]-1) for r in range(6)]
    print(f'{mem}: PMU off {off:.1f}, on {on:.1f} GFLOPS; on/off {100*(on/off-1):+.2f}%, paired range {min(pairs):+.2f}..{max(pairs):+.2f}%.')
print('Neither CPI nor elapsed region time identifies a physical issue port. No fixed noise threshold or universal speedup follows from these diagnostic samples.')
