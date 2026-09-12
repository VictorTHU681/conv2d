#!/usr/bin/env python3
"""Generate reversible v51 experiments from an immutable Git baseline."""
import argparse
import hashlib
from pathlib import Path
import re
import subprocess


def unroll(source, factor, offsets=False):
    for name in ('k16pair', 'k16pairf', 'k16pairf3', 'k16pairf4', 'k16single'):
        start = source.index('static void ' + name + '(')
        end = source.index('\n}\n', start) + 3
        function = source[start:end]
        label = '        "2:\\n\\t"\n'
        begin = function.index(label)
        finish = function.index('        "subs x15, x15, #1\\n\\t"\n', begin)
        body = function[begin + len(label):finish]
        old = (function[begin:finish] +
               '        "subs x15, x15, #1\\n\\t"\n        "b.ne 2b\\n\\t"\n')
        assert function.count(old) == 1, name
        repeated = body * factor
        if offsets:
            pattern = re.compile(r'^        "add (x16|x2|x3|x13), \1, #(\d+)\\n\\t"\n', re.M)
            advances = pattern.findall(body)
            assert ('x16', '4') in advances and ('x2', '64') in advances, name
            stripped = pattern.sub('', body)
            repeated = ''
            for step in range(factor):
                part = stripped
                if step:
                    part = part.replace('[x16', '[x21')
                    part = f'        "add x21, x16, #{4 * step}\\n\\t"\n' + part
                    for register, advance in advances:
                        if register in ('x2', 'x3'):
                            part = part.replace(f'[{register}]', f'[{register}, #{step}, mul vl]')
                        elif register == 'x13':
                            part = part.replace('[x13]', f'[x13, #{step * int(advance)}]')
                repeated += part
            for register, advance in advances:
                repeated += f'        "add {register}, {register}, #{factor * int(advance)}\\n\\t"\n'
        new = (
            f'        "cmp x15, #{factor}\\n\\t" "b.lo 42f\\n\\t"\n' + label +
            repeated + f'        "sub x15, x15, #{factor}\\n\\t"\n' +
            f'        "cmp x15, #{factor}\\n\\t" "b.hs 2b\\n\\t"\n' +
            '        "42:\\n\\t"\n        "cbz x15, 44f\\n\\t"\n' +
            '        "43:\\n\\t"\n' + body +
            '        "subs x15, x15, #1\\n\\t" "b.ne 43b\\n\\t"\n' +
            '        "44:\\n\\t"\n')
        source = source[:start] + function.replace(old, new) + source[end:]
    return source


def full_unroll(source):
    shapes = {'k16pair': (81,), 'k16pairf': (41, 81), 'k16pairf3': (55,),
              'k16pairf4': (39,), 'k16single': (55, 81)}
    for name, widths in shapes.items():
        start = source.index('static void ' + name + '(')
        end = source.index('\n}\n', start) + 3
        f = source[start:end]
        label = '        "2:\\n\\t"\n'
        a = f.index(label)
        b = f.index('        "subs x15, x15, #1\\n\\t"\n', a)
        body = f[a + len(label):b]
        old = f[a:b] + '        "subs x15, x15, #1\\n\\t"\n        "b.ne 2b\\n\\t"\n'
        assert f.count(old) == 1
        new = ''
        for i, width in enumerate(widths):
            target = 50 + i
            new += (f'        "cmp x15, #{width}\\n\\t" "b.ne {target}f\\n\\t"\n'
                    f'        ".rept {width}\\n\\t"\n' + body +
                    '        ".endr\\n\\t"\n        "b 54f\\n\\t"\n' +
                    f'        "{target}:\\n\\t"\n')
        new += old + '        "54:\\n\\t"\n'
        source = source[:start] + f.replace(old, new) + source[end:]
    return source


