// Hardware throughput control; no change to the production operator.
#include "../conv2d.c"
#include <stdio.h>
static double v55_peak(int nf)
{
    const long iterations = 3000000;
    uint64_t elapsed[1024] = {0}; int nth = 0;
#pragma omp parallel
    {
        int tid=omp_get_thread_num();
#pragma omp single
        nth=omp_get_num_threads();
        sme_start();
        asm volatile("ptrue p0.s\n\t zero {za}\n\t fmov z0.s, #1.0\n\t fmov z1.s, #1.0\n\t"
                     ::: "z0", "z1", "p0", "memory");
        asm volatile("fmov z8.s, #0.0" ::: "z8");
        asm volatile("fmov z9.s, #0.0" ::: "z9");
        asm volatile("fmov z10.s, #0.0" ::: "z10");
        asm volatile("fmov z11.s, #0.0" ::: "z11");
        asm volatile("fmov z12.s, #0.0" ::: "z12");
        asm volatile("fmov z13.s, #0.0" ::: "z13");
        asm volatile("fmov z14.s, #0.0" ::: "z14");
        asm volatile("fmov z15.s, #0.0" ::: "z15");
        asm volatile("fmov z16.s, #0.0" ::: "z16");
        asm volatile("fmov z17.s, #0.0" ::: "z17");
        asm volatile("fmov z18.s, #0.0" ::: "z18");
        asm volatile("fmov z19.s, #0.0" ::: "z19");
        asm volatile("fmov z20.s, #0.0" ::: "z20");
        asm volatile("fmov z21.s, #0.0" ::: "z21");
        asm volatile("fmov z22.s, #0.0" ::: "z22");
        asm volatile("fmov z23.s, #0.0" ::: "z23");
        uint64_t t0=cyc(); long n=iterations;
        if (nf==0) asm volatile("1:\n\t"
            "fmopa za0.s, p0/m, p0/m, z0.s, z1.s\n\t"
            "fmopa za1.s, p0/m, p0/m, z0.s, z1.s\n\t"
            "fmopa za2.s, p0/m, p0/m, z0.s, z1.s\n\t"
            "fmopa za3.s, p0/m, p0/m, z0.s, z1.s\n\t"
            "fmopa za0.s, p0/m, p0/m, z0.s, z1.s\n\t"
            "fmopa za1.s, p0/m, p0/m, z0.s, z1.s\n\t"
            "fmopa za2.s, p0/m, p0/m, z0.s, z1.s\n\t"
            "fmopa za3.s, p0/m, p0/m, z0.s, z1.s\n\t"
            "subs %[n], %[n], #1\n\t b.ne 1b\n\t"
            : [n] "+r"(n) : : "memory", "cc", "z8","z9","z10","z11","z12","z13","z14","z15","z16","z17","z18","z19","z20","z21","z22","z23");
        else if (nf==8) asm volatile("1:\n\t"
            "fmopa za0.s, p0/m, p0/m, z0.s, z1.s\n\t"
            "fmla z8.s, p0/m, z0.s, z1.s\n\t"
            "fmopa za1.s, p0/m, p0/m, z0.s, z1.s\n\t"
            "fmla z9.s, p0/m, z0.s, z1.s\n\t"
            "fmopa za2.s, p0/m, p0/m, z0.s, z1.s\n\t"
            "fmla z10.s, p0/m, z0.s, z1.s\n\t"
            "fmopa za3.s, p0/m, p0/m, z0.s, z1.s\n\t"
            "fmla z11.s, p0/m, z0.s, z1.s\n\t"
            "fmopa za0.s, p0/m, p0/m, z0.s, z1.s\n\t"
            "fmla z12.s, p0/m, z0.s, z1.s\n\t"
            "fmopa za1.s, p0/m, p0/m, z0.s, z1.s\n\t"
            "fmla z13.s, p0/m, z0.s, z1.s\n\t"
            "fmopa za2.s, p0/m, p0/m, z0.s, z1.s\n\t"
            "fmla z14.s, p0/m, z0.s, z1.s\n\t"
            "fmopa za3.s, p0/m, p0/m, z0.s, z1.s\n\t"
            "fmla z15.s, p0/m, z0.s, z1.s\n\t"
            "subs %[n], %[n], #1\n\t b.ne 1b\n\t"
            : [n] "+r"(n) : : "memory", "cc", "z8","z9","z10","z11","z12","z13","z14","z15","z16","z17","z18","z19","z20","z21","z22","z23");
        else if (nf==16) asm volatile("1:\n\t"
            "fmopa za0.s, p0/m, p0/m, z0.s, z1.s\n\t"
            "fmla z8.s, p0/m, z0.s, z1.s\n\t"
            "fmla z9.s, p0/m, z0.s, z1.s\n\t"
            "fmopa za1.s, p0/m, p0/m, z0.s, z1.s\n\t"
            "fmla z10.s, p0/m, z0.s, z1.s\n\t"
            "fmla z11.s, p0/m, z0.s, z1.s\n\t"
            "fmopa za2.s, p0/m, p0/m, z0.s, z1.s\n\t"
            "fmla z12.s, p0/m, z0.s, z1.s\n\t"
            "fmla z13.s, p0/m, z0.s, z1.s\n\t"
            "fmopa za3.s, p0/m, p0/m, z0.s, z1.s\n\t"
            "fmla z14.s, p0/m, z0.s, z1.s\n\t"
            "fmla z15.s, p0/m, z0.s, z1.s\n\t"
            "fmopa za0.s, p0/m, p0/m, z0.s, z1.s\n\t"
            "fmla z16.s, p0/m, z0.s, z1.s\n\t"
            "fmla z17.s, p0/m, z0.s, z1.s\n\t"
            "fmopa za1.s, p0/m, p0/m, z0.s, z1.s\n\t"
            "fmla z18.s, p0/m, z0.s, z1.s\n\t"
            "fmla z19.s, p0/m, z0.s, z1.s\n\t"
            "fmopa za2.s, p0/m, p0/m, z0.s, z1.s\n\t"
            "fmla z20.s, p0/m, z0.s, z1.s\n\t"
            "fmla z21.s, p0/m, z0.s, z1.s\n\t"
            "fmopa za3.s, p0/m, p0/m, z0.s, z1.s\n\t"
            "fmla z22.s, p0/m, z0.s, z1.s\n\t"
            "fmla z23.s, p0/m, z0.s, z1.s\n\t"
            "subs %[n], %[n], #1\n\t b.ne 1b\n\t"
            : [n] "+r"(n) : : "memory", "cc", "z8","z9","z10","z11","z12","z13","z14","z15","z16","z17","z18","z19","z20","z21","z22","z23");
        else if (nf==32) asm volatile("1:\n\t"
            "fmopa za0.s, p0/m, p0/m, z0.s, z1.s\n\t"
            "fmla z8.s, p0/m, z0.s, z1.s\n\t"
            "fmla z9.s, p0/m, z0.s, z1.s\n\t"
            "fmla z10.s, p0/m, z0.s, z1.s\n\t"
            "fmla z11.s, p0/m, z0.s, z1.s\n\t"
            "fmopa za1.s, p0/m, p0/m, z0.s, z1.s\n\t"
            "fmla z12.s, p0/m, z0.s, z1.s\n\t"
            "fmla z13.s, p0/m, z0.s, z1.s\n\t"
            "fmla z14.s, p0/m, z0.s, z1.s\n\t"
            "fmla z15.s, p0/m, z0.s, z1.s\n\t"
            "fmopa za2.s, p0/m, p0/m, z0.s, z1.s\n\t"
            "fmla z16.s, p0/m, z0.s, z1.s\n\t"
            "fmla z17.s, p0/m, z0.s, z1.s\n\t"
            "fmla z18.s, p0/m, z0.s, z1.s\n\t"
            "fmla z19.s, p0/m, z0.s, z1.s\n\t"
            "fmopa za3.s, p0/m, p0/m, z0.s, z1.s\n\t"
            "fmla z20.s, p0/m, z0.s, z1.s\n\t"
            "fmla z21.s, p0/m, z0.s, z1.s\n\t"
            "fmla z22.s, p0/m, z0.s, z1.s\n\t"
            "fmla z23.s, p0/m, z0.s, z1.s\n\t"
            "fmopa za0.s, p0/m, p0/m, z0.s, z1.s\n\t"
            "fmla z8.s, p0/m, z0.s, z1.s\n\t"
            "fmla z9.s, p0/m, z0.s, z1.s\n\t"
            "fmla z10.s, p0/m, z0.s, z1.s\n\t"
            "fmla z11.s, p0/m, z0.s, z1.s\n\t"
            "fmopa za1.s, p0/m, p0/m, z0.s, z1.s\n\t"
            "fmla z12.s, p0/m, z0.s, z1.s\n\t"
            "fmla z13.s, p0/m, z0.s, z1.s\n\t"
            "fmla z14.s, p0/m, z0.s, z1.s\n\t"
            "fmla z15.s, p0/m, z0.s, z1.s\n\t"
            "fmopa za2.s, p0/m, p0/m, z0.s, z1.s\n\t"
            "fmla z16.s, p0/m, z0.s, z1.s\n\t"
            "fmla z17.s, p0/m, z0.s, z1.s\n\t"
            "fmla z18.s, p0/m, z0.s, z1.s\n\t"
            "fmla z19.s, p0/m, z0.s, z1.s\n\t"
            "fmopa za3.s, p0/m, p0/m, z0.s, z1.s\n\t"
            "fmla z20.s, p0/m, z0.s, z1.s\n\t"
            "fmla z21.s, p0/m, z0.s, z1.s\n\t"
            "fmla z22.s, p0/m, z0.s, z1.s\n\t"
            "fmla z23.s, p0/m, z0.s, z1.s\n\t"
            "subs %[n], %[n], #1\n\t b.ne 1b\n\t"
            : [n] "+r"(n) : : "memory", "cc", "z8","z9","z10","z11","z12","z13","z14","z15","z16","z17","z18","z19","z20","z21","z22","z23");
        elapsed[tid]=cyc()-t0;
        sme_stop();
    }
    uint64_t max=0;
    for(int t=0;t<nth;t++) if(elapsed[t]>max) max=elapsed[t];
    double seconds=(double)max/cyc_hz();
    double gflops=(8*512.0+nf*32.0)*iterations*nth/seconds*1e-9;
    printf("PEAK nf=%d threads=%d tick_hz=%llu max_ms=%.3f gflops=%.1f\n",nf,nth,(unsigned long long)cyc_hz(),seconds*1000,gflops);
    return gflops;
}
int main(void)
{
    double peak=0;
    for(int r=0;r<3;r++) for(int nf=0;nf<=32;nf=nf?nf*2:8) {
        double g=v55_peak(nf); if(nf==0 && g>peak) peak=g;
    }
    read_knobs();
    int khs[]={39,41,55,81};
    for(int i=0;i<4;i++) {
        long kh=khs[i],kw=kh; rgrp_t G[12]; int ng=roll_groups(kh,kw,G);
        double cost=0;
        for(int g=0;g<ng;g++) cost+=(double)(G[g].kind==4?kw+3:G[g].steps)/G[g].width;
        printf("OPA_MODEL kh=%ld kw=%ld optimistic_gflops=%.1f excl_warmup_pack_transfer_output_scheduling\n",kh,kw,peak*kh*kw/(1024*cost));
    }
    return 0;
}
