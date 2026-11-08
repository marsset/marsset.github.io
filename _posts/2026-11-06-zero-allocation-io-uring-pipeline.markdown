---
title:  "Zero-Allocation io_uring"
date:  2026-11-06 11:30:00 +0800
categories:
  - system
tags: system linux kernel io-uring memory-management concurrency
excerpt: >
  a production engineering blueprint for line-rate direct i/o: designing 4kb-aligned user-space buffer pools, pre-pinning fixed memory to bypass get_user_pages(), and coordinating io_uring with lockless spsc ring queues for 100% compute/i/o overlap.
---

In high-throughput storage engines—such as quantitative market data replay systems, columnar Parquet/ORC readers, or LSM-tree compaction pipelines—achieving multi-gigabyte line-rate ingestion requires [**bypassing the Linux Page Cache**]({% post_url 2026-11-05-page-cache-thrashing %}) via `O_DIRECT` to prevent catastrophic direct reclaim storms. 

This post dissects why traditional `read()` fundamentally fails under Direct I/O, and presents a complete, production-grade C++ architecture: pairing **Linux `io_uring`** with a **pre-pinned 4KB-aligned memory arena** and **lockless Single-Producer Single-Consumer (SPSC) ring queues** to achieve zero heap allocation on the hot path and 100% overlap between NVMe DMA and CPU compute.

---

## 1. Why read() Fundamentally Fails with O_DIRECT

When developers transition from cached I/O to Direct I/O, they often assume they can simply add the `O_DIRECT` flag to their existing synchronous `read()` loop:

```c
int fd = open("market_ticks.bin", O_RDONLY | O_DIRECT);
char *buf = (char *)malloc(128 * 1024);
ssize_t n = read(fd, buf, 128 * 1024);
```

In production, this naive pattern collapses under three compounding failure modes:

### 1.1 The Serialization Trap (Zero Compute Overlap)
In cached I/O, `read()` returns almost instantaneously if the data resides in the Page Cache. With `O_DIRECT`, the kernel bypasses the Page Cache entirely:
1. The calling thread traps into the kernel and issues an NVMe command.
2. The thread enters an uninterruptible sleep state (`TASK_UNINTERRUPTIBLE`, state `D` in `ps`).
3. The NVMe controller transfers data across PCIe lanes into host RAM via Direct Memory Access (DMA).
4. A hardware interrupt fires, waking the thread to return to user space.
5. The thread finally executes compute (decompression, parsing, filtering).

```
Timeline (Serialized read() Execution):
CPU:  [   Idle Wait (0%)   ] [ Compute Chunk 0 ] [   Idle Wait (0%)   ] [ Compute Chunk 1 ]
NVMe: [ DMA Chunk 0 Transf ] [  Idle Disk (0%) ] [ DMA Chunk 1 Transf ] [  Idle Disk (0%) ]
```

While the NVMe controller transfers data, the CPU sits completely idle. While the CPU decompresses data, the NVMe controller has zero requests in flight ($\text{Queue Depth} = 0$). 

The total elapsed time is strictly additive:
$$T_{\text{total}} = T_{\text{DMA}} + T_{\text{Compute}}$$
Both the storage hardware and the CPU cores operate at barely $50\%$ physical utilization.

### 1.2 The Alignment Trap (Why malloc() Aborts with -EINVAL)
In the snippet above, `read()` does not just run slowly—**it immediately fails, returning `-1` with `errno = EINVAL` (Invalid argument)**.

Under cached I/O, the disk controller transfers data into kernel-owned page cache frames, and the kernel subsequently executes a CPU `memcpy` into user space. CPU memory copies tolerate arbitrary byte alignment.

Under `O_DIRECT`, however, the kernel steps aside completely. The physical PCIe DMA controller transfers data directly between the SSD flash buffers and your user-space memory pointer. Because hardware DMA burst engines operate on memory bus transaction boundaries, the kernel enforces **three strict physical alignment rules**:
1. **Buffer Pointer Alignment:** `(uintptr_t)buf % 4096 == 0` (virtual address must align to a 4KB page/sector boundary).
2. **File Offset Alignment:** `offset % 4096 == 0` (cannot start reading from an arbitrary byte offset).
3. **Transfer Length Alignment:** `length % 4096 == 0` (must read in whole sector/page multiples).

