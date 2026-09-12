"""Resume individual strips from published block boundaries, with work stealing."""
from v54_carry import carry_blocks


def clean_resume(source):
    """Remove obsolete batch claiming and document the retained state protocol."""
    a = source.index('static int carry_claim(')
    b = source.index('static int resume_claim(', a)
    source = source[:a] + source[b:]
    source = source.replace('kw4, khkw4, carry, resume;\n} ka_t;',
        'kw4, khkw4, carry, resume;\n} ka_t;\n_Static_assert(offsetof(ka_t, carry) == 280 && offsetof(ka_t, resume) == 288, "rolling state assembly offsets");')
    source = source.replace('static int resume_claim(',
        '// Each strip publishes progress after saving ZA and the live FMLA vectors.\n'
        '// Acquire/release transfers those accumulators when another worker resumes it.\n'
        'static int resume_claim(')
    source = source.replace('    long step = 512; if (step < KH) step = KH;',
        '    // Neighboring strips reuse input rows; state carry avoids repeated warm-up.\n'
        '    long step = 512; if (step < KH) step = KH;')
    return source


def resumable(source, block_rows):
    source = carry_blocks(source, block_rows)
    source = source.replace('float* carry; int nthr_alloc;',
                            'float* carry; padded_u64* ready; size_t carry_cap; int nthr_alloc;')
    source = source.replace('free(P->rings); free(P->scratch); free(P->carry);',
                            'free(P->rings); free(P->scratch);')
    old = '        P->carry = alloc_aligned((size_t)nth * 4 * 4608);\n'
    assert source.count(old) == 1
    source = source.replace(old, '')
    start = source.index('static void roll_prepare(')
    end = source.index('\n}\n', start)
    allocation = '''
    if (P->carry_cap < (size_t)P->npieces) {
        free(P->carry); free(P->ready);
        P->carry = alloc_aligned((size_t)P->npieces * 4608);
        P->ready = alloc_aligned((size_t)P->npieces * sizeof(padded_u64));
        P->carry_cap = P->npieces;
    }
    memset(P->ready, 0, (size_t)P->npieces * sizeof(padded_u64));
'''
    source = source[:end] + allocation + source[end:]
    a = source.index('static void roll_worker(')
    b = source.index('\nstatic void roll_diag_print', a)
    old = source[a:b]
    body = old[old.index('        const rgrp_t* g ='):old.index('\n            }\n        }')]
    helper = r'''
static int resume_claim(const rplan_t* P, int first, int last, int* cursor, long KH, long* off)
{
    for (int n = first; n < last; n++) {
        int i = *cursor;
        if (++*cursor >= last) *cursor = first;
        uint64_t w = __atomic_load_n(&P->ready[i].v, __ATOMIC_RELAXED);
        long total = P->pieces[i].jb - P->pieces[i].ja + KH - 1;
        if (w >= (uint64_t)total) continue; // Includes the high-bit busy marker.
        uint64_t nw = w | ((uint64_t)1 << 63);
        if (__atomic_compare_exchange_n(&P->ready[i].v, &w, nw, 0, __ATOMIC_ACQUIRE, __ATOMIC_RELAXED)) {
            *off = (long)w; return i;
        }
    }
    return -1;
}
'''
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
    const int first = P->pstart[tid], last = P->pstart[tid+1];
    int cursor = first, other = last < P->npieces ? last : 0;
    long step = {block_rows}; if (step < KH) step = KH;
    for (;;) {{
        long off = 0;
        int pi = resume_claim(P, first, last, &cursor, KH, &off);
        if (pi < 0) pi = resume_claim(P, 0, P->npieces, &other, KH, &off);
        if (pi < 0) break;
        const rpiece_t* pc = &P->pieces[pi];
        long total = pc->jb - pc->ja + KH - 1;
        long rows = total - off; if (rows > step) rows = step;
        const long ja = pc->ja + off;
        float* state = P->carry + (size_t)pi * 1152;
{body}
        __atomic_store_n(&P->ready[pi].v, (uint64_t)(off + rows), __ATOMIC_RELEASE);
    }}
    sme_stop();
    if (g_roll_diag) D->tot = cyc() - t_start;
}}
'''
    return source[:a] + helper + worker + source[b:]
