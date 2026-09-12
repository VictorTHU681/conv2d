// Test real preparation/packing and claim functions from the staged candidate.
#ifndef KF_SOURCE
#define KF_SOURCE "merged.c"
#endif
#include KF_SOURCE
#include <assert.h>

int main(int argc, char** argv) {
    (void)argv;
    read_knobs();
    // Isolate kf ownership from R ownership to exercise the new dependency.
    // Both readiness states use the actual resume_claim implementation.
    rplan_t q={0}; ritem_t item={1,0}; rpiece_t piece={0,0,8,0,0};
    padded_u64 ready={0}; q.items=&item; q.pieces=&piece; q.ready=&ready;
    q.G[1].kind=35; q.G[1].Rowner=1; q.G[1].kfowner=0;
    g_pk_gdone[0].v=0; g_pk_gdone[1].v=1;
    int cursor=0; long off=-1;
    int got=resume_claim(&q,0,1,&cursor,81,&off,1);
    if (argc>1) {
        assert(got==0); puts("KF_GATE_POSITIVE detected_missing_dependency=1"); return 0;
    }
    assert(got==-1);
    g_pk_gdone[0].v=1; cursor=0;
    assert(resume_claim(&q,0,1,&cursor,81,&off,1)==0 && off==0);
    const int khs[]={39,55,71,81,87,103,113,119,145,177,209,241};
    const int kws[]={3,63,64,65,81,400};
    unsigned long cases=0,shared=0,values=0,nonowner_rows=0;
    for(int mode=0;mode<2;mode++) for(int round=0;round<2;round++)
    for(unsigned h=0;h<sizeof(khs)/sizeof(khs[0]);h++)
    for(unsigned w=0;w<sizeof(kws)/sizeof(kws[0]);w++) {
        long KH=khs[h],KW=kws[w];
        float* k=malloc(KH*KW*sizeof(float)); assert(k);
        for(long i=0;i<KH*KW;i++) k[i]=(float)((i*13+round*31+mode*7)%127-63)*0.125f;
        roll_prepare(k,KH+9,KW+272,KH,KW,7);
        rplan_t* P=&g_rp;
        for(int g=0;g<P->ng;g++) {
            rgrp_t* G=&P->G[g]; if(G->kind!=34 && G->kind!=35) continue;
            assert(G->kfowner>=0 && G->kfowner<=g);
            rgrp_t* O=&P->G[G->kfowner];
            assert(O->kf==G->kf && O->steps==G->steps && O->kind==G->kind && O->kfowner==G->kfowner);
            if(G->kfowner==g) memset(G->kf,0x5a,KH*G->steps*4*sizeof(float));
            else shared++;
        }
        // Nonowners must leave the poisoned shared kf table completely untouched.
        for(int g=0;g<P->ng;g++) {
            rgrp_t* G=&P->G[g];
            if((G->kind==34 || G->kind==35) && G->kfowner!=g) {
                for(int y=0;y<KH;y++) {roll_pack_chunk(P,k,KH,KW,g*KH+y);nonowner_rows++;}
                const unsigned char* bytes=(const unsigned char*)G->kf;
                for(size_t n=0;n<(size_t)KH*G->steps*4*sizeof(float);n++) assert(bytes[n]==0x5a);
            }
        }
        const int nc=P->ng*KH;
        if(mode==0) {for(int i=nc-1;i>=0;i--) roll_pack_chunk(P,k,KH,KW,i);}
        else {
#pragma omp parallel for num_threads(7) schedule(dynamic,1)
            for(int i=0;i<nc;i++) roll_pack_chunk(P,k,KH,KW,i);
        }
        for(int g=0;g<P->ng;g++) {
            const rgrp_t* G=&P->G[g]; if(G->kind!=34 && G->kind!=35) continue;
            for(long a=0;a<KH;a++) for(long x=0;x<G->steps;x++) for(int c=0;c<4;c++) {
                float expect=(x<KW && (c<3 || G->kind==35))?k[((a+c)%KH)*KW+x]:0;
                assert(memcmp(&expect,G->kf+(a*G->steps+x)*4+c,sizeof(float))==0); values++;
            }
        }
        free(k);cases++;
    }
    assert(shared>0 && nonowner_rows>0);
    printf("KF_SHARE_PASS cases=%lu shared_groups=%lu nonowner_rows=%lu values=%lu gate_checks=2\n",cases,shared,nonowner_rows,values);
    return 0;
}
