---
title: "Socket Busy Polling"
date: 2026-11-09 07:15:00 +0800
categories:
  - system
tags: system linux kernel networking tcp low-latency performance epoll
excerpt: >
  A first-principles deep dive into Linux socket busy polling (SO_BUSY_POLL) and epoll Reactor architecture: how bypassing interrupts rewrites the NIC receive path, CPU cache and thermal trade-offs, Edge vs. Level triggering, and preventing FD starvation during market bursts.
---

In our previous explorations of [TCP Receive Queue Anatomy](/system/2026/11/08/tcp-receive-queue.html) and [epoll Anatomy](/system/2026/11/09/epoll-anatomy.html), we analyzed how packets travel from the wire into kernel memory buffers (`sk_receive_queue`) and how `epoll` multiplexes hundreds of connections using kernel Red-Black trees and ready lists.

Yet under default Linux network configurations, both `epoll` and standard socket I/O rely on hardware interrupts and OS scheduler wakeups that inject $5$ to $20\,\mu\text{s}$ of tail latency into every packet.

To eliminate this overhead, high-frequency execution stacks turn to **`SO_BUSY_POLL`**.

---

## 1. The Latency Trap: Traditional NAPI and Interrupts

Under the default Linux network stack, how does `epoll_wait()` know when to wake up?

It relies on a chain of hardware interrupts, software interrupts (NAPI softirqs), and OS scheduler context switches:

```text
1. Wire Arrival:       Packet lands in NIC Hardware RX Ring via DMA
                              │
2. Hardware Interrupt: NIC fires IRQ line to CPU core
                              │
3. Top-Half Handler:   CPU suspends user code; masks NIC interrupts; schedules NAPI
                              │
4. Bottom-Half (NAPI): ksoftirqd wakes; calls driver napi_poll(); allocates sk_buff;
                       enqueues to sk_receive_queue; calls sk->sk_data_ready()
                              │
5. Scheduler Wakeup:   Kernel moves user thread from wait queue to run queue;
                       context switches CPU registers and memory page tables
                              │
6. Application Read:   Thread returns from epoll_wait(), executes recv()
```

### The Cost of the Interrupt Chain
This traditional chain introduces severe latency liabilities for high-frequency trading:
* **Context-Switch Penalties:** Transitioning the CPU core from user space to kernel space, running interrupt service routines, and switching back costs $2$ to $5\,\mu\text{s}$.
* **Scheduler Jitter:** The OS scheduler may take anywhere from $5$ to $50\,\mu\text{s}$ to reschedule a sleeping thread (`TASK_INTERRUPTIBLE` $\to$ `TASK_RUNNING`), especially under core contention.
* **CPU Cache Thrashing:** In many Linux configurations, the hardware interrupt fires on Core A (servicing `ksoftirqd`), while your trading application runs on Core B. When Core B finally calls `recv()`, the packet headers and payload reside on Core A's L1/L2 caches, forcing an expensive **cross-core cache coherency bounce (L3 miss)**.

---

## 2. How `SO_BUSY_POLL` Rewrites the Receive Path

Linux 3.11 introduced **`SO_BUSY_POLL`** (`SOL_SOCKET`), fundamentally altering the packet delivery pipeline:

```c
int busy_poll_us = 50; // Poll for up to 50 microseconds
setsockopt(sock_fd, SOL_SOCKET, SO_BUSY_POLL, &busy_poll_us, sizeof(busy_poll_us));
```

### The Fundamental Shift: Inverting Control
Instead of passively yielding the CPU and waiting for the kernel to wake it up via interrupt, **the user-space application thread itself drives the NIC polling routine from process context**.

```text
TRADITIONAL INTERRUPT PATH:
Application: [ epoll_wait() ] ──► SLEEP (Yields CPU) ───────────────► WAKEUP ──► recv()
                                     ▲                                  ▲
Hardware:    Packet Arrives ──► Hard IRQ ──► SoftIRQ (napi_poll) ───────┘

SO_BUSY_POLL PATH:
Application: [ epoll_wait() / recv() ]
                   │
                   ▼ (Receive queue empty? DO NOT SLEEP!)
             User thread calls directly into driver's napi_poll()
                   │
                   ├─► Checks NIC Hardware RX Ring descriptors in RAM
                   ├─► Packet detected! Moves into sk_receive_queue
                   ▼
             Returns data immediately to user buffer! (ZERO IRQs, ZERO Context Switches)
```

