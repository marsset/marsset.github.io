---
title:  "io_uring on Modern SSDs"
date:  2026-11-06 09:30:00 +0800
categories:
  - system
tags: system linux kernel io-uring nvme memory-management
excerpt: >
  a focused architectural deep dive into why modern nvme ssds require high queue depth to saturate, how io_uring's lockless shared rings achieve this inside a single thread, and empirical benchmarks on bare-metal flash vs. cloud storage.
---

When building high-throughput quantitative backtest engines, columnar data scanners, or low-latency time-series stores, engineers frequently reach for `O_DIRECT` to bypass the Linux Page Cache and prevent memory pressure from triggering [**Direct Reclaim Storms**]({% post_url 2026-11-05-page-cache-thrashing %}).

Yet, when you replace standard cached reads with a synchronous `read()` or `pread()` loop, sequential read throughput collapses to a fraction of the hardware's rated capacity—often delivering barely $1.0\text{ GB/s}$ on a drive rated for $5\text{ to }7\text{ GB/s}$.

The bottleneck is not the disk speed. It is a fundamental mismatch between **synchronous software execution** and the **massively parallel physics of solid-state storage**.

---

## 1. The Hardware Reality: Why SSDs Idle on Synchronous Reads

An NVMe SSD is not a single sequential tape. Internally, a modern SSD controller manages **8 to 16 parallel flash channels**, with each channel connected to multiple NAND flash dies:

```
                  ┌───────────────────────────────┐
                  │      NVMe Flash Controller     │
                  └────────┬─────────────┬────────┘
                           │             │
              ┌────────────┴───┐     ┌───┴────────────┐
              │ Flash Channel 0│ ... │Flash Channel 15│
              └──┬───────────┬─┘     └──┬───────────┬─┘
                 │           │          │           │
              ┌──┴───┐    ┌──┴───┐   ┌──┴───┐    ┌──┴───┐
              │Die 0 │    │Die 1 │   │Die 0 │    │Die 1 │
              └──────┘    └──────┘   └──────┘    └──────┘
```

When you read a block synchronously via `O_DIRECT`:

```c
ssize_t n = read(fd, buf, 128 * 1024); // 128 KB synchronous read
```

1. The calling thread traps into the kernel and issues a single NVMe command.
2. The calling thread enters an uninterruptible sleep state (`TASK_UNINTERRUPTIBLE`).
3. The NVMe controller fetches the data from physical flash cells across PCIe DMA into host memory.
4. The hardware interrupt fires, waking the thread to return to user space.

Physical NAND flash cells impose an unavoidable physical read latency ($t_R \approx 80 - 120\text{ }\mu\text{s}$). If each synchronous $128\text{ KB}$ round-trip takes $120\text{ }\mu\text{s}$:

$$\text{Maximum Synchronous Throughput} = \frac{128\text{ KB}}{120\text{ }\mu\text{s}} \approx 1.04\text{ GB/s}$$

A synchronous read loop enforces a **Queue Depth of 1 ($\text{QD} = 1$)**. While the host thread waits for that single block, the SSD controller cannot prefetch subsequent flash blocks, leaving **roughly $80\%$ of its internal flash channels completely idle**.

To saturate physical PCIe bandwidth, the host software must supply a continuous pipeline of concurrent in-flight requests—maintaining a **Queue Depth ($\text{QD} \ge 16$)** so the controller can read from all NAND dies simultaneously.

---

## 2. The Engine: How io_uring Delivers Single-Thread Queue Depth

Historically, achieving $\text{QD} = 16$ required either spawning 16 separate worker threads (wasting memory stacks and suffering CPU thread preemption) or fighting archaic APIs. 

Today, **`io_uring`** is the standard Linux asynchronous I/O engine. Instead of trapping into the kernel on every operation, `io_uring` establishes **two lockless circular ring buffers** in kernel memory and maps them directly into user space via `mmap()`:

