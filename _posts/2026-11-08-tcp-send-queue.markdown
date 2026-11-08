---
title: "TCP Send Queue Anatomy"
date: 2026-11-08 15:45:00 +0800
categories:
  - system
tags: system linux kernel networking tcp low-latency performance
excerpt: >
  A deep dive into how the Linux kernel manages socket send memory: the lifecycle taxonomy of sk_buff states, sequence pointer boundaries (snd_una, snd_nxt, write_seq), transmission scheduling priority, and the structural split between sk_write_queue and tcp_rtx_queue.
---

When an application calls `send()` or `write()` on a TCP socket, the payload does not simply vanish onto the wire. It enters one of the most sophisticated queue management engines in operating system engineering: the **Linux TCP Send Queue**.

Understanding modern low-latency optimizations—such as `TCP_NOTSENT_LOWAT` and bufferbloat mitigation—requires understanding how the kernel actually classifies, tracks, and schedules data inside socket memory:

* How does the kernel distinguish between bytes that are **in flight across the continent** versus bytes **waiting idle in local RAM**?
* Why does the kernel keep holding data in memory long after the network card has physically transmitted it?
* When a network loss occurs, how does the kernel prioritize retransmissions versus fresh outbound orders?

This article breaks down the internal anatomy of the Linux TCP send buffer: its sequence pointer boundaries, the packet lifecycle taxonomy, and the kernel scheduling loop that selects what gets transmitted next. *(For the inbound market data path, see our companion post: [TCP Receive Queue Anatomy](/system/2026/11/08/tcp-receive-queue.html)).*

---

## 1. The Sequence Pointers: The Three Mathematical Boundaries

The Linux TCP implementation (`struct tcp_sock` in `include/linux/tcp.h`) does not use a state machine flag inside each byte to track its status. Instead, the entire send buffer is modeled as a continuous line of 32-bit sequence numbers governed by **three fundamental pointer boundaries**:

```
0                       snd_una              snd_nxt             write_seq
├──────────────────────────┼────────────────────┼───────────────────┤
│    ACKed & Cleaned       │     In-Flight      │      Unsent       │
│  (Freed from Memory)     │ (Awaiting ACK/Loss)│ (Idle in Host RAM)│
└──────────────────────────┴────────────────────┴───────────────────┘
```

### 1. `snd_una` (Send Unacknowledged)
* **What it is:** The oldest sequence number that has been transmitted but has not yet been acknowledged by the receiver.
* **The Boundary:** Everything to the left ($< \text{snd_una}$) has been confirmed received. The kernel has deleted these packets from RAM.
* **Who updates it:** Incoming ACK packets from the receiver. When the exchange returns `ack = 5000`, the kernel advances `snd_una` to $5{,}000$.

### 2. `snd_nxt` (Send Next)
* **What it is:** The next sequence number that the network card is scheduled to transmit onto the physical wire.
* **The Boundary:** The dividing line between what has left the host machine and what is still waiting inside local memory.
* **Who updates it:** The kernel transmission engine (`tcp_write_xmit()`). Every time the NIC transmits a frame, `snd_nxt` advances by the number of payload bytes sent.

### 3. `write_seq` (Application Write Sequence)
* **What it is:** The sequence number of the very latest byte written by the user application via `send()` or `write()`.
* **The Boundary:** The outer right edge of the socket buffer.
* **Who updates it:** The application thread executing the `sys_send()` or `sys_write()` syscall.

---

## 2. The Taxonomy of Socket Buffer States

Using these three pointers, all data inside a TCP socket buffer falls into one of four distinct states:

