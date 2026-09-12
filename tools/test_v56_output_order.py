#!/usr/bin/env python3
"""Exercise extracted dependency builder and atomic claim state transitions."""
from pathlib import Path
import subprocess
import sys

root = Path('build/v56/experiments/output-order')
variant = 'pipelined' if '--pipeline' in sys.argv else 'ordered'
custom_source = Path(sys.argv[sys.argv.index('--source')+1]) if '--source' in sys.argv else None
if custom_source:
    root=custom_source.parent
s = (custom_source or root/(variant+'.c')).read_text()
types = s[s.index('typedef struct { int kind;'):s.index('static rplan_t g_rp;')]
groups = s[s.index('static int roll_groups_base('):s.index('// KW 在条带步数上限内')]
link = s[s.index('static void roll_link_output_dependencies('):s.index('static void roll_prepare(')]
claim = s[s.index('static int resume_claim('):s.index('\nstatic void roll_worker(')]
prefix = '''#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
typedef struct { uint64_t v; } padded_u64;
static padded_u64 g_pk_gdone[12];
static int env_int(const char* name,int fallback) { (void)name; return fallback; }
'''
harness = r'''
static uint32_t seed=56887;
static uint32_t rnd(void) { seed=seed*1664525u+1013904223u; return seed; }
static int overlap(const rplan_t* P,int a,int b) {
    const rpiece_t *x=&P->pieces[a],*y=&P->pieces[b];
    const ritem_t *u=&P->items[x->item],*v=&P->items[y->item];
    long width=P->G[u->g].width;
    return u->g==v->g && x->ja<y->jb && y->ja<x->jb &&
           u->base<v->base+width && v->base<u->base+width;
}
static unsigned long claims,edges,plans,resumes;
static void run(long KH,long KW,long OH,long OW) {
    rplan_t P={0};
    P.ng=roll_groups_width(KH,KW,P.G,OW);
    for(int g=0;g<P.ng;g++) if(P.G[g].width>OW) return;
    P.items=calloc(4096,sizeof(*P.items));
    P.pieces=calloc(16384,sizeof(*P.pieces));
    P.ready=calloc(16384,sizeof(*P.ready));
    assert(P.items && P.pieces && P.ready);
    for(int g=0;g<P.ng;g++) {
        long width=P.G[g].width,n=(OW+width-1)/width;
        for(long st=0;st<n;st++) {
            assert(P.nit<4096);
            long base=st*width; if(base+width>OW) base=OW-width;
            P.items[P.nit]=(ritem_t){g,base};
            long row=0;
            while(row<OH) {
                long end=row+1+rnd()%(OH/3+1); if(end>OH) end=OH;
                assert(P.npieces<16384);
                P.pieces[P.npieces++]=(rpiece_t){P.nit,row,end,0,0}; row=end;
            }
            P.nit++;
        }
    }
    roll_link_output_dependencies(&P);
    // Every pair of intersecting output rectangles is ordered; no unrelated
    // rectangle receives an unnecessary dependency. Different groups own
    // distinct row residues and are outside this cross-item check.
    for(int i=0;i<P.npieces;i++) for(int j=0;j<i;j++) {
        int dep=j>=P.pieces[i].dep_first && j<P.pieces[i].dep_end;
        assert(dep==overlap(&P,i,j)); edges+=dep;
    }
    int active[8]; long progress[8];
    for(int t=0;t<8;t++) active[t]=-1;
    int remaining=P.npieces,iterations=0;
    while(remaining) {
        assert(++iterations<P.npieces*1000);
        for(int t=0;t<8;t++) if(active[t]<0) {
            int cursor=(int)(rnd()%P.npieces); long off=-1;
            int pi=resume_claim(&P,0,P.npieces,&cursor,KH,&off,0);
            if(pi>=0) {
                for(int u=0;u<8;u++) if(active[u]>=0) assert(!overlap(&P,pi,active[u]));
                active[t]=pi; progress[t]=off; claims++; resumes+=off!=0;
            }
        }
        int t=(int)(rnd()%8),found=0;
        for(int u=0;u<8;u++) { t=(t+1)%8; if(active[t]>=0) { found=1; break; } }
        assert(found); // Incomplete work must not get stuck behind a cycle.
        int pi=active[t];
        long total=P.pieces[pi].jb-P.pieces[pi].ja+KH-1;
        long next=progress[t]+1+rnd()%(KH*2); if(next>total) next=total;
        __atomic_store_n(&P.ready[pi].v,(uint64_t)next,__ATOMIC_RELEASE);
        if(next==total) remaining--;
        active[t]=-1;
    }
    free(P.items); free(P.pieces); free(P.ready); plans++;
}
int main(void) {
    long widths[]={32,33,63,64,65,127,128,129,255,256,257,273,511,512,513};
    for(long kh=16;kh<=256;kh++) for(unsigned j=0;j<sizeof(widths)/sizeof(*widths);j++)
        run(kh,3+(kh*17)%398,j%2?535:9,widths[j]);
    run(39,39,4058,6106); run(41,41,6104,4056);
    run(55,55,4202,6336); run(81,81,6310,4176);
    assert(edges && resumes);
    printf("OUTPUT_ORDER_HOST PASS plans=%lu dependency_edges=%lu claims=%lu resumed_claims=%lu\n",
           plans,edges,claims,resumes);
    return 0;
}
'''
if variant == 'pipelined':
    prefix += 'static int g_roll_step=8;\n'
    harness = harness.replace('static unsigned long claims,edges,plans,resumes;', r'''
static int chunk_overlap(const rplan_t* P,int a,long ao,int b,long bo,long KH) {
    if(!overlap(P,a,b)) return 0;
    const rpiece_t *x=&P->pieces[a],*y=&P->pieces[b];
    long alo=x->ja+ao-KH+1,blo=y->ja+bo-KH+1;
    if(alo<x->ja) alo=x->ja; if(blo<y->ja) blo=y->ja;
    long ahi=x->ja+ao+g_roll_step*KH-KH+1,bhi=y->ja+bo+g_roll_step*KH-KH+1;
    if(ahi>x->jb) ahi=x->jb; if(bhi>y->jb) bhi=y->jb;
    return alo<bhi && blo<ahi;
}
static unsigned long claims,edges,plans,resumes;
''')
    harness = harness.replace('assert(!overlap(&P,pi,active[u]));',
                              'assert(!chunk_overlap(&P,pi,off,active[u],progress[u],KH));')
    harness = harness.replace('progress[t]+1+rnd()%(KH*2)', 'progress[t]+g_roll_step*KH')
    harness = harness.replace('    for(long kh=16;',
                              '    for(g_roll_step=1;g_roll_step<=64;g_roll_step*=2)\n    for(long kh=16;')
    harness = harness.replace('    run(39,39,4058,6106);', '    g_roll_step=8; run(39,39,4058,6106);')
    harness = harness.replace('OUTPUT_ORDER_HOST', 'OUTPUT_PIPELINE_HOST')
