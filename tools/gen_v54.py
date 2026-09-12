#!/usr/bin/env python3
"""Reproducible scheduling/packing experiments on the current v53 mainline."""
from pathlib import Path
import hashlib
import subprocess
import re
from v54_carry import carry_blocks
from v54_resume import resumable, clean_resume
from v54_folds import multi_fold
from v54_share import share_tables

BASE = '376da01'


def blocked(source, rows):
    def replace(old, new):
        nonlocal source
        assert source.count(old) == 1, old
        source = source.replace(old, new)
    replace('typedef struct { int g; long base; } ritem_t;',
            'typedef struct { int g; long base, ja, jb; } ritem_t;')
    replace('        int nit = 0;\n',
            f'        const long block_rows = {rows};\n'
            '        const long blocks = (outH + block_rows - 1) / block_rows;\n'
            '        int nit = 0;\n')
    replace('nit += (int)((outW + P->G[g].width - 1) / P->G[g].width);',
            'nit += (int)(blocks * ((outW + P->G[g].width - 1) / P->G[g].width));')
    replace('            for (long st = 0; st < nstrip; st++) {',
            '            for (long row0 = 0; row0 < outH; row0 += block_rows)\n'
            '            for (long st = 0; st < nstrip; st++) {\n'
            '                long row1 = row0 + block_rows; if (row1 > outH) row1 = outH;')
    replace('(ritem_t){g, base}', '(ritem_t){g, base, row0, row1}')
    replace('(double)G->steps * outH * w', '(double)G->steps * (row1 - row0) * w')
    replace('for (int i = 0; i < P->nit; i++) { double w = P->cost[i] / outH; total += w * (outH + ovh); wsum += w; }',
            'for (int i = 0; i < P->nit; i++) { long h = P->items[i].jb - P->items[i].ja; double w = P->cost[i] / h; total += w * (h + ovh); wsum += w; }')
    replace('double w = P->cost[i] / outH; long R = outH - r;',
            'long h = P->items[i].jb - P->items[i].ja;\n'
            '                long row0 = P->items[i].ja;\n'
            '                double w = P->cost[i] / h; long R = h - r;')
    replace('(rpiece_t){i, r, outH}', '(rpiece_t){i, row0 + r, row0 + h}')
    replace('(rpiece_t){i, r, r + rows}', '(rpiece_t){i, row0 + r, row0 + r + rows}')
    return source


def phase_profile(source):
    # Add coarse per-thread packing and host preparation timers, without changing
    # assembly. Fine sampling is handled by perf record in the separate job.
    old = 'static rdiag_t g_rdiag[1024];'
    assert source.count(old) == 1
    source = source.replace(old, old + '\nstatic uint64_t v54_pack_ticks[1024];')
    old = '    roll_pack_all(P, c->k, KH, KW);'
    assert source.count(old) == 1
    source = source.replace(old, '    uint64_t v54_pt = cyc();\n' + old + '\n    v54_pack_ticks[tid] = cyc() - v54_pt;')
    old = '    roll_prepare(k, H, W, KH, KW, nth);'
    assert source.count(old) == 1
    source = source.replace(old, '    uint64_t v54_t0 = cyc();\n' + old + '\n    uint64_t v54_t1 = cyc();')
    old = '    run_parallel(nth, &ctx, g_knobs.pool);\n    if (g_roll_diag)'
    assert source.count(old) == 1
    source = source.replace(old, '''    uint64_t v54_t2 = cyc();
    run_parallel(nth, &ctx, g_knobs.pool);
    uint64_t v54_t3 = cyc(), pkmax = 0, pksum = 0;
    for (int t = 0; t < nth; t++) { pksum += v54_pack_ticks[t]; if (v54_pack_ticks[t] > pkmax) pkmax = v54_pack_ticks[t]; }
    fprintf(stderr, "[v54-phase] prepare_us=%.2f host_pack_us=%.2f workers_us=%.2f pack_worker_mean_us=%.2f pack_worker_max_us=%.2f total_us=%.2f\\n",
            (v54_t1-v54_t0)/100.0, (v54_t2-v54_t1)/100.0, (v54_t3-v54_t2)/100.0,
            pksum/(100.0*nth), pkmax/100.0, (v54_t3-v54_t0)/100.0);
    if (g_roll_diag)''')
    return source


def gather_pack(source):
    a = source.index('static void roll_build_R_row(')
    b = source.index('\n}\n', a) + 3
    signature = source[a:source.index('\n{', a)]
    replacement = '#include <arm_sve.h>\n' + signature + r'''
{
    int32_t offsets[16], shifts[16], live[16];
    for (int c = 0; c < 16; c++) {
        long sidx = kind == 16 ? c : kind == 8 ? c >> 1 : c >> 2;
        long ic = kind == 16 ? 0 : kind == 8 ? c & 1 : c & 3;
        long kj = y - sidx; if (kj < 0) kj += KH;
        offsets[c] = (int32_t)(kj * KW - ic);
        shifts[c] = (int32_t)ic;
        live[c] = s_base + sidx < KH;
    }
    float* Ry = R + y * steps * 16;
    for (int c = 0; c < 16; c += (int)svcntw()) {
        svbool_t lanes = svwhilelt_b32(c, 16);
        svint32_t idx = svld1_s32(lanes, offsets + c);
        svbool_t active = svcmpne_n_s32(lanes, svld1_s32(lanes, live + c), 0);
        if (kind == 16) {
            for (long X = 0; X < steps; X++)
                svst1_f32(lanes, Ry + X*16 + c, svld1_gather_s32index_f32(active, k + X, idx));
        } else {
            svint32_t lo = svld1_s32(lanes, shifts + c);
            svint32_t hi = svadd_n_s32_x(lanes, lo, (int32_t)KW);
            for (long X = 0; X < steps; X++) {
                svbool_t p = svand_b_z(lanes, active, svcmple_n_s32(lanes, lo, (int32_t)X));
                p = svand_b_z(lanes, p, svcmpgt_n_s32(lanes, hi, (int32_t)X));
                svst1_f32(lanes, Ry + X*16 + c, svld1_gather_s32index_f32(p, k + X, idx));
            }
        }
    }
}
'''
    return source[:a] + replacement + source[b:]


