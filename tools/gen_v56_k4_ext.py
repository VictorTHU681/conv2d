#!/usr/bin/env python3
"""Apply upstream K4 window/K9 alignment ideas while retaining local fixes and K5."""
from pathlib import Path
import hashlib,subprocess,sys
root=Path('build/v56/experiments/k4-ext');root.mkdir(parents=True,exist_ok=True)
s=subprocess.check_output(['git','show','113d3d6:conv2d.c'],text=True)
u=subprocess.check_output(['git','show','364b46d:conv2d.c'],text=True)
assert hashlib.sha256(s.encode()).hexdigest()=='4b35b3d5af1d85c8d6cf2ddc54073c0ccc75467cdc185229e0bbd906b355f905'
def once(s,a,b):
    assert s.count(a)==1,(s.count(a),a[:90]);return s.replace(a,b)
def fn(s,sig):
    a=s.index(sig);b=s.index('\n}\n',a)+3;return s[a:b]
macros=u[u.index('#define K4E_SUB('):u.index('#define K4_EV(')]
k4=s.replace('#define K4_EV(',macros+'#define K4_EV(',1)
f=fn(k4,'static void k4(')
loads='''        K4E_WIN(x16, z0, z1, z2, z3)
        K4E_WIN(x22, z4, z5, z6, z7)
        K4E_WIN(x23, z8, z9, z10, z11)
        K4E_WIN(x25, z12, z13, z14, z15)
'''
needle='        "ldr x20, [%[A], #296]\\n\\t"\n        "mov x15, x7\\n\\t"'
f=once(f,needle,loads+needle)
old='''        K4_STEP(x16, 0)
        K4_STEP(x22, 1)
        K4_STEP(x23, 2)
        K4_STEP(x25, 3)'''
new='''        K4E_SUB(z0, z1, z2, z3, 0)
        K4E_SUB(z4, z5, z6, z7, 1)
        K4E_SUB(z8, z9, z10, z11, 2)
        K4E_SUB(z12, z13, z14, z15, 3)
        K4E_ADV(x16, z0, z1, z2, z3, z16)
        K4E_ADV(x22, z4, z5, z6, z7, z17)
        K4E_ADV(x23, z8, z9, z10, z11, z18)
        K4E_ADV(x25, z12, z13, z14, z15, z19)'''
assert f.count(old)==2;f=f.replace(old,new)
for a,b in [('K4_STEP(x16, 0)','K4E_SUB(z0, z1, z2, z3, 0)'),('K4_STEP(x22, 1)','K4E_SUB(z4, z5, z6, z7, 1)'),('K4_STEP(x23, 2)','K4E_SUB(z8, z9, z10, z11, 2)')]: f=once(f,a,b)
f=once(f,': XCLOB, "z0", "z1", "z2", "z3", "z4", "z25",',': XCLOB, '+', '.join('"z%d"'%i for i in range(21))+', "z25",')
original=fn(k4,'static void k4(')
assert f[:f.index('    asm volatile(')]==original[:original.index('    asm volatile(')]
k4=once(k4,original,f)
def align(s):
    f=fn(s,'static __attribute__((noinline)) void k8f(')
    # Local K9 reuses four even-plane vectors. Preload them before branching.
    needle='        "ld1w {z6.s}, p0/z, [x16, #3, mul vl]\\n\\t"\n        "2:\\n\\t"'
    replacement='        "ld1w {z6.s}, p0/z, [x16, #3, mul vl]\\n\\t"\n        "b 2f\\n\\t"\n        ".p2align 7\\n"\n        "2:\\n\\t"'
    return once(s,f,once(f,needle,replacement))
variants={'baseline':s,'k4ext':k4,'k9align':align(s),'both':align(k4)}
for name,v in variants.items():
    for sig in ['static void roll_worker(', 'static int resume_claim(', 'static void roll_link_output_dependencies(', 'static void roll_prepare(', 'static void fill_args(', 'static __attribute__((noinline)) void roll_first_planes(', 'static __attribute__((noinline)) void k5(']:
        assert fn(s,sig)==fn(v,sig),(name,sig)
    (root/(name+'.c')).write_text(v)
    if name in ['baseline','k4ext']:
        poisoned=once(v,'    roll_prepare(k, H, W, KH, KW, nth);','    roll_prepare(k, H, W, KH, KW, nth);\n    memset(g_rp.rings,0xff,(size_t)g_rp.nthr_alloc*32768); // Diagnostic NaN poison only.')
        (root/(name+'_poison.c')).write_text(poisoned)
(root/'fbench.c').write_bytes(subprocess.check_output(['git','show','113d3d6:tools/fbench.c']))
for p in [root/(n+'.c') for n in list(variants)+['baseline_poison','k4ext_poison','fbench']]:print(hashlib.sha256(p.read_bytes()).hexdigest(),p)
guard=Path('tools/test_v56_planar_full_guard.c').read_text().replace('17,39,40,41,399,400','17,39,40,41,63,64,65,399,400').replace('k<14','k<17')
(root/'guard.c').write_text(guard)
# Bound every full boundary-vector load within its own internally padded plane.
checked=0
for kw in range(3,401):
    for sh in range(16):
        ncp=kw+255+sh;tsb=(((ncp+3)//4+15)&~15)*4+64;it=(kw+3)//4
        for sub in range(4):
            off=((sh+sub)//4)*4
            assert off+256<=tsb
            assert off+4*(it-1)+320<=tsb,(kw,sh,sub,tsb)
            checked+=1
report=f'K4 internal-plane boundary-vector bounds PASS configurations={checked}\n'
(root/'bounds.txt').write_text(report);print(report.strip(),file=sys.stderr)
