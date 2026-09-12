#!/usr/bin/env python3
"""Generate exact-FP32 candidates from immutable production v51."""
import hashlib
from pathlib import Path
import re
import subprocess

BASE = 'dfa1bdd003318a756ef54862d8bf9cbc606cb4ff'


def cache_fix(s):
    assert s.count('P->kcopy_n == kn') == 1
    s = s.replace('P->kcopy_n == kn', 'P->kcopy_n >= kn')
    old = '        P->ng = roll_groups(KH, KW, P->G);'
    new = '''        rgrp_t groups[12];
        P->ng = roll_groups(KH, KW, groups);
        for (int g = 0; g < P->ng; g++) {
            groups[g].R = P->G[g].R; groups[g].Rcap = P->G[g].Rcap;
            groups[g].kf = P->G[g].kf; groups[g].kfcap = P->G[g].kfcap;
            P->G[g] = groups[g];
        }'''
    assert s.count(old) == 1
    return s.replace(old, new)


def tune(s, mode):
    for name in ('k16pair', 'k16pairf', 'k16pairf3', 'k16pairf4', 'k16single'):
        a = s.index('static void ' + name + '(')
        b = s.index('\n}\n', a) + 3
        f = s[a:b]
        label = '        "2:\\n\\t"\n'
        start = f.index(label) + len(label)
        end = f.index('        "add x', start)
        body = f[start:end]
        if mode.startswith('align'):
            f = f.replace('        ".p2align 4\\n"\n', '')
            f = f.replace(label, '        ".p2align ' + mode[5:] + '\\n\\t"\n' + label)
        elif mode == 'mix' and name in ('k16pairf', 'k16pairf3', 'k16pairf4'):
            lines = body.splitlines(keepends=True)
            loads = [x for x in lines if 'ld1' in x]
            outer = [x for x in lines if 'fmopa' in x]
            vector = [x for x in lines if '"fmla' in x]
            assert len(loads) + len(outer) + len(vector) == len(lines)
            new = ''.join(loads)
            for i, x in enumerate(outer):
                new += x + ''.join(vector[2*i:2*i+2])
            assert len(outer) == 4 and len(vector) <= 8
            f = f.replace(body, new)
        elif mode == 'early':
            lines = body.splitlines(keepends=True)
            loads = [x for x in lines if 'ld1' in x]
            outer = [x for x in lines if 'fmopa' in x]
            vector = [x for x in lines if '"fmla' in x]
            assert len(loads) + len(outer) + len(vector) == len(lines)
            if name == 'k16single':
                continue
            new = ''.join(loads[:3]) + ''.join(outer[:2]) + ''.join(loads[3:]) + ''.join(outer[2:]) + ''.join(vector)
            f = f.replace(body, new)
        s = s[:a] + f + s[b:]
    return s


def copy_unroll(s, factor):
    a = s.index('#define ROW_HEAD_COMMON')
    b = s.index('\n\n', a)
    macro = s[a:b]
    start = macro.index('        "3:\\n\\t"')
    end = macro.index('        "7:\\n\\t"', start)
    def line(ins):
        return '        "' + ins + '\\n\\t" \\\n'
    new = line(f'cmp x12, #{factor}') + line('b.lo 43f') + line('3:')
    for i in range(factor):
        off = f', #{i}, mul vl' if i else ''
        new += line(f'prfm pldl2keep, [x21, #{64*i}]')
        new += line('ld1w {z24.s}, p0/z, [x22' + off + ']')
        new += line('st1w {z24.s}, p0, [x23' + off + ']')
    for reg in ('x21', 'x22', 'x23'):
        new += line(f'add {reg}, {reg}, #{64*factor}')
    new += line(f'sub x12, x12, #{factor}') + line(f'cmp x12, #{factor}') + line('b.hs 3b')
    new += line('43:') + line('cbz x12, 7f') + line('44:')
    new += line('prfm pldl2keep, [x21]') + line('ld1w {z24.s}, p0/z, [x22]') + line('st1w {z24.s}, p0, [x23]')
    for reg in ('x21', 'x22', 'x23'):
        new += line(f'add {reg}, {reg}, #64')
    new += line('subs x12, x12, #1') + line('b.ne 44b')
    return s[:a] + macro[:start] + new + macro[end:] + s[b:]


def private_done(s):
    changes = (
        ('static padded_u64 g_done __attribute__((aligned(64)));',
         'static padded_u64 g_done_t[1024] __attribute__((aligned(64)));'),
        ('__atomic_fetch_add(&g_done.v, 1, __ATOMIC_ACQ_REL);',
         '__atomic_store_n(&g_done_t[tid].v, g, __ATOMIC_RELEASE);'),
        ('        __atomic_store_n(&g_done.v, 0, __ATOMIC_RELEASE);\n', ''),
        ('        while (__atomic_load_n(&g_done.v, __ATOMIC_ACQUIRE) != (uint64_t)(nth - 1)) asm volatile("yield" ::: "memory");',
         '        for (int t = 1; t < nth; t++)\n'
         '            while (__atomic_load_n(&g_done_t[t].v, __ATOMIC_ACQUIRE) != gen) asm volatile("yield" ::: "memory");'),
    )
    for old, new in changes:
        assert s.count(old) == 1, old
        s = s.replace(old, new)
    return s


def copy_pairf4(s):
    copied = copy_unroll(s, 4)
    a = copied.index('#define ROW_HEAD_COMMON')
    b = copied.index('\n\n', a)
    macro = copied[a:b].replace('ROW_HEAD_COMMON', 'ROW_HEAD_COPY4')
    pos = s.index('// ---------------- 16×1 对')
    s = s[:pos] + macro + '\n\n' + s[pos:]
    a = s.index('static void k16pairf4(')
    b = s.index('\n}\n', a) + 3
    f = s[a:b]
    assert f.count('ROW_HEAD_COMMON') == 1
    return s[:a] + f.replace('ROW_HEAD_COMMON', 'ROW_HEAD_COPY4') + s[b:]


def main():
    source = subprocess.check_output(['git', 'show', BASE + ':conv2d.c'], text=True)
    fixed = cache_fix(source)
    nf4 = fixed.replace('((n16 & 1) ? 3 : 4)', '4')
    assert nf4 != fixed
    variants = dict(baseline=source, cache=fixed, nf4=nf4)
    for mode in ('mix', 'early', 'align6', 'align7'):
        variants[mode] = tune(fixed, mode)
    variants['nf4mix'] = tune(nf4, 'mix')
    variants['copy2'] = copy_unroll(fixed, 2)
    variants['copy4'] = copy_unroll(fixed, 4)
    variants['done'] = private_done(fixed)
    variants['donecopy2'] = private_done(variants['copy2'])
    variants['copy4f4'] = copy_pairf4(fixed)
    out = Path('build/v52')
    out.mkdir(parents=True, exist_ok=True)
    for name, contents in variants.items():
        (out / (name + '.c')).write_text(contents)
        print(name, hashlib.sha256(contents.encode()).hexdigest())


if __name__ == '__main__':
    main()