stem = 'host_test' if variant == 'ordered' else 'host_pipeline'
if custom_source:
    harness=harness.replace('128,129,255,256,257,273,511,512,513',
                            '128,129,191,192,193,255,256,257,273,383,384,385,511,512,513')
    harness=harness.replace('    P.items=calloc(4096,sizeof(*P.items));',r'''
    // Prove distinct groups partition the output-row residues exactly once.
    for(long row=0;row<KH;row++) {
        int owners=0;
        for(int g=0;g<P.ng;g++) {
            rgrp_t* x=&P.G[g];
            owners += row>=x->s_base && row<x->s_base+x->nvA;
            owners += x->nvB && row>=x->s_base+16 && row<x->s_base+16+x->nvB;
            int nf=x->kind==35?4:x->kind==34?3:(x->kind==33||x->kind==9)?1:0;
            owners += nf && row<=x->sf && row>x->sf-nf;
            owners += x->kind==17 && (row==KH-3 || row==KH-2);
        }
        assert(owners==1);
    }
    P.items=calloc(4096,sizeof(*P.items));''')
    import hashlib
    print('CUSTOM_SOURCE',custom_source,hashlib.sha256(s.encode()).hexdigest(),flush=True)
(root/(stem+'.c')).write_text(prefix+types+groups+link+claim+harness)
subprocess.run(['gcc','-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer',
                str(root/(stem+'.c')),'-o',str(root/stem)],check=True)
subprocess.run([str(root/stem)],check=True)