<svg viewBox="0 0 960 520" width="100%" height="auto" style="max-width:960px;display:block;margin:1.5em auto;background:rgba(0,0,0,0.02);border:1px solid rgba(0,0,0,0.1);border-radius:12px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
  <!-- Title -->
  <text x="480" y="32" text-anchor="middle" font-size="19" font-weight="800" fill="currentColor">The Four States of Data in the Linux TCP Send Buffer</text>
  <text x="480" y="54" text-anchor="middle" font-size="13.5" fill="currentColor" fill-opacity="0.65">How Pointer Boundaries Partition Socket RAM</text>

  <!-- State 1: Freed / Reaped -->
  <rect x="25" y="80" width="210" height="415" rx="8" fill="currentColor" fill-opacity="0.02" stroke="currentColor" stroke-opacity="0.2" stroke-width="1.5"/>
  <rect x="35" y="90" width="190" height="35" rx="6" fill="currentColor" fill-opacity="0.08"/>
  <text x="130" y="113" text-anchor="middle" font-size="15" font-weight="700" fill="currentColor">1. ACKed &amp; Freed</text>
  <text x="130" y="145" text-anchor="middle" font-size="13" font-family="monospace" fill="currentColor">seq &lt; snd_una</text>
  
  <rect x="40" y="170" width="180" height="90" rx="6" fill="currentColor" fill-opacity="0.04" stroke="currentColor" stroke-opacity="0.1"/>
  <text x="130" y="200" text-anchor="middle" font-size="13" font-weight="600" fill="currentColor">RAM Status: FREED</text>
  <text x="130" y="225" text-anchor="middle" font-size="12.5" fill="currentColor" fill-opacity="0.75">Deleted by tcp_clean_rtx</text>
  <text x="130" y="245" text-anchor="middle" font-size="12.5" fill="currentColor" fill-opacity="0.75">Memory returned to OS</text>

  <rect x="40" y="280" width="180" height="195" rx="6" fill="currentColor" fill-opacity="0.03"/>
  <text x="130" y="310" text-anchor="middle" font-size="13.5" font-weight="700" fill="currentColor">Physical Location</text>
  <text x="130" y="335" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.8">Safely received by peer</text>
  <text x="130" y="360" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.8">Acknowledged by ACK</text>
  <text x="130" y="395" text-anchor="middle" font-size="13.5" font-weight="700" fill="currentColor">Action Needed</text>
  <text x="130" y="420" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.8">None (Finished)</text>


  <!-- State 2: In-Flight -->
  <rect x="255" y="80" width="215" height="415" rx="8" fill="#1890ff" fill-opacity="0.03" stroke="#1890ff" stroke-opacity="0.5" stroke-width="2"/>
  <rect x="265" y="90" width="195" height="35" rx="6" fill="#1890ff" fill-opacity="0.15"/>
  <text x="362" y="113" text-anchor="middle" font-size="15" font-weight="800" fill="#1890ff">2. In-Flight (Wire)</text>
  <text x="362" y="145" text-anchor="middle" font-size="13" font-family="monospace" fill="currentColor">snd_una &le; seq &lt; snd_nxt</text>

  <rect x="270" y="170" width="185" height="90" rx="6" fill="#1890ff" fill-opacity="0.08" stroke="#1890ff" stroke-opacity="0.3"/>
  <text x="362" y="200" text-anchor="middle" font-size="13" font-weight="700" fill="#1890ff">RAM Status: RETAINED</text>
  <text x="362" y="225" text-anchor="middle" font-size="12.5" fill="currentColor">Stored in tcp_rtx_queue</text>
  <text x="362" y="245" text-anchor="middle" font-size="12.5" fill="currentColor">Held for retransmission</text>

  <rect x="270" y="280" width="185" height="195" rx="6" fill="currentColor" fill-opacity="0.03"/>
  <text x="362" y="310" text-anchor="middle" font-size="13.5" font-weight="700" fill="currentColor">Physical Location</text>
  <text x="362" y="335" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.8">Fiber optic cable</text>
  <text x="362" y="360" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.8">Traveling across WAN</text>
  <text x="362" y="395" text-anchor="middle" font-size="13.5" font-weight="700" fill="#1890ff">Does It Block Cancels?</text>
  <text x="362" y="420" text-anchor="middle" font-size="14" font-weight="800" fill="#52c41a">NO (Already left NIC)</text>


  <!-- State 3: Unsent (Host Backlog) -->
  <rect x="490" y="80" width="215" height="415" rx="8" fill="#ff4d4f" fill-opacity="0.03" stroke="#ff4d4f" stroke-opacity="0.5" stroke-width="2"/>
  <rect x="500" y="90" width="195" height="35" rx="6" fill="#ff4d4f" fill-opacity="0.15"/>
  <text x="597" y="113" text-anchor="middle" font-size="15" font-weight="800" fill="#ff4d4f">3. Unsent (Local RAM)</text>
  <text x="597" y="145" text-anchor="middle" font-size="13" font-family="monospace" fill="currentColor">snd_nxt &le; seq &lt; write_seq</text>

  <rect x="505" y="170" width="185" height="90" rx="6" fill="#ff4d4f" fill-opacity="0.08" stroke="#ff4d4f" stroke-opacity="0.3"/>
  <text x="597" y="200" text-anchor="middle" font-size="13" font-weight="700" fill="#ff4d4f">RAM Status: QUEUED</text>
  <text x="597" y="225" text-anchor="middle" font-size="12.5" fill="currentColor">Stored in sk_write_queue</text>
  <text x="597" y="245" text-anchor="middle" font-size="12.5" fill="currentColor">Waiting for NIC scheduler</text>

  <rect x="505" y="280" width="185" height="195" rx="6" fill="currentColor" fill-opacity="0.03"/>
  <text x="597" y="310" text-anchor="middle" font-size="13.5" font-weight="700" fill="currentColor">Physical Location</text>
  <text x="597" y="335" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.8">Local host memory</text>
  <text x="597" y="360" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.8">Has not touched wire</text>
  <text x="597" y="395" text-anchor="middle" font-size="13.5" font-weight="700" fill="#ff4d4f">Does It Block Cancels?</text>
  <text x="597" y="420" text-anchor="middle" font-size="14" font-weight="800" fill="#ff4d4f">YES (Direct FIFO Delay!)</text>


  <!-- State 4: Retransmission Pending -->
  <rect x="725" y="80" width="210" height="415" rx="8" fill="#faad14" fill-opacity="0.03" stroke="#faad14" stroke-opacity="0.5" stroke-width="1.5"/>
  <rect x="735" y="90" width="190" height="35" rx="6" fill="#faad14" fill-opacity="0.15"/>
  <text x="830" y="113" text-anchor="middle" font-size="15" font-weight="800" fill="#faad14">4. Lost / SACK Hole</text>
  <text x="830" y="145" text-anchor="middle" font-size="13" font-family="monospace" fill="currentColor">Flagged in tcp_rtx_queue</text>

  <rect x="740" y="170" width="180" height="90" rx="6" fill="#faad14" fill-opacity="0.08" stroke="#faad14" stroke-opacity="0.3"/>
  <text x="830" y="200" text-anchor="middle" font-size="13" font-weight="700" fill="#faad14">RAM Status: FLAGGED</text>
  <text x="830" y="225" text-anchor="middle" font-size="12.5" fill="currentColor">TCPCB_LOST marked</text>
  <text x="830" y="245" text-anchor="middle" font-size="12.5" fill="currentColor">Targeted for Fast Retransmit</text>

  <rect x="740" y="280" width="180" height="195" rx="6" fill="currentColor" fill-opacity="0.03"/>
  <text x="830" y="310" text-anchor="middle" font-size="13.5" font-weight="700" fill="currentColor">Scheduling Priority</text>
  <text x="830" y="335" text-anchor="middle" font-size="14.5" font-weight="800" fill="#ff4d4f">HIGHEST PRIORITY</text>
  <text x="830" y="360" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.8">Jumps ahead of Unsent!</text>
  <text x="830" y="395" text-anchor="middle" font-size="13.5" font-weight="700" fill="currentColor">Kernel Function</text>
  <text x="830" y="420" text-anchor="middle" font-size="12" font-family="monospace" fill="currentColor">tcp_xmit_retransmit()</text>