* **Submission Queue (SQ):** An array of Submission Queue Entries (`struct io_uring_sqe`). User space enqueues read commands by writing to the ring and advancing its tail pointer.
* **Completion Queue (CQ):** An array of Completion Queue Entries (`struct io_uring_cqe`). The kernel posts completed DMA events by advancing the CQ tail pointer; user space consumes them by advancing the CQ head pointer.

<svg viewBox="0 0 880 340" width="100%" style="max-width:880px;display:block;margin:1.8em auto;" role="img" aria-label="io_uring Shared Memory Architecture">
  <defs>
    <marker id="ring-arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="currentColor" fill-opacity="0.7"/>
    </marker>
  </defs>

  <!-- User Space Region -->
  <rect x="20" y="20" width="400" height="300" rx="8" fill="currentColor" fill-opacity="0.03" stroke="currentColor" stroke-opacity="0.3" stroke-width="1.5"/>
  <text x="220" y="50" text-anchor="middle" font-size="16" font-weight="700" fill="currentColor" fill-opacity="0.95">User Space (Application)</text>

  <!-- Kernel Space Region -->
  <rect x="460" y="20" width="400" height="300" rx="8" fill="currentColor" fill-opacity="0.06" stroke="currentColor" stroke-opacity="0.4" stroke-width="1.5"/>
  <text x="660" y="50" text-anchor="middle" font-size="16" font-weight="700" fill="currentColor" fill-opacity="0.95">Kernel Space (OS & NVMe Driver)</text>

  <!-- Shared Submission Ring -->
  <rect x="180" y="80" width="520" height="90" rx="6" fill="currentColor" fill-opacity="0.08" stroke="currentColor" stroke-opacity="0.6" stroke-width="1.8"/>
  <text x="440" y="105" text-anchor="middle" font-size="13" font-weight="700" fill="currentColor" fill-opacity="0.9">Shared Memory: Submission Queue Ring (SQ)</text>
  <rect x="200" y="120" width="110" height="35" rx="4" fill="currentColor" fill-opacity="0.15" stroke="currentColor" stroke-opacity="0.5"/>
  <text x="255" y="142" text-anchor="middle" font-size="11" fill="currentColor">SQE 0 (Read)</text>
  <rect x="325" y="120" width="110" height="35" rx="4" fill="currentColor" fill-opacity="0.15" stroke="currentColor" stroke-opacity="0.5"/>
  <text x="380" y="142" text-anchor="middle" font-size="11" fill="currentColor">SQE 1 (Read)</text>
  <rect x="450" y="120" width="110" height="35" rx="4" fill="currentColor" fill-opacity="0.15" stroke="currentColor" stroke-opacity="0.5"/>
  <text x="505" y="142" text-anchor="middle" font-size="11" fill="currentColor">SQE 2 (Read)</text>
  <text x="600" y="142" font-size="14" fill="currentColor" fill-opacity="0.6">...</text>

  <!-- Shared Completion Ring -->
  <rect x="180" y="200" width="520" height="90" rx="6" fill="currentColor" fill-opacity="0.08" stroke="currentColor" stroke-opacity="0.6" stroke-width="1.8"/>
  <text x="440" y="225" text-anchor="middle" font-size="13" font-weight="700" fill="currentColor" fill-opacity="0.9">Shared Memory: Completion Queue Ring (CQ)</text>
  <rect x="200" y="240" width="110" height="35" rx="4" fill="currentColor" fill-opacity="0.2" stroke="currentColor" stroke-opacity="0.6"/>
  <text x="255" y="262" text-anchor="middle" font-size="11" fill="currentColor">CQE 0 (Done)</text>
  <rect x="325" y="240" width="110" height="35" rx="4" fill="currentColor" fill-opacity="0.2" stroke="currentColor" stroke-opacity="0.6"/>
  <text x="380" y="262" text-anchor="middle" font-size="11" fill="currentColor">CQE 1 (Done)</text>
  <text x="475" y="262" font-size="14" fill="currentColor" fill-opacity="0.6">...</text>

  <!-- Pointers -->
  <path d="M 120 137 L 190 137" stroke="currentColor" stroke-width="2" marker-end="url(#ring-arrow)"/>
  <text x="110" y="132" text-anchor="end" font-size="11" fill="currentColor">App writes SQE</text>

  <path d="M 690 137 L 760 137" stroke="currentColor" stroke-width="2" marker-end="url(#ring-arrow)"/>
  <text x="770" y="132" text-anchor="start" font-size="11" fill="currentColor">Kernel polls SQE</text>

  <path d="M 760 257 L 690 257" stroke="currentColor" stroke-width="2" marker-end="url(#ring-arrow)"/>
  <text x="770" y="252" text-anchor="start" font-size="11" fill="currentColor">Kernel posts CQE</text>

  <path d="M 190 257 L 120 257" stroke="currentColor" stroke-width="2" marker-end="url(#ring-arrow)"/>
  <text x="110" y="252" text-anchor="end" font-size="11" fill="currentColor">App reaps CQE</text>
