// Reuse the exact reference checker, with tall inputs and few workers so each
// worker holds several stripes and every candidate crosses block boundaries.
#define main original_test_main
#include "test_conv.c"
#undef main
int main(void)
{
    int shapes[][4] = {
        {1200, 640, 39, 39}, {1197, 650, 41, 41},
        {1255, 640, 55, 55}, {1300, 651, 81, 81},
        {1200, 640, 16, 17}, {1200, 640, 23, 25},
        {1200, 640, 71, 39}, {1300, 647, 129, 7},
    };
    int ok = 1;
    for (int i = 0; i < 8; i++)
        ok &= run_case(shapes[i][0], shapes[i][1], shapes[i][2], shapes[i][3], 54601+i, 1);
    puts(ok ? "CARRY_ALL_PASS" : "CARRY_FAIL");
    return ok ? 0 : 1;
}
