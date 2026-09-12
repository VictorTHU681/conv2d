#!/usr/bin/env python3
"""Isolate executed-step scheduling costs without changing K5 kernel bodies."""
from pathlib import Path
import hashlib,subprocess
root=Path('build/v56/experiments/k5-cost');root.mkdir(parents=True,exist_ok=True)
base=subprocess.check_output(['git','show','4817eff:conv2d.c'])
s=Path('build/v56/experiments/k5-layout/triplet.c').read_text()
assert hashlib.sha256(s.encode()).hexdigest()=='4b35b3d5af1d85c8d6cf2ddc54073c0ccc75467cdc185229e0bbd906b355f905'
(root/'baseline.c').write_bytes(base);(root/'triplet.c').write_text(s)
old='P->cost[P->nit] = (double)G->steps * outH * w;'
assert s.count(old)==1
for name,expr in [('k5cost','G->kind == 5 ? KW + 2 : G->steps'),('tailcost','G->kind == 5 ? KW + 2 : G->kind == 4 ? KW + 3 : G->steps')]:
    v=s.replace(old,'P->cost[P->nit] = (double)('+expr+') * outH * w;')
    for sig in ['static void roll_worker(', 'static int resume_claim(', 'static void roll_link_output_dependencies(', 'static int roll_groups_width(']:
        def extract(t):
            a=t.index(sig);b=t.index('\n}\n',a)+3;return t[a:b]
        assert extract(s)==extract(v),sig
    (root/(name+'.c')).write_text(v)
for name in ['baseline','triplet','k5cost','tailcost']:
    p=root/(name+'.c');print(hashlib.sha256(p.read_bytes()).hexdigest(),p)
