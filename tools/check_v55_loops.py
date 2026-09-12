#!/usr/bin/env python3
"""Offline operand-order check for v55 KW loops at the target's 512-bit SVL.

Trace symbolic memory addresses through loads and EXT, recording each FMA's
ordered operands per accumulator. This checks numerical dataflow, not hardware
execution, memory bounds, surrounding row logic, or compiler clobber handling.
Also emit standalone assembly for a local AArch64 assembler syntax check.
"""
import ast
from collections import defaultdict
from pathlib import Path
import re

NAMES = ('k16pair', 'k16pairf', 'k16pairf3', 'k16pairf4', 'k16single')
VARIANTS = ('extall', 'extsingle', 'extpair3', 'unroll2',
            'weaveall', 'weave3', 'weave4')


def extract(source, name):
    start = source.index('static void ' + name + '(')
    start = source.index('        "mov x15, x7', start)
    end = source.index('        WRAP_B(', start)
    literals = re.findall(r'"(?:[^"\\]|\\.)*"', source[start:end])
    return [line.strip() for line in ''.join(map(ast.literal_eval, literals)).splitlines()
            if line.strip()]


def trace(code, kw, offset):
    x = {'x7': kw, 'x16': 1000000 + offset, 'x2': 2000000,
         'x3': 3000000, 'x13': 4000000}
    z, accum = {}, defaultdict(list)
    labels = {line[:-1]: i for i, line in enumerate(code) if line.endswith(':')}
    pc, zero, steps = 0, False, 0
    while pc < len(code):
        ins = code[pc]
        pc += 1
        steps += 1
        assert steps < 100000, 'nonterminating loop'
        if ins.endswith(':') or ins.startswith('.p2align '):
            continue
        m = re.fullmatch(r'(ld1w|ld1rw|ld1rqw) \{(z\d+)\.s\}, p0/z, \[(x\d+)(?:, #(\d+), mul vl)?\]', ins)
        if m:
            op, dest, base, displacement = m.groups()
            addr = x[base] + 64 * int(displacement or 0)
            lanes = {'ld1w': 16, 'ld1rw': 1, 'ld1rqw': 4}[op]
            z[dest] = tuple(addr + 4 * (lane % lanes) for lane in range(16))
            continue
        m = re.fullmatch(r'ext (z\d+)\.b, (z\d+)\.b, (z\d+)\.b, #4', ins)
        if m:
            dest, left, right = m.groups()
            z[dest] = z[left][1:] + z[right][:1]
            continue
        m = re.fullmatch(r'fmopa (za\d+)\.s, p0/m, p0/m, (z\d+)\.s, (z\d+)\.s', ins)
        if m:
            dest, left, right = m.groups()
            accum[dest].append((z[left], z[right]))
            continue
        m = re.fullmatch(r'fmla (z\d+)\.s, (?:p0/m, )?(z\d+)\.s, (z\d+)\.s(?:\[(\d+)\])?', ins)
        if m:
            dest, left, right, index = m.groups()
            rhs = z[right] if index is None else tuple(z[right][4 * (lane // 4) + int(index)] for lane in range(16))
            accum[dest].append((z[left], rhs))
            continue
        m = re.fullmatch(r'(mov|add|subs|lsr) (x\d+), (x\d+)(?:, #(\d+))?', ins)
        if m:
            op, dest, src, immediate = m.groups()
            value, n = x[src], int(immediate or 0)
            x[dest] = {'mov': lambda: value, 'add': lambda: value + n,
                       'subs': lambda: value - n, 'lsr': lambda: value >> n}[op]()
            if op == 'subs':
                zero = x[dest] == 0
            continue
        m = re.fullmatch(r'cbz (x\d+), (\d+)f', ins)
        if m:
            if x[m[1]] == 0:
                pc = labels[m[2]]
            continue
        m = re.fullmatch(r'tbz (x\d+), #(\d+), (\d+)f', ins)
        if m:
            if not (x[m[1]] & (1 << int(m[2]))):
                pc = labels[m[3]]
            continue
        m = re.fullmatch(r'b.ne (\d+)b', ins)
        if m:
            if not zero:
                pc = labels[m[1]]
            continue
        raise AssertionError('Unsupported instruction: ' + ins)
    return dict(accum), tuple(x[r] for r in ('x16', 'x2', 'x3', 'x13'))


def main():
    root = Path('build/v55')
    bounds = 0
    # fill_args copies count*16-1+KW+shift floats into each aligned slot.
    # EXT consumes only the first float of the additional end-vector load.
    # Check both slots against the worker's existing 8192-float allocation.
    for count in (2, 4):
        for kw in range(2, 401):
            for shift in range(16):
                copied = count * 16 - 1 + kw + shift
                slot = (copied + 15) // 16 * 16
                extra = shift + 2 * (kw // 2 - 1) + count * 16
                assert extra < copied
                assert slot + extra + 16 <= 8192
                bounds += 1
    print(f'PASS {bounds} ring end-load bounds combinations (KW <= 400)')
    baseline = (root / 'baseline.c').read_text()
    assembly, checks = ['.text'], 0
    for variant in VARIANTS:
        source = (root / (variant + '.c')).read_text()
        for name in NAMES:
            old, new = extract(baseline, name), extract(source, name)
            assembly += [f'{variant}_{name}:', *new, 'ret']
            for kw in (1, 2, 3, 4, 17, 38, 39, 40, 41, 54, 55, 80, 81, 399, 400):
                for offset in (0, 4, 60):
                    assert trace(old, kw, offset) == trace(new, kw, offset), (variant, name, kw, offset)
                    checks += 1
    (root / 'loops.s').write_text('\n'.join(assembly) + '\n')
    print(f'PASS {checks} symbolic loop comparisons; assembly: {root / "loops.s"}')


if __name__ == '__main__':
    main()