</svg>

---

## 3. Cumulative ACKs vs. SACK: How Holes Are Detected in In-Flight Data

A fundamental question arises when observing the in-flight boundary (`snd_una`):
> *"If `snd_una = 5000`, and the receiver reports that byte `5300` has arrived, does that leave a hole in the queue? How does the kernel detect missing data without losing track of sequence numbers?"*

The answer depends on whether the connection is using **Standard Cumulative ACKs** or **Selective ACKs (SACK)**:

### 3.1 Standard Cumulative ACKs (RFC 793): Strictly Monotonic, Zero Holes

In the standard TCP header, the 32-bit `Acknowledgment Number` field is **strictly cumulative**:
* When a receiver emits `ACK = 5300`, RFC 793 defines this unambiguously: *"I have received **every single byte up to 5299** without exception. The next byte I expect from you is 5300."*
* If bytes $5000\text{--}5299$ were lost in transit, the receiver is **legally forbidden** from advertising $5300$. Instead, it repeats `ACK = 5000` (a Duplicate ACK).
* Therefore, in standard TCP, an ACK can **never** jump forward and leave a hole in the send queue. The sender simply advances `snd_una` from $5000$ to $5300$, and frees all bytes in between from RAM.

### 3.2 SACK (RFC 2018): Exposing Holes in the In-Flight Window

Standard cumulative ACKs are inefficient across high-speed WAN lines. If 1 packet drops out of 100, standard TCP leaves the sender completely blind to whether the other 99 packets made it through.

