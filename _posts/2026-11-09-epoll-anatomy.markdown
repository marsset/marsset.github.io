---
title: "epoll Anatomy"
date: 2026-11-09 07:30:00 +0800
categories:
  - system
tags: system linux kernel networking epoll performance low-latency
excerpt: >
  A first-principles deep dive into the Linux epoll subsystem: how kernel Red-Black trees and ready lists replace O(N) scanning, the ep_poll_callback mechanic, Edge vs. Level triggering at the kernel data-structure level, and avoiding multi-threaded thundering herds.
---

In modern network servers and high-frequency trading (HFT) gateways, an application rarely communicates with just one peer. A market data handler or execution engine might manage hundreds of TCP connections simultaneously: exchange order entry ports, drop-copy feeds, market data multicast gateways, and internal risk channels.

If an application were to assign one operating system thread to every single connection, the system would drown under thread stack memory ($8\,\text{MB}$ default per thread) and OS scheduler context-switching churn.

To solve this, Linux provides **I/O multiplexing**: allowing a single thread to monitor hundreds or thousands of file descriptors (FDs) simultaneously.

While legacy systems relied on `select()` and `poll()`, modern Linux relies almost exclusively on **`epoll` (Event Poll)**. 

To understand why `epoll` works so efficiently—and where its subtle latency pitfalls lie—we must examine how it is implemented inside the Linux kernel.

---

## 1. The Predecessors: Why `select()` and `poll()` Collapsed

To appreciate `epoll`, we must first understand the catastrophic scalability bottleneck of its predecessors: `select()` and `poll()`.

Suppose an exchange gateway monitors $10{,}000$ client connections. In any given millisecond, only $2$ of those connections have inbound orders; the other $9{,}998$ connections are completely idle.

Under `select()` or `poll()`:

```text
USER SPACE                                    KERNEL SPACE
┌───────────────────────────────┐             ┌───────────────────────────────┐
│ 10,000 FDs in array           │ ──────────► │ Copy 10,000 FDs across        │
│                               │             │ boundary                      │
│                               │             │                               │
│                               │             │ O(N) Loop: Inspect every      │
│                               │             │ socket receive queue one-     │
│                               │             │ by-one to see if ready        │
│                               │             │                               │
│ Re-scan entire 10,000 array   │ ◄────────── │ Copy 10,000 results back      │
│ in user space to find the 2!  │             │ to user space                 │
└───────────────────────────────┘             └───────────────────────────────┘
```

This architecture suffers from three fatal design flaws:
1. **$O(N)$ Memory Copies on Every Tick:** On every single event loop iteration, user space must serialize and copy the entire array of $10{,}000$ file descriptors across the kernel boundary, and the kernel must copy them back.
2. **$O(N)$ Kernel Polling:** The kernel must linearly iterate through all $10{,}000$ sockets, inspecting each socket's `sk_receive_queue` to determine if data has arrived.
3. **Stateless Amnesia:** The kernel retains zero memory of your watched sockets between system calls. Even if your $10{,}000$ connections never change, you must re-register the entire set on every call to `select()`.

At $10{,}000$ connections, your CPU core spends $99.9\%$ of its time scanning empty memory arrays rather than processing trades.

---

## 2. The Core Architecture of `epoll`

Linux 2.5.44 introduced **`epoll`**, which completely eliminates $O(N)$ scanning by transforming the kernel interface from a **stateless poll** into a **stateful event registration**.

Instead of passing an array of sockets into the kernel on every call, `epoll` stores your watched sockets **permanently inside the kernel** across two dedicated data structures:

```text
                             [ struct eventpoll ]
                               (Kernel Object)
                                      │
            ┌─────────────────────────┴─────────────────────────┐
            ▼                                                   ▼
   [ The Interest List ]                               [ The Ready List ]
    (Red-Black Tree: rbr)                              (Doubly-Linked List: rdllist)
            │                                                   │
   Stores ALL monitored sockets                        Stores ONLY sockets that 
   (e.g., 10,000 total connections)                    have unread data in RAM (e.g., 2)
   Operations: O(log N) lookup/add/del                 Operations: O(1) drain
```

