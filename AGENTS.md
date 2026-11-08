# Agent Guidelines & Operational Rules for marsset.github.io

> This document defines mandatory guidelines, local preview workflows, and operational rules for AI agents contributing to this repository (`marsset.github.io`).

---

## 1. Local Preview & Server Workflow

When creating, editing, or inspecting posts, **always use the native Jekyll server for local preview**:

```bash
# Start local Jekyll server with auto-regeneration and LiveReload
bundle exec jekyll serve -H 127.0.0.1 -P 4000 --livereload
```

### Why:
- **Auto-Regeneration:** Watches for file changes across `_posts/`, `_layouts/`, `_includes/`, and rebuilds automatically.
- **Root-Relative Asset Resolution:** The site uses root-relative paths (e.g. `/assets/css/main.css`). Opening generated HTML files directly via `file://` breaks CSS, JS, and font loading.
- **Do NOT use `python3 -m http.server`:** It lacks file-watching and LiveReload, requiring manual re-compilation after every change.

### Preview URLs:
- Base: `http://localhost:4000/` (or `http://127.0.0.1:4000/`)
- Post URL format: `http://localhost:4000/<category>/YYYY/MM/DD/<post-slug>.html`
  - Example: `http://localhost:4000/system/2026/11/05/mmap-lock-contention.html`

---

## 2. Publishing & Git Rules (Strict Constraints)

- **NEVER publish or push to remote without explicit user command:**
  - Do NOT commit or push to `mainline` (or any remote branch) unless the user explicitly tells you to publish.
  - Keep drafts and changes local for user review.
- **Language Policy:**
  - Write all posts in **clean, professional English only**.
  - Do NOT include Chinese characters or commentary in posts unless explicitly requested by the user.
- **Categorization:**
  - Technical and infrastructure deep-dives belong in the `system` category:
    ```yaml
    categories:
      - system
    tags: system linux kernel memory-management
    ```
- **Mandatory Mobile Layout QA Check Before Publishing:**
  - Before pushing or publishing, always execute:
    ```bash
    python3 scripts/test_mobile_layout.py --fix
    ```
  - This verifies and guarantees that math equations, SVGs, tables, and images strictly conform to mobile phone viewports without horizontal blowout or layout breakage.
  - A git pre-push hook (`.git/hooks/pre-push`) automatically enforces this on every `git push`.

---

## 3. Post Drafting & Technical Formatting Conventions

### Front Matter Template
```yaml
---
title:  "Descriptive Technical Title"
date:  YYYY-MM-DD HH:MM:SS +0800
categories:
  - system
tags: system
classes: wide
layout: single
use_math: true
excerpt: >
  Concise lowercase one-sentence summary for SEO and feed generation.
---
```

### Critical Gotchas
1. **Timestamp Check:**
   - Always ensure `date` is set to the current or past local time (e.g. earlier in the current day).
   - If `date` is in the future relative to system time, Jekyll will silently skip building the post unless `--future` is specified.
2. **MathJax & Code Escaping:**
   - Set `use_math: true` in the front matter.
   - Do NOT use MathJax `\text{uint64\_t}` or `\text{int64\_t}` for programming types, variable names, or bitwise operators; MathJax 2.7.9 escapes backslashes inconsistently. Instead, format code types as standard inline Markdown code (e.g. `` `uint64_t` ``).
