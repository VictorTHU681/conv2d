"""Retain K9 only where it reduces matrix work; balance measured K9 cost."""


def selected_nine(source, weight=130, outline=False):
    old = '    if (!((np>=1 && rem==9) || (np>=2 && rem==17))) return ng;'
    assert source.count(old) == 1
    source = source.replace(old, '    if (np<2 || rem!=17) return ng;')
    old = 'double w = (G->kind == 8 || G->kind == 9) ? g_knobs.roll_w8 / 100.0 :'
    assert source.count(old) == 1
    source = source.replace(old, f'double w = G->kind == 9 ? {weight}/100.0 : G->kind == 8 ? g_knobs.roll_w8 / 100.0 :')
    # KH <= 256: the per-group residual index fits in the original struct's
    # four-byte tail padding, keeping other plan fields and arrays the same size.
    old = 'int Rowner; long sf; } rgrp_t;'
    assert source.count(old) == 1
    source = source.replace(old, 'int Rowner; int sf; } rgrp_t;')
    if outline:
        source = source.replace('static void k8f(', 'static __attribute__((noinline)) void k8f(')
    return source
