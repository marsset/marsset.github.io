---
title: "TCP Receive Queue Anatomy"
date: 2026-11-08 16:30:00 +0800
categories:
  - system
tags: system linux kernel networking tcp low-latency performance
excerpt: >
  A sister deep dive into how the Linux kernel handles incoming network traffic: the three-stage queue pipeline (NIC ring, sk_backlog, and sk_receive_queue), out-of-order RB-tree reassembly, receive window sequence pointers, and low-latency HFT tuning traps like GRO, tcp_collapse, and SO_BUSY_POLL.
---

In network systems engineering, the send queue and the receive queue appear symmetrical on paper. In production high-frequency trading (HFT) and market data processing, however, **the receive queue is vastly more dangerous and subtle**.

When sending data, your application controls the schedule: it calls `send()` when it chooses to. 

When receiving market data, **the external world dictates the arrival schedule**. During economic announcements or exchange opening crosses, market data packets hit the physical network interface at **14.88 million packets per second** ($10\,\text{GbE}$ wire rate). 

If your receive pipeline stumbles for even $50\,\mu\text{s}$, inbound packets cascade through multiple kernel buffer layers, triggering cache thrashing, out-of-order reassembly stalls, or kernel buffer pruning (`tcp_collapse`).

This article explores the internal architecture of the Linux TCP receive stack: its multi-tier queue taxonomy, receive window pointer mechanics, out-of-order reassembly, and critical tuning traps for ultra-low latency execution gateways.

---

## 1. The Multi-Tier Queue Architecture

Incoming data does not jump straight from the network wire into `sk_buff` queues accessible by `read()`. It must navigate **three distinct physical and logical queues**:

<svg viewBox="0 0 960 520" width="100%" height="auto" style="max-width:960px;display:block;margin:1.5em auto;background:rgba(0,0,0,0.02);border:1px solid rgba(0,0,0,0.1);border-radius:12px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
  <!-- Title -->
  <text x="480" y="32" text-anchor="middle" font-size="19" font-weight="800" fill="currentColor">The Three-Tier Architecture of the Linux TCP Receive Stack</text>
  <text x="480" y="54" text-anchor="middle" font-size="13.5" fill="currentColor" fill-opacity="0.65">How Incoming Packets Traverse from Physical NIC DMA to User Space Application</text>

  <!-- Tier 1: Hardware NIC Ring Buffer -->
  <rect x="25" y="80" width="285" height="415" rx="8" fill="currentColor" fill-opacity="0.02" stroke="currentColor" stroke-opacity="0.2" stroke-width="1.5"/>
  <rect x="35" y="90" width="265" height="35" rx="6" fill="currentColor" fill-opacity="0.08"/>
  <text x="167" y="113" text-anchor="middle" font-size="15" font-weight="700" fill="currentColor">1. NIC RX Ring Buffer</text>
  <text x="167" y="145" text-anchor="middle" font-size="13" font-family="monospace" fill="currentColor">Hardware / DMA Layer</text>

  <rect x="40" y="165" width="255" height="95" rx="6" fill="currentColor" fill-opacity="0.04" stroke="currentColor" stroke-opacity="0.1"/>
  <text x="167" y="192" text-anchor="middle" font-size="13.5" font-weight="700" fill="currentColor">Mechanism: Circular DMA Ring</text>
  <text x="167" y="217" text-anchor="middle" font-size="12.5" fill="currentColor" fill-opacity="0.75">NIC writes direct to host RAM</text>
  <text x="167" y="238" text-anchor="middle" font-size="12.5" fill="currentColor" fill-opacity="0.75">Governed by ethtool -g (e.g. 4096)</text>

  <rect x="40" y="275" width="255" height="205" rx="6" fill="currentColor" fill-opacity="0.03"/>
  <text x="167" y="302" text-anchor="middle" font-size="13.5" font-weight="700" fill="#ff4d4f">The HFT Latency Risk</text>
  <text x="167" y="328" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.85">Ring Overflow (rx_dropped)</text>
  <text x="167" y="352" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.85">If CPU softirq does not drain</text>
  <text x="167" y="376" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.85">in time, NIC drops at wire speed</text>
  <text x="167" y="415" text-anchor="middle" font-size="13.5" font-weight="700" fill="#52c41a">Mitigation</text>
  <text x="167" y="440" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.85">Expand ring size &amp; SO_BUSY_POLL</text>


  <!-- Tier 2: The Lock Bypass Backlog (sk_backlog) -->
  <rect x="337" y="80" width="285" height="415" rx="8" fill="#faad14" fill-opacity="0.03" stroke="#faad14" stroke-opacity="0.5" stroke-width="2"/>
  <rect x="347" y="90" width="265" height="35" rx="6" fill="#faad14" fill-opacity="0.15"/>
  <text x="479" y="113" text-anchor="middle" font-size="15" font-weight="800" fill="#faad14">2. Socket Backlog Queue</text>
  <text x="479" y="145" text-anchor="middle" font-size="13" font-family="monospace" fill="currentColor">sk-&gt;sk_backlog (Lock Bypass)</text>

  <rect x="352" y="165" width="255" height="95" rx="6" fill="#faad14" fill-opacity="0.08" stroke="#faad14" stroke-opacity="0.3"/>
  <text x="479" y="192" text-anchor="middle" font-size="13.5" font-weight="700" fill="#faad14">When is it Used?</text>
  <text x="479" y="217" text-anchor="middle" font-size="12.5" fill="currentColor">When User Thread locks socket</text>
  <text x="479" y="238" text-anchor="middle" font-size="12.5" fill="currentColor">(sock_owned_by_user == true)</text>

  <rect x="352" y="275" width="255" height="205" rx="6" fill="currentColor" fill-opacity="0.03"/>
  <text x="479" y="302" text-anchor="middle" font-size="13.5" font-weight="700" fill="#faad14">The HFT Latency Risk</text>
  <text x="479" y="328" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.85">Softirq cannot touch main queue</text>
  <text x="479" y="352" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.85">Appends skb to backlog list</text>
  <text x="479" y="376" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.85">Causes massive jitter spikes</text>
  <text x="479" y="415" text-anchor="middle" font-size="13.5" font-weight="700" fill="#52c41a">Mitigation</text>
  <text x="479" y="440" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.85">Zero-copy drain; keep locks fast</text>


  <!-- Tier 3: The Main Receive Queue (sk_receive_queue) -->
  <rect x="650" y="80" width="285" height="415" rx="8" fill="#52c41a" fill-opacity="0.03" stroke="#52c41a" stroke-opacity="0.6" stroke-width="2.5"/>
  <rect x="660" y="90" width="265" height="35" rx="6" fill="#52c41a" fill-opacity="0.15"/>
  <text x="792" y="113" text-anchor="middle" font-size="15" font-weight="800" fill="#52c41a">3. Main Receive Queue</text>
  <text x="792" y="145" text-anchor="middle" font-size="13" font-family="monospace" fill="currentColor">sk-&gt;sk_receive_queue</text>

  <rect x="665" y="165" width="255" height="95" rx="6" fill="#52c41a" fill-opacity="0.08" stroke="#52c41a" stroke-opacity="0.3"/>
  <text x="792" y="192" text-anchor="middle" font-size="13.5" font-weight="700" fill="#52c41a">Ready for Application</text>
  <text x="792" y="217" text-anchor="middle" font-size="12.5" fill="currentColor">In-order, validated TCP payloads</text>
  <text x="792" y="238" text-anchor="middle" font-size="12.5" fill="currentColor">Drained by recv() / read()</text>

  <rect x="665" y="275" width="255" height="205" rx="6" fill="currentColor" fill-opacity="0.03"/>
  <text x="792" y="302" text-anchor="middle" font-size="13.5" font-weight="700" fill="#ff4d4f">The HFT Latency Risk</text>
  <text x="792" y="328" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.85">Bufferbloat &amp; ZeroWindow</text>
  <text x="792" y="352" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.85">Oversized queue adds lag;</text>
  <text x="792" y="376" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.85">Undersized queue forces drops</text>
  <text x="792" y="415" text-anchor="middle" font-size="13.5" font-weight="700" fill="#52c41a">Mitigation</text>
  <text x="792" y="440" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.85">BDP tuning &amp; TCP_QUICKACK</text>
</svg>

---

## 2. The Three Receive Queues in Detail

### 1. Hardware NIC Ring Buffer (`rx_ring`)
* **Physical Location:** Host DRAM mapped into PCIe address space.
* **How it Works:** The network card uses Direct Memory Access (DMA) to write raw packet frames directly into pre-allocated memory buffers without CPU intervention.
* **The HFT Risk:** If the CPU core assigned to the network interrupt is delayed—even for a few microseconds due to cache eviction or kernel scheduling—the circular ring fills up. The NIC has nowhere to DMA the next packet, resulting in hardware drops (`rx_dropped` or `rx_missed_errors`).

