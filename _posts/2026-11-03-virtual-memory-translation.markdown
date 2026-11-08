---
title:  "Virtual Memory Translation"
date:  2026-11-03 13:00:00 +0800
categories:
  - system
tags: system
excerpt: >
  how the MMU and the cache hierarchy fit together on a memory access, and how virtual addresses become physical ones.
---

The Memory Management Unit (MMU), a dedicated hardware unit inside the CPU, and the L1/L2/L3 caches are two stages placed back to back on every memory access: the MMU translates a virtual address into a physical address, and the cache hierarchy checks whether the data at that physical address can be served directly from fast cache instead of going all the way to DRAM.

<svg viewBox="0 0 716 156" width="100%" style="max-width:716px;display:block;margin:1.5em auto;" role="img" aria-label="Memory access flow, typical sizes, and latencies: inside the CPU chip, Core sends VA to MMU (~1 ns TLB), then PA to L1 (64–128 KB, ~1 ns), L2 (4–16 MB, ~4 ns), and L3 (24–32 MB, ~15 ns); on an L3 miss, it goes off-chip to DRAM (16–64 GB, ~80 ns)">
  <!-- On-chip CPU boundary -->
  <rect x="6" y="18" width="574" height="128" rx="8" fill="none" stroke="currentColor" stroke-opacity="0.3" stroke-width="1.2" stroke-dasharray="4,4"/>
  <text x="16" y="12" text-anchor="start" font-size="11" fill="currentColor" fill-opacity="0.5">CPU (on-chip)</text>

  <!-- Typical latencies -->
  <text x="176" y="36" text-anchor="middle" font-size="11" fill="currentColor" fill-opacity="0.55">~1 ns (TLB)</text>
  <text x="298" y="36" text-anchor="middle" font-size="11" fill="currentColor" fill-opacity="0.55">~1 ns</text>
  <text x="416" y="36" text-anchor="middle" font-size="11" fill="currentColor" fill-opacity="0.55">~4 ns</text>
  <text x="534" y="36" text-anchor="middle" font-size="11" fill="currentColor" fill-opacity="0.55">~15 ns</text>
  <text x="669" y="36" text-anchor="middle" font-size="11" fill="currentColor" fill-opacity="0.55">~80 ns</text>

  <!-- Nodes -->
  <rect x="20" y="44" width="68" height="44" rx="6" fill="currentColor" fill-opacity="0.07" stroke="currentColor" stroke-opacity="0.55" stroke-width="1.2"/>
  <text x="54" y="70" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.9">Core</text>

  <rect x="138" y="44" width="76" height="44" rx="6" fill="currentColor" fill-opacity="0.07" stroke="currentColor" stroke-opacity="0.55" stroke-width="1.2"/>
  <text x="176" y="70" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.9">MMU</text>

  <rect x="264" y="44" width="68" height="44" rx="6" fill="currentColor" fill-opacity="0.07" stroke="currentColor" stroke-opacity="0.55" stroke-width="1.2"/>
  <text x="298" y="62" text-anchor="middle" font-size="12.5" font-weight="600" fill="currentColor" fill-opacity="0.95">L1</text>
  <text x="298" y="77" text-anchor="middle" font-size="9.5" fill="currentColor" fill-opacity="0.6">64–128 KB</text>

  <rect x="382" y="44" width="68" height="44" rx="6" fill="currentColor" fill-opacity="0.07" stroke="currentColor" stroke-opacity="0.55" stroke-width="1.2"/>
  <text x="416" y="62" text-anchor="middle" font-size="12.5" font-weight="600" fill="currentColor" fill-opacity="0.95">L2</text>
  <text x="416" y="77" text-anchor="middle" font-size="9.5" fill="currentColor" fill-opacity="0.6">4–16 MB</text>

  <rect x="500" y="44" width="68" height="44" rx="6" fill="currentColor" fill-opacity="0.07" stroke="currentColor" stroke-opacity="0.55" stroke-width="1.2"/>
  <text x="534" y="62" text-anchor="middle" font-size="12.5" font-weight="600" fill="currentColor" fill-opacity="0.95">L3</text>
  <text x="534" y="77" text-anchor="middle" font-size="9.5" fill="currentColor" fill-opacity="0.6">24–32 MB</text>

  <rect x="632" y="44" width="74" height="44" rx="6" fill="currentColor" fill-opacity="0.07" stroke="currentColor" stroke-opacity="0.55" stroke-width="1.2"/>
  <text x="669" y="62" text-anchor="middle" font-size="12.5" font-weight="600" fill="currentColor" fill-opacity="0.95">DRAM</text>
  <text x="669" y="77" text-anchor="middle" font-size="9.5" fill="currentColor" fill-opacity="0.6">16–64 GB</text>

  <!-- Forward arrows -->
  <line x1="88" y1="66" x2="132" y2="66" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>
  <path d="M130,62.5 L136,66 L130,69.5" fill="none" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>
  <text x="112" y="58" text-anchor="middle" font-size="11.5" fill="currentColor" fill-opacity="0.65">VA</text>

  <line x1="214" y1="66" x2="258" y2="66" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>
  <path d="M256,62.5 L262,66 L256,69.5" fill="none" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>
  <text x="238" y="58" text-anchor="middle" font-size="11.5" fill="currentColor" fill-opacity="0.65">PA</text>

  <line x1="332" y1="66" x2="376" y2="66" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>
  <path d="M374,62.5 L380,66 L374,69.5" fill="none" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>
  <text x="356" y="58" text-anchor="middle" font-size="11" fill="currentColor" fill-opacity="0.55">miss</text>

  <line x1="450" y1="66" x2="494" y2="66" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>
  <path d="M492,62.5 L498,66 L492,69.5" fill="none" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>
  <text x="474" y="58" text-anchor="middle" font-size="11" fill="currentColor" fill-opacity="0.55">miss</text>

  <line x1="568" y1="66" x2="626" y2="66" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>
  <path d="M624,62.5 L630,66 L624,69.5" fill="none" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>
  <text x="600" y="58" text-anchor="middle" font-size="11" fill="currentColor" fill-opacity="0.55">miss</text>

  <!-- Return path (hit / data return to Core) -->
  <line x1="298" y1="88" x2="298" y2="128" stroke="currentColor" stroke-opacity="0.45" stroke-width="1.2"/>
  <text x="310" y="112" text-anchor="start" font-size="11" fill="currentColor" fill-opacity="0.55">hit</text>

  <line x1="416" y1="88" x2="416" y2="128" stroke="currentColor" stroke-opacity="0.45" stroke-width="1.2"/>
  <text x="428" y="112" text-anchor="start" font-size="11" fill="currentColor" fill-opacity="0.55">hit</text>

  <line x1="534" y1="88" x2="534" y2="128" stroke="currentColor" stroke-opacity="0.45" stroke-width="1.2"/>
  <text x="546" y="112" text-anchor="start" font-size="11" fill="currentColor" fill-opacity="0.55">hit</text>

  <line x1="669" y1="88" x2="669" y2="128" stroke="currentColor" stroke-opacity="0.45" stroke-width="1.2"/>

  <line x1="669" y1="128" x2="54" y2="128" stroke="currentColor" stroke-opacity="0.45" stroke-width="1.2"/>
  <line x1="54" y1="128" x2="54" y2="94" stroke="currentColor" stroke-opacity="0.45" stroke-width="1.2"/>
  <path d="M50.5,96 L54,90 L57.5,96" fill="none" stroke="currentColor" stroke-opacity="0.45" stroke-width="1.2"/>
