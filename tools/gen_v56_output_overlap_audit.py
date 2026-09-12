#!/usr/bin/env python3
"""Observe overlapping live output regions around actual SME kernel calls."""
from pathlib import Path
import hashlib

root = Path('build/v56/experiments/output-order')
helper = '''// Diagnostic only: metadata lock does not cover kernel execution.
static int audit_lock;
static unsigned long audit_calls, audit_conflicts;
static struct { int active, group; long lo, hi, col, width; } audit_live[1024];
static void audit_acquire(void) {
    while (__atomic_exchange_n(&audit_lock, 1, __ATOMIC_ACQUIRE)) asm volatile("yield");
}
static int audit_group_row(const rgrp_t* g, long row, long KH) {
    long r = row % KH;
    if (r >= g->s_base && r < g->s_base + g->nvA) return 1;
    if (g->nvB && r >= g->s_base+16 && r < g->s_base+16+g->nvB) return 1;
    int extra = g->kind==35 ? 4 : g->kind==34 ? 3 : (g->kind==33 || g->kind==9) ? 1 : 0;
    if (extra && r <= g->sf && r > g->sf-extra) return 1;
    return g->kind==17 && (r==KH-3 || r==KH-2);
}
static void audit_enter(int tid, const rplan_t* P, int pi, long ja, long rows, long KH) {
    const rpiece_t* pc = &P->pieces[pi];
    const ritem_t* item = &P->items[pc->item];
    const rgrp_t* g = &P->G[item->g];
    long lo = ja-KH+1; if (lo<pc->ja) lo=pc->ja;
    long hi = ja+rows-KH+1; if (hi>pc->jb) hi=pc->jb;
    audit_acquire();
    audit_calls++;
    for (int t=0;t<1024;t++) {
        if (!audit_live[t].active || audit_live[t].group!=item->g ||
            audit_live[t].col+audit_live[t].width<=item->base ||
            item->base+g->width<=audit_live[t].col) continue;
        long begin=lo>audit_live[t].lo?lo:audit_live[t].lo;
        long end=hi<audit_live[t].hi?hi:audit_live[t].hi;
        if (end>begin+KH) end=begin+KH;
        for (long y=begin;y<end;y++) if (audit_group_row(g,y,KH)) { audit_conflicts++; break; }
    }
    audit_live[tid].active=1; audit_live[tid].group=item->g;
    audit_live[tid].lo=lo; audit_live[tid].hi=hi;
    audit_live[tid].col=item->base; audit_live[tid].width=g->width;
    __atomic_store_n(&audit_lock,0,__ATOMIC_RELEASE);
}
static void audit_leave(int tid) {
    audit_acquire(); audit_live[tid].active=0;
    __atomic_store_n(&audit_lock,0,__ATOMIC_RELEASE);
}
void conv_output_audit_report(unsigned long* calls, unsigned long* conflicts) {
    audit_acquire(); *calls=audit_calls; *conflicts=audit_conflicts;
    __atomic_store_n(&audit_lock,0,__ATOMIC_RELEASE);
}

'''
for variant in ['baseline','ordered','pipelined']:
    s = (root/(variant+'.c')).read_text()
    needle = 'static void roll_worker('
    assert s.count(needle)==1
    s = s.replace(needle,helper+needle)
    needle = '        if (g->kind == 32) k16pair(&K);'
    assert s.count(needle)==1
    s = s.replace(needle,'        audit_enter(tid, P, pi, ja, rows, KH);\n'+needle)
    needle = '        if (g_roll_diag) { int ki = roll_kind_idx(g->kind);'
    assert s.count(needle)==1
    s = s.replace(needle,'        audit_leave(tid);\n'+needle)
    path = root/(variant+'_audit.c')
    path.write_text(s)
    print(hashlib.sha256(s.encode()).hexdigest(),path)