**Selective Acknowledgment (SACK)** resolves this by splitting acknowledgment feedback into two channels within the same packet:

```
TCP Packet from Receiver:
┌────────────────────────────────────────────────────────┐
│ Main TCP Header:                                       │
│   ACK = 5000   <-- Cumulative ACK (snd_una CANNOT move!)│
├────────────────────────────────────────────────────────┤
│ TCP Options Header (SACK Block):                       │
│   SACK Range: [5300, 5600]  <-- Received out-of-order  │
└────────────────────────────────────────────────────────┘
```

1. **The Primary Header ACK (`snd_una` boundary):** Remains pinned at the earliest missing byte (`ACK = 5000`).
2. **The TCP Options SACK Blocks:** Carries explicit byte ranges that successfully reached the receiver out of order (e.g., `[5300, 5600]`).

### 3.3 Identifying and Repairing the Hole

When the sender's TCP stack processes this SACK packet:

1. **`snd_una` Stays Pinned at 5000:** Because the cumulative ACK is $5000$, `snd_una` cannot advance. Memory cannot be freed yet.
2. **The Hole is Identified:** The kernel compares the SACK range with `snd_una`:
   * Packets in $[5300, 5600)$ are flagged as `TCPCB_SACKED_ACKED` (confirmed received; do not retransmit).
   * The gap between `snd_una` and the left edge of the SACK block—the range **$[5000, 5300)$**—is officially **The Hole**.
3. **Loss Flagging (`TCPCB_LOST`):** When the SACK scoreboard observes that packets beyond the hole have arrived (or after receiving 3 duplicate ACKs), the kernel flags the packets inside $[5000, 5300)$ as `TCPCB_LOST`.
4. **Fast Retransmit Priority:** As detailed in Section 5 below, the transmission engine immediately re-transmits this missing hole ahead of any fresh unsent data.
5. **Reaping upon Gap Repair:** Once the retransmitted $[5000, 5300)$ segment reaches the receiver, the receiver emits a new cumulative `ACK = 5600`. `snd_una` jumps to $5600$, and the kernel reaps the entire $[5000, 5600)$ range from memory in a single operation.

---

## 4. The Modern Kernel Architecture: Why In-Flight Data Uses a Red-Black Tree

Now that we see how SACK creates arbitrary out-of-order holes across thousands of in-flight packets, consider the operating system engineering challenge: **How should the kernel physically store and search these in-flight packets in host memory?**

Prior to Linux 4.15, the kernel stored all packets—both transmitted and unsent—in a single doubly linked list (`sk->sk_write_queue`). When an ACK arrived, the kernel had to traverse the list linearly ($O(N)$) to find and delete acknowledged packets. On 10GbE lines with thousands of packets in flight, this linear traversal caused severe CPU cache misses and lock contention.

In Linux 4.15+, kernel developer Eric Dumazet redesigned this subsystem into **two physically separate data structures**:

```
[ struct sock ]
       │
       ├──► sk_write_queue  (struct sk_buff_head: Doubly Linked List)
       │    └── Holds ONLY Unsent Data (snd_nxt <= seq < write_seq)
       │
       └──► tcp_rtx_queue   (struct rb_root: Red-Black Tree)
            └── Holds ONLY Transmitted In-Flight Data (snd_una <= seq < snd_nxt)
```

### Why the Red-Black Tree for In-Flight Data?

By indexing in-flight packets inside an augmented **Red-Black Tree (`tcp_rtx_queue`)** ordered by sequence number:
* **$O(\log N)$ SACK Processing:** Finding, verifying, and deleting SACKed segments or identifying holes runs in $O(\log N)$ logarithmic time rather than $O(N)$ linear scans.
* **Decoupled Outbound Queue:** Fresh outbound packets in `sk_write_queue` are completely decoupled from in-flight retransmission accounting.

---

## 5. How the Kernel Schedules the Send Queue

When the network interface card signals that it can transmit more data, how does the kernel choose what to send?

In `net/ipv4/tcp_output.c`, the kernel follows a **strict hierarchical priority order**:

