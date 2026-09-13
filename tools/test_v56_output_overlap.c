// The diagnostic tracks live kernel write regions; it does not time performance.
#define main original_test_main
#include "test_conv.c"
#undef main
void conv_output_audit_report(unsigned long*,unsigned long*);
int main(void) {
    const int khs[]={39,41,55,81,113,145};
    const int widths[]={257,273,513};
    int ok=1,cases=0;
    for(int r=0;r<3;r++) for(int g=0;g<6;g++) for(int w=0;w<3;w++) {
        int KH=khs[g],KW=3+r*7,OH=33+r*251,OW=widths[w];
        ok &= run_case(OH+KH-1,OW+KW-1,KH,KW,56901+cases,0); cases++;
    }
    unsigned long calls,conflicts;
    conv_output_audit_report(&calls,&conflicts);
    int positive=getenv("EXPECT_OUTPUT_OVERLAP")!=NULL;
    ok &= calls>0 && (positive?conflicts>0:conflicts==0);
    printf("OUTPUT_OVERLAP %s cases=%d calls=%lu active_conflicts=%lu positive_control=%d\n",
           ok?"PASS":"FAIL",cases,calls,conflicts,positive);
    return ok?0:1;
}
