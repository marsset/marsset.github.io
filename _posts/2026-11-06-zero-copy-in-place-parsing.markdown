---
title:  "Zero-Copy Binary Parsing"
date:  2026-11-06 16:30:00 +0800
categories:
  - system
tags: system linux kernel high-frequency-trading cpp memory-management microarchitecture
classes: wide
layout: single
use_math: true
excerpt: >
  a deep dive into nanosecond-level market data parsing: navigating unaligned memory access, eliminating undefined behavior and simd vector faults, and executing single-cycle hardware byte swapping via bswap and fused movbe instructions.
---

In high-frequency trading (HFT) gateways and line-rate market data ingestion engines, incoming exchange feeds (such as NASDAQ ITCH 5.0, CME MDP 3.0, or exchange tick streams) deliver tens of millions of binary messages per second.

When a network packet or storage chunk arrives at the consumer worker, the thread receives a naked memory pointer (`const char* buffer`) referencing a raw byte slice.

To achieve single-digit nanosecond processing latency, **traditional deserialization is strictly prohibited**:
* There are no JSON, Protobuf, or SBE reflection parsers.
* There are no intermediate dynamic heap allocations (`malloc()` / `new`).
* There are no full-packet struct copies (`memcpy` into intermediate DTO objects).

Instead, the parser executes **Zero-Copy In-Place Binary Parsing**: the consumer thread reads numeric fields *directly from the raw byte stream in-place*.

However, this in-place paradigm immediately collides with two fundamental engineering challenges:
1. **Unaligned Memory Access & Undefined Behavior (UB):** Packed binary protocols place multi-byte integers at arbitrary, odd memory offsets (e.g., offset 5). Naive pointer dereferencing triggers ISO C++ Undefined Behavior and fatal aligned SIMD vectorization faults (`vmovaps` / `SIGSEGV`).
2. **Hardware-Level Endianness Flipping:** Network protocols arrive in Big-Endian, while host server CPUs (x86-64 / ARM64) operate in Little-Endian. Converting byte order without stalling the CPU superscalar pipeline requires **single-cycle hardware primitives (`bswap`, `rev`, and `movbe`)**.

---

## 1. Unaligned Memory Access: The Undefined Behavior Trap

To minimize bandwidth across financial market multicast streams, exchange protocols pack fields tightly without padding bytes:

```c
// Example: NASDAQ ITCH 5.0 Order Add Message (Packed)
#pragma pack(push, 1)
struct RawItchOrderAdd {
    char     msg_type;      // Offset 0: 1 byte ('A')
    uint16_t stock_locate;  // Offset 1: 2 bytes
    uint16_t tracking_num;  // Offset 3: 2 bytes
    uint64_t timestamp_ns;  // Offset 5: 8 bytes (ODD ADDRESS!)
    uint64_t order_ref_num; // Offset 13: 8 bytes
    char     buy_sell_flag; // Offset 21: 1 byte
    uint32_t shares;        // Offset 22: 4 bytes
    char     stock[8];      // Offset 26: 8 bytes
    uint32_t price;         // Offset 34: 4 bytes
};
#pragma pack(pop)
```

Notice `timestamp_ns`: it is an 8-byte integer starting at **offset 5**.

---

### 1.1 Why `reinterpret_cast` is Fatal: The UB & SIMD Trap

A developer attempting to extract the timestamp directly might write:

```cpp
// DANGEROUS: Undefined Behavior & Crash Risk
uint64_t ts = *reinterpret_cast<const uint64_t*>(buffer + 5);
```

While x86-64 CPUs permit scalar unaligned memory reads at the silicon level, writing this in C++ is catastrophic:

#### 1. Language Specification & Compiler UB
Under ISO C++ (and C11/C17), casting a pointer to a type with stricter alignment requirements and dereferencing it is **Undefined Behavior (UB)**.

Compilers assume all `uint64_t*` pointers are aligned to $8\text{ bytes}$ (`address % 8 == 0`). When compiling with optimization flags (`-O3`), LLVM/Clang vectorization engines assume this alignment invariant and may emit aligned SIMD load instructions (such as x86 `vmovaps` or `movdqa`).

When fed an odd address like `buffer + 5`, these aligned vector instructions throw an immediate **Hardware General Protection Fault (`SIGSEGV` / `SIGBUS`)**, terminating the trading engine instantly. On ARM architectures (e.g. strict alignment modes or older cores), unaligned scalar pointer dereferencing directly faults at the CPU level.

---

### 1.2 The Software Solution: Stack `std::memcpy`

To extract unaligned fields with 100% standard compliance and zero performance penalty, we use stack-allocated `std::memcpy`:

