#!/usr/bin/env python3
"""Quick principled variant sweep on a fixed dataset (no refetch per variant).
Tests whether the crossover approach is salvageable with sensible tuning.
Honest caveat: this is in-sample; a good number here is necessary, not sufficient."""
import json
import urllib.request

UA = {"User-Agent": "Mozilla/5.0"}
SPREAD_PCT = 0.0002


def fetch(interval, rng):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/GC=F?interval={interval}&range={rng}"
    d = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read())
    r = d["chart"]["result"][0]
    ts, q = r["timestamp"], r["indicators"]["quote"][0]
    out = []
    for i in range(len(ts)):
        o, h, l, c = q["open"][i], q["high"][i], q["low"][i], q["close"][i]
        if None not in (o, h, l, c):
            out.append((o, h, l, c))
    return out


def sma(xs, n):
    seg = xs[-n:]
    return sum(seg) / len(seg) if seg else 0.0


def atr(w, n):
    trs, pc = [], None
    for o, h, l, cl in w:
        trs.append((h - l) if pc is None else max(h - l, abs(h - pc), abs(l - pc)))
        pc = cl
    seg = trs[-n:]
    return sum(seg) / len(seg) if seg else 0.0


def run(candles, short, lng, slm, tpm, mode, thresh=0.0008, atrw=14, maxvol=0.05):
    pos, trades = None, []
    closes_all = [c[3] for c in candles]
    for i in range(len(candles)):
        o, h, l, c = candles[i]
        if pos:
            side, entry, sl, tp = pos
            ex = None
            if side == "UP":
                ex = sl if l <= sl else (tp if h >= tp else None)
            else:
                ex = sl if h >= sl else (tp if l <= tp else None)
            if ex is not None:
                risk = abs(entry - sl)
                raw = (ex - entry) if side == "UP" else (entry - ex)
                trades.append((raw - 2 * SPREAD_PCT * entry) / risk if risk else 0.0)
                pos = None
        if not pos and i >= lng:
            cl = closes_all[: i + 1]
            s, lg = sma(cl, short), sma(cl, lng)
            diff = (s - lg) / lg if lg else 0.0
            price = cl[-1]
            vol = atr(candles[: i + 1], atrw) / price if price else 0.0
            if vol <= 0 or vol > maxvol:
                continue
            raw_trend = None
            if diff > thresh and cl[-1] >= s:
                raw_trend = "UP"
            elif diff < -thresh and cl[-1] <= s:
                raw_trend = "DOWN"
            if raw_trend:
                trend = raw_trend if mode == "trend" else ("DOWN" if raw_trend == "UP" else "UP")
                if trend == "UP":
                    sl, tp = price - slm * vol * price, price + tpm * vol * price
                else:
                    sl, tp = price + slm * vol * price, price - tpm * vol * price
                pos = (trend, price, sl, tp)
    return trades


def stat(trades):
    n = len(trades)
    if not n:
        return "no trades"
    wins = [t for t in trades if t > 0]
    gl = -sum(t for t in trades if t <= 0)
    pf = (sum(wins) / gl) if gl else 99.9
    return f"n={n:>4} win%={len(wins)/n*100:4.1f} totalR={sum(trades):+6.1f} exp={sum(trades)/n:+.3f}R PF={pf:.2f}"


for tf, rng in [("1h", "730d"), ("15m", "60d")]:
    print(f"\n=== {tf}/{rng} ===")
    candles = fetch(tf, rng)
    variants = [
        ("baseline 5/20 SL2 TP3 trend", 5, 20, 2, 3, "trend"),
        ("slow 10/40 SL2 TP3 trend", 10, 40, 2, 3, "trend"),
        ("let-run 5/20 SL2 TP5 trend", 5, 20, 2, 5, "trend"),
        ("tight-stop 5/20 SL1 TP3 trend", 5, 20, 1, 3, "trend"),
        ("fade 5/20 SL2 TP3 revert", 5, 20, 2, 3, "fade"),
        ("fade slow 10/40 SL2 TP2", 10, 40, 2, 2, "fade"),
    ]
    for name, s, lg, slm, tpm, mode in variants:
        print(f"  {name:<32} {stat(run(candles, s, lg, slm, tpm, mode))}")
