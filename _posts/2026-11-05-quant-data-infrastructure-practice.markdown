---
title:  "Quantitative Financial Data Infrastructure: Practice Problems"
date:  2026-11-05 10:00:00 +0800
categories:
  - system
tags: system
classes: wide
layout: single
use_math: true
excerpt: >
  fourteen practice problems for a quantitative data infrastructure and financial market data engineer role: ten to talk through, four to code.
---

Fourteen practice problems for a quantitative financial data infrastructure and market data engineer role (focused on high-throughput historical and real-time tick/order-book data pipelines, low-level systems, and replay engines). The first ten are discussion questions covering the pipeline from exchange feed ingestion to historical replay; the last four are coding problems. Only the questions are listed, for self-testing and repeated practice. A good shape for each answer: clarify → framework → detail → metrics → risks.

### 1. The market data pipeline end to end

A high-performance financial data pipeline is often structured as: "feed capture → hardware timestamping → protocol normalization → deduplication & cleaning → order book state reconstruction → columnar compression & cold storage → point-in-time replay & analytics". In your own words: how does a complete quantitative data platform run, what problem does each stage solve, and why is "strict determinism" the single most critical requirement for quantitative research?

**Follow-up:** Exchange feeds (e.g. NASDAQ ITCH, CME MDP 3.0, Binance WebSocket/SBE) deliver both trade ticks and depth updates over UDP multicast or WebSocket. If a research backtest executes against reconstructed historical order books, what subtle discrepancy between historical data replay and live production execution causes the most severe backtest-to-live performance degradation?

### 2. Out-of-order ticks, timestamp drift, and watermarking

Market data packets arrive from multiple exchange matching engines, gateway IPs, and collector nodes. Due to network jitter, route flapping, and clock skew:
1. Packets for the same symbol can arrive slightly out of order (microsecond-to-millisecond interleaving).
2. Exchange matching engine timestamps ($T_{\text{exch}}$) and local network interface card timestamps ($T_{\text{local}}$) may drift.

How do you design a streaming deduplication and reordering engine? How do you define a watermark window $\tau$ to trade off pipeline latency against data completeness? What happens if a packet arrives after the watermark has already advanced?

### 3. L2/L3 order book reconstruction from incremental feeds

Most electronic exchanges do not broadcast the entire limit order book on every price change. Instead, they broadcast periodic full snapshots plus high-frequency incremental delta updates (insert, modify, delete, execute).

How do you design an order book reconstruction engine that:
1. Safely bootstraps state from a snapshot and applies subsequent incremental deltas without race conditions?
2. Detects missing sequence numbers (packet drops) and recovers without corrupting the book?
3. Validates order book integrity in real time (e.g. detecting crossed books where best bid $\ge$ best ask)?

### 4. Time-series compression and memory layouts (AoS vs. SoA)

A financial data platform stores petabytes of historical tick data ($10^9$ to $10^{10}$ events per day across equities, futures, and crypto). Tick records typically consist of `(timestamp_ns, symbol_id, price, size, side, trade_flag, sequence_id)`.
1. How does the choice between **Array of Structures (AoS)** and **Structure of Arrays (SoA)** impact CPU cache line utilization, SIMD vectorization, and query throughput during backtesting scans?
2. Why is general-purpose compression (e.g. gzip, zstd) often suboptimal for tick data? How do specialized time-series encoding algorithms—such as **Gorilla delta-of-delta** for timestamps and **XOR bit-packing** for IEEE 754 floating-point prices—achieve both higher compression ratios and orders-of-magnitude faster decompression?

### 5. Zero-copy I/O and kernel mechanics

When ingesting or serving tens of gigabytes of market data per second per storage node, traditional user-kernel context switching and buffer copying become the primary throughput bottleneck.
1. Compare `read()` / `write()`, `mmap()` with memory-mapped files, and `O_DIRECT` (direct I/O). Under what access patterns does each approach shine, and where does each fail?
2. How does the OS page cache interact with large sequential scans? Why can an unconstrained sequential scan cause "page cache thrashing" that evicts hot working memory, and how do POSIX primitives like `posix_fadvise(..., POSIX_FADV_DONTNEED)` or `madvise(..., MADV_SEQUENTIAL)` mitigate this?

### 6. Concurrency and lock-free data pipelines

In an ultra-low-latency market data pipeline, worker threads must pass millions of ticks per second from network parser threads to order book builders and disk logging writers without locking.
1. Why are standard mutexes and blocking queues (`std::mutex`, `pthread_mutex_t`, Python `queue.Queue`) avoided on hot data paths?
2. Explain the architecture of a **Lock-Free Single-Producer Single-Consumer (SPSC) Ring Buffer**. How do atomic load/store operations, CPU cache-line padding (64 bytes), and acquire-release memory ordering guarantee safe data exchange without mutexes or false sharing?

