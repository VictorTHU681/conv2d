// malloc 128 MB 并触碰，读自己的 smaps_rollup 看实际拿到多少透明大页
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(void)
{
    size_t n = 128ul << 20;
    char* p = malloc(n);
    if (!p) { printf("malloc fail\n"); return 1; }
    memset(p, 1, n);
    FILE* f = fopen("/proc/self/smaps_rollup", "r");
    char line[256];
    while (f && fgets(line, sizeof line, f))
        if (strstr(line, "AnonHugePages") || strstr(line, "Rss:")) printf("thpprobe(128M touched): %s", line);
    if (f) fclose(f);
    __asm__ volatile("" :: "r"(p) : "memory");
    return 0;
}
