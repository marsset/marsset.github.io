---
title:  "Financial Tick Storage"
date:  2026-11-05 11:30:00 +0800
categories:
  - system
tags: system database architecture time-series memory-management
excerpt: >
  analyzing why general-purpose columnar formats like parquet fall short for high-throughput tick replay, and how pax hybrid layouts, kdb+, and dolphindb resolve the row-stitching penalty, decompression bottlenecks, and page cache thrashing.
---

In enterprise data engineering and cloud analytics, **Apache Parquet** (and its sister format **Apache ORC**) is the undisputed industry standard. It delivers remarkable compression ratios, powers distributed SQL engines like Trino, ClickHouse, and Spark, and minimizes AWS S3 storage bills through columnar projection and dictionary encoding.

Yet, step onto a quantitative trading desk or an automated market-making team, and you will notice a glaring paradox: **production tick replay engines and high-frequency backtesters almost never consume raw Parquet files directly**. Instead, trading infrastructure teams build bespoke binary flat files, license proprietary time-series systems like **KDB+/q** and **DolphinDB**, or construct specialized **PAX (Partition Attributes Across)** chunked formats.

Why does a format that dominates petabyte-scale data lakes fail so decisively when feeding quantitative strategy models? 

The answer lies in the fundamental mechanical conflict between **distributed batch OLAP** and **event-driven quantitative execution**, governed by CPU L1/L2 cache behavior, decompression instruction budgets, and OS page cache dynamics.

---

## 1. The Two Opposing Quant Workloads

To understand storage design, one must first isolate the two contrasting access patterns that stress quantitative storage tiers:

```
+--------------------------------------------------------------------------------------------------+
|                                The Quantitative Workload Dualism                                 |
|                                                                                                  |
|   Workload A: High-Throughput Strategy Replay           Workload B: Sub-Millisecond Point Slice  |
|   ------------------------------------------           ----------------------------------------  |
|   • Monotonic full-day sequential scan                 • Microsecond-to-minute window extraction |
|   • Volume: 10^8 - 10^10 events (100s of GBs)          • Example: L2 book +/- 5m around 14:02:15 |
|   • Access pattern: Sequential, streaming              • Access pattern: Sparse, random seek     |
|   • Metric: Sustained throughput (GB/s)                • Metric: Latency (< 500 us, zero warmup) |
|   • Model consumes: Full coherent event tuples         • Model consumes: Full state snapshots    |
+--------------------------------------------------------------------------------------------------+
```

* **Workload A (Tick-by-Tick Strategy Replay):** A backtesting algorithm models an execution strategy across an entire trading day. It behaves as an **event-driven state machine**, stepping through time tick-by-tick. For each event, the strategy logic requires the coherent order book update or trade record: `(timestamp, symbol_id, price, size, side, depth_levels)`.
* **Workload B (Sub-Millisecond Point Slicing):** A researcher investigating an anomalous price jump or training a localized microstructure model needs an order book slice surrounding a specific timestamp (e.g., $\pm 5$ minutes around `14:02:15`). The query must locate, decompress, and return several megabytes of data without scanning unrelated historical hours.

General-purpose columnar formats were engineered for a third, completely different workload: **broad analytical aggregation over subset columns** (e.g., `SELECT avg(price) FROM trades WHERE date = 20261105`). When subjected to Workloads A and B, general-purpose columnar engines break down across four architectural battlegrounds.

---

## 2. Battleground 1: Layout Models & The "Row-Stitching" Penalty

The classic literature on database storage divides physical formats into two primary camps: the **N-ary Storage Model (NSM)** and the **Decomposition Storage Model (DSM)**.

### NSM (Row-Store) vs. DSM (Column-Store)

```
N-ary Storage Model (NSM / Row Store):
+------------------------------------+------------------------------------+
| Tick 0: [Time | Sym | Price | Size]| Tick 1: [Time | Sym | Price | Size]|
+------------------------------------+------------------------------------+
-> Ideal for row reconstruction; terrible for compression & column filtering.

Decomposition Storage Model (DSM / Pure Columnar / Parquet RowGroup):
+-----------------------+-----------------------+-----------------------+
| Column Time: [T0, T1] | Column Price:[P0, P1] | Column Size: [S0, S1] |
+-----------------------+-----------------------+-----------------------+
-> Ideal for scanning single attributes; devastating for row reconstruction.
```