### How It Works Mechanically
1. When your application calls `recv()`, `read()`, or `epoll_wait()`, the kernel checks `sk_receive_queue`.
2. If packets are already present, they are returned immediately.
3. If the queue is empty, the kernel **refuses to sleep**. Instead, the current thread enters a tight loop for up to `busy_poll_us` microseconds.
4. On every loop iteration, the user thread calls the network device driver's `napi_poll()` method directly.
5. The thread reads the physical NIC RX ring descriptors in host RAM. As soon as a descriptor indicates a packet has arrived via DMA, the thread executes the TCP stack logic inline and copies the payload to user space.

If no packet arrives before the `busy_poll_us` timer expires, the thread gracefully falls back to the traditional interrupt-driven sleep.

---

## 3. Architectural Trade-offs: Cache, Core, and Thermals

While `SO_BUSY_POLL` eliminates interrupt overhead, it is not a free lunch. It trades hardware efficiency and power for deterministic tail latency.

### 1. CPU Cache: The Pure Win
* **Zero L3 Cache Bouncing:** The exact CPU core that processes the trading logic is the core executing `napi_poll()`.
* **Hot L1/L2 Cachelines:** As the core DMA-polls the ring buffer and executes TCP validation, the packet payload is brought directly into the core's private L1 and L2 data caches. When the function returns to user space, the payload is already smoking hot in L1 cache, allowing message decoders (e.g., SBE or FIX parsers) to run with zero memory stall cycles.

### 2. Core Utilization: The Dedicated Resource Cost
* In traditional systems, an idle network thread yields the CPU, allowing other processes to run.
* With `SO_BUSY_POLL`, the core spins at **100% CPU utilization** during active bursts. 
* To prevent priority inversions and thread starvation, cores running `SO_BUSY_POLL` must be **strictly isolated (`isolcpus`)** and dedicated to network processing. You cannot safely co-locate batch computing or logging threads on a busy-polling core.

### 3. Thermal & Power Consumption: Turbo Frequency Penalties
* **No C-States:** Modern Intel/AMD CPUs drop idle cores into low-power sleep states (C1, C6) to conserve energy and manage thermal headroom. Busy polling keeps the core pinned in C0 (full power) indefinitely.
* **Thermal Throttling & Turbo Budget:** Server processors dynamically allocate power to boost clock frequencies (Intel Turbo Boost / AMD Precision Boost). When multiple cores are pinned at 100% running busy polls, package power consumption spikes. This can force the processor to downclock all cores across the socket to stay within the thermal envelope (TDP), inadvertently reducing the peak clock speed of your pricing calculation engines.

---

## 4. Reactor Triggering: Edge (`EPOLLET`) vs. Level (`EPOLLLT`)

In an `epoll`-based Reactor architecture, the kernel allows you to configure how sockets notify your event loop:

### Level-Triggered (`EPOLLLT` - The Default)
* **Behavior:** As long as there is unread data sitting in `sk_receive_queue`, `epoll_wait()` will **repeatedly report the socket as ready** on every single invocation.
* **Advantage:** Foolproof simplicity. If your application only reads 500 bytes of a 2 KB message, the very next call to `epoll_wait()` will immediately return the socket again.
* **Disadvantage:** High system call overhead. If you cannot process all data immediately, `epoll_wait()` continually wakes up on the same FD, burning unnecessary CPU cycles.

### Edge-Triggered (`EPOLLET` - The State Transition)
* **Behavior:** `epoll_wait()` delivers a notification **only when new data arrives on a previously quiescent socket** (a rising edge from 0 bytes to $> 0$ bytes).
* **Advantage:** Maximum throughput and minimal kernel event transitions. `epoll` notifies you once; it will not notify you again until *new* traffic arrives from the wire.
* **The Dangerous Trap:** If you call `recv()` once, consume only half the available buffer, and return to `epoll_wait()`, **the kernel will never notify you again for the remaining data**. The remaining bytes will sit frozen in `sk_receive_queue` indefinitely until an unrelated packet arrives to trigger a new edge.

```text
EDGE-TRIGGERED MANDATE:
When using EPOLLET, you MUST use non-blocking sockets (O_NONBLOCK) 
and read in a tight loop until recv() explicitly returns -1 with EAGAIN or EWOULDBLOCK.
```

---

## 5. The FD Starvation Catastrophe

The strict requirement of `EPOLLET`—draining a socket until `EAGAIN`—creates one of the most dangerous failure modes in financial market gateways: **File Descriptor Starvation (FD Starvation)**.

### The Attack Vector: The Market Burst
Imagine your Reactor thread monitors two sockets:
* **Socket A:** Binance BTC-USDT market data tick stream.
* **Socket B:** CME Order Execution Gateway (where your fill confirmations arrive).