</svg>

### Zero-Allocation Buffer Engineering
To use `O_DIRECT` safely and maximize efficiency with `io_uring`:

1. **Mandatory 4KB Alignment:** Physical DMA controllers transfer data across memory bus boundaries at sector or page granularity. All user buffers must be aligned to 4096 bytes via `posix_memalign(&buf, 4096, size)` or `mmap()`, otherwise operations immediately fail with `-EINVAL`.
2. **Fixed Registered Buffers (`IORING_OP_READ_FIXED`):** In standard `O_DIRECT`, the kernel executes `get_user_pages()` on every single read, walking the 4-level page table and modifying refcounts. By calling `io_uring_register_buffers()` once at startup, the kernel pins the memory pool upfront. Subsequent reads use `io_uring_prep_read_fixed()`, completely bypassing page table walks on the fast path.

---

## 3. Empirical Benchmarks: Bare-Metal NVMe vs. Virtualized Cloud Storage

To validate the theoretical Queue Depth predictions against reality, we benchmarked unbuffered reads across two distinct production environments:
1. **Bare-Metal Physical Flash:** Apple M4 Pro NVMe SSD scanning a $4\text{ GB}$ dataset.
2. **Virtualized Cloud Storage:** 64-bit ARM Linux server (AWS Graviton2, Linux 7.0) backed by an AWS NVMe EBS gp3 volume scanning a $512\text{ MB}$ dataset.

The full benchmark harnesses are maintained in standalone files:
* Linux `io_uring` harness: <a href="{{ '/assets/code/bench_io_uring/' | relative_url }}" target="_blank" rel="noopener">bench_io_uring.c</a>.
* Apple Silicon unbuffered harness: <a href="{{ '/assets/code/m4_direct_bench/' | relative_url }}" target="_blank" rel="noopener">m4_direct_bench.c</a>.

---

### 3.1 Bare-Metal NVMe: Apple M4 Pro SSD (Physical Flash Parallelism)

| Queue Depth ($QD$) | Execution Mode | Elapsed Time | Measured Bandwidth | Hardware Saturation |
| :--- | :--- | :--- | :--- | :--- |
| **QD = 1** | Synchronous Unbuffered | $3.86\text{ s}$ | **$1.04\text{ GB/s}$** ($1,061.9\text{ MB/s}$) | $20.3\%$ |
| **QD = 4** | Pipelined Unbuffered | $1.34\text{ s}$ | **$2.98\text{ GB/s}$** ($3,051.1\text{ MB/s}$) | $58.3\%$ |
| **QD = 8** | Pipelined Unbuffered | $1.06\text{ s}$ | **$3.79\text{ GB/s}$** ($3,876.9\text{ MB/s}$) | $74.2\%$ |
| **QD = 16** | Pipelined Unbuffered | $0.78\text{ s}$ | **$5.11\text{ GB/s}$** ($5,230.5\text{ MB/s}$) | **$100.0\%$ (Hardware Ceiling)** |
| **QD = 32** | Pipelined Unbuffered | $0.78\text{ s}$ | **$5.11\text{ GB/s}$** ($5,236.5\text{ MB/s}$) | **$100.0\%$ (Hardware Ceiling)** |

