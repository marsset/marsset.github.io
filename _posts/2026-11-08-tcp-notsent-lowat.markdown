---
title: "TCP_NOTSENT_LOWAT: Decoupling Network Throughput from Queuing Latency"
date: 2026-11-08 14:00:00 +0800
categories:
  - system
tags: system linux kernel networking tcp low-latency performance
excerpt: >
  Why high-bandwidth TCP connections destroy tail latency during quote storms, how traditional Linux conflated in-flight capacity with local queue depth, and how TCP_NOTSENT_LOWAT eliminates the bufferbloat penalty for emergency order cancels.
---

In high-throughput, low-latency financial systems—such as cross-region order routing between Chicago (CME) and New York (Carteret/Secaucus), or London (LD4) and Frankfurt (FR2)—engineers face a notorious Catch-22:

1. **To saturate a 10GbE long-haul line**, the TCP sliding window requires a **large send buffer** (e.g., $4\,\text{MB}$ to $16\,\text{MB}$) to keep the fiber pipe full.
2. **To react to market events instantly**, an algorithm requires an **empty send buffer**, so that an emergency order cancellation isn't trapped behind megabytes of backlogged quotes.

Historically, Linux offered only a single knob for both: `SO_SNDBUF`. Setting it large delivered wire-speed throughput but introduced catastrophic **Bufferbloat (缓冲区膨胀)**. Setting it small bound latency to microseconds but caused **Throughput Collapse (吞吐量崩溃)**.

Linux 3.12 resolved this decade-old architectural conflict with **`TCP_NOTSENT_LOWAT`** (RFC 7684). This post breaks down why this socket option is indispensable in modern trading gateways, how it works inside the kernel TCP stack, and how to configure it in production C++ execution engines.

---

## 1. The Mental Model: The Highway and the Warehouse

To understand the core conflict without getting bogged down in TCP state machines, consider a cross-border logistics company shipping goods by truck from **London to Frankfurt**:

* **Propagation Delay ($RTT$):** It takes 10 hours for a truck to drive to Frankfurt, unload, and return the confirmation receipt.
* **Highway Capacity (Bandwidth-Delay Product):** To keep the supply chain running at 100% capacity, you must have **100 trucks moving on the highway simultaneously**. If you only dispatch one truck at a time, the entire highway sits empty for 9.9 hours.

Now, imagine an urgent business emergency occurs:
> *"CEO Alert: Cancel Shipment #401 immediately! A fatal defect was discovered. Send this STOP RECALL order to Frankfurt at once!"*

What happens to that emergency notice depends entirely on how your local distribution center operates:

<svg viewBox="0 0 960 520" width="100%" height="auto" style="max-width:960px;display:block;margin:1.5em auto;display:block; margin: 2rem auto; background: rgba(0,0,0,0.02); border: 1px solid rgba(0,0,0,0.1); border-radius: 12px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <!-- Title Header -->
  <text x="480" y="32" text-anchor="middle" font-size="19" font-weight="800" fill="currentColor">The Dilemma: In-Flight Highway vs. Local Warehouse Queue</text>
  <text x="480" y="54" text-anchor="middle" font-size="13.5" fill="currentColor" fill-opacity="0.65">How Traditional Linux Conflated In-Flight Throughput with Local Backlog</text>

  <!-- Left Column: Traditional Linux (Huge Warehouse) -->
  <rect x="25" y="75" width="440" height="425" rx="10" fill="currentColor" fill-opacity="0.02" stroke="#ff4d4f" stroke-opacity="0.5" stroke-width="2"/>
  <text x="245" y="105" text-anchor="middle" font-size="17" font-weight="800" fill="#ff4d4f">Traditional Linux: SO_SNDBUF Only</text>
  <text x="245" y="127" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.7">One single threshold controls both highway and queue</text>

  <!-- Local Warehouse Box Left -->
  <rect x="45" y="145" width="400" height="155" rx="8" fill="#ff4d4f" fill-opacity="0.08" stroke="#ff4d4f" stroke-opacity="0.3" stroke-width="1.5"/>
  <text x="245" y="170" text-anchor="middle" font-size="14.5" font-weight="700" fill="currentColor">Local Kernel Memory (sk_write_queue)</text>
  
  <rect x="60" y="185" width="370" height="30" rx="4" fill="#ff4d4f" fill-opacity="0.2"/>
  <text x="245" y="205" text-anchor="middle" font-size="13" font-weight="600" fill="currentColor">5,000 Unsent Routine Quotes (4 MB backlog)</text>
  
  <rect x="60" y="222" width="370" height="30" rx="4" fill="#ff4d4f" fill-opacity="0.5" stroke="#ff4d4f" stroke-width="1"/>
  <text x="245" y="242" text-anchor="middle" font-size="13" font-weight="800" fill="#ffffff">TRAPPED: Emergency CancelOrder (Appended at Tail)</text>
  
  <text x="245" y="285" text-anchor="middle" font-size="13" font-weight="700" fill="#ff4d4f">Local Queue Delay: 3,200 µs (3.2 ms)!</text>

  <!-- Consequence Box Left -->
  <rect x="45" y="315" width="400" height="170" rx="8" fill="currentColor" fill-opacity="0.04" stroke="currentColor" stroke-opacity="0.12" stroke-width="1.5"/>
  <text x="245" y="342" text-anchor="middle" font-size="14" font-weight="700" fill="#ff4d4f">Why It Failed</text>
  <text x="245" y="368" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.85">epoll says "Writable!" as long as Memory &lt; 8 MB</text>
  <text x="245" y="394" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.85">App floods memory with speculative updates</text>
  <text x="245" y="420" text-anchor="middle" font-size="14.5" font-weight="800" fill="#ff4d4f">Result: Stale Quotes Filled on Exchange</text>
  <text x="245" y="446" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.75">Cancel arrives 3.2 ms too late</text>


  <!-- Right Column: Modern Linux (TCP_NOTSENT_LOWAT) -->
  <rect x="495" y="75" width="440" height="425" rx="10" fill="currentColor" fill-opacity="0.02" stroke="#52c41a" stroke-opacity="0.6" stroke-width="2.5"/>
  <text x="715" y="105" text-anchor="middle" font-size="17" font-weight="800" fill="#52c41a">Modern Linux: TCP_NOTSENT_LOWAT</text>
  <text x="715" y="127" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.7">Highway capacity decoupled from local waiting room</text>

  <!-- Local Warehouse Box Right -->
  <rect x="515" y="145" width="400" height="155" rx="8" fill="#52c41a" fill-opacity="0.08" stroke="#52c41a" stroke-opacity="0.3" stroke-width="1.5"/>
  <text x="715" y="170" text-anchor="middle" font-size="14.5" font-weight="700" fill="currentColor">Local Kernel Memory (sk_write_queue)</text>
  
  <rect x="530" y="185" width="370" height="30" rx="4" fill="#52c41a" fill-opacity="0.2"/>
  <text x="715" y="205" text-anchor="middle" font-size="13" font-weight="600" fill="currentColor">Bouncer Rule: Max 16 KB Unsent Backlog</text>
  
  <rect x="530" y="222" width="370" height="30" rx="4" fill="#52c41a" fill-opacity="0.45" stroke="#52c41a" stroke-width="1"/>
  <text x="715" y="242" text-anchor="middle" font-size="13" font-weight="800" fill="currentColor">EXPRESS: Emergency CancelOrder (Behind &lt; 16 KB)</text>
  
  <text x="715" y="285" text-anchor="middle" font-size="13" font-weight="700" fill="#52c41a">Local Queue Delay: &lt; 13 µs bounded!</text>

  <!-- Consequence Box Right -->
  <rect x="515" y="315" width="400" height="170" rx="8" fill="currentColor" fill-opacity="0.04" stroke="currentColor" stroke-opacity="0.12" stroke-width="1.5"/>
  <text x="715" y="342" text-anchor="middle" font-size="14" font-weight="700" fill="#52c41a">Why It Succeeds</text>
  <text x="715" y="368" text-anchor="middle" font-size="13.5" font-weight="600" fill="currentColor">Highway: 100% full (8 MB in flight across Europe)</text>
  <text x="715" y="394" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.85">epoll pauses app as soon as unsent bytes hit 16 KB</text>
  <text x="715" y="420" text-anchor="middle" font-size="14.5" font-weight="800" fill="#52c41a">Result: Microsecond Cancel Dispatch</text>
  <text x="715" y="446" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.75">Full 10 Gbps throughput without the bufferbloat</text>