```cpp
template <typename T>
inline T read_unaligned(const void* ptr) noexcept {
    static_assert(std::is_trivially_copyable_v<T>, "T must be trivially copyable");
    T val;
    std::memcpy(&val, ptr, sizeof(T)); // Stack local variable: zero heap allocation
    return val;
}
```

#### Why `std::memcpy` Costs Zero Extra CPU Cycles
Many developers fear `std::memcpy`, assuming it causes dynamic heap allocation or an expensive runtime function call:
* `val` is a local stack variable: **zero heap allocation**.
* Because `sizeof(T)` is known at compile time ($8\text{ bytes}$), GCC and Clang treat `std::memcpy` as a **Compiler Intrinsic**.
* The compiler **erases the function call entirely**, emitting a single hardware instruction that understands unaligned semantics:
  * **On x86-64:** Emits a single scalar load:
    ```assembly
    mov rax, QWORD PTR [rdi + 5]  ; Direct unaligned scalar load (1 cycle)
    ```
  * **On ARM64:** Emits a single unaligned load:
    ```assembly
    ldr x0, [x1, #5]              ; Hardware unaligned LDR (1 cycle)
    ```

---

## 2. Hardware-Level Endianness: Single-Cycle BSWAP & MOVBE

Financial exchange network protocols transmit numbers in **Big-Endian (Network Byte Order)**, where the most significant byte is transmitted first. 

Standard commodity hardware running quantitative engines (Intel Core/Xeon, AMD EPYC, Apple M-series, AWS Graviton) is **Little-Endian**, where the least significant byte is stored first.

If a raw 64-bit Big-Endian timestamp `0x000000003B9ACA00` ($1\text{ second in ns}$) is read by a Little-Endian CPU, it interprets the bytes as `0x00CA9A3B00000000`—producing corrupt timestamps.

### 2.1 The Naive Shift Loop (Pipeline Killer)
Writing portable endianness code via bitwise shift operators:
```cpp
// AVOID: Stalls execution pipeline
uint64_t bad_bswap64(uint64_t x) {
    return ((x & 0xFF00000000000000ULL) >> 56) |
           ((x & 0x00FF000000000000ULL) >> 40) |
           ((x & 0x0000FF0000000000ULL) >> 24) |
           ((x & 0x000000FF00000000ULL) >>  8) |
           ((x & 0x00000000FF000000ULL) <<  8) |
           ((x & 0x0000000000FF0000ULL) << 24) |
           ((x & 0x000000000000FF00ULL) << 40) |
           ((x & 0x00000000000000FFULL) << 56);
}
```
This naive routine generates **more than 15 separate arithmetic instructions** (`and`, `shr`, `shl`, `or`). Because each operation depends on the outcome of the previous, it creates a deep data dependency chain, clogging ALU execution ports and inducing a $6 - 10\text{ cycle}$ latency penalty.

### 2.2 Single-Cycle Hardware Instruction: `bswap` & `rev`
Both x86 and ARM microarchitectures integrate dedicated silicon circuits to reverse byte order in **a single clock cycle**:
* **x86-64 `bswap`:** The `bswap r64` instruction flips all 8 bytes inside a 64-bit general-purpose register with a **latency of 1 cycle** and throughput of $0.5\text{ cycles}$ (can execute 2 per cycle on modern Intel Golden Cove / AMD Zen 4 cores).
* **ARM64 `rev`:** The `rev x0, x0` instruction similarly reverses bytes in a 64-bit register in **1 single clock cycle**.

We expose these instructions directly to the compiler using intrinsics:
```cpp
template <typename T>
inline T byteswap_be(T val) noexcept {
#if __cplusplus >= 202302L
    return std::byteswap(val); // C++23 standard
#else
    if constexpr (sizeof(T) == 8) {
        return __builtin_bswap64(val);
    } else if constexpr (sizeof(T) == 4) {
        return __builtin_bswap32(val);
    } else if constexpr (sizeof(T) == 2) {
        return __builtin_bswap16(val);
    } else {
        return val; // 1-byte char needs no swapping
    }
#endif
}
```

---

### 2.3 The Ultimate Hardware Fusion: x86 `MOVBE`

In production quantitative engines running on modern Intel/AMD servers, we do not even spend 1 cycle on `mov` followed by 1 cycle on `bswap`.

Modern x86 processors support the **`MOVBE` (Move Big-Endian)** instruction.

`MOVBE` is a fused microarchitectural operation: **it reads unaligned bytes from memory, flips their endianness in-flight inside the Load Buffer, and deposits the Little-Endian result directly into the destination register in a single instruction!**

```assembly
; Reading an unaligned 64-bit Big-Endian timestamp at offset 5:
movbe rax, QWORD PTR [rdi + 5]   ; Load + Byte-Swap Fused in 1 Instruction!
```

To enable this optimization, compile with `-march=native` or `-mmovbe`. When Clang/GCC encounters `read_unaligned` followed by `__builtin_bswap64`, the compiler optimizer **automatically folds the two operations into a single `movbe` instruction**.

