#!/usr/bin/env python3
"""Measure matrix/EXT issue budgets and K4-like dependency scheduling."""
from pathlib import Path
import hashlib
root=Path('build/v56/experiments/ext-throughput');root.mkdir(parents=True,exist_ok=True)
variants=[]
for n in [0,4,8,16]:
    ops=[];j=0
    for tile in range(4):
        ops.append(f'fmopa za{tile}.s, p0/m, p0/m, z0.s, z1.s')
        for _ in range(n//4):
            ops.append(f'ext z{8+j}.b, z{8+j}.b, z{8+(j+1)%24}.b, #4');j+=1
    variants.append((f'mix{n}',ops,1))
for interleaved in [False,True]:
    subs=[];advs=[]
    for plane in range(4):
        zs=4*plane
        subs.append([f'fmopa za{t}.s, p0/m, p0/m, z{zs+t}.s, z20.s' for t in range(4)])
        advs.append([f'ext z{zs+t}.b, z{zs+t}.b, z{zs+t+1 if t<3 else 16+plane}.b, #4' for t in range(4)])
    ops=sum([subs[p]+advs[p] for p in range(4)],[]) if interleaved else sum(subs,[])+sum(advs,[])
    variants.append(('window_interleaved' if interleaved else 'window_block',ops,4))
def strings(ops):return ''.join('        "'+op+'\\n\\t"\n' for op in ops)
s='''// Standalone synthetic diagnostic, never an operator or submission artifact.
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <omp.h>
static uint64_t hz(void) { uint64_t t;asm volatile("mrs %0, cntfrq_el0":"=r"(t));return t; }
typedef uint64_t (*probe_t)(long);
'''
for name,ops,groups in variants:
    s+=f'static __attribute__((noinline,aligned(128))) uint64_t {name}(long iters) {{\n    uint64_t begin,end;\n    asm volatile(\n'
    init=['smstart','ptrue p0.s']+[f'fmov z{r}.s, #{1 if r%2==0 else 2}.0' for r in range(32)]+['zero {za}','isb','mrs %[begin], cntvct_el0','b 1f','.p2align 7','1:']
    s+=strings(init+ops*4+['subs %[iters], %[iters], #1','b.ne 1b','isb','mrs %[end], cntvct_el0','smstop'])
    s+='        : [begin]"=&r"(begin),[end]"=&r"(end),[iters]"+r"(iters)\n        : : '+','.join(f'"z{r}"' for r in range(32))+',"p0","cc","memory");\n    return end-begin;\n}\n'
s+='static probe_t funcs[]={'+','.join(n for n,_,_ in variants)+'};\n'
s+='static const char* names[]={'+','.join('"'+n+'"' for n,_,_ in variants)+'};\n'
s+='static const int groups[]={'+','.join(str(g) for _,_,g in variants)+'};\n'
s+='''int main(int argc,char** argv) {
    long iters=argc>1?atol(argv[1]):1000000;if(iters<1)return 2;
    int nt=omp_get_max_threads();double* times=calloc(nt,sizeof(double));if(!times)return 3;
    double freq=(double)hz();printf("EXT_TIMER_HZ %.0f threads=%d iters=%ld\\n",freq,nt,iters);
    for(int round=0;round<3;round++) for(int j=0;j<6;j++) {
        int v=round%2?5-j:j,used=0;
        #pragma omp parallel shared(used)
        {
            int tid=omp_get_thread_num();
            #pragma omp single
            used=omp_get_num_threads();
            funcs[v](1000);
            #pragma omp barrier
            times[tid]=(double)funcs[v](iters)*1e9/(freq*iters*4.0*groups[v]);
        }
        double mn=times[0],mx=mn,total=0;
        for(int t=0;t<used;t++) { if(times[t]<mn)mn=times[t];if(times[t]>mx)mx=times[t];total+=times[t]; }
        printf("EXT_BUDGET round=%d variant=%s threads=%d ns_per_four_fmopa_min=%.6f mean=%.6f max=%.6f\\n",round,names[v],used,mn,total/used,mx);
    }
    free(times);return 0;
}
'''
p=root/'probe.c';p.write_text(s);print(hashlib.sha256(p.read_bytes()).hexdigest(),p)
