#!/usr/bin/env python3
"""
test_mobile_layout.py - Automated Mobile Phone Layout Quality Assurance & Auto-Fixer

Verifies that all posts and assets in marsset.github.io conform to mobile phone
screen constraints (e.g. iPhone / Android viewport widths ~360px - 430px).

Checks:
1. Responsive SVGs:
   - Must have `viewBox` attribute for scalable vector rendering.
   - Must have `width="100%"` and `style="max-width: ..."` to prevent horizontal blowout.
   - Auto-fix: automatically injects width="100%" and style="max-width: {W}px; display: block; margin: auto;".
2. Kramdown Display Math Blank Lines:
   - Display equations ($$) must be surrounded by blank lines so Kramdown parses them
     as true block-level MathJax containers (.MathJax_Display) rather than inline <p> math.
   - Auto-fix: inserts missing blank lines around $$ blocks.
3. Fixed Pixel Widths:
   - Elements with hardcoded width > 350px must have max-width: 100% constraints.
4. CSS Mobile Safeguards:
   - Validates that _sass/_custom.scss includes horizontal scrolling rules for MathJax
     (.MathJax_Display), responsive SVGs, and table scrolling.
5. SVG Font Size Legibility:
   - Font sizes in <svg> diagrams must be >= 12.0px to remain legible when scaled down
     on desktop and mobile screens.
   - Auto-fix: automatically bumps sub-12px font sizes to 12.0px.
6. Escaped Underscores:
   - Detects and repairs escaped underscores (e.g. \\text{sk\\_rcvbuf} or prose ident\\_name)
     that cause MathJax or markdown to render ugly literal backslashes on screen.
"""

import sys
import os
import re
import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = REPO_ROOT / "_posts"
CSS_FILE = REPO_ROOT / "_sass" / "_custom.scss"

def check_css_safeguards():
    """Verify that _sass/_custom.scss has all mandatory mobile responsive guards."""
    if not CSS_FILE.exists():
        return [f"CSS file missing: {CSS_FILE}"]
    
    content = CSS_FILE.read_text(encoding="utf-8")
    errors = []
    
    if "MathJax_Display" not in content or "overflow-x" not in content:
        errors.append("Missing .MathJax_Display overflow-x: auto in _sass/_custom.scss")
    if "max-width: 100%" not in content:
        errors.append("Missing max-width: 100% rules in _sass/_custom.scss")
    if "overflow-wrap: break-word" not in content and "word-wrap: break-word" not in content:
        errors.append("Missing overflow-wrap: break-word in _sass/_custom.scss")
    if "@media (max-width:" not in content and "@media(max-width:" not in content:
        errors.append("Missing mobile media query table rules in _sass/_custom.scss")
        
    return errors

