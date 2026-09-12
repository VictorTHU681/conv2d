// Official-style allocations from drv.c; perf is enabled only around measured
// conv2d calls. Reported wall times include control overhead: profiling only.
#include <fcntl.h>
#include <poll.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

void conv2d(const float*, int, int, const float*, int, int, float*);
static void perf_command(const char* command)
{
    static int ctl = -1, ack = -1;
    if (ctl < 0) {
        const char* c = getenv("V54_PERF_CTL");
        const char* a = getenv("V54_PERF_ACK");
        if (!c || !a) { fprintf(stderr, "Missing perf control FIFO paths\n"); exit(3); }
        ctl = open(c, O_WRONLY); ack = open(a, O_RDONLY);
        if (ctl < 0 || ack < 0) { perror("perf FIFO"); exit(3); }
    }
    size_t n = strlen(command);
    if (write(ctl, command, n) != (ssize_t)n) { perror("perf command"); exit(3); }
    struct pollfd p = {.fd=ack, .events=POLLIN};
    if (poll(&p, 1, 10000) <= 0) { fprintf(stderr, "perf acknowledgement timeout\n"); exit(3); }
    char reply[64];
    if (read(ack, reply, sizeof(reply)) <= 0) { perror("perf ack"); exit(3); }
}
static void measured_conv(const float* in, int H, int W, const float* k, int KH, int KW, float* out)
{
    static int calls;
    int measured = ++calls > 2;
    if (measured) perf_command("enable\n");
    conv2d(in, H, W, k, KH, KW, out);
    if (measured) perf_command("disable\n");
}
#define conv2d measured_conv
#include "drv.c"
