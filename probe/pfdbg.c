// pairf 定位：单形状全图比对，按 (j mod KH) 汇总错行
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <omp.h>
typedef float CONVFLOAT; typedef int CONVINT;
void conv2d(const CONVFLOAT*, CONVINT, CONVINT, const CONVFLOAT*, CONVINT, CONVINT, CONVFLOAT*);
static float rl(int* s){int h=*s/127773,l=*s%127773,t=16807*l-2836*h;*s=t+((t>0)?0:2147483647);return (float)*s/2147483647.0f;}
int main(int argc,char**argv){
    int H=atoi(argv[1]),W=atoi(argv[2]),KH=atoi(argv[3]),KW=atoi(argv[4]);
    int oh=H-KH+1,ow=W-KW+1;
    float*in=malloc((size_t)H*W*4),*k=malloc((size_t)KH*KW*4),*o=malloc((size_t)oh*ow*4),*r=malloc((size_t)oh*ow*4);
    int s=7; for(long i=0;i<(long)H*W;i++)in[i]=rl(&s); for(long i=0;i<(long)KH*KW;i++)k[i]=rl(&s);
    memset(r,0,(size_t)oh*ow*4);
    #pragma omp parallel for
    for(int j=0;j<oh;j++)for(int jk=0;jk<KH;jk++)for(int i=0;i<ow;i++)for(int ik=0;ik<KW;ik++)r[(long)j*ow+i]+= in[(long)(j+jk)*W+i+ik]*k[(long)jk*KW+ik];
    conv2d(in,H,W,k,KH,KW,o);
    long bad=0; static long badres[256]; long badcol_lo=1e9,badcol_hi=-1;
    for(int j=0;j<oh;j++)for(int i=0;i<ow;i++){ float a=o[(long)j*ow+i],b=r[(long)j*ow+i];
        if(fabsf(a-b)>1e-2f*fmaxf(1.f,fabsf(b))){bad++;badres[j%KH]++; if(i<badcol_lo)badcol_lo=i; if(i>badcol_hi)badcol_hi=i; if(bad<6)printf("  j=%d(res %d) i=%d got %.6g ref %.6g\n",j,j%KH,i,a,b);} }
    printf("bad=%ld/%ld  cols[%ld,%ld]\n",bad,(long)oh*ow,badcol_lo,badcol_hi);
    printf("residues with errors:"); for(int q=0;q<KH;q++) if(badres[q]) printf(" %d(%ld)",q,badres[q]); printf("\n");
    return 0;
}