def audit_and_fix_post(filepath: Path, fix: bool = False):
    """Audit a single markdown post for mobile phone layout hazards."""
    content = filepath.read_text(encoding="utf-8")
    original = content
    issues = []
    
    # -------------------------------------------------------------------------
    # 1. SVG Audit & Auto-Fix
    # -------------------------------------------------------------------------
    def fix_svg_match(match):
        full_tag = match.group(0)
        attrs = match.group(1)
        
        # Check viewBox
        vb_match = re.search(r'viewBox=["\']([^"\']+)["\']', attrs)
        has_vb = bool(vb_match)
        has_pct_width = bool(re.search(r'width=["\']100%["\']', attrs) or re.search(r'width\s*:\s*100%', attrs))
        has_max_width = bool(re.search(r'max-width\s*:', attrs))
        
        if not has_vb:
            # Check if width and height exist to synthesize viewBox
            w_match = re.search(r'width=["\'](\d+)["\']', attrs)
            h_match = re.search(r'height=["\'](\d+)["\']', attrs)
            if w_match and h_match:
                w, h = w_match.group(1), h_match.group(1)
                new_attrs = f' viewBox="0 0 {w} {h}" ' + attrs
                attrs = new_attrs
                has_vb = True
                vb_match = re.search(r'viewBox=["\']([^"\']+)["\']', attrs)
            else:
                issues.append(f"SVG missing viewBox: {full_tag[:70]}...")
                return full_tag
        
        # If viewBox is present but width="100%" or max-width is missing
        if has_vb and (not has_pct_width or not has_max_width):
            vb_parts = vb_match.group(1).split()
            max_w = vb_parts[2] if len(vb_parts) >= 3 else "800"
            
            # Clean up existing conflicting style or width
            new_attrs = attrs
            if not has_pct_width:
                # remove fixed width="..."
                new_attrs = re.sub(r'\bwidth=["\']\d+px?["\']', '', new_attrs)
                new_attrs = f' width="100%"' + new_attrs
            
            if not has_max_width:
                if 'style="' in new_attrs:
                    new_attrs = re.sub(r'style="([^"]*)"', lambda m: f'style="max-width:{max_w}px;display:block;margin:1.5em auto;{m.group(1)}"', new_attrs)
                elif "style='" in new_attrs:
                    new_attrs = re.sub(r"style='([^']*)'", lambda m: f"style='max-width:{max_w}px;display:block;margin:1.5em auto;{m.group(1)}'", new_attrs)
                else:
                    new_attrs += f' style="max-width:{max_w}px;display:block;margin:1.5em auto;"'
            
            new_tag = f"<svg{new_attrs}>"
            issues.append(f"Fixed unconstrained SVG: added width=100% and max-width:{max_w}px")
            return new_tag
            
        return full_tag

    if fix:
        content = re.sub(r'<svg([^>]*)>', fix_svg_match, content)
    else:
        for match in re.finditer(r'<svg([^>]*)>', content):
            attrs = match.group(1)
            has_vb = 'viewBox' in attrs
            has_pct = 'width="100%"' in attrs or 'width:100%' in attrs or 'width: 100%' in attrs
            if not has_vb:
                issues.append(f"SVG missing viewBox: {match.group(0)[:60]}...")
            elif not has_pct:
                issues.append(f"SVG missing responsive width='100%': {match.group(0)[:60]}...")

    # -------------------------------------------------------------------------
    # 2. Hardcoded large fixed pixel widths (> 350px) without max-width
    # -------------------------------------------------------------------------
    for match in re.finditer(r'width\s*[:=]\s*["\']?\s*(\d{3,4})px?', content):
        val = int(match.group(1))
        surrounding = content[max(0, match.start() - 60):min(len(content), match.end() + 60)]
        if val > 350 and 'max-width' not in surrounding and 'viewBox' not in surrounding:
            issues.append(f"Hardcoded fixed width {val}px without max-width near: {surrounding.strip()[:60]}...")

    # -------------------------------------------------------------------------
    # 3. Kramdown Display Math Blank Lines Enclosure
    # -------------------------------------------------------------------------
    # In Jekyll Kramdown, $$ preceded or followed immediately by a non-empty line
    # (except for quotes or code blocks) is rendered inline, breaking math display.
    lines = content.split('\n')
    new_lines = []
    in_code_block = False
    in_math_block = False
    math_modified = False

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            new_lines.append(line)
            continue
            
        if in_code_block:
            new_lines.append(line)
            continue

        # Check display math delimiter
        if stripped == "$$":
            if not in_math_block:
                # Opening $$
                # Check previous line
                if fix and len(new_lines) > 0 and new_lines[-1].strip() != "" and not new_lines[-1].strip().startswith("---"):
                    new_lines.append("")
                    math_modified = True
                    issues.append(f"Inserted missing blank line before opening $$ at line {i+1}")
                in_math_block = True
                new_lines.append(line)
            else:
                # Closing $$
                in_math_block = False
                new_lines.append(line)
                # Check next line
                if fix and i + 1 < len(lines) and lines[i+1].strip() != "":
                    new_lines.append("")
                    math_modified = True
                    issues.append(f"Inserted missing blank line after closing $$ at line {i+1}")
        else:
            new_lines.append(line)

    # -------------------------------------------------------------------------
    # 4. GFM Alert Check (> [!WARNING], > [!NOTE], etc.)
    # -------------------------------------------------------------------------
    # Kramdown does not support GitHub alerts; they render as raw text "[!WARNING]".
    # Minimal Mistakes requires <div class="notice--..." markdown="1">.
    alert_map = {
        "NOTE": "info",
        "TIP": "info",
        "IMPORTANT": "primary",
        "WARNING": "warning",
        "CAUTION": "danger",
    }
    for match in re.finditer(r'>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]', content):
        alert_type = match.group(1)
        notice_class = alert_map.get(alert_type, "warning")
        issues.append(f"GFM alert syntax > [!{alert_type}] found. Use <div class=\"notice--{notice_class}\" markdown=\"1\">")

    # -------------------------------------------------------------------------
    # 5. SVG Font Size Legibility Check & Auto-Fix
    # -------------------------------------------------------------------------
    # In scaled SVGs (viewBox ~800-960px), font sizes below 12.0px scale down to
    # sub-8pt on laptops and sub-4pt on phones, rendering text unreadable.
    # Minimum allowed font-size in any SVG is 12.0px.
    MIN_SVG_FONT_SIZE = 12.0
    def check_and_fix_font_sizes(svg_match):
        svg_text = svg_match.group(0)
        
        def replace_attr_font(m):
            val_str = m.group(1)
            try:
                val = float(val_str)
                if val < MIN_SVG_FONT_SIZE:
                    issues.append(f"SVG font-size=\"{val_str}\" is illegibly small (< {MIN_SVG_FONT_SIZE}px)")
                    if fix:
                        return f'font-size="{MIN_SVG_FONT_SIZE:.1f}"'
            except ValueError:
                pass
            return m.group(0)
            
        def replace_style_font(m):
            val_str = m.group(1)
            try:
                val = float(val_str)
                if val < MIN_SVG_FONT_SIZE:
                    issues.append(f"SVG style font-size:{val_str}px is illegibly small (< {MIN_SVG_FONT_SIZE}px)")
                    if fix:
                        return f'font-size:{MIN_SVG_FONT_SIZE:.1f}px'
            except ValueError:
                pass
            return m.group(0)

        new_svg = re.sub(r'font-size=["\']([0-9\.]+)["\']', replace_attr_font, svg_text)
        new_svg = re.sub(r'font-size\s*:\s*([0-9\.]+)px', replace_style_font, new_svg)
        return new_svg

    content = re.sub(r'<svg\b[^>]*>.*?</svg>', check_and_fix_font_sizes, content, flags=re.DOTALL)

    # -------------------------------------------------------------------------
    # 6. Escaped Underscores Check & Auto-Fix (\text{sk\_rcvbuf} / ident\_name)
    # -------------------------------------------------------------------------
    # In MathJax, writing \_ inside \text{...} causes literal backslashes to render
    # on screen (e.g. "sk\_rcvbuf" instead of "sk_rcvbuf").
    # In prose, escaped underscores like variable\_name are formatting artifacts.
    def fix_escaped_underscores_in_text(match):
        full_text_block = match.group(0)
        if r"\_" in full_text_block:
            issues.append(f"Escaped underscore in MathJax text: {full_text_block[:50]}")
            if fix:
                return full_text_block.replace(r"\_", "_")
        return full_text_block

    content = re.sub(r'\\text\{[^}]*\}', fix_escaped_underscores_in_text, content)
    content = re.sub(r'\\mathrm\{[^}]*\}', fix_escaped_underscores_in_text, content)
    content = re.sub(r'\\operatorname\{[^}]*\}', fix_escaped_underscores_in_text, content)

    # In prose outside code blocks, check for word\_word
    lines_prose = content.split('\n')
    new_lines_prose = []
    in_code = False
    in_math = False
    prose_modified = False
    for line in lines_prose:
        st = line.strip()
        if st.startswith("```"):
            in_code = not in_code
            new_lines_prose.append(line)
            continue
        if in_code:
            new_lines_prose.append(line)
            continue
        if st == "$$":
            in_math = not in_math
            new_lines_prose.append(line)
            continue
        if in_math:
            new_lines_prose.append(line)
            continue

        # Look for words with \_ outside inline code `...`
        parts = line.split('`')
        line_changed = False
        for idx in range(0, len(parts), 2):  # even index = outside inline code
            part = parts[idx]
            escaped_words = re.findall(r'\b\w+\\_\w+\b', part)
            for ew in escaped_words:
                issues.append(f"Escaped underscore in prose: '{ew}'")
                if fix:
                    parts[idx] = parts[idx].replace(ew, ew.replace(r'\_', '_'))
                    line_changed = True
                    prose_modified = True
        if line_changed:
            new_lines_prose.append('`'.join(parts))
        else:
            new_lines_prose.append(line)

    if fix and prose_modified:
        content = '\n'.join(new_lines_prose)

    if fix and math_modified:
        content = '\n'.join(new_lines)

    # If changes made, write back
    if fix and content != original:
        filepath.write_text(content, encoding="utf-8")
        
    return issues

