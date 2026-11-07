#!/usr/bin/env python3
"""
Generate an inline SVG plot of Poisson Probability Mass Functions across varying arrival intensities (lambda = 1, 4, 10, 20).
Adheres to marsset.github.io inline SVG standards with currentColor for automatic light/dark mode adaptation.
"""

import math

def poisson_pmf(k, lam):
    return (lam**k * math.exp(-lam)) / math.factorial(k)

def catmull_rom_to_bezier(pts):
    if len(pts) < 2:
        return ""
    d = f"M {pts[0][0]:.2f} {pts[0][1]:.2f}"
    for i in range(len(pts) - 1):
        p0 = pts[i - 1] if i > 0 else pts[i]
        p1 = pts[i]
        p2 = pts[i + 1]
        p3 = pts[i + 2] if i + 2 < len(pts) else p2
        
        cpx1 = p1[0] + (p2[0] - p0[0]) / 6.0
        cpy1 = p1[1] + (p2[1] - p0[1]) / 6.0
        cpx2 = p2[0] - (p3[0] - p1[0]) / 6.0
        cpy2 = p2[1] - (p3[1] - p1[1]) / 6.0
        d += f" C {cpx1:.2f} {cpy1:.2f}, {cpx2:.2f} {cpy2:.2f}, {p2[0]:.2f} {p2[1]:.2f}"
    return d

