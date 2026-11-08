---
title: "TCP Collapse"
date: 2026-11-09 06:30:00 +0800
categories:
  - system
tags: system linux kernel networking tcp low-latency performance
excerpt: >
  An intuitive, deep dive into Linux tcp_collapse(): the truesize amplification trap, how thousands of small packets deceive TCP flow control, why emergency kernel defragmentation freezes CPU cores for milliseconds during market bursts, and how to eliminate it.
---

Suppose you configure a generous 10 MB receive buffer for an execution socket:

```bash
sysctl -w net.ipv4.tcp_rmem="4096 87380 10485760"
```

During the market open, an exchange sends a burst of 5,000 small price quotes, each 100 bytes long. The total volume of data that traveled across the wire is just **500 KB**—barely 5% of your configured socket buffer.

Yet, right at that exact millisecond, your trading gateway freezes:
* Latency on the socket blows out from $5\,\mu\text{s}$ to **over $3\,\text{ms}$**.
* The CPU core servicing the network interface is pegged at 100% in kernel softirq execution.
* The physical Network Interface Card (NIC) begins dropping subsequent inbound packets onto the floor.

How can 500 KB of data completely choke a 10 MB socket buffer?

The culprit is one of the most notorious tail-latency traps in the Linux kernel: **`tcp_collapse()`**.

---

## 1. The Core Trap: The `truesize` Amplification

In high-performance networking, engineers naturally assume that receiving a 100-byte trade confirmation consumes 100 bytes of memory in the socket receive buffer (`sk_rcvbuf`).

In the Linux kernel, this assumption is completely wrong.

Every network packet arriving from the wire must be wrapped in kernel metadata structures. To track a single packet, Linux allocates:
1. **`struct sk_buff`**: The primary socket buffer metadata container (~224 to 256 bytes).
2. **`struct skb_shared_info`**: Fragment and memory refcounting structures (~320 bytes).
3. **Memory Allocator Alignments**: Modern Network Interface Cards (NICs) use driver page pools or slab allocators (e.g., `kmalloc-2048` or 4 KB page fragments) to avoid memory fragmentation during high-speed DMA.

The total memory charged against the socket for this single packet is tracked in **`skb->truesize`**:

```text
[ 100B Payload ]  +  [ 240B sk_buff ]  +  [ 320B shinfo ]  +  [ 1.4KB Slab Slack ]
└──────────────────────────────────────┬───────────────────────────────────────────┘
                     skb->truesize ≈ 2,048 Bytes!
```

$$\text{Payload} = 100 \text{ bytes} \quad \ll \quad \text{truesize} \approx 2{,}048 \text{ bytes}$$

Now the math behind our mystery becomes clear:

$$5{,}000 \text{ packets} \times 2{,}048 \text{ bytes (truesize)} = 10{,}240{,}000 \text{ bytes} \approx 10\,\text{MB}$$

The mere **500 KB** of market quotes on the wire silently consumed the **entire 10 MB** of kernel memory allocated to the socket!

---

## 2. Why TCP Flow Control Fails to Prevent It

TCP has a built-in mechanism to prevent buffer overflow: **The Advertised Receive Window (`RWND`)**.

The receiver tells the sender: *"I have 64 KB of free space in my buffer. You are legally allowed to send up to 64 KB."*

Here is where the architecture breaks down:

```
Sender View:    "I have 64 KB of budget. I will send 640 small packets of 100 bytes each."
                  Payload on wire: 64 KB

Receiver Reality: 640 packets × 2,048 Bytes (truesize) = 1,310,720 Bytes (1.3 MB)!
```

The TCP receive window is measured strictly in **payload bytes**. 

The Linux kernel socket memory limit (`sk->sk_rcvbuf`), however, is tracked in **allocated RAM (`sk->sk_rmem_alloc`)**, which aggregates `truesize`.

Because the sender has no idea what memory overhead the receiver's NIC driver and kernel slab allocator assign to each packet, the sender can easily exhaust the receiver's memory **while remaining completely compliant with the advertised window**.

---

## 3. The Emergency Procedure: `tcp_prune_queue()`

