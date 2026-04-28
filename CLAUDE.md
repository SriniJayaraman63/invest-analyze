# Equity Research Platform — CLAUDE.md

Project context for Claude Code. Read this before making any changes.

## What this app is

A professional-grade stock, ETF, and tax analysis web app built with Streamlit.
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
Live deployment: **https://invest-analyze-srinijayaraman63.streamlit.app/**

## Python version

**Python 3.9** (macOS system Python via CommandLineTools).
- Always include `from __future__ import annotations` at the top of any file that uses union type hints (`X | Y`).
- Do NOT use `X | None` syntax without that import — it will raise a TypeError at runtime.

## File structure

| File | Purpose |
|------|---------|
| `app.py` | Main Streamlit UI — all four modes, CSS, charts, sidebar, security/rate-limiting |
| `stock_analyzer.py` | yfinance data layer — fetches and computes all stock metrics |
| `interpretations.py` | Plain-English interpretation functions — one per metric, returns `(rating, text)` |
| `portfolio_builder.py` | ETF portfolio optimisation engine — MVO via SciPy SLSQP, CASH_STABLE_ETFS |
| `tax_optimizer.py` | Federal tax engine — IRS 2025 brackets, recommendations, projected savings |
| `requirements.txt` | Python dependencies |

## Four app modes (sidebar radio)

### 1. Deep Dive — Single Stock
- Enter one US ticker
- Shows: valuation, profitability, financial health, growth, dividends, technicals, analyst view, company info
- Each metric has a rating (`strong`/`good`/`fair`/`caution`/`weak`/`neutral`) + plain-English interpretation

### 2. Compare Stocks
- Enter 2–3 tickers
- Shows: side-by-side comparison table, rebased price chart, category scorecard, analyst verdict

### 3. Portfolio Builder (ETFs)
- Enter up to 10 ETF tickers; default set includes SGOV for cash/capital-preservation
- User selects: risk profile (Conservative / Moderate / Aggressive) + horizon (Quarterly / Half-Yearly / Annual)
- Runs Mean-Variance Optimisation (SciPy SLSQP) with expense-ratio-adjusted net returns
- Cash/stable ETFs (SGOV, BIL, SHV, etc.) get a 40% per-ETF cap in Conservative mode instead of 25%
- Output: % allocation totalling 100%, efficient frontier chart, per-ETF rationale

### 4. Tax Optimizer
- W-2 based federal tax-saving recommendation engine using IRS 2025 data
- Three input sections: income/filing status, retirement/HSA contributions, itemized deductions
- Generates up to 10 ranked strategies; user toggles each via checkbox
- Selections persist across Streamlit reruns via `st.session_state["_tax_inputs"]`
- Shows waterfall comparison: current vs projected AGI, taxable income, federal tax, savings

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
- `CASH_STABLE_ETFS` set: SGOV, BIL, SHV, TBIL, USFR, JPST, MINT, ICSH, NEAR, FLOT, CLTL, GSY — get capital-preservation rationale language and higher weight cap in Conservative mode
- Conservative profile has `"max_w_cash": 0.40` key; optimizer bounds are per-ticker
- `SCIPY_AVAILABLE` flag — falls back to heuristic weighting if scipy not installed

### tax_optimizer.py
- IRS 2025 constants: `TAX_BRACKETS`, `STANDARD_DEDUCTIONS`, `LIMITS`, `IRA_DEDUCT_PHASEOUT`, `ROTH_PHASEOUT`, NIIT thresholds, FICA rates, `SALT_CAP = 10000`
- `compute_federal_tax(taxable_income, filing_status)` — progressive bracket math
- `marginal_rate(taxable_income, filing_status)` — top bracket rate
- `TaxOptimizer` class — 25+ `__init__` params covering all W-2 fields
- `generate_recommendations()` → list of dicts with keys: `id, category, strategy, detail, current, recommended, deduction, fed_saving, fica_saving, priority, note`
- `projected_tax(selected_ids: set)` → recalculates with selected strategies applied
- `current_summary()` → `gross_income, current_agi, federal_tax, effective_rate, marginal_rate, refund_or_owe`

### app.py — security & rate limiting
- `_MAX_PER_SESSION = 20`, `_COOLDOWN_SECS = 3`
- `_TICKER_RE = re.compile(r'^[A-Z0-9.\-\^]{1,12}$')` — all ticker inputs sanitized before fetch
- `_rate_limit_ok()` / `_record_request()` — enforce per-session limits stored in `st.session_state`
- `_fetch_all(ticker)` decorated with `@st.cache_data(ttl=600)` — caches yfinance responses for 10 min; covers both Deep Dive and Compare modes
- `_is_rate_limit(e)` — detects Yahoo Finance 429 and shows a friendly message

### app.py — Tax Optimizer session state pattern
- `st.form("tax_form")` + `st.form_submit_button` returns True for only ONE rerun
- Widget interactions (checkbox toggles) trigger reruns where `submitted=False`
- Fix: on submit, save all 25 inputs to `st.session_state["_tax_inputs"]`; check `"_tax_inputs" not in st.session_state` as the gate instead of `submitted`
- "Edit Inputs" button clears `st.session_state["_tax_inputs"]` to return to the form

### app.py CSS
- Dark navy sidebar: `#00194e`
- Primary brand blue: `#003087`
- Gold accent: `#c9a240`
- All custom components use HTML via `st.markdown(..., unsafe_allow_html=True)`
- Monospaced numbers use `font-family:'SF Mono','Fira Code',monospace`

## Data source

**Yahoo Finance via yfinance** — free, no API key required.
- Rate limited under heavy traffic; mitigated by `@st.cache_data(ttl=600)`
- May be delayed ~15 min for some fields
- `netExpenseRatio` for ETFs is returned as percentage-decimal (divide by 100)

**IRS Rev. Proc. 2024-40** — 2025 tax year parameters hardcoded in `tax_optimizer.py`. No external API.

## No AI/LLM calls at runtime

This app does **not** call Claude API or any LLM at runtime.
All interpretations and tax recommendations are rule-based Python. No tokens consumed by users.

## Deployment

Live on **Streamlit Community Cloud**: https://invest-analyze-srinijayaraman63.streamlit.app/  
GitHub: https://github.com/SriniJayaraman63/invest-analyze

## Known gotchas

- Backslash inside f-string expressions not allowed in Python 3.9 — use string concatenation instead
- D/E ratio from yfinance may be in percentage form (>10 means divide by 100 to get the ratio)
- Some ETFs have missing fields (expense ratio, beta) — always use `_safe()` / `_g()` helpers
- yfinance `history()` returns empty DataFrame for invalid tickers — check `len(hist) < 30` before processing
- `st.form_submit_button` returns True for only ONE rerun — do not use it as a gate for results that must survive checkbox interactions; use `st.session_state` instead
- `st.column_config.NumberColumn.format` uses C printf syntax — `%,.0f` with comma is invalid; pre-format dollar values as Python strings (`f"${v:,.0f}"`) and use `TextColumn` instead
- `st.caption()` renders as a non-wrapping inline element — for long text that must wrap, use `st.markdown()` with `word-wrap:break-word;overflow-wrap:anywhere` CSS
- Shared Streamlit Community Cloud IPs are frequently rate-limited by Yahoo Finance — always wrap yfinance calls in `@st.cache_data` to reduce repeat fetches