### 1. The Interest List (`rbr` - Red-Black Tree)
When you add a socket to `epoll` via `epoll_ctl(epfd, EPOLL_CTL_ADD, fd, &event)`, the kernel stores an internal descriptor (`struct epitem`) in an augmented **Red-Black Tree** ordered by file descriptor number.
* **Why an RB-Tree?** It allows the kernel to search, add, or remove watched file descriptors in $O(\log N)$ time, preventing duplicates and supporting rapid dynamic socket lifecycle changes without memory reallocations.

### 2. The Ready List (`rdllist` - Doubly Linked List)
The ready list contains references to **only those sockets that currently have unread data or pending events**.
* When your thread calls `epoll_wait(epfd, events, maxevents, timeout)`, the kernel does **not** scan the $10{,}000$ sockets in the Red-Black tree.
* It simply inspects the head of `rdllist`. 
* If `rdllist` is empty, your thread sleeps on the `eventpoll` wait queue (`ep->wq`).
* If `rdllist` is non-empty, the kernel immediately drains up to `maxevents` items from `rdllist` and copies them directly into your user-space array.

The performance of `epoll_wait()` is **$O(K)$**, where $K$ is the number of active sockets (e.g., $2$), completely independent of the total number of monitored connections $N$ ($10{,}000$).

---

## 3. Under the Hood: The `ep_poll_callback` Engine

How does a socket physically jump from the Red-Black tree onto the Ready List when a packet arrives?

There is no background polling thread inside the kernel. The movement is driven entirely by **hardware interrupt callbacks**.

```text
1. Wire Arrival:       Packet arrives at NIC -> DMA transfer to Host RAM
                              │
2. SoftIRQ Execution:  NAPI poll packages sk_buff into sk_receive_queue
                              │
3. Socket Wakeup:      Kernel calls socket's internal callback:
                       sk->sk_data_ready()
                              │
4. The epoll Hook:     sk_data_ready() invokes ep_poll_callback()!
                              │
5. Ready List Insert:  ep_poll_callback() locks epoll spinlock,
                       inserts epitem into rdllist (if not already present),
                       and wakes up any thread sleeping on epoll_wait()
```

### The Registration Chain
1. When you call `epoll_ctl(..., EPOLL_CTL_ADD, ...)`, the kernel calls the underlying driver's poll method (`vfs_poll` / `tcp_poll`).
2. The kernel initializes a wait queue entry and attaches an internal kernel callback: **`ep_poll_callback()`** to the socket's internal wait queue (`sk->sk_wq`).
3. As covered in our [TCP Receive Queue Anatomy](/system/2026/11/08/tcp-receive-queue.html), when an incoming packet passes TCP checksum and enters `sk_receive_queue`, the TCP stack executes `sk->sk_data_ready()`.
4. `sk->sk_data_ready()` walks the socket's wait queue and triggers `ep_poll_callback()`.
5. `ep_poll_callback()` verifies the event mask (e.g., `EPOLLIN`), unlinks the `epitem` if needed, appends it to `rdllist`, and wakes up the trading thread sleeping in `epoll_wait()`.

Everything is reactive. Zero CPU cycles are burned on idle connections.

---

## 4. Edge-Triggered vs. Level-Triggered at Kernel Data Structure Level

The difference between Level-Triggered (`EPOLLLT`) and Edge-Triggered (`EPOLLET`) is frequently misunderstood. The difference becomes blindingly obvious when you look at how the kernel manipulates the **Ready List (`rdllist`)** during `epoll_wait()`.

```text
======================================================================
 LEVEL-TRIGGERED (EPOLLLT) WORKFLOW
======================================================================
1. epoll_wait() pops epitem from rdllist.
2. Copies event to user-space array.
3. Kernel checks: Does socket's sk_receive_queue STILL have unread bytes?
     ├─► YES: Kernel immediately RE-INSERTS epitem back into rdllist!
     └─► NO:  Leave off rdllist.
(Result: If you do not read all data, next epoll_wait() wakes up instantly!)

======================================================================
 EDGE-TRIGGERED (EPOLLET) WORKFLOW
======================================================================
1. epoll_wait() pops epitem from rdllist.
2. Copies event to user-space array.
3. Kernel does NOT check sk_receive_queue!
4. epitem is NEVER re-inserted into rdllist by epoll_wait().
(Result: The socket will ONLY return to rdllist when a BRAND NEW packet 
 arrives from the wire to trigger ep_poll_callback() again!)
```

