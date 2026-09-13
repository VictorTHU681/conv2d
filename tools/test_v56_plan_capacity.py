#!/usr/bin/env python3
"""Run actual extracted roll_prepare across shape/thread changes under ASan/UBSan.

The unchanged source must fail at its pstart write; the fixed source must pass.
No SME instructions execute here, so this is a host plan-allocation regression.
"""
from pathlib import Path
import os, subprocess

root = Path('build/v56/experiments/plan-capacity')
results = Path('results/v56/experiments/plan-capacity')
results.mkdir(parents=True, exist_ok=True)
prefix = '''#include <assert.h>
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef struct { uint64_t v; char pad[56]; } padded_u64;
static struct { int roll_w8, roll_w4, roll_w16; } g_knobs = {104,123,102};
static int env_int(const char* name,int fallback) { (void)name; return fallback; }
static void* alloc_aligned(size_t n) { void* p=0; assert(!posix_memalign(&p,64,n)); return p; }
'''
harness = r'''
static unsigned plans;
static void check(long kh,long kw,long oh,long ow,int nth) {
    assert(roll_shape_ok(oh+kh-1,ow+kw-1,kh,kw));
    roll_prepare(NULL,oh+kh-1,ow+kw-1,kh,kw,nth);
    rplan_t* p=&g_rp;
    assert(p->pnth==nth && p->npieces<=p->pcap);
    assert(p->pstart[0]==0 && p->pstart[nth]==p->npieces);
    for(int t=0;t<nth;t++) assert(p->pstart[t]<=p->pstart[t+1]);
    int item=0; long next=0;
    for(int i=0;i<p->npieces;i++) {
        const rpiece_t* pc=&p->pieces[i];
        assert(pc->item==item && pc->ja==next && pc->jb>pc->ja && pc->jb<=oh);
        assert(pc->ya<kh && pc->yb<kh && pc->af<kh && pc->cf<kh);
        next=pc->jb;
        if(next==oh) { item++; next=0; }
    }
    assert(item==p->nit && next==0);
    plans++;
}
int main(void) {
    // More pieces with one thread, then fewer pieces with 38 threads. The
    // old guard skips reallocation despite pstart having only two entries.
    check(41,13,534,8192,1);
    fprintf(stderr,"FIRST_PLAN pcap=%d nit=%d nth=1\n",g_rp.pcap,g_rp.nit);
    check(41,13,534,512,38);
    const long khs[]={16,39,41,55,57,81,249,256};
    const long widths[]={512,8192,513,256,4096};
    const int threads[]={1,38,2,64,7,3};
    for(int repeat=0;repeat<2;repeat++)
    for(unsigned k=0;k<sizeof(khs)/sizeof(*khs);k++)
    for(unsigned w=0;w<sizeof(widths)/sizeof(*widths);w++)
    for(unsigned t=0;t<sizeof(threads)/sizeof(*threads);t++)
        check(khs[k],3+(k*17)%398,535+repeat*4096,widths[w],threads[t]);
    printf("PLAN_CAPACITY_HOST PASS plans=%u\n",plans);
    return 0;
}
'''
for variant in ['baseline', 'capacity']:
    s = (root / f'{variant}.c').read_text()
    types = s[s.index('typedef struct { int kind;'):s.index('static rplan_t g_rp;')]
    start = s.index('static int roll_groups_base(')
    groups_prepare = s[start:s.index('\nstatic inline void carry_store_za(')]
    src = root / f'host_{variant}.c'
    src.write_text(prefix + types + '\nstatic rplan_t g_rp;\n' + groups_prepare + harness)
    binary = root / f'host_{variant}'
    subprocess.run(['gcc','-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer',
                    '-fno-pie','-no-pie',str(src),'-o',str(binary)], check=True)
    env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1', UBSAN_OPTIONS='halt_on_error=1')
    run = subprocess.run([str(binary)], env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (results / f'host_{variant}.txt').write_text(run.stdout)
    if variant == 'baseline':
        assert run.returncode != 0 and 'AddressSanitizer: heap-buffer-overflow' in run.stdout
        assert 'WRITE of size 4' in run.stdout and 'roll_prepare' in run.stdout
        print('BASELINE positive control: heap-buffer-overflow WRITE of size 4 in roll_prepare')
    else:
        assert run.returncode == 0, run.stdout
        assert 'PLAN_CAPACITY_HOST PASS plans=482' in run.stdout
        print(run.stdout, end='')
