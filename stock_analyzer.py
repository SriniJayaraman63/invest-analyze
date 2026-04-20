"""
stock_analyzer.py — Data fetching and metric calculation layer.
Wraps yfinance and computes derived metrics.
"""

from __future__ import annotations

import yfinance as yf
import pandas as pd
import numpy as np
import math


def _safe(val):
    """Return None if val is None or NaN, else return val."""
    if val is None:
        return None
    try:
        if isinstance(val, float) and math.isnan(val):
            return None
    except TypeError:
        pass
    return val


class StockAnalyzer:
    def __init__(self, ticker: str):
        self.ticker = ticker.upper().strip()
        self._stock = yf.Ticker(self.ticker)
        self._info: dict | None = None
        self._history: pd.DataFrame | None = None

    # ── Internal helpers ───────────────────────────────────────────────
    @property
    def info(self) -> dict:
        if self._info is None:
            self._info = self._stock.info
        return self._info

    @property
    def history(self) -> pd.DataFrame:
        if self._history is None:
            self._history = self._stock.history(period="1y")
        return self._history

    def _g(self, key, default=None):
        """Safe dict get with NaN guard."""
        return _safe(self.info.get(key, default)) or default

    # ── Public API ─────────────────────────────────────────────────────
    def get_company_overview(self) -> dict:
        return {
            "name":        self._g("longName", self.ticker),
            "ticker":      self.ticker,
            "sector":      self._g("sector", "N/A"),
            "industry":    self._g("industry", "N/A"),
            "country":     self._g("country", "N/A"),
            "employees":   self._g("fullTimeEmployees"),
            "website":     self._g("website", ""),
            "description": self._g("longBusinessSummary", "No description available."),
            "exchange":    self._g("exchange", "N/A"),
        }

    def get_price_data(self) -> dict:
        current   = self._g("currentPrice") or self._g("regularMarketPrice")
        prev      = self._g("previousClose") or self._g("regularMarketPreviousClose")
        change    = (current - prev) if (current and prev) else None
        change_pct = (change / prev * 100) if (change and prev) else None

        week52h = self._g("fiftyTwoWeekHigh")
        week52l = self._g("fiftyTwoWeekLow")
        week52_position = None
        if current and week52h and week52l and (week52h - week52l) > 0:
            week52_position = (current - week52l) / (week52h - week52l) * 100

        return {
            "current_price":   current,
            "prev_close":      prev,
            "day_change":      change,
            "day_change_pct":  change_pct,
            "open":            self._g("open") or self._g("regularMarketOpen"),
            "day_high":        self._g("dayHigh") or self._g("regularMarketDayHigh"),
            "day_low":         self._g("dayLow") or self._g("regularMarketDayLow"),
            "week_52_high":    week52h,
            "week_52_low":     week52l,
            "week_52_position": week52_position,
            "volume":          self._g("volume") or self._g("regularMarketVolume"),
            "avg_volume":      self._g("averageVolume"),
            "market_cap":      self._g("marketCap"),
        }

    def get_valuation_metrics(self) -> dict:
        return {
            "pe_ratio":   self._g("trailingPE"),
            "forward_pe": self._g("forwardPE"),
            "peg_ratio":  self._g("pegRatio"),
            "pb_ratio":   self._g("priceToBook"),
            "ps_ratio":   self._g("priceToSalesTrailing12Months"),
            "ev_ebitda":  self._g("enterpriseToEbitda"),
            "ev":         self._g("enterpriseValue"),
        }

    def get_profitability_metrics(self) -> dict:
        ebitda  = self._g("ebitda")
        revenue = self._g("totalRevenue")
        ebitda_margin = (ebitda / revenue) if (ebitda and revenue and revenue > 0) else None

        return {
            "revenue":        revenue,
            "gross_margin":   self._g("grossMargins"),
            "operating_margin": self._g("operatingMargins"),
            "net_margin":     self._g("profitMargins"),
            "ebitda":         ebitda,
            "ebitda_margin":  ebitda_margin,
            "roe":            self._g("returnOnEquity"),
            "roa":            self._g("returnOnAssets"),
            "eps_ttm":        self._g("trailingEps"),
            "eps_forward":    self._g("forwardEps"),
        }

    def get_financial_health(self) -> dict:
        total_debt = self._g("totalDebt") or 0
        total_cash = self._g("totalCash") or 0

        return {
            "total_cash":          self._g("totalCash"),
            "total_debt":          self._g("totalDebt"),
            "net_debt":            total_debt - total_cash,
            "debt_to_equity":      self._g("debtToEquity"),
            "current_ratio":       self._g("currentRatio"),
            "quick_ratio":         self._g("quickRatio"),
            "free_cash_flow":      self._g("freeCashflow"),
            "operating_cash_flow": self._g("operatingCashflow"),
            "cash_per_share":      self._g("totalCashPerShare"),
        }

    def get_growth_metrics(self) -> dict:
        return {
            "revenue_growth":            self._g("revenueGrowth"),
            "earnings_growth":           self._g("earningsGrowth"),
            "earnings_quarterly_growth": self._g("earningsQuarterlyGrowth"),
        }

    def get_dividend_info(self) -> dict:
        return {
            "dividend_yield":    self._g("dividendYield"),
            "annual_dividend":   self._g("dividendRate"),
            "payout_ratio":      self._g("payoutRatio"),
            "ex_dividend_date":  self._g("exDividendDate"),
            "five_yr_avg_yield": self._g("fiveYearAvgDividendYield"),
        }

    def get_technical_indicators(self) -> dict:
        hist = self.history
        if hist.empty:
            return {}

        close = hist["Close"]
        n = len(close)

        rsi    = _calc_rsi(close, 14)
        sma50  = float(close.rolling(50).mean().iloc[-1])  if n >= 50  else None
        sma200 = float(close.rolling(200).mean().iloc[-1]) if n >= 200 else None

        current = float(close.iloc[-1])
        pct_above_50  = ((current - sma50)  / sma50  * 100) if sma50  else None
        pct_above_200 = ((current - sma200) / sma200 * 100) if sma200 else None

        cross_signal = None
        if sma50 and sma200:
            cross_signal = "Golden Cross (Bullish)" if sma50 > sma200 else "Death Cross (Bearish)"

        vol     = self._g("volume") or self._g("regularMarketVolume")
        avg_vol = self._g("averageVolume")
        vol_ratio = (vol / avg_vol) if (vol and avg_vol and avg_vol > 0) else None

        return {
            "rsi":            rsi,
            "sma_50":         sma50,
            "sma_200":        sma200,
            "pct_above_50":   pct_above_50,
            "pct_above_200":  pct_above_200,
            "cross_signal":   cross_signal,
            "beta":           self._g("beta"),
            "volume_vs_avg":  vol_ratio,
        }

    def get_analyst_info(self) -> dict:
        target_mean = self._g("targetMeanPrice")
        target_high = self._g("targetHighPrice")
        target_low  = self._g("targetLowPrice")
        current     = self._g("currentPrice") or self._g("regularMarketPrice")
        upside      = ((target_mean - current) / current * 100) if (target_mean and current) else None

        return {
            "recommendation":      self._g("recommendationKey", "N/A"),
            "recommendation_mean": self._g("recommendationMean"),
            "target_mean":         target_mean,
            "target_high":         target_high,
            "target_low":          target_low,
            "upside_potential":    upside,
            "num_analysts":        self._g("numberOfAnalystOpinions"),
            "strong_buy_count":    self._g("strongBuyCount", 0) or 0,
            "buy_count":           self._g("buyCount", 0) or 0,
            "hold_count":          self._g("holdCount", 0) or 0,
            "sell_count":          self._g("sellCount", 0) or 0,
            "strong_sell_count":   self._g("strongSellCount", 0) or 0,
        }


# ── Utility functions ─────────────────────────────────────────────────────

def _calc_rsi(prices: pd.Series, period: int = 14) -> float | None:
    delta = prices.diff()
    gain  = delta.where(delta > 0, 0.0).rolling(period).mean()
    loss  = (-delta.where(delta < 0, 0.0)).rolling(period).mean()
    rs    = gain / loss
    rsi   = 100 - (100 / (1 + rs))
    val   = rsi.iloc[-1]
    return float(val) if not math.isnan(float(val)) else None


def fmt_large(num, prefix="$") -> str:
    if num is None:
        return "N/A"
    if abs(num) >= 1e12:
        return f"{prefix}{num/1e12:.2f}T"
    if abs(num) >= 1e9:
        return f"{prefix}{num/1e9:.2f}B"
    if abs(num) >= 1e6:
        return f"{prefix}{num/1e6:.2f}M"
    return f"{prefix}{num:,.0f}"