def output_prefetch(source, mode):
    for name in ('k16pair', 'k16pairf', 'k16pairf3', 'k16pairf4', 'k16single'):
        start = source.index('static void ' + name + '(')
        end = source.index('\n}\n', start) + 3
        f = source[start:end]
        if mode in ('none', 'clean'):
            f, count = re.subn(r'"prfm pstl2keep, \[x21(?:, #\d+)?\]\\n\\t"', '""', f)
            assert count in (2, 4), (name, count)
            if mode == 'clean':
                setup = ('"ldr x21, [%[A], #232]\\n\\t"', '"add x21, x9, x21\\n\\t"') if name == 'k16single' else ('"ldr x25, [%[A], #232]\\n\\t"', '"add x21, x9, x25\\n\\t"')
                for instruction in setup:
                    assert f.count(instruction) == 1, (name, instruction)
                    f = f.replace(instruction, '""')
        elif mode == 'l1':
            assert f.count('prfm pstl2keep') in (2, 4)
            f = f.replace('prfm pstl2keep', 'prfm pstl1keep')
        elif mode == 'extra':
            last = 192 if name == 'k16single' else 64
            old = f'"prfm pstl2keep, [x21, #{last}]\\n\\t"'
            assert f.count(old) == 1
            f = f.replace(old, old + f' "prfm pstl2keep, [x21, #{last+64}]\\n\\t"')
        else:
            raise ValueError(mode)
        f = re.sub(r'(?m)^[ \t]*(?:""[ \t]*)+\n', '', f)
        source = source[:start] + f + source[end:]
    return source


def height_fix(source):
    replacements = (
        ('long KH, KW, outW;', 'long KH, KW, outW, outH;'),
        ('if (!same || P->pnth != nth) {', 'if (!same || P->pnth != nth || P->outH != outH) {'),
        ('P->npieces = np; P->pnth = nth;', 'P->npieces = np; P->pnth = nth; P->outH = outH;'))
    for old, new in replacements:
        assert source.count(old) == 1, old
        source = source.replace(old, new)
    return source


def preload_tail(source):
    start = source.index('static void k4(')
    end = source.index('\n}\n', start) + 3
    f = source[start:end]
    old = '        "ldr x12, [%[A], #264]\\n\\t"\n'
    assert f.count(old) == 1
    f = f.replace(old, '')
    old = '        "mov x15, x7\\n\\t"\n'
    assert f.count(old) == 1
    f = f.replace(old, '        "ldr x13, [%[A], #264]\\n\\t"\n' + old)
    for old, new in (('"cbz x12, 42f', '"cbz x13, 42f'),
                     ('"cmp x12, #1', '"cmp x13, #1'),
                     ('"cmp x12, #2', '"cmp x13, #2')):
        assert f.count(old) == 1
        f = f.replace(old, new)
    return source[:start] + f + source[end:]


def compact_kernel(source):
    def replace(old, new):
        nonlocal source
        assert source.count(old) == 1, old[:100]
        source = source.replace(old, new)

    replace('    const float* kb20; long cf20;',
            '    int compact;\n    const float* kb20; long cf20;')
    # Explicit flag avoids inferring a layout from dimensions or pointer values.
    replace('                   NULL, NULL, NULL, 0, NULL, 0 };',
            '                   NULL, NULL, NULL, 0, 0, NULL, 0 };\n'
            '        K.compact = (g->kind >= 16);')
    replace('A->Rend = (int64_t)(P->R + P->KH * P->RSB / 4);',
            'A->Rend = P->compact ? P->steps * P->RSB + 4 : (int64_t)(P->R + P->KH * P->RSB / 4);')
    for side in ('A', 'B'):
        replace(f'A->b{side} = (int64_t)(P->R + P->y{side}0 * P->RSB / 4);',
                f'A->b{side} = (int64_t)(P->R + (P->compact ? (P->KH - P->y{side}0) % P->KH : P->y{side}0 * P->RSB / 4));')
    replace('    if (ncp) roll_copy_row(P->ring, src, ncp);',
            '    A->khkw4 = P->RSB;\n'
            '    if (ncp) roll_copy_row(P->ring, src, ncp);')
    # Each column contains a reversed cyclic kernel-height sequence with 15
    # extra elements. Adjacent y windows share 15/16 values, without rounding.
    replace('    for (int g = 0; g < ng; g++) G[g].RSB = G[g].steps * 64;',
            '    for (int g = 0; g < ng; g++) G[g].RSB = G[g].kind >= 16 ? ((KH + 30) & ~15L) * 4 : G[g].steps * 64;')
    replace('            size_t need = (size_t)KH * G->RSB;',
            '            size_t need = (size_t)(G->kind >= 16 ? G->steps : KH) * G->RSB;')
    old = '            roll_build_R(G->R, k, KH, KW, G->steps, G->s_base, (G->kind == 32 || G->kind == 33 || G->kind == 34 || G->kind == 35 || G->kind == 17) ? 16 : G->kind);'
    replace(old,
            '            if (G->kind >= 16) {\n'
            '                for (long x = 0; x < G->steps; x++)\n'
            '                    for (long y = 0; y < G->RSB / 4; y++)\n'
            '                        G->R[x * (G->RSB / 4) + y] = x < KW ? k[((KH - y % KH) % KH) * KW + x] : 0.0f;\n'
            '            } else {\n' + old + '\n            }')
    # x5 holds the byte span plus four; a completed row returns to the
    # previous element of the first column, wrapping by KH elements.
    for name in ('k16pair', 'k16pairf', 'k16pairf3', 'k16pairf4', 'k16single', 'k16singlef2'):
        start = source.index('static void ' + name + '(')
        end = source.index('\n}\n', start) + 3
        f = source[start:end]
        old = '        "mov x15, x7\\n\\t"\n'
        assert f.count(old) == 1
        f = f.replace(old, '        "ldr x12, [%[A], #272]\\n\\t"\n' + old)
        for reg in ('x2', 'x3'):
            old = f'"add {reg}, {reg}, #64\\n\\t"'
            if old in f:
                f = f.replace(old, f'"add {reg}, {reg}, x12\\n\\t"')
            old = f'WRAP_B({reg})'
            if old in f:
                new = (f'"sub {reg}, {reg}, x5\\n\\t" '
                       f'"cmp {reg}, x4\\n\\t" '
                       f'"add x21, {reg}, x6, lsl #2\\n\\t" '
                       f'"csel {reg}, x21, {reg}, lo\\n\\t"')
                f = f.replace(old, new)
        source = source[:start] + f + source[end:]
    return source