In DSM (Parquet, Arrow, ORC), each column is encoded and stored in separate, contiguous arrays within a large **RowGroup** (typically 128 MB to 512 MB). 

When an OLAP database calculates an average price, DSM is optimal: the CPU pulls only the `Price` column vector into cache, ignoring all other attributes. Memory bandwidth efficiency approaches $100\%$.

However, in **Workload A**, the quant backtesting model cannot consume isolated column vectors; it requires a complete `Tick` structure to evaluate whether a simulated order fills. To feed the model, the execution engine must perform **Tuple Reconstruction (Row Stitching)**:

$$\text{Tick}_i = \left( \text{Time}[i],\, \text{Sym}[i],\, \text{Price}[i],\, \text{Size}[i],\, \text{Side}[i],\, \dots \right)$$

### The Cacheline Transposition Stall

If an L2 tick record consists of 20 fields (timestamps, price levels, volumes, order counts), assembling row $i$ requires reading memory from **20 distinct, spatially distant memory regions**. 

Because each column array is megabytes in size, their memory addresses reside on completely different 4 KB virtual pages and 64-byte hardware cachelines:
1. Fetching $\text{Time}[i]$ loads a 64-byte cacheline holding times $i \dots i+7$.
2. Fetching $\text{Price}[i]$ evicts or competes in the L1/L2 CPU cache to load a separate cacheline holding prices $i \dots i+7$.
3. By the time row $i$ is fully stitched, the CPU has performed 20 independent cache lookups across separate memory streams.

This phenomenon is known as the **Transposition Stall**: the CPU spends up to $70\%$ of its cycles waiting on memory bus arbitration and cache line refills, failing to exploit spatial prefetching.

### The PAX Alternative (Partition Attributes Across)

To eliminate the row-stitching stall while retaining columnar compression, high-performance engines turn to **PAX**, first formalized by Ailamaki et al. (VLDB 2001):