</svg>

### Inside the MMU: Virtual to Physical Translation

Memory is divided into fixed-size blocks called pages (typically 4 KB or 16 KB). Because virtual pages and physical page frames have the same size, a virtual address (VA) splits into two fields: a Virtual Page Number (VPN) that identifies the page, and an Offset that locates the byte inside the page. Only the VPN needs translation; the Offset is copied unchanged into the physical address (PA).

To translate the VPN into a Physical Frame Number (PFN), the MMU follows three possible paths:

1. TLB hit (fast path): The MMU first checks the Translation Lookaside Buffer (TLB), an on-chip hardware cache of recent VPN-to-PFN mappings. On a hit, the PFN is returned in ~1 ns and concatenated with the Offset to form the PA.
2. TLB miss and page table walk: Page tables live in physical DRAM as a multi-level tree (typically 4 levels on x86-64 and ARM64, splitting the VPN into four 9-bit indices), anchored by a root register in the CPU (`CR3` or `TTBR`). On a TLB miss, the MMU's hardware page table walker steps through the tree up to 4 times—each non-leaf Page Table Entry (PTE) supplying the physical base address of the next-level table, and each step checking the L1/L2/L3 cache hierarchy first (~1–15 ns on a hit) before falling back to physical DRAM (~80 ns on a miss). If the final leaf PTE's present bit is set (`P = 1`), the MMU loads the translation into the TLB and outputs the PFN to form the PA.
3. Page fault (`P = 0`): If the present bit is zero, the target page is not in DRAM. The MMU raises a page fault exception (`#PF`) to the OS kernel, which loads the page from disk or swap (~µs–ms) into a physical frame in DRAM, updates the PTE, and restarts the instruction.