#### Architectural Insight:
* **The Synchronous Stall ($1.04\text{ GB/s}$):** At $\text{QD} = 1$, round-trip latency perfectly bounds throughput to $\frac{128\text{ KB}}{1.04\text{ GB/s}} \approx 120.2\text{ }\mu\text{s}$. The drive operates in single-channel mode.
* **The 4.9x Saturation Plateau ($5.11\text{ GB/s}$):** Scaling Queue Depth to $\text{QD} \ge 16$ unlocks **$5.11\text{ GB/s}$**, fully saturating the PCIe Gen 4 bus. Increasing to $\text{QD} = 32$ yields identical results, confirming the physical hardware ceiling has been reached.

---

### 3.2 Virtualized Cloud Storage: Linux 64-bit ARM (Graviton2 NVMe EBS)

| Benchmark Configuration | Mechanism | Elapsed Time | Measured Bandwidth | % of Provisioned Baseline |
| :--- | :--- | :--- | :--- | :--- |
| **Sync read()** | Synchronous `read()` ($QD = 1$) | $4.303\text{ s}$ | **$119.0\text{ MB/s}$** | $95.2\%$ |
| **io_uring (QD = 1)** | Asynchronous Ring ($QD = 1$) | $4.322\text{ s}$ | **$118.5\text{ MB/s}$** | $94.8\%$ |
| **io_uring (QD = 4)** | Asynchronous Ring ($QD = 4$) | $3.098\text{ s}$ | **$165.3\text{ MB/s}$** | **$132.2\%$ (Burst Active)** |
| **io_uring (QD = 8)** | Asynchronous Ring ($QD = 8$) | $4.106\text{ s}$ | **$124.7\text{ MB/s}$** | $99.8\%$ |
| **io_uring (QD = 16)** | Asynchronous Ring ($QD = 16$) | $4.096\text{ s}$ | **$125.0\text{ MB/s}$** | **$100.0\%$ (Hypervisor Ceiling)** |
| **io_uring (QD = 32)** | Asynchronous Ring ($QD = 32$) | $4.091\text{ s}$ | **$125.1\text{ MB/s}$** | **$100.1\%$ (Hypervisor Ceiling)** |
| **io_uring Fixed (QD = 16)** | Registered Buffers (`READ_FIXED`) | $4.103\text{ s}$ | **$124.8\text{ MB/s}$** | $99.8\%$ |

#### Architectural Insight:
* **Hypervisor Token-Bucket Limiting:** Cloud block devices (such as AWS EBS gp3) are rate-limited in software to provisioned targets ($125\text{ MB/s}$ baseline). While bare-metal NVMe scales to $5\text{ GB/s}$, cloud storage hits a hard ceiling at $\text{QD} \ge 16$ at **$125.0 - 125.1\text{ MB/s}$** ($100.0\%$ provisioned line rate).
* **The Burst Phenomenon at QD = 4 ($165.3\text{ MB/s}$):** Parallel request submission initially drained AWS EBS burst credits, spiking throughput to $165.3\text{ MB/s}$ before throttling down to the baseline.
* **The Real Cloud Win: Zero-Syscall CPU Efficiency:** In synchronous `read()`, transferring $512\text{ MB}$ required **4,096 blocking system calls** and 8,192 thread context switches into `TASK_UNINTERRUPTIBLE`. With `io_uring`, the entire transfer executed inside a **single thread** with zero thread preemption and no `get_user_pages()` page table walks.

---

## 4. Summary: The Engineering Recipe

When designing high-throughput data engines:

1. **Queue Depth $\ge 16$ is mandatory:** A synchronous loop ($\text{QD} = 1$) leaves physical NAND flash channels starved and stalls around $\sim 1\text{ GB/s}$.
2. **`io_uring` provides line rate in a single thread:** Lockless shared memory rings eliminate system calls and avoid thread-pool scheduling overhead.
3. **Always register fixed 4KB-aligned buffers:** Use `posix_memalign` to meet physical DMA alignment and `io_uring_register_buffers` to eliminate kernel page-pinning walks on the fast path.
