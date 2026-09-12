"""Explore FMLA folds across several pair groups using a structural cost model."""


def multi_fold(source, prefer_more=False):
    old = 'float* kf; size_t kfcap; } rgrp_t;'
    assert source.count(old) == 1
    source = source.replace(old, 'float* kf; size_t kfcap; long sf; } rgrp_t;')
    source = source.replace('static int roll_groups(long KH, long KW, rgrp_t* G)',
                            'static int roll_groups_base(long KH, long KW, rgrp_t* G)')
    pos = source.index('// 滚动形态的结构性开关')
    wrapper = r'''
static double fold_cost(const rgrp_t* G, int ng)
{
    double cost = 0;
    for (int g = 0; g < ng; g++) {
        double w = G[g].kind == 8 ? g_knobs.roll_w8 / 100.0 : G[g].kind == 4 ? g_knobs.roll_w4 / 100.0 : G[g].kind == 16 ? g_knobs.roll_w16 / 100.0 : 1.0;
        cost += G[g].steps * w / G[g].width;
    }
    return cost;
}
static int fold_plan(long KH, long KW, int n4, int n3, int n1, rgrp_t* G)
{
    int np = KH / 32, ng = 0;
    long s = 0, sf = KH - 1;
    for (int p = 0; p < np; p++) {
        int nf = p < n4 ? 4 : p < n4 + n3 ? 3 : p < n4 + n3 + n1 ? 1 : 0;
        int kind = nf == 4 ? 35 : nf == 3 ? 34 : nf == 1 ? 33 : 32;
        G[ng] = (rgrp_t){kind, s, 16, 16, 32, KW, KW * 64, NULL, 0};
        G[ng++].sf = sf; sf -= nf; s += 32;
    }
    long rem = sf + 1 - s;
    if (rem >= 16) { G[ng++] = (rgrp_t){16, s, 16, 0, 64, KW, KW * 64, NULL, 0}; s += 16; rem -= 16; }
    while (rem >= 5) {
        long nv = rem > 8 ? 8 : rem, steps = (KW & 1) ? KW + 1 : KW + 2;
        G[ng++] = (rgrp_t){8, s, nv, 0, 128, steps, steps * 64, NULL, 0}; s += nv; rem -= nv;
    }
    if (rem) { long steps = (KW + 6) & ~3L; G[ng++] = (rgrp_t){4, s, rem, 0, 256, steps, steps * 64, NULL, 0}; }
    return ng;
}
static int roll_groups(long KH, long KW, rgrp_t* G)
{
    int ng = roll_groups_base(KH, KW, G), np = KH / 32;
    for (int g = 0; g < ng; g++) G[g].sf = KH - 1;
    const double base = fold_cost(G, ng);
    double best = base; int bestfold = 0;
    rgrp_t trial[12];
    for (int n4 = 0; n4 <= np; n4++)
        for (int n3 = 0; n3 <= np - n4; n3++)
            for (int n1 = 0; n1 <= np - n4 - n3; n1++) {
                int fold = 4*n4 + 3*n3 + n1;
                if (fold > KH - 32*np) continue;
                int n = fold_plan(KH, KW, n4, n3, n1, trial);
                double cost = fold_cost(trial, n);
                if (cost >= base * .99) continue;
                if (cost < best - 1e-12 || (fabs(cost - best) < 1e-12 && TIE)) {
                    best = cost; bestfold = fold; ng = n;
                    memcpy(G, trial, n * sizeof(*G));
                }
            }
    return ng;
}
'''.replace('TIE', 'fold > bestfold' if prefer_more else 'fold < bestfold')
    source = source[:pos] + wrapper + source[pos:]
    source = source.replace('const long sF = KH - 1,', 'const long sF = g->sf,')
    return source