</svg>

### The Two Warehouse Policies

1. **Policy A: The Massive Warehouse (Old Linux with large `SO_SNDBUF`):**
   To keep 100 trucks moving on the highway, you built a massive warehouse holding 500 waiting boxes. When the CEO's emergency notice arrives, it gets placed at the back of the queue behind all 500 boxes. It takes **3 hours** just to exit the loading dock! By the time it arrives in Frankfurt, the wrong goods are already sold.
2. **Policy B: The Lean Warehouse (`TCP_NOTSENT_LOWAT`):**
   You keep 100 trucks moving on the highway, but your warehouse has a strict bouncer: **never allow more than 1 box to wait on the dock**. Whenever a truck pulls out, the bouncer lets the next box in. When the emergency notice arrives, there is only 1 box ahead of it. It exits the loading dock in **seconds**, while the highway remains fully saturated!

---

## 2. The Architectural Flaw in Traditional Linux

Why did traditional Linux create this problem in the first place?

In early TCP implementations, the kernel used a single metric—**total allocated socket memory (`sk_wmem_alloc`)**—to govern two completely unrelated responsibilities:
1. **Network Sliding Window:** How much data TCP is permitted to keep in flight across the physical network pipe before receiving ACKs.
2. **Application Write Readiness:** When `epoll` signals `EPOLLOUT` to tell user-space applications that they may call `write()` or `send()`.

### The Anatomy of the Send Buffer

To see why this was flawed, inspect what is actually inside a TCP socket write queue at any moment:

$$
\text{Total Buffered Data} = \underbrace{\text{In-Flight Bytes}}_{\text{Already on the Wire}} + \underbrace{\text{Unsent Bytes}}_{\text{Idle in Local RAM}}
$$

```
┌────────────────────────────────────────────────────────────────────────┐
│                      Total Socket Memory (SO_SNDBUF)                   │
├───────────────────────────────────────┬────────────────────────────────┤
│       1. In-Flight Bytes (CWND)       │        2. Unsent Bytes         │
│  (Photons flying through fiber optic) │   (Sitting idle in local RAM)  │
│  Already dispatched onto physical wire│   Waiting for NIC to transmit  │
│  ❌ DOES NOT DELAY NEW CANCELS!       │   ⚠️ BLOCKS ALL NEW CANCELS!   │
└───────────────────────────────────────┴────────────────────────────────┘
```

#### Why In-Flight Bytes Do NOT Cause Queue Delay
Bytes that are "in flight" have already exited your network card (NIC). They are literally pulses of light traveling through underground dark fiber between cities. 
When your algorithm calls `send(cancel_order_fd)`, your cancel packet **does not wait for in-flight packets**—it is placed directly on the wire as soon as whatever is waiting *inside local host memory* has cleared!

#### The Source of the Delay: Unsent Bytes
The only packets that delay your emergency cancel order are the **unsent bytes** idling inside local host RAM. 

Under traditional Linux, the socket layer checked:

$$
\text{Writable if: } \text{sk_wmem_alloc} < \text{sk_sndbuf}
$$

If `sk_sndbuf` was set to $8\,\text{MB}$ to support a London–Frankfurt WAN line, the kernel permitted the trading application to dump up to **$8\,\text{MB}$ of speculative, unsent quotes** into `sk_write_queue`. 

When market volatility triggered an emergency cancel:

$$
T_{\text{queue}} = \frac{8 \times 10^6 \times 8 \text{ bits}}{10 \times 10^9 \text{ bps}} = \mathbf{6.4\,\text{ms}}
$$

The cancel sat trapped in local operating system memory for **$6.4\,\text{milliseconds}$** before the NIC could physically touch it!

---

## 3. How `TCP_NOTSENT_LOWAT` Works Under the Hood

