#include <assert.h>
#include <stdio.h>
static inline long roll_phase_sub(long a, long b, long kh)
{
    long d=a-b; return d<0 ? d+kh : d;
}

static long norm(long x,long kh) { return (x%kh+kh)%kh; }
int main(void) {
    unsigned long cases=0;
    for(long kh=16;kh<=256;kh++) for(long j=0;j<kh;j++) for(long s=0;s<kh;s++) {
        for(long q=0;q<4;q++) {
            long ja=j+(q==3?65537:q)*kh;
            long jp=ja%kh,ya=roll_phase_sub(jp,s,kh),yb=ya>=16?ya-16:ya+kh-16;
            long ca=ya+1==kh?0:ya+1,cb=yb+1==kh?0:yb+1;
            assert(ya==norm(ja-s,kh)); assert(yb==norm(ja-s-16,kh));
            assert(ca==norm(ja+1-s,kh)); assert(cb==norm(ja+1-s-16,kh));
            assert(roll_phase_sub(j,s,kh)==norm(j-s,kh));
            assert(roll_phase_sub(jp,kh-3,kh)==norm(ja-(kh-3),kh));
            assert(roll_phase_sub(jp,kh-2,kh)==norm(ja-(kh-2),kh));
            cases++;
        }
    }
    printf("PHASE_EQUIVALENCE PASS cases=%lu KH=16..256 all_normalized_phases=1 row_quotients=0,1,2,65537\n",cases);
}