def k4_tail(source):
    start = source.index('static void k4(')
    end = source.index('\n}\n', start) + 3
    f = source[start:end]
    old = '    A.it = steps4 / 4;'
    assert f.count(old) == 1
    f = f.replace(old, '    A.it = (P->KW + 3) / 4;\n    A.kw4 = (P->KW + 3) % 4;')
    old = '        WRAP_B(x2) SEL_OUT\n'
    assert f.count(old) == 1
    new = (
        '        "ldr x12, [%[A], #264]\\n\\t"\n'
        '        "cbz x12, 42f\\n\\t"\n'
        '        K4_STEP(x16, 0)\n'
        '        "cmp x12, #1\\n\\t" "b.eq 41f\\n\\t"\n'
        '        K4_STEP(x22, 1)\n'
        '        "cmp x12, #2\\n\\t" "b.eq 41f\\n\\t"\n'
        '        K4_STEP(x23, 2)\n'
        '        "41:\\n\\t" "add x2, x2, #256\\n\\t"\n'
        '        "42:\\n\\t"\n' + old)
    f = f.replace(old, new)
    return source[:start] + f + source[end:]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', default='24ef2ea')
    parser.add_argument('--out', type=Path, default=Path('build/v51'))
    args = parser.parse_args()
    source = subprocess.check_output(['git', 'show', args.revision + ':conv2d.c'], text=True)
    args.out.mkdir(parents=True, exist_ok=True)
    variants = {'baseline': source, 'unroll2': unroll(source, 2),
                'unroll4': unroll(source, 4), 'k4tail': k4_tail(source),
                'offset2': unroll(source, 2, True), 'offset4': unroll(source, 4, True),
                'full': full_unroll(source), 'nopfo': output_prefetch(source, 'none'),
                'pfol1': output_prefetch(source, 'l1'),
                'pfoextra': output_prefetch(source, 'extra'),
                'compact': compact_kernel(source), 'heightfix': height_fix(source),
                'nopfo_clean': height_fix(output_prefetch(source, 'clean')),
                'combo': height_fix(output_prefetch(k4_tail(source), 'clean')),
                'combo_preload': height_fix(output_prefetch(preload_tail(k4_tail(source)), 'clean'))}
    for name, contents in variants.items():
        path = args.out / (name + '.c')
        path.write_text(contents)
        print(name, hashlib.sha256(contents.encode()).hexdigest())


if __name__ == '__main__':
    main()
