"""Carry ZA and FMLA state across row blocks; retain each output's FMA order."""


def carry_blocks(source, block_rows, batch=4, mode='greedy'):
    def replace(old, new):
        nonlocal source
        assert source.count(old) == 1, old[:120]
        source = source.replace(old, new)

    replace('kw4, khkw4;\n} ka_t;', 'kw4, khkw4, carry, resume;\n} ka_t;')
    replace('} kp_t;', '    float* carry; long resume;\n} kp_t;')
    replace('    (void)slot_unused;', '    (void)slot_unused;\n    A->carry = (int64_t)P->carry; A->resume = P->resume;')
    replace('A->va = P->KH - 1;', 'A->va = P->resume ? 0 : P->KH - 1;')
    replace('float* rings; float* scratch; int nthr_alloc;', 'float* rings; float* scratch; float* carry; int nthr_alloc;')
    replace('free(P->rings); free(P->scratch);', 'free(P->rings); free(P->scratch); free(P->carry);')
    replace('        P->nthr_alloc = nth;',
            f'        P->carry = alloc_aligned((size_t)nth * {batch} * 4608);\n        P->nthr_alloc = nth;')

    def asm(ins):
        return '        "' + ins + '\\n\\t"\n'

    # FMLA registers are live accumulators outside ZA. Save/restore those too.
    for name, regs in [('k16pairf', range(10, 12)), ('k16pairf3', range(10, 16)),
                       ('k16pairf4', range(10, 18)), ('k16singlef2', range(16, 24))]:
        a = source.index('static void ' + name + '(')
        b = source.index('\n}\n', a) + 3
        f = source[a:b]
        label = '        "1:\\n\\t"\n'
        restore = asm('ldr x12, [%[A], #288]') + asm('cbz x12, 47f')
        restore += asm('ldr x12, [%[A], #280]')
        for i, reg in enumerate(regs):
            restore += asm(f'ld1w {{z{reg}.s}}, p0/z, [x12, #{i}, mul vl]')
        restore += asm('47:')
        assert f.count(label) == 1
        f = f.replace(label, restore + label)
        save = asm('ldr x12, [%[A], #280]') + asm('cbz x12, 48f')
        for i, reg in enumerate(regs):
            save += asm(f'st1w {{z{reg}.s}}, p0, [x12, #{i}, mul vl]')
        save += asm('48:')
        assert f.count('        ROW_TAIL\n') == 1
        f = f.replace('        ROW_TAIL\n', '        ROW_TAIL\n' + save)
        source = source[:a] + f + source[b:]

    a = source.index('static void roll_worker(')
    b = source.index('\nstatic void roll_diag_print', a)
    old = source[a:b]
    # Preserve the arithmetic dispatch and all starting coefficient indices.
    body = old[old.index('        const rgrp_t* g ='):old.index('\n    }\n    sme_stop();')]
    body = body.replace('jb - ja + KH - 1', 'rows')
    body = body.replace('        sme_zero_za();',
                        '        K.carry = state + 1024; K.resume = off != 0;\n'
                        '        if (off) carry_load_za(state); else sme_zero_za();')
    body += '\n        if (off + rows < total) carry_store_za(state);\n'
    helpers = r'''
static inline void carry_store_za(float* p)
{
    asm volatile("mov w12, #0\n\t"
                 "49: str za[w12, 0], [%[p]]\n\t"
                 "add %[p], %[p], #64\n\t"
                 "add w12, w12, #1\n\t"
                 "cmp w12, #64\n\t" "b.lo 49b\n\t"
                 : [p] "+r"(p) : : "x12", "memory", "cc");
}
static inline void carry_load_za(const float* p)
{
    asm volatile("mov w12, #0\n\t"
                 "49: ldr za[w12, 0], [%[p]]\n\t"
                 "add %[p], %[p], #64\n\t"
                 "add w12, w12, #1\n\t"
                 "cmp w12, #64\n\t" "b.lo 49b\n\t"
                 : [p] "+r"(p) : : "x12", "memory", "cc");
}
static int carry_claim(int tid, int nth)
{
    int victim = tid;
    for (;;) {
        uint64_t w = __atomic_load_n(&g_rwork[victim].v, __ATOMIC_RELAXED);
        uint32_t cur = (uint32_t)w, end = (uint32_t)(w >> 32);
        if (cur < end) {
            uint64_t nw = victim == tid ? w + 1 : w - ((uint64_t)1 << 32);
            if (__atomic_compare_exchange_n(&g_rwork[victim].v, &w, nw, 1, __ATOMIC_RELAXED, __ATOMIC_RELAXED))
                return victim == tid ? (int)cur : (int)end - 1;
            continue;
        }
        if (victim != tid) { victim = tid; continue; }
        int best = -1; uint32_t most = 0;
        for (int t = 0; t < nth; t++) {
            w = __atomic_load_n(&g_rwork[t].v, __ATOMIC_RELAXED);
            uint32_t rem = (uint32_t)(w >> 32) - (uint32_t)w;
            if ((int32_t)rem > 0 && rem > most) { most = rem; best = t; }
        }
        if (best < 0) return -1;
        victim = best;
    }
}
'''
    claim = 'carry_claim'
    empty = 'if (!count) break;'
    if mode != 'greedy':
        claim = 'carry_claim_own'
        helpers += r'''
static int carry_claim_own(int tid, int nth)
{
    (void)nth;
    for (;;) {
        uint64_t w = __atomic_load_n(&g_rwork[tid].v, __ATOMIC_RELAXED);
        if ((uint32_t)w >= (uint32_t)(w >> 32)) return -1;
        uint64_t nw = w + 1;
        if (__atomic_compare_exchange_n(&g_rwork[tid].v, &w, nw, 1, __ATOMIC_RELAXED, __ATOMIC_RELAXED)) return (int)(uint32_t)w;
    }
}
'''
        if mode == 'own':
            empty = '''if (!count) {
            int pi = carry_claim(tid, nth); if (pi < 0) break;
            ids[count++] = pi;
            longest = P->pieces[pi].jb - P->pieces[pi].ja + KH - 1;
        }'''
    worker = f'''
static void roll_worker(int tid, int nth, const ctx_t* c)
{{
    const rplan_t* P = (const rplan_t*)c->rp;
    const long KH = c->KH, KW = c->KW, W = c->W;
    float* ring = P->rings + (size_t)tid * 8192; float* scr = P->scratch + (size_t)tid * 2048;
    rdiag_t* D = &g_rdiag[tid]; uint64_t t_start = 0;
    if (g_roll_diag) {{ memset(D, 0, sizeof(*D)); t_start = cyc(); }}
    if (tid >= nth || tid >= P->pnth) return;
    roll_pack_all(P, c->k, KH, KW);
    sme_start();
    for (;;) {{
        int ids[{batch}], count = 0; long longest = 0;
        for (int i = 0; i < {batch}; i++) {{
            int pi = {claim}(tid, nth); if (pi < 0) break;
            ids[count++] = pi;
            long n = P->pieces[pi].jb - P->pieces[pi].ja + KH - 1;
            if (n > longest) longest = n;
        }}
        {empty}
        long step = count == 1 ? longest : {block_rows};
        if (step < KH) step = KH;
        for (long off = 0; off < longest; off += step) {{
            for (int bi = 0; bi < count; bi++) {{
                const rpiece_t* pc = &P->pieces[ids[bi]];
                long total = pc->jb - pc->ja + KH - 1;
                if (off >= total) continue;
                long rows = total - off; if (rows > step) rows = step;
                const long ja = pc->ja + off;
                float* state = P->carry + ((size_t)tid * {batch} + bi) * 1152;
{body}
            }}
        }}
    }}
    sme_stop();
    if (g_roll_diag) D->tot = cyc() - t_start;
}}
'''
    return source[:a] + helpers + worker + source[b:]
