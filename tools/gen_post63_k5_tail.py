#!/usr/bin/env python3
"""Isolate empty-vector-tail bypass and bounded scalar-tail unrolling on v62."""
from pathlib import Path
import hashlib
import subprocess

root=Path('build/post63/k5-tail');out=Path('results/post63/k5-tail')
root.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
source=subprocess.check_output(['git','show','cf42580:conv2d.c'],text=True)
assert hashlib.sha256(source.encode()).hexdigest()=='5a423250471305054185ef31635af7b1ca61dc0133170a048383e6ff8878d7f6'
a=source.index('static __attribute__((noinline)) void k5(');b=source.index('\n}\n',a)+3
body=source[a:b]
old='''        "ldr x24, [%[A], #176]\\n\\t"
        "whilelo p4.s, xzr, x24\\n\\t"'''
new='''        "ldr x24, [%[A], #176]\\n\\t"
        "cbz x24, 77f\\n\\t"
        "whilelo p4.s, xzr, x24\\n\\t"'''
assert body.count(old)==1 and '77:' not in body and '77f' not in body
part=body.replace(old,new)
# Skip the predicated load, three zero-padding stores and zero cursor increments
# only when there are no complete triples. Scalar remainder still executes.
old2='''        "add x20, x20, x24, lsl #2\\n\\t"
        "ldr x24, [%[A], #272]\\n\\t"'''
new2='''        "add x20, x20, x24, lsl #2\\n\\t"
        "77:\\n\\t"
        "ldr x24, [%[A], #272]\\n\\t"'''
assert part.count(old2)==1
part=part.replace(old2,new2)
assert part.replace(new,old).replace(new2,old2)==body
sources={'baseline':source,'guard':source[:a]+part+source[b:]}
old='''        "72:\\n\\t"
        "ld1rw {z0.s}, p0/z, [x13]\\n\\t"
        "st1w {z0.s}, p4, [x20]\\n\\t"
        "add x13, x13, #4\\n\\t"
        "add x20, x20, x3\\n\\t"
        "subs x24, x24, #1\\n\\t"
        "b.ne 72b\\n\\t"'''
new='''        "ld1rw {z0.s}, p0/z, [x13]\\n\\t"
        "st1w {z0.s}, p4, [x20]\\n\\t"
        "cmp x24, #1\\n\\t"
        "b.eq 73f\\n\\t"
        "ld1rw {z0.s}, p0/z, [x13, #4]\\n\\t"
        "add x20, x20, x3\\n\\t"
        "st1w {z0.s}, p4, [x20]\\n\\t"'''
assert body.count(old)==1
part=body.replace(old,new)
assert part.replace(new,old)==body
sources['unroll']=source[:a]+part+source[b:]
# Diagnostic-only histogram: records row counts for each actual tail geometry.
# No new allocations, no workload skipping, and no performance inference from it.
s=source
defs='''static unsigned long tail_hist_calls[16][3], tail_hist_rows[16][3], tail_hist_call;
'''
s=s[:a]+defs+s[a:]
a=s.index('static __attribute__((noinline)) void k5(')
b=s.index('    asm volatile(',a)
s=s[:b]+'''    __atomic_fetch_add(&tail_hist_calls[A.ncp_tail][A.khkw4],1,__ATOMIC_RELAXED);
    __atomic_fetch_add(&tail_hist_rows[A.ncp_tail][A.khkw4],P->nrows,__ATOMIC_RELAXED);
'''+s[b:]
old='    run_parallel(nth, &ctx, g_knobs.pool);\n    if (g_roll_diag)'
new='''    run_parallel(nth, &ctx, g_knobs.pool);
    ++tail_hist_call;
    for(int t=0;t<16;t++) for(int r=0;r<3;r++) {
        unsigned long calls=tail_hist_calls[t][r],rows=tail_hist_rows[t][r];
        if(calls) fprintf(stderr,"K5_TAIL_HIST call=%lu triples=%d scalars=%d calls=%lu rows=%lu\\n",tail_hist_call,t,r,calls,rows);
        tail_hist_calls[t][r]=tail_hist_rows[t][r]=0;
    }
    if (g_roll_diag)'''
assert s.count(old)==1
sources['histogram']=s.replace(old,new)
for name,data in sources.items():(root/(name+'.c')).write_text(data)
(root/'fbench.c').write_bytes(subprocess.check_output(['git','show','8b6b295:tools/fbench.c']))
assert hashlib.sha256((root/'fbench.c').read_bytes()).hexdigest()=='e5e52c8d666584cc49ca6f11162be4868b240e2cc99a3c3ef0a2f8ac292c65ad'
files=[root/(n+'.c') for n in [*sources,'fbench']]
manifest=''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p}\n' for p in files)
(out/'sources.sha256').write_text(manifest)
benchmark=subprocess.check_output(['git','show','d2b65c4:bench_conv.c'])
assert hashlib.sha256(benchmark).hexdigest()=='2548861ae7e29826e454b4c0b098d682f7f04996222e664cd1ea9bc92dd2e927'
(root/'bench_conv.c').write_bytes(benchmark)
official=[root/(n+'.c') for n in ['baseline','unroll','bench_conv']]
(out/'official_sources.sha256').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p}\n' for p in official))

print(manifest,end='')
print('Each fixed candidate changes only one K5 copy-tail region. No changes to FMA, first-row initialization, complete-block interleave or output operations. Histogram is diagnostic-only.')
