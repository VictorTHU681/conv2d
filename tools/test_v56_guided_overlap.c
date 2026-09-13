// Diagnostic-only: ensure long K5 pieces really use both chunk sizes.
#define main original_test_main
#include "test_conv.c"
#undef main
void conv_output_audit_report(unsigned long*, unsigned long*);
void conv_guided_audit_report(unsigned long*, unsigned long*);
int main(void) {
    const int heights[]={41,57,249}, widths[]={193,257};
    int ok=1,cases=0;
    for(int r=0;r<2;r++) for(int k=0;k<3;k++) for(int w=0;w<2;w++) {
        int kh=heights[k],kw=3+2*r,oh=4099+14*r,ow=widths[w];
        ok &= run_case(oh+kh-1,ow+kw-1,kh,kw,57101+cases,1);
        cases++;
    }
    unsigned long calls,conflicts,large,small;
    conv_output_audit_report(&calls,&conflicts);
    conv_guided_audit_report(&large,&small);
    ok &= calls>0 && conflicts==0 && large>0 && small>0;
    printf("GUIDED_OVERLAP %s cases=%d calls=%lu large=%lu small=%lu active_conflicts=%lu\n",
           ok?"PASS":"FAIL",cases,calls,large,small,conflicts);
    return ok?0:1;
}
