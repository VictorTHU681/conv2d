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
                'full': full_unroll(source)}
    for name, contents in variants.items():
        path = args.out / (name + '.c')
        path.write_text(contents)
        print(name, hashlib.sha256(contents.encode()).hexdigest())


if __name__ == '__main__':
    main()
