#!/usr/bin/env python3
"""Try a 36+5 family: four FMLA-folded rows and a three-way K5 tail."""
from pathlib import Path
import hashlib
import subprocess
import re

source=subprocess.check_output(['git','show','68f0276:conv2d.c'],text=True)
assert hashlib.sha256(source.encode()).hexdigest()=='4393346986d6c0c71c7db9ecd804ed76c22839923f8ed963f07488854809d121'
def once(s,old,new):
    assert s.count(old)==1,(s.count(old),old[:80])
    return s.replace(old,new)
def asm(ops): return ''.join('        "'+op+'\\n\\t"\n' for op in ops)

copy=['mov x12, x22','mov x13, x17','ldr x24, [%[A], #168]',
      'cbz x24, 71f','70:']
for off in [0,64,128]: copy.append(f'prfm pldl2keep, [x21, #{off}]')
copy+=['ld3w {z0.s, z1.s, z2.s}, p0/z, [x12]',
       'st1w {z0.s}, p0, [x13]','add x23, x13, x3',
       'st1w {z1.s}, p0, [x23]','add x23, x23, x3','st1w {z2.s}, p0, [x23]',
       'add x12, x12, #192','add x13, x13, #64','add x21, x21, #192',
       'subs x24, x24, #1','b.ne 70b','71:','ldr x24, [%[A], #176]',
       'whilelo p4.s, xzr, x24','ld3w {z0.s, z1.s, z2.s}, p4/z, [x12]',
       'st1w {z0.s}, p0, [x13]','add x23, x13, x3',
       'st1w {z1.s}, p0, [x23]','add x23, x23, x3','st1w {z2.s}, p0, [x23]',
       'add x12, x12, x24, lsl #3','add x12, x12, x24, lsl #2',
       'add x13, x13, x24, lsl #2','ldr x24, [%[A], #272]',
       'cbz x24, 73f','ptrue p4.s, vl1','72:',
       'ld1rw {z0.s}, p0/z, [x12]','st1w {z0.s}, p4, [x13]',
       'add x12, x12, #4','add x13, x13, x3','subs x24, x24, #1','b.ne 72b',
       '73:','ldr x24, [%[A], #112]']

step=source[source.index('#define K4_STEP('):source.index('#define K4_EV(')].replace('K4_STEP','K5_STEP')
events=''
for tile in range(4):
    ops=[f'mova z{j}.s, p0/m, za{tile}v.s[w12, {j}]' for j in range(3)]
    ops += [f'st3w {{z0.s, z1.s, z2.s}}, p0, [x20, #{3*tile}, mul vl]']
    ops += [f'mova za{tile}v.s[w12, {j}], p0/m, z31.s' for j in range(3)]
    events+=asm(ops)
