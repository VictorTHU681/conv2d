"""Pre-deinterleave K9 input rows, freeing vector issue slots for FMLA."""
from v55_nine import line


def planar_nine(source, use_ext=False):
    macro = r'''
// Exact input span -> two padded planes. Full tail stores initialize padding;
// an odd final float uses one scalar load, avoiding a rounded-up source read.
#define K9_CP(DST) \
        "mov x12, x22\n\t" "mov x23, " #DST "\n\t" \
        "ldr x24, [%[A], #168]\n\t" "cbz x24, 91f\n\t" \
        "90:\n\t" \
        "prfm pldl2keep, [x21]\n\t" "prfm pldl2keep, [x21, #64]\n\t" \
        "ld2w {z0.s, z1.s}, p0/z, [x12]\n\t" \
        "st1w {z0.s}, p0, [x23]\n\t" "add x15, x23, x3\n\t" \
        "st1w {z1.s}, p0, [x15]\n\t" \
        "add x12, x12, #128\n\t" "add x23, x23, #64\n\t" \
        "add x21, x21, #128\n\t" "subs x24, x24, #1\n\t" "b.ne 90b\n\t" \
        "91:\n\t" \
        "prfm pldl2keep, [x21]\n\t" "prfm pldl2keep, [x21, #64]\n\t" \
        "ldr x24, [%[A], #176]\n\t" "whilelo p4.s, xzr, x24\n\t" \
        "ld2w {z0.s, z1.s}, p4/z, [x12]\n\t" \
        "st1w {z0.s}, p0, [x23]\n\t" "add x15, x23, x3\n\t" \
        "st1w {z1.s}, p0, [x15]\n\t" \
        "ldr x15, [%[A], #272]\n\t" "cbz x15, 92f\n\t" \
        "add x12, x12, x24, lsl #3\n\t" "add x23, x23, x24, lsl #2\n\t" \
        "ld1rw {z0.s}, p0/z, [x12]\n\t" "ptrue p4.s, vl1\n\t" \
        "st1w {z0.s}, p4, [x23]\n\t" \
        "92:\n\t" "ldr x24, [%[A], #112]\n\t"
'''
    lo = source.index('static void k8f(')
    hi = source.index('\n}\n', lo) + 3
    f = source[lo:hi]
    emit = lambda instructions: ''.join(map(line, instructions))
    old = '    ka_t A; fill_args(&A, P, 2, 896, 126 + P->steps);'
    assert f.count(old) == 1
    f = f.replace(old, '''    ka_t A; fill_args(&A, P, 2, 0, 0);
    const long sh = ((uintptr_t)P->in_row >> 2) & 15;
    const long ncp = P->KW + 127 + sh;
    const long tsb = (((ncp + 1)/2 + 15) & ~15L)*4 + 64;
    A.in_row = (int64_t)(P->in_row - sh); A.slot = 2*tsb; A.TSB = tsb;
    A.ncp_full = ncp/32; A.ncp_tail = (ncp%32)/2; A.khkw4 = ncp&1;
    A.kb2 = tsb*(sh&1) + 4*(sh>>1);
    A.cf2 = tsb*((sh+1)&1) + 4*((sh+1)>>1);''')
    init = emit(['ldr x3, [%[A], #200]', 'mov x22, x0', 'add x21, x0, x26'])
    f = f.replace(line('1:'), init + '        K9_CP(x17)\n' + line('1:'), 1)
    head = emit(['mov x16, x17', 'sub x17, x28, x17',
                 'add x22, x0, x1', 'cmp x8, #1', 'csel x22, x0, x22, eq',
                 'add x21, x0, x26'])
    head += '        K9_CP(x17)\n'
    head += emit(['ldr x25, [%[A], #256]', 'add x25, x25, x16',
                  'ldr x12, [%[A], #248]', 'add x16, x16, x12'])
    assert f.count('        ROW_HEAD_COMMON\n') == 1
    f = f.replace('        ROW_HEAD_COMMON\n', head)
    for i in (0,2,4,6):
        addr = '[x16]' if i==0 else f'[x16, #{i}, mul vl]'
        old = line(f'ld2w {{z{i}.s, z{i+1}.s}}, p0/z, {addr}')
        even = '[x16]' if i==0 else f'[x16, #{i//2}, mul vl]'
        odd = '[x25]' if i==0 else f'[x25, #{i//2}, mul vl]'
        assert f.count(old) == 1
        f = f.replace(old, emit([f'ld1w {{z{i}.s}}, p0/z, {even}',
                                f'ld1w {{z{i+1}.s}}, p0/z, {odd}']))
    if use_ext:
        assert f.count(line('add x21, x16, #512')) == 1
        f = f.replace(line('add x21, x16, #512'), line('add x21, x16, #256'))
    else:
        for i in (0,2,4,6):
            addr = '[x21]' if i==0 else f'[x21, #{i}, mul vl]'
            old = line(f'ld2w {{z{i}.s, z{i+1}.s}}, p0/z, {addr}')
            addr = '[x21]' if i==0 else f'[x21, #{i//2}, mul vl]'
            assert f.count(old) == 1
            f = f.replace(old, line(f'ld1w {{z{i}.s}}, p0/z, {addr}'))
        # Only the second FMLA step changes register mapping; the first uses
        # even/odd input vectors in the original order.
        a = f.index(line('add x21, x16, #4'))
        b = f.index(line('83:'), a)
        part = f[a:b]
        for i in range(8):
            old = line(f'fmla z{16+i}.s, p0/m, z{i}.s, z24.s')
            new = line(f'fmla z{16+i}.s, p0/m, z{i+1 if i%2==0 else i-1}.s, z24.s')
            assert part.count(old) == 1
            part = part.replace(old, new)
        f = f[:a] + part + f[b:]
    f = f.replace(line('add x16, x16, #8'), emit(['add x16, x16, #4', 'add x25, x25, #4']))
    f = f.replace('"p0", "p3", "memory"', '"p0", "p3", "p4", "memory"')
    return source[:lo] + macro + f + source[hi:]
