// Steady-allocation PMU diagnostic. Not the official timing/allocation protocol.
#include <stdio.h>
#include <stdlib.h>
#include <omp.h>

void conv2d(const float*, int, int, const float*, int, int, float*);

int main(int argc, char** argv)
{
    if (argc != 6) return 2;
    int H=atoi(argv[1]), W=atoi(argv[2]), KH=atoi(argv[3]), KW=atoi(argv[4]);
    int runs=atoi(argv[5]);
    if (H<KH || W<KW || KH<1 || KW<1 || runs<1) return 2;
    size_t ni=(size_t)H*W, nk=(size_t)KH*KW;
    size_t no=(size_t)(H-KH+1)*(W-KW+1);
    float* input=malloc(ni*sizeof(float));
    float* kernel=malloc(nk*sizeof(float));
    float* output=malloc(no*sizeof(float));
    if (!input || !kernel || !output) return 3;
    #pragma omp parallel for
    for (size_t i=0;i<ni;i++) input[i]=(float)((int)((i*37+19)%257)-128)/256;
    #pragma omp parallel for
    for (size_t i=0;i<nk;i++) kernel[i]=(float)((int)((i*43+11)%257)-128)/256;
    #pragma omp parallel for
    for (size_t i=0;i<no;i++) output[i]=0;
    for (int r=0;r<2;r++) conv2d(input,H,W,kernel,KH,KW,output);
    double start=omp_get_wtime();
    for (int r=0;r<runs;r++) conv2d(input,H,W,kernel,KH,KW,output);
    double ms=(omp_get_wtime()-start)*1000/runs;
    printf("STEADY_DIAGNOSTIC kh=%d runs=%d mean_ms=%.4f sample=%g\n",KH,runs,ms,output[0]);
    free(input); free(kernel); free(output);
    return 0;
}
