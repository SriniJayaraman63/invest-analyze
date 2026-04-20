"""
portfolio_builder.py — ETF Portfolio Optimisation Engine

Pipeline:
  1. Fetch price history + fund metadata (yfinance)
  2. Compute per-ETF risk/return metrics (Sharpe, Sortino, Max Drawdown, Calmar, Treynor)
  3. Run Mean-Variance Optimisation with expense-ratio-adjusted net returns
  4. Generate analyst-style per-ETF rationale
  5. Monte-Carlo efficient frontier simulation for visualisation
"""

from __future__ import annotations
import math
import warnings
import numpy as np
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore")

try:
    from scipy.optimize import minimize as _sp_min
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

# ── Risk-free rate ─────────────────────────────────────────────────────────────
RISK_FREE_RATE = 0.043          # ~4.3 % (10-Year US Treasury, Apr 2026)

# ── Historical lookback per rebalancing horizon ────────────────────────────────
LOOKBACK = {
    "Quarterly":   "2y",        # 2-year history for quarterly rebalancers
    "Half-Yearly": "3y",
    "Annual":      "5y",
}

# ── Optimisation parameters per risk profile ───────────────────────────────────
# vol_cap: annualised portfolio volatility ceiling; varies by horizon (Q/H/A)
PROFILE_CFG = {
    "Conservative": {
        "max_w":      0.25,
        "max_w_cash": 0.40,            # higher cap for cash/stable-fund ETFs
        "min_w":      0.03,
        "obj":        "min_vol",       # minimise portfolio volatility
        "vol_cap": {"Quarterly": 0.07, "Half-Yearly": 0.09, "Annual": 0.11},
        "icon":    "🛡️",
        "color":   "#0d7c4e",
        "desc": (
            "Prioritises capital preservation and income. "
            "Minimises portfolio volatility — expense ratio and drawdown are primary constraints. "
            "Cash/stable ETFs (SGOV, BIL, SHV, JPST) may receive up to 40 % allocation. "
            "All other ETFs capped at 25 %. "
            "Quarterly horizon applies the tightest volatility cap (7 %)."
        ),
    },
    "Moderate": {
        "max_w":   0.38,
        "min_w":   0.02,
        "obj":     "max_sharpe",       # maximise Sharpe ratio
        "vol_cap": {"Quarterly": 0.11, "Half-Yearly": 0.14, "Annual": 0.17},
        "icon":    "⚖️",
        "color":   "#1a56db",
        "desc": (
            "Balances growth and risk. "
            "Maximises the Sharpe ratio — best net return per unit of volatility. "
            "Expense ratio is deducted from expected return before optimisation. "
            "Max 38 % per ETF."
        ),
    },
    "Aggressive": {
        "max_w":   0.55,
        "min_w":   0.00,
        "obj":     "max_return",       # maximise net expected return
        "vol_cap": {"Quarterly": 0.17, "Half-Yearly": 0.22, "Annual": 0.30},
        "icon":    "🚀",
        "color":   "#c41e3a",
        "desc": (
            "Maximises expected return net of fees. "
            "Accepts elevated volatility for long-run capital growth. "
            "Low-return or high-cost ETFs may receive zero or minimal allocation. "
            "Max 55 % per ETF."
        ),
    },
}

# ── Known cash / ultra-short / stable-fund ETFs ───────────────────────────────
# These receive capital-preservation-specific rationale language.
CASH_STABLE_ETFS = {
    "SGOV",  # iShares 0-3 Month Treasury Bond
    "BIL",   # SPDR Bloomberg 1-3 Month T-Bill
    "SHV",   # iShares Short Treasury Bond (1-12M)
    "TBIL",  # US Treasury 3 Month Bill
    "USFR",  # WisdomTree Floating Rate Treasury
    "JPST",  # JPMorgan Ultra-Short Income
    "MINT",  # PIMCO Enhanced Short Maturity
    "ICSH",  # iShares Ultra Short-Term Bond
    "NEAR",  # iShares Short Maturity Bond
    "FLOT",  # iShares Floating Rate Bond
    "CLTL",  # Invesco Treasury Collateral ETF
    "GSY",   # Invesco Ultra Short Duration
}

