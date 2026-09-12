#!/usr/bin/env python3
"""Stage immutable upstream kf sharing over the locally corrected F4 gate."""
from pathlib import Path
import hashlib, subprocess
root=Path('build/v56/experiments/kf-share');root.mkdir(parents=True,exist_ok=True)
for name,rev in [('baseline','4817eff'),('common','87fa5d7'),('upstream','76ec03d')]:
    (root/(name+'.c')).write_bytes(subprocess.check_output(['git','show',rev+':conv2d.c']))
r=subprocess.run(['git','merge-file','-p',str(root/'baseline.c'),str(root/'common.c'),str(root/'upstream.c')],capture_output=True,text=True)
assert r.returncode==0,r.stderr
base=(root/'baseline.c').read_text();s=r.stdout
for sig in ['static void roll_link_output_dependencies(', 'static void fill_args(', 'static __attribute__((noinline)) void roll_first_planes(', 'static void roll_pack_all(', 'static void roll_worker(']:
    def function(x):
        a=x.index(sig);b=x.index('\n}\n',a)+3;return x[a:b]
    assert function(base)==function(s),sig
(root/'merged.c').write_text(s)
line='            if ((P->G[gi].kind == 34 || P->G[gi].kind == 35) && ko != gi && !__atomic_load_n(&g_pk_gdone[ko].v, __ATOMIC_ACQUIRE)) continue;'
assert s.count(line)==1
(root/'nogate.c').write_text(s.replace(line,'            (void)ko; // Deliberately missing dependency: diagnostic positive control.'))
guard=Path('tools/test_v56_planar_full_guard.c').read_text().replace('17,39,40,41,399,400','17,39,40,41,63,64,65,399,400').replace('k<14','k<17')
(root/'guard.c').write_text(guard)
for name in ['baseline','common','upstream','merged','nogate']:
    p=root/(name+'.c');print(hashlib.sha256(p.read_bytes()).hexdigest(),p)
