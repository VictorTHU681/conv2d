// Exercise every rolling kernel height, table sharing, and call-local state
// resets. Short outputs keep the full ordered reference affordable.
#define main original_test_main
#include "test_conv.c"
#undef main

int main(void)
{
    int ok = 1, count = 0;
    for (int kh = 16; kh <= 256; kh++) {
        int kw = 3 + (kh * 17 % 94);
        ok &= run_case(kh + 8, kw + 272, kh, kw, 55101 + kh, 0);
        count++;
    }
    // Repeated shape changes include enough input rows for state transfer;
    // each call changes both inputs and coefficients and overwrites output.
    const int khs[] = {39, 81, 55, 41, 113, 145, 177, 209, 241, 39};
    for (int round = 0; round < 2; round++) {
        for (unsigned i = 0; i < sizeof(khs)/sizeof(khs[0]); i++) {
            int kh = khs[i], kw = 7 + (int)i * 2;
            ok &= run_case(kh + 533 + round, kw + 560, kh, kw,
                           55401 + round * 100 + (int)i, 1);
            count++;
        }
    }
    printf("STATE_SWEEP %s cases=%d\n", ok ? "PASS" : "FAIL", count);
    return ok ? 0 : 1;
}