# ── Colour palette for allocation chart ───────────────────────────────────────
ALLOC_COLORS = [
    "#003087", "#0052cc", "#1a8fe3", "#38b6ff", "#c9a240",
    "#d4691e", "#7c3aed", "#059669", "#db2777", "#64748b",
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _safe(v):
    if v is None:
        return None
    try:
        if math.isnan(float(v)):
            return None
    except (TypeError, ValueError):
        pass
    return v


def _ann_return_from_hist(r: pd.Series) -> float:
    return float(r.mean() * 252)


def _ann_vol_from_hist(r: pd.Series) -> float:
    return float(r.std() * math.sqrt(252))


# ── Main class ────────────────────────────────────────────────────────────────

class ETFPortfolioOptimizer:
    """
    End-to-end ETF portfolio optimiser using Mean-Variance Optimisation (MVO).
    """

    def __init__(self, tickers: list, risk_profile: str, time_horizon: str):
        self.tickers      = [t.upper().strip() for t in tickers if t.strip()]
        self.risk_profile = risk_profile
        self.time_horizon = time_horizon
        self._raw: dict           = {}          # raw metadata per ticker
        self._returns: pd.DataFrame | None = None

    # ── 1. Data load ──────────────────────────────────────────────────────────

    def load(self, progress_cb=None) -> list:
        """
        Fetch price history + fund metadata for every ticker.
        Returns list of tickers that loaded successfully.
        """
        period = LOOKBACK[self.time_horizon]

        for idx, ticker in enumerate(list(self.tickers)):
            if progress_cb:
                progress_cb(ticker, idx, len(self.tickers))
            try:
                etf  = yf.Ticker(ticker)
                info = etf.info
                hist = etf.history(period=period)

                if hist.empty or len(hist) < 30:
                    continue

                # yfinance returns netExpenseRatio as already-a-percentage decimal
                # e.g. SPY = 0.0945 meaning 0.0945%, not 9.45%
                # Divide by 100 to get the true annual decimal for calculations
                raw_exp = (
                    _safe(info.get("annualReportExpenseRatio"))
                    or _safe(info.get("netExpenseRatio"))
                    or 0.0
                )
                exp_r = float(raw_exp) / 100.0 if raw_exp else 0.0

                self._raw[ticker] = {
                    "name":          info.get("longName") or info.get("shortName") or ticker,
                    "category":      info.get("category") or info.get("quoteType") or "—",
                    "fund_family":   info.get("fundFamily") or "—",
                    "expense_ratio": float(exp_r or 0.0),
                    "beta":          float(_safe(info.get("beta3Year")) or _safe(info.get("beta")) or 1.0),
                    "aum":           _safe(info.get("totalAssets")),
                    "div_yield":     float(_safe(info.get("yield")) or _safe(info.get("dividendYield")) or 0.0),
                    "3yr_return":    _safe(info.get("threeYearAverageReturn")),
                    "5yr_return":    _safe(info.get("fiveYearAverageReturn")),
                    "history":       hist,
                }
            except Exception:
                pass

        self.tickers = [t for t in self.tickers if t in self._raw]
        return self.tickers

    # ── 2. Per-ETF metrics ────────────────────────────────────────────────────

    def compute_metrics(self) -> dict:
        """
        Compute risk/return metrics from price history.
        Returns dict[ticker -> metrics_dict].
        """
        price_map = {t: self._raw[t]["history"]["Close"] for t in self.tickers}
        prices = pd.DataFrame(price_map).ffill().dropna(how="all")
        self._returns = prices.pct_change().dropna()

        rfr_daily = RISK_FREE_RATE / 252
        out = {}

        for t in self.tickers:
            if t not in self._returns.columns:
                continue
            r       = self._returns[t]
            ann_ret = _ann_return_from_hist(r)
            ann_vol = _ann_vol_from_hist(r)
            exp_r   = self._raw[t]["expense_ratio"]
            net_ret = ann_ret - exp_r               # fee-adjusted expected return

            # Sharpe (net of fees)
            sharpe = (net_ret - RISK_FREE_RATE) / ann_vol if ann_vol > 0 else 0.0

            # Sortino — downside deviation only
            neg_r    = r[r < rfr_daily]
            down_dev = float(neg_r.std() * math.sqrt(252)) if len(neg_r) > 5 else ann_vol
            sortino  = (net_ret - RISK_FREE_RATE) / down_dev if down_dev > 0 else 0.0

            # Max Drawdown
            cum      = (1 + r).cumprod()
            roll_max = cum.cummax()
            dd_ser   = (cum - roll_max) / roll_max
            max_dd   = float(dd_ser.min())

            # Calmar ratio
            calmar = net_ret / abs(max_dd) if max_dd < -0.001 else 0.0

            # Treynor ratio
            beta_v  = self._raw[t]["beta"]
            treynor = (net_ret - RISK_FREE_RATE) / beta_v if beta_v and beta_v != 0 else 0.0

            # Value-at-Risk (95 %, parametric)
            var_95 = float(ann_ret - 1.645 * ann_vol)

            out[t] = {
                "name":          self._raw[t]["name"],
                "category":      self._raw[t]["category"],
                "fund_family":   self._raw[t]["fund_family"],
                "expense_ratio": exp_r,
                "aum":           self._raw[t]["aum"],
                "div_yield":     self._raw[t]["div_yield"],
                "beta":          beta_v,
                "ann_return":    ann_ret,
                "net_return":    net_ret,
                "ann_vol":       ann_vol,
                "sharpe":        sharpe,
                "sortino":       sortino,
                "max_drawdown":  max_dd,
                "calmar":        calmar,
                "treynor":       treynor,
                "var_95":        var_95,
                "3yr_return":    self._raw[t]["3yr_return"],
                "5yr_return":    self._raw[t]["5yr_return"],
            }

        return out

    # ── 3. MVO Optimisation ───────────────────────────────────────────────────

    def optimize(self, metrics: dict) -> tuple:
        """
        Run Mean-Variance Optimisation with expense-ratio-adjusted returns.
        Returns (weights_dict, portfolio_metrics_dict).
        """
        valid = [t for t in self.tickers if t in metrics and t in (self._returns.columns if self._returns is not None else [])]
        n = len(valid)
        if n == 0:
            return {}, {}

        cfg     = PROFILE_CFG[self.risk_profile]
        vol_cap = cfg["vol_cap"][self.time_horizon]
        rfr     = RISK_FREE_RATE

        mu    = np.array([metrics[t]["net_return"] for t in valid])
        sigma = self._returns[valid].cov().values * 252   # annualised covariance

        def p_ret(w):  return float(np.dot(w, mu))
        def p_vol(w):  return float(math.sqrt(max(float(w @ sigma @ w), 1e-12)))
        def neg_sharpe(w):
            v = p_vol(w)
            return -(p_ret(w) - rfr) / v if v > 0 else 0.0

        obj_map = {
            "min_vol":    p_vol,
            "max_sharpe": neg_sharpe,
            "max_return": lambda w: -p_ret(w),
        }
        obj_fn = obj_map[cfg["obj"]]

        eq_w   = np.ones(n) / n
        max_w_cash = cfg.get("max_w_cash", cfg["max_w"])
        bounds = [
            (cfg["min_w"], max_w_cash if t in CASH_STABLE_ETFS else cfg["max_w"])
            for t in valid
        ]
        cons   = [
            {"type": "eq",   "fun": lambda w: np.sum(w) - 1.0},
            {"type": "ineq", "fun": lambda w: vol_cap - p_vol(w)},
        ]

        best_w, best_obj = None, float("inf")

        if SCIPY_AVAILABLE:
            rng = np.random.default_rng(42)
            starts = [eq_w]
            for _ in range(10):
                ws = rng.dirichlet(np.ones(n))
                ws = np.clip(ws, cfg["min_w"], cfg["max_w"])
                ws /= ws.sum()
                starts.append(ws)

            for w0 in starts:
                try:
                    res = _sp_min(
                        obj_fn, w0, method="SLSQP",
                        bounds=bounds, constraints=cons,
                        options={"maxiter": 3000, "ftol": 1e-11},
                    )
                    if res.success and res.fun < best_obj:
                        best_obj, best_w = res.fun, res.x.copy()
                except Exception:
                    pass

        if best_w is None:
            # Heuristic fallback — score-proportional weights
            scores = np.array([max(metrics[t]["sharpe"] - metrics[t]["expense_ratio"] * 15, 0.01)
                               for t in valid])
            best_w = scores / scores.sum()
            best_w = np.clip(best_w, cfg["min_w"], cfg["max_w"])
            best_w /= best_w.sum()

        w = np.clip(best_w, 0.0, 1.0)
        w /= w.sum()
        weights = {t: float(w[i]) for i, t in enumerate(valid)}

        # ── Portfolio-level metrics ──
        port_r  = p_ret(w)
        port_v  = p_vol(w)
        port_daily = self._returns[valid].values @ w

        rfr_d   = rfr / 252
        neg_d   = port_daily[port_daily < rfr_d]
        down_v  = float(np.std(neg_d) * math.sqrt(252)) if len(neg_d) > 5 else port_v
        sharpe_p  = (port_r - rfr) / port_v  if port_v  > 0 else 0.0
        sortino_p = (port_r - rfr) / down_v  if down_v  > 0 else 0.0

        cum_p    = (1 + pd.Series(port_daily)).cumprod()
        rm_p     = cum_p.cummax()
        dd_p     = (cum_p - rm_p) / rm_p
        max_dd_p = float(dd_p.min())
        calmar_p = port_r / abs(max_dd_p) if max_dd_p < -0.001 else 0.0

        wtd_exp   = sum(weights[t] * metrics[t]["expense_ratio"]             for t in valid)
        wtd_beta  = sum(weights[t] * float(metrics[t]["beta"] or 1.0)        for t in valid)
        wtd_yield = sum(weights[t] * float(metrics[t]["div_yield"] or 0.0)   for t in valid)

        port_metrics = {
            "expected_return":        port_r,
            "volatility":             port_v,
            "sharpe":                 sharpe_p,
            "sortino":                sortino_p,
            "max_drawdown":           max_dd_p,
            "calmar":                 calmar_p,
            "weighted_expense_ratio": wtd_exp,
            "weighted_beta":          wtd_beta,
            "weighted_yield":         wtd_yield,
            "optimizer": "SciPy SLSQP (MVO)" if SCIPY_AVAILABLE else "Heuristic (install scipy for MVO)",
        }
        return weights, port_metrics

    # ── 4. Per-ETF rationale ──────────────────────────────────────────────────

    def generate_rationale(self, ticker: str, weight: float,
                           metrics: dict, port_metrics: dict) -> str:
        """Return an analyst-style rationale HTML paragraph for one ETF."""
        m   = metrics[ticker]
        pct = weight * 100
        sh  = m["sharpe"]
        sol = m["sortino"]
        vol = m["ann_vol"]
        exp = m["expense_ratio"] or 0.0
        dd  = m["max_drawdown"]
        pv  = port_metrics["volatility"]
        cal = m["calmar"]

        drivers = []

        # ── Cash / stable fund: bespoke rationale ────────────────────────────
        if ticker in CASH_STABLE_ETFS:
            drivers.append(
                f"cash-equivalent / ultra-short duration fund — "
                f"acts as a capital-preservation anchor and liquidity buffer"
            )
            if m["div_yield"] > 0:
                drivers.append(
                    f"currently yielding <b>{m['div_yield']*100:.2f}%</b> "
                    f"with near-zero interest-rate risk"
                )
            if abs(dd) < 0.05:
                drivers.append(
                    f"minimal drawdown risk (<b>{dd*100:.2f}%</b> max) — "
                    f"provides a stable floor under adverse market conditions"
                )
            exp = m["expense_ratio"] or 0.0
            if exp > 0:
                drivers.append(f"low expense ratio <b>{exp*100:.3f}%</b>")

            if pct >= 20:
                tier = f"<b>Core preservation holding ({pct:.1f}%)</b>"
            elif pct >= 10:
                tier = f"<b>Significant cash allocation ({pct:.1f}%)</b>"
            elif pct >= 4:
                tier = f"<b>Liquidity buffer ({pct:.1f}%)</b>"
            elif pct > 0:
                tier = f"<b>Nominal cash position ({pct:.1f}%)</b>"
            else:
                tier = "<b>Zero weight</b>"

            return tier + ": " + " &nbsp;·&nbsp; ".join(drivers[:4]) + "."

        # ── Standard ETF rationale ────────────────────────────────────────────

        # Return quality
        if sh > 1.2:
            drivers.append(f"strong Sharpe ratio <b>{sh:.2f}</b> — highly efficient risk-adjusted returns")
        elif sh > 0.6:
            drivers.append(f"adequate Sharpe ratio <b>{sh:.2f}</b>")
        else:
            drivers.append(f"below-average Sharpe <b>{sh:.2f}</b> — limited return per unit of risk taken")

        # Expense ratio
        if exp > 0.008:
            drivers.append(f"high expense ratio <b>{exp*100:.2f}%</b> — materially drags net return; allocation constrained")
        elif exp > 0.003:
            drivers.append(f"moderate expense ratio <b>{exp*100:.2f}%</b>")
        elif exp > 0:
            drivers.append(f"cost-efficient with a low expense ratio of <b>{exp*100:.3f}%</b>")
        else:
            drivers.append("expense ratio not reported")

        # Volatility vs portfolio
        if vol > pv * 1.6:
            drivers.append(f"volatility <b>{vol*100:.1f}%</b> well above portfolio average — allocation capped to limit concentration risk")
        elif vol < pv * 0.65:
            drivers.append(f"low volatility <b>{vol*100:.1f}%</b> acts as a stabilising anchor, reducing overall portfolio risk")
        else:
            drivers.append(f"volatility <b>{vol*100:.1f}%</b> broadly in line with portfolio target")

        # Drawdown / Calmar
        if abs(dd) > 0.30:
            drivers.append(f"severe max drawdown <b>{dd*100:.1f}%</b> — significant downside tail risk")
        elif abs(dd) > 0.18:
            drivers.append(f"notable max drawdown <b>{dd*100:.1f}%</b> warrants position sizing discipline")
        elif abs(dd) < 0.08:
            drivers.append(f"resilient with a shallow max drawdown of only <b>{dd*100:.1f}%</b>")

        # Sortino / downside quality
        if sol > 1.5:
            drivers.append(f"excellent downside protection (Sortino <b>{sol:.2f}</b>)")
        elif sol < 0.3:
            drivers.append(f"weak downside return quality (Sortino <b>{sol:.2f}</b>)")

        # Allocation tier label
        if pct >= 20:
            tier = f"<b>Core holding ({pct:.1f}%)</b>"
        elif pct >= 10:
            tier = f"<b>Significant position ({pct:.1f}%)</b>"
        elif pct >= 4:
            tier = f"<b>Supporting position ({pct:.1f}%)</b>"
        elif pct > 0:
            tier = f"<b>Diversifier ({pct:.1f}%)</b>"
        else:
            tier = "<b>Zero weight</b>"

        return tier + ": " + " &nbsp;·&nbsp; ".join(drivers[:4]) + "."

    # ── 5. Efficient frontier simulation ─────────────────────────────────────

    def simulate_frontier(self, n_sims: int = 4000) -> pd.DataFrame:
        """Monte-Carlo: random portfolio points for efficient frontier viz."""
        valid = [t for t in self.tickers if t in (self._returns.columns if self._returns is not None else [])]
        if len(valid) < 2:
            return pd.DataFrame()

        mu    = self._returns[valid].mean().values * 252
        sigma = self._returns[valid].cov().values  * 252
        rng   = np.random.default_rng(0)
        rows  = []

        for _ in range(n_sims):
            w   = rng.dirichlet(np.ones(len(valid)))
            ret = float(np.dot(w, mu))
            vol = float(math.sqrt(max(float(w @ sigma @ w), 1e-12)))
            sh  = (ret - RISK_FREE_RATE) / vol if vol > 0 else 0.0
            rows.append({"return": ret, "volatility": vol, "sharpe": sh})

        return pd.DataFrame(rows)
