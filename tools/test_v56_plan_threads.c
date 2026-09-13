// Actual convolution calls alternate output width and OpenMP thread count.
#define main original_test_main
#include "test_conv.c"
#undef main
int main(void) {
    const int khs[]={41,39,55,81};
    const int threads[]={1,38,2,7,1,38};
    const int widths[]={8192,512,4096,257,8192,513};
    int ok=1,cases=0;
    omp_set_dynamic(0);
    for(int k=0;k<4;k++) for(int t=0;t<6;t++) {
        int kh=khs[k],kw=3+2*k,oh=37+3*t,ow=widths[t];
        omp_set_num_threads(threads[t]);
        printf("PLAN_THREADS_CASE nth=%d kh=%d ow=%d\n",threads[t],kh,ow);
        ok &= run_case(oh+kh-1,ow+kw-1,kh,kw,58001+cases,1);
        cases++;
    }
    printf("PLAN_THREADS %s cases=%d\n",ok?"PASS":"FAIL",cases);
    return ok?0:1;
}
