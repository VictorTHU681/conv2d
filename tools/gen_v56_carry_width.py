#!/usr/bin/env python3
"""Isolate ZA loop-control cost after accepted per-call phase preparation."""
from pathlib import Path
import hashlib
import subprocess

root = Path('build/v56/experiments/carry-width')
root.mkdir(parents=True, exist_ok=True)
source = subprocess.check_output(['git', 'show', '8629457:conv2d.c'], text=True)
assert hashlib.sha256(source.encode()).hexdigest() == '1d3f5071d51cd4f8c88720b8d4fa91983515ffd83bdeb4983377a991df2b871a'

def function(text, signature):
    start = text.index(signature)
    return text[start:text.index('\n}\n', start) + 3]

paths = []
for name, width in [('baseline', 4), ('u8', 8), ('u16', 16)]:
    candidate = source
    if width != 4:
        for direction, op, qualifier in [('store', 'str', ''), ('load', 'ldr', 'const ')]:
            signature = f'static inline void carry_{direction}_za('
            original = function(source, signature)
            body = '\n'.join(
                f'                 "{op} za[w12, {i}], [%[p], #{i}, mul vl]\\n\\t"'
                for i in range(width))
            replacement = f'''static inline void carry_{direction}_za({qualifier}float* p)
{{
    asm volatile("mov w12, #0\\n\\t"
                 "49:\\n\\t"
{body}
                 "add %[p], %[p], #{64 * width}\\n\\t"
                 "add w12, w12, #{width}\\n\\t"
                 "cmp w12, #64\\n\\t" "b.lo 49b\\n\\t"
                 : [p] "+r"(p) : : "x12", "memory", "cc");
}}
'''
            assert candidate.count(original) == 1
            candidate = candidate.replace(original, replacement)
        # Everything outside these transfers, including state ownership and
        # FP32 arithmetic, is exactly the accepted source.
        restored = candidate
        for direction in ['store', 'load']:
            signature = f'static inline void carry_{direction}_za('
            restored = restored.replace(function(restored, signature), function(source, signature))
        assert restored == source
    slices = [base + offset for base in range(0, 64, width) for offset in range(width)]
    assert slices == list(range(64))
    assert [(i * 64, (i + 1) * 64) for i in slices][-1][1] == 4096
    path = root / f'{name}.c'
    path.write_text(candidate)
    paths.append(path)

path = root / 'fbench.c'
path.write_bytes(subprocess.check_output(['git', 'show', '8b6b295:tools/fbench.c']))
assert hashlib.sha256(path.read_bytes()).hexdigest() == 'e5e52c8d666584cc49ca6f11162be4868b240e2cc99a3c3ef0a2f8ac292c65ad'
paths.append(path)
for path in paths:
    print(hashlib.sha256(path.read_bytes()).hexdigest(), path)
