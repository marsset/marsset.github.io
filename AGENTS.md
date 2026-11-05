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
