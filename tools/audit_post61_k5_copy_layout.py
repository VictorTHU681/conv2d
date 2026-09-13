#!/usr/bin/env python3
"""Check all supported KW/alignment prefix geometries, not machine accesses."""
from collections import Counter
cases = 0
public = Counter()
for kw in range(1, 401):
    live = kw + 191
    for alignment in range(16):
        for mode in range(3):
            sh = 0 if mode == 1 else (3-live%3)%3 if mode == 2 else alignment
            ncp = live + sh
            stride = ((ncp+2)//3 + 15)//16*16 + 16
            full, tail, scalar = ncp//48, ncp%48//3, ncp%3
            assert full*48 + tail*3 + scalar == ncp
            assert ncp-sh == live and 0 <= sh <= 15
            assert full*16+16 <= stride
            if mode == 2:
                assert scalar == 0 and sh <= 2
            # Each compute step q reads 64 values from one plane. All used
            # elements map to q+3*j in live input, independent of the prefix.
            for q in sorted({0, 1, 2, kw-1, kw, kw+1}):
                if not 0 <= q < kw+2:
                    continue
                plane, start = (sh+q)%3, (sh+q)//3
                for j in [0, 63]:
                    x = (start+j)*3+plane-sh
                    assert x == q+3*j and 0 <= x < live
                    assert start+j < stride
            # Later copies use next row, or the current last row. First row
            # initialization is separate and only reads live source values.
            # Noninitial rows are at least one complete input row into the
            # object; a prefix of <=15 floats stays within that object.
            assert live >= sh
            cases += 1
            if kw == 41 and alignment in [0, 4, 8, 12]:
                public[mode, alignment] = (sh, full, tail, scalar, stride)
print(f'{cases} KW/alignment/mode geometries PASS. Per-plane endpoint mappings and copy lengths validate; this is a geometry model, not an audit of all assembly accesses.')
for (mode, alignment), values in sorted(public.items()):
    print(f'KH41/KW41 mode={mode} alignment={alignment}: prefix/full48/tail_triples/scalars/stride={values}')