Standard `malloc()` or `new` only guarantees 8-byte or 16-byte alignment (sufficient for standard scalar types and SIMD registers, but virtually never 4096-byte page boundaries). Passing a pointer like `0x...1010` causes the kernel's Direct I/O sanity check to instantly abort with `-EINVAL`.

### 1.3 The Stateless Page-Pinning Tax (get_user_pages Overhead)
Even if you manually align the buffer, synchronous `read()` suffers from a hidden, severe microarchitectural penalty: **stateless page table walks**.

Because NVMe DMA controllers operate on physical bus addresses (`dma_addr_t`), the kernel must translate the user virtual address `buf` into physical memory frames. Furthermore, the kernel must ensure the operating system does not swap out or remap those physical frames while the PCIe DMA transaction is active.

Because POSIX `read()` is completely stateless, the kernel has no memory of previous calls. On **every single `read()` invocation**, the kernel must execute **`get_user_pages()` (GUP)**:
1. Traverses the calling process's 4-level MMU page table: $\text{PGD} \to \text{PUD} \to \text{PMD} \to \text{PTE}$.
2. Atomically increments the reference counter on every physical page: `page_ref_inc(page)`.
3. Programs the physical Scatter-Gather List (SGL / PRP) into the NVMe controller.
4. Upon DMA completion interrupt, traverses the pages again to atomically decrement reference counts: `put_page(page)`.

At $5\text{ GB/s}$ wire speed with $128\text{ KB}$ chunks, the application issues over **$40,000\text{ IOPS}$**. This forces the kernel to execute over **$1,280,000$ atomic reference-count operations per second**, triggering catastrophic CPU cacheline bouncing (false sharing on `struct page->_refcount`) across cores and burning up to $25\%$ of total CPU cycles.

Crucially, **POSIX `read()` has no API mechanism to register memory upfront**. It is doomed to pay this page-table walk tax on every single read.

---

## 2. Memory Arena Engineering: 4KB Alignment & Stateful Buffer Pools

To eliminate both the `-EINVAL` alignment failure and the `get_user_pages()` overhead, we must transform user-space memory from an ad-hoc dynamic heap into a **pre-pinned, stateful memory arena**.

### 2.1 The Three Allocation Strategies

| Allocation Interface | Alignment Mechanism | TLB Pressure | Production Evaluation |
| :--- | :--- | :--- | :--- |
| **`posix_memalign()` / C11 `aligned_alloc()`** | Explicitly requests 4096-byte chunk from glibc | High (standard 4KB PTEs) | Suitable for isolated test harnesses |
| **Anonymous `mmap()`** | **Naturally page-aligned by the OS kernel** | Standard (4KB PTEs) | **Recommended for production multi-megabyte arenas** |
| **HugeTLB `mmap(MAP_HUGETLB)`** | Naturally 2MB or 1GB aligned | **Zero TLB thrashing** | **Optimal for line-rate 5+ GB/s streaming engines** |

#### Why Anonymous mmap() is the Production Standard
Rather than requesting aligned chunks from the glibc heap manager, production engines allocate the entire buffer arena via anonymous `mmap()`:
```cpp
void* arena = mmap(nullptr, total_pool_size,
                   PROT_READ | PROT_WRITE,
                   MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
mlock(arena, total_pool_size); // Lock pages in RAM, prevent swapping
```
Because the Linux virtual memory subsystem manages memory in pages, **any memory region returned by `mmap()` is mathematically guaranteed to start on a 4096-byte boundary**.

For ultra-high-throughput engines scanning terabytes of historical data at $5\text{ to }7\text{ GB/s}$, allocating via `MAP_HUGETLB` (2MB HugePages) reduces page table entries by a factor of $512$, virtually eliminating CPU Translation Lookaside Buffer (TLB) misses.

### 2.2 Eliminating get_user_pages() via io_uring Fixed Buffers
`io_uring` introduces the concept of **stateful buffer registration**:

```cpp
// 1. One-time startup registration (Slow Path)
struct iovec iov[POOL_SLOTS];
for (size_t i = 0; i < POOL_SLOTS; i++) {
    iov[i].iov_base = static_cast<char*>(arena) + (i * CHUNK_SIZE);
    iov[i].iov_len  = CHUNK_SIZE;
}
io_uring_register_buffers(&ring, iov, POOL_SLOTS);

// 2. High-speed streaming loop (Fast Path)
io_uring_prep_read_fixed(sqe, fd, buf, CHUNK_SIZE, file_offset, slot_idx);
```