```
                    ┌───────────────────────────────────┐
                    │    NIC Signals Egress Capacity    │
                    └─────────────────┬─────────────────┘
                                      │
                                      ▼
               [ Priority 1: Retransmissions (tcp_rtx_queue) ]
               Are there segments flagged with TCPCB_LOST?
                        │                     │
                       YES                    NO
                        │                     │
                        ▼                     ▼
             [ Transmit Lost Packet ]   [ Priority 2: Unsent Data (sk_write_queue) ]
             Bypasses unsent queue!     Check CWND & RWND limits.
                                        Check TCP_NOTSENT_LOWAT threshold.
                                                 │
                                                 ▼
                                        [ Transmit Fresh Segment ]
                                        Move skb from sk_write_queue
                                        into tcp_rtx_queue. Advance snd_nxt.
```

### Priority 1: Retransmissions (Repairs First!)
If Selective ACKs or a retransmission timeout indicates that a packet was lost on the wire, the kernel **always services retransmissions before transmitting any new unsent data**:
* Function: `tcp_xmit_retransmit_queue()`
* **Why?** Because of [TCP's Head-of-Line blocking](/system/2026/11/08/tcp-hol-blocking.html) contract. The receiver cannot expose *any* subsequent data to the peer application until the missing segment is received. Sending fresh data while a gap exists only wastes receiver buffer space.

### Priority 2: Fresh Outbound Data
If there are no lost packets awaiting retransmission, the transmission loop proceeds to `tcp_write_xmit()`:
1. It inspects the head of `sk_write_queue` (the oldest unsent packet).
2. It verifies that transmitting does not violate:
   * **Congestion Window (`CWND`):** Does the network have capacity?
   * **Receiver Window (`RWND`):** Does the peer have buffer room?
   * **Pacing Rate:** Has the Sch_fq packet scheduler approved the time slot?
3. The NIC driver pulls the packet via DMA, transmits it, and the kernel:
   * Removes the `sk_buff` from `sk_write_queue`.
   * Inserts it into `tcp_rtx_queue`.
   * Increments `snd_nxt` by the packet length.

---

## 6. Why `TCP_NOTSENT_LOWAT` is Mathematically Trivial for the Kernel

Now that the boundary pointers are clear, notice why `TCP_NOTSENT_LOWAT` imposes **virtually zero CPU overhead**:

The kernel does not iterate through arrays or calculate complex queue depths. The volume of unsent data is a single subtraction:

$$
\text{Unsent Bytes} = \text{write_seq} - \text{snd_nxt}
$$

In `include/net/tcp.h`:

```c
static inline u32 tcp_notsent_lowat(const struct tcp_sock *tp)
{
    struct net *net = sock_net((struct sock *)tp);
    return tp->notsent_lowat ?: READ_ONCE(net->ipv4.sysctl_tcp_notsent_lowat);
}

static inline bool tcp_stream_memory_free(const struct sock *sk, int wake)
{
    const struct tcp_sock *tp = tcp_sk(sk);
    u32 notsent_bytes = tp->write_seq - tp->snd_nxt;

    return notsent_bytes < tcp_notsent_lowat(tp);
}
```

* When an application calls `write()` faster than the line rate, `write_seq` pulls away from `snd_nxt`.
* The microsecond `write_seq - snd_nxt >= 16384`, `tcp_stream_memory_free()` returns `false`.
* `epoll` withholds `EPOLLOUT`. The application is paused until the physical wire advances `snd_nxt`.

---

## 7. Summary: The Complete Packet Lifecycle

| Stage | Sequence Range | Physical Location | Kernel Storage | Memory Impact |
| :--- | :--- | :--- | :--- | :--- |
| **1. Unsent** | $[\text{snd_nxt}, \text{write_seq})$ | Local host RAM | `sk_write_queue` (FIFO list) | Contributes to `sk_wmem_alloc`; governed by `TCP_NOTSENT_LOWAT`. |
| **2. In-Flight** | $[\text{snd_una}, \text{snd_nxt})$ | Fiber optic wire / Peer NIC | `tcp_rtx_queue` (RB-Tree) | Retained in RAM for retransmission; governed by `SO_SNDBUF`. |
| **3. Lost / SACK** | Subsets in $[\text{snd_una}, \text{snd_nxt})$ | Dropped in network | `tcp_rtx_queue` (flagged `LOST`) | Prioritized above unsent queue by `tcp_xmit_retransmit_queue()`. |
| **4. ACKed** | $< \text{snd_una}$ | Delivered to peer application | None (Freed) | `sk_buff` returned to slab allocator cache; memory released. |

By decoupling `sk_write_queue` (unsent data) from `tcp_rtx_queue` (in-flight data), modern Linux allows trading systems to hold megabytes of in-flight data on long-distance WAN lines while bounding local unsent queuing latency to microseconds.
