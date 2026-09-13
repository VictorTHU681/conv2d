// Generalized coverage of the structural three-fold dispatcher and COPY4 span.
#define main original_test_main
#include "test_conv.c"
#undef main
int main(void)
{
    int ok = 1, count = 0;
    const int widths[] = {3,4,16,17,40,41,80,81,127,128,399,400};
    for (int kh = 39; kh <= 231; kh += 32) {
        for (unsigned i = 0; i < sizeof(widths)/sizeof(widths[0]); i++) {
            int kw = widths[i], ow = i % 2 ? 257 : 513;
            ok &= run_case(kh + 4, kw + ow - 1, kh, kw, 56601 + count, 0);
            count++;
        }
        for (int j = 0; j < 2; j++) {
            int kw = 7 + 10*j;
            ok &= run_case(kh + 8*kh + 3, kw + 272, kh, kw, 56701 + count, 1);
            count++;
        }
    }
    printf("FOLD_SELECT %s cases=%d\n", ok ? "PASS" : "FAIL", count);
    return ok ? 0 : 1;
}