---

## 3. Production Implementation: The In-Place Field Extractor

Below is a self-contained, zero-allocation C++20 implementation. It defines the in-place parsing primitive, demonstrates packed ITCH 5.0 parsing, and includes compiler assertions:

```cpp
#include <cstdio>
#include <cstdint>
#include <cstring>
#include <type_traits>
#include <bit>

// -----------------------------------------------------------------------------
// Nanosecond In-Place Binary Field Extractor
// -----------------------------------------------------------------------------
template <typename T>
[[nodiscard]] inline T extract_be(const char* buffer, size_t offset) noexcept {
    static_assert(std::is_trivially_copyable_v<T>, "T must be trivially copyable");

    // 1. Zero-UB, zero-allocation unaligned read
    T raw;
    std::memcpy(&raw, buffer + offset, sizeof(T));

    // 2. Single-cycle hardware byte swap (Fuses to MOVBE on x86)
#if __cplusplus >= 202302L
    return std::byteswap(raw);
#else
    if constexpr (sizeof(T) == 8) {
        return __builtin_bswap64(raw);
    } else if constexpr (sizeof(T) == 4) {
        return __builtin_bswap32(raw);
    } else if constexpr (sizeof(T) == 2) {
        return __builtin_bswap16(raw);
    } else {
        return raw;
    }
#endif
}

// -----------------------------------------------------------------------------
// Domain Representation: Normalized Internal Tick Event
// -----------------------------------------------------------------------------
struct InternalTick {
    uint64_t timestamp_ns;
    uint64_t order_id;
    uint32_t price_fixed;
    uint32_t shares;
    char     side;
    char     symbol[8];
};

// -----------------------------------------------------------------------------
// In-Place Parser Worker
// -----------------------------------------------------------------------------
void parse_itch_add_order(const char* packet_payload, InternalTick& out_tick) noexcept {
    // NASDAQ ITCH 5.0 Message Type 'A' Field Offsets:
    // Offset  0: Message Type ('A')
    // Offset  1: Stock Locate (uint16_t)
    // Offset  3: Tracking Number (uint16_t)
    // Offset  5: Timestamp (uint64_t nanoseconds, Big-Endian, Unaligned)
    // Offset 13: Order Reference Number (uint64_t, Big-Endian, Unaligned)
    // Offset 21: Buy/Sell Indicator (char: 'B' or 'S')
    // Offset 22: Shares (uint32_t, Big-Endian, Unaligned)
    // Offset 26: Stock Symbol (8 bytes ASCII)
    // Offset 34: Price (uint32_t, 4 decimal places, Big-Endian, Unaligned)

    out_tick.timestamp_ns = extract_be<uint64_t>(packet_payload, 5);
    out_tick.order_id     = extract_be<uint64_t>(packet_payload, 13);
    out_tick.side         = packet_payload[21];
    out_tick.shares       = extract_be<uint32_t>(packet_payload, 22);
    
    // Copy 8-byte stock ticker directly via 64-bit scalar load
    std::memcpy(out_tick.symbol, packet_payload + 26, 8);
    
    out_tick.price_fixed  = extract_be<uint32_t>(packet_payload, 34);
}
```

### Compiler Assembly Verification (GCC 14 / Clang 18 `-O3 -march=x86-64-v3`)
When compiling the `extract_be<uint64_t>(packet_payload, 5)` call, GCC outputs:

```assembly
movbe   rax, QWORD PTR [rdi + 5]   ; Single instruction: Unaligned Read + Big-Endian Swap
mov     QWORD PTR [rsi], rax       ; Store timestamp into out_tick
```

There are no stack spills, no runtime `memcpy` function branches, no 15-instruction shift loops, and no undefined behavior.

---

## 4. Summary: Rules of Engagement for In-Place Parsers

When implementing ultra-low-latency binary protocol parsers in high-frequency trading:

1. **Never use `reinterpret_cast` on unaligned byte pointers:** Casting unaligned byte offsets to typed pointers invokes undefined behavior and risks `SIGSEGV`/`SIGBUS` crashes when vectorizers emit aligned SIMD instructions (`vmovaps`).
2. **Use stack-allocated `std::memcpy` for unaligned loads:** Compilers treat fixed-size `std::memcpy` as intrinsics, emitting a single non-aligned `mov` or `ldr` instruction with zero overhead.
3. **Always use hardware intrinsics for endianness conversion:** Replace manual shift/mask logic with `__builtin_bswap64` (x86 `bswap`) or ARM64 `rev`.
4. **Target modern ISAs for `MOVBE` fusion:** Ensure flags like `-march=native` or `-mmovbe` are enabled so loads and swaps collapse into single-cycle atomic instructions.