### 7. Point-in-time correctness, corporate actions, and bias elimination

Quantitative backtesting results are notoriously vulnerable to data leakage and historical biases.
1. **Lookahead Bias & Point-in-Time Correctness:** A company restates its Q3 financial results on November 15th, or an exchange issues a retroactive trade cancellation at 16:05. How must a historical data engine store and version data so that a simulation run at virtual time $T$ sees *only* what was known at $T$?
2. **Survivorship Bias & Corporate Actions:** How do you handle stock splits, reverse splits, dividends, symbol changes, and delistings across decades of daily and intraday data? When should prices be adjusted (backward/forward adjustment) versus kept unadjusted?

### 8. Data quality, anomaly detection, and sanity auditing

Upstream exchange feeds and third-party vendor aggregators occasionally publish corrupted data: flash-crash spikes due to exchange software bugs, dropped multicast packets, phantom trades, or quote stuffing.
1. What automated sanity checks would you run in real time on incoming ticks before committing them to the clean historical lake?
2. How do you distinguish between a genuine market crash (e.g. a sudden sweep eating through 15 depth levels) and an errant tick caused by gateway packet corruption?

### 9. Historical tick replay engine architecture

A core product of a financial data infrastructure team is a **High-Fidelity Tick Replay Engine** that feeds historical market state into strategy algorithms as if running against live markets.
1. In multi-asset backtesting (e.g. cross-venue arbitrage between Binance and CME), ticks arrive asynchronously across different exchanges with independent clocks. How do you coordinate time synchronization across dozens of concurrent feeds?
2. Why is replaying market ticks alone insufficient for realistic maker strategy evaluation? How do you model queue position (FIFO order priority within a price level) and cancellation latency ($\lambda_{\text{ack}} \approx 10\text{–}100\text{ms}$)?

### 10. Multi-asset scaling, partitioning, and schema evolution

A data platform handles heterogeneous asset classes: cash equities, perpetual futures, calendar spreads, and options chains (where thousands of strike/expiry combinations expire and spawn daily).
1. How do you design the storage partitioning strategy (e.g. in a Parquet/Arrow-based data lake) across `(Asset Class, Exchange, Date, Symbol)` to optimize for both broad market-wide scans and single-asset microsecond time-series queries?
2. Exchange protocols update their binary formats periodically (e.g. adding new order flags, nanosecond precision timestamps, or match reason codes). How do you design schema evolution so that historic petabytes do not need full rewriting whenever a schema version updates?

---

### 11. Multi-stream K-way merge of monotonic ticks (coding)

In a market data normalization engine, multiple independent data collectors ingest ticks for the same market session from $K$ parallel feeds. Each feed produces a pre-sorted stream of ticks ordered strictly by timestamp.

Implement a memory-efficient generator/iterator that merges $K$ timestamp-ordered streams into a single globally ordered stream. When timestamps are identical, tie-break stably by sequence ID.

```python
from typing import Iterator, List, NamedTuple

class Tick(NamedTuple):
    timestamp_ns: int
    symbol: str
    price: float
    size: float
    seq_id: int

def merge_k_tick_streams(streams: List[Iterator[Tick]]) -> Iterator[Tick]:
    """
    streams: A list of K iterators, where each iterator yields Ticks in strictly
             non-decreasing order of timestamp_ns.
    yields:  A single merged stream of Ticks, globally ordered by timestamp_ns,
             with ties broken by seq_id.
    """
```

- Total number of streams $K$ can be up to $1,000$. Total ticks $N$ can exceed $10^8$ (cannot load all ticks into memory).
- Time complexity must be $O(N \log K)$.
- Space overhead must be $O(K)$, strictly independent of total ticks $N$.

**Follow-ups:**
1. What happens if an upstream feed stalls or experiences network delay? How does standard min-heap merge block, and how would you incorporate a sliding watermark/timeout to unblock healthy feeds?
2. In C++, how would you implement this using a cache-friendly flat array (loser tree or tournament tree) rather than a pointer-based heap to minimize branch mispredictions and memory indirection?

### 12. Rolling time-window VWAP aggregator (coding)

Volume-Weighted Average Price (VWAP) is a benchmark execution metric defined as:

$$
\text{VWAP} = \frac{\sum (P_i \times V_i)}{\sum V_i}
$$

Implement a streaming rolling VWAP calculator that maintains the VWAP over a sliding time window of $\Delta t$ nanoseconds (e.g. rolling 5 minutes = $300 \times 10^9\text{ ns}$).

