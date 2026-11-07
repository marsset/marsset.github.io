# Project Rules & Guidelines: marsset.github.io

See full operational guidelines and editorial philosophy in [AGENTS.md](file:///Users/wangzhihao/Desktop/source/marsset.github.io/AGENTS.md).

## Core Principles (Mandatory Memory)

1. **Short, Concise Titles:**
   - Always prefer short, punchy titles (e.g. *"Poisson Distribution"*, *"Page Cache Thrashing"*, *"Zero-Copy Binary Parsing"*, *"Memory Ordering"*).
   - Avoid long compound titles, academic subtitles, or run-on explanatory clauses. Keep titles strictly under 3–4 words whenever possible, placing extended summaries into the `excerpt:` field.

2. **Publishing Policy:**
   - Never push to remote without explicit user instruction.
   - Clean professional English only.

3. **Systems Engineering Depth:**
   - Always ground analyses in physical hardware reality (L1/L2/L3 caches, NUMA, PCIe, NVMe, kernel page tables, locks).

4. **Mobile Layout QA:**
   - Always run `python3 scripts/test_mobile_layout.py --fix` before publishing to ensure wide equations, SVGs, and tables never break mobile viewports.