kernel='''// Five output-row residues, each with three interleaved column classes.
// ZA column 15 is inactive; exact live input is KW+191 floats.
'''+step+'''static __attribute__((noinline)) void k5(const kp_t* P)
{
    const long sh = ((uintptr_t)P->in_row >> 2) & 15;
    const long live = P->KW + 191, ncp = live + sh;
    const long TSB = (((ncp + 2) / 3 + 15) & ~15L) * 4 + 64;
    ka_t A; fill_args(&A, P, 1, 0, 0);
    A.in_row = (int64_t)((uintptr_t)P->in_row - (uintptr_t)sh * sizeof(float));
    A.slot = 3 * TSB; A.TSB = TSB;
    A.it = (P->KW + 2) / 3; A.kw4 = (P->KW + 2) % 3;
    A.ncp_full = ncp / 48; A.ncp_tail = (ncp % 48) / 3; A.khkw4 = ncp % 3;
    A.n2 = TSB * ((sh + 0) % 3) + 4 * ((sh + 0) / 3);
    A.e2 = TSB * ((sh + 1) % 3) + 4 * ((sh + 1) / 3);
    A.T  = TSB * ((sh + 2) % 3) + 4 * ((sh + 2) / 3);
    roll_first_planes(P->ring, P->in_row, live, sh, 3, TSB / 4);
    asm volatile(
        LOAD_ARGS
'''+asm(['ldr x3, [%[A], #200]','ldr x7, [%[A], #136]',
         'fmov z31.s, #0.0','1:','mov x16, x17','sub x17, x28, x17',
         'add x22, x0, x1','cmp x8, #1','csel x22, x0, x22, eq',
         'add x21, x0, x26'])+asm(copy)+asm([
         'ldr x22, [%[A], #192]','add x22, x22, x16',
         'ldr x23, [%[A], #208]','add x23, x23, x16',
         'ldr x12, [%[A], #184]','add x16, x16, x12',
         'mov x15, x7','.p2align 4','2:'])+'''
        K5_STEP(x16, 0)
        K5_STEP(x22, 1)
        K5_STEP(x23, 2)
'''+asm(['add x16, x16, #4','add x22, x22, #4','add x23, x23, #4',
         'add x2, x2, #192','subs x15, x15, #1','b.ne 2b',
         'ldr x12, [%[A], #264]','cbz x12, 42f'])+'''
        K5_STEP(x16, 0)
'''+asm(['cmp x12, #1','b.eq 41f'])+'''
        K5_STEP(x22, 1)
'''+asm(['41:','add x2, x2, #192','42:'])+'''
        WRAP_B(x2) SEL_OUT
'''+asm(['cmp x27, x24','b.hs 4f','add w12, w27, w27, lsl #1'])+events+asm(['4:'])+'''
        ADV_CNT(x27)
        ROW_TAIL
        : : [A]"r"(&A)
        : XCLOB, "z0", "z1", "z2", "z3", "z4", "z31", "p0", "p3", "p4", "memory", "cc");
}
#undef K5_STEP

'''
s=once(source,'// b 表：kind 16:',kernel+'// b 表：kind 16:')
s=once(s,'kind == 8 ? c >> 1 : c >> 2;', 'kind == 8 ? c >> 1 : kind == 5 ? c / 3 : c >> 2;')
s=once(s,'kind == 8 ? c & 1 : c & 3;', 'kind == 8 ? c & 1 : kind == 5 ? c % 3 : c & 3;')
s=once(s,'live[c] = s_base + sidx < KH;', 'live[c] = s_base + sidx < KH && (kind != 5 || c < 15);')
a=s.index('static int roll_groups_width(');b=s.index('\n}\n',a)+3
s=s[:a]+'''static int roll_groups_width(long KH, long KW, rgrp_t* G, long outW)
{
    int ng;
    if (outW >= 128) ng = roll_groups(KH, KW, G);
    else {
        ng = roll_groups_base(KH, KW, G);
        for (int g = 0; g < ng; g++) G[g].sf = KH - 1;
    }
    if (outW >= 192) {
        int pair = -1, tail = -1;
        for (int g = 0; g < ng; g++) {
            if (G[g].kind == 33) pair = g;
            if (G[g].kind == 8 && G[g].nvA == 8) tail = g;
        }
        if (pair >= 0 && tail >= 0) {
            G[pair].kind = 35;
            G[tail].kind = 5; G[tail].nvA = 5; G[tail].width = 192;
            G[tail].steps = ((KW + 4) / 3) * 3;
            G[tail].RSB = G[tail].steps * 64;
        }
    }
    return ng;
}
'''+s[b:]
s=once(s,'G->kind == 4 ? g_knobs.roll_w4', '(G->kind == 4 || G->kind == 5) ? g_knobs.roll_w4')
s=once(s,'else if (g->kind == 8) k8(&K); else k4(&K);',
       'else if (g->kind == 8) k8(&K); else if (g->kind == 5) k5(&K); else k4(&K);')
