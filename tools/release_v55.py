#!/usr/bin/env python3
"""Prepare an unpublished v55 candidate from the measured K9 implementation."""
from pathlib import Path
import hashlib
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--variant', default='nine_hoist128')
parser.add_argument('--output', default='final/candidate')
args = parser.parse_args()
source = Path('build/v55', args.variant+'.c').read_text()
source = source.replace(
    '// Structural controls: rem=9 moves the existing fold from pair to K8;\n'
    '// rem=17 with >=2 pairs folds four rows into each of two pairs, leaving nine.\n',
    '// Fold four rows into each of two pairs only when the remaining nine-row\n'
    '// group replaces a single-16 group and reduces matrix work.\n')
pos = source.index('// 滚动形态的结构性开关')
helper = '''// Preserve the original rolling plan when a 128-column K9 strip cannot fit.
static int roll_groups_width(long KH, long KW, rgrp_t* G, long outW)
{
    if (outW >= 128) return roll_groups(KH, KW, G);
    int ng = roll_groups_base(KH, KW, G);
    for (int g = 0; g < ng; g++) G[g].sf = KH - 1;
    return ng;
}
'''
source = source[:pos] + helper + source[pos:]
old = 'rgrp_t G[12]; int ng = roll_groups(KH, KW, G);'
assert source.count(old) == 1
source = source.replace(old, 'rgrp_t G[12]; int ng = roll_groups_width(KH, KW, G, W - KW + 1);')
old = 'P->ng = roll_groups(KH, KW, P->G);'
assert source.count(old) == 1
source = source.replace(old, 'P->ng = roll_groups_width(KH, KW, P->G, outW);')
dest = Path('build/v55', args.output+'.c')
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(source)
print(hashlib.sha256(source.encode()).hexdigest(), dest)
