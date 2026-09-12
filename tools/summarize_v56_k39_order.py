#!/usr/bin/env python3
"""Summarize balanced original-benchmark runs separately from runtime profiles."""
from collections import Counter,defaultdict
from pathlib import Path
from statistics import median
import re,sys
s=Path(sys.argv[1]).read_text()
assert 'K39_ORDER_DONE' in s and 'FAIL' not in s
rows=defaultdict(dict);data=defaultdict(list);profiles=defaultdict(list);key=None;prof=None;profile_checks=0
for line in s.splitlines():
    m=re.match(r'K39_ORDER memory=HBM round=(\d+) variant=(\S+) position=(\d+)',line)
    if m:
        assert key is None
        key=int(m[1]),m[2],int(m[3])
    m=re.match(r'K39_PROFILE memory=HBM variant=(\S+)',line)
    if m: prof=m[1];assert key is None
    m=re.match(r'\s*4096\s*x\s*6144\s+39\s*x\s*39\s+([\d.]+)\s+([\d.]+)\s+(\S+)\s+(PASS|FAIL)',line)
    if m:
        assert m[4]=='PASS' and float(m[3])==0
        if key:
            r,v,p=key;assert p not in rows[r]
            rows[r][p]=v;data[v].append(float(m[2]));key=None
        elif prof: profile_checks+=1
    m=re.search(r'周期/tile步: pair ([\d.]+).*4x4 ([\d.]+) \| 份额 %: ([\d.]+) .* ([\d.]+)$',line)
    if m and prof: profiles[prof].append(tuple(map(float,m.groups())))
assert len(data)==6 and all(len(v)==6 for v in data.values()) and profile_checks==6
assert set(rows)==set(range(6)) and all(set(r)==set(range(6)) for r in rows.values())
pred=Counter((r[p-1],r[p]) for r in rows.values() for p in range(1,6))
assert len(pred)==30 and set(pred.values())=={1}
assert all(len({r[p] for r in rows.values()})==6 for p in range(6))
print('36 uninstrumented full-reference checks and 6 diagnostic full-reference checks PASS, all maximum errors 0.')
print('All process positions and all 30 ordered predecessor pairs are balanced.')
print('\n| Variant | Median GFLOPS | vs baseline | Min GFLOPS | Max GFLOPS |')
print('| --- | ---: | ---: | ---: | ---: |')
base=median(data['baseline'])
for v,x in data.items():
    print(f'| {v} | {median(x):.1f} | {100*(median(x)/base-1):+.2f}% | {min(x):.1f} | {max(x):.1f} |')
print('\nRuntime-profile medians of the final two timed calls; validation and warmup excluded.')
print('Cycles are the existing counter normalization at 1.55 GHz, not per-instruction latency or IPC.')
print('| Variant | Pair cycles/tile-step | K4 cycles/tile-step | Pair work time % | K4 work time % |')
print('| --- | ---: | ---: | ---: | ---: |')
for v,x in profiles.items():
    assert len(x)==4
    a=[median(t[i] for t in x[-2:]) for i in range(4)]
    print('| '+v+' | '+' | '.join(f'{y:.2f}' for y in a)+' |')
