#!/usr/bin/env python3
"""
Walk-forward edge hunt for gold (GC=F).
For each strategy: optimise parameters on the first 60% of history (in-sample),
then judge ONLY on the last 40% it never saw (out-of-sample). A strategy earns
attention only if its OUT-OF-SAMPLE Sharpe and return are positive net of costs.
Position-based (long/short/flat); cost charged on every position change.
"""
import json, math, urllib.request

UA = {"User-Agent": "Mozilla/5.0"}
COST = 0.0002  # per side, fraction of price (~conservative gold spread/slippage)
BARS_PER_YEAR = {"1h": 6000, "1d": 252, "15m": 24000}


def fetch(interval, rng):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/GC=F?interval={interval}&range={rng}"
    d = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read())
    r = d["chart"]["result"][0]
    q = r["indicators"]["quote"][0]
    o, h, l, c = q["open"], q["high"], q["low"], q["close"]
    out = [(o[i], h[i], l[i], c[i]) for i in range(len(c)) if None not in (o[i], h[i], l[i], c[i])]
    return out


def sma(xs, i, n):
    if i + 1 < n:
        return None
    s = xs[i - n + 1 : i + 1]
    return sum(s) / n


def rsi(closes, i, n=14):
    if i < n:
        return None
    gains = losses = 0.0
    for k in range(i - n + 1, i + 1):
        ch = closes[k] - closes[k - 1]
        if ch >= 0:
            gains += ch
        else:
            losses -= ch
    if losses == 0:
        return 100.0
    rs = (gains / n) / (losses / n)
    return 100 - 100 / (1 + rs)


def positions(candles, strat, p):
    """Return list of target positions (-1/0/1) per bar."""
    closes = [c[3] for c in candles]
    highs = [c[1] for c in candles]
    lows = [c[2] for c in candles]
    n = len(candles)
    pos = [0] * n
    cur = 0
    for i in range(n):
        if strat == "ma":
            s, l = sma(closes, i, p[0]), sma(closes, i, p[1])
            if s is not None and l is not None:
                cur = 1 if s > l else -1
        elif strat == "tsmom":
            L = p[0]
            if i >= L:
                cur = 1 if closes[i] > closes[i - L] else -1
        elif strat == "donchian":
            N = p[0]
            if i >= N:
                hi = max(highs[i - N : i])
                lo = min(lows[i - N : i])
                if closes[i] > hi:
                    cur = 1
                elif closes[i] < lo:
                    cur = -1
                # else keep cur (breakout persistence)
        elif strat == "rsi":
            lo, hi = p[0], p[1]
            r = rsi(closes, i)
            if r is not None:
                if r < lo:
                    cur = 1
                elif r > hi:
                    cur = -1
                elif 45 < r < 55:
                    cur = 0
        elif strat == "boll":
            N, k = p[0], p[1]
            m = sma(closes, i, N)
            if m is not None:
                seg = closes[i - N + 1 : i + 1]
                sd = (sum((x - m) ** 2 for x in seg) / N) ** 0.5
                if sd > 0:
                    if closes[i] < m - k * sd:
                        cur = 1
                    elif closes[i] > m + k * sd:
                        cur = -1
                    elif abs(closes[i] - m) < 0.2 * sd:
                        cur = 0
        pos[i] = cur
    return pos


def evaluate(candles, pos, bpy):
    closes = [c[3] for c in candles]
    rets = []
    changes = 0
    for i in range(1, len(candles)):
        r = pos[i - 1] * (closes[i] / closes[i - 1] - 1)
        if pos[i] != pos[i - 1]:
            r -= COST * abs(pos[i] - pos[i - 1])
            changes += 1
        rets.append(r)
    if not rets:
        return None
    mean = sum(rets) / len(rets)
    var = sum((x - mean) ** 2 for x in rets) / len(rets)
    sd = var ** 0.5
    sharpe = (mean / sd * math.sqrt(bpy)) if sd > 0 else 0.0
    total = 1.0
    eq = []
    for r in rets:
        total *= 1 + r
        eq.append(total)
    peak = -1e9
    mdd = 0.0
    for v in eq:
        peak = max(peak, v)
        mdd = min(mdd, v / peak - 1)
    in_mkt = sum(1 for x in pos if x != 0) / len(pos)
    return {"sharpe": sharpe, "ret_pct": (total - 1) * 100, "mdd_pct": mdd * 100,
            "trades": changes, "in_mkt": in_mkt * 100}


GRIDS = {
    "ma": [(s, l) for s in (10, 20, 50) for l in (50, 100, 200) if s < l],
    "tsmom": [(L,) for L in (10, 20, 40, 80)],
    "donchian": [(N,) for N in (20, 40, 80)],
    "rsi": [(30, 70), (25, 75), (20, 80)],
    "boll": [(20, 2.0), (40, 2.0), (20, 2.5)],
}


def walk(candles, strat, bpy):
    split = int(len(candles) * 0.6)
    tr, te = candles[:split], candles[split:]
    best, best_s = None, -1e9
    for p in GRIDS[strat]:
        m = evaluate(tr, positions(tr, strat, p), bpy)
        if m and m["sharpe"] > best_s:
            best_s, best = m["sharpe"], p
    if best is None:
        return None
    oos = evaluate(te, positions(te, strat, best), bpy)
    ins = evaluate(tr, positions(tr, strat, best), bpy)
    return best, ins, oos


for tf, rng in [("1h", "730d"), ("1d", "max")]:
    bpy = BARS_PER_YEAR.get(tf, 252)
    try:
        candles = fetch(tf, rng)
    except Exception as e:
        print(f"{tf}: fetch error {e}")
        continue
    print(f"\n===== {tf}/{rng} : {len(candles)} bars (60% train / 40% OOS), cost={COST*1e4:.0f}bps/side =====")
    print(f"{'strategy':<10}{'best param':<14}{'IS Sharpe':>10}{'OOS Sharpe':>11}{'OOS ret%':>10}{'OOS DD%':>9}{'trades':>8}")
    for strat in GRIDS:
        r = walk(candles, strat, bpy)
        if not r:
            continue
        best, ins, oos = r
        print(f"{strat:<10}{str(best):<14}{ins['sharpe']:>10.2f}{oos['sharpe']:>11.2f}{oos['ret_pct']:>10.1f}{oos['mdd_pct']:>9.1f}{oos['trades']:>8}")