<svg viewBox="0 0 716 324" width="100%" style="max-width:716px;display:block;margin:1.5em auto;" role="img" aria-label="Virtual memory translation inside and outside the CPU chip: on-chip, VA splits into VPN and Offset; VPN checks the TLB (hit ~1 ns -> PFN, miss -> Page Table Walk -> L1/L2/L3 Cache, hit ~1-15 ns -> PTE). On a cache miss, the walk goes off-chip to DRAM (Page Table) (~80 ns) to fetch the PTE. Non-leaf PTEs loop back to the Page Table Walk across 4 levels; once the leaf PTE is reached with P=1, it loads the TLB and outputs PFN; if P=0, it raises a Page Fault (#PF) that goes off-chip to Disk / Swap (~us-ms).">
  <!-- On-chip CPU boundary -->
  <rect x="6" y="18" width="704" height="224" rx="8" fill="none" stroke="currentColor" stroke-opacity="0.3" stroke-width="1.2" stroke-dasharray="4,4"/>
  <text x="16" y="12" text-anchor="start" font-size="11" fill="currentColor" fill-opacity="0.5">CPU (on-chip)</text>

  <!-- VA (VPN | Offset) -->
  <text x="98" y="30" text-anchor="middle" font-size="11" fill="currentColor" fill-opacity="0.55">VA</text>
  <rect x="20" y="36" width="92" height="36" rx="4" fill="currentColor" fill-opacity="0.07" stroke="currentColor" stroke-opacity="0.55" stroke-width="1.2"/>
  <text x="66" y="58" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.9">VPN</text>
  <rect x="112" y="36" width="64" height="36" rx="4" fill="currentColor" fill-opacity="0.07" stroke="currentColor" stroke-opacity="0.55" stroke-width="1.2"/>
  <text x="144" y="58" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.9">Offset</text>

  <!-- PA (PFN | Offset) -->
  <text x="510" y="78" text-anchor="middle" font-size="11" fill="currentColor" fill-opacity="0.55">PA</text>
  <rect x="444" y="84" width="92" height="36" rx="4" fill="currentColor" fill-opacity="0.07" stroke="currentColor" stroke-opacity="0.55" stroke-width="1.2"/>
  <text x="490" y="106" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.9">PFN</text>
  <rect x="536" y="84" width="64" height="36" rx="4" fill="currentColor" fill-opacity="0.07" stroke="currentColor" stroke-opacity="0.55" stroke-width="1.2"/>
  <text x="568" y="106" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.9">Offset</text>

  <!-- Offset direct pass-through -->
  <line x1="176" y1="54" x2="568" y2="54" stroke="currentColor" stroke-opacity="0.45" stroke-width="1.2"/>
  <line x1="568" y1="54" x2="568" y2="78" stroke="currentColor" stroke-opacity="0.45" stroke-width="1.2"/>
  <path d="M564.5,76 L568,82 L571.5,76" fill="none" stroke="currentColor" stroke-opacity="0.45" stroke-width="1.2"/>

  <!-- TLB -->
  <rect x="116" y="84" width="96" height="36" rx="6" fill="currentColor" fill-opacity="0.07" stroke="currentColor" stroke-opacity="0.55" stroke-width="1.2"/>
  <text x="164" y="106" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.9">TLB</text>

  <!-- VPN -> TLB -->
  <line x1="66" y1="72" x2="66" y2="102" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>
  <line x1="66" y1="102" x2="110" y2="102" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>
  <path d="M108,98.5 L114,102 L108,105.5" fill="none" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>

  <!-- TLB --hit--> PFN -->
  <line x1="212" y1="102" x2="438" y2="102" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>
  <path d="M436,98.5 L442,102 L436,105.5" fill="none" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>
  <text x="328" y="94" text-anchor="middle" font-size="11" fill="currentColor" fill-opacity="0.55">hit (~1 ns)</text>

  <!-- TLB --miss--> Page Table Walk -->
  <line x1="128" y1="120" x2="128" y2="178" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>
  <path d="M124.5,176 L128,182 L131.5,176" fill="none" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>
  <text x="118" y="154" text-anchor="end" font-size="11" fill="currentColor" fill-opacity="0.55">miss</text>

  <!-- Page Table Walk -->
  <rect x="44" y="184" width="136" height="44" rx="6" fill="currentColor" fill-opacity="0.07" stroke="currentColor" stroke-opacity="0.55" stroke-width="1.2"/>
  <text x="112" y="203" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.9">Page Table Walk</text>
  <text x="112" y="219" text-anchor="middle" font-size="10.5" fill="currentColor" fill-opacity="0.55">MMU (CR3 / TTBR)</text>

  <!-- Page Table Walk -> L1/L2/L3 Cache -->
  <line x1="180" y1="206" x2="210" y2="206" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>
  <path d="M208,202.5 L214,206 L208,209.5" fill="none" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>

  <!-- 1. L1 / L2 / L3 Cache (on-chip) -->
  <rect x="216" y="186" width="128" height="40" rx="6" fill="currentColor" fill-opacity="0.07" stroke="currentColor" stroke-opacity="0.55" stroke-width="1.2"/>
  <text x="280" y="210" text-anchor="middle" font-size="12.5" fill="currentColor" fill-opacity="0.9">L1 / L2 / L3 Cache</text>

  <!-- Cache --hit--> PTE -->
  <line x1="344" y1="206" x2="440" y2="206" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>
  <path d="M438,202.5 L444,206 L438,209.5" fill="none" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>
  <text x="395" y="198" text-anchor="middle" font-size="11" fill="currentColor" fill-opacity="0.55">hit (~1–15 ns)</text>

  <!-- Cache --miss--> DRAM (Page Table) (off-chip) -->
  <line x1="280" y1="226" x2="280" y2="268" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>
  <path d="M276.5,266 L280,272 L283.5,266" fill="none" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>
  <text x="290" y="260" text-anchor="start" font-size="11" fill="currentColor" fill-opacity="0.55">miss</text>

  <!-- 2. DRAM (Page Table) (off-chip) -->
  <rect x="216" y="274" width="128" height="40" rx="6" fill="currentColor" fill-opacity="0.07" stroke="currentColor" stroke-opacity="0.55" stroke-width="1.2"/>
  <text x="280" y="298" text-anchor="middle" font-size="12.5" fill="currentColor" fill-opacity="0.9">DRAM (Page Table)</text>

  <!-- DRAM --> PTE -->
  <line x1="344" y1="294" x2="490" y2="294" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>
  <line x1="490" y1="294" x2="490" y2="232" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>
  <path d="M486.5,234 L490,228 L493.5,234" fill="none" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>
  <text x="417" y="286" text-anchor="middle" font-size="11" fill="currentColor" fill-opacity="0.55">~80 ns</text>

  <!-- PTE -->
  <rect x="446" y="186" width="88" height="40" rx="6" fill="currentColor" fill-opacity="0.07" stroke="currentColor" stroke-opacity="0.55" stroke-width="1.2"/>
  <text x="490" y="210" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.9">PTE</text>

  <!-- PTE --next level (x4)--> Page Table Walk -->
  <line x1="464" y1="186" x2="464" y2="162" stroke="currentColor" stroke-opacity="0.45" stroke-width="1.2"/>
  <line x1="464" y1="162" x2="158" y2="162" stroke="currentColor" stroke-opacity="0.45" stroke-width="1.2"/>
  <line x1="158" y1="162" x2="158" y2="178" stroke="currentColor" stroke-opacity="0.45" stroke-width="1.2"/>
  <path d="M154.5,176 L158,182 L161.5,176" fill="none" stroke="currentColor" stroke-opacity="0.45" stroke-width="1.2"/>
  <text x="311" y="156" text-anchor="middle" font-size="10.5" fill="currentColor" fill-opacity="0.55">next level (×4)</text>

  <!-- PTE --leaf (P=1)--> PFN & Load into TLB -->
  <line x1="504" y1="186" x2="504" y2="126" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>
  <path d="M500.5,128 L504,122 L507.5,128" fill="none" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>
  <text x="514" y="160" text-anchor="start" font-size="11" fill="currentColor" fill-opacity="0.55">P = 1 (leaf)</text>

  <line x1="504" y1="136" x2="188" y2="136" stroke="currentColor" stroke-opacity="0.45" stroke-width="1.2" stroke-dasharray="4,3"/>
  <line x1="188" y1="136" x2="188" y2="126" stroke="currentColor" stroke-opacity="0.45" stroke-width="1.2" stroke-dasharray="4,3"/>
  <path d="M184.5,128 L188,122 L191.5,128" fill="none" stroke="currentColor" stroke-opacity="0.45" stroke-width="1.2"/>
  <text x="346" y="130" text-anchor="middle" font-size="10.5" fill="currentColor" fill-opacity="0.55">load into TLB</text>

  <!-- PTE --P=0--> Page Fault (#PF) -->
  <line x1="534" y1="206" x2="582" y2="206" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>
  <path d="M580,202.5 L586,206 L580,209.5" fill="none" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>
  <text x="560" y="198" text-anchor="middle" font-size="11" fill="currentColor" fill-opacity="0.55">P = 0</text>

  <!-- Page Fault (#PF) -->
  <rect x="588" y="186" width="108" height="40" rx="6" fill="currentColor" fill-opacity="0.07" stroke="currentColor" stroke-opacity="0.55" stroke-width="1.2"/>
  <text x="642" y="210" text-anchor="middle" font-size="12.5" fill="currentColor" fill-opacity="0.9">Page Fault (#PF)</text>

  <!-- Page Fault (#PF) -> Disk / Swap (off-chip) -->
  <line x1="642" y1="226" x2="642" y2="268" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>
  <path d="M638.5,266 L642,272 L645.5,266" fill="none" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>
  <text x="652" y="260" text-anchor="start" font-size="11" fill="currentColor" fill-opacity="0.55">~µs–ms</text>

  <!-- Disk / Swap (off-chip) -->
  <rect x="594" y="274" width="96" height="40" rx="6" fill="currentColor" fill-opacity="0.07" stroke="currentColor" stroke-opacity="0.55" stroke-width="1.2"/>
  <text x="642" y="298" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.9">Disk / Swap</text>
</svg>

### Inside the Cache: A Hardware-Implemented Hash Table

Once the MMU produces a 64-bit Physical Address (or while lookup is overlapped), how does the CPU check whether that address is in L1, L2, or L3 cache? It cannot loop through thousands of cache lines in software fashion. Instead, a CPU cache is built as a hardware-implemented hash table with fixed-capacity buckets ($N$-way set-associative mapping).

For a typical 32 KB, 8-way set-associative L1 cache with 64-byte cache lines and 64 sets ($64 \times 8 \times 64\text{ B} = 32\text{ KB}$), hardware slices the 64-bit address directly via wire routing into three bitfields:

- Offset ($\text{address} \bmod 2^6$, bits $[5:0]$): Selects the exact byte ($0\text{–}63$) inside the 64-byte cache line.
- Index ($(\text{address} \gg 6) \bmod 2^6$, bits $[11:6]$): Acts as the bucket index. A hardware row decoder uses these 6 bits to energize 1 of the 64 sets immediately—never touching the other 63 sets.
- Tag ($\text{address} \gg 12$, bits $[63:12]$): Acts as the lookup key. Because many different addresses share the same lower 12 bits and map to the same set, the upper 52 bits identify which specific memory block currently occupies each slot.

<svg viewBox="0 0 716 248" width="100%" style="max-width:716px;display:block;margin:1.5em auto;" role="img" aria-label="Set-associative cache lookup: 64-bit Physical Address splits into Tag (52 bits, key), Index (6 bits, set), and Offset (6 bits, byte). Index decodes 1 of 64 sets containing 8 ways; Tag is compared in parallel across all 8 ways in a single cycle; on a hit, Offset selects the requested bytes from the matching 64-byte cache line.">
  <!-- PA Bitfields -->
  <text x="88" y="16" text-anchor="middle" font-size="11" fill="currentColor" fill-opacity="0.55">key (bits 63:12)</text>
  <rect x="20" y="24" width="136" height="36" rx="4" fill="currentColor" fill-opacity="0.07" stroke="currentColor" stroke-opacity="0.55" stroke-width="1.2"/>
  <text x="88" y="46" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.9">Tag (52b)</text>

  <text x="204" y="16" text-anchor="middle" font-size="11" fill="currentColor" fill-opacity="0.55">bucket (bits 11:6)</text>
  <rect x="156" y="24" width="96" height="36" rx="4" fill="currentColor" fill-opacity="0.07" stroke="currentColor" stroke-opacity="0.55" stroke-width="1.2"/>
  <text x="204" y="46" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.9">Index (6b)</text>

  <text x="298" y="16" text-anchor="middle" font-size="11" fill="currentColor" fill-opacity="0.55">byte (bits 5:0)</text>
  <rect x="252" y="24" width="92" height="36" rx="4" fill="currentColor" fill-opacity="0.07" stroke="currentColor" stroke-opacity="0.55" stroke-width="1.2"/>
  <text x="298" y="46" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.9">Offset (6b)</text>

  <!-- Step 1: Index -> Activated Set -->
  <line x1="204" y1="60" x2="204" y2="98" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>
  <path d="M200.5,96 L204,102 L207.5,96" fill="none" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>
  <text x="214" y="84" text-anchor="start" font-size="11" fill="currentColor" fill-opacity="0.55">1. decode 1 of 64 sets</text>

  <!-- Activated Set (8 Ways) -->
  <rect x="128" y="104" width="388" height="72" rx="6" fill="none" stroke="currentColor" stroke-opacity="0.35" stroke-width="1.2" stroke-dasharray="4,4"/>
  <text x="322" y="120" text-anchor="middle" font-size="11" fill="currentColor" fill-opacity="0.55">Activated Set (8-Way Bucket in SRAM)</text>

  <rect x="140" y="128" width="104" height="38" rx="4" fill="currentColor" fill-opacity="0.07" stroke="currentColor" stroke-opacity="0.55" stroke-width="1.2"/>
  <text x="192" y="145" text-anchor="middle" font-size="12" fill="currentColor" fill-opacity="0.9">Way 0</text>
  <text x="192" y="159" text-anchor="middle" font-size="10" fill="currentColor" fill-opacity="0.55">V | Tag | 64B</text>

  <rect x="256" y="128" width="104" height="38" rx="4" fill="currentColor" fill-opacity="0.07" stroke="currentColor" stroke-opacity="0.55" stroke-width="1.2"/>
  <text x="308" y="145" text-anchor="middle" font-size="12" fill="currentColor" fill-opacity="0.9">Way 1</text>
  <text x="308" y="159" text-anchor="middle" font-size="10" fill="currentColor" fill-opacity="0.55">V | Tag | 64B</text>

  <text x="379" y="151" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.6">...</text>

  <rect x="398" y="128" width="104" height="38" rx="4" fill="currentColor" fill-opacity="0.07" stroke="currentColor" stroke-opacity="0.55" stroke-width="1.2"/>
  <text x="450" y="145" text-anchor="middle" font-size="12" fill="currentColor" fill-opacity="0.9">Way 7</text>
  <text x="450" y="159" text-anchor="middle" font-size="10" fill="currentColor" fill-opacity="0.55">V | Tag | 64B</text>

  <!-- Ways -> Parallel Tag Comparators -->
  <line x1="192" y1="166" x2="192" y2="192" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>
  <path d="M188.5,190 L192,196 L195.5,190" fill="none" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>

  <line x1="308" y1="166" x2="308" y2="192" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>
  <path d="M304.5,190 L308,196 L311.5,190" fill="none" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>

  <line x1="450" y1="166" x2="450" y2="192" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>
  <path d="M446.5,190 L450,196 L453.5,190" fill="none" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>

  <!-- Step 2: Tag -> Parallel Tag Comparators -->
  <line x1="88" y1="60" x2="88" y2="216" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>
  <line x1="88" y1="216" x2="134" y2="216" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>
  <path d="M132,212.5 L138,216 L132,219.5" fill="none" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>

  <rect x="140" y="198" width="362" height="36" rx="6" fill="currentColor" fill-opacity="0.07" stroke="currentColor" stroke-opacity="0.55" stroke-width="1.2"/>
  <text x="321" y="220" text-anchor="middle" font-size="12.5" fill="currentColor" fill-opacity="0.9">2. Parallel Tag Comparators (V = 1 &amp; Tag == Key)</text>

  <!-- Step 3: Hit + Offset -> Target Data -->
  <line x1="502" y1="216" x2="564" y2="216" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>
  <path d="M562,212.5 L568,216 L562,219.5" fill="none" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.2"/>
  <text x="534" y="208" text-anchor="middle" font-size="11" fill="currentColor" fill-opacity="0.55">hit (64B)</text>

  <line x1="344" y1="42" x2="634" y2="42" stroke="currentColor" stroke-opacity="0.45" stroke-width="1.2"/>
  <line x1="634" y1="42" x2="634" y2="192" stroke="currentColor" stroke-opacity="0.45" stroke-width="1.2"/>
  <path d="M630.5,190 L634,196 L637.5,190" fill="none" stroke="currentColor" stroke-opacity="0.45" stroke-width="1.2"/>
  <text x="624" y="120" text-anchor="end" font-size="11" fill="currentColor" fill-opacity="0.55">3. select byte</text>

  <rect x="570" y="198" width="128" height="36" rx="6" fill="currentColor" fill-opacity="0.07" stroke="currentColor" stroke-opacity="0.55" stroke-width="1.2"/>
  <text x="634" y="220" text-anchor="middle" font-size="12.5" fill="currentColor" fill-opacity="0.9">Target Data</text>
</svg>

Inside the selected set, hardware resolves lookups and collisions in a single clock cycle:

1. Parallel $O(1)$ tag matching: An 8-way set contains 8 slots ("ways"). Rather than scanning ways $0\text{–}7$ sequentially, 8 physical comparator circuits compare the incoming `Tag` against all 8 stored tags simultaneously while checking that the entry's Valid bit ($V$) is `1`.
2. Allocation and eviction on a miss: Each way stores a Valid bit ($V = 0$ when empty, $V = 1$ when occupied) and a Dirty bit ($D = 1$ when modified by a store). On a cache miss, a hardware priority encoder checks the 8 valid bits in parallel: if any way has $V = 0$, the fetched 64-byte line is placed into that open slot; if all 8 ways have $V = 1$, replacement logic (such as Pseudo-LRU) evicts one entry—discarding it if clean ($D = 0$) or writing it back down the hierarchy if dirty ($D = 1$).

### References

1. [wangzhihao/otterix](https://github.com/wangzhihao/otterix), a finance example: Market Data Replay and Order Book Reconstruction.

