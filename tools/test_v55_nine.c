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

static int guard_case(int KW, int OW)
{
    int KH=81,H=2*KH+7,W=KW+OW-1,OH=H-KH+1;
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
    int khs[]={81,113,145,177,209,241};
    int kws[]={3,4,5,16,17,40,41,80,81,127,128,399,400};
    int guard_kws[]={3,4,17,80,81,399,400};
    int ok=1,n=0;
    for (int k=0;k<6;k++) {
        for (int q=0;q<13;q++) {
            int KH=khs[k], KW=kws[q], OW=128+(k+q)%7;
            ok &= run_case(2*KH+7,OW+KW-1,KH,KW,58301+n++,1);
        }
        for (int KW=3;KW<=4;KW++) {
            int KH=khs[k];
            ok &= run_case(17*KH+7,260+KW-1,KH,KW,58301+n++,1);
            int widths[]={64,65,127};
            for (int w=0;w<3;w++)
                ok &= run_case(2*KH+7,widths[w]+KW-1,KH,KW,58301+n++,1);
        }
    }
    for (int q=0;q<7;q++) for (int OW=128;OW<=129;OW++) {
        ok &= guard_case(guard_kws[q],OW); n++;
    }
    printf("NINE_EXTENDED_%s cases=%d\n",ok?"PASS":"FAIL",n);
    return ok?0:1;
}
