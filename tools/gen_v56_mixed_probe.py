#!/usr/bin/env python3
"""Generate a standalone arithmetic-throughput diagnostic, not a convolution."""
from pathlib import Path
import hashlib
import sys
indexed='--indexed' in sys.argv
root=Path('build/v56/experiments/mixed-throughput'+('-indexed' if indexed else ''));root.mkdir(parents=True,exist_ok=True)
variants=[('mix'+str(n),4,n) for n in (0,2,4,6,8,10,12,16,18)]
variants += [('vec'+str(n),0,n) for n in (2,4,8,16,18)]
s='''// Synthetic matrix/vector throughput diagnostic; never a submission source.
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <omp.h>
static uint64_t timer_hz(void) { uint64_t v; asm volatile("mrs %0, cntfrq_el0" : "=r"(v)); return v; }
typedef uint64_t (*probe_t)(long);
'''
def strings(ops):return ''.join('        "'+op+'\\n\\t"\n' for op in ops)
for name,matrix,nf in variants:
    s+=f'static __attribute__((noinline,aligned(128))) uint64_t {name}(long remaining) {{\n    uint64_t begin,end;\n    asm volatile(\n'
    init=['smstart','ptrue p0.s','fmov z0.s, #1.0','fmov z1.s, #1.0','zero {za}']
    if indexed:init += [f'fmov z{r}.s, #1.0' for r in [4,5,6]]
    init += [f'fmov z{r}.s, #0.0' for r in range(8,32)]
    s+=strings(init+['isb','mrs %[begin], cntvct_el0','.p2align 6','1:'])
    step=[]
    if matrix:
        acc=8
        for tile in range(4):
            step.append(f'fmopa za{tile}.s, p0/m, p0/m, z0.s, z1.s')
            for _ in range(nf//4+(tile<nf%4)):
                j=acc-8
                step.append(f'fmla z{acc}.s, z{j%2}.s, z{4+j//8}.s[{(j//2)%4}]' if indexed else f'fmla z{acc}.s, p0/m, z0.s, z1.s');acc+=1
        assert acc==8+nf
    else:
        step=[f'fmla z{8+j}.s, z{j%2}.s, z{4+j//8}.s[{(j//2)%4}]' if indexed else f'fmla z{8+j}.s, p0/m, z0.s, z1.s' for j in range(nf)]
    s+=strings(step*4+['subs %[remaining], %[remaining], #1','b.ne 1b','isb','mrs %[end], cntvct_el0','smstop'])
    s+='        : [begin]"=&r"(begin), [end]"=&r"(end), [remaining]"+r"(remaining)\n        : : '+', '.join('"z'+str(r)+'"' for r in [0,1]+([4,5,6] if indexed else [])+list(range(8,32)))+', "p0", "memory", "cc");\n    return end-begin;\n}\n'
s+='static probe_t funcs[]={'+','.join(v[0] for v in variants)+'};\n'
s+='static const char* names[]={'+','.join('"'+v[0]+'"' for v in variants)+'};\n'
s+='''int main(int argc,char** argv) {
    long iters=argc>1?atol(argv[1]):1000000;
    if(iters<1)return 2;
    int nt=omp_get_max_threads();
    double* times=calloc((size_t)nt,sizeof(double));
    if(!times)return 3;
    double hz=(double)timer_hz();
    printf("MIXED_TIMER_HZ %.0f threads=%d outer_iters=%ld steps_per_iter=4\\n",hz,nt,iters);
    for(int round=0;round<3;round++) for(int j=0;j<(int)(sizeof(funcs)/sizeof(funcs[0]));j++) {
        int v=round%2?((int)(sizeof(funcs)/sizeof(funcs[0]))-1-j):j;
        int used=0;
        #pragma omp parallel shared(used)
        {
            int tid=omp_get_thread_num();
            #pragma omp single
            used=omp_get_num_threads();
            funcs[v](1000);
            #pragma omp barrier
            times[tid]=(double)funcs[v](iters)*1e9/(hz*iters*4.0);
        }
        double mn=times[0],mx=times[0],sum=0;
        for(int t=0;t<used;t++) { double x=times[t];if(x<mn)mn=x;if(x>mx)mx=x;sum+=x; }
        printf("MIXED_THROUGHPUT round=%d variant=%s threads=%d ns_per_step_min=%.6f mean=%.6f max=%.6f\\n",round,names[v],used,mn,sum/used,mx);
    }
    free(times);return 0;
}
'''
p=root/'probe.c';p.write_text(s)
print(hashlib.sha256(s.encode()).hexdigest(),p)
