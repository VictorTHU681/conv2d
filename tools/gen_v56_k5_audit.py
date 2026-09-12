#!/usr/bin/env python3
"""Instrument live source-copy intervals; not every SME memory instruction."""
from pathlib import Path
import hashlib,argparse

parser=argparse.ArgumentParser()
parser.add_argument('--root',type=Path,default=Path('build/v56/experiments/k5-triplet'))
parser.add_argument('--variant',default='triplet')
args=parser.parse_args()
root=args.root
s=(root/(args.variant+'.c')).read_text()
defs='''static uintptr_t audit_lo,audit_hi;
static unsigned long audit_calls,audit_outside;
static void audit_span(uintptr_t p,size_t bytes) {
    __atomic_fetch_add(&audit_calls,1,__ATOMIC_RELAXED);
    if(p<audit_lo || bytes>audit_hi-audit_lo || p>audit_hi-bytes)
        __atomic_fetch_add(&audit_outside,1,__ATOMIC_RELAXED);
}
void conv_audit_report(unsigned long* calls,unsigned long* outside) {
    *calls=audit_calls;*outside=audit_outside;
}
'''
a=s.index('static void roll_copy_row(');s=s[:a]+defs+s[a:]
a=s.index('static void roll_copy_row(');b=s.index('{',a)+1
s=s[:b]+'\n    audit_span((uintptr_t)src,(size_t)n*4);\n'+s[b:]
a=s.index('static void fill_args(');b=s.index('\n}\n',a)
s=s[:b]+'''\n    if(ncp) for(long row=0;row<P->nrows;row++) {
        long next=row+1<P->nrows?row+1:row;
        audit_span((uintptr_t)A->in_row+next*P->rsb,(size_t)(A->ncp_full*16+A->ncp_tail)*4);
    }
'''+s[b:]
a=s.index('static __attribute__((noinline)) void roll_first_planes(');b=s.index('{',a)+1
s=s[:b]+'\n    audit_span((uintptr_t)src,(size_t)live*4);\n'+s[b:]
for sig,count in [('static __attribute__((noinline)) void k8f(',32),('static void k4(',64),
                  ('static __attribute__((noinline)) void k5(',48)]:
    planes=count//16
    a=s.index(sig);b=s.index('    asm volatile(',a)
    extra=f'''    for(long row=0;row<P->nrows;row++) {{
        long next=row+1<P->nrows?row+1:row;
        audit_span((uintptr_t)A.in_row+next*P->rsb,(size_t)(A.ncp_full*{count}+A.ncp_tail*{planes}+A.khkw4)*4);
    }}
'''
    s=s[:b]+extra+s[b:]
a=s.index('void conv2d(const CONVFLOAT* input,');b=s.index('{',a)+1
s=s[:b]+'\n    audit_lo=(uintptr_t)input; audit_hi=audit_lo+(size_t)inputHeight*inputWidth*4;\n'+s[b:]
p=root/(args.variant+'_audit.c');p.write_text(s)
print(hashlib.sha256(s.encode()).hexdigest(),p)
