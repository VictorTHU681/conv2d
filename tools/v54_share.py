"""Share identical full sixteen-row coefficient tables within one call."""


def share_tables(source):
    old = 'float* kf; size_t kfcap;'
    assert source.count(old) == 2  # group and retained allocation slot
    source = source.replace(old, old + ' int Rowner;', 1)
    old = '    roll_build_R_row(G->R, k, KH, KW, G->steps, G->s_base,'
    assert source.count(old) == 1
    source = source.replace(old, '    if (G->Rowner == i / (int)KH)\n' + old)
    old = '            G->R = g_rbuf[g].R; G->Rcap = g_rbuf[g].Rcap;'
    extra = r'''
            G->Rowner = g;
            if ((G->kind >= 16) && G->s_base + 16 <= KH) {
                for (int p = 0; p < g; p++) {
                    const rgrp_t* A = &P->G[p];
                    if (A->kind >= 16 && A->s_base + 16 <= KH && A->steps == G->steps) {
                        G->R = A->R; G->Rcap = A->Rcap; G->Rowner = A->Rowner;
                        break;
                    }
                }
            }
'''
    assert source.count(old) == 1
    return source.replace(old, old + extra)