<svg viewBox="0 0 860 310" xmlns="http://www.w3.org/2000/svg" style="max-width:860px;display:block;margin:1.5em auto;width:100%; height:auto; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <!-- Background -->
  <rect width="860" height="310" rx="8" fill="currentColor" fill-opacity="0.03" stroke="currentColor" stroke-opacity="0.15" stroke-width="1"/>
  
  <!-- Container Header -->
  <text x="20" y="32" font-size="14" font-weight="700" fill="currentColor" fill-opacity="0.9">PAX (Partition Attributes Across) 2 MB Physical Chunk Layout</text>
  <text x="20" y="50" font-size="12" fill="currentColor" fill-opacity="0.6">Maintains columnar layout strictly WITHIN fixed cache-sized chunks (e.g. 65,536 ticks per chunk)</text>

  <!-- Chunk Box -->
  <rect x="20" y="70" width="820" height="215" rx="6" fill="currentColor" fill-opacity="0.04" stroke="currentColor" stroke-opacity="0.3" stroke-width="1.5" stroke-dasharray="none"/>
  
  <!-- Chunk Header -->
  <rect x="35" y="85" width="120" height="185" rx="4" fill="currentColor" fill-opacity="0.12" stroke="currentColor" stroke-opacity="0.4" stroke-width="1"/>
  <text x="95" y="115" font-size="12" font-weight="700" text-anchor="middle" fill="currentColor">Chunk Header</text>
  <text x="95" y="140" font-size="11" text-anchor="middle" fill="currentColor" fill-opacity="0.7">• Magic &amp; CRC32</text>
  <text x="95" y="160" font-size="11" text-anchor="middle" fill="currentColor" fill-opacity="0.7">• T_min / T_max</text>
  <text x="95" y="180" font-size="11" text-anchor="middle" fill="currentColor" fill-opacity="0.7">• Row Count (64K)</text>
  <text x="95" y="200" font-size="11" text-anchor="middle" fill="currentColor" fill-opacity="0.7">• Col Offsets</text>
  <text x="95" y="235" font-size="10" text-anchor="middle" fill="currentColor" fill-opacity="0.5">Fixed 512B Block</text>

  <!-- Column mini-blocks -->
  <rect x="170" y="85" width="150" height="185" rx="4" fill="currentColor" fill-opacity="0.08" stroke="currentColor" stroke-opacity="0.3" stroke-width="1"/>
  <text x="245" y="115" font-size="12" font-weight="700" text-anchor="middle" fill="currentColor">Timestamp Col</text>
  <text x="245" y="140" font-size="11" text-anchor="middle" fill="currentColor" fill-opacity="0.7">Gorilla Delta-of-Delta</text>
  <text x="245" y="165" font-size="11" text-anchor="middle" fill="currentColor" fill-opacity="0.7">Dense Bit-Packing</text>
  <text x="245" y="235" font-size="10" text-anchor="middle" fill="currentColor" fill-opacity="0.5">~32 KB Compressed</text>

  <rect x="335" y="85" width="150" height="185" rx="4" fill="currentColor" fill-opacity="0.08" stroke="currentColor" stroke-opacity="0.3" stroke-width="1"/>
  <text x="410" y="115" font-size="12" font-weight="700" text-anchor="middle" fill="currentColor">Price Column</text>
  <text x="410" y="140" font-size="11" text-anchor="middle" fill="currentColor" fill-opacity="0.7">Fixed-Point int64</text>
  <text x="410" y="165" font-size="11" text-anchor="middle" fill="currentColor" fill-opacity="0.7">XOR / FoR Packing</text>
  <text x="410" y="235" font-size="10" text-anchor="middle" fill="currentColor" fill-opacity="0.5">~48 KB Compressed</text>

  <rect x="500" y="85" width="150" height="185" rx="4" fill="currentColor" fill-opacity="0.08" stroke="currentColor" stroke-opacity="0.3" stroke-width="1"/>
  <text x="575" y="115" font-size="12" font-weight="700" text-anchor="middle" fill="currentColor">Size Column</text>
  <text x="575" y="140" font-size="11" text-anchor="middle" fill="currentColor" fill-opacity="0.7">Integer Bit-Packing</text>
  <text x="575" y="165" font-size="11" text-anchor="middle" fill="currentColor" fill-opacity="0.7">Frame-of-Reference</text>
  <text x="575" y="235" font-size="10" text-anchor="middle" fill="currentColor" fill-opacity="0.5">~32 KB Compressed</text>

  <rect x="665" y="85" width="160" height="185" rx="4" fill="currentColor" fill-opacity="0.08" stroke="currentColor" stroke-opacity="0.3" stroke-width="1"/>
  <text x="745" y="115" font-size="12" font-weight="700" text-anchor="middle" fill="currentColor">Side &amp; Flags Col</text>
  <text x="745" y="140" font-size="11" text-anchor="middle" fill="currentColor" fill-opacity="0.7">Byte / Bit Vectors</text>
  <text x="745" y="165" font-size="11" text-anchor="middle" fill="currentColor" fill-opacity="0.7">SIMD Maskable</text>
  <text x="745" y="235" font-size="10" text-anchor="middle" fill="currentColor" fill-opacity="0.5">~8 KB Compressed</text>
</svg>

Under PAX, data is partitioned horizontally into small, fixed-size chunks (e.g., 2 MB, perfectly aligning with CPU HugePages and NVMe flash blocks). Within that 2 MB chunk, attributes are stored columnarly. 

When a backtester reads a PAX chunk:
* The entire chunk fits cleanly into CPU L2/L3 cache ($256\text{ KB} - 2\text{ MB}$).
* Transposition happens entirely inside high-speed CPU SRAM, eliminating memory bus stalls.
* Vectorized SIMD filters can scan the `Side` column at 20 GB/s before reconstructing only the matching rows.

---

## 3. Battleground 2: Codecs & The CPU Decompression Choke Point

Storage formats are fundamentally a trade-off between **compression ratio** (reducing disk space) and **CPU decode throughput** (maximizing computational bandwidth).

### The Parquet Dilemma: Heavy General Compressors

