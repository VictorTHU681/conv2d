// BR 方案调试：单个用例，按输出行 (j mod 4) 与列统计误差，定位是前半/后半/哪些 tile 出错
// gcc -O2 -march=armv9-a+sme+sve2 -fopenmp brdbg.c ../conv2d.c -o brdbg -lm
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
typedef float CONVFLOAT; typedef int CONVINT;
void conv2d(const CONVFLOAT*, CONVINT, CONVINT, const CONVFLOAT*, CONVINT, CONVINT, CONVFLOAT*);
static float lcg(int* s) { int hi = *s / 127773, lo = *s % 127773; int t = 16807 * lo - 2836 * hi; *s = t + (t > 0 ? 0 : 2147483647); return (float)*s / 2147483647.0f; }
int main(int argc, char** argv)
{
    int H = atoi(argv[1]), W = atoi(argv[2]), KH = atoi(argv[3]), KW = atoi(argv[4]);
    long oH = H - KH + 1, oW = W - KW + 1;
    float* in = malloc((size_t)H * W * 4); float* k = malloc((size_t)KH * KW * 4);
    float* o1 = calloc(oH * oW, 4); float* o2 = calloc(oH * oW, 4);
    int s = 777; for (long i = 0; i < (long)H * W; i++) in[i] = lcg(&s); for (long i = 0; i < KH * KW; i++) k[i] = lcg(&s);
    for (long j = 0; j < oH; j++) for (long i = 0; i < oW; i++) { float acc = 0; for (int y = 0; y < KH; y++) for (int x = 0; x < KW; x++) acc = fmaf(in[(j + y) * W + i + x], k[y * KW + x], acc); o1[j * oW + i] = acc; }
    conv2d(in, H, W, k, KH, KW, o2);
    long bad[4] = {0, 0, 0, 0}, tot[4] = {0, 0, 0, 0}; double mx[4] = {0, 0, 0, 0};
    for (long j = 0; j < oH; j++) for (long i = 0; i < oW; i++) { double e = fabs((double)o1[j * oW + i] - o2[j * oW + i]); int r = j & 3; tot[r]++; if (e > 1e-5) bad[r]++; if (e > mx[r]) mx[r] = e; }
    for (int r = 0; r < 4; r++) printf("row j%%4=%d (jc=%d): bad %ld/%ld maxerr %.3g\n", r, 3 - r, bad[r], tot[r], mx[r]);
    // 第一个坏输出行：按列段（64 列一段）统计
    for (long j = 0; j < oH && j < 8; j++) {
        printf("row %2ld:", j);
        for (long c0 = 0; c0 < oW; c0 += 64) { long b = 0; for (long i = c0; i < c0 + 64 && i < oW; i++) if (fabs((double)o1[j * oW + i] - o2[j * oW + i]) > 1e-5) b++; printf(" %2ld", b); }
        printf("\n");
    }
    // 打印 row 0 的前 8 个元素的 ref/got 差
    for (long j = 0; j < 4; j++) { printf("row %ld col0..3 diff:", j); for (long i = 0; i < 4; i++) printf(" %+.4g", (double)o2[j * oW + i] - o1[j * oW + i]); printf("\n"); }
    return 0;
}
