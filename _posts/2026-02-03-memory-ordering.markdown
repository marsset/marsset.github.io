---
title:  "Memory Ordering"
date:  2026-02-03 11:33:53 +0800
tags: memory
classes: wide
layout: single
---
<!-- Intro memory order concept -->
One view of a program is to treat it as a bunch of memory accesses (load & store).
In a multi-core shared-memory architecture, the order of memory accesses can suprise since not only the programmer but also CPU and compiler change it.
A wrong order of memory accesses means incorrectness.

<!-- Intro the first example -->
Check the following example in [std::memory_order][memory_order] from cppreference.com, which says `r1 == r2 == 42` is allowed to produce. Why?

[memory_order]: https://en.cppreference.com/w/cpp/atomic/memory_order.html

```cpp
// Thread 1:
r1 = y.load(std::memory_order_relaxed); // A
x.store(r1, std::memory_order_relaxed); // B
// Thread 2:
r2 = x.load(std::memory_order_relaxed); // C
y.store(42, std::memory_order_relaxed); // D
```
<!-- sequential consistency match our intuition -->
A natural intution is `A` completes before `B` starts, and `C` completes before `D` starts.
Inter threads can interleave as long as inner-thread order is preserved, so something like
`A -> C -> B -> D` is allowed, but not `D -> A -> B -> C`.
This is called [sequential consistency][sc], which means all events can be treated as
some atomic instant points and projected into a global timeline with a total order.
However, the above code doesn't follow sequential consistency, thus counterintuitive.
we can also say `r1 == 42` on thread1 and `r2 == 42` on thread2 is sequential inconsistent.

[sc]: https://en.wikipedia.org/wiki/Sequential_consistency

<!-- memory latency -->
Sequential consistency means in-order execution. But memory is way slower than CPU.
Load/store takes 550 cycles (122ns) to hit main memory
on my Apple M4 (4.5GHz) [^benchmark],
while arithmetic instruction like add only takes 1 cycle.
In-order execution will be a disaster since a load/store can block 550 adds.
As a result, mordern machine doesn't follow sequential consistency.

[^benchmark]: Measured by https://github.com/timoheimonen/macOS-memory-benchmark

<!--
 compiler reordering
TODO: under what criteria can compiler reorder?
 -->
Statically, compiler can reorder C and D since there is no observable inner-thread change,
but not A and B since there is a data dependency between them.
Memory order `D -> A -> B -> C` then is possible, which results `r1 == r2 == 42`.

<!-- CPU out-of-order execution -->
Dynamically, CPU can perform out-of-order execution.
It's a hardware implemented asynchronous runtime.
Take Tomasulo’s algorithm [^computer-arch] as an example,
all in-flight instructions stay in a pool called reservation station
(load/store buf achieve the similar function), waiting for their dependent
operands to be ready.
Instructions whose all operands is ready first execute first.
So imagine `C` hits main memory and `D` hits the cache,
and `D` execute first, then
the execution order `D -> A -> B -> C` can occur,
which results `r1 == r2 == 42`.

[^computer-arch]: Computer Architecture: A Quantitative Approach, Edition 6, Section 3.4

<!-- how to regain control -->
The above example demonstrates under `memory_order_relaxed`  how things can go out of
control and make memory ordering unpredictable. The next example shows how a technique
called acquire/release can help us to regain the control.

Example: Why r1 will be 17 for certain?

```cpp
int data;
atomic<bool> sync;

^ // Thread 1
^ data = 17;
- sync.store(true, std::memory_model_release);
~

~ // Thread 2
- while (!sync.load(std::memory_model_acquire)) {}
v r1 = data;
v
```

This example reflects the original intention of acquire/release [^Kourosh]. We want
a way to synchronize two threads so that `data = 17` happens before
`r1 = data`. Memory is what two threads only share and serves as the
synchronization media. A tag `release` is marked on store against memory location `sync`
so that the uppper region marked by `^` can't reorder below `release`. In the same manner,
a tag `acquire` is marked on load against memory location `sync` so that the lower region
marked by `v` can't flow up `acquire`.
In this way, we can ensure region `^` happens before region `v`.
Other irrelevant region marked by `~` can reorder at will.
In other words, `acquire` and `release`
are half fences. Regarding the implementation, compiler and CPU will respect tags
`acquire` and `release` all the way in their implementation without break these tags'
semantics.

Since mordern lock is built on top of acquire/release, so they need to pass a memory
location during intialization.

The acquire/release gives the programmer a precise way to control memory ordering in the
background of compiler reordering and CPU out-of-order execution.


[^Kourosh]: Memory Consistency and Event Ordering in Scalable Shared-Memory Multiprocessors