Parquet relies on general-purpose byte-stream compressors—primarily **Snappy**, **Gzip**, or **zstd**:
* **Compression Ratio:** Excellent. Zstd level 3 can compress raw market depth by $6\times$ to $12\times$.
* **Decompression Speed:** Catastrophic for real-time replay. Standard `zstd` decompressors process roughly **$400 - 800\text{ MB/s}$ per core**.

Consider a modern storage node equipped with a single PCIe 4.0 NVMe SSD capable of $6.5\text{ GB/s}$ sequential read bandwidth:

$$\text{Required Core Count} = \frac{6500\text{ MB/s}}{600\text{ MB/s/core}} \approx 11\text{ dedicated CPU cores}$$

Just to decompress the disk stream at hardware line-rate, you must burn **11 full CPU cores purely on decompressor loops**, leaving insufficient CPU budget for the actual quant backtest or strategy signal evaluation. The backtest becomes strictly **CPU-decompression bound**.

### Domain-Specific Quant Codecs: Speed Over Everything

Quantitative time-series data exhibits structural properties that general byte compressors fail to exploit natively without expensive entropy models:

| Field | Numerical Property | Optimal Quant Codec | Decompress Throughput |
| :--- | :--- | :--- | :--- |
| **`timestamp_ns`** | Monotonically increasing; delta between ticks is clustered (e.g. 5ms, 10ms, or exchange heartbeat). | **Gorilla Delta-of-Delta Encoding** | $3.5\text{ GB/s}$ |
| **`price`** | IEEE 754 float; adjacent ticks share high-order exponent and mantissa bits. Or fixed-point `int64`. | **XOR Bit-Packing** / **Frame-of-Reference (FoR)** | $4.2\text{ GB/s}$ |
| **`size` / `volume`** | Small integers; clustered around round lots (1, 10, 100). | **Bit-Packing** (e.g. FastPFor / Simple8b) | $5.0+\text{ GB/s}$ |
| **`side` / `flags`** | Low-cardinality boolean / enum (Buy=1, Sell=2). | **Dense Bitsets** (packed uint64 words) | $15.0+\text{ GB/s}$ (SIMD) |

By avoiding dictionary searches and complex Huffman/FSE tree traversals, these codecs map directly onto hardware primitive instructions (bitwise shifts, bitwise XOR, popcount, leading-zero counts, and SIMD vector lanes).

#### 1. Timestamps: Gorilla Delta-of-Delta Encoding

In high-frequency feeds, timestamps $t_0, t_1, \dots, t_n$ increase monotonically. While first-order deltas $D_i = t_i - t_{i-1}$ reduce magnitude, they still require 16 to 32 bits due to occasional inter-tick gaps. However, because exchange matching engines process events in micro-bursts or emit heartbeats at regular cadence (e.g., exactly 10ms or 100ms intervals), the **second-order delta (delta-of-delta)**:

$$\Delta_i = D_i - D_{i-1} = (t_i - t_{i-1}) - (t_{i-1} - t_{i-2})$$

is predominantly **zero**, or tightly clustered within a small integer neighborhood $[-63, 64]$.

The Gorilla codec (originating from Pelkonen et al., Facebook 2015) uses a variable-length bit-prefix scheme optimized for branch-predictor efficiency:

```
Gorilla Timestamp Bit Stream:
-------------------------------------------------------------------------------------
Case 1: Delta-of-Delta is 0
[0]                                             --> 1 bit total (heartbeat / regular tick)

Case 2: Delta-of-Delta in [-63, 64]
[10] [7-bit signed value]                       --> 9 bits total

Case 3: Delta-of-Delta in [-255, 256]
[110] [9-bit signed value]                      --> 12 bits total

Case 4: Delta-of-Delta in [-2047, 2048]
[1110] [12-bit signed value]                    --> 16 bits total

Case 5: Large Delta Jump
[1111] [32-bit signed value]                    --> 36 bits total
-------------------------------------------------------------------------------------
```

* **Why it hits $3.5\text{ GB/s}$:** When processing steady book activity or timer heartbeats, the CPU executes a single branch test and bit-shift per element. Decompression requires only two additions: $D_i = D_{i-1} + \Delta_i$, followed by $t_i = t_{i-1} + D_i$. In vectorized engines, delta-of-delta streams can be pre-parsed into 64-element batches and reconstructed using SIMD prefix-sum operations (`_mm256_add_epi64`).

