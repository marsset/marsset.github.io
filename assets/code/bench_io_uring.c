#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/time.h>
#include <liburing.h>
#include <string.h>

#define CHUNK_SIZE     (128 * 1024)           // 128 KB chunks
#define ALIGNMENT      4096                   // 4 KB page / sector alignment
#define FILE_SIZE      (512ULL * 1024 * 1024) // 512 MB test dataset

static inline double get_time_sec(void) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return tv.tv_sec + tv.tv_usec * 1e-6;
}

// 1. Synchronous Direct I/O Baseline (QD = 1)
void bench_sync_direct(const char *path) {
    int fd = open(path, O_RDONLY | O_DIRECT);
    if (fd < 0) { perror("open sync"); return; }

    void *buf = NULL;
    posix_memalign(&buf, ALIGNMENT, CHUNK_SIZE);

    double t0 = get_time_sec();
    size_t total_read = 0;
    while (total_read < FILE_SIZE) {
        ssize_t n = read(fd, buf, CHUNK_SIZE);
        if (n <= 0) break;
        total_read += n;
    }
    double t1 = get_time_sec();
    close(fd);
    free(buf);

    double elapsed = t1 - t0;
    double mb_s = (total_read / (1024.0 * 1024.0)) / elapsed;
    printf("[Sync read() (O_DIRECT QD=1)] %6.3f s | %5.1f MB/s (%4.2f GB/s)\n",
           elapsed, mb_s, mb_s / 1024.0);
}

// 2. Asynchronous io_uring Pipeline (Arbitrary QD & Fixed Buffers)
void bench_io_uring(const char *path, int qd, int use_fixed_bufs) {
    int fd = open(path, O_RDONLY | O_DIRECT);
    if (fd < 0) { perror("open uring"); return; }

    struct io_uring ring;
    if (io_uring_queue_init(qd * 2, &ring, 0) < 0) {
        perror("io_uring_queue_init");
        close(fd);
        return;
    }

    // Allocate 4KB-aligned buffer slots
    void **buffers = malloc(qd * sizeof(void *));
    struct iovec *iovecs = malloc(qd * sizeof(struct iovec));
    for (int i = 0; i < qd; i++) {
        posix_memalign(&buffers[i], ALIGNMENT, CHUNK_SIZE);
        iovecs[i].iov_base = buffers[i];
        iovecs[i].iov_len  = CHUNK_SIZE;
    }

    if (use_fixed_bufs) {
        if (io_uring_register_buffers(&ring, iovecs, qd) < 0) {
            perror("io_uring_register_buffers");
        }
    }

    double t0 = get_time_sec();
    size_t submitted_bytes = 0, completed_bytes = 0;
    int in_flight = 0;

    // Fill initial submission pipeline
    for (int i = 0; i < qd && submitted_bytes < FILE_SIZE; i++) {
        struct io_uring_sqe *sqe = io_uring_get_sqe(&ring);
        if (use_fixed_bufs) {
            io_uring_prep_read_fixed(sqe, fd, buffers[i], CHUNK_SIZE, submitted_bytes, i);
        } else {
            io_uring_prep_read(sqe, fd, buffers[i], CHUNK_SIZE, submitted_bytes);
        }
        sqe->user_data = i; // slot index
        submitted_bytes += CHUNK_SIZE;
        in_flight++;
    }
    io_uring_submit(&ring);

    // Event Loop: Reap completed chunks and immediately dispatch new ones
    while (completed_bytes < FILE_SIZE) {
        struct io_uring_cqe *cqe;
        int ret = io_uring_wait_cqe(&ring, &cqe);
        if (ret < 0) break;

        if (cqe->res > 0) {
            completed_bytes += cqe->res;
        }
        int slot = (int)cqe->user_data;
        io_uring_cqe_seen(&ring, cqe);
        in_flight--;

        if (submitted_bytes < FILE_SIZE) {
            struct io_uring_sqe *sqe = io_uring_get_sqe(&ring);
            if (sqe) {
                if (use_fixed_bufs) {
                    io_uring_prep_read_fixed(sqe, fd, buffers[slot], CHUNK_SIZE, submitted_bytes, slot);
                } else {
                    io_uring_prep_read(sqe, fd, buffers[slot], CHUNK_SIZE, submitted_bytes);
                }
                sqe->user_data = slot;
                submitted_bytes += CHUNK_SIZE;
                in_flight++;
                io_uring_submit(&ring);
            }
        }
    }

    double t1 = get_time_sec();
    io_uring_queue_exit(&ring);
    close(fd);
    for (int i = 0; i < qd; i++) free(buffers[i]);
    free(buffers);
    free(iovecs);

    double elapsed = t1 - t0;
    double mb_s = (completed_bytes / (1024.0 * 1024.0)) / elapsed;
    printf("[io_uring %s (QD=%2d)] %6.3f s | %5.1f MB/s (%4.2f GB/s)\n",
           use_fixed_bufs ? "Fixed Buffers" : "O_DIRECT     ",
           qd, elapsed, mb_s, mb_s / 1024.0);
}

int main(int argc, char **argv) {
    const char *path = (argc > 1) ? argv[1] : "test_uring.bin";
    printf("--- Direct I/O Baseline ---\n");
    bench_sync_direct(path);

    printf("\n--- io_uring Standard Direct I/O ---\n");
    int qds[] = {1, 4, 8, 16, 32};
    for (int i = 0; i < 5; i++) {
        bench_io_uring(path, qds[i], 0);
    }

    printf("\n--- io_uring Registered Fixed Buffers ---\n");
    bench_io_uring(path, 16, 1);
    bench_io_uring(path, 32, 1);

    return 0;
}
