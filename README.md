# Equity Research Platform

A professional-grade stock, ETF, and tax analysis web app styled after JPMC / Goldman Sachs investment research tooling. Built with Streamlit, powered by Yahoo Finance data — no API keys, no subscriptions, no runtime AI costs.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-red) ![License](https://img.shields.io/badge/License-MIT-green)

**Live app:** https://invest-analyze-srinijayaraman63.streamlit.app/

---

## What it does

The app has **four analysis modes**, selectable from the sidebar:

| Mode | Description |
|------|-------------|
| **Deep Dive** | Full analyst-grade breakdown of a single US stock |
| **Compare Stocks** | Side-by-side comparison of 2–3 tickers |
| **Portfolio Builder** | Risk-return optimised ETF allocation recommendations |
| **Tax Optimizer** | W-2 based federal tax-saving recommendation engine |

Every metric is shown with both the raw number (for analysts) and a plain-English interpretation (for retail investors).

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

The default ETF set includes **SGOV** (iShares 0-3 Month Treasury Bond ETF) as a cash/capital-preservation option, especially suited for Conservative allocations.

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
   - **Cash/stable ETFs** (SGOV, BIL, SHV, TBIL, USFR, JPST, MINT, etc.) receive a higher per-ETF weight cap of 40% in Conservative mode
4. **Efficient Frontier** is simulated with 4,000 random portfolios via Monte Carlo
5. Per-ETF **analyst-style rationale** is generated explaining why each ETF received its allocation

**Optimisation objectives by risk profile**

| Profile | Objective | Max weight/ETF | Vol cap (Q / H / A) |
|---------|-----------|---------------|---------------------|
| Conservative 🛡️ | Minimise portfolio volatility | 25% (40% for cash ETFs) | 7% / 9% / 11% |
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

### Mode 4 — Tax Optimizer

A W-2 based federal tax-saving recommendation engine using **IRS 2025 data** (Rev. Proc. 2024-40). Designed for high-income households that are under-utilising available tax-advantaged vehicles.

**Inputs (W-2 and financial profile)**

| Section | Fields |
|---------|--------|
| A — Income | W-2 Box 1 wages, spouse wages, other income, withholding, filing status, ages |
| B — Retirement & HSA | 401k traditional/Roth contributions, IRA contributions, HSA contributions, dependents |
| C — Itemized Deductions | Mortgage interest, state/local taxes (SALT), charitable contributions, medical expenses |

The form is pre-filled with a realistic $350,000 household income example that is intentionally under-optimised — useful as a starting point for exploration.

**What the engine calculates**

- **Current tax position** — gross income, AGI, taxable income, federal tax, effective rate, marginal rate, refund or amount owed
- **FICA** — Social Security (up to $176,100 wage base), Medicare (1.45%), Additional Medicare (0.9% above $200k/$250k), NIIT (3.8% on net investment income above threshold)
- **Up to 10 ranked recommendations** across these strategies:

| Category | Example strategies |
|----------|--------------------|
| Retirement | Maximise 401k traditional, add catch-up (age 50+), SECURE 2.0 super catch-up (age 60–63: +$11,250) |
| IRA | Deductible Traditional IRA, Backdoor Roth IRA |
| HSA | Max-fund Health Savings Account (triple tax advantage) |
| Itemized Deductions | Mortgage interest, SALT (capped at $10k), charitable giving |
| Self-Employed | SEP-IRA, Solo 401k (if applicable) |

**Interactive recommendation table**

Each recommendation row includes:
- A checkbox to **select or deselect** individual strategies
- Priority ranking (1 = highest impact)
- Current vs. recommended contribution levels
- Additional deduction unlocked
- Projected federal tax saving
- FICA saving (where applicable)

Unchecking a row instantly updates the projected totals without resetting the form — selections are preserved across Streamlit reruns via `st.session_state`.

**Outputs**
- Waterfall comparison table: Current AGI → Taxable Income → Federal Tax vs. projected values with selected strategies applied
- Total projected federal tax saving and FICA saving
- Marginal and effective rate impact

---

## Security

The publicly deployed app includes the following protections:

- **Session rate limiting** — each browser session is limited to 20 stock/ETF analyses, with a 3-second cooldown between requests
- **Ticker sanitization** — all ticker inputs are validated against `^[A-Z0-9.\-\^]{1,12}$` before any data fetch
- **Yahoo Finance caching** — `@st.cache_data(ttl=600)` on the data-fetch layer prevents redundant calls and reduces exposure to rate-limit errors from Yahoo Finance's shared-IP throttling on Community Cloud
- **Friendly rate-limit errors** — when Yahoo Finance returns a 429, the app shows a readable message instead of a raw exception

---

## File Structure

```
invest-analyze/
├── app.py                # Streamlit UI — all four modes, CSS, charts, sidebar, security
├── stock_analyzer.py     # yfinance data layer — fetches and computes all stock metrics
├── interpretations.py    # Rule-based interpretation functions — one per metric, returns (rating, text)
├── portfolio_builder.py  # ETF portfolio optimisation engine — MVO via SciPy SLSQP
├── tax_optimizer.py      # Federal tax engine — IRS 2025 brackets, recommendations, projected savings
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
- `CASH_STABLE_ETFS` — set of known capital-preservation tickers (SGOV, BIL, SHV, TBIL, USFR, etc.) that receive special rationale language and higher weight caps in Conservative mode
- Falls back to score-based heuristic weighting if SciPy is not installed

**`tax_optimizer.py`**
- IRS 2025 constants: `TAX_BRACKETS`, `STANDARD_DEDUCTIONS`, `LIMITS`, `IRA_DEDUCT_PHASEOUT`, `ROTH_PHASEOUT`, NIIT thresholds, FICA rates, `SALT_CAP`
- `compute_federal_tax(taxable_income, filing_status)` — progressive bracket math
- `marginal_rate(taxable_income, filing_status)` — top bracket rate
- `TaxOptimizer` class — accepts 25+ W-2 and financial parameters
- `generate_recommendations()` — returns up to 10 ranked strategy dicts with deduction, federal saving, FICA saving, and priority
- `projected_tax(selected_ids)` — recalculates tax with a subset of strategies applied
- `current_summary()` — returns current AGI, taxable income, federal tax, effective/marginal rates, refund/owe

---

## Data Source

All market data is fetched from **Yahoo Finance** via the `yfinance` library.

- Free, no API key required
- Data may be delayed ~15 minutes for some fields
- Rate-limited under very heavy traffic — the app caches responses for 10 minutes to reduce repeat calls
- Not suitable for high-frequency or latency-sensitive applications

Tax data is sourced from **IRS Rev. Proc. 2024-40** (2025 tax year parameters) — hardcoded constants, no external API required.

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

**Live:** https://invest-analyze-srinijayaraman63.streamlit.app/

To deploy your own fork:

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
- **Tax calculations** — Based on IRS 2025 parameters. State taxes are not modelled. Consult a CPA for filing decisions.

---

## Disclaimer

This application is for **informational and educational purposes only**. Nothing in this app constitutes financial, investment, tax, or legal advice. Always consult a qualified financial advisor or CPA before making investment or tax decisions. Past performance is not indicative of future results.

---

## License

MIT — see [LICENSE](LICENSE) for details.
