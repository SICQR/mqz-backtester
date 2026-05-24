# MQZ Backtester — an honest gold strategy backtester (zero dependencies)

A small, **dependency-free** Python backtester for gold strategies. No numpy, no pandas — just Python 3 and stdlib. It pulls real gold data, simulates intrabar stop/target exits with realistic costs, and reports win rate, expectancy (in R), profit factor, and max drawdown. There's also a parameter sweep, a walk-forward (in-sample/out-of-sample) tester, and a multi-regime analysis over 16 years.

This is the research half of [MESS QUANT ZERO](https://scanme2.gumroad.com/l/qlbax), open-sourced. I'm publishing it because it produced a result most "trading bot" sellers would hide.

## The honest result

I ran textbook strategies (no curve-fitting) over 16 years of daily gold, net of ~2bps/side costs. **Nothing beat buy-and-hold.**

| Strategy            | CAGR % | Sharpe | MaxDD % |
|---------------------|-------:|-------:|--------:|
| **Buy & hold gold** | **8.2**| **0.56**| -45.6  |
| SMA200 long-only    | 5.4    | 0.46   | -34.2   |
| 50/200 cross long   | 5.6    | 0.48   | -35.3   |
| 12m momentum long   | 4.5    | 0.40   | -36.7   |
| Donchian-50 L/S     | 3.0    | 0.27   | -53.7   |

Every timing rule underperformed simply holding gold, on return **and** Sharpe. This matches the literature: single-asset trend-following doesn't reliably beat holding the asset — trend needs diversification across many uncorrelated markets to work. Full write-up in [RESEARCH_FINDINGS.md](RESEARCH_FINDINGS.md).

## Quickstart

```bash
git clone https://github.com/SICQR/mqz-backtester.git
cd mqz-backtester
python3 scripts/backtest.py        # backtest the default fast crossover
python3 scripts/sweep.py           # parameter sweep
python3 scripts/walkforward.py     # in-sample / out-of-sample
python3 scripts/deep_analysis.py   # 16-year multi-regime test
```

No install step. No dependencies. Python 3.8+. Data is fetched live from a public endpoint at runtime. See [BACKTEST.md](BACKTEST.md) for details and flags.

## What this is — and isn't

This repo is the **backtester only**. The full **MESS QUANT ZERO** kit is the production trading *machine* that runs a strategy live: a 10-service Dockerised stack (live feed → signal → risk → execution → journal), a Next.js cockpit dashboard, Telegram ops bot (bring your own), Supabase persistence, and one-command deploy — paper-trading by default and LIVE-LOCKED.

- 🛒 **Full source kit (£69):** https://scanme2.gumroad.com/l/qlbax
- 📊 **Live cockpit demo:** https://dashboard-sage-three-98.vercel.app
- 🤗 **Hugging Face Space:** https://huggingface.co/spaces/HOTMESSLDN/mess-quant-zero

If this backtester is useful, a ⭐ helps.

## License

MIT — see [LICENSE](LICENSE). Educational software, provided as-is. **Not financial advice**, not a solicitation, and not a guarantee of profit. Trading carries risk of loss.
