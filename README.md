# Equity Research Platform

A professional-grade stock and ETF analysis web app styled after JPMC / Goldman Sachs investment research tooling. Built with Streamlit, powered by Yahoo Finance data — no API keys, no subscriptions, no runtime AI costs.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-red) ![License](https://img.shields.io/badge/License-MIT-green)

---

## What it does

The app has **three analysis modes**, selectable from the sidebar:

| Mode | Description |
|------|-------------|
| **Deep Dive** | Full analyst-grade breakdown of a single US stock |
| **Compare Stocks** | Side-by-side comparison of 2–3 tickers |
| **Portfolio Builder** | Risk-return optimised ETF allocation recommendations |

Every metric is shown with both the raw number (for analysts) and a plain-English interpretation (for retail investors).

---

## Screenshots

> Deep Dive · Compare Stocks · Portfolio Builder

*(Deploy to Streamlit Community Cloud and add screenshots here.)*

---

## Quick Start

### Prerequisites

- Python 3.9 or later
- pip

### Install

```bash
git clone https://github.com/SriniJayaraman63/invest-analyze.git
cd invest-analyze
pip install -r requirements.txt
```

### Run

```bash
streamlit run app.py
```

App opens at **http://localhost:8501**

---

## Features

### Mode 1 — Deep Dive (Single Stock)

Enter any US ticker symbol (e.g. `AAPL`, `MSFT`, `NVDA`) and get a full research report:

**Valuation**
| Metric | What it measures |
|--------|-----------------|
| P/E Ratio | Price relative to trailing earnings |
| Forward P/E | Price relative to next-12-month estimated earnings |
| PEG Ratio | P/E adjusted for earnings growth rate |
| P/B Ratio | Price relative to book (net asset) value |
| P/S Ratio | Price relative to revenue |
| EV/EBITDA | Enterprise value relative to operating cash flow proxy |

**Profitability**
| Metric | What it measures |
|--------|-----------------|
| Gross Margin | Revenue retained after cost of goods |
| Operating Margin | Profit from core business operations |
| Net Margin | Bottom-line profit percentage |
| Return on Equity (ROE) | Profit generated per dollar of shareholder equity |
| Return on Assets (ROA) | Efficiency of asset utilisation |

**Financial Health**
| Metric | What it measures |
|--------|-----------------|
| Debt/Equity Ratio | Financial leverage |
| Current Ratio | Short-term liquidity (assets vs liabilities) |

**Growth**
| Metric | What it measures |
|--------|-----------------|
| Revenue Growth (YoY) | Year-over-year top-line expansion |
| Earnings Growth (YoY) | Year-over-year EPS expansion |

**Dividends**
| Metric | What it measures |
|--------|-----------------|
| Dividend Yield | Annual income as % of stock price |
| Payout Ratio | % of earnings distributed as dividends |

**Technicals**
| Metric | What it measures |
|--------|-----------------|
| RSI (14-day) | Momentum — overbought/oversold signal |
| Beta | Sensitivity to broad market moves |
| 52-Week Range | Current price position within the annual range |

**Analyst View**
- Consensus rating (Strong Buy → Strong Sell)
- Price target vs current price
- Number of analyst opinions

**Company Info**
- Sector, industry, headquarters, employee count
- Business description

Each metric includes a traffic-light rating (`strong` / `good` / `fair` / `caution` / `weak` / `neutral`) and a plain-English sentence explaining what the number means for an investor.

---

### Mode 2 — Compare Stocks

Enter 2 or 3 ticker symbols to get:

- **Side-by-side comparison table** across all metrics, with the best value highlighted in green and the worst in red
- **Rebased price chart** — all tickers normalised to 100 at the start of the period so performance is directly comparable
- **Category scorecard** — win counts per category (Valuation, Profitability, Health, Growth, Dividends, Technicals)
- **Analyst verdict** — summary of which stock scores best overall and why

---

### Mode 3 — Portfolio Builder (ETFs)

Enter up to 10 ETF ticker symbols and configure:

**Inputs**
- **Risk Profile** — Conservative, Moderate, or Aggressive
- **Time Horizon** — Quarterly, Half-Yearly, or Annual

**What happens under the hood**

1. Price history is fetched from Yahoo Finance (lookback: 2y / 3y / 5y depending on horizon)
2. Per-ETF risk/return metrics are calculated:
   - **Annualised Return** — geometric compounding over the lookback period
   - **Annualised Volatility** — standard deviation of daily returns × √252
   - **Sharpe Ratio** — excess return per unit of total risk
   - **Sortino Ratio** — excess return per unit of downside risk only
   - **Max Drawdown** — worst peak-to-trough decline in the period
   - **Calmar Ratio** — return divided by max drawdown
   - **Treynor Ratio** — excess return per unit of market (beta) risk
   - **VaR 95%** — worst daily loss at 95% confidence
   - **Expense Ratio** — annual fund cost deducted from net return
3. **Mean-Variance Optimisation** (Modern Portfolio Theory) is run via SciPy SLSQP solver:
   - Objective function varies by risk profile (see table below)
   - Expense ratio is deducted from expected return before optimisation — high-cost ETFs are naturally penalised
   - Portfolio volatility is capped per horizon
4. **Efficient Frontier** is simulated with 4,000 random portfolios via Monte Carlo
5. Per-ETF **analyst-style rationale** is generated explaining why each ETF received its allocation

**Optimisation objectives by risk profile**

| Profile | Objective | Max weight/ETF | Vol cap (Q / H / A) |
|---------|-----------|---------------|---------------------|
| Conservative 🛡️ | Minimise portfolio volatility | 25% | 7% / 9% / 11% |
| Moderate ⚖️ | Maximise Sharpe ratio | 38% | 11% / 14% / 17% |
| Aggressive 🚀 | Maximise net expected return | 55% | 17% / 22% / 30% |

**Outputs**
- % allocation per ETF, summing to exactly 100%
- Portfolio-level Sharpe, Sortino, volatility, max drawdown, and net return metrics
- Donut chart of allocation
- Efficient frontier scatter chart (your portfolio highlighted)
- Allocation table with weight, Sharpe ratio, expense ratio, and max drawdown per ETF
- Per-ETF rationale cards in analyst report style

---

## File Structure

```
invest-analyze/
├── app.py                # Streamlit UI — all three modes, CSS, charts, sidebar
├── stock_analyzer.py     # yfinance data layer — fetches and computes all stock metrics
├── interpretations.py    # Rule-based interpretation functions — one per metric, returns (rating, text)
├── portfolio_builder.py  # ETF portfolio optimisation engine — MVO via SciPy SLSQP
├── requirements.txt      # Python dependencies
├── CLAUDE.md             # Project context for Claude Code AI assistant
└── .gitignore
```

### Module responsibilities

**`stock_analyzer.py`**
- `StockAnalyzer(ticker)` — main class
- `info` and `history` properties are lazy-loaded and cached on first access
- `_g(key, default)` — safe getter that handles `None` and `NaN` from yfinance
- Returns structured dicts from `get_valuation_metrics()`, `get_profitability_metrics()`, etc.

**`interpretations.py`**
- One function per metric, e.g. `pe_ratio(value)`, `rsi(value)`, `debt_to_equity(value)`
- Every function returns `(rating: str, interpretation: str)`
- Rating is one of: `strong`, `good`, `fair`, `caution`, `weak`, `neutral`
- No LLM calls — entirely rule-based thresholds

**`portfolio_builder.py`**
- `ETFPortfolioOptimizer(tickers, risk_profile, time_horizon)`
- `load()` — fetches data, returns list of valid tickers
- `compute_metrics()` — returns per-ETF metrics dict
- `optimize(metrics)` — runs MVO, returns `(weights_dict, portfolio_metrics_dict)`
- `generate_rationale(ticker, weight, metrics, port_metrics)` — analyst-style HTML explanation
- `simulate_frontier(n_sims=4000)` — Monte Carlo for efficient frontier chart
- Falls back to score-based heuristic weighting if SciPy is not installed

---

## Data Source

All data is fetched from **Yahoo Finance** via the `yfinance` library.

- Free, no API key required
- Data may be delayed ~15 minutes for some fields
- Rate-limited under very heavy traffic — if a ticker fails to load, try again in a few seconds
- Not suitable for high-frequency or latency-sensitive applications

---

## Design

The UI is styled to match a JPMC / Goldman Sachs investment research aesthetic:

| Element | Colour |
|---------|--------|
| Sidebar background | `#00194e` (dark navy) |
| Primary brand | `#003087` (JP Morgan blue) |
| Gold accent | `#c9a240` |
| Content background | `#f0f4f9` (light grey-blue) |
| Strong rating | `#0d7c4e` (green) |
| Caution rating | `#b45309` (amber) |
| Weak rating | `#b91c1c` (red) |

Numbers use `SF Mono` / `Fira Code` monospaced fonts for tabular readability.

---

## Deployment

### Streamlit Community Cloud (free)

1. Fork or push this repo to your GitHub account
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
3. Click **New app**
4. Select this repository, set the main file to `app.py`
5. Click **Deploy** — live in ~2 minutes

No server, no Docker, no cost.

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `streamlit >= 1.28` | Web app framework |
| `yfinance >= 0.2.31` | Yahoo Finance data |
| `plotly >= 5.17` | Interactive charts |
| `pandas >= 2.0` | Data manipulation |
| `numpy >= 1.24` | Numerical computation |
| `scipy >= 1.11` | SLSQP optimisation solver |

---

## Limitations

- **Data freshness** — Yahoo Finance data can be delayed or occasionally unavailable. Refresh if a metric shows `N/A`.
- **ETF coverage** — Some ETFs have incomplete metadata (expense ratio, beta). The app handles these gracefully with fallbacks.
- **Optimisation** — MVO assumes returns are normally distributed and that historical performance is indicative of future risk/return. It is a quantitative starting point, not financial advice.
- **No real-time streaming** — Prices are point-in-time snapshots, not live ticks.

---

## Disclaimer

This application is for **informational and educational purposes only**. Nothing in this app constitutes financial, investment, tax, or legal advice. Always consult a qualified financial advisor before making investment decisions. Past performance is not indicative of future results.

---

## License

MIT — see [LICENSE](LICENSE) for details.
