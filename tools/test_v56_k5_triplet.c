// Independent ordered reference, exact input intervals and guarded tail arrays.
#define main original_test_main
#include "test_conv.c"
#undef main
#include <sys/mman.h>
#include <unistd.h>
#ifdef K5_INPUT_AUDIT
void conv_audit_report(unsigned long*,unsigned long*);
#endif
typedef struct { void* map; size_t bytes; float* p; } guarded_t;
static guarded_t guard_alloc(size_t n) {
    size_t page=(size_t)sysconf(_SC_PAGESIZE),live=n*sizeof(float);
    size_t usable=(live+page-1)/page*page,total=usable+2*page;
    void* p=mmap(NULL,total,PROT_NONE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
    if(p==MAP_FAILED || mprotect((char*)p+page,usable,PROT_READ|PROT_WRITE)) exit(3);
    return (guarded_t){p,total,(float*)((char*)p+page+usable-live)};
}
static int aligned_case(int KH,int KW,int OW,int shift,int guard) {
    int OH=3+shift%5,H=OH+KH-1,W=OW+KW-1,seed=57101+KH*17+KW+shift;
    size_t ni=(size_t)H*W,nk=(size_t)KH*KW,no=(size_t)OH*OW;
    float *allocation=NULL,*input,*kernel,*output,*expected=malloc(no*sizeof(float));
    guarded_t gi={0},gk={0},go={0};
    if(guard) {
        gi=guard_alloc(ni);gk=guard_alloc(nk);go=guard_alloc(no);
        input=gi.p;kernel=gk.p;output=go.p;
    } else {
        if(posix_memalign((void**)&allocation,64,(ni+16)*sizeof(float))) exit(3);
        for(size_t i=0;i<ni+16;i++) allocation[i]=NAN;
        input=allocation+shift;kernel=malloc(nk*sizeof(float));output=malloc(no*sizeof(float));
    }
    if(!expected||!input||!kernel||!output) exit(3);
    for(size_t i=0;i<ni;i++) input[i]=2*rand_lcg(&seed)-1;
    for(size_t i=0;i<nk;i++) kernel[i]=2*rand_lcg(&seed)-1;
    for(size_t i=0;i<no;i++) output[i]=7;
    reference(input,H,W,kernel,KH,KW,expected);
    conv2d(input,H,W,kernel,KH,KW,output);
    int ok=!memcmp(output,expected,no*sizeof(float));
    if(!ok) printf("K5_FAIL kh=%d kw=%d ow=%d shift=%d guard=%d\n",KH,KW,OW,shift,guard);
    if(guard) { munmap(gi.map,gi.bytes);munmap(gk.map,gk.bytes);munmap(go.map,go.bytes); }
    else { free(allocation);free(kernel);free(output); }
    free(expected);return ok;
}
int main(void) {
    int kws[]={3,4,5,6,7,8,17,18,19,398,399,400};
    int widths[]={191,192,193,255,383,384,385};
    int ok=1,cases=0;
    for(int kh=41;kh<=249;kh+=16) {
        for(int shift=0;shift<16;shift++) {
            ok &= aligned_case(kh,kws[shift%12],192+shift%3,shift,0);cases++;
        }
        for(int w=0;w<7;w++) for(int kw=3;kw<=5;kw++) {
            ok &= run_case(kh+2,widths[w]+kw-1,kh,kw,57501+cases,0);cases++;
        }
    }
    const int tall[]={41,57,105,249},gkws[]={3,4,5,398,399,400};
    for(int g=0;g<4;g++) {
        for(int r=0;r<2;r++) {
            int kh=tall[g],kw=7+r*12,oh=8*kh+17+r;
            ok &= run_case(oh+kh-1,385+kw-1,kh,kw,57901+cases,0);cases++;
        }
        for(int k=0;k<6;k++) for(int w=192;w<=193;w++) {
            ok &= aligned_case(tall[g],gkws[k],w,0,1);cases++;
        }
    }
#ifdef K5_INPUT_AUDIT
    unsigned long calls,outside;
    conv_audit_report(&calls,&outside);ok &= calls>0 && outside==0;
    printf("K5_INPUT_AUDIT calls=%lu outside=%lu\n",calls,outside);
#endif
    printf("K5_EXTENDED %s cases=%d\n",ok?"PASS":"FAIL",cases);
    return ok?0:1;
}
