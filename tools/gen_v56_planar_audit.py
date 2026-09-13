#!/usr/bin/env python3
"""Audit initial helper and planar-copy intervals; never use for timing."""
from pathlib import Path
import hashlib
import subprocess

root = Path('build/v56/experiments/planar-audit')
root.mkdir(parents=True, exist_ok=True)
defs = '''static uintptr_t audit_input_lo, audit_input_hi;
static unsigned long audit_calls, audit_overreads, audit_kind_bad[3];
void conv_audit_reset(void) { audit_calls = audit_overreads = 0; }
unsigned long conv_audit_calls(void) { return audit_calls; }
unsigned long conv_audit_overreads(void) { return audit_overreads; }
unsigned long conv_audit_kind(int kind) { return audit_kind_bad[kind]; }
static void audit_span(uintptr_t src, size_t bytes, int kind) {
    __atomic_fetch_add(&audit_calls, 1, __ATOMIC_RELAXED);
    if (src < audit_input_lo || src + bytes > audit_input_hi) {
        __atomic_fetch_add(&audit_overreads, 1, __ATOMIC_RELAXED);
        __atomic_fetch_add(&audit_kind_bad[kind], 1, __ATOMIC_RELAXED);
    }
}
'''
for name, revision in [('local', '93163b4'), ('upstream', 'b9591de')]:
    s = subprocess.check_output(['git', 'show', revision + ':conv2d.c'], text=True)
    a = s.index('static void roll_copy_row(')
    s = s[:a] + defs + s[a:]
    a = s.index('static void roll_copy_row(')
    b = s.index('{', a) + 1
    s = s[:b] + '\n    audit_span((uintptr_t)src, (size_t)n * sizeof(float), 0);\n' + s[b:]
    # These intervals match actual full-vector and predicated-tail loads in
    # the initial K9_CP / K4_CP expansions, before entering their row loops.
    for signature, count, kind in [
        ('static __attribute__((noinline)) void k8f(', 'A.ncp_full * 32 + A.ncp_tail * 2 + A.khkw4', 1),
        ('static void k4(', 'A.ncp_full * 64 + A.ncp_tail * 4', 2),
    ]:
        a = s.index(signature)
        b = s.index('    asm volatile(', a)
        s = s[:b] + f'    audit_span((uintptr_t)A.in_row, (size_t)({count}) * sizeof(float), {kind});\n' + s[b:]
    a = s.index('void conv2d(const CONVFLOAT* input,')
    b = s.index('{', a) + 1
    s = s[:b] + '\n    audit_input_lo = (uintptr_t)input;\n    audit_input_hi = audit_input_lo + (size_t)inputHeight * inputWidth * sizeof(float);\n' + s[b:]
    p = root / (name + '.c')
    p.write_text(s)
    print(hashlib.sha256(s.encode()).hexdigest(), p)