### 2. The Socket Backlog Queue (`sk->sk_backlog`)
In Linux network internals, this is one of the least understood sources of tail latency:
* **The Concurrency Problem:** When a packet finishes DMA transfer, the kernel triggers a software interrupt (NAPI / softirq). The softirq needs to validate TCP headers and place the packet into `sk->sk_receive_queue`.
* **The Lock Collision:** What if the user-space trading thread is *already* inside a `recv()` syscall, actively draining the socket? The socket is locked (`sock_owned_by_user(sk) == true`).
* **The Bypass:** The softirq cannot block or wait for the user space thread. Instead, it pushes incoming packets into `sk->sk_backlog`.
* **The Wakeup Penalty:** When the user thread finishes its syscall and calls `release_sock()`, it is forced to process every packet that accumulated in `sk_backlog`. If your thread takes too long parsing market data, `sk_backlog` surges, blowing out your 99.9th percentile latency.

### 3. The Main In-Order Receive Queue (`sk->sk_receive_queue`)
* Holds fully validated, continuous, in-order TCP payload segments.
* When your event loop receives `EPOLLIN`, `sk_receive_queue` is the queue drained by `read()` or `recvmsg()`.

---

## 3. The Out-of-Order Reassembly Tree (`tp->out_of_order_queue`)

What happens when Packet 1 is dropped on the wire, but Packets 2, 3, and 4 arrive safely?

As explained in [TCP Head-of-Line Blocking](/system/2026/11/08/tcp-hol-blocking.html), the kernel is legally forbidden from handing Packets 2, 3, and 4 to user space. 

Instead, the kernel stores out-of-order packets in an internal **Red-Black Tree** ordered by sequence number (`tp->out_of_order_queue`):

```
                                [ tp->out_of_order_queue ]
                                   (Augmented RB-Tree)
                                          │
                        ┌─────────────────┴─────────────────┐
                        ▼                                   ▼
              [ Packet 2: seq 2000 ]               [ Packet 4: seq 4000 ]
                        │
                        ▼
              [ Packet 3: seq 3000 ]
```

### The Reassembly Avalanche
When the sender retransmits the missing Packet 1 (sequence 1000):
1. The receiver verifies that Packet 1 fills the missing sequence gap.
2. The kernel initiates an **in-memory reassembly traversal**: it walks `out_of_order_queue`, merges adjacent contiguous buffers, unlinks them from the RB-tree, and enqueues them all into `sk_receive_queue`.
3. In a volatile market with packet loss, this reassembly process burns significant CPU cycles in softirq context, stalling the consumer thread.

---

## 4. Sequence Pointers on the Receive Side

Just as the send queue is bounded by pointers, the receive stack tracks state using four core 32-bit sequence boundaries:

$$
\text{copied_seq} \le \text{rcv_wup} \le \text{rcv_nxt} \le \text{Right Edge } (\text{rcv_wup} + \text{rcv_wnd})
$$

```
0              copied_seq        rcv_wup                 rcv_nxt             rcv_wup + rcv_wnd
├───────────────────┼───────────────┼───────────────────────┼────────────────────────┤
│  Read by App      │ ACKed to peer,│ Un-ACKed packets      │ Remaining allowance    │
│  (Freed by user)  │ not read yet  │ arrived from wire     │ sender can still emit  │
└───────────────────┴───────────────┴───────────────────────┴────────────────────────┘
                    ▲                                       ▲
                    │ ◄────── In Receive Queue ───────────► │
                    │        (Unread Backlog in RAM)        │
                    │                                       │
                                    ▲                                                ▲
                                    │ ◄────────── Advertised Window (rcv_wnd) ─────► │
                                    │   (Promised to sender at last ACK: rcv_wnd)    │
```

### 1. `copied_seq` (Application Read Pointer)
* **What it is:** The sequence number up to which user-space application code has read data via `read()` or `recvmsg()`.
* **The Boundary:** Everything to the left ($< \text{copied_seq}$) has been copied to user-space buffers and reaped from kernel memory.

### 2. `rcv_wup` (Receive Window Update Pointer)
* **What it is:** The sequence number acknowledged the **last time an ACK packet was actually transmitted** to the sender.
* **Why it is NOT simply `rcv_nxt`:** Packets arrive continuously from the wire, advancing `rcv_nxt`. However, ACKs are not emitted on every byte (e.g., Delayed ACK or packet coalescing). `rcv_wup` serves as the historical anchor of what the sender currently knows.

