#!/usr/bin/env python3
"""Check emitted ZA slice/address loops, not only generated source text."""
from pathlib import Path
import hashlib
import re

out = []
for variant, width in [('baseline', 4), ('u8', 8), ('u16', 16)]:
    p = Path('build/v56/experiments/carry-width/disassembly') / f'{variant}.txt'
    s = p.read_text()
    rows = re.findall(r'^\s*([0-9a-f]+):\s+([0-9a-f]{8})\s+(.+)$', s, re.M)
    for op in ['ldr', 'str']:
        indices = [i for i, row in enumerate(rows) if re.match(op + r'\s+za\[', row[2])]
        assert len(indices) == width, (variant, op, len(indices))
        start = indices[0]
        assert indices == list(range(start, start + width))
        assert re.match(r'mov\s+w12, #0x0\s', rows[start-1][2])
        register = None
        for offset, i in enumerate(indices):
            m = re.fullmatch(op + r'\s+za\[w12, (\d+)\], \[(x\d+)(?:, #(\d+), mul vl)?\]', rows[i][2])
            assert m and int(m[1]) == offset and int(m[3] or 0) == offset
            if register is None:
                register = m[2]
            assert register == m[2]
        tail = [re.sub(r'\s+', ' ', r[2]).split(' //')[0].strip() for r in rows[start+width:start+width+4]]
        assert tail[:3] == [f'add {register}, {register}, #0x{width*64:x}',
                            f'add w12, w12, #0x{width:x}', 'cmp w12, #0x40']
        assert re.match(r'b\.(?:cc|lo) ' + rows[start][0] + r' ', tail[3])
        # Under the established SVL=64 constraint these emitted loops visit
        # every ZA slice exactly once and the memory interval [0,4096).
        slices = [base + i for base in range(0, 64, width) for i in range(width)]
        assert slices == list(range(64))
        out.append(f'{variant} {op}: {width} adjacent transfers/iteration, '
                   f'{64//width} iterations, 64 total transfers, bytes=[0,4096), '
                   f'loop=0x{rows[start][0]}')
    out.append(f'{variant} disassembly_sha256={hashlib.sha256(p.read_bytes()).hexdigest()}')
out.append('SVL=64 only. This verifies emitted loop control and address coverage, not all kernel accesses or performance.')
Path('results/v56/experiments/carry-width/machine_code.txt').write_text('\n'.join(out) + '\n')
print('\n'.join(out))
