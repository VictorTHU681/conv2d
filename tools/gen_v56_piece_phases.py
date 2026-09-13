#!/usr/bin/env python3
"""Precompute shape-only piece phases in existing structure padding each call."""
from pathlib import Path
import hashlib,subprocess
root=Path('build/v56/experiments/piece-phases');root.mkdir(parents=True,exist_ok=True)
s=Path('build/v56/experiments/chunk-setup/baseline.c').read_text()
phase=Path('build/v56/experiments/chunk-setup/phase.c').read_text()
assert hashlib.sha256(s.encode()).hexdigest()=='bb82ce3b4826514e9ce6f729ef017a23d5aa08d2396f5d0975a512e39da76819'
v=s
def once(old,new):
    global v
    assert v.count(old)==1,(v.count(old),old[:80]);v=v.replace(old,new)
once('typedef struct { int item; long ja, jb; int dep_first, dep_end; } rpiece_t;', '''typedef struct { int item; unsigned char ya, yb, af, cf; long ja, jb; int dep_first, dep_end; } rpiece_t;
_Static_assert(sizeof(rpiece_t)==32 && offsetof(rpiece_t,ja)==8 && offsetof(rpiece_t,dep_first)==24,
               "piece phases must use only former padding");''')
once('(rpiece_t){i, r, outH}', '(rpiece_t){.item=i, .ja=r, .jb=outH}')
once('(rpiece_t){i, r, r + rows}', '(rpiece_t){.item=i, .ja=r, .jb=r+rows}')
a=phase.index('static inline long roll_phase_sub(');b=phase.index('\n}\n',a)+3
once('static void roll_prepare(',phase[a:b]+'\nstatic void roll_prepare(')
once('        roll_link_output_dependencies(P);','''        roll_link_output_dependencies(P);
        // Continuation offsets are multiples of KH, so these phases are
        // constant within a piece. Rebuild them with every call's plan.
        for(int pi=0;pi<P->npieces;pi++) {
            rpiece_t* pc=&P->pieces[pi]; const rgrp_t* g=&P->G[P->items[pc->item].g];
            long jp=pc->ja % KH, ya=roll_phase_sub(jp,g->s_base,KH);
            pc->ya=(unsigned char)ya;
            pc->yb=(unsigned char)(ya>=16 ? ya-16 : ya+KH-16);
            pc->af=(unsigned char)roll_phase_sub(jp,g->sf,KH);
            pc->cf=(unsigned char)roll_phase_sub(g->sf,g->s_base,KH);
        }''')
a=v.index('static void roll_worker(');b=v.index('\nstatic void roll_diag_print(',a);w=v[a:b]
replacements={
    '((ja + 1 - g->s_base) % KH + KH) % KH':'(pc->ya+1==KH ? 0 : pc->ya+1)',
    '((ja + 1 - g->s_base - 16) % KH + KH) % KH':'(pc->yb+1==KH ? 0 : pc->yb+1)',
    '((ja - g->s_base) % KH + KH) % KH':'pc->ya',
    '((ja - g->s_base - 16) % KH + KH) % KH':'pc->yb',
    '((ja - sF) % KH + KH) % KH':'pc->af',
    '((sF - g->s_base) % KH + KH) % KH':'pc->cf',
}
for old,new in replacements.items():assert old in w,old;w=w.replace(old,new)
v=v[:a]+w+v[b:]
for sig in ['static int resume_claim(', 'static void roll_link_output_dependencies(', 'static void k16pairf3(', 'static void k16pairf4(', 'static void fill_args(']:
    def extract(t):
        a=t.index(sig);return t[a:t.index('\n}\n',a)+3]
    assert extract(v)==extract(s),sig
for name,t in [('baseline',s),('phase',phase),('cached',v)]:
    p=root/(name+'.c');p.write_text(t);print(hashlib.sha256(p.read_bytes()).hexdigest(),p)
p=root/'fbench.c';p.write_bytes(subprocess.check_output(['git','show','8b6b295:tools/fbench.c']));print(hashlib.sha256(p.read_bytes()).hexdigest(),p)
