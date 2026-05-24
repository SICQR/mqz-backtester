#!/usr/bin/env python3
"""
Deep, multi-regime analysis of trend vs gold.
Data: GLD (SPDR Gold ETF, ~20y daily, every regime: 2008 crisis, 2011 peak,
2013-15 bear, 2020 spike, 2022 selloff, 2024-25 bull). Uses TEXTBOOK parameters
(no optimisation = no curve-fitting). Benchmarks every strategy against simply
holding gold, and breaks results down by calendar year. Costs charged on turnover.
NOTE: long/short ignores CFD overnight financing (a real live cost) — gross figures.
"""
import json, math, time, urllib.request, datetime

UA = {"User-Agent": "Mozilla/5.0"}
COST = 0.0002


def fetch(symbol, years=16):
    p2 = int(time.time()); p1 = p2 - int(years * 365.25 * 86400)
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
           f"?period1={p1}&period2={p2}&interval=1d")
    d = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read())
    r = d["chart"]["result"][0]
    ts = r["timestamp"]
    q = r["indicators"]["quote"][0]
    c, h, l = q["close"], q["high"], q["low"]
    out = []
    for i in range(len(ts)):
        if None not in (c[i], h[i], l[i]):
            out.append((ts[i], h[i], l[i], c[i]))
    return out


def sma(xs, i, n):
    return sum(xs[i - n + 1 : i + 1]) / n if i + 1 >= n else None


def positions(candles, strat):
    closes = [x[3] for x in candles]
    highs = [x[1] for x in candles]
    lows = [x[2] for x in candles]
    n = len(candles)
    pos = [0] * n
    cur = 0
    for i in range(n):
        if strat == "buyhold":
            cur = 1
        elif strat == "sma200_long":               # long only when above 200d
            m = sma(closes, i, 200)
            cur = 1 if (m and closes[i] > m) else 0
        elif strat == "ma_50_200_ls":               # golden/death cross long/short
            a, b = sma(closes, i, 50), sma(closes, i, 200)
            if a and b:
                cur = 1 if a > b else -1
        elif strat == "ma_50_200_long":             # golden cross long/flat
            a, b = sma(closes, i, 50), sma(closes, i, 200)
            if a and b:
                cur = 1 if a > b else 0
        elif strat == "tsmom_252_ls":               # 12m time-series momentum L/S
            if i >= 252:
                cur = 1 if closes[i] > closes[i - 252] else -1
        elif strat == "tsmom_252_long":
            if i >= 252:
                cur = 1 if closes[i] > closes[i - 252] else 0
        elif strat == "donchian_50_ls":
            if i >= 50:
                hi, lo = max(highs[i - 50 : i]), min(lows[i - 50 : i])
                if closes[i] > hi:
                    cur = 1
                elif closes[i] < lo:
                    cur = -1
        pos[i] = cur
    return pos


def metrics(candles, pos, bpy=252):
    closes = [x[3] for x in candles]
    rets = []
    for i in range(1, len(candles)):
        r = pos[i - 1] * (closes[i] / closes[i - 1] - 1)
        if pos[i] != pos[i - 1]:
            r -= COST * abs(pos[i] - pos[i - 1])
        rets.append(r)
    if not rets:
        return None
    eq = 1.0
    curve = []
    for r in rets:
        eq *= 1 + r
        curve.append(eq)
    yrs = len(rets) / bpy
    cagr = (eq ** (1 / yrs) - 1) * 100 if yrs > 0 and eq > 0 else -100
    mean = sum(rets) / len(rets)
    sd = (sum((x - mean) ** 2 for x in rets) / len(rets)) ** 0.5
    sharpe = mean / sd * math.sqrt(bpy) if sd > 0 else 0
    peak, mdd = -1e9, 0
    for v in curve:
        peak = max(peak, v)
        mdd = min(mdd, v / peak - 1)
    inmkt = sum(1 for x in pos if x != 0) / len(pos) * 100
    return {"cagr": cagr, "sharpe": sharpe, "mdd": mdd * 100, "inmkt": inmkt,
            "final": eq, "curve": curve}


def by_year(candles, pos):
    years = {}
    closes = [x[3] for x in candles]
    for i in range(1, len(candles)):
        y = datetime.datetime.fromtimestamp(candles[i][0], datetime.timezone.utc).year
        r = pos[i - 1] * (closes[i] / closes[i - 1] - 1)
        if pos[i] != pos[i - 1]:
            r -= COST * abs(pos[i] - pos[i - 1])
        years.setdefault(y, 1.0)
        years[y] *= 1 + r
    return {y: (v - 1) * 100 for y, v in years.items()}


candles = fetch("GLD", years=16)
y0 = datetime.datetime.fromtimestamp(candles[0][0], datetime.timezone.utc).year
y1 = datetime.datetime.fromtimestamp(candles[-1][0], datetime.timezone.utc).year
print(f"GLD daily: {len(candles)} bars, {y0}–{y1}, cost={COST*1e4:.0f}bps/side\n")
strats = ["buyhold", "sma200_long", "ma_50_200_long", "ma_50_200_ls",
          "tsmom_252_long", "tsmom_252_ls", "donchian_50_ls"]
print(f"{'strategy':<17}{'CAGR%':>8}{'Sharpe':>8}{'MaxDD%':>9}{'%inMkt':>8}")
results = {}
for s in strats:
    m = metrics(candles, positions(candles, s))
    results[s] = m
    print(f"{s:<17}{m['cagr']:>8.1f}{m['sharpe']:>8.2f}{m['mdd']:>9.1f}{m['inmkt']:>8.0f}")

print("\nPer-year return %  (BH = buy&hold gold, TF = tsmom_252_long, FILT = sma200_long)")
bh = by_year(candles, positions(candles, "buyhold"))
tf = by_year(candles, positions(candles, "tsmom_252_long"))
fl = by_year(candles, positions(candles, "sma200_long"))
print(f"{'year':<6}{'BH':>8}{'TF':>8}{'FILT':>8}")
for y in sorted(bh):
    print(f"{y:<6}{bh[y]:>8.1f}{tf.get(y,0):>8.1f}{fl.get(y,0):>8.1f}")

# down-year value-add: how trend did in years gold fell
downs = [y for y in bh if bh[y] < 0]
if downs:
    bh_d = sum(bh[y] for y in downs) / len(downs)
    tf_d = sum(tf.get(y, 0) for y in downs) / len(downs)
    fl_d = sum(fl.get(y, 0) for y in downs) / len(downs)
    print(f"\nGold DOWN years ({len(downs)}): avg BH {bh_d:+.1f}%  vs TF {tf_d:+.1f}%  vs FILT {fl_d:+.1f}%")
