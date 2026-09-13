// Instrument the first-copy source interval and verify all 16 float alignments.
#define main original_test_main
#include "test_conv.c"
#undef main
void conv_audit_reset(void);
unsigned long conv_audit_calls(void);
unsigned long conv_audit_overreads(void);
int main(void)
{
    int khs[]={39,41,55,81,113,231}, kws[]={3,17,81,400};
    int ok=1, cases=0;
    unsigned long copies=0, overreads=0;
    for (int g=0;g<6;g++) for (int shift=0;shift<16;shift++) {
        int KH=khs[g],KW=kws[shift%4],OH=5,OW=257,H=OH+KH-1,W=OW+KW-1;
        size_t ni=(size_t)H*W,nk=(size_t)KH*KW,no=(size_t)OH*OW;
        float* allocation=NULL;
        if (posix_memalign((void**)&allocation,64,(ni+16)*sizeof(float))) return 3;
        float* in=allocation+shift;
        float* k=malloc(nk*sizeof(float)),*out=malloc(no*sizeof(float)),*ref=malloc(no*sizeof(float));
        if (!k||!out||!ref) return 3;
        int seed=56801+cases;
        for (size_t i=0;i<ni+16;i++) allocation[i]=NAN;
        for (size_t i=0;i<ni;i++) in[i]=2*rand_lcg(&seed)-1;
        for (size_t i=0;i<nk;i++) k[i]=2*rand_lcg(&seed)-1;
        for (size_t i=0;i<no;i++) out[i]=7;
        reference(in,H,W,k,KH,KW,ref);
        conv_audit_reset();
        conv2d(in,H,W,k,KH,KW,out);
        int equal=!memcmp(out,ref,no*sizeof(float));
        ok &= equal;
        copies+=conv_audit_calls();overreads+=conv_audit_overreads();
        if (!equal) printf("FIRST_COPY_FAIL KH=%d KW=%d shift=%d\n",KH,KW,shift);
        free(allocation);free(k);free(out);free(ref);cases++;
    }
    int expect_overread=getenv("AUDIT_EXPECT_OVERREAD")!=NULL;
    ok &= copies>0 && (expect_overread ? overreads>0 : overreads==0);
    printf("FIRST_COPY_AUDIT %s cases=%d copies=%lu outside_input=%lu expected_overread=%d\n",ok?"PASS":"FAIL",cases,copies,overreads,expect_overread);
    return ok?0:1;
}