Introduced in Linux 3.12 (RFC 7684) by Google network engineers, `TCP_NOTSENT_LOWAT` breaks this coupling by introducing a dedicated threshold for **unsent bytes only**.

### 3.1 The Writable Condition in the Kernel

With `TCP_NOTSENT_LOWAT` enabled, the kernel inspects the unsent queue depth:

$$
\text{Unsent Bytes} = \text{sk_wmem_alloc} - \text{In-Flight Bytes}
$$

In `net/ipv4/tcp_output.c`, the kernel replaces the naive memory check with `tcp_stream_memory_free()`:

```c
/* net/ipv4/tcp_output.c */
static inline bool tcp_stream_memory_free(const struct sock *sk, int wake)
{
    const struct tcp_sock *tp = tcp_sk(sk);
    u32 notsent_bytes = tp->write_seq - tp->snd_nxt;

    /* If unsent bytes exceed TCP_NOTSENT_LOWAT, suppress EPOLLOUT */
    return notsent_bytes < tcp_notsent_lowat(tp);
}
```

Here:
* `tp->write_seq`: The sequence number of the highest byte written by the user application.
* `tp->snd_nxt`: The sequence number of the next byte to be transmitted onto the physical wire by the NIC.
* `tp->write_seq - tp->snd_nxt`: The exact volume of **unsent bytes** sitting in local kernel memory!

### 3.2 The Decoupled Architecture

| Parameter | Metric Governed | Optimal Value in HFT | Consequence |
| :--- | :--- | :--- | :--- |
| **`SO_SNDBUF`** | In-flight window on network | **Large** ($4\,\text{MB} - 16\,\text{MB}$) | Fully saturates physical bandwidth-delay product ($10\text{G}$ wire speed). |
| **`TCP_NOTSENT_LOWAT`** | Unsent queue depth in host RAM | **Small** ($16\,\text{KB} - 32\,\text{KB}$) | Caps local queue delay to $\le 13\,\mu\text{s}$, enabling instant cancels. |

---

## 4. Production Implementation in C++

Configuring `TCP_NOTSENT_LOWAT` requires a single socket option call on an established or connecting TCP socket:

```cpp
#include <sys/socket.h>
#include <netinet/tcp.h>
#include <iostream>
#include <cstring>
#include <unistd.h>

bool configure_low_latency_socket(int fd, uint32_t notsent_lowat_bytes = 16384) {
    // 1. Configure massive send buffer to saturate 10GbE WAN pipeline
    int sndbuf = 8 * 1024 * 1024; // 8MB
    if (setsockopt(fd, SOL_SOCKET, SO_SNDBUF, &sndbuf, sizeof(sndbuf)) < 0) {
        std::cerr << "Failed to set SO_SNDBUF: " << strerror(errno) << "\n";
        return false;
    }

    // 2. Bound unsent local queue depth to 16KB (TCP_NOTSENT_LOWAT)
    if (setsockopt(fd, IPPROTO_TCP, TCP_NOTSENT_LOWAT, 
                   &notsent_lowat_bytes, sizeof(notsent_lowat_bytes)) < 0) {
        std::cerr << "Failed to set TCP_NOTSENT_LOWAT: " << strerror(errno) << "\n";
        return false;
    }

    // 3. Disable Nagle's algorithm (instant dispatch of small packets)
    int nodelay = 1;
    if (setsockopt(fd, IPPROTO_TCP, TCP_NODELAY, &nodelay, sizeof(nodelay)) < 0) {
        std::cerr << "Failed to set TCP_NODELAY: " << strerror(errno) << "\n";
        return false;
    }

    return true;
}
```

### 4.1 System-Wide Global Configuration

Rather than modifying every individual application binary, Linux allows setting a global default via `sysctl`:

```bash
# Set system-wide default threshold to 16KB (16384 bytes)
sudo sysctl -w net.ipv4.tcp_notsent_lowat=16384

# Persist configuration across reboots in /etc/sysctl.d/
echo "net.ipv4.tcp_notsent_lowat = 16384" | sudo tee /etc/sysctl.d/99-tcp-lowat.conf
sudo sysctl --system
```

