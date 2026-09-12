// Count actual v54 work pieces. No convolution or performance timing here.
#include "../conv2d.c"

int main(void)
{
    const long shapes[][4] = {{4096,6144,39,39}, {6144,4096,41,41},
                             {4256,6390,55,55}, {6390,4256,81,81}};
    read_knobs();
    for (int c = 0; c < 4; c++) {
        const long H=shapes[c][0], W=shapes[c][1], KH=shapes[c][2], KW=shapes[c][3];
        const long OH=H-KH+1, OW=W-KW+1;
        roll_prepare(NULL,H,W,KH,KW,38);
        const rplan_t* P=&g_rp;
        double infinite=0, unwarmed=0, total=0, transfers=0;
        for (int g=0;g<P->ng;g++) {
            const rgrp_t* G=&P->G[g];
            long steps=G->kind==4 ? KW+3 : G->steps;
            infinite += 4.0*steps*OH*OW/G->width;
        }
        for (int i=0;i<P->npieces;i++) {
            const rpiece_t* pc=&P->pieces[i];
            const rgrp_t* G=&P->G[P->items[pc->item].g];
            long steps=G->kind==4 ? KW+3 : G->steps;
            long rows=pc->jb-pc->ja+KH-1;
            long blocks=(rows+8*KH-1)/(8*KH);
            unwarmed += 4.0*steps*(pc->jb-pc->ja);
            total += 4.0*steps*rows;
            // ZA transfers only; FMLA save/restore is separate in each kernel.
            transfers += 2.0*(blocks-1)*4096;
        }
        const double useful=2.0*OH*OW*KH*KW;
        printf("GEOMETRY kh=%ld groups=%d items=%d pieces=%d tile_steps=%.0f "
               "edge_extra_pct=%.3f warm_extra_pct=%.3f za_transfer_MiB=%.3f "
               "useful_per_opa_flop=%.6f ideal_ms_at_1.55GHz_2cycles_per_opa=%.4f\n",
               KH,P->ng,P->nit,P->npieces,total,100*(unwarmed/infinite-1),
               100*(total/unwarmed-1),transfers/(1024*1024),useful/(total*512),
               total*2/(38*1.55e6));
    }
}