def main():
    parser = argparse.ArgumentParser(description="Audit and fix mobile phone layout hazards in blog posts.")
    parser.add_argument("--fix", action="store_true", default=False, help="Automatically repair layout hazards.")
    parser.add_argument("--post", type=str, default=None, help="Check a specific post filename.")
    args = parser.parse_args()

    print("=" * 70)
    print(" Running Mobile Phone Layout QA Test (marsset.github.io)")
    print("=" * 70)

    # 1. CSS Safeguards Audit
    css_errors = check_css_safeguards()
    if css_errors:
        print("\n[FAIL] CSS Mobile Safeguards Issues:")
        for err in css_errors:
            print(f"  • {err}")
    else:
        print("[PASS] CSS Mobile Safeguards Verified (_sass/_custom.scss)")

    # 2. Posts Audit
    if args.post:
        target_path = POSTS_DIR / args.post if not Path(args.post).is_file() else Path(args.post)
        posts = [target_path]
    else:
        posts = sorted(POSTS_DIR.glob("*.markdown"))

    total_issues = 0
    fixed_count = 0
    posts_with_issues = 0

    for post in posts:
        issues = audit_and_fix_post(post, fix=args.fix)
        if issues:
            posts_with_issues += 1
            total_issues += len(issues)
            status_label = "[FIXED]" if args.fix else "[FAIL]"
            print(f"\n{status_label} {post.name}:")
            for issue in issues:
                print(f"  • {issue}")
                if "Fixed" in issue or "Inserted" in issue:
                    fixed_count += 1

    print("\n" + "-" * 70)
    print(f"Audit Summary: {len(posts)} posts scanned.")
    if total_issues == 0 and not css_errors:
        print("[ALL PASS] 100% of posts and CSS conform to mobile phone layout!")
        return 0
    elif args.fix and not css_errors:
        print(f"[REPAIRED] Auto-fixed {fixed_count} issue(s) across {posts_with_issues} post(s).")
        # Run a second pass to guarantee clean pass
        remaining = 0
        for post in posts:
            issues = audit_and_fix_post(post, fix=False)
            remaining += len(issues)
        if remaining == 0:
            print("[VERIFIED] Post-repair re-scan passed with 0 remaining errors.")
            return 0
        else:
            print(f"[WARN] {remaining} unfixable issue(s) require manual review.")
            return 1
    else:
        print(f"[FAIL] Found {total_issues} issue(s) across {posts_with_issues} post(s).")
        print("Run with --fix to automatically repair standard layout hazards.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