<div class="notice--info" markdown="1">
**Kernel Priority Rule:** If an application explicitly sets `TCP_NOTSENT_LOWAT` via `setsockopt()`, the socket-level setting overrides the system-wide `net.ipv4.tcp_notsent_lowat` value.
</div>

---

## 5. Production Diagnostics & Verification

How can you prove in production that `TCP_NOTSENT_LOWAT` is actively protecting your gateway from bufferbloat?

### 5.1 Inspecting Active Sockets with `iproute2` (`ss`)

The `ss` utility with the `-ti` (TCP internal info) flag exposes the exact split between in-flight data and unsent bytes:

```bash
ss -ti -H dst 198.51.100.12
```

**Output Breakdown:**

```text
ESTAB 0 16384 10.0.1.50:48292 198.51.100.12:10443
     skmem:(r0,rb131072,t0,tb8388608,f0,w16384,o0,bl0)
     cubic wscale:7,7 rto:200 rtt:4.2/0.05 ato:40 mss:1460 rcvspace:131072
     cwnd:3424 ssthresh:2280 bytes_acked:582910408 segs_out:400291
     notsent:16384 bps:9800000000
```

Notice the key fields:
* `tb8388608`: Total send buffer ceiling ($8\,\text{MB}$).
* `cwnd:3424`: Congestion window permits $\approx 5.0\,\text{MB}$ in flight ($3424 \times 1460$).
* `notsent:16384`: Unsent queue depth is capped tightly at exactly $16\,\text{KB}$.

### 5.2 Real-Time BPF Queue Latency Profiler

To measure the exact microsecond delay experienced by packets waiting in `sk_write_queue`, run this `bpftrace` one-liner:

```bash
sudo bpftrace -e '
kprobe:tcp_write_xmit {
    $sk = (struct sock *)arg0;
    $tp = (struct tcp_sock *)arg0;
    $notsent = $tp->write_seq - $tp->snd_nxt;
    if ($notsent > 0) {
        @notsent_bytes = hist($notsent);
    }
}'
```

**Result on an un-tuned socket (without `TCP_NOTSENT_LOWAT`):**
```text
@notsent_bytes: 
[1K, 2K)             12 |@                                       |
[16K, 32K)           45 |@@@@                                    |
[256K, 512K)        190 |@@@@@@@@@@@@@@@                         |
[2M, 4M)            840 |@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@|  <-- CATASTROPHIC BUFFERBLOAT!
```

**Result on a tuned socket (`TCP_NOTSENT_LOWAT = 16384`):**
```text
@notsent_bytes: 
[0, 4K)            1240 |@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@|
[4K, 8K)            620 |@@@@@@@@@@@@@@@@@@@@                    |
[8K, 16K)           310 |@@@@@@@@@@                              |
[16K, 32K)            0 |                                        |  <-- HARD CEILING AT 16KB!
```

---

## 6. Summary Comparison

| Architectural Trait | Traditional `SO_SNDBUF` Only | Modern `TCP_NOTSENT_LOWAT` (RFC 7684) |
| :--- | :--- | :--- |
| **Decoupling** | Monolithic: in-flight window = local queue size | Decoupled: massive wire window, tiny local queue |
| **WAN Saturation (10G)** | Requires huge buffer ($> 4\,\text{MB}$) | Enabled via huge buffer ($> 4\,\text{MB}$) |
| **Local Host Queuing** | Sits at full buffer capacity ($4\,\text{MB}-16\,\text{MB}$) | Bound to configured threshold ($\le 16\,\text{KB}$) |
| **Emergency Cancel Latency** | **$3{,}200\,\mu\text{s} - 6{,}400\,\mu\text{s}$** ($3.2 - 6.4\,\text{ms}$) | **$< 13\,\mu\text{s}$** |
| **Execution Risk** | Severe: stale quotes filled during volatility | Negligible: order cancels hit the wire instantly |

By setting `TCP_NOTSENT_LOWAT` to $16\,\text{KB}$ alongside a generous `SO_SNDBUF`, low-latency execution systems eliminate the trade-off between throughput and determinism, ensuring that urgent market signals never wait behind a bloated local buffer.
