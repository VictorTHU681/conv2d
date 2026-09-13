#!/usr/bin/env python3
"""Check first and subsequent rolling planar-copy intervals (not timings)."""
from pathlib import Path
import hashlib
import sys
full='--full' in sys.argv
root=Path('build/v56/experiments/planar-fix' + ('-full' if full else ''))
defs='''static uintptr_t audit_input_lo, audit_input_hi;
static unsigned long audit_calls, audit_overreads, audit_kind_bad[3];
void conv_audit_reset(void) { audit_calls = audit_overreads = 0; }
unsigned long conv_audit_calls(void) { return audit_calls; }
unsigned long conv_audit_overreads(void) { return audit_overreads; }
unsigned long conv_audit_kind(int k) { return audit_kind_bad[k]; }
static void audit_span(uintptr_t src, size_t bytes, int kind) {
    __atomic_fetch_add(&audit_calls, 1, __ATOMIC_RELAXED);
    if (src < audit_input_lo || src + bytes > audit_input_hi) {
        __atomic_fetch_add(&audit_overreads, 1, __ATOMIC_RELAXED);
        __atomic_fetch_add(&audit_kind_bad[kind], 1, __ATOMIC_RELAXED);
    }
}
'''
for name in ['baseline','fixed','mergedfixed']:
    s=(root/(name+'.c')).read_text();fixed=name!='baseline'
    a=s.index('static void roll_copy_row(');s=s[:a]+defs+s[a:]
    a=s.index('static void roll_copy_row(');b=s.index('{',a)+1
    s=s[:b]+'\n    audit_span((uintptr_t)src, (size_t)n * 4, 0);\n'+s[b:]
    if full:
        a=s.index('static void fill_args(');b=s.index('\n}\n',a)
        s=s[:b]+'''\n    if (ncp) for (long row = 0; row < P->nrows; row++) {
        long next = row + 1 < P->nrows ? row + 1 : row;
        audit_span((uintptr_t)A->in_row + next * P->rsb,
                   (size_t)(A->ncp_full * 16 + A->ncp_tail) * 4, 0);
    }
'''+s[b:]
    if fixed:
        a=s.index('static __attribute__((noinline)) void roll_first_planes(');b=s.index('{',a)+1
        s=s[:b]+'\n    audit_span((uintptr_t)src, (size_t)live * 4, planes == 2 ? 1 : 2);\n'+s[b:]
    for sig,kind,count in [
        ('static __attribute__((noinline)) void k8f(',1,'A.ncp_full * 32 + A.ncp_tail * 2 + A.khkw4'),
        ('static void k4(',2,'A.ncp_full * 64 + A.ncp_tail * 4'+(' + A.khkw4' if fixed else ''))]:
        a=s.index(sig);b=s.index('    asm volatile(',a)
        extra='' if fixed else f'    audit_span((uintptr_t)A.in_row, (size_t)({count}) * 4, {kind});\n'
        extra+='    for (long row = 0; row < P->nrows; row++) {\n'
        extra+='        long next = row + 1 < P->nrows ? row + 1 : row;\n'
        extra+=f'        audit_span((uintptr_t)A.in_row + next * P->rsb, (size_t)({count}) * 4, {kind});\n    }}\n'
        s=s[:b]+extra+s[b:]
    a=s.index('void conv2d(const CONVFLOAT* input,');b=s.index('{',a)+1
    s=s[:b]+'\n    audit_input_lo=(uintptr_t)input;\n    audit_input_hi=audit_input_lo+(size_t)inputHeight*inputWidth*4;\n'+s[b:]
    p=root/(name+'_audit.c');p.write_text(s)
    print(hashlib.sha256(s.encode()).hexdigest(),p)