#### 2. Prices: XOR Bit-Packing & Fixed-Point Frame-of-Reference (FoR)

Floating-point numbers in IEEE 754 format (`float64`) are notoriously hostile to general byte-stream compressors because fractional price changes flip the low-order mantissa bits, causing byte-boundary entropy to spike.

However, adjacent market quotes (e.g., $64,321.10$ and $64,321.15$) share identical sign bits, identical exponents, and identical high-order mantissa bits. Taking the bitwise XOR of their 64-bit binary representations (via `std::bit_cast<uint64_t>`):

$$X_i = \text{bits}(P_i) \oplus \text{bits}(P_{i-1})$$

the resulting 64-bit integer $X_i$ contains a massive sequence of **leading zeros** (from unchanged high bits) and **trailing zeros** (from unchanged fractional increments).

```
IEEE 754 Float64 XOR Pattern:
P[i-1] : 0 10000001111 1111101101000001010000000000000000000000000000000000 (64321.10)
P[i]   : 0 10000001111 1111101101000001011000000000000000000000000000000000 (64321.15)
---------------------------------------------------------------------------------------------
XOR    : 0 00000000000 0000000000000000001000000000000000000000000000000000
         |------------------------------|--|--------------------------------|
             31 Leading Zeros           2b         31 Trailing Zeros
```

The XOR encoding algorithm executes as follows:
1. **$X_i = 0$ (Price unchanged):** Store a single `0` bit. (In L2 book updates where size changes but price holds, this compresses price to **1 bit**).
2. **$X_i \neq 0$:** Store control bit `1`.
   * **If $X_i$ falls within the same leading/trailing zero bounds as $X_{i-1}$:** Store control bit `0`, followed immediately by only the meaningful bits between the bounds.
   * **If the bounds change:** Store control bit `1`, followed by 5 bits encoding the leading zero count, 6 bits encoding the length of the meaningful window, and then the meaningful payload bits.

* **Fixed-Point Frame-of-Reference (FoR) Alternative:** If prices are stored as scaled integers (e.g., cents or Satoshi ticks: $P_{\text{int}} = \text{round}(P \times 10^k)$), a quant engine uses **Frame-of-Reference (FoR)** over 64-element blocks:
  $$P_{\text{stored}}[i] = P_{\text{int}}[i] - P_{\min}$$
  Since $P_{\max} - P_{\min}$ within a 64-tick micro-burst is rarely more than a few ticks (e.g. $\le 15$ ticks), all 64 values fit into a compact 4-bit bit-width. Unpacking is a single AVX2 bit-shift and addition with the broadcasted baseline $P_{\min}$, achieving **$4.2\text{ GB/s}$ throughput**.

#### 3. Sizes & Volumes: Bit-Packing (FastPFor / Simple-8b)

Order book quantities and trade volumes are small positive integers clustered around standardized lot sizes ($1, 5, 10, 100$). However, market data occasionally experiences large institutional block orders (e.g., $50,000$ shares), creating an extreme outlier distribution that would inflate normal integer bit-packing.

Quant formats resolve this using two complementary techniques:

* **Simple-8b:** Packs a fixed 64-bit machine word with a **4-bit selector** and **60 payload bits**. The 4-bit selector encodes one of 16 predefined integer packing configurations:
  * Selector `0`: 240 0-bit integers (run-length encoded zeros).
  * Selector `1`: 60 1-bit integers ($\in [0, 1]$).
  * Selector `2`: 30 2-bit integers ($\in [0, 3]$).
  * Selector `3`: 20 3-bit integers ($\in [0, 7]$).
  * ...
  * Selector `14`: 1 60-bit integer.
  
  Decompression executes through a branchless 16-entry direct jump table or unrolled switch statement, unpacking directly into output vectors with zero branch mispredictions.