When the socket's memory usage surpasses the limit (`sk_rmem_alloc > sk_rcvbuf`), the kernel enters the emergency pruning path inside `net/ipv4/tcp_input.c`:

```
                       Incoming Packet Arrives
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │ sk_rmem_alloc > limit │
                     └───────────┬───────────┘
                                 │ Yes
                                 ▼
                     ┌───────────────────────┐
                     │  tcp_prune_queue()    │
                     └───────────┬───────────┘
                                 │
         ┌───────────────────────┴───────────────────────┐
         ▼                                               ▼
  [ Phase 1: Prune OFO ]                         [ Phase 2: Collapse ]
  Drop out-of-order queue                        Walk sk_receive_queue:
  (Re-allocations & ACKs lost)                   Allocate contiguous pages,
                                                 memcpy payload together,
                                                 free thousands of sk_buffs
```

### Phase 1: Discard Out-of-Order Packets (`tcp_prune_ofo_queue`)
The kernel first inspects the out-of-order reassembly queue (`tp->out_of_order_queue`). If packets arrived out of order, the kernel immediately discards them. The sender will eventually timeout and retransmit them, but this frees up immediate memory.

### Phase 2: Emergency Buffer Collapse (`tcp_collapse`)
If dropping out-of-order packets fails to reclaim enough space, the kernel initiates `tcp_collapse()`.

The kernel refuses to drop contiguous, in-order packets that have already been acknowledged to the sender. Instead, it chooses to perform **in-flight memory defragmentation**:
1. It walks the doubly linked list of `sk_buff`s in `sk_receive_queue`.
2. It allocates fresh, larger memory chunks.
3. It performs back-to-back **`memcpy`** operations, packing the payload of dozens of tiny `sk_buff`s into a single combined buffer.
4. It unlinks and frees the thousands of individual `sk_buff` headers back to the slab cache.

```text
BEFORE COLLAPSE:
[skb 1: 80B data (2KB truesize)] ─► [skb 2: 80B data (2KB truesize)] ─► [skb 3: 80B data (2KB truesize)]
Total Payload: 240 Bytes | Memory Consumed: 6,144 Bytes

AFTER COLLAPSE:
[Combined skb: 240B data (512B truesize)]
Total Payload: 240 Bytes | Memory Consumed: 512 Bytes (5,632 Bytes reclaimed!)
```

---

## 4. Why It Is a Catastrophe: The Anatomy of a Freeze

On paper, defragmentation sounds sensible. In high-performance systems, however, `tcp_collapse()` is one of the most destructive kernel routines in existence:

### 1. Socket Lock & Softirq Core Stall
`tcp_collapse()` executes with the **socket lock held**, often in software interrupt (`ksoftirqd` / NAPI softirq) context. 
Walking thousands of `sk_buff`s, calling page allocators, and copying memory blocks locks up the CPU core for **hundreds of microseconds to multiple milliseconds**.

### 2. Cache Annihilation
The CPU core must perform millions of memory reads and writes across scattered memory addresses to repack the payload. This completely evicts your application's hot instructions, L1/L2 cache lines, and pricing lookup tables right before your application needs to make trading decisions.

### 3. The NIC Ring Overflow Cascade
While the CPU core is frozen running `tcp_collapse()`, it cannot service new interrupts or poll the physical Network Interface Card.
The hardware RX ring on the NIC fills up within microseconds. The NIC has no choice but to start dropping incoming physical Ethernet frames (`rx_dropped` / `rx_missed_errors`).

```text
CPU Core:   [────────── Running tcp_collapse() (Stalled 2 ms) ──────────]
                                                                  ▲
NIC Hardware RX Ring: [■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■] (FULL!)
Incoming Packets:       ▲       ▲       ▲       ▲       ▲
                      DROPPED DROPPED DROPPED DROPPED DROPPED
```

### 4. Malicious Timing: The "Burst Trap"
`tcp_collapse()` does not happen during quiet market periods. It triggers when:
$$\text{Sudden Traffic Spike} + \text{Small Packets} + \text{Consumer Core Briefly Busy}$$

It strikes at the exact millisecond of a central bank rate announcement, earnings release, or market open—the precise instant when an execution gateway cannot afford a 2-millisecond blind spot.

---

