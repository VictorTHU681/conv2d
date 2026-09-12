#!/usr/bin/env python3
"""Isolate modular phase setup and ZA carry-loop overhead controls."""
from pathlib import Path
import hashlib,subprocess
root=Path('build/v56/experiments/chunk-setup');root.mkdir(parents=True,exist_ok=True)
s=subprocess.check_output(['git','show','8b6b295:conv2d.c'],text=True)
assert hashlib.sha256(s.encode()).hexdigest()=='bb82ce3b4826514e9ce6f729ef017a23d5aa08d2396f5d0975a512e39da76819'
def phase(v):
    old='static void roll_worker(int tid, int nth, const ctx_t* c)'
    helper='''// a and b are normalized kernel-row phases in [0, kh).
static inline long roll_phase_sub(long a, long b, long kh)
{
    long d=a-b; return d<0 ? d+kh : d;
}
'''
    assert v.count(old)==1;v=v.replace(old,helper+old)
    old='        uint64_t t0 = g_roll_diag ? cyc() : 0;\n        kp_t K ='
    new='''        uint64_t t0 = g_roll_diag ? cyc() : 0;
        const long jp=ja % KH;
        const long ya=roll_phase_sub(jp,g->s_base,KH);
        const long yb=ya>=16 ? ya-16 : ya+KH-16;
        const long ca=ya+1==KH ? 0 : ya+1, cb=yb+1==KH ? 0 : yb+1;
        kp_t K ='''
    assert v.count(old)==1;v=v.replace(old,new)
    replacements={
        '((ja + 1 - g->s_base) % KH + KH) % KH':'ca',
        '((ja + 1 - g->s_base - 16) % KH + KH) % KH':'cb',
        '((ja - g->s_base) % KH + KH) % KH':'ya',
        '((ja - g->s_base - 16) % KH + KH) % KH':'yb',
        '((ja - sF) % KH + KH) % KH':'roll_phase_sub(jp,sF,KH)',
        '((sF - g->s_base) % KH + KH) % KH':'roll_phase_sub(sF,g->s_base,KH)',
        '((ja - sF1) % KH + KH) % KH':'roll_phase_sub(jp,sF1,KH)',
        '((ja - sF2) % KH + KH) % KH':'roll_phase_sub(jp,sF2,KH)',
        '((sF1 - g->s_base) % KH + KH) % KH':'roll_phase_sub(sF1,g->s_base,KH)',
        '((sF2 - g->s_base) % KH + KH) % KH':'roll_phase_sub(sF2,g->s_base,KH)',
    }
    a=v.index('static void roll_worker(')
    b=v.index('\nstatic void roll_diag_print(',a);w=v[a:b]
    for old,new in replacements.items():assert old in w,old;w=w.replace(old,new)
    return v[:a]+w+v[b:]
def carry(v):
    for op in ['str','ldr']:
        old=f'''"49: {op} za[w12, 0], [%[p]]\\n\\t"
                 "add %[p], %[p], #64\\n\\t"
                 "add w12, w12, #1\\n\\t"'''
        body=''.join(f'                 "{op} za[w12, {i}], [%[p], #{i}, mul vl]\\n\\t"\n' for i in range(4))
        new='"49:\\n\\t"\n'+body+'                 "add %[p], %[p], #256\\n\\t"\n                 "add w12, w12, #4\\n\\t"'
        assert v.count(old)==1,(op,v.count(old));v=v.replace(old,new)
    return v
variants={'baseline':s,'phase':phase(s),'carry4':carry(s),'both':carry(phase(s))}
for name,v in variants.items():
    # No grouping, work ownership, coefficient packing or kernel arithmetic changes.
    for sig in ['static int resume_claim(', 'static void roll_prepare(', 'static void roll_link_output_dependencies(', 'static void fill_args(', 'static void k16pairf4(']:
        def extract(t):
            a=t.index(sig);return t[a:t.index('\n}\n',a)+3]
        assert extract(v)==extract(s),(name,sig)
    p=root/(name+'.c');p.write_text(v);print(hashlib.sha256(p.read_bytes()).hexdigest(),p)
p=root/'fbench.c';p.write_bytes(subprocess.check_output(['git','show','8b6b295:tools/fbench.c']));print(hashlib.sha256(p.read_bytes()).hexdigest(),p)

# The host equivalence check uses the exact normalized phase helper emitted above.
proof=Path('tools/test_v56_chunk_phases.c').read_text()
def helper(t):
    a=t.index('static inline long roll_phase_sub(');return t[a:t.index('\n}\n',a)+3]
assert helper(proof)==helper(variants['phase'])