3. **Diagrams & Flowcharts:**
   - **Always use inline SVG (`<svg viewBox="..." ...>`)** with `fill="currentColor"`, `stroke="currentColor"`, and relative opacity (`fill-opacity="..."`, `stroke-opacity="..."`) for automatic light/dark mode adaptation.
   - **Do NOT use Mermaid code blocks (` ```mermaid `)**: the Jekyll theme's kramdown markdown parser does not load or bundle `mermaid.js`, causing Mermaid diagrams to render as raw unformatted text blocks in the browser. See `_posts/2026-11-03-virtual-memory-translation.markdown` for reference SVG styling.
4. **Formula Clarity:**
   - Clearly label units and words when showing calculations (e.g. $\frac{8192\text{ bits}}{64\text{ bits/word}} = 128\text{ words} = 1024\text{ bytes (1 KB)}$).
5. **Short, Concise Titles (Mandatory Memory):**
   - Always prefer short, punchy titles (e.g. *"Poisson Distribution"*, *"Page Cache Thrashing"*, *"Zero-Copy Binary Parsing"*, *"Memory Ordering"*).
   - Avoid long compound titles, academic subtitles, or run-on explanatory clauses. Keep titles strictly under 3–4 words whenever possible, placing extended summaries into the `excerpt:` field.
6. **Notices & Callout Boxes (No GitHub Alert Syntax):**
   - **Do NOT use GitHub Flavored Markdown alerts (`> [!WARNING]`, `> [!NOTE]`)**: Kramdown does not recognize GFM alerts, rendering them as raw, ugly `[!WARNING]` text inside standard blockquotes.
   - Instead, always use Minimal Mistakes native notice HTML blocks:
     ```html
     <div class="notice--warning" markdown="1">
     #### Title
     Content here...
     </div>
     ```
     Available variants: `.notice--warning`, `.notice--info`, `.notice--danger`, `.notice--primary`.
7. **Effortless Understanding Standard (Mandatory Writing Philosophy):**
   - Complex Linux kernel, networking, and systems concepts must be structured so comprehension feels effortless without being condescending or childish.
   - **NO Juvenile Analogies:** Strictly avoid childish or forced real-world fables (no moving crates with pencils, pizza delivery boys, or post office parables). These insult the reader's intelligence and clutter technical prose.
   - **The Ideal Easy Intro: A Concrete Technical Paradox / Grounded Riddle:**
     1. *The Intuitive Setup:* Establish a concrete, relatable scenario with real numbers (e.g., *"You configure a 10 MB receive buffer. The exchange sends only 500 KB of data..."*).
     2. *The Baffling Failure:* Present the sudden, catastrophic production failure (e.g., *"Why did the trading gateway freeze for 3 ms and drop packets when the buffer was barely 5% full?"*).
     3. *The Mechanical Reveal:* Answer the paradox step-by-step using precise kernel mechanics (`truesize`, `sk_rmem_alloc`, `sk_buff` overhead) so the "Aha!" realization feels mathematically natural.
     4. *The Production & Latency Consequence:* Detail why this destroys p99.9 tail latency (CPU lockup, cache annihilation, hardware RX ring drops).
     5. *The Actionable Playbook:* Conclude with battle-tested kernel parameters (`sysctl`), diagnostic commands (`nstat`, `bpftrace`), and architectural remedies (kernel bypass, spinning cores).
   - **Immediate Jargon Anchoring:** Whenever introducing kernel terms (`truesize`, `sk_rmem_alloc`, `sk_buff`, `tcp_prune_queue`), immediately anchor them with their plain-English meaning and operational purpose.
   - **Visual Diagrams:** Use clean, immediately readable ASCII schematics and timelines that communicate layout and boundaries at a single glance.

---

## 4. Systems Engineering Philosophy & Editorial "Flavor"

Every technical deep-dive on this site must adhere to a distinct systems engineering doctrine. We do not write surface-level tutorials, API syntax summaries, or generic "how-to" articles. Every post must bridge **hardware physics**, **kernel mechanics**, and **user-space software architecture**.

### 1. The 3-Tier Physical Model (Mandatory Architecture)
Every systems analysis must be grounded in the machine's physical reality across three tiers:

```
+==================================================================================================+
| [Tier 1: Hardware Ground Truth]                                                                  |
| • CPU Microarchitecture: L1/L2/L3 caches, 64-byte cachelines, false sharing, branch predictors,  |
|   SIMD vector execution units (AVX2/AVX-512).                                                    |
| • Memory & Bus: NUMA nodes/sockets, DDR4/DDR5 bandwidth, PCIe Gen 4/5 bus lanes (16–32 GB/s).    |
| • Storage Hardware: NVMe flash controllers, 8–16 parallel NAND channels, die interleaving,       |
|   Queue Depth (QD >= 32), 4KB physical LBA boundaries, hardware DMA bursts.                      |
+--------------------------------------------------------------------------------------------------+
                                                 │
                                                 ▼
+==================================================================================================+
| [Tier 2: OS & Kernel Boundary]                                                                   |
| • Virtual Memory: MMU page tables (PGD->PUD->PMD->PTE), TLB shootdowns, page faults,             |
|   get_user_pages() page pinning and refcount cacheline bouncing.                                 |
| • Subsystem Locks: mmap_lock rwsem contention, zone watermarks, kswapd vs direct reclaim storms, |
|   dual-LRU active/inactive list churn.                                                           |
| • Execution Overhead: System call trap overhead, KPTI (Meltdown/Spectre) page-table trampolines, |
|   scheduler context switches (TASK_UNINTERRUPTIBLE vs TASK_RUNNING).                             |
+--------------------------------------------------------------------------------------------------+
                                                 │
                                                 ▼
+==================================================================================================+
| [Tier 3: User-Space Software Architecture]                                                       |
| • Layout & Alignment: 4KB page alignment (posix_memalign, mmap, HugeTLB 2MB), cacheline         |
|   padding, zero-copy buffer pools.                                                               |
| • Concurrency & Queues: Lockless circular ring buffers, atomic head/tail pointers, memory        |
|   barriers, shared-memory SQE/CQE pipelines.                                                     |
| • Compute Overlap: 100% overlap between physical DMA transfers and CPU SIMD decompression/compute |
|   (T_total = max(T_io, T_compute)).                                                              |
+==================================================================================================+
```

### 2. Strict Anti-Patterns (What We Never Do)
- **NO Dry API Walkthroughs:** Never document an API in a vacuum (e.g. *"Function X takes parameters Y and Z"*). Always explain *why* the API was forced into existence by the failure of previous abstractions (`read()` $\to$ `libaio` $\to$ `io_uring`).
- **NO Vague Performance Claims:** Never say *"it is much faster"* or *"reduces latency significantly"*. Always provide concrete mathematical bounds, latency numbers, and hardware calculations (e.g. $\frac{128\text{ KB}}{100\text{ }\mu\text{s}} = 1.28\text{ GB/s}$, 64 booleans in `uint64_t` saves 87.5% memory bus bandwidth).
- **NO Toy Code Snippets:** Provide production-grade, compilable, idiomatic C/C++ showing exact flags (`O_DIRECT`, `MAP_HUGETLB`, `IORING_SETUP_SQPOLL`), alignment assertions, and error handling.

### 3. Structural Anatomy of a Great Post
1. **The Intuitive Analogy & Core Dilemma:** Open with a relatable mental model and an apparent paradox or engineering failure (e.g. *"Why does packing an 80-byte trade fill consume 2 KB of RAM?"* or *"Why do sequential scans evict random-access working sets?"*).
2. **The Battlegrounds:** Frame technical sections as concrete trade-offs (e.g. *Row-Stitching vs. Decompression*, *Synchronous Stall vs. Async Pipeline*, *truesize vs. Payload Window*).
3. **Hardware / Data-Flow Diagrams:** Every post must feature clean visual schematics (inline SVG or clean ASCII diagrams) showing memory layouts, kernel/user boundaries, or queue state transitions.
4. **Summary Rules of Engagement:** Conclude with actionable, battle-tested engineering heuristics and diagnostic commands for production system architects.