## 5. Diagnostics: Is Your System Collapsing?

Linux tracks buffer collapse events in its kernel SNMP counters.

You can inspect whether your system has ever triggered this emergency path using `nstat`:

```bash
# View current counter value
nstat -az | grep -i collapse
```

Or using `netstat`:

```bash
netstat -s | grep -i "packets collapsed"
```

If `TcpExtTCPRcvCollapsed` is non-zero and incrementing during market hours, your trading gateway or network service is periodically undergoing emergency stop-the-world defragmentation.

You can also pinpoint the exact socket and process using `bpftrace`:

```bash
# Trace callers of tcp_collapse in real time
sudo bpftrace -e 'kprobe:tcp_collapse { printf("tcp_collapse triggered by comm: %s (PID: %d)\n", comm, pid); }'
```

---

## 6. How to Eliminate `tcp_collapse()`

Eliminating `tcp_collapse()` requires addressing either the memory calculation mismatch, the buffer draining rate, or bypassing kernel allocations altogether.

### 1. Tune `tcp_adv_win_scale` (The Direct Fix)
Linux provides a kernel parameter specifically designed to compensate for the `truesize` overhead:

```bash
# Add to /etc/sysctl.conf
net.ipv4.tcp_adv_win_scale = 2
```

How it works:
* `tcp_adv_win_scale = 1`: The kernel reserves $\frac{1}{2}$ ($50\%$) of the socket buffer for kernel metadata overhead, advertising only the remaining $50\%$ to the sender as `RWND`.
* `tcp_adv_win_scale = 2`: The kernel reserves $\frac{3}{4}$ ($75\%$) of the socket buffer for overhead, advertising only $25\%$ to the sender.

By increasing `tcp_adv_win_scale`, you force the TCP receive window to shrink much earlier, stopping the sender before small packet overhead can breach `sk_rcvbuf`.

### 2. Expand Socket Receive Memory (`tcp_rmem`)
Ensure your receive memory ceilings have enough slack to absorb high-frequency micro-bursts without hitting pruning limits:

```bash
# Set min, default, and max receive buffers in bytes (e.g., 16 MB max)
sysctl -w net.ipv4.tcp_rmem="4096 131072 16777216"
```

### 3. Spin Draining with [`SO_BUSY_POLL`](/system/2026/11/09/socket-busy-polling.html)
If the user-space thread drains packets the instant they hit `sk_receive_queue`, memory usage never accumulates to trigger `tcp_prune_queue()`.

Enabling low-latency busy polling bypasses interrupt scheduling delays and keeps the receive queue drained in sub-microsecond time (see [Socket Busy Polling](/system/2026/11/09/socket-busy-polling.html) for architecture details):

```c
int busy_poll_us = 50;
setsockopt(fd, SOL_SOCKET, SO_BUSY_POLL, &busy_poll_us, sizeof(busy_poll_us));
```

### 4. Kernel Bypass (The Production Solution)
For ultra-low latency systems, the true solution is to remove `sk_buff` from the datapath entirely.

Technologies like **Solarflare Onload**, **Mellanox VMA / Rivermax**, or **DPDK**:
* Deliver packets directly from NIC DMA rings into application memory.
* Eliminate the `sk_buff` control structure and page-pool wrapper completely.
* Possess zero `truesize` amplification.

In kernel-bypass architectures, `tcp_collapse()` is not just tuned away—it is architecturally eradicated.

---

## Summary Checklist

| Metric / Parameter | Default | Recommended for Low Latency | Why |
| :--- | :--- | :--- | :--- |
| `net.ipv4.tcp_adv_win_scale` | `1` ($50\%$ reserve) | `2` ($75\%$ reserve) | Accounts for tiny-packet `truesize` amplification |
| `net.ipv4.tcp_rmem` (max) | Varies (often ~6 MB) | `16777216` (16 MB) | Prevents burst-induced buffer exhaustion |
| `SO_BUSY_POLL` | `0` (Disabled) | `50` $\mu\text{s}$ | Eliminates wake-up lag; drains `sk_receive_queue` immediately |
| Diagnostic Metric | `TCPRcvCollapsed` | Must be `0` | Any increments indicate stop-the-world kernel latency spikes |
