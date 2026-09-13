#!/usr/bin/env python3
"""Audit hash-between-timings intervention with fixed operator binaries."""
from pathlib import Path
from statistics import median
from collections import defaultdict,Counter
import re,sys
root=Path('results/post64/hash-between');s=Path(sys.argv[1]).read_text()
assert 'HASH_BETWEEN_DONE' in s and 'FAIL' not in s
for line in (root/'sources.sha256').read_text().splitlines():
 h,p=line.split();assert re.search(r'^'+h+r'\s+'+re.escape(p)+r'$',s,re.M)
for n in ['baseline','all']:assert re.search(r'^[0-9a-f]{64}\s+build/post64/hash-between/bench_'+n+r'$',s,re.M)
m=re.search(r'^PLACEMENT cpu_node=\d+ hbm_node=(-?\d+)$',s,re.M);assert m
memories=['DDR'] if int(m[1])<0 else ['DDR','HBM']
conditions=[('baseline',1),('all',1),('baseline',0),('all',0)]
shapes={39:(4096,6144,39,39),41:(6144,4096,41,41),55:(4256,6390,55,55)}
orders=defaultdict(list);runs=defaultdict(list);data={};key=None;checked=unchecked=0
for line in s.splitlines():
 m=re.match(r'HASH_BETWEEN memory=(\w+) round=(\d+) condition=(\d+) variant=(\w+) hash_each=(\d+) shape=(\d+) (\d+) (\d+) (\d+)$',line)
 if m:
  assert key is None;kh=int(m[8]);assert tuple(map(int,m.groups()[5:]))==shapes[kh]
  condition=int(m[3]);assert (m[4],int(m[5]))==conditions[condition]
  key=m[1],int(m[2]),condition,kh;orders[key[0],key[1],kh].append(condition)
 m=re.search(r' run(\d+)\s+[\d.]+ ms\s+[\d.]+ GFLOPS (PASS|UNCHECKED)$',line)
 if m:
  assert key is not None;r=int(m[1]);h=conditions[key[2]][1]
  expected='PASS' if h or r==4 else 'UNCHECKED';assert m[2]==expected
  runs[key].append(r);checked+=expected=='PASS';unchecked+=expected=='UNCHECKED'
 m=re.search(r'\| avg\s+[\d.]+ ms\s+([\d.]+) GFLOPS\s+PASS$',line)
 if m:
  assert key is not None and key not in data and runs[key]==list(range(5));data[key]=float(m[1]);key=None
assert key is None
assert set(data)=={(m,r,c,k) for m in memories for r in range(8) for c in range(4) for k in shapes}
for m in memories:
 for k in shapes:
  seqs=[orders[m,r,k] for r in range(8)]
  assert all(sorted(seq)==list(range(4)) for seq in seqs)
  assert all(Counter(seq[pos] for seq in seqs)==Counter({c:2 for c in range(4)}) for pos in range(4))
  assert Counter((seq[i],seq[i+1]) for seq in seqs for i in range(3))==Counter({(a,b):2 for a in range(4) for b in range(4) if a!=b})
assert checked==len(data)*3 and unchecked==len(data)*2
print(f'{len(data)} processes completed initial hash validation; {checked} timed-output hashes PASS; {unchecked} timed outputs explicitly UNCHECKED (first four in last-only mode). Each process has a checked final timed output.')
print('Eight balanced condition orders; same operator binary used for both hash modes. Driver differs from the official benchmark and changes linked layout. Diagnostic only; no production acceptance or historical adjustment follows from this comparison.')
print('\n| Memory | KH | Hash mode | Baseline | Indexed all | All/base |')
print('| --- | ---: | --- | ---: | ---: | ---: |')
for mem in memories:
 for k in shapes:
  for label,a,b in [('each',0,1),('last-only',2,3)]:
   x,y=[median(data[mem,r,c,k] for r in range(8)) for c in [a,b]]
   print(f'| {mem} | {k} | {label} | {x:.1f} | {y:.1f} | {100*(y/x-1):+.2f}% |')
print('\n| Memory | KH | Baseline last-only/each | Indexed-all last-only/each |')
print('| --- | ---: | ---: | ---: |')
for mem in memories:
 for k in shapes:
  xs=[median(data[mem,r,c,k] for r in range(8)) for c in range(4)]
  print(f'| {mem} | {k} | {100*(xs[2]/xs[0]-1):+.2f}% | {100*(xs[3]/xs[1]-1):+.2f}% |')
print('\nPaired all/base ranges retain every outlier; not confidence intervals.')
for mem in memories:
 for k in shapes:
  for label,a,b in [('each',0,1),('last-only',2,3)]:
   xs=[100*(data[mem,r,b,k]/data[mem,r,a,k]-1) for r in range(8)]
   print(f'{mem} KH{k} {label}: median {median(xs):+.2f}%, range {min(xs):+.2f}..{max(xs):+.2f}%, positive {sum(x>0 for x in xs)}/8')
print('\nPaired last-only/each ranges within each operator binary; not confidence intervals.')
for mem in memories:
 for k in shapes:
  for label,a,b in [('baseline',0,2),('indexed-all',1,3)]:
   xs=[100*(data[mem,r,b,k]/data[mem,r,a,k]-1) for r in range(8)]
   print(f'{mem} KH{k} {label}: median {median(xs):+.2f}%, range {min(xs):+.2f}..{max(xs):+.2f}%, positive {sum(x>0 for x in xs)}/8')
