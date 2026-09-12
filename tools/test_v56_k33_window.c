// K33 unroll boundaries; guard pages after input, coefficients and output.
#define main original_test_main
#include "test_conv.c"
#undef main
#include <sys/mman.h>
#include <unistd.h>

typedef struct { void* mapping; size_t bytes; float* data; } guarded_t;
static guarded_t guarded(size_t n)
{
    size_t page=(size_t)sysconf(_SC_PAGESIZE), bytes=n*sizeof(float);
    size_t usable=(bytes+page-1)/page*page, total=usable+2*page;
    void* p=mmap(NULL,total,PROT_NONE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
    if (p==MAP_FAILED || mprotect((char*)p+page,usable,PROT_READ|PROT_WRITE)) {
        perror("guard allocation"); exit(3);
    }
    return (guarded_t){p,total,(float*)((char*)p+page+usable-bytes)};
}

static int guard_case(int KH, int KW, int OW)
{
    int H=2*KH+7,W=KW+OW-1,OH=H-KH+1;
    size_t ni=(size_t)H*W, nk=(size_t)KH*KW, no=(size_t)OH*OW;
    guarded_t in=guarded(ni), out=guarded(no);
    guarded_t kg=guarded(nk); float* kernel=kg.data;
    float* expected=malloc(no*sizeof(float));
    if (!kernel || !expected) exit(3);
    int seed=58101+KW+OW;
    for (size_t i=0;i<ni;i++) in.data[i]=2*rand_lcg(&seed)-1;
    for (size_t i=0;i<nk;i++) kernel[i]=2*rand_lcg(&seed)-1;
    for (size_t i=0;i<no;i++) out.data[i]=7;
    reference(in.data,H,W,kernel,KH,KW,expected);
    conv2d(in.data,H,W,kernel,KH,KW,out.data);
    int ok=memcmp(out.data,expected,no*sizeof(float))==0;
    printf("GUARD kh=%d kw=%d outW=%d %s\n",KH,KW,OW,ok?"PASS":"FAIL");
    munmap(kg.mapping,kg.bytes); free(expected);
    munmap(in.mapping,in.bytes); munmap(out.mapping,out.bytes);
    return ok;
}

int main(void)
{
    const int khs[]={33,41,49,57,65,105,233};
    const int kws[]={3,4,7,8,9,15,16,17,31,32,33,399,400};
    const int guard_kws[]={3,7,8,15,16,17,400};
    int ok=1,n=0;
    for (int g=0;g<7;g++) for (int j=0;j<13;j++) {
        int KH=khs[g],KW=kws[j],OW=257+(g+j)%3;
        ok &= run_case(KH+4,OW+KW-1,KH,KW,56901+n++,0);
    }
    for (int g=1;g<7;g+=2) {
        int KH=khs[g];
        ok &= run_case(9*KH+5,289,KH,17,57101+n++,1);
    }
    for (int g=0;g<2;g++) for (int j=0;j<7;j++) for (int OW=128;OW<=129;OW++) {
        ok &= guard_case(g?233:41,guard_kws[j],OW);n++;
    }
    printf("K33_WINDOW_%s cases=%d\n",ok?"PASS":"FAIL",n);
    return ok?0:1;
}