s=s.replace('8x2 %.2f 4x4 %.2f','8x2 %.2f 4x4/5x3 %.2f')
root=Path('build/v56/experiments/k5-triplet');root.mkdir(parents=True,exist_ok=True)
def change_k5(text,prefetch=False,overlap=False):
    a=text.index('static __attribute__((noinline)) void k5(');b=text.index('\n}\n',a)+3
    f=text[a:b]
    if prefetch:
        pf=asm(['ldr x12, [%[A], #144]','add x13, x27, x12','cmp x13, x6',
                'sub x12, x13, x6','csel x13, x12, x13, hs','cmp x13, x24','b.hs 60f',
                'ldr x12, [%[A], #232]','add x12, x9, x12']+
               [f'prfm pstl2keep, [x12, #{64*j}]' for j in range(12)]+['60:'])
        f=once(f,asm(['1:']),asm(['1:'])+pf)
    if overlap:
        f=once(f,'    A.n2 = TSB * ((sh + 0) % 3)',
               '    A.ovn = A.it - 1 < A.ncp_full ? A.it - 1 : A.ncp_full;\n'
               '    A.ovr = A.ncp_full - A.ovn;\n    A.n2 = TSB * ((sh + 0) % 3)')
        # Copy the floor-predicated tail and 0..2 scalars before the compute loop.
        tail=copy[copy.index('71:')+1:]
        mapping={'x12':'x13','x13':'x20'}
        tail=[re.sub(r'\bx\d+\b',lambda m:mapping.get(m[0],m[0]),op) for op in tail]
        tail_setup=['ldr x12, [%[A], #168]','mov x13, #192','madd x13, x12, x13, x22',
                    'add x20, x17, x12, lsl #6']
        supplement=['ldr x20, [%[A], #304]','cbz x20, 64f',
                    'ldr x12, [%[A], #296]','mov x13, #192','madd x13, x12, x13, x22',
                    'add x24, x17, x12, lsl #6','63:',
                    'ld3w {z0.s, z1.s, z2.s}, p0/z, [x13]',
                    'st1w {z0.s}, p0, [x24]','add x23, x24, x3',
                    'st1w {z1.s}, p0, [x23]','add x23, x23, x3','st1w {z2.s}, p0, [x23]',
                    'add x13, x13, #192','add x24, x24, #64',
                    'subs x20, x20, #1','b.ne 63b','64:',
                    'mov x13, x22','mov x12, x17']
        f=once(f,asm(copy),asm(tail_setup+tail+supplement))
        f=once(f,asm(['ldr x12, [%[A], #184]','add x16, x16, x12']),
               asm(['ldr x20, [%[A], #184]','add x16, x16, x20']))
        body='''        K5_STEP(x16, 0)
        K5_STEP(x22, 1)
        K5_STEP(x23, 2)
'''+asm(['add x16, x16, #4','add x22, x22, #4','add x23, x23, #4','add x2, x2, #192'])
        ovl=asm(['ldr x20, [%[A], #296]','mov x15, x7','cbz x20, 62f',
                 'sub x15, x15, x20','.p2align 4','61:'])+body+asm(
            [f'prfm pldl2keep, [x21, #{j*64}]' for j in range(3)]+
            ['ld3w {z25.s, z26.s, z27.s}, p0/z, [x13]',
             'st1w {z25.s}, p0, [x12]','add x24, x12, x3',
             'st1w {z26.s}, p0, [x24]','add x24, x24, x3','st1w {z27.s}, p0, [x24]',
             'add x13, x13, #192','add x12, x12, #64','add x21, x21, #192',
             'subs x20, x20, #1','b.ne 61b','62:','ldr x24, [%[A], #112]',
             '.p2align 4','2:'])
        f=once(f,asm(['mov x15, x7','.p2align 4','2:']),ovl)
        f=once(f,': XCLOB, "z0",', ': XCLOB, "z25", "z26", "z27", "z0",')
    return text[:a]+f+text[b:]

variants={'baseline':source,'triplet':s,'prefetch':change_k5(s,True),
          'overlap':change_k5(s,False,True),'both':change_k5(s,True,True)}
for name,code in variants.items():
    p=root/(name+'.c');p.write_text(code)
    print(hashlib.sha256(code.encode()).hexdigest(),p)
