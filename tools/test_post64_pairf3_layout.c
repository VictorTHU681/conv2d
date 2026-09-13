// Test-only inclusion exposes the real static packer; no production hooks.
#include CONV_SOURCE_FILE
#include <sys/mman.h>
#include <unistd.h>
#include <assert.h>

static void probe(const float *p, float *out)
{
    asm volatile("smstart\n\t"
                 "ptrue p0.s\n\t"
                 "ld1rqw {z0.s}, p0/z, [%0]\n\t"
                 "st1w {z0.s}, p0, [%1]\n\t"
                 "smstop\n\t"
                 :: "r"(p), "r"(out) : "memory", VCLOB, PCLOB);
}

int main(void)
{
    long svl;
    asm volatile("rdsvl %0, #1" : "=r"(svl));
    if (svl != 64) { fprintf(stderr, "Expected SVL 64, got %ld\n", svl); return 1; }
    const int heights[] = {16,39,55,87,119,247,256};
    const int widths[] = {3,4,5,15,16,17,39,55,63,64,65,399,400};
    const uint32_t poison = 0x7fc1dead;
    long pg = sysconf(_SC_PAGESIZE);
    unsigned cases = 0, probes = 0;
    for (unsigned hi=0; hi<sizeof(heights)/sizeof(*heights); hi++)
    for (unsigned wi=0; wi<sizeof(widths)/sizeof(*widths); wi++)
    for (int extra=0; extra<=1; extra++) {
        int kh=heights[hi], kw=widths[wi], steps=kw+extra;
        size_t pitch=3*steps+1, words=kh*pitch, bytes=words*sizeof(float);
        size_t span=(bytes+pg-1)/pg*pg;
        char *map=mmap(NULL,span+2*pg,PROT_NONE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
        assert(map != MAP_FAILED);
        assert(mprotect(map+pg,span,PROT_READ|PROT_WRITE)==0);
        float *table=(float *)(map+pg+span-bytes);
        float *kernel=malloc((size_t)kh*kw*sizeof(float));
        assert(kernel);
        for (int i=0;i<kh*kw;i++) kernel[i]=(float)(i+1)*(i%2 ? -0.125f : 0.125f);
        for (size_t i=0;i<words;i++) memcpy(table+i,&poison,4);
        rplan_t plan={0};
        plan.ng=1; plan.G[0].kind=34; plan.G[0].steps=steps;
        plan.G[0].Rowner=-1; plan.G[0].kf=table;
        int order[256], done[256]={0};
        for (int i=0;i<kh;i++) order[i]=i;
        unsigned rng=0x194abU;
        for (int i=kh-1;i>0;i--) {
            rng=rng*1664525U+1013904223U;
            int j=rng%(i+1), tmp=order[i]; order[i]=order[j]; order[j]=tmp;
        }
        for (int n=0;n<kh;n++) {
            int row=order[n];
            roll_pack_chunk(&plan,kernel,kh,kw,row);
            done[row]=1;
            // Verify every untouched chunk remains poison, every packed one exact.
            for (int y=0;y<kh;y++) for (size_t x=0;x<pitch;x++) {
                uint32_t actual, expected=poison;
                memcpy(&actual,table+y*pitch+x,4);
                if (done[y]) {
                    float val=0.f;
                    if (x < (size_t)3*kw) val=kernel[((y+x%3)%kh)*kw+x/3];
                    memcpy(&expected,&val,4);
                }
                if (actual!=expected) {
                    fprintf(stderr,"FAIL kh=%d kw=%d extra=%d packed=%d row=%d slot=%zu\n",kh,kw,extra,n,y,x);
                    return 1;
                }
            }
            // Actual 16-byte load at this row's final step, repeated across SVL.
            // Last table row ends immediately at a PROT_NONE page.
            float out[16] __attribute__((aligned(64)));
            const float *last=table+row*pitch+3*(steps-1);
            probe(last,out);
            for (int j=0;j<16;j++) assert(memcmp(out+j,last+j%4,4)==0);
            probes++;
        }
        free(kernel); assert(munmap(map,span+2*pg)==0); cases++;
    }
    printf("PAIRF3_LAYOUT PASS cases=%u row_load_probes=%u SVL=%ld\n",cases,probes,svl);
    return 0;
}
