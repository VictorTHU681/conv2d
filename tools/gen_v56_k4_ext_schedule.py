#!/usr/bin/env python3
"""Rebase bounded EXT control and interleave each window advance after its FMOPA group."""
from pathlib import Path
import hashlib,subprocess
root=Path('build/v56/experiments/k4-ext-schedule');root.mkdir(parents=True,exist_ok=True)
base=subprocess.check_output(['git','show','8b6b295:conv2d.c'],text=True)
old=Path('build/v56/experiments/k4-ext/k4ext.c').read_text()
assert hashlib.sha256(base.encode()).hexdigest()=='bb82ce3b4826514e9ce6f729ef017a23d5aa08d2396f5d0975a512e39da76819'
assert hashlib.sha256(old.encode()).hexdigest()=='4b96fef6c2d11b114543ae3d38b742cc05f3523fa7a77a67d1d6ccafb99688a3'
def func(t,sig):
    a=t.index(sig);return t[a:t.index('\n}\n',a)+3]
a=old.index('#define K4E_SUB');b=old.index('#define K4_EV',a);macros=old[a:b]
blocked=base.replace('#define K4_EV',macros+'#define K4_EV',1).replace(func(base,'static void k4('),func(old,'static void k4('))
subs=[f'        K4E_SUB(z{p*4}, z{p*4+1}, z{p*4+2}, z{p*4+3}, {p})\n' for p in range(4)]
advs=[f'        K4E_ADV({reg}, z{p*4}, z{p*4+1}, z{p*4+2}, z{p*4+3}, z{p+16})\n' for p,reg in enumerate(['x16','x22','x23','x25'])]
old_order=''.join(subs+advs);new_order=''.join(subs[p]+advs[p] for p in range(4))
assert blocked.count(old_order)==2
interleaved=blocked.replace(old_order,new_order)
for t in [blocked,interleaved]:
    assert func(t,'static void k4(').split('    asm volatile(')[0]==func(base,'static void k4(').split('    asm volatile(')[0]
    for sig in ['static void roll_worker(', 'static void roll_prepare(', 'static int resume_claim(', 'static void roll_link_output_dependencies(', 'static void fill_args(']:assert func(t,sig)==func(base,sig),sig
for name,t in [('baseline',base),('blocked',blocked),('interleaved',interleaved)]:
    p=root/(name+'.c');p.write_text(t);print(hashlib.sha256(p.read_bytes()).hexdigest(),p)
needle='    roll_prepare(k, H, W, KH, KW, nth);';assert interleaved.count(needle)==1
poison=interleaved.replace(needle,needle+'\n    memset(g_rp.rings,0xff,(size_t)g_rp.nthr_alloc*32768);')
p=root/'interleaved_poison.c';p.write_text(poison);print(hashlib.sha256(p.read_bytes()).hexdigest(),p)
p=root/'fbench.c';p.write_bytes(subprocess.check_output(['git','show','8b6b295:tools/fbench.c']));print(hashlib.sha256(p.read_bytes()).hexdigest(),p)
