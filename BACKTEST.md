# MESS QUANT ZERO — Default strategy backtest (the honest part)

We refuse to sell a fantasy. Here are the **real** results of the included default
strategy (SMA 5/20 crossover + ATR stops, 2bps/side cost) on historical gold (GC=F),
measured in **R-multiples** (1R = risk per trade). Run it yourself: `python3 scripts/backtest.py`.

| Timeframe | Trades | Win % | Expectancy | Profit factor |
|-----------|-------:|------:|-----------:|--------------:|
| 1m / 7d   | 221    | 38.0  | -0.377R    | 0.54 |
| 5m / 60d  | 647    | 39.7  | -0.151R    | 0.78 |
| 15m / 60d | 232    | 40.1  | -0.077R    | 0.88 |
| 1h / 730d | 689    | 39.3  | -0.079R    | 0.88 |

**Verdict:** the default crossover has **no edge** on gold — profit factor < 1 everywhere
with a meaningful sample. A variant sweep (`scripts/sweep.py`) found nothing that held up
across timeframes (the one positive line failed to replicate = overfit).

**Why ship this?** Because it's the truth, and because it proves the point: MQZ is the
**machine**, not the alpha. The hard, production-grade infrastructure is done — feed,
risk controls, execution, journaling, alerts, dashboard, persistence, backtester. Plug
in a real edge and it runs 24/7 with discipline. Finding that edge is your job (and it's hard).