During initialization, `io_uring_register_buffers()` walks the page table and pins all physical frames **once**. 

During the streaming loop, `io_uring_prep_read_fixed()` passes only the integer `slot_idx`. The kernel resolves physical bus addresses via an internal pre-pinned lookup table:
* **Zero page table walks.**
* **Zero calls to `get_user_pages()`.**
* **Zero atomic refcount increments or decrements (zero cacheline bouncing).**

---

## 3. The Architectural Blueprint: Decoupled Dual-Thread Pipeline

To completely eliminate the serialization bottleneck and overlap physical I/O with vector compute (e.g. Gorilla decompression, bit-unpacking, or parquet decoding), we separate duties between two dedicated threads communicating exclusively via **32-bit slot indices**:

```
+==================================================================================================+
|                                    ZERO-ALLOCATION PIPELINE                                      |
+==================================================================================================+
                                        ┌───────────────┐
                                        │  free_slots   │ ◄──────────────────────┐
                                        │ (SPSC Queue)  │                        │
                                        └───────┬───────┘                        │
                                                │ Pop slot_idx                   │
                                                ▼                                │
  ┌───────────────┐       SQE Read Fixed ┌───────────────┐                       │
  │   NVMe SSD    │ ◄─────────────────── │  I/O Thread   │                       │
  │  (PCIe DMA)   │ ───────────────────► │  (Submitter / │                       │
  └───────────────┘       CQE Harvest    │   Harvester)  │                       │
                                         └───────┬───────┘                       │
                                                 │ Push slot_idx                 │
                                                 ▼                               │
                                        ┌───────────────┐                        │
                                        │  ready_slots  │                        │
                                        │ (SPSC Queue)  │                        │
                                        └───────┬───────┘                        │
                                                │ Pop slot_idx                   │
                                                ▼                                │
                                         ┌───────────────┐    Recycle slot_idx   │
                                         │Compute Thread │ ──────────────────────┘
                                         │ (SIMD/Decode) │
                                         └───────────────┘
```

### The Pipeline Timeline:
* **Synchronous Serial Model:**
  $$T_{\text{total}} = \sum_{i=1}^M \left( T_{\text{DMA}}(i) + T_{\text{Compute}}(i) \right)$$
* **Pipelined Asynchronous Model (Compute Overlap):**
  $$T_{\text{total}} \approx \max\left( \sum_{i=1}^M T_{\text{DMA}}(i), \; \sum_{i=1}^M T_{\text{Compute}}(i) \right) + T_{\text{drain}}$$

When $T_{\text{Compute}} \le T_{\text{DMA}}$, the pipeline runs at **$100\%$ NVMe wire speed**—the compute time is completely hidden inside the DMA window. When $T_{\text{DMA}} \le T_{\text{Compute}}$, the pipeline runs at **$100\%$ CPU vector compute saturation** without ever stalling for disk reads.

---

## 4. Lockless SPSC Ring Queue: Zero False Sharing

To coordinate between the I/O thread and the Compute thread without mutex contention or heap allocations, we implement a lock-free Single-Producer Single-Consumer (SPSC) circular ring.

### Cacheline False Sharing Protection
In multi-threaded x86-64 and ARM64 architectures, adjacent variables located within the same 64-byte cacheline trigger **false sharing**. If Thread A modifies `tail_` while Thread B modifies `head_`, the CPU cache coherency protocol (MESI) constantly invalidates the cacheline between L1/L2 caches, stalling execution.

We strictly isolate `head_`, `tail_`, and the ring storage across distinct 64-byte boundaries using `alignas(64)`.

