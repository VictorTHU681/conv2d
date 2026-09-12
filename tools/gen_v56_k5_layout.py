#!/usr/bin/env python3
"""Rebase the isolated K5 candidate and match F4 outlining on both sides."""
from pathlib import Path
import hashlib,subprocess
root=Path('build/v56/experiments/k5-layout');root.mkdir(parents=True,exist_ok=True)
base=subprocess.check_output(['git','show','4817eff:conv2d.c'])
common=subprocess.check_output(['git','show','68f0276:conv2d.c'])
legacy=Path('build/v56/experiments/k5-triplet/triplet.c').read_bytes()
assert hashlib.sha256(legacy).hexdigest()=='126a9a86bc805cff11a3c5c1c2ed1aa713e03bdadf753b538b3e416a220cc798'
for name,data in [('baseline',base),('common',common),('legacy',legacy)]: (root/(name+'.c')).write_bytes(data)
r=subprocess.run(['git','merge-file','-p',str(root/'baseline.c'),str(root/'common.c'),str(root/'legacy.c')],capture_output=True,text=True)
assert r.returncode==0,r.stderr
s=r.stdout;(root/'triplet.c').write_text(s)
for sig in ['static void roll_link_output_dependencies(', 'static int resume_claim(', 'static void fill_args(', 'static __attribute__((noinline)) void roll_first_planes(']:
    def function(x):
        a=x.index(sig);b=x.index('\n}\n',a)+3;return x[a:b]
    assert function(base.decode())==function(s),sig
for name in ['baseline','triplet']:
    s=(root/(name+'.c')).read_text();old='static void k16pairf4(const kp_t* P)'
    assert s.count(old)==1
    (root/(name+'_out.c')).write_text(s.replace(old,'static __attribute__((noinline)) void k16pairf4(const kp_t* P)'))
for name in ['baseline','triplet','baseline_out','triplet_out']:
    p=root/(name+'.c');print(hashlib.sha256(p.read_bytes()).hexdigest(),p)
