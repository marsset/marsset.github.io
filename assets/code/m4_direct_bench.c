#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/time.h>
#include <pthread.h>
#include <string.h>

#define FILE_SIZE  (4ULL * 1024 * 1024 * 1024) // 4 GB test dataset
#define BLOCK_SIZE (128 * 1024)                // 128 KB aligned blocks
#define FILE_PATH  "/tmp/test_m4_bench.bin"

static inline double get_time_sec(void) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return tv.tv_sec + tv.tv_usec * 1e-6;
}

typedef struct {
    int    fd;
    size_t offset;
    size_t bytes;
} WorkerArg;

void *worker_thread(void *arg) {
    WorkerArg *w = (WorkerArg *)arg;
    void *buf = NULL;
    // 1. Mandatory 4KB physical page alignment for Direct DMA
    posix_memalign(&buf, 4096, BLOCK_SIZE);

    size_t done = 0;
    while (done < w->bytes) {
        ssize_t n = pread(w->fd, buf, BLOCK_SIZE, w->offset + done);
        if (n <= 0) break;
        done += n;
    }
    free(buf);
    return NULL;
}

void bench_unbuffered(int qd) {
    int fd = open(FILE_PATH, O_RDONLY);
    if (fd < 0) { perror("open"); exit(1); }

    // 2. Bypass OS Unified Memory cache (macOS equivalent of Linux O_DIRECT)
    fcntl(fd, F_GLOBAL_NOCACHE, 1);
    fcntl(fd, F_NOCACHE, 1);

    double t0 = get_time_sec();

    if (qd == 1) {
        // Synchronous unbuffered execution (Enforced QD = 1)
        void *buf = NULL;
        posix_memalign(&buf, 4096, BLOCK_SIZE);
        size_t done = 0;
        while (done < FILE_SIZE) {
            ssize_t n = read(fd, buf, BLOCK_SIZE);
            if (n <= 0) break;
            done += n;
        }
        free(buf);
    } else {
        // Pipelined unbuffered execution (Hardware Queue Depth = qd)
        pthread_t th[qd];
        WorkerArg args[qd];
        size_t per_th = FILE_SIZE / qd;

        for (int i = 0; i < qd; i++) {
            args[i].fd     = fd;
            args[i].offset = i * per_th;
            args[i].bytes  = per_th;
            pthread_create(&th[i], NULL, worker_thread, &args[i]);
        }
        for (int i = 0; i < qd; i++) pthread_join(th[i], NULL);
    }

    double elapsed = get_time_sec() - t0;
    double gb = (double)FILE_SIZE / (1024.0 * 1024.0 * 1024.0);
    double gbps = gb / elapsed;

    printf("M4 Pro SSD | QD = %2d | Time: %5.2f s | Bandwidth: %5.2f GB/s (%6.1f MB/s)\n",
           qd, elapsed, gbps, gbps * 1024.0);
    close(fd);
}

int main(int argc, char **argv) {
    int qds[] = {1, 2, 4, 8, 16, 32};
    printf("[Benchmark] Running Apple Silicon Direct I/O Reads (128 KB blocks)...\n");
    for (int i = 0; i < 6; i++) {
        bench_unbuffered(qds[i]);
    }
    return 0;
}
