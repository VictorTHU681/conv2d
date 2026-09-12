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


def main():
    source = subprocess.check_output(['git', 'show', BASE + ':conv2d.c'], text=True)
    fixed = cache_fix(source)
    nf4 = fixed.replace('((n16 & 1) ? 3 : 4)', '4')
    assert nf4 != fixed
    variants = dict(baseline=source, cache=fixed, nf4=nf4)
    for mode in ('mix', 'early', 'align6', 'align7'):
        variants[mode] = tune(fixed, mode)
    variants['nf4mix'] = tune(nf4, 'mix')
    out = Path('build/v52')
    out.mkdir(parents=True, exist_ok=True)
    for name, contents in variants.items():
        (out / (name + '.c')).write_text(contents)
        print(name, hashlib.sha256(contents.encode()).hexdigest())


if __name__ == '__main__':
    main()
