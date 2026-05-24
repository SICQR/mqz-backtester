# MESS QUANT ZERO — Strategy Research Findings

**Question:** Is there a systematic edge that lets MQZ make money trading gold?
**Method:** Backtest + walk-forward (in-sample/out-of-sample) + deep multi-regime
analysis on 16 years of daily gold (GLD, 2010–2026, 4,025 bars), textbook params
(no curve-fitting), net of ~2bps/side costs. Tools: `scripts/backtest.py`,
`scripts/sweep.py`, `scripts/walkforward.py`, `scripts/deep_analysis.py`.

## Finding 1 — The default fast crossover loses
SMA(5/20)+ATR on 1m–1h gold: negative expectancy everywhere, profit factor < 1.
No edge.

## Finding 2 — Mean-reversion is dead (on gold)
RSI and Bollinger reversion: negative in-sample AND out-of-sample. Drop it.

## Finding 3 — Trend looked promising on one split… but doesn't hold up
A single 60/40 walk-forward on 1h gold showed positive OOS trend Sharpe (0.4–0.9).
BUT that window was a gold bull run, and the deep multi-regime test killed the hope.

## Finding 4 (the big one) — Nothing beats buy-and-hold gold
16 years, every regime, textbook params:

| Strategy            | CAGR % | Sharpe | MaxDD % |
|---------------------|-------:|-------:|--------:|
| **Buy & hold gold** | **8.2**| **0.56**| -45.6  |
| SMA200 long-only    | 5.4    | 0.46   | -34.2   |
| 50/200 cross long   | 5.6    | 0.48   | -35.3   |
| 50/200 cross L/S    | 3.2    | 0.28   | -44.7   |
| 12m momentum long   | 4.5    | 0.40   | -36.7   |
| 12m momentum L/S    | 1.6    | 0.18   | -57.8   |
| Donchian-50 L/S     | 3.0    | 0.27   | -53.7   |

Every timing rule underperformed holding gold on return **and** Sharpe. Shorting
hurt. Trend only reduced drawdown (sitting out ~40% of the time) — at a worse
risk-adjusted return, and it whipsawed in choppy years.

## Conclusion
**There is no tradeable single-asset edge here.** This matches the literature:
trend-following needs *diversification across many uncorrelated markets* (CTA /
managed-futures) to work — it does not reliably beat holding a single asset like gold.

## Honest implications
- Don't trade gold expecting to beat owning gold. To own gold, just own it (no bot needed).
- A real systematic edge would require a **diversified multi-asset trend** portfolio
  (commodities + FX + rates + indices) — a much larger build, modest expected Sharpe
  (~0.5–0.8), uncertain, and a tough recent decade for the style.
- MQZ's value is proven **infrastructure**, not alpha. Treat it as: a portfolio/credibility
  piece, a sellable template, or the chassis for a future multi-asset research effort.

*Not financial advice. Paper research only.*
