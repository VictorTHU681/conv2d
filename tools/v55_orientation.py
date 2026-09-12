"""Transpose rolling ZA tiles and use horizontal output slices.

For finite FP32 values, swapping multiplicands leaves each ordered FMA chain
unchanged. The complete ZA backing state remains saved between row blocks.
"""
import re


def horizontal(source, k4_only=False):
    lo = source.index('#define K4_STEP(' if k4_only else 'static void k16pair(')
    hi = source.index('// b 表：kind 16:', lo)
    part = source[lo:hi]
    pattern = r'(fmopa za\d\.s, p0/m, p0/m, )(z\d+\.s), (z\d+\.s)'
    part, count = re.subn(pattern, r'\1\3, \2', part)
    assert count == (4 if k4_only else 36), count
    part = re.sub(r'(za\d)v\.s', r'\1h.s', part)
    part = part.replace(' #T "v.s', ' #T "h.s')
    assert not re.search(r'za\dv\.s|#T "v\.s', part)
    return source[:lo] + part + source[hi:]