def pingpong(source, ahead=False):
    a = source.index('static void k16pairf4(')
    b = source.index('\n}\n', a) + 3
    f = source[a:b]
    label = '        "2:\\n\\t"\n'
    start = f.index(label)
    stop = f.index('        "subs x15, x15, #1\\n\\t"\n', start)
    body = f[start+len(label):stop]
    tail = '        "subs x15, x15, #1\\n\\t"\n        "b.ne 2b\\n\\t"\n'
    old = label + body + tail
    assert f.count(old) == 1
    mapping = {'z0':'z5', 'z1':'z6', 'z2':'z18', 'z3':'z19', 'z4':'z7'}
    alternate = re.sub(r'\bz\d+\b', lambda m: mapping.get(m[0], m[0]), body)
    repeated = body + alternate
    if ahead:
        lines = body.splitlines(keepends=True)
        alt_lines = alternate.splitlines(keepends=True)
        loads = ''.join(x for x in lines if '"ld1' in x)
        math = ''.join(x for x in lines if '"fm' in x)
        alt_loads = ''.join(x for x in alt_lines if '"ld1' in x)
        alt_math = ''.join(x for x in alt_lines if '"fm' in x)
        alt_loads = alt_loads.replace('[x16', '[x21').replace('[x2]', '[x2, #1, mul vl]').replace('[x3]', '[x3, #1, mul vl]').replace('[x13]', '[x13, #16]')
        assert len(lines) == 5 + 12 + 4
        repeated = loads + '        "add x21, x16, #4\\n\\t"\n' + alt_loads + math + alt_math
        for reg, step in [('x13',32), ('x16',8), ('x2',128), ('x3',128)]:
            repeated += f'        "add {reg}, {reg}, #{step}\\n\\t"\n'
    new = ('        "lsr x15, x7, #1\\n\\t"\n        "cbz x15, 43f\\n\\t"\n' + label + repeated + tail +
           '        "43:\\n\\t"\n        "tbz x7, #0, 44f\\n\\t"\n' + body + '        "44:\\n\\t"\n')
    f = f.replace(old, new)
    f = f.replace(': XCLOB, "z0",', ': XCLOB, "z5", "z6", "z7", "z18", "z19", "z0",')
    return source[:a] + f + source[b:]


def main():
    source = subprocess.check_output(['git', 'show', BASE + ':conv2d.c'], text=True)
    variants = {'baseline': source, 'phase': phase_profile(source)}
    for rows in (256, 512, 1024, 2048):
        variants[f'block{rows}'] = blocked(source, rows)
    for rows in (256, 512, 1024):
        variants[f'carry{rows}'] = carry_blocks(source, rows)
    variants['gather'] = gather_pack(source)
    variants['gatherser'] = variants['gather'].replace('if (ps < 0) ps = pk_el <= (1L << 17);', 'if (ps < 0) ps = 1;')
    variants['carrygather'] = carry_blocks(variants['gatherser'], 512)
    variants['pingpong'] = pingpong(source)
    variants['lookahead'] = pingpong(source, True)
    variants['own256'] = carry_blocks(source, 256, mode='own')
    variants['own512'] = carry_blocks(source, 512, mode='own')
    variants['static512'] = carry_blocks(source, 512, mode='static')
    variants['owngather'] = carry_blocks(variants['gatherser'], 256, mode='own')
    for rows in (128, 256, 512):
        variants[f'resume{rows}'] = resumable(source, rows)
    variants['resumegather'] = resumable(variants['gatherser'], 256)
    variants['foldmin'] = multi_fold(source)
    variants['foldmax'] = multi_fold(source, True)
    variants['foldown'] = carry_blocks(variants['foldmin'], 256, mode='own')
    variants['share'] = share_tables(source)
    variants['sharegather'] = share_tables(variants['gatherser'])
    variants['shared256'] = resumable(variants['sharegather'], 256)
    variants['shared512'] = resumable(variants['sharegather'], 512)
    variants['foldshared'] = resumable(share_tables(multi_fold(variants['gatherser'])), 256)
    variants['period8'] = resumable(variants['sharegather'], '8 * KH')
    variants['period16'] = resumable(variants['sharegather'], '16 * KH')
    variants['candidate'] = clean_resume(variants['shared512'])
    variants['candidatephase'] = phase_profile(variants['candidate'])
    out = Path('build/v54')
    out.mkdir(parents=True, exist_ok=True)
    for name, text in variants.items():
        (out / f'{name}.c').write_text(text)
        print(name, hashlib.sha256(text.encode()).hexdigest())


if __name__ == '__main__':
    main()
