"""Nine-residual kernel: eight via ZA, one via eight vector FMA chains."""


def line(ins):
    return '        "' + ins + '\\n\\t"\n'


def nine(source, use_ext=False):
    emit = lambda instructions: ''.join(map(line, instructions))
    a = source.index('static void k8(')
    b = source.index('\n}\n', a) + 3
    f = source[a:b].replace('static void k8(', 'static void k8f(')
    f = f.replace('    asm volatile(', '''    A.n2 = (int64_t)P->kb0; A.e2 = (int64_t)P->kbase;
    A.T = (int64_t)P->kend; A.nlines = P->cf0; A.kw4 = P->KW;
    asm volatile(''', 1)
    init = ['ldr x13, [%[A], #184]']
    init += [f'fmov z{i}.s, #0.0' for i in range(16, 24)]
    init += ['ldr x12, [%[A], #288]', 'cbz x12, 81f', 'ldr x12, [%[A], #280]']
    init += [f'ld1w {{z{i}.s}}, p0/z, [x12, #{i-16}, mul vl]' for i in range(16, 24)]
    init += ['81:']
    f = f.replace(line('1:'), emit(init) + line('1:'), 1)
    f = f.replace(line('mov x15, x7'), line('ldr x12, [%[A], #264]') + line('mov x15, x7'), 1)
    first = ['cbz x12, 82f', 'ld1rw {z24.s}, p0/z, [x13]',
             'add x13, x13, #4', 'sub x12, x12, #1']
    first += [f'fmla z{16+i}.s, p0/m, z{i}.s, z24.s' for i in range(8)]
    first += ['82:']
    marker = line('fmopa za0.s, p0/m, p0/m, z1.s, z9.s')
    assert f.count(marker) == 1
    f = f.replace(marker, emit(first) + marker)
    second = ['cbz x12, 83f', 'ld1rw {z24.s}, p0/z, [x13]',
              'add x13, x13, #4', 'sub x12, x12, #1']
    if use_ext:
        second += ['add x21, x16, #512', 'ld1w {z25.s}, p0/z, [x21]']
        # Ascending order preserves the higher source until it has been used.
        second += [f'ext z{i}.b, z{i}.b, z{i+2 if i<6 else 25}.b, #4' for i in (0,2,4,6)]
        second += [f'fmla z{16+i}.s, p0/m, z{i+1 if i%2==0 else i-1}.s, z24.s' for i in range(8)]
    else:
        second += ['add x21, x16, #4', 'ld2w {z0.s, z1.s}, p0/z, [x21]']
        second += [f'ld2w {{z{i}.s, z{i+1}.s}}, p0/z, [x21, #{i}, mul vl]' for i in (2,4,6)]
        second += [f'fmla z{16+i}.s, p0/m, z{i}.s, z24.s' for i in range(8)]
    second += ['83:']
    marker = line('add x16, x16, #8')
    assert f.count(marker) == 1
    f = f.replace(marker, emit(second) + marker)
    marker = '        WRAP_B(x2) SEL_OUT\n'
    wrap = ['ldr x21, [%[A], #208]', 'cmp x13, x21',
            'ldr x21, [%[A], #192]', 'csel x13, x21, x13, eq']
    event = ['ldr x12, [%[A], #216]', 'cmp x27, x12', 'b.eq 80f']
    f = f.replace(marker, emit(wrap) + marker + emit(event))
    event = ['b 4f', '80:', 'st2w {z16.s, z17.s}, p0, [x20]']
    event += [f'st2w {{z{i}.s, z{i+1}.s}}, p0, [x20, #{i-16}, mul vl]' for i in (18,20,22)]
    event += [f'fmov z{i}.s, #0.0' for i in range(16,24)]
    f = f.replace(line('4:'), emit(event) + line('4:'), 1)
    save = ['ldr x12, [%[A], #280]', 'cbz x12, 84f']
    save += [f'st1w {{z{i}.s}}, p0, [x12, #{i-16}, mul vl]' for i in range(16,24)]
    save += ['84:']
    f = f.replace('        ROW_TAIL\n', '        ROW_TAIL\n' + emit(save), 1)
    clobbers = ', '.join(f'"z{i}"' for i in range(16,24))
    if use_ext:
        clobbers += ', "z25"'
    f = f.replace(': XCLOB,', ': XCLOB, ' + clobbers + ',')
    source = source[:b] + '\n' + f + source[b:]

    old = 'int Rowner; } rgrp_t;'
    assert source.count(old) == 1
    source = source.replace(old, 'int Rowner; long sf; } rgrp_t;')
    source = source.replace('static int roll_groups(long KH, long KW, rgrp_t* G)',
                            'static int roll_groups_base(long KH, long KW, rgrp_t* G)')
    pos = source.index('// 滚动形态的结构性开关')
    wrapper = r'''
// Structural controls: rem=9 moves the existing fold from pair to K8;
// rem=17 with >=2 pairs folds four rows into each of two pairs, leaving nine.
static int roll_groups(long KH, long KW, rgrp_t* G)
{
    int ng=roll_groups_base(KH,KW,G), np=KH/32, rem=KH%32;
    for (int g=0;g<ng;g++) G[g].sf=KH-1;
    if (!((np>=1 && rem==9) || (np>=2 && rem==17))) return ng;
    ng=0;
    long sf=KH-1, s=0;
    for (int p=0;p<np;p++) {
        int folded=rem==17 && p<2;
        G[ng]=(rgrp_t){folded?35:32,s,16,16,32,KW,KW*64,NULL,0};
        G[ng++].sf=sf;
        if (folded) sf-=4;
        s+=32;
    }
    long steps=(KW&1)?KW+1:KW+2;
    G[ng]=(rgrp_t){9,s,8,0,128,steps,steps*64,NULL,0};
    G[ng++].sf=sf;
    return ng;
}
'''
    source = source[:pos] + wrapper + source[pos:]
    old = '? 16 : G->kind, y);'
    assert source.count(old) == 1
    source = source.replace(old, '? 16 : G->kind == 9 ? 8 : G->kind, y);')
    source = source.replace('G->kind == 8 ?', '(G->kind == 8 || G->kind == 9) ?')
    source = source.replace('kind == 8 ? 2 : 3;', '(kind == 8 || kind == 9) ? 2 : 3;')
    assert source.count('const long sF = KH - 1,') == 2
    source = source.replace('const long sF = KH - 1,', 'const long sF = g->sf,')
    source = source.replace('} else if (g->kind == 33) {', '} else if (g->kind == 33 || g->kind == 9) {')
    source = source.replace('else if (g->kind == 8) k8(&K);', 'else if (g->kind == 9) k8f(&K); else if (g->kind == 8) k8(&K);')
    return source