def generate_svg():
    W, H = 840, 500
    L, R, T, B = 70, 805, 50, 420
    PW = R - L
    PH = B - T
    max_k = 32
    max_p = 0.40

    def fx(k):
        return L + (k / max_k) * PW

    def fy(p):
        return B - (p / max_p) * PH

    svg = []
    svg.append(f"""<figure style="margin: 2.2em auto; text-align: center;">
<svg viewBox="0 0 {W} {H}" width="100%" style="max-width:{W}px;display:block;margin:0 auto;font-family:-apple-system,BlinkMacSystemFont,\x27Segoe UI\x27,Roboto,sans-serif;" role="img" aria-label="Poisson distribution probability mass functions for lambda equals 1, 4, 10, and 20">
  <defs>
    <style>
      .p-axis {{ stroke: currentColor; stroke-opacity: 0.5; stroke-width: 1.2; }}
      .p-grid {{ stroke: currentColor; stroke-opacity: 0.08; stroke-dasharray: 3,3; stroke-width: 1; }}
      .p-tick {{ fill: currentColor; font-size: 11.5px; fill-opacity: 0.65; }}
      .p-axis-title {{ fill: currentColor; font-size: 13px; font-weight: 500; fill-opacity: 0.85; }}
      .p-legend-title {{ fill: currentColor; font-size: 12px; font-weight: 600; fill-opacity: 0.9; }}
      .p-legend-text {{ fill: currentColor; font-size: 11.5px; fill-opacity: 0.8; }}
      .p-annot {{ font-size: 11px; font-weight: 500; }}
    </style>
  </defs>""")

    # Horizontal grid and y-axis ticks
    for p_tick in [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40]:
        y = fy(p_tick)
        svg.append(f"  <line x1=\"{L}\" y1=\"{y:.2f}\" x2=\"{R}\" y2=\"{y:.2f}\" class=\"p-grid\" />")
        svg.append(f"  <text x=\"{L-10}\" y=\"{y+4:.2f}\" text-anchor=\"end\" class=\"p-tick\">{p_tick:.2f}</text>")

    # Vertical grid and x-axis ticks
    for k_tick in range(0, max_k + 1, 2):
        x = fx(k_tick)
        svg.append(f"  <line x1=\"{x:.2f}\" y1=\"{T}\" x2=\"{x:.2f}\" y2=\"{B}\" class=\"p-grid\" />")
        svg.append(f"  <text x=\"{x:.2f}\" y=\"{B+20:.2f}\" text-anchor=\"middle\" class=\"p-tick\">{k_tick}</text>")

    # Sub-ticks for odd k
    for k_tick in range(1, max_k + 1, 2):
        x = fx(k_tick)
        svg.append(f"  <line x1=\"{x:.2f}\" y1=\"{B}\" x2=\"{x:.2f}\" y2=\"{B+4}\" class=\"p-axis\" />")

    # Axes lines
    svg.append(f"  <line x1=\"{L}\" y1=\"{B}\" x2=\"{R}\" y2=\"{B}\" class=\"p-axis\" />")
    svg.append(f"  <line x1=\"{L}\" y1=\"{T}\" x2=\"{L}\" y2=\"{B}\" class=\"p-axis\" />")

    # Axis Titles
    svg.append(f"  <text x=\"{(L+R)/2:.1f}\" y=\"{B+48}\" text-anchor=\"middle\" class=\"p-axis-title\">Number of Occurrences (k)</text>")
    svg.append(f"  <text x=\"{L-46:.1f}\" y=\"{(T+B)/2:.1f}\" text-anchor=\"middle\" transform=\"rotate(-90, {L-46:.1f}, {(T+B)/2:.1f})\" class=\"p-axis-title\">Probability P(K = k)</text>")

    # Legend Box
    leg_w, leg_h = 190, 118
    leg_x, leg_y = R - leg_w - 5, T + 5
    svg.append(f"""  <g transform=\"translate({leg_x}, {leg_y})\">
    <rect x=\"0\" y=\"0\" width=\"{leg_w}\" height=\"{leg_h}\" rx=\"6\" fill=\"currentColor\" fill-opacity=\"0.04\" stroke=\"currentColor\" stroke-opacity=\"0.14\" />
    <text x=\"16\" y=\"20\" class=\"p-legend-title\">Mean Arrival Rate (λ)</text>""")

    series_data = [
        (1,  "#3b82f6", 0, 8,  "λ = 1 (σ = 1.00)"),
        (4,  "#10b981", 0, 14, "λ = 4 (σ = 2.00)"),
        (10, "#f59e0b", 1, 22, "λ = 10 (σ = 3.16)"),
        (20, "#8b5cf6", 7, 32, "λ = 20 (σ = 4.47)")
    ]

    for idx, (lam, col, k_min, k_max, label) in enumerate(series_data):
        ly = 40 + idx * 20
        svg.append(f"    <circle cx=\"24\" cy=\"{ly}\" r=\"4\" fill=\"{col}\" />")
        svg.append(f"    <line x1=\"12\" y1=\"{ly}\" x2=\"36\" y2=\"{ly}\" stroke=\"{col}\" stroke-width=\"2\" />")
        svg.append(f"    <text x=\"46\" y=\"{ly+3.5:.1f}\" class=\"p-legend-text\">{label}</text>")
    svg.append("  </g>")

    # Draw series
    for lam, col, k_min, k_max, _ in series_data:
        pts = []
        for k in range(k_min, k_max + 1):
            p = poisson_pmf(k, lam)
            pts.append((fx(k), fy(p), k, p))
        
        # 1. Stems
        for x, y, k, p in pts:
            svg.append(f"  <line x1=\"{x:.2f}\" y1=\"{B}\" x2=\"{x:.2f}\" y2=\"{y:.2f}\" stroke=\"{col}\" stroke-width=\"1.2\" stroke-opacity=\"0.35\" />")
        
        # 2. Translucent Area
        curve_pts = [(x, y) for x, y, _, _ in pts]
        bezier_d = catmull_rom_to_bezier(curve_pts)
        first_x, first_y = curve_pts[0]
        last_x, last_y = curve_pts[-1]
        area_d = f"{bezier_d} L {last_x:.2f} {B} L {first_x:.2f} {B} Z"
        svg.append(f"  <path d=\"{area_d}\" fill=\"{col}\" fill-opacity=\"0.07\" />")

        # 3. Smooth Curve
        svg.append(f"  <path d=\"{bezier_d}\" fill=\"none\" stroke=\"{col}\" stroke-width=\"2.2\" />")

        # 4. Marker dots
        for x, y, k, p in pts:
            svg.append(f"  <circle cx=\"{x:.2f}\" cy=\"{y:.2f}\" r=\"3.8\" fill=\"{col}\" stroke=\"currentColor\" stroke-opacity=\"0.1\" stroke-width=\"1\" />")

    # Vertical mean reference markers
    for lam, col, _, _, _ in series_data:
        mx = fx(lam)
        p_mean = poisson_pmf(lam, lam)
        my = fy(p_mean)
        svg.append(f"  <line x1=\"{mx:.2f}\" y1=\"{my}\" x2=\"{mx:.2f}\" y2=\"{B}\" stroke=\"{col}\" stroke-width=\"1.4\" stroke-dasharray=\"4,3\" stroke-opacity=\"0.7\" />")
        svg.append(f"  <text x=\"{mx:.2f}\" y=\"{my-8:.2f}\" text-anchor=\"middle\" fill=\"{col}\" class=\"p-annot\">μ={lam}</text>")

    svg.append("""</svg>
</figure>""")

    return "\n".join(svg)

if __name__ == "__main__":
    print(generate_svg())