* **FastPFor (Patched Frame of Reference):** Divides integers into blocks of 128 or 256 numbers. Instead of sizing bit-width to the absolute maximum outlier, it picks a bit-width $b$ that satisfies **$95\%-99\%$ of values** (e.g. $b = 4$ bits for values $\le 15$). The rare outliers that exceed $2^b - 1$ have their lower $b$ bits stored in the primary array, while their overflow bits and entry indices are "patched" into a secondary buffer.
  
  During replay, the primary stream is unpacked via SIMD vector instructions (`_mm256_maskz_compress_epi32` or bit-shift shuffles) at **$5.0+\text{ GB/s}$**, and the patch list is applied in a tight post-processing loop.

#### 4. Side & Order Flags: Dense Bitsets & SIMD Packed Words

Every trade or depth event contains categorical flags:
* `side`: Binary (`0` = Ask / Sell, `1` = Bid / Buy).
* `flags`: Small bitfields (e.g. Maker vs. Taker, Aggressor side, Continuous vs. Auction trade, Top-of-Book update).

In generic formats or unoptimized C++ structs, engineers often represent these using `bool` (1 byte) or `enum class` (4 bytes). This produces catastrophic cache waste: storing a boolean in a 1-byte field discards **$87.5\%$ of memory bus bandwidth** on empty padding.

Quant storage engines collapse categorical flags into **Dense Bitsets** (packed `uint64_t` words):
* **64 consecutive trades** are stored in a single 8-byte scalar word.
* A single 512-bit AVX-512 vector register (`__m512i`) holds the side and flags of **512 consecutive market events**.

When an alpha strategy evaluates conditional filters—such as *“compute VWAP over buyer-initiated aggressor trades”*—the engine performs SIMD bitwise masks:

```cpp
// Evaluate 512 trade sides in a single CPU cycle:
__m512i buy_mask = _mm512_cmpeq_epu64_mask(side_vec, _mm512_set1_epi64(1));
__m512d filtered_vol = _mm512_maskz_loadu_pd(buy_mask, &sizes[i]);
```

Because zero bit-unpacking or decompression logic is required beyond bitwise masking and population counts (`__builtin_popcountll`), throughput exceeds **$15.0+\text{ GB/s}$**, operating at CPU L1 cache and register speeds.

By utilizing SIMD instructions (AVX2 / AVX-512), integer bit-unpacking and delta additions execute in **sub-nanosecond cycles per element**. A single thread can achieve **$3.5 - 5.0\text{ GB/s}$ decompression throughput**, allowing a strategy engine to saturate NVMe line rate on a single core.

---

## 4. Battleground 3: Read Amplification in Point Slicing

When an alpha researcher queries **Workload B** (*“give me L2 book ticks between 14:00:00 and 14:05:00”*), storage format geometry dictates I/O amplification:

```
Parquet RowGroup (128 MB):
[================================================================================]
         | 2 MB Target Window |
         v                    v
[........|XXXXXXXXXXXXXXXXXXXX|..................................................]
-> Read Amplification: Must fetch & parse entire 128 MB RowGroup (64x Amplification!)

Chunked PAX with Sparse Index:
[Chunk 0: 2MB] [Chunk 1: 2MB] [Chunk 2: 2MB] ... [Chunk N: 2MB] | Index Footer |
                              |-------------|                   |--------------|
                              Only read 4MB                     In-Memory RAM
-> Read Amplification: ~ 1.05x
```

### Why Parquet Suffers $60\times$ Read Amplification
1. **RowGroup Sizing:** To optimize cloud S3 object writes, Parquet mandates huge RowGroups (128 MB to 512 MB). 
2. **Page Boundaries:** While Parquet has internal Data Pages (usually 1 MB), dictionary headers and column offsets require parsing metadata trees.
3. To extract a 5-minute slice ($2\text{ MB}$ uncompressed), a query engine must read the entire $128\text{ MB}$ block from disk, decompress all constituent column pages, and discard $98\%$ of the rows. Latency degrades from **sub-millisecond to hundreds of milliseconds**.

### The Two-Level Sparse Index Architecture
Quant time-series engines structure physical files around strict temporal monotonicity:
1. **Physical Chunks:** Files are partitioned into uniform 2 MB Chunks ($65,536$ records).
2. **Footer Sparse Index:** Appended at the end of the file:
   $$\text{IndexEntry}_k = \left\{ T_{\min},\, T_{\max},\, \text{Offset}_{\text{file}},\, \text{CompressedBytes} \right\}$$