```cpp
#include <atomic>
#include <cstdint>
#include <cstddef>
#include <new>

constexpr size_t CACHELINE_BYTES = 64;

template <typename T, size_t Capacity>
class alignas(CACHELINE_BYTES) SPSCRingQueue {
    static_assert((Capacity & (Capacity - 1)) == 0, "Capacity must be power of 2");

public:
    SPSCRingQueue() : head_(0), tail_(0) {}

    // Producer API: Push item into queue
    bool push(T val) noexcept {
        const size_t current_tail = tail_.load(std::memory_order_relaxed);
        // Acquire barrier ensures we see the consumer's latest head update
        if (current_tail - head_.load(std::memory_order_acquire) == Capacity) {
            return false; // Queue is full
        }
        buffer_[current_tail & (Capacity - 1)] = val;
        // Release barrier ensures buffer entry write is globally visible
        tail_.store(current_tail + 1, std::memory_order_release);
        return true;
    }

    // Consumer API: Pop item from queue
    bool pop(T &val) noexcept {
        const size_t current_head = head_.load(std::memory_order_relaxed);
        // Acquire barrier ensures we see the producer's latest tail update
        if (current_head == tail_.load(std::memory_order_acquire)) {
            return false; // Queue is empty
        }
        val = buffer_[current_head & (Capacity - 1)];
        // Release barrier ensures slot consumption is globally visible
        head_.store(current_head + 1, std::memory_order_release);
        return true;
    }

private:
    // Slot buffer storage
    T buffer_[Capacity];

    // Align head and tail to distinct cachelines to prevent False Sharing
    alignas(CACHELINE_BYTES) std::atomic<size_t> head_;
    alignas(CACHELINE_BYTES) std::atomic<size_t> tail_;
};
```

---

## 5. Complete Production Implementation

Below is the complete, self-contained implementation of the dual-thread zero-allocation pipeline. 

It reads an unbuffered Direct I/O dataset at physical wire speed while streaming chunks directly into user-space vector compute:

```cpp
#define _GNU_SOURCE
#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/time.h>
#include <liburing.h>
#include <thread>
#include <atomic>
#include <vector>

#if defined(__x86_64__)
#include <immintrin.h>
#define CPU_PAUSE() _mm_pause()
#elif defined(__aarch64__)
#define CPU_PAUSE() asm volatile("yield")
#else
#define CPU_PAUSE() ((void)0)
#endif

// -----------------------------------------------------------------------------
// Architecture Sizing Constants
// -----------------------------------------------------------------------------
constexpr size_t CHUNK_SIZE = 128 * 1024; // 128 KB chunks
constexpr size_t QD         = 16;         // Hardware Queue Depth
constexpr size_t POOL_SLOTS = 32;         // 2x QD buffer capacity (power of 2)
constexpr size_t TOTAL_POOL = CHUNK_SIZE * POOL_SLOTS; // 4 MB memory pool

// Two lockless ring queues transferring 32-bit slot indices only
static SPSCRingQueue<uint32_t, POOL_SLOTS> free_slots;
static SPSCRingQueue<uint32_t, POOL_SLOTS> ready_slots;
static std::atomic<bool> io_finished{false};

// -----------------------------------------------------------------------------
// Vector Compute Kernel Placeholder (Zero-Allocation)
// -----------------------------------------------------------------------------
static inline void process_compute_chunk(const char *data, size_t len) {
    // In production, execute SIMD Gorilla parsing, Bitset scanning, or Parquet decode.
    // Memory access occurs strictly within L2/L3 cache without heap allocations.
    uint64_t checksum = 0;
    const auto *words = reinterpret_cast<const uint64_t *>(data);
    size_t count = len / sizeof(uint64_t);
    for (size_t i = 0; i < count; i += 8) {
        checksum ^= words[i];
    }
    asm volatile("" : : "r"(checksum) : "memory");
}

// -----------------------------------------------------------------------------
// I/O Producer Thread: Submits SQEs and Reaps CQEs
// -----------------------------------------------------------------------------
void io_thread_func(int fd, size_t file_size, struct io_uring *ring, char *arena_base) {
    size_t submitted_offset = 0;
    size_t completed_bytes  = 0;
    size_t in_flight        = 0;

    while (completed_bytes < file_size) {
        // 1. Maintain Target Queue Depth: Dispatch new reads into SQ
        uint32_t slot_idx;
        while (in_flight < QD && submitted_offset < file_size && free_slots.pop(slot_idx)) {
            struct io_uring_sqe *sqe = io_uring_get_sqe(ring);
            
            size_t bytes_to_read = CHUNK_SIZE;
            if (submitted_offset + bytes_to_read > file_size) {
                bytes_to_read = file_size - submitted_offset;
            }

            // Fixed buffer read: zero page-table walks, zero GUP overhead
            io_uring_prep_read_fixed(sqe, fd,
                                     arena_base + (slot_idx * CHUNK_SIZE),
                                     bytes_to_read, submitted_offset,
                                     slot_idx);
            sqe->user_data = slot_idx;

            submitted_offset += bytes_to_read;
            in_flight++;
        }

        // 2. Submit queued SQEs in batch
        if (in_flight > 0) {
            io_uring_submit(ring);
        }

        // 3. Harvest completed DMA chunks non-blockingly
        struct io_uring_cqe *cqe;
        while (io_uring_peek_cqe(ring, &cqe) == 0) {
            uint32_t done_slot = static_cast<uint32_t>(cqe->user_data);
            if (cqe->res > 0) {
                completed_bytes += cqe->res;
            }
            io_uring_cqe_seen(ring, cqe);
            in_flight--;

            // Push ready slot to Compute Thread
            while (!ready_slots.push(done_slot)) {
                CPU_PAUSE();
            }
        }

        if (in_flight == 0 && submitted_offset >= file_size) {
            break;
        }
    }

    io_finished.store(true, std::memory_order_release);
}

// -----------------------------------------------------------------------------
// Compute Consumer Thread: Decompresses & Reclaims Slots
// -----------------------------------------------------------------------------
void compute_thread_func(size_t file_size, char *arena_base) {
    size_t processed_bytes = 0;

    while (processed_bytes < file_size) {
        uint32_t slot_idx;
        if (ready_slots.pop(slot_idx)) {
            const char *data_ptr = arena_base + (slot_idx * CHUNK_SIZE);
            
            // Execute in-place decode / scan
            process_compute_chunk(data_ptr, CHUNK_SIZE);
            processed_bytes += CHUNK_SIZE;

            // Recycle slot index back to I/O thread immediately
            while (!free_slots.push(slot_idx)) {
                CPU_PAUSE();
            }
        } else {
            if (io_finished.load(std::memory_order_acquire) && processed_bytes >= file_size) {
                break;
            }
            CPU_PAUSE();
        }
    }
}
```

