#!/usr/bin/env python3
"""
MQZ strategy backtest
=====================
Replicates the live signal + risk logic over historical GC=F (gold) candles and
simulates intrabar stop/target exits with a realistic round-trip cost. Reports
per-timeframe win rate, expectancy (in R), profit factor, and max drawdown.
Results are in R-multiples (1R = the risk per trade), so they are independent of
position sizing and timeframe. Costs are modelled as a spread fraction per side.
"""
import json
import urllib.request

UA = {"User-Agent": "Mozilla/5.0"}

# strategy params (mirror the live engine defaults)
SHORT, LONG, MINC, THRESH, ATRW = 5, 20, 20, 0.0008, 14
SL_MULT, TP_MULT, MIN_CONF, MAX_VOL, CONF_SCALE = 2.0, 3.0, 0.48, 0.05, 60.0
SPREAD_PCT = 0.0002  # cost per side (round trip = 2x); ~2bps


def fetch(interval, rng):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/GC=F?interval={interval}&range={rng}"
    req = urllib.request.Request(url, headers=UA)
    d = json.loads(urllib.request.urlopen(req, timeout=25).read())
    r = d["chart"]["result"][0]
    ts = r["timestamp"]
    q = r["indicators"]["quote"][0]
    out = []
    for i in range(len(ts)):
        o, h, l, c = q["open"][i], q["high"][i], q["low"][i], q["close"][i]
        if None in (o, h, l, c):
            continue
        out.append((o, h, l, c))
    return out


def sma(xs, n):
    seg = xs[-n:]
    return sum(seg) / len(seg) if seg else 0.0


def atr(window, n):
    trs = []
    pc = None
    for o, h, l, cl in window:
        tr = (h - l) if pc is None else max(h - l, abs(h - pc), abs(l - pc))
        trs.append(tr)
        pc = cl
    seg = trs[-n:]
    return sum(seg) / len(seg) if seg else 0.0


def signal(window):
    closes = [c[3] for c in window]
    if len(closes) < MINC:
        return None
    s, lg = sma(closes, SHORT), sma(closes, LONG)
    diff = (s - lg) / lg if lg else 0.0
    price = closes[-1]
    a = atr(window, ATRW)
    vol = a / price if price else 0.0
    last = closes[-1]
    if diff > THRESH and last >= s:
        trend = "UP"
    elif diff < -THRESH and last <= s:
        trend = "DOWN"
    else:
        return None
    conf = min(0.5 + abs(diff) * CONF_SCALE, 0.95)
    if conf < MIN_CONF:
        return None
    if vol <= 0 or vol > MAX_VOL:
        return None
    return trend, price, vol


def backtest(candles):
    pos = None
    trades = []
    for i in range(len(candles)):
        o, h, l, c = candles[i]
        if pos:
            side, entry, sl, tp = pos
            exitp = None
            if side == "UP":
                if l <= sl:
                    exitp = sl
                elif h >= tp:
                    exitp = tp
            else:
                if h >= sl:
                    exitp = sl
                elif l <= tp:
                    exitp = tp
            if exitp is not None:
                risk = abs(entry - sl)
                raw = (exitp - entry) if side == "UP" else (entry - exitp)
                cost = 2 * SPREAD_PCT * entry
                trades.append((raw - cost) / risk if risk else 0.0)
                pos = None
        if not pos and i >= MINC:
            sg = signal(candles[: i + 1])
            if sg:
                trend, price, vol = sg
                if trend == "UP":
                    sl, tp = price - SL_MULT * vol * price, price + TP_MULT * vol * price
                else:
                    sl, tp = price + SL_MULT * vol * price, price - TP_MULT * vol * price
                pos = (trend, price, sl, tp)
    return trades


def report(name, trades):
    n = len(trades)
    if not n:
        print(f"{name}: no trades")
        return
    wins = [t for t in trades if t > 0]
    losses = [t for t in trades if t <= 0]
    total = sum(trades)
    wr = len(wins) / n * 100
    gp, gl = sum(wins), -sum(losses)
    pf = gp / gl if gl else float("inf")
    cum = peak = mdd = 0.0
    for t in trades:
        cum += t
        peak = max(peak, cum)
        mdd = min(mdd, cum - peak)
    aw = (sum(wins) / len(wins)) if wins else 0.0
    al = (sum(losses) / len(losses)) if losses else 0.0
    print(
        f"{name}: trades={n} win%={wr:.1f} totalR={total:+.1f} "
        f"exp/trade={total/n:+.3f}R PF={pf:.2f} maxDD={mdd:.1f}R "
        f"avgW={aw:+.2f}R avgL={al:+.2f}R"
    )


print("MQZ backtest — GC=F gold, R-multiples, cost=%.0fbps/side\n" % (SPREAD_PCT * 10000))
for interval, rng in [("1m", "7d"), ("5m", "60d"), ("15m", "60d"), ("1h", "730d"), ("1d", "max")]:
    try:
        c = fetch(interval, rng)
        report(f"{interval:>3}/{rng:<4} ({len(c):>4} bars)", backtest(c))
    except Exception as e:
        print(f"{interval}/{rng}: error {e}")
