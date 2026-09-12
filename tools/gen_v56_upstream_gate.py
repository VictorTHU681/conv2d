#!/usr/bin/env python3
"""Merge upstream long-row F4 gate with locally accepted correctness fixes."""
from pathlib import Path
import hashlib
import subprocess

root=Path('build/v56/experiments/upstream-gate');root.mkdir(parents=True,exist_ok=True)
for name,rev in [('baseline','68f0276'),('common','b9591de'),('upstream','87fa5d7')]:
    (root/(name+'.c')).write_bytes(subprocess.check_output(['git','show',rev+':conv2d.c']))
r=subprocess.run(['git','merge-file','-p',str(root/'baseline.c'),str(root/'common.c'),str(root/'upstream.c')],
                 capture_output=True,text=True)
assert r.returncode==0,r.stderr
(root/'merged.c').write_text(r.stdout)
# Output ownership and bounded first-copy helpers must survive unchanged.
base=(root/'baseline.c').read_text()
for signature in ['static void roll_link_output_dependencies(', 'static int resume_claim(',
                  'static __attribute__((noinline)) void roll_first_planes(', 'static void fill_args(']:
    def function(s):
        a=s.index(signature);b=s.index('\n}\n',a)+3;return s[a:b]
    assert function(base)==function(r.stdout),signature
for name in ['baseline','common','upstream','merged']:
    p=root/(name+'.c');print(hashlib.sha256(p.read_bytes()).hexdigest(),p)
guard=Path('tools/test_v56_planar_full_guard.c').read_text()
assert '17,39,40,41,399,400' in guard
guard=guard.replace('17,39,40,41,399,400','17,39,40,41,63,64,65,399,400').replace('k<14','k<17')
# This generated driver is beside the source; expose tools/ for its reference include.
(root/'guard.c').write_text(guard)
