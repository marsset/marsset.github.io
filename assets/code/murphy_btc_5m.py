"""Murphy Decomposition on Polymarket 5-Minute BTC Up-Down Orderbook Data.

Usage:
    python3 murphy_btc_5m.py --data-dir ./data/real --days 30

Each round file (btc-updown-5m-<ts>.json.gz) contains orderbook snapshots:
    ticks[i] = {"t": float, "upBid": float, "upAsk": float, "downBid": float, "downAsk": float, ...}
and the resolved binary outcome ("Up" -> Y = 1, "Down" -> Y = 0).
"""

import argparse
from concurrent.futures import ProcessPoolExecutor
import gzip
import json
import os
import time
import numpy as np

TARGETS = [15, 30, 60, 90, 120, 150, 180, 210, 240, 270]


def parse_round(path: str):
    """Extract binary outcome Y in {0, 1} and UP mid-prices Q_poly(t) at TARGETS."""
    try:
        with gzip.open(path, "rt") as fp:
            d = json.load(fp)
    except Exception:
        return None

    ticks = d.get("ticks") or []
    if len(ticks) < 10:
        return None

    res = d.get("resolution")
    if not res:
        last = ticks[-1]
        ua, da = last.get("upAsk", 0.5), last.get("downAsk", 0.5)
        if ua >= 0.95 and da <= 0.10:
            res = "Up"
        elif da >= 0.95 and ua <= 0.10:
            res = "Down"
    if res not in ("Up", "Down"):
        return None

    y = 1 if res == "Up" else 0
    out = [None] * len(TARGETS)
    idx = 0
    n = len(ticks)

    for ti, targ in enumerate(TARGETS):
        while idx + 1 < n and ticks[idx + 1].get("t", 0) <= targ:
            idx += 1
        tk = ticks[idx]
        t_val = tk.get("t", 0)
        if abs(t_val - targ) <= 10.0:
            ub, ua = tk.get("upBid"), tk.get("upAsk")
            if ub is not None and ua is not None and 0.0 <= ub <= ua <= 1.0:
                out[ti] = 0.5 * (ub + ua)
    return (y, out)


def murphy(y: np.ndarray, q: np.ndarray, n_bins: int = 10):
    """Compute binned Murphy (1973) decomposition: BS = UNC - RES + REL."""
    N = len(y)
    p = float(y.mean())
    unc = p * (1.0 - p)
    bs_direct = float(np.mean((y - q) ** 2))

    edges = np.linspace(0.0, 1.0, n_bins + 1)
    bin_idx = np.clip(np.digitize(q, edges) - 1, 0, n_bins - 1)

    res = 0.0
    rel = 0.0
    rows = []
    for k in range(n_bins):
        mask = bin_idx == k
        nk = int(mask.sum())
        if nk == 0:
            continue
        fk = float(q[mask].mean())
        yk = float(y[mask].mean())
        res += (nk / N) * ((yk - p) ** 2)
        rel += (nk / N) * ((fk - yk) ** 2)
        rows.append((k, edges[k], edges[k + 1], nk, fk, yk))

    bs_decomp = unc - res + rel
    bss = (res - rel) / unc
    return dict(
        N=N,
        p=p,
        unc=unc,
        res=res,
        rel=rel,
        bs_direct=bs_direct,
        bs_decomp=bs_decomp,
        bss=bss,
        rows=rows,
    )


def main():
    parser = argparse.ArgumentParser(description="Murphy decomposition on 5m BTC rounds")
    parser.add_argument("--data-dir", default="./data/real", help="Directory containing date folders")
    parser.add_argument("--days", type=int, default=30, help="Number of most recent trading days")
    args = parser.parse_args()

    t0 = time.time()
    dates = sorted(
        d for d in os.listdir(args.data_dir)
        if os.path.isdir(os.path.join(args.data_dir, d)) and d[:4].isdigit()
    )
    selected_dates = dates[-args.days :] if args.days > 0 else dates

    round_files = {}
    for d in selected_dates:
        dd = os.path.join(args.data_dir, d)
        for root, _, files in os.walk(dd):
            for f in files:
                if f.startswith("btc-updown-5m-") and f.endswith(".json.gz"):
                    slug = f[:-8]
                    if slug not in round_files:
                        round_files[slug] = os.path.join(root, f)

    paths = list(round_files.values())
    with ProcessPoolExecutor() as ex:
        results = [r for r in ex.map(parse_round, paths, chunksize=64) if r is not None]

    ys = np.array([r[0] for r in results], dtype=np.float64)
    p_overall = ys.mean()
    unc_overall = p_overall * (1.0 - p_overall)
    print(f"Parsed {len(results)} resolved rounds in {time.time() - t0:.2f}s")
    print(f"Overall N={len(ys)} rounds, Up={int(ys.sum())}, p={p_overall:.4f}, UNC={unc_overall:.6f}")

    all_y, all_q = [], []
    for y, out in results:
        for q in out:
            if q is not None:
                all_y.append(y)
                all_q.append(q)
    all_y = np.array(all_y)
    all_q = np.array(all_q)

    m_all = murphy(all_y, all_q, n_bins=10)
    print("\n=== Pooled Across All Snapshot Times (10-bin Murphy) ===")
    print(
        f"N={m_all['N']}, p={m_all['p']:.4f}, UNC={m_all['unc']:.5f}, "
        f"RES={m_all['res']:.5f}, REL={m_all['rel']:.5f}, "
        f"BS={m_all['bs_decomp']:.5f}, BSS={m_all['bss'] * 100:.1f}%"
    )
    for _, lo, hi, nk, fk, yk in m_all["rows"]:
        print(
            f"  Bin [{lo:.1f}, {hi:.1f}): n={nk:6d} ({nk / m_all['N'] * 100:5.1f}%) | "
            f"Q={fk:.4f} | pi_Q={yk:.4f} | Q - pi_Q={fk - yk:+.4f}"
        )

    print("\n=== Murphy Decomposition by Time-In-Round t (sec) ===")
    for ti, targ in enumerate(TARGETS):
        yt = np.array([y for y, out in results if out[ti] is not None])
        qt = np.array([out[ti] for _, out in results if out[ti] is not None])
        mt = murphy(yt, qt, n_bins=10)
        print(
            f"  t={targ:3d}s (tau={300 - targ:3d}s): N={mt['N']:5d} | "
            f"UNC={mt['unc']:.4f} | RES={mt['res']:.4f} | REL={mt['rel']:.5f} | "
            f"BS={mt['bs_decomp']:.4f} | BSS={mt['bss'] * 100:5.1f}%"
        )


if __name__ == "__main__":
    main()