---

## 6. Architectural & Microarchitectural Properties

### 6.1 CPU Cache Footprint: Permanent L3 Cache Residency
Because the entire memory arena is fixed at $N = 32$ slots of $128\text{ KB}$, the total buffer footprint is:
$$\text{Memory Footprint} = 32 \times 128\text{ KB} = 4\text{ MB}$$

On modern server architectures (e.g. AMD EPYC, Intel Xeon, AWS Graviton), L3 cache sizes range from $32\text{ MB}$ to over $256\text{ MB}$. 
* A 4 MB arena **permanently resides in L3 cache**.
* The 128 KB slot currently being consumed by the compute thread comfortably fits into modern L2 caches (typically $512\text{ KB}$ to $1\text{ MB}$ per core).
* Zero main memory (DRAM) allocation or deallocation occurs during the entire streaming session.

### 6.2 Lockless Contention Profile
* The I/O thread is the **sole producer** of `ready_slots` and the **sole consumer** of `free_slots`.
* The Compute thread is the **sole consumer** of `ready_slots` and the **sole producer** of `free_slots`.
* Because `head_` and `tail_` are strictly padded to separate 64-byte cache lines, there is **zero cacheline bouncing** across CPU cores. Inter-thread communication reduces to single-word atomic synchronization with release/acquire semantics.

---

## 7. Summary: Rules of Engagement for Line-Rate Pipelines

When designing direct-to-disk pipelines in latency-critical and high-throughput systems:

1. **Decouple I/O and Compute into SPSC Stages:** Never execute decompression or parsing inside the thread that harvests storage completion events. Use lockless SPSC queues transferring integer slot indices.
2. **Always Use Anonymous `mmap` with `mlock`:** Allocate 4KB-aligned buffer arenas upfront. Size the pool to $2 \times QD$ so neither the storage controller nor the compute thread ever starves.
3. **Register Buffers with `io_uring_register_buffers`:** Pin physical memory upfront. Eliminate the repetitive `get_user_pages()` page table traversal and reference count contention on the hot path.
4. **Pad Queue Pointers to 64-byte Boundaries:** Ensure that atomic head and tail pointers reside on distinct cachelines to eliminate false sharing.