### 3. `rcv_nxt` (Receive Next Expected Byte)
* **What it is:** The next sequence number expected from the physical wire.
* **The In-Memory Backlog:** The total volume of unread packets sitting in `sk_receive_queue` is:
  $$\text{Unread Backlog} = \text{rcv_nxt} - \text{copied_seq}$$
* **Un-ACKed Inbound Data:** The bytes that have physically arrived in host RAM but have not yet been acknowledged back to the peer:
  $$\text{Un-ACKed Data} = \text{rcv_nxt} - \text{rcv_wup}$$

### 4. `rcv_wup + rcv_wnd` (The Advertised Right Edge)
* **What it is:** The absolute sequence ceiling that the sender is legally permitted to transmit without stalling.
* **The Sender's Remaining Budget:** The volume of data the sender is still permitted to emit before hitting the window limit:
  $$\text{Remaining Allowance} = (\text{rcv_wup} + \text{rcv_wnd}) - \text{rcv_nxt}$$
* **The Golden Rule of Window Updates:** The kernel compares $\text{rcv_nxt} + \text{free_space}$ against $\text{rcv_wup} + \text{rcv_wnd}$. It sends a window update only when the right edge can advance by at least 1 MSS or half the receive buffer, preventing Silly Window Syndrome (SWS) and illegal window shrinking.

---

## 5. Low-Latency HFT Tuning Traps

In high-frequency trading gateways, several default Linux kernel mechanisms designed for high throughput become severe tail-latency liabilities on the receive path:

### 1. The `tcp_collapse()` Catastrophe
When memory usage exceeds `sk_rcvbuf`, the Linux kernel does not immediately drop packets. Instead, it enters **Emergency Buffer Collapse ([`tcp_collapse()`](/system/2026/11/09/tcp-collapse.html))**:
* It walks all `sk_buff`s in `sk_receive_queue` and `out_of_order_queue`.
* It re-allocates memory and copies smaller chunks into contiguous larger buffers to eliminate slab allocator padding and header overhead.
* **Impact:** In trading systems, `tcp_collapse()` can lock the socket and freeze the CPU core for **hundreds of microseconds to milliseconds**, occurring exactly during a market burst when latency matters most!

### 2. Disable Generic Receive Offload (GRO / LRO)
Modern NICs use Generic Receive Offload (GRO) to bundle multiple incoming TCP packets into a single giant $64\,\text{KB}$ `sk_buff` before passing it to the kernel.
* **Why it destroys HFT:** To bundle packets, the NIC driver must introduce a small artificial delay to wait for subsequent packets to arrive.
* **Fix:** In ultra-low latency setups, disable GRO and LRO immediately:
  ```bash
  sudo ethtool -K eth0 gro off lro off
  ```

### 3. Eliminate Interrupt Jitter with `SO_BUSY_POLL`
Traditional packet delivery relies on hardware interrupts $\to$ NAPI softirq scheduling $\to$ context switch to user thread. This introduces $2\,\mu\text{s}$ to $10\,\mu\text{s}$ of unpredictable jitter.

By configuring `SO_BUSY_POLL`, the user-space thread spins directly on the device driver queue, draining packets the nanosecond DMA finishes:

```cpp
int busy_poll_us = 50; // Poll for 50 microseconds
if (setsockopt(fd, SOL_SOCKET, SO_BUSY_POLL, &busy_poll_us, sizeof(busy_poll_us)) < 0) {
    perror("setsockopt SO_BUSY_POLL");
}
```

---

## 6. Summary Comparison: Send Queue vs. Receive Queue

| Dimension | Send Queue (`sk_write_queue`) | Receive Queue (`sk_receive_queue`) |
| :--- | :--- | :--- |
| **Pace Dictator** | Local Application CPU (Controlled) | External Exchange Wire (Uncontrolled) |
| **Primary Data Structure** | Linked List (Unsent) + RB-Tree (In-Flight) | Linked List (In-Order) + RB-Tree (Out-of-Order) |
| **Contention Queue** | None (Serial writes) | **`sk_backlog`** (Softirq vs. User Thread Lock) |
| **Primary Latency Threat** | Local Bufferbloat ($3.2\,\text{ms}$ cancel delay) | **`tcp_collapse`** & NIC Ring Drops |
| **Key Tuning Lever** | `TCP_NOTSENT_LOWAT` | `SO_BUSY_POLL` & GRO disabling |

By understanding how incoming packets transition from the hardware ring buffer to `sk_backlog` and `sk_receive_queue`, systems engineers can eliminate kernel lock contention and protect critical market feeds from tail latency spikes.
