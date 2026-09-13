// Diagnostic only. Every syscall runs outside streaming mode.
#include <linux/perf_event.h>
#include <sys/syscall.h>
#include <sys/ioctl.h>
#include <errno.h>

typedef struct { uint64_t nr, enabled, running; struct { uint64_t value, id; } value[2]; } diag_pmu_read_t;
typedef struct { uint64_t cycles, instructions, enabled_ns, running_ns, ticks; } __attribute__((aligned(64))) diag_pmu_record_t;
static diag_pmu_record_t diag_pmu_records[1024];
static __thread struct {
    int initialized, fd[2];
    uint64_t id[2], enabled0, running0, tick0;
} diag_pmu_tls;
static void diag_pmu_error(const char* where) {
    fprintf(stderr,"PMU_ERROR where=%s errno=%d\n",where,errno);
    exit(3);
}
static void diag_pmu_read(diag_pmu_read_t* r) {
    ssize_t n=read(diag_pmu_tls.fd[0],r,sizeof(*r));
    if(n!=(ssize_t)sizeof(*r) || r->nr!=2) diag_pmu_error("group_read");
}
static __attribute__((noinline)) void diag_pmu_begin(void) {
    if(!g_diag_pmu_enabled) return;
    if(!diag_pmu_tls.initialized) {
        const uint64_t event[2]={PERF_COUNT_HW_CPU_CYCLES,PERF_COUNT_HW_INSTRUCTIONS};
        for(int i=0;i<2;i++) {
            struct perf_event_attr a;memset(&a,0,sizeof(a));
            a.type=PERF_TYPE_HARDWARE;a.size=sizeof(a);a.config=event[i];
            a.disabled=1;a.exclude_kernel=1;a.exclude_hv=1;
            a.read_format=PERF_FORMAT_GROUP|PERF_FORMAT_ID|PERF_FORMAT_TOTAL_TIME_ENABLED|PERF_FORMAT_TOTAL_TIME_RUNNING;
            int fd=(int)syscall(__NR_perf_event_open,&a,0,-1,i?diag_pmu_tls.fd[0]:-1,PERF_FLAG_FD_CLOEXEC);
            if(fd<0) diag_pmu_error("open");
            diag_pmu_tls.fd[i]=fd;
            if(ioctl(fd,PERF_EVENT_IOC_ID,&diag_pmu_tls.id[i])) diag_pmu_error("id");
        }
        diag_pmu_tls.initialized=1;
    }
    if(ioctl(diag_pmu_tls.fd[0],PERF_EVENT_IOC_RESET,PERF_IOC_FLAG_GROUP)) diag_pmu_error("reset");
    // RESET does not reset enabled/running time. Read their previous totals.
    diag_pmu_read_t before;diag_pmu_read(&before);
    diag_pmu_tls.enabled0=before.enabled;diag_pmu_tls.running0=before.running;
    if(ioctl(diag_pmu_tls.fd[0],PERF_EVENT_IOC_ENABLE,PERF_IOC_FLAG_GROUP)) diag_pmu_error("enable");
    diag_pmu_tls.tick0=cyc();
}
static __attribute__((noinline)) void diag_pmu_end(int tid) {
    if(!g_diag_pmu_enabled) return;
    uint64_t end=cyc();
    if(ioctl(diag_pmu_tls.fd[0],PERF_EVENT_IOC_DISABLE,PERF_IOC_FLAG_GROUP)) diag_pmu_error("disable");
    diag_pmu_read_t after;diag_pmu_read(&after);
    diag_pmu_record_t* d=&diag_pmu_records[tid];
    int found=0;
    for(int j=0;j<2;j++) {
        if(after.value[j].id==diag_pmu_tls.id[0]) {d->cycles=after.value[j].value;found|=1;}
        else if(after.value[j].id==diag_pmu_tls.id[1]) {d->instructions=after.value[j].value;found|=2;}
        else diag_pmu_error("unknown_id");
    }
    if(found!=3 || after.enabled<diag_pmu_tls.enabled0 || after.running<diag_pmu_tls.running0) diag_pmu_error("counter_order");
    d->enabled_ns=after.enabled-diag_pmu_tls.enabled0;
    d->running_ns=after.running-diag_pmu_tls.running0;
    d->ticks=end-diag_pmu_tls.tick0;
}
