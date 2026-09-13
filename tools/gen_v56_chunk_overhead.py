#!/usr/bin/env python3
"""Instrument continuation phase costs; diagnostic-only, never packaged."""
from pathlib import Path
import subprocess,hashlib,argparse
parser=argparse.ArgumentParser()
parser.add_argument('--root',type=Path,default=Path('build/v56/experiments/chunk-overhead'))
parser.add_argument('--variant',default='candidate')
args=parser.parse_args();root=args.root
subprocess.run(['python3','tools/gen_v56_k5_profile.py','--root',str(root),'--variants',args.variant,'--thread-detail'],check=True,stdout=subprocess.DEVNULL)
p=root/(args.variant+'_profile.c');s=p.read_text()
def once(old,new):
    global s
    assert s.count(old)==1,(s.count(old),old[:80])
    s=s.replace(old,new)
once('static uint64_t k5_start_ticks[1024];','''static uint64_t k5_start_ticks[1024];
typedef struct {
    uint64_t claim, setup, restore, kernel, publish;
    unsigned long chunks, resumes, saves, steals, rows;
} chunk_prof_t;
static chunk_prof_t chunk_prof[1024];
static inline uint64_t chunk_tick(void) {
    asm volatile("" ::: "memory");
    uint64_t t=cyc();
    asm volatile("" ::: "memory"); return t;
}''')
once('    k5_start_ticks[tid]=t_start;', '    k5_start_ticks[tid]=t_start;\n    chunk_prof_t* CP=&chunk_prof[tid]; memset(CP,0,sizeof(*CP));')
a=s.index('static void roll_worker(');b=s.index('\nstatic void roll_diag_print(',a)
w=s[a:b]
def change(old,new):
    global w
    assert w.count(old)==1,(w.count(old),old[:80]);w=w.replace(old,new)
change('        long off = 0;', '        uint64_t ct0=chunk_tick();\n        long off = 0;')
change('        if (pi < 0) {', '        uint64_t ct1=chunk_tick(); CP->claim+=ct1-ct0;\n        if (pi < 0) {')
change('        K.carry = state + 1024; K.resume = off != 0;', '        K.carry = state + 1024; K.resume = off != 0;\n        uint64_t ct2=chunk_tick(); CP->setup+=ct2-ct1;')
change('        if (off) carry_load_za(state); else sme_zero_za();','        if (off) carry_load_za(state); else sme_zero_za();\n        uint64_t ct3=chunk_tick(); CP->restore+=ct3-ct2;')
change('        if (g_roll_diag) { int ki = roll_kind_idx(g->kind);', '        uint64_t ct4=chunk_tick(); CP->kernel+=ct4-ct3;\n        if (g_roll_diag) { int ki = roll_kind_idx(g->kind);')
publication='        __atomic_store_n(&P->ready[pi].v, (uint64_t)(off + rows), __ATOMIC_RELEASE);'
if 'g_roll_unfinished' in w:
    publication+='\n        if (g_roll_guided && off + rows == total)\n            __atomic_sub_fetch(&g_roll_unfinished.v, 1, __ATOMIC_RELAXED);'
change(publication,publication+'''
        uint64_t ct5=chunk_tick(); CP->publish+=ct5-ct4;
        CP->chunks++; CP->resumes+=off!=0; CP->saves+=off+rows<total;
        CP->steals+=pi<first || pi>=last; CP->rows+=(unsigned long)rows;''')
s=s[:a]+w+s[b:]
once('    uint64_t origin=k5_start_ticks[0];','''    for(int t=0;t<nth;t++) {
        const chunk_prof_t* q=&chunk_prof[t];
        fprintf(stderr,"CHUNK_DETAIL call=%lu tid=%d claim_us=%.3f setup_us=%.3f restore_us=%.3f kernel_us=%.3f publish_us=%.3f chunks=%lu resumes=%lu saves=%lu steals=%lu rows=%lu\\n",
            call,t,q->claim*1e6/hz,q->setup*1e6/hz,q->restore*1e6/hz,q->kernel*1e6/hz,q->publish*1e6/hz,
            q->chunks,q->resumes,q->saves,q->steals,q->rows);
    }
    uint64_t origin=k5_start_ticks[0];''')
p.write_text(s);print(hashlib.sha256(p.read_bytes()).hexdigest(),p)