At 08:30:00 EST (CPI data release), Binance unleashes an avalanche of 500,000 quote updates per second.

Because Socket A is in `EPOLLET` mode, your worker thread executes the standard draining loop:

```c
// THE DANGEROUS LOOP:
while ((bytes_read = recv(sock_a, buf, sizeof(buf), MSG_DONTWAIT)) > 0) {
    process_quote(buf, bytes_read);
}
// Thread will NOT exit this loop until recv() returns EAGAIN!
```

If packets arrive on Socket A faster than the thread can parse them, **`recv()` never returns `EAGAIN`**. 

The thread remains permanently trapped in the `while` loop on Socket A. Meanwhile, an urgent fill confirmation arrives on Socket B. Because the thread never returns to `epoll_wait()`, **Socket B is completely starved of CPU time**, leading to stale risk checks and blown trade execution windows.

```text
Thread Timeline:
[ Draining Socket A ] ──► [ Draining Socket A ] ──► [ Draining Socket A ] (Trapped!)
                                                                  ▲
Socket B (Order Fill): [ Arrived at 08:30:00.001 ] ───────────────┴── STARVED! (Not inspected)
```

---

## 6. How to Prevent FD Starvation in Production

High-performance systems use three battle-tested architectural patterns to prevent single-socket monopolization:

### 1. Quota-Based Fair Draining (The Heuristic Approach)
Never allow an event loop iteration to drain an unbounded volume of data from a single socket. Enforce a **read quota** (e.g., maximum 64 KB or 32 packets per event):

```c
int packets_read = 0;
const int MAX_BATCH_QUOTA = 32;

while (packets_read < MAX_BATCH_QUOTA) {
    ssize_t n = recv(fd, buf, sizeof(buf), MSG_DONTWAIT);
    if (n < 0) {
        if (errno == EAGAIN || errno == EWOULDBLOCK) break; // Fully drained
        handle_error(fd);
        break;
    }
    process_message(buf, n);
    packets_read++;
}

if (packets_read == MAX_BATCH_QUOTA) {
    // Quota exhausted! Socket may still have data.
    // Re-insert into internal pending queue to process on next tick!
    enqueue_pending_fd(fd);
}
```

If a socket hits its quota before reaching `EAGAIN`, the application stores the socket in an in-memory round-robin queue. The event loop moves on to service other ready FDs, ensuring fair CPU scheduling across all connections.

### 2. Multi-Reactor Thread Isolation
Do not mix market data ingestion with order execution on the same event loop:
* **Market Data Thread (Core 2):** Dedicated solely to handling high-throughput market quote streams using busy polling and batched quotas.
* **Order Entry Thread (Core 3):** Dedicated exclusively to low-volume, ultra-low-latency order management and fill responses.

By isolating these connections across distinct CPU cores, a flood on market data feeds physically cannot starve the order execution pathway.

### 3. `EPOLLONESHOT` Thread Hand-off
For multi-threaded worker pools, configure sockets with `EPOLLONESHOT`:
```c
event.events = EPOLLIN | EPOLLET | EPOLLONESHOT;
epoll_ctl(epfd, EPOLL_CTL_MOD, sock_fd, &event);
```
Once `epoll_wait()` returns a notification for that socket, the kernel automatically disables further events on it until your application explicitly re-arms it with `epoll_ctl(..., EPOLL_CTL_MOD, ...)`. 

This guarantees that only one worker thread touches the socket at any given moment, enabling other threads to concurrently service remaining connections without race conditions.

---

## Summary Architecture Matrix

| Dimension | Standard Linux Network Stack | `SO_BUSY_POLL` Stack |
| :--- | :--- | :--- |
| **Notification Trigger** | Hardware IRQ $\to$ SoftIRQ (`ksoftirqd`) | Process-context DMA Ring Polling |
| **Context Switches** | Required ($2$–$5\,\mu\text{s}$ overhead) | Zero (In-thread execution) |
| **Cache Behavior** | Cross-core bounce (Core A $\to$ Core B) | In-core hot L1/L2 cache residency |
| **Core Utilization** | Low when idle; yields CPU | 100% dedicated during polling window |
| **CPU Thermals** | Normal (allows C1/C6 power saving) | High (pins core in C0 state) |
| **Trigger Mechanism** | Level-Triggered (`EPOLLLT`) default | Edge-Triggered (`EPOLLET`) with quotas |
| **Burst Hazard** | Tail-latency spikes from scheduler lag | FD Starvation under unmetered loops |