3. **RAM Residency:** A full trading day of 100 million ticks comprises $\sim 1,500$ chunks. The entire sparse index is **$\approx 36\text{ KB}$**, which resides permanently in user-space RAM.

When Workload B executes:
* The engine performs a `std::lower_bound` binary search across the in-memory array ($\le 25\text{ ns}$).
* It identifies that target interval $[14:00, 14:05]$ spans exactly Chunks 842 and 843.
* It executes a targeted, aligned `preadv2()` or `io_uring` direct read for exactly 4 MB of disk blocks. **Read amplification is virtually $1.0\times$, and response time is $< 400\ \mu\text{s}$**.

---

## 5. Architectural Deep-Dive: How Industry Systems Solve It

How do prominent production systems implement these trade-offs?

```
+----------------------------------------------------------------------------------------------------+
|                                Systems Comparison Spectrum                                         |
|                                                                                                    |
|   Apache Parquet            KDB+ / q                 DolphinDB              Modern Custom PAX      |
|   -----------------         ------------             ------------           ------------------     |
|   • Cloud-first OLAP        • Pure In-Memory SoA     • Dual TSDB/OLAP       • Zero-Copy PAX Chunk  |
|   • Large RowGroups         • POSIX mmap() file map  • Segmented TSDB Block • io_uring + O_DIRECT  |
|   • Heavy zstd/snappy       • Native binary vectors  • Specialized Codecs   • 2MB HugePage Arena   |
|   • Broad aggregations      • Ultra-fast q queries   • Cluster distribution • Direct backtest link |
+----------------------------------------------------------------------------------------------------+
```