```python
from collections import deque
from typing import Optional

class RollingVWAP:
    def __init__(self, window_ns: int):
        """
        window_ns: The sliding time window length in nanoseconds.
        """
        self.window_ns = window_ns
        self.queue = deque()  # stores (timestamp_ns, price, size)
        self.cum_dollar_volume = 0.0
        self.cum_volume = 0.0

    def on_tick(self, timestamp_ns: int, price: float, size: float) -> Optional[float]:
        """
        Ingest a new tick, evict expired ticks older than (timestamp_ns - window_ns),
        and return the current rolling VWAP.
        Returns None if total rolling volume is zero.
        """
```

- Ingestion must achieve $O(1)$ amortized time complexity per tick.
- Floating-point addition and subtraction of millions of ticks can suffer from **catastrophic cancellation** or numerical drift when subtracting expired values from running sums. How do you maintain precision?

**Follow-ups:**
1. What happens when tick timestamps arrive out of order (e.g. timestamp $T_2 < T_1$ due to packet interleaving)? How does this break the FIFO deque assumption, and how would you handle microsecond-level late arrivals?
2. If you need to query VWAP over multiple arbitrary window lengths (1 min, 5 min, 1 hour) concurrently, how would you optimize storage using hierarchical time buckets?

### 13. Lock-free SPSC circular buffer (coding)

Implement the core mechanics of a **Single-Producer Single-Consumer (SPSC)** lock-free circular buffer for streaming fixed-size tick structures between two dedicated threads.

```python
class SPSCQueue:
    def __init__(self, capacity: int):
        """
        capacity: Maximum capacity of the ring buffer (must be a power of 2).
        """
        assert capacity > 0 and (capacity & (capacity - 1)) == 0, "Capacity must be power of 2"
        self.capacity = capacity
        self.mask = capacity - 1
        self.buffer = [None] * capacity
        self.head = 0  # written only by producer
        self.tail = 0  # written only by consumer

    def push(self, item) -> bool:
        """
        Attempt to push an item into the buffer.
        Returns True if successful, False if buffer is full.
        """

    def pop(self):
        """
        Attempt to pop an item from the buffer.
        Returns the item if available, None if buffer is empty.
        """
```

- Explain how bitwise masking `index & (capacity - 1)` replaces expensive modulo operations `% capacity`.
- In a compiled multi-threaded environment (C++ / Rust):
  1. Which variables must be `std::atomic`? What memory orderings (`memory_order_relaxed`, `memory_order_acquire`, `memory_order_release`) should be used on `head` and `tail`?
  2. Why must `head` and `tail` reside on separate CPU cache lines (e.g. `alignas(64)`), and what performance pathology occurs if they share a cache line?

### 14. Floating-point Gorilla XOR compression (coding)

Financial tick prices for a single asset often remain identical or fluctuate by only a few price increments across consecutive updates. Facebook's Gorilla paper (2015) introduced XOR-based floating-point compression for time series.

Given a series of 64-bit IEEE 754 float prices, implement the core XOR delta bit-manipulation logic:

```python
import struct

def float_to_bits(val: float) -> int:
    return struct.unpack('>Q', struct.pack('>d', val))[0]

def count_leading_zeros(val: int, bits: int = 64) -> int:
    if val == 0:
        return bits
    return bits - val.bit_length()

def count_trailing_zeros(val: int, bits: int = 64) -> int:
    if val == 0:
        return bits
    return (val & -val).bit_length() - 1

def encode_price_xor(prev_val: float, curr_val: float) -> tuple:
    """
    Computes the Gorilla XOR difference between prev_val and curr_val.
    Returns:
      - xor_val: Integer representation of (prev_bits ^ curr_bits).
      - is_zero: Boolean, True if curr_val == prev_val (stored as a single '0' bit).
      - leading_zeros: Number of leading zeros in xor_val.
      - trailing_zeros: Number of trailing zeros in xor_val.
    """
```

- When `prev_val == curr_val`, the XOR delta is `0`, requiring only **1 bit** in the compressed output stream.
- When `prev_val != curr_val`, show how storing only the meaningful bits between leading and trailing zeros compresses a 64-bit float into typically 10–18 bits.

**Follow-ups:**
1. Why does fixed-point integer representation (e.g. encoding prices as integer price ticks in cents/micros: `price_ticks = round(price * 10000)`) often outperform floating-point XOR compression for equity and futures markets?
2. How does SIMD vectorization (AVX-512) alter the trade-off between complex bit-level entropy decoding and simpler fixed-width byte packing?
