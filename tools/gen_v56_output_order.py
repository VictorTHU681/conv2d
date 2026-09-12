#!/usr/bin/env python3
"""Order overlapping final strips without changing FP32 kernels or their stores."""
from pathlib import Path
import hashlib
import subprocess

source = subprocess.check_output(['git', 'show', '54dc05d:conv2d.c'], text=True)
assert hashlib.sha256(source.encode()).hexdigest() == '695c449ccdc0b234ae16812a49b26afc7a7d0153d5d0b33983c7b3a281f3530b'
def once(s, old, new):
    assert s.count(old) == 1, (s.count(old), old[:100])
    return s.replace(old, new)

link = '''// A clamped final strip overlaps only its immediate predecessor. Order
// intersecting row pieces, leaving disjoint rows and all other strips parallel.
// Dependencies point strictly to earlier items, so the claim graph is acyclic.
static void roll_link_output_dependencies(rplan_t* P)
{
    for (int i = 0; i < P->npieces; i++) {
        rpiece_t* pc = &P->pieces[i];
        pc->dep_first = pc->dep_end = 0;
        const int item = pc->item;
        if (item == 0) continue;
        const ritem_t* current = &P->items[item];
        const ritem_t* previous = &P->items[item - 1];
        if (previous->g != current->g ||
            previous->base + P->G[current->g].width <= current->base) continue;
        for (int j = i - 1; j >= 0; j--) {
            const rpiece_t* other = &P->pieces[j];
            if (other->item < item - 1) break;
            if (other->item != item - 1 || other->jb <= pc->ja || other->ja >= pc->jb) continue;
            if (!pc->dep_end) pc->dep_end = j + 1;
            pc->dep_first = j;
        }
    }
}

'''
s = once(source, 'typedef struct { int item; long ja, jb; } rpiece_t;',
         'typedef struct { int item; long ja, jb; int dep_first, dep_end; } rpiece_t;')
s = once(s, 'static void roll_prepare(', link + 'static void roll_prepare(')
s = once(s, '        P->pstart[nth] = np; P->npieces = np; P->pnth = nth;',
         '        P->pstart[nth] = np; P->npieces = np; P->pnth = nth;\n        roll_link_output_dependencies(P);')
s = once(s, '        uint64_t nw = w | ((uint64_t)1 << 63);', '''        // First claim acquires completion of every overlapping predecessor.
        // Later resumes inherit that ordering through this piece's ready flag.
        if (w == 0) {
            const rpiece_t* pc = &P->pieces[i];
            int pending = 0;
            for (int j = pc->dep_first; j < pc->dep_end; j++) {
                uint64_t done = (uint64_t)(P->pieces[j].jb - P->pieces[j].ja + KH - 1);
                if (__atomic_load_n(&P->ready[j].v, __ATOMIC_ACQUIRE) != done) {
                    pending = 1; break;
                }
            }
            if (pending) continue;
        }
        uint64_t nw = w | ((uint64_t)1 << 63);''')
s = once(s, '    float* out_row0; float* scratch;',
         '    uintptr_t out_row0; float* scratch;')
s = once(s, '                   c->out + (ja - KH + 1) * c->outW + base, scr,',
         '                   (uintptr_t)c->out + (uintptr_t)((ja - KH + 1) * c->outW + base) * sizeof(float), scr,')
root = Path('build/v56/experiments/output-order')
root.mkdir(parents=True, exist_ok=True)
start = s.index('        // First claim acquires completion')
end = s.index('        uint64_t nw = w |', start)
pipelined = s[:start] + '''        // Wait only for the rows this chunk will actually write. A busy
        // predecessor still publishes its completed prefix in the low bits;
        // acquire observes that earlier release through the CAS release sequence.
        const rpiece_t* pc = &P->pieces[i];
        if (pc->dep_first != pc->dep_end) {
            long step = g_roll_step * KH; if (step < KH) step = KH;
            long rows = total - (long)w; if (rows > step) rows = step;
            long lo = pc->ja + (long)w - KH + 1; if (lo < pc->ja) lo = pc->ja;
            long hi = pc->ja + (long)w + rows - KH + 1;
            int pending = 0;
            for (int j = pc->dep_first; j < pc->dep_end; j++) {
                const rpiece_t* previous = &P->pieces[j];
                long begin = lo > previous->ja ? lo : previous->ja;
                long end = hi < previous->jb ? hi : previous->jb;
                if (begin >= end) continue;
                uint64_t need = (uint64_t)(end - previous->ja + KH - 1);
                uint64_t done = __atomic_load_n(&P->ready[j].v, __ATOMIC_ACQUIRE);
                done &= ~((uint64_t)1 << 63);
                if (done < need) { pending = 1; break; }
            }
            if (pending) continue;
        }
''' + s[end:]
for name, code in [('baseline', source), ('ordered', s), ('pipelined', pipelined)]:
    p = root / (name + '.c')
    p.write_text(code)
    print(hashlib.sha256(code.encode()).hexdigest(), p)
