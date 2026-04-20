# Equity Research Platform — CLAUDE.md

Project context for Claude Code. Read this before making any changes.

## What this app is

A professional-grade stock & ETF analysis web app built with Streamlit.
Styled to match a JPMC/Goldman Sachs investment research aesthetic.
Targets two audiences simultaneously: investment analysts (metrics) and retail investors (plain-English interpretations).

## How to run

```bash
cd /Users/s.g.jayaraman/Documents/Invest_Analyze
/Users/s.g.jayaraman/Library/Python/3.9/bin/streamlit run app.py
```

Or after adding `~/Library/Python/3.9/bin` to PATH (already done in `~/.zshrc`):

```bash
streamlit run app.py
```

App runs on **http://localhost:8501**

## Python version

**Python 3.9** (macOS system Python via CommandLineTools).
- Always include `from __future__ import annotations` at the top of any file that uses union type hints (`X | Y`).
- Do NOT use `X | None` syntax without that import — it will raise a TypeError at runtime.

## File structure

| File | Purpose |
|------|---------|
| `app.py` | Main Streamlit UI — all three modes, CSS, charts, sidebar |
| `stock_analyzer.py` | yfinance data layer — fetches and computes all stock metrics |
| `interpretations.py` | Plain-English interpretation functions — one per metric, returns `(rating, text)` |
| `portfolio_builder.py` | ETF portfolio optimisation engine — MVO via SciPy SLSQP |
| `requirements.txt` | Python dependencies |

## Three app modes (sidebar radio)

### 1. Deep Dive — Single Stock
- Enter one US ticker
- Shows: valuation, profitability, financial health, growth, dividends, technicals, analyst view, company info
- Each metric has a rating (`strong`/`good`/`fair`/`caution`/`weak`/`neutral`) + plain-English interpretation

### 2. Compare Stocks
- Enter 2–3 tickers
- Shows: side-by-side comparison table, rebased price chart, category scorecard, analyst verdict

### 3. Portfolio Builder (ETFs)
- Enter up to 10 ETF tickers
- User selects: risk profile (Conservative / Moderate / Aggressive) + horizon (Quarterly / Half-Yearly / Annual)
- Runs Mean-Variance Optimisation (SciPy SLSQP) with expense-ratio-adjusted net returns
- Output: % allocation totalling 100%, efficient frontier chart, per-ETF rationale

## Key architecture decisions

### interpretations.py
- Every function takes a raw metric value, returns `(rating: str, interpretation: str)`
- Rating is one of: `strong`, `good`, `fair`, `caution`, `weak`, `neutral`
- No Claude/LLM calls — all rule-based

### stock_analyzer.py
- `StockAnalyzer` class wraps yfinance
- Properties `info` and `history` are lazily fetched and cached
- `_g(key, default)` is the safe getter that handles None and NaN

### portfolio_builder.py
- `ETFPortfolioOptimizer(tickers, risk_profile, time_horizon)`
- `load()` → fetches data, returns list of valid tickers
- `compute_metrics()` → returns `dict[ticker -> metrics_dict]`
- `optimize(metrics)` → returns `(weights_dict, portfolio_metrics_dict)`
- **Expense ratio scaling**: yfinance `netExpenseRatio` is in "percent-as-decimal" format (e.g. `0.0945` = 0.0945%). Divide by 100 before using in calculations.
- `SCIPY_AVAILABLE` flag — falls back to heuristic weighting if scipy not installed

### app.py CSS
- Dark navy sidebar: `#00194e`
- Primary brand blue: `#003087`
- Gold accent: `#c9a240`
- All custom components use HTML via `st.markdown(..., unsafe_allow_html=True)`
- Monospaced numbers use `font-family:'SF Mono','Fira Code',monospace`

## Data source

**Yahoo Finance via yfinance** — free, no API key required.
- Rate limited under heavy traffic
- May be delayed ~15 min for some fields
- `netExpenseRatio` for ETFs is returned as percentage-decimal (divide by 100)

## No AI/LLM calls at runtime

This app does **not** call Claude API or any LLM at runtime.
All interpretations are rule-based Python. No tokens consumed by users.

## Deployment

Can be deployed free on **Streamlit Community Cloud** (share.streamlit.io).
Requires a public GitHub repo with `app.py` and `requirements.txt`.

## Known gotchas

- Backslash inside f-string expressions not allowed in Python 3.9 — use string concatenation instead
- D/E ratio from yfinance may be in percentage form (>10 means divide by 100 to get the ratio)
- Some ETFs have missing fields (expense ratio, beta) — always use `_safe()` / `_g()` helpers
- yfinance `history()` returns empty DataFrame for invalid tickers — check `len(hist) < 30` before processing