### 1. KDB+ (First Data / KX Systems)
* **Design Philosophy:** Raw simplicity and in-memory vector performance.
* **Physical Layout:** Pure column-store on local NVMe disk. A partitioned KDB+ database stores each column as an independent, raw, uncompressed (or lightly compressed with LZ4) binary file within directory trees: `/data/20261105/BTCUSDT/price`.
* **I/O Mechanism:** Relies heavily on **POSIX `mmap()`**. When a query executes, KDB+ maps the column files directly into the virtual address space and lets the vector processor operate on bare pointers (`long*`, `double*`).
* **Merits:** Unrivaled vector query execution speed; vector arithmetic compiles to zero-overhead CPU loops.
* **Challenges & Weaknesses:** As detailed in our [mmap_lock contention analysis](file:///Users/wangzhihao/Desktop/source/marsset.github.io/_posts/2026-11-05-mmap-lock-contention.markdown), when multiple researchers run concurrent queries exceeding physical RAM, KDB+ instances can suffer from kernel page table bloat, TLB shootdowns, and violent `mmap_lock` read/write semaphore stalls.

### 2. DolphinDB
* **Design Philosophy:** Distributed financial database unifying database engine, distributed computing, and streaming analytics.
* **Physical Layout:** **Dual-Engine Architecture**.
  * **OLAP Engine:** Traditional column store optimized for analytical reporting.
  * **TSDB Engine:** Tailored specifically for Level 2/3 ticks. Implements an LSM-tree-inspired block organization where data within a chunk is sorted by `(Symbol, Timestamp)` and indexed by a sparse multi-level index.
* **Compression:** Implements native time-series encodings: double-delta, Gorilla, and vector LZ4.
* **Merits:** Seamless transition between distributed SQL analytics and point-in-time order book reconstruction; out-of-the-box cluster failover and distributed sorting.

### 3. Modern In-House C++20 PAX Engine (`io_uring` + `O_DIRECT`)
Leading proprietary trading firms increasingly deploy minimal, bare-metal C++ storage libraries for their historical tick archives:
* **Storage Geometry:** 2 MB aligned PAX chunks with embedded metadata headers and sparse footers.
* **Kernel Bypass via `O_DIRECT`:** Sequential scans bypass the OS Page Cache entirely, avoiding the memory eviction storms documented in our [Page Cache Thrashing guide](file:///Users/wangzhihao/Desktop/source/marsset.github.io/_posts/2026-11-05-page-cache-thrashing.markdown).
* **Asynchronous Double-Buffering:** Uses Linux `io_uring` with registered buffers (`IORING_REGISTER_BUFFERS`):
  * Core thread processes Chunk $N$ in user-space buffer $A$.
  * NVMe controller concurrently DMAs Chunk $N+1$ into user-space buffer $B$.
  * Thread swaps buffers with zero syscall overhead and zero CPU copies.

---

## 6. Comprehensive Technical Comparison

| Technical Dimension | **Apache Parquet / ORC** | **KDB+ (q)** | **DolphinDB (TSDB)** | **In-House PAX / Arrow** |
| :--- | :--- | :--- | :--- | :--- |
| **Primary Domain** | Cloud Data Lakes, Trino, Spark | High-frequency hedge funds, proprietary trading | Quantitative research platforms, hedge funds | Execution backtesting, replay simulation |
| **Physical Layout** | DSM (RowGroups: 128–512MB) | Separate per-column binary files | Segmented chunks with sort keys | PAX (2MB aligned chunks) |
| **Row Reconstruction**| High CPU penalty (transposition stall) | Fast for vectors; slow for tick iteration | Optimized TSDB tuple assembly | **Zero penalty** (SRAM-resident L2/L3 transposition) |
| **Primary Codecs** | Snappy, zstd, Gzip | Raw binary, LZ4 | Gorilla, Double-Delta, LZ4 | **SIMD Gorilla + Bit-Packing** |
| **Decompression Rate**| $400 - 800\text{ MB/s}$ / core | Line rate (often uncompressed) | $2.5 - 4.0\text{ GB/s}$ / core | **$3.5 - 5.5\text{ GB/s}$ / core** |
| **5-Min Slice Query** | Massive read amplification ($60\times+$) | Instantaneous if pre-partitioned | Microsecond-level (sparse block index) | **$< 500\ \mu\text{s}$** (sparse RAM index + `pread`) |
| **Kernel/IO Pathway** | User-space stream `read()` / S3 API | POSIX `mmap()` (kernel page cache) | User-space buffer pool + multi-threading | **`io_uring` + `O_DIRECT`** (zero cache pollution) |
| **Storage Density** | Highest ($8\times - 12\times$) | Lowest ($1\times - 2.5\times$) | High ($4\times - 7\times$) | Balanced ($4\times - 6\times$) |

---

## 7. Architectural Decision Framework

When should an engineering team use which format? The optimal data architecture typically separates storage into tiers based on query frequency and compute proximity:

```
+--------------------------------------------------------------------------------------------------+
|                               Three-Tier Quantitative Storage Pipeline                           |
|                                                                                                  |
|   Tier 1: Cold Historical Archive & Factor Lake (Cloud S3)                                       |
|   Format: Apache Parquet (zstd compressed, partitioned by Date / Asset Class)                   |
|   Role: Cross-sectional factor mining, SQL discovery, deep learning training in Spark / Ray.    |
|                                        |                                                         |
|                                        v  ETL / Extract Window                                   |
|   Tier 2: Interactive Research & Time-Series DB (Enterprise Cluster)                             |
|   Format: DolphinDB TSDB / KDB+ Partitioned Tables                                              |
|   Role: Multi-user alpha research, multi-asset interactive queries, intraday analytics.          |
|                                        |                                                         |
|                                        v  Direct NVMe Pre-bake                                   |
|   Tier 3: Hot Strategy Backtesting & Production Replay (Local NVMe)                              |
|   Format: Proprietary PAX Binary Chunks (Gorilla/XOR encoded, 2MB aligned)                       |
|   Role: Event-driven backtesting, L2/L3 order book simulation saturating PCIe 4.0/5.0 NVMe bus.   |
+--------------------------------------------------------------------------------------------------+
```

### Summary Rules of Thumb
1. **Never use standard Parquet for high-frequency tick replay engines.** The row-stitching transposition penalty and zstd decompression bottlenecks will starve your simulation threads of data.
2. **If your workload is pure vectorized mathematics over single columns** (e.g. calculating rolling VWAP over billions of records), **KDB+ and columnar memory models excel**.
3. **If your workload requires event-driven row-by-row simulation of multi-level order books**, choose a **PAX layout** that bounds columnar compression within small, cache-resident chunks, paired with a memory-resident sparse timestamp index.