### The Edge-Triggered Trap
If you use `EPOLLET` and your application reads $1{,}000$ bytes of a $2{,}000$-byte message and then returns to `epoll_wait()`:
* The kernel will **never** notify you about the remaining $1{,}000$ bytes!
* The remaining bytes sit frozen in `sk_receive_queue` indefinitely.
* **The Rule of ET:** You must always set your socket to non-blocking (`O_NONBLOCK`) and loop `recv()` until it explicitly returns `-1` with `errno == EAGAIN` or `EWOULDBLOCK`.

---

## 5. Multi-Threaded Latency Traps in HFT

When scaling an `epoll` architecture across multiple CPU cores, high-throughput systems encounter three severe latency bottlenecks:

### 1. The Thundering Herd Problem (`EPOLLEXCLUSIVE`)
In high-concurrency architectures, engineers often create a single `epoll` instance shared across 8 worker threads:
* All 8 threads call `epoll_wait(shared_epfd, ...)` and sleep.
* A single packet arrives on one socket.
* Historically, the kernel woke up **all 8 threads** simultaneously.
* One thread succeeded in calling `recv()`, while the other 7 threads received `EAGAIN`, having wasted microseconds on useless context switches and cache thrashing.

**The Solution:**
Linux 4.5 introduced **`EPOLLEXCLUSIVE`**:
```c
struct epoll_event ev;
ev.events = EPOLLIN | EPOLLET | EPOLLEXCLUSIVE;
epoll_ctl(epfd, EPOLL_CTL_ADD, sock_fd, &ev);
```
With `EPOLLEXCLUSIVE`, when an event arrives, the kernel guarantees that **only one** sleeping thread is awakened.

### 2. Multi-Thread Race Conditions (`EPOLLONESHOT`)
If you share an `epoll` set across worker threads without strict coordination, a race condition can occur:
1. Thread 1 wakes up on Socket A and begins draining data.
2. While Thread 1 is still parsing, another packet arrives on Socket A from the wire.
3. The kernel wakes up Thread 2 on Socket A!
4. Now **two different threads are concurrently executing `recv()` on the same TCP stream**, causing corrupted out-of-order application message parsing.

**The Solution:**
Mark the socket with **`EPOLLONESHOT`**:
```c
ev.events = EPOLLIN | EPOLLET | EPOLLONESHOT;
```
Once `epoll_wait()` returns an event for that socket, the kernel automatically disables further events for that FD. No other thread will ever be notified for it until Thread 1 completely finishes processing and explicitly re-arms it:
```c
epoll_ctl(epfd, EPOLL_CTL_MOD, sock_fd, &ev);
```

### 3. The Shared Epoll Spinlock Contention
Inside `struct eventpoll`, the ready list `rdllist` and the wait queue `wq` are protected by a single spinlock (`ep->lock`).

If 16 CPU cores actively call `epoll_ctl()` and `epoll_wait()` on the **same shared `epfd`**, the cores spend substantial time spinning on `ep->lock`, causing severe CPU cacheline bouncing.

**The Production HFT Architecture:**
Never share an `epoll` instance across threads. Instead, use a **Thread-Per-Core Shared-Nothing Reactor Architecture**:
* Each CPU core owns its own independent `epfd`.
* Sockets are partitioned among cores (e.g., via `SO_REUSEPORT` with BPF hashing or explicit connection pinning).
* Each core polls its own local `epfd` with zero lock contention.

---

## Summary: Evolution Matrix

| Mechanism | Registration Complexity | Event Check Complexity | Kernel State | Scalability Bottleneck |
| :--- | :--- | :--- | :--- | :--- |
| `select()` | $O(N)$ copy every tick | $O(N)$ linear loop | Stateless | Limited to 1024 FDs (`FD_SETSIZE`) |
| `poll()` | $O(N)$ copy every tick | $O(N)$ linear loop | Stateless | Memory copy and iteration scaling |
| `epoll (LT)` | $O(\log N)$ add once (RB-Tree) | $O(K)$ active items (Ready List) | Stateful | Syscall churn on unconsumed buffers |
| `epoll (ET)` | $O(\log N)$ add once (RB-Tree) | $O(K)$ active items (Ready List) | Stateful | Risk of FD starvation or silent freeze |
