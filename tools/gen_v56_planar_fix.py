#!/usr/bin/env python3
"""Bound planar input copies and give each packing chunk exactly one writer."""
from pathlib import Path
import hashlib
import subprocess
import sys

include_k8 = '--k8' in sys.argv
root = Path('build/v56/experiments/planar-fix' + ('-full' if include_k8 else ''))
root.mkdir(parents=True, exist_ok=True)
def revision(rev):
    return subprocess.check_output(['git', 'show', rev+':conv2d.c'], text=True)
def once(s, old, new):
    assert s.count(old) == 1, (s.count(old), old[:100])
    return s.replace(old, new)
baseline = revision('93163b4')
upstream = revision('b9591de')
for name, s in [('baseline',baseline), ('common',revision('8ce8af2')), ('upstream',upstream)]:
    (root/(name+'.c')).write_text(s)
r = subprocess.run(['git','merge-file','-p',str(root/'baseline.c'),str(root/'common.c'),str(root/'upstream.c')],capture_output=True,text=True)
assert r.returncode == 1 and r.stdout.count('<<<<<<<') == 1
s = r.stdout
a=s.index('<<<<<<<');b=s.index('=======',a);c=s.index('>>>>>>>',b);d=s.index('\n',c)+1
merged = s[:a]+s[b+len('=======\n'):c]+s[d:]
merged=once(merged,'if (ncp) roll_copy_row(P->ring, src, ncp);','if (ncp) roll_copy_row(P->ring + sh, P->in_row, ncp - sh);')

helper='''// Initialize only from live input; unused aligned prefix and tail are zero.
static __attribute__((noinline)) void roll_first_planes(float* dst, const float* src,
                                                       long live, long sh, long planes, long stride)
{
    for (long p = 0; p < planes; p++) {
        float* d = dst + p * stride;
        for (long i = 0; i < stride; i++) {
            long x = i * planes + p - sh;
            d[i] = (unsigned long)x < (unsigned long)live ? src[x] : 0.f;
        }
    }
}
'''
def asm(ops, macro=False):
    return ''.join('        "'+op+'\\n\\t"'+(' \\' if macro else '')+'\n' for op in ops)
def tail_remainder(src,dst,macro):
    return asm([
        f'add {src}, {src}, x24, lsl #4', f'add {dst}, {dst}, x24, lsl #2',
        'ldr x24, [%[A], #272]', 'cbz x24, 72f', 'ptrue p4.s, vl1', '71:',
        f'ld1rw {{z0.s}}, p0/z, [{src}]', f'st1w {{z0.s}}, p4, [{dst}]',
        f'add {src}, {src}, #4', f'add {dst}, {dst}, x3',
        'subs x24, x24, #1','b.ne 71b','72:'
    ],macro)
def fix(s):
    if include_k8:
        s=once(s,'    ka_t A; fill_args(&A, P, 2, 896, 126 + P->steps);', '''    ka_t A; fill_args(&A, P, 2, 896, 127 + P->KW);
    // Even KW computes one padded input element: initialize it inside both
    // ring slots instead of reading beyond the live input row span.
    const long live = 127 + P->KW + A.sh4 / 4;
    A.slot = ((live + 1) * 4 + 63) & ~63L;
    P->ring[live] = 0.f;
    P->ring[A.slot / 4 + live] = 0.f;''')
    # A receives an address for later rows, without out-of-object C subtraction.
    assert s.count('(int64_t)(P->in_row - sh)')==2
    s=s.replace('(int64_t)(P->in_row - sh)','(int64_t)((uintptr_t)P->in_row - (uintptr_t)sh * sizeof(float))')
    a=s.index('// Exact input span -> two padded planes.')
    s=s[:a]+helper+s[a:]
    for sig,planes,stride,live,cp in [
        ('static __attribute__((noinline)) void k8f(',2,'tsb / 4','P->KW + 127','K9_CP'),
        ('static void k4(',4,'TSB / 4','P->KW + 255','K4_CP')]:
        a=s.index(sig); b=s.index('\n}\n',a)+3; f=s[a:b]
        k=f.index('    asm volatile(')
        f=f[:k]+f'    roll_first_planes(P->ring, P->in_row, {live}, sh, {planes}, {stride});\n'+f[k:]
        old=asm(['mov x22, x0','add x21, x0, x26'])+f'        {cp}(x17)\n'
        f=once(f,old,'')
        if planes==4:
            f=once(f,'const long ncp = steps4 + 252 + sh;', 'const long ncp = P->KW + 255 + sh;')
            f=once(f,'(((ncp + 3) / 4 + 15) & ~15L) * 4;', '(((ncp + 3) / 4 + 15) & ~15L) * 4 + 64;')
            f=once(f,'A.ncp_tail = ((ncp % 64) + 3) / 4;', 'A.ncp_tail = (ncp % 64) / 4; A.khkw4 = ncp % 4;')
            if 'A.ovn' in f:  # Upstream overlap copies its tail before the loop.
                start=f.index('        "ld4w {z0.s, z1.s, z2.s, z3.s}, p4/z, [x13]')
                end=f.index('        "ldr x20, [%[A], #304]',start)
                part=f[start:end].replace('}, p4,','}, p0,')
                f=f[:start]+part+tail_remainder('x13','x20',False)+f[end:]
        s=s[:a]+f+s[b:]
    # Full vectors plus a floor-divided ld4w tail and 0..3 scalar inputs.
    a=s.index('#define K4_CP(');b=s.index('#define K4_STEP(',a)
    f=s[a:b].replace('}, p4,','}, p0,')
    marker='        "ldr x24, [%[A], #112]\\n\\t"\n'
    f=once(f,marker,tail_remainder('x12','x13',True)+marker)
    s=s[:a]+f+s[b:]
    # A done flag publishes writes; it is not permission to duplicate a writer.
    a=s.index('    for (;;) {   // 兜底：');b=s.index('\n}\n',a)
    s=s[:a]+'''    for (int i = 0; i < nc; i++)
        while (!__atomic_load_n(&g_pk_done[i], __ATOMIC_ACQUIRE))
            asm volatile("yield" ::: "memory");
'''+s[b:]
    s=s.replace('// R/kf 打包的并行化：chunk = (组 g, 行 y)，id = g*KH + y。内容由 (kernel, 形状) 唯一决定 → 幂等，可重复执行。\n// 全体线程原子认领；认领耗尽后空闲线程直接重做未完成的 chunk（不自旋等慢线程，分时/换出不放大）。',
                '// R/kf packing: unique atomic claims; wait for each owner to publish completion.\n// Equal values do not make concurrent non-atomic writes safe.')
    return s

for name,s in [('baseline',baseline),('upstream',upstream),('fixed',fix(baseline)),('mergedfixed',fix(merged))]:
    p=root/(name+'.c');p.write_text(s)
    print(hashlib.sha256(s.encode()).hexdigest(),p)
