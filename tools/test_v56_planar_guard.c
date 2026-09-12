// Structural K9 coverage plus inaccessible pages immediately after input/output.
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
    float* kernel=malloc(nk*sizeof(float));
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
    free(kernel); free(expected);
    munmap(in.mapping,in.bytes); munmap(out.mapping,out.bytes);
    return ok;
}

int main(void)
{
    int khs[]={19,39,55,81,113,231};
    int kws[]={3,4,5,6,7,8,9,10,17,39,40,41,399,400};
    int ok=1,n=0;
    for(int g=0;g<6;g++) for(int k=0;k<14;k++) for(int w=0;w<2;w++) {
        ok &= guard_case(khs[g],kws[k],256+w); n++;
    }
    printf("PLANAR_GUARD_%s cases=%d\n",ok?"PASS":"FAIL",n);
    return ok?0:1;
}
