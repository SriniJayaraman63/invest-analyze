"""
Equity Research Platform — JPMC-style investment analysis tool.
Single stock deep-dive + multi-stock comparison with analyst-grade commentary.

Run: streamlit run app.py
"""

from __future__ import annotations
import math, warnings
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

warnings.filterwarnings("ignore")

from stock_analyzer import StockAnalyzer, fmt_large
import interpretations as interp
from portfolio_builder import ETFPortfolioOptimizer, PROFILE_CFG, ALLOC_COLORS, SCIPY_AVAILABLE

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Equity Research Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Global ── */
[data-testid="stAppViewContainer"] { background: #f0f4f9 !important; }
[data-testid="stSidebar"]          { background: #00194e !important; }
[data-testid="stSidebar"] section  { background: #00194e !important; }
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div      { color: #c8d8f0 !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3       { color: #ffffff !important; }
[data-testid="stSidebar"] .stTextInput input {
    background: #0a1f3d !important; color: #e0eaff !important;
    border: 1px solid #1e3d6e !important; border-radius: 6px !important;
    font-size: 0.9em !important;
}
[data-testid="stSidebar"] .stButton > button {
    background: #1a56db !important; color: white !important;
    border: none !important; border-radius: 6px !important;
    font-weight: 700 !important; letter-spacing: .3px !important;
    padding: 10px 0 !important; font-size: 0.9em !important;
}
[data-testid="stSidebar"] .stButton > button:hover { background: #1d4ed8 !important; }
[data-testid="stSidebar"] .stRadio label span { color: #c8d8f0 !important; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] hr {
    border-color: #1e3d6e !important;
}

/* ── Remove default Streamlit top padding ── */
.block-container { padding-top: 1.5rem !important; }

/* ── Ticker header card ── */
.ticker-header {
    background: linear-gradient(135deg, #00194e 0%, #003087 100%);
    border-radius: 10px; padding: 18px 22px; color: white; margin-bottom: 0;
    border: 1px solid #1e3d6e;
}
.th-label  { font-size: 0.7em; opacity: .6; text-transform: uppercase; letter-spacing: 1px; }
.th-name   { font-size: 1.0em; font-weight: 700; line-height: 1.2; }
.th-ticker { font-size: 0.8em; opacity: .7; }
.th-price  { font-size: 2.2em; font-weight: 800; font-variant-numeric: tabular-nums; line-height: 1.1; margin-top: 8px; }
.th-up     { color: #4ade80; font-size: 0.9em; font-weight: 600; }
.th-dn     { color: #f87171; font-size: 0.9em; font-weight: 600; }
.th-mcap   { font-size: 0.72em; opacity: .55; margin-top: 6px; }
.th-tags   { margin-top: 8px; }
.th-tag    { display:inline-block; background:rgba(255,255,255,.12); color:white;
             font-size:0.65em; padding:2px 8px; border-radius:10px; margin-right:4px; }

/* ── 52-week bar ── */
.w52-wrap  { margin: 10px 0 6px; }
.w52-labs  { display:flex; justify-content:space-between; font-size:0.72em; color:#94a3b8; margin-bottom:3px; }
.w52-track { background:#e2e8f0; border-radius:4px; height:6px; position:relative; }
.w52-fill  { height:6px; border-radius:4px; background:linear-gradient(90deg,#ef4444,#f59e0b,#22c55e); }
.w52-pin   { position:absolute; top:-5px; width:16px; height:16px; background:#003087;
             border:2.5px solid white; border-radius:50%; transform:translateX(-50%);
             box-shadow:0 1px 4px rgba(0,0,0,.3); }
.w52-pct   { font-size:0.7em; color:#94a3b8; text-align:center; margin-top:4px; }

/* ── At-a-glance scorecard ── */
.aag-box { background:white; border-radius:8px; padding:12px; text-align:center;
           box-shadow:0 1px 4px rgba(0,25,78,.07); }
.aag-icon { font-size:1.5em; }
.aag-cat  { font-size:0.65em; font-weight:700; color:#4a5568; text-transform:uppercase;
            letter-spacing:.8px; margin-top:3px; }
.aag-r    { font-size:0.68em; color:#64748b; }

/* ── Metric row (single stock view) ── */
.mrow  { display:flex; align-items:flex-start; padding:10px 0; border-bottom:1px solid #f0f4f9; gap:12px; }
.mname { font-weight:600; min-width:215px; font-size:0.86em; color:#0f172a; flex-shrink:0; }
.mval  { font-family:'SF Mono','Fira Code',monospace; font-size:0.9em; font-weight:700;
         min-width:88px; flex-shrink:0; color:#0f172a; }
.minterp { font-size:0.8em; color:#475569; line-height:1.55; flex:1; }

/* ── Pill badges ── */
.pill { display:inline-block; padding:1px 8px; border-radius:10px; font-size:0.7em; font-weight:700; margin-left:4px; }
.pill-strong  { background:#d1fae5; color:#065f46; }
.pill-good    { background:#dcfce7; color:#166534; }
.pill-fair    { background:#fef9c3; color:#854d0e; }
.pill-caution { background:#ffedd5; color:#9a3412; }
.pill-weak    { background:#fee2e2; color:#991b1b; }
.pill-neutral { background:#f1f5f9; color:#475569; }

/* ── Section note ── */
.snote { background:#eff6ff; border-left:3px solid #1a56db;
         padding:8px 14px; border-radius:0 6px 6px 0;
         font-size:0.81em; color:#1e40af; margin-bottom:14px; }

/* ── Comparison table ── */
.comp-wrap { background:white; border-radius:10px; overflow:hidden;
             box-shadow:0 2px 10px rgba(0,25,78,.09); margin: 16px 0; }
.comp-table { width:100%; border-collapse:collapse; font-size:0.83em; }
.comp-table thead th {
    background:#00194e; color:white; padding:11px 14px;
    font-weight:600; font-size:0.8em; letter-spacing:.3px; }
.comp-table thead th:not(:first-child) { text-align:right; }
.comp-table .sec-row td {
    background:#eef2f9; color:#003087; font-weight:700; font-size:0.69em;
    letter-spacing:1.8px; text-transform:uppercase; padding:6px 14px;
    border-top:1px solid #dde3ed; border-bottom:1px solid #dde3ed; }
.comp-table tbody tr:not(.sec-row):hover { background:#f8fafc; }
.comp-table tbody td { padding:10px 14px; border-bottom:1px solid #f5f7fb; vertical-align:top; }
.comp-table .m-name { font-weight:600; color:#1a202c; font-size:0.85em; }
.comp-table .m-sub  { font-size:0.72em; color:#94a3b8; font-weight:400; display:block; }
.comp-table .nval   { text-align:right; font-family:'SF Mono','Fira Code',monospace;
                      font-weight:700; font-size:0.9em; white-space:nowrap; }
.comp-table .note-cell { color:#4a5568; font-size:0.78em; line-height:1.5; }
.cb { background:#f0fdf4 !important; }
.cw { background:#fef2f2 !important; }
.cb .nval { color:#065f46 !important; }
.cw .nval { color:#991b1b !important; }

/* rating dots */
.d { display:inline-block; width:6px; height:6px; border-radius:50%; margin-left:4px; vertical-align:middle; }
.d-strong  { background:#065f46; }
.d-good    { background:#16a34a; }
.d-fair    { background:#d97706; }
.d-caution { background:#ea580c; }
.d-weak    { background:#dc2626; }
.d-neutral { background:#94a3b8; }

/* ── Verdict ── */
.verdict-wrap {
    background:linear-gradient(135deg, #00194e 0%, #003087 100%);
    border-radius:10px; padding:24px 28px; color:white; margin:20px 0;
    border:1px solid #1e4080;
}
.v-eyebrow { font-size:0.65em; letter-spacing:2.5px; text-transform:uppercase;
             color:#c9a240; font-weight:700; margin-bottom:6px; }
.v-title   { font-size:1.25em; font-weight:800; margin-bottom:10px; }
.v-body    { font-size:0.83em; line-height:1.75; opacity:.92; }
.v-tag     { display:inline-block; background:rgba(201,162,64,.2); color:#f0c040;
             border:1px solid rgba(201,162,64,.4); font-size:0.72em; font-weight:700;
             padding:2px 10px; border-radius:12px; margin:0 4px; }

/* ── Score summary cards ── */
.sc-card { background:white; border-radius:8px; padding:12px 14px; text-align:center;
           box-shadow:0 1px 4px rgba(0,25,78,.07); }
.sc-cat  { font-size:0.65em; font-weight:700; text-transform:uppercase; letter-spacing:.8px;
           color:#64748b; }
.sc-win  { font-size:1.05em; font-weight:800; color:#003087; margin-top:4px; }
.sc-note { font-size:0.67em; color:#94a3b8; margin-top:2px; }

/* ── Streamlit metric container tweak ── */
[data-testid="metric-container"] {
    background:white; border-radius:8px; padding:10px 14px;
    box-shadow:0 1px 3px rgba(0,25,78,.07);
}

/* ── Portfolio Builder ── */
.pb-step { display:flex; align-items:center; gap:10px; margin-bottom:6px; }
.pb-step-num {
    background:#00194e; color:#c9a240; width:26px; height:26px; border-radius:50%;
    display:flex; align-items:center; justify-content:center;
    font-size:.78em; font-weight:800; flex-shrink:0;
}
.pb-step-label { font-weight:700; color:#00194e; font-size:.92em; }

.port-metric-card {
    background:white; border-radius:10px; padding:16px 18px;
    box-shadow:0 2px 8px rgba(0,25,78,.08); text-align:center;
}
.pmc-label    { font-size:.68em; font-weight:700; text-transform:uppercase;
                letter-spacing:.9px; color:#64748b; }
.pmc-value    { font-size:1.55em; font-weight:800; font-variant-numeric:tabular-nums;
                color:#00194e; margin:4px 0 2px; line-height:1.1; }
.pmc-sublabel { font-size:.68em; color:#94a3b8; }

.alloc-table { width:100%; border-collapse:collapse; font-size:.82em; }
.alloc-table thead th {
    background:#00194e; color:white; padding:10px 13px;
    font-weight:600; font-size:.78em; letter-spacing:.3px; white-space:nowrap;
}
.alloc-table thead th.num { text-align:right; }
.alloc-table tbody td { padding:9px 13px; border-bottom:1px solid #f0f4f9; vertical-align:middle; }
.alloc-table tbody tr:hover { background:#f8fafc; }
.alloc-table .nv { text-align:right; font-family:'SF Mono','Fira Code',monospace; font-weight:700; }
.at-bar-wrap { background:#e2e8f0; border-radius:3px; height:5px; width:100%; margin-top:5px; }
.at-bar-fill { height:5px; border-radius:3px; }

.rationale-card {
    background:white; border-radius:10px; padding:16px 18px;
    box-shadow:0 1px 6px rgba(0,25,78,.07); border-left:4px solid #003087;
}
.rat-header { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px; }
.rat-ticker { font-size:.7em; font-weight:700; text-transform:uppercase;
              letter-spacing:1px; color:#003087; }
.rat-name   { font-size:.86em; font-weight:700; color:#0f172a; margin-top:2px; }
.rat-alloc  { font-size:1.9em; font-weight:800; color:#003087; font-variant-numeric:tabular-nums; }
.rat-body   { font-size:.79em; color:#475569; line-height:1.65; }

.optimizer-badge {
    display:inline-block; background:#eff6ff; color:#1e40af;
    border:1px solid #bfdbfe; border-radius:12px;
    font-size:.68em; font-weight:600; padding:2px 10px; margin-left:6px;
}

/* ── Tab styling ── */
.stTabs [data-baseweb="tab-list"] { gap:4px; }
.stTabs [data-baseweb="tab"] {
    background:#e8eef8; border-radius:6px 6px 0 0;
    font-size:0.82em; font-weight:600; color:#3d5a99;
    padding:6px 14px;
}
.stTabs [aria-selected="true"][data-baseweb="tab"] {
    background:#00194e; color:white;
}

/* ── Disclaimer ── */
.disclaimer {
    background:#fffbeb; border:1px solid #fde68a; border-radius:8px;
    padding:12px 16px; font-size:0.76em; color:#92400e; margin-top:16px;
    line-height:1.6;
}
</style>
""", unsafe_allow_html=True)


# ─── Format helpers ───────────────────────────────────────────────────────────

def _fv(val, spec=".2f", prefix="", suffix="", na="—"):
    if val is None: return na
    try:
        if math.isnan(float(val)): return na
        return f"{prefix}{val:{spec}}{suffix}"
    except Exception: return na

def _fp(val, na="—"):
    if val is None: return na
    try:
        if math.isnan(float(val)): return na
        return f"{val*100:.2f}%"
    except Exception: return na

def _pill(rating):
    icons = {"strong":"▲ Strong","good":"✓ Good","fair":"~ Fair",
             "caution":"⚠ Caution","weak":"▼ Weak","neutral":"— N/A"}
    return f'<span class="pill pill-{rating}">{icons.get(rating,rating)}</span>'

def _dot(rating):
    return f'<span class="d d-{rating}"></span>'

def _render_metric(name, value, rating, interpretation):
    st.markdown(
        f'<div class="mrow">'
        f'<div class="mname">{name}{_pill(rating)}</div>'
        f'<div class="mval">{value}</div>'
        f'<div class="minterp">{interpretation}</div>'
        f'</div>', unsafe_allow_html=True)

def _note(text):
    st.markdown(f'<div class="snote">{text}</div>', unsafe_allow_html=True)


# ─── 52-week range bar ────────────────────────────────────────────────────────

def _52w_bar(low, high, current):
    if not (low and high and current and high > low): return
    pct = max(0, min(100, (current - low) / (high - low) * 100))
    st.markdown(f"""
    <div class="w52-wrap">
      <div class="w52-labs">
        <span>52W Low ${low:,.2f}</span>
        <span style="font-weight:600;color:#1e293b;">Current ${current:,.2f}</span>
        <span>52W High ${high:,.2f}</span>
      </div>
      <div class="w52-track">
        <div class="w52-fill" style="width:{pct}%"></div>
        <div class="w52-pin"  style="left:{pct}%"></div>
      </div>
      <div class="w52-pct">{pct:.0f}% of 52-week range</div>
    </div>""", unsafe_allow_html=True)


# ─── Price chart ──────────────────────────────────────────────────────────────

def _chart(hist, ticker, color="#003087"):
    if hist is None or hist.empty: return
    df = hist.copy()
    df["SMA50"]  = df["Close"].rolling(50).mean()
    df["SMA200"] = df["Close"].rolling(200).mean()

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        vertical_spacing=0.03, row_heights=[0.75, 0.25])

    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"],
        increasing_line_color="#22c55e", decreasing_line_color="#ef4444",
        showlegend=False), row=1, col=1)

    if not df["SMA50"].isna().all():
        fig.add_trace(go.Scatter(x=df.index, y=df["SMA50"],
            name="50-Day MA", line=dict(color="#f59e0b", width=1.8)), row=1, col=1)
    if not df["SMA200"].isna().all():
        fig.add_trace(go.Scatter(x=df.index, y=df["SMA200"],
            name="200-Day MA", line=dict(color="#6366f1", width=1.8)), row=1, col=1)

    colors = ["#22c55e" if c >= o else "#ef4444"
              for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(go.Bar(x=df.index, y=df["Volume"],
        marker_color=colors, showlegend=False), row=2, col=1)

    fig.update_layout(height=440, xaxis_rangeslider_visible=False,
        margin=dict(l=0, r=0, t=8, b=0),
        legend=dict(orientation="h", y=1.05, x=0, font_size=11),
        paper_bgcolor="white", plot_bgcolor="#fafafa",
        hovermode="x unified", font=dict(family="Inter,sans-serif"))
    for r in [1, 2]:
        fig.update_yaxes(gridcolor="#e2e8f0", row=r, col=1)
    fig.update_xaxes(gridcolor="#e2e8f0")
    st.plotly_chart(fig, use_container_width=True)


# ─── Scorecard ────────────────────────────────────────────────────────────────

SCORE_ICON = {"strong":"🟢","good":"🟢","fair":"🟡","caution":"🟠","weak":"🔴","neutral":"⚪"}

def _compute_scores(val_m, prof_m, health_m, growth_m, div_m, tech_m):
    def _avg(*ratings):
        w = {"strong":5,"good":4,"fair":3,"caution":2,"weak":1,"neutral":3}
        s = [w.get(r,3) for r in ratings if r!="neutral"]
        if not s: return "neutral"
        a = sum(s)/len(s)
        if a >= 4.5: return "strong"
        if a >= 3.8: return "good"
        if a >= 3.0: return "fair"
        if a >= 2.2: return "caution"
        return "weak"

    pe_r,  _ = interp.pe_ratio(val_m.get("pe_ratio"))
    fpe_r, _ = interp.forward_pe(val_m.get("forward_pe"))
    peg_r, _ = interp.peg_ratio(val_m.get("peg_ratio"))
    pb_r,  _ = interp.pb_ratio(val_m.get("pb_ratio"))
    ps_r,  _ = interp.ps_ratio(val_m.get("ps_ratio"))
    ev_r,  _ = interp.ev_ebitda(val_m.get("ev_ebitda"))

    gm_r,  _ = interp.gross_margin(prof_m.get("gross_margin"))
    om_r,  _ = interp.operating_margin(prof_m.get("operating_margin"))
    nm_r,  _ = interp.net_margin(prof_m.get("net_margin"))
    roe_r, _ = interp.roe(prof_m.get("roe"))
    roa_r, _ = interp.roa(prof_m.get("roa"))

    de_r,  _ = interp.debt_to_equity(health_m.get("debt_to_equity"))
    cr_r,  _ = interp.current_ratio(health_m.get("current_ratio"))
    fcf    = health_m.get("free_cash_flow") or 0
    fcf_r  = "good" if fcf > 0 else "caution"

    rg_r,  _ = interp.revenue_growth(growth_m.get("revenue_growth"))
    eg_r,  _ = interp.earnings_growth(growth_m.get("earnings_growth"))
    dy_r,  _ = interp.dividend_yield(div_m.get("dividend_yield"))
    pr_r,  _ = interp.payout_ratio(div_m.get("payout_ratio"))
    rsi_r, _ = interp.rsi(tech_m.get("rsi"))
    b_r,   _ = interp.beta(tech_m.get("beta"))

    return {
        "Valuation":        _avg(pe_r, fpe_r, peg_r, pb_r, ps_r, ev_r),
        "Profitability":    _avg(gm_r, om_r, nm_r, roe_r, roa_r),
        "Financial Health": _avg(de_r, cr_r, fcf_r),
        "Growth":           _avg(rg_r, eg_r),
        "Dividends":        _avg(dy_r, pr_r),
        "Technicals":       _avg(rsi_r, b_r),
    }


# ─── Comparison helpers ───────────────────────────────────────────────────────

def _best_idx(values, mode):
    """
    mode: 'lower' = lower positive wins, 'higher' = higher wins,
          'near1' = closest to 1.0 wins, 'mid' = closest to 55 wins (RSI)
    Returns index of best, or None if all None.
    """
    indexed = [(i, v) for i, v in enumerate(values) if v is not None and not math.isnan(float(v))]
    if len(indexed) < 2: return None
    if mode == "lower":
        pos = [(i, v) for i, v in indexed if v > 0]
        if not pos: return None
        return min(pos, key=lambda x: x[1])[0]
    if mode == "higher":
        return max(indexed, key=lambda x: x[1])[0]
    if mode == "near1":
        return min(indexed, key=lambda x: abs(x[1] - 1.0))[0]
    if mode == "mid":
        return min(indexed, key=lambda x: abs(x[1] - 55))[0]
    return None

def _worst_idx(values, mode):
    indexed = [(i, v) for i, v in enumerate(values) if v is not None and not math.isnan(float(v))]
    if len(indexed) < 2: return None
    if mode == "lower":
        pos = [(i, v) for i, v in indexed if v > 0]
        if not pos: return None
        return max(pos, key=lambda x: x[1])[0]
    if mode == "higher":
        return min(indexed, key=lambda x: x[1])[0]
    if mode in ("near1", "mid"):
        bi = _best_idx(values, mode)
        remaining = [(i, v) for i, v in indexed if i != bi]
        if not remaining: return None
        return max(remaining, key=lambda x: abs(x[1] - (1.0 if mode=="near1" else 55)))[0]
    return None

def _comp_note(names, values, mode, metric, unit=""):
    """
    Generate a brief analyst-style comparison note.
    """
    valid = [(n, v) for n, v in zip(names, values) if v is not None]
    if len(valid) < 2: return "Insufficient data."
    bi = _best_idx(values, mode)
    wi = _worst_idx(values, mode)
    if bi is None: return ""
    best_name, best_val = names[bi], values[bi]
    worst_name = names[wi] if wi is not None else None
    worst_val  = values[wi] if wi is not None else None

    if mode == "lower" and worst_val and best_val and best_val > 0:
        disc = (worst_val - best_val) / best_val * 100
        return f"<b>{best_name}</b> is the cheapest at {best_val:.1f}{unit} — {disc:.0f}% discount to {worst_name} ({worst_val:.1f}{unit})."
    if mode == "higher" and worst_val is not None:
        if abs(best_val) < 5:  # it's a ratio/margin
            diff = (best_val - worst_val) * 100
            return f"<b>{best_name}</b> leads with {best_val*100:.1f}% vs {worst_name}'s {worst_val*100:.1f}% (+{diff:.1f} pp advantage)."
        return f"<b>{best_name}</b> leads: {best_val:.1f}{unit} vs {worst_name}'s {worst_val:.1f}{unit}."
    if mode == "near1":
        return f"<b>{best_name}</b> has the most balanced PEG ({best_val:.2f}) relative to its growth."
    return f"<b>{best_name}</b> shows the stronger signal on {metric}."

def _cell(val_str, rating, cls):
    return f'<td class="nval {cls}">{val_str} {_dot(rating)}</td>'

def _build_comp_table(all_data, tickers, names, n):
    """Build the full comparison HTML table."""

    # ── helpers ──────────────────────────────────────────────────────────────
    def note_col(text):
        return f'<td class="note-cell">{text}</td>'

    def row(metric, sub, values_strs, values_raw, ratings, mode, note_txt):
        bi = _best_idx(values_raw, mode)
        wi = _worst_idx(values_raw, mode)
        cells = ""
        for i, (vs, rt) in enumerate(zip(values_strs, ratings)):
            cls = "cb" if i == bi else ("cw" if i == wi else "")
            cells += _cell(vs, rt, cls)
        sub_html = f'<span class="m-sub">{sub}</span>' if sub else ""
        return (f'<tr><td class="m-name">{metric}{sub_html}</td>'
                f'{cells}{note_col(note_txt)}</tr>')

    def sec(label):
        return f'<tr class="sec-row"><td colspan="{n+2}">{label}</td></tr>'

    # ── pull data ─────────────────────────────────────────────────────────────
    def _g(cat, key):
        return [all_data[t][cat].get(key) for t in tickers]

    note_hdr = "Analyst Note" if n == 2 else "Analyst Note"
    ticker_headers = "".join(
        f'<th style="text-align:right">{nm}<br><span style="font-size:.8em;opacity:.6;">{tickers[i]}</span></th>'
        for i, nm in enumerate(names)
    )

    rows_html = ""

    # ── VALUATION ─────────────────────────────────────────────────────────────
    rows_html += sec("📊  Valuation — Is it cheap or expensive?")

    def val_row(metric, sub, key, mode, fmt_s, unit, rating_fn):
        raw   = _g("val", key)
        strs  = [fmt_s(v) for v in raw]
        rats  = [rating_fn(v)[0] for v in raw]
        note  = _comp_note(names, raw, mode, metric, unit)
        return row(metric, sub, strs, raw, rats, mode, note)

    rows_html += val_row("P/E Ratio","Trailing 12M","pe_ratio","lower",
        lambda v: _fv(v,".1f",suffix="x"), "x", interp.pe_ratio)
    rows_html += val_row("Forward P/E","Next 12M est.","forward_pe","lower",
        lambda v: _fv(v,".1f",suffix="x"), "x", interp.forward_pe)
    rows_html += val_row("PEG Ratio","Growth-adjusted P/E","peg_ratio","near1",
        lambda v: _fv(v,".2f"), "", interp.peg_ratio)
    rows_html += val_row("Price / Book","P/B","pb_ratio","lower",
        lambda v: _fv(v,".2f",suffix="x"), "x", interp.pb_ratio)
    rows_html += val_row("Price / Sales","P/S TTM","ps_ratio","lower",
        lambda v: _fv(v,".2f",suffix="x"), "x", interp.ps_ratio)
    rows_html += val_row("EV / EBITDA","Enterprise multiple","ev_ebitda","lower",
        lambda v: _fv(v,".1f",suffix="x"), "x", interp.ev_ebitda)

    # ── PROFITABILITY ─────────────────────────────────────────────────────────
    rows_html += sec("💰  Profitability — How well does it convert sales to profit?")

    def prof_row(metric, sub, key, mode, fmt_s, unit, rating_fn):
        raw  = _g("prof", key)
        strs = [fmt_s(v) for v in raw]
        rats = [rating_fn(v)[0] for v in raw]
        note = _comp_note(names, raw, mode, metric, unit)
        return row(metric, sub, strs, raw, rats, mode, note)

    rows_html += prof_row("Gross Margin","","gross_margin","higher",
        lambda v: _fp(v), "%", interp.gross_margin)
    rows_html += prof_row("Operating Margin","EBIT/Revenue","operating_margin","higher",
        lambda v: _fp(v), "%", interp.operating_margin)
    rows_html += prof_row("Net Profit Margin","Bottom line","net_margin","higher",
        lambda v: _fp(v), "%", interp.net_margin)
    rows_html += prof_row("Return on Equity","ROE","roe","higher",
        lambda v: _fp(v), "%", interp.roe)
    rows_html += prof_row("Return on Assets","ROA","roa","higher",
        lambda v: _fp(v), "%", interp.roa)

    # ── FINANCIAL HEALTH ──────────────────────────────────────────────────────
    rows_html += sec("🏦  Financial Health — Is the balance sheet solid?")

    de_raw  = _g("health", "debt_to_equity")
    de_n    = [v/100 if (v and abs(v)>10) else v for v in de_raw]
    de_strs = [_fv(v, ".2f", suffix="x") for v in de_n]
    de_rats = [interp.debt_to_equity(v)[0] for v in de_raw]
    de_note = _comp_note(names, de_n, "lower", "D/E", "x")
    rows_html += row("Debt / Equity","Leverage ratio", de_strs, de_n, de_rats, "lower", de_note)

    cr_raw  = _g("health", "current_ratio")
    cr_strs = [_fv(v,".2f",suffix="x") for v in cr_raw]
    cr_rats = [interp.current_ratio(v)[0] for v in cr_raw]
    cr_note = _comp_note(names, cr_raw, "higher", "Current Ratio", "x")
    rows_html += row("Current Ratio","Short-term liquidity", cr_strs, cr_raw, cr_rats, "higher", cr_note)

    fcf_raw  = _g("health", "free_cash_flow")
    fcf_strs = [fmt_large(v) if v else "—" for v in fcf_raw]
    fcf_rats = ["good" if (v or 0)>0 else ("caution" if v is not None else "neutral") for v in fcf_raw]
    fcf_bi   = _best_idx(fcf_raw, "higher")
    fcf_wi   = _worst_idx(fcf_raw, "higher")
    fcf_cells = ""
    for i, (vs, rt) in enumerate(zip(fcf_strs, fcf_rats)):
        cls = "cb" if i==fcf_bi else ("cw" if i==fcf_wi else "")
        fcf_cells += _cell(vs, rt, cls)
    fcf_note_parts = [f"{nm}: {fmt_large(v)}" for nm, v in zip(names, fcf_raw) if v is not None]
    fcf_note = (f"<b>{names[fcf_bi]}</b> generates the most free cash — " +
                " vs ".join(fcf_note_parts) + ".") if fcf_bi is not None else "FCF comparison unavailable."
    rows_html += (f'<tr><td class="m-name">Free Cash Flow<span class="m-sub">Cash after capex</span></td>'
                  f'{fcf_cells}<td class="note-cell">{fcf_note}</td></tr>')

    # ── GROWTH ────────────────────────────────────────────────────────────────
    rows_html += sec("📈  Growth — How fast is the business expanding?")

    def grow_row(metric, sub, key, rating_fn):
        raw  = _g("growth", key)
        strs = [_fp(v) for v in raw]
        rats = [rating_fn(v)[0] for v in raw]
        note = _comp_note(names, raw, "higher", metric, "%")
        return row(metric, sub, strs, raw, rats, "higher", note)

    rows_html += grow_row("Revenue Growth","Year-over-year","revenue_growth", interp.revenue_growth)
    rows_html += grow_row("Earnings Growth","Year-over-year","earnings_growth", interp.earnings_growth)

    # ── DIVIDENDS ─────────────────────────────────────────────────────────────
    rows_html += sec("💵  Dividends — Does it pay you to hold it?")

    dy_raw  = _g("div", "dividend_yield")
    dy_strs = [_fp(v) if v else "None" for v in dy_raw]
    dy_rats = [interp.dividend_yield(v)[0] for v in dy_raw]
    dy_note = _comp_note(names, [v or 0 for v in dy_raw], "higher", "Yield", "%")
    rows_html += row("Dividend Yield","Annual %", dy_strs, [v or 0 for v in dy_raw], dy_rats, "higher", dy_note)

    pr_raw  = _g("div", "payout_ratio")
    pr_strs = [_fp(v) for v in pr_raw]
    pr_rats = [interp.payout_ratio(v)[0] for v in pr_raw]
    pr_note_parts = [f"{nm}: {_fp(v)}" for nm, v in zip(names, pr_raw) if v is not None]
    pr_note = "Payout ratio comparison: " + " | ".join(pr_note_parts) + ". Lower payout leaves more room for reinvestment and dividend growth." if pr_note_parts else "Not available."
    rows_html += row("Payout Ratio","% of earnings paid out", pr_strs, pr_raw, pr_rats, "lower", pr_note)

    # ── TECHNICALS ────────────────────────────────────────────────────────────
    rows_html += sec("📉  Technicals — What does the market signal?")

    rsi_raw  = _g("tech", "rsi")
    rsi_strs = [_fv(v,".1f") for v in rsi_raw]
    rsi_rats = [interp.rsi(v)[0] for v in rsi_raw]
    rsi_bi   = _best_idx(rsi_raw, "mid")
    rsi_wi   = _worst_idx(rsi_raw, "mid")
    rsi_cells = ""
    for i, (vs, rt) in enumerate(zip(rsi_strs, rsi_rats)):
        cls = "cb" if i==rsi_bi else ("cw" if i==rsi_wi else "")
        rsi_cells += _cell(vs, rt, cls)
    rsi_note_parts = [f"{nm}: RSI {_fv(v,'.1f')}" for nm, v in zip(names, rsi_raw) if v is not None]
    rsi_note = " | ".join(rsi_note_parts) + ". RSI between 40–60 is neutral momentum; above 70 overbought; below 30 oversold." if rsi_note_parts else "Not available."
    rows_html += (f'<tr><td class="m-name">RSI (14-Day)<span class="m-sub">Momentum gauge</span></td>'
                  f'{rsi_cells}<td class="note-cell">{rsi_note}</td></tr>')

    beta_raw  = _g("tech", "beta")
    beta_strs = [_fv(v,".2f") for v in beta_raw]
    beta_rats = [interp.beta(v)[0] for v in beta_raw]
    beta_note = _comp_note(names, beta_raw, "lower", "Beta", "")
    rows_html += row("Beta","vs S&P 500 volatility", beta_strs, beta_raw, beta_rats, "lower", beta_note)

    # ── TABLE ASSEMBLY ─────────────────────────────────────────────────────────
    note_w = "28%" if n == 2 else "22%"
    col_w  = f"{(72 - int(note_w[:-1])) // (n+1)}%"

    html = f"""
    <div class="comp-wrap">
    <table class="comp-table">
      <thead>
        <tr>
          <th style="width:{col_w}">Metric</th>
          {ticker_headers}
          <th style="text-align:left;width:{note_w}">{note_hdr}</th>
        </tr>
      </thead>
      <tbody>
        {rows_html}
      </tbody>
    </table>
    </div>
    """
    return html


# ─── Comparison verdict ───────────────────────────────────────────────────────

def _build_verdict(all_data, tickers, names, scores_per_ticker):
    """
    Build analyst-style verdict HTML based on scored metrics.
    """
    CATS = ["Valuation", "Profitability", "Financial Health", "Growth", "Dividends", "Technicals"]
    W    = {"strong":5, "good":4, "fair":3, "caution":2, "weak":1, "neutral":3}

    totals = {t: sum(W.get(scores_per_ticker[t].get(c, "neutral"), 3) for c in CATS)
              for t in tickers}
    ranked = sorted(tickers, key=lambda t: totals[t], reverse=True)
    winner = ranked[0]
    w_name = names[tickers.index(winner)]

    # Category wins
    cat_winners = {}
    for cat in CATS:
        best_t = max(tickers, key=lambda t: W.get(scores_per_ticker[t].get(cat,"neutral"),3))
        cat_winners[cat] = names[tickers.index(best_t)]

    # Build bullet points
    bullets = []
    val_win = cat_winners.get("Valuation")
    prof_win = cat_winners.get("Profitability")
    grow_win = cat_winners.get("Growth")
    health_win = cat_winners.get("Financial Health")
    div_win = cat_winners.get("Dividends")
    tech_win = cat_winners.get("Technicals")

    if val_win:
        pe_vals = {names[i]: all_data[t]["val"].get("pe_ratio") for i, t in enumerate(tickers)}
        pe_str  = " | ".join(f"{n}: {_fv(v,'.1f','','x')}" for n, v in pe_vals.items() if v)
        bullets.append(f"<b>{val_win}</b> offers the most attractive valuation on earnings and enterprise multiples. ({pe_str})")

    if prof_win:
        nm_vals = {names[i]: all_data[t]["prof"].get("net_margin") for i, t in enumerate(tickers)}
        nm_str  = " | ".join(f"{n}: {_fp(v)}" for n, v in nm_vals.items() if v)
        bullets.append(f"<b>{prof_win}</b> is the most profitable business, with the strongest margin and return metrics. ({nm_str} net margin)")

    if grow_win:
        rg_vals = {names[i]: all_data[t]["growth"].get("revenue_growth") for i, t in enumerate(tickers)}
        rg_str  = " | ".join(f"{n}: {_fp(v)}" for n, v in rg_vals.items() if v)
        bullets.append(f"<b>{grow_win}</b> is growing fastest, with superior revenue and earnings expansion. ({rg_str} revenue growth YoY)")

    if health_win:
        bullets.append(f"<b>{health_win}</b> has the most conservative balance sheet — lowest leverage and strongest liquidity position.")

    all_same = len(set(cat_winners.values())) == 1
    if all_same:
        summary = f"{w_name} leads across all six dimensions — valuation, profitability, financial health, growth, dividends, and technicals."
    else:
        win_cats = [c for c, n in cat_winners.items() if n == w_name]
        summary = (f"{w_name} presents the strongest overall fundamental and technical profile, "
                   f"leading on {len(win_cats)} of {len(CATS)} dimensions: {', '.join(win_cats)}.")

    # Tags for each ticker
    tag_html = ""
    for i, (t, nm) in enumerate(zip(tickers, names)):
        wins = [c for c, wn in cat_winners.items() if wn == nm]
        if wins:
            tag_html += f'<span class="v-tag">{nm} → {", ".join(wins)}</span> '

    bullet_html = "".join(f"<li style='margin-bottom:6px'>{b}</li>" for b in bullets)

    return f"""
    <div class="verdict-wrap">
      <div class="v-eyebrow">Analyst Verdict</div>
      <div class="v-title">{summary}</div>
      <div class="v-body">
        <ul style="padding-left:18px; margin:8px 0 14px">
          {bullet_html}
        </ul>
        {tag_html}
      </div>
      <div style="font-size:0.7em;opacity:.45;margin-top:14px;">
        This analysis is algorithmic and for informational purposes only. Not financial advice.
      </div>
    </div>"""


# ─── Comparison view ─────────────────────────────────────────────────────────

def render_comparison(tickers_input):
    tickers = [t.strip().upper() for t in tickers_input if t.strip()]
    if not tickers:
        return

    st.markdown(f"### Comparing {' · '.join(tickers)}")

    # ── Fetch all data ────────────────────────────────────────────────────────
    all_data   = {}
    names      = []
    price_data = {}
    hists      = {}

    progress = st.progress(0, text="Fetching data…")
    for idx, ticker in enumerate(tickers):
        progress.progress((idx + 1) / len(tickers), text=f"Loading {ticker}…")
        try:
            az = StockAnalyzer(ticker)
            pd_ = az.get_price_data()
            if not pd_.get("current_price"):
                st.error(f"Could not fetch data for **{ticker}**. Skipping.")
                continue
            all_data[ticker] = {
                "val":    az.get_valuation_metrics(),
                "prof":   az.get_profitability_metrics(),
                "health": az.get_financial_health(),
                "growth": az.get_growth_metrics(),
                "div":    az.get_dividend_info(),
                "tech":   az.get_technical_indicators(),
            }
            names.append(az.get_company_overview()["name"].split()[0])  # short name
            price_data[ticker] = pd_
            hists[ticker]      = az.history
        except Exception as e:
            st.error(f"Error loading {ticker}: {e}")
    progress.empty()

    tickers = [t for t in tickers if t in all_data]
    if len(tickers) < 2:
        st.warning("Need at least 2 valid tickers to compare.")
        return
    n = len(tickers)

    # ── Ticker header cards ───────────────────────────────────────────────────
    header_cols = st.columns(n)
    for col, ticker, name in zip(header_cols, tickers, names):
        pd_ = price_data[ticker]
        cur   = pd_.get("current_price", 0)
        chg   = pd_.get("day_change")
        chgp  = pd_.get("day_change_pct")
        mcap  = pd_.get("market_cap")
        sec   = all_data[ticker]["val"]   # reuse
        sector   = StockAnalyzer(ticker).get_company_overview().get("sector","—")
        industry = StockAnalyzer(ticker).get_company_overview().get("industry","—")

        if chg is not None:
            arrow = "▲" if chg >= 0 else "▼"
            cls   = "th-up" if chg >= 0 else "th-dn"
            chg_html = f'<span class="{cls}">{arrow} ${abs(chg):.2f} ({abs(chgp):.2f}%)</span>'
        else:
            chg_html = ""

        with col:
            st.markdown(f"""
            <div class="ticker-header">
              <div class="th-label">EQUITY RESEARCH</div>
              <div class="th-name">{name}</div>
              <div class="th-ticker">{ticker}</div>
              <div class="th-price">${cur:,.2f}</div>
              <div style="margin-top:2px">{chg_html}</div>
              <div class="th-mcap">Mkt Cap: {fmt_large(mcap)}</div>
              <div class="th-tags">
                <span class="th-tag">{sector}</span>
                <span class="th-tag">{industry[:22]}</span>
              </div>
            </div>""", unsafe_allow_html=True)
            _52w_bar(pd_.get("week_52_low"), pd_.get("week_52_high"), cur)

    # ── Overlaid price chart ──────────────────────────────────────────────────
    with st.expander("📈 Price History — Relative Performance (1Y)", expanded=True):
        fig = go.Figure()
        for ticker in tickers:
            hist = hists.get(ticker)
            if hist is not None and not hist.empty:
                close = hist["Close"]
                rebased = (close / close.iloc[0]) * 100
                fig.add_trace(go.Scatter(
                    x=hist.index, y=rebased,
                    name=ticker, mode="lines", line=dict(width=2.2),
                ))
        fig.update_layout(
            height=360, paper_bgcolor="white", plot_bgcolor="#fafafa",
            margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation="h", y=1.05),
            hovermode="x unified",
            yaxis_title="Rebased to 100 (1Y ago)",
            font=dict(family="Inter,sans-serif"),
        )
        fig.update_yaxes(gridcolor="#e2e8f0")
        fig.update_xaxes(gridcolor="#e2e8f0")
        st.plotly_chart(fig, use_container_width=True)

    # ── Score summary ─────────────────────────────────────────────────────────
    scores_per_ticker = {}
    for ticker in tickers:
        d = all_data[ticker]
        scores_per_ticker[ticker] = _compute_scores(
            d["val"], d["prof"], d["health"], d["growth"], d["div"], d["tech"])

    CATS = ["Valuation", "Profitability", "Financial Health", "Growth", "Dividends", "Technicals"]
    W    = {"strong":5,"good":4,"fair":3,"caution":2,"weak":1,"neutral":3}

    st.markdown("#### Category Scorecard")
    sc_cols = st.columns(len(CATS))
    for col, cat in zip(sc_cols, CATS):
        best_t = max(tickers, key=lambda t: W.get(scores_per_ticker[t].get(cat,"neutral"),3))
        best_n = names[tickers.index(best_t)]
        best_r = scores_per_ticker[best_t].get(cat, "neutral")
        icon   = SCORE_ICON.get(best_r, "⚪")
        others = " | ".join(
            f"{names[tickers.index(t)]}: {scores_per_ticker[t].get(cat,'neutral').title()}"
            for t in tickers
        )
        col.markdown(
            f'<div class="sc-card">'
            f'<div class="sc-cat">{cat}</div>'
            f'<div style="font-size:1.5em;margin:3px 0">{icon}</div>'
            f'<div class="sc-win">{best_n} leads</div>'
            f'<div class="sc-note">{others}</div>'
            f'</div>', unsafe_allow_html=True)

    st.markdown("&nbsp;", unsafe_allow_html=True)

    # ── Verdict ───────────────────────────────────────────────────────────────
    st.markdown(_build_verdict(all_data, tickers, names, scores_per_ticker),
                unsafe_allow_html=True)

    # ── Comparison table ──────────────────────────────────────────────────────
    st.markdown("#### Side-by-Side Fundamental & Technical Comparison")
    table_html = _build_comp_table(all_data, tickers, names, n)
    st.markdown(table_html, unsafe_allow_html=True)

    st.markdown("""
    <div class="disclaimer">
    <b>Disclaimer:</b> This analysis is generated algorithmically from public market data and is for
    <b>informational purposes only</b>. It does not constitute financial advice, a recommendation to buy or sell
    any security, or an offer. Market data may be delayed. Past performance is not indicative of future results.
    Always consult a qualified financial professional before making investment decisions.
    </div>""", unsafe_allow_html=True)


# ─── Single stock view ────────────────────────────────────────────────────────

def render_single(ticker_input):
    ticker = ticker_input.strip().upper()
    with st.spinner(f"Loading {ticker} …"):
        try:
            az = StockAnalyzer(ticker)
            ov = az.get_company_overview()
            pd_ = az.get_price_data()
            val_m    = az.get_valuation_metrics()
            prof_m   = az.get_profitability_metrics()
            health_m = az.get_financial_health()
            growth_m = az.get_growth_metrics()
            div_m    = az.get_dividend_info()
            tech_m   = az.get_technical_indicators()
            analyst_m= az.get_analyst_info()
            hist     = az.history
            if not pd_.get("current_price"):
                st.error(f"No data found for **{ticker}**. Check the symbol.")
                return
        except Exception as e:
            st.error(f"Error: {e}")
            return

    cur   = pd_["current_price"]
    chg   = pd_.get("day_change")
    chgp  = pd_.get("day_change_pct")
    mcap  = pd_.get("market_cap")
    emp   = ov.get("employees")

    # ── Header ────────────────────────────────────────────────────────────────
    if chg is not None:
        arrow, cls = ("▲","th-up") if chg >= 0 else ("▼","th-dn")
        chg_html = f'<span class="{cls}">{arrow} ${abs(chg):.2f} ({abs(chgp):.2f}%)</span>'
    else:
        chg_html = ""

    emp_str = f"{emp:,} employees · " if emp else ""

    col_hdr, col_meta = st.columns([3, 2])
    with col_hdr:
        st.markdown(f"""
        <div class="ticker-header">
          <div class="th-label">EQUITY RESEARCH · SINGLE STOCK ANALYSIS</div>
          <div class="th-name" style="font-size:1.2em">{ov['name']}</div>
          <div class="th-ticker">{ticker} · {ov['exchange']} · {ov['sector']}</div>
          <div class="th-price">${cur:,.2f}</div>
          <div style="margin-top:2px">{chg_html}</div>
          <div class="th-mcap">Market Cap: {fmt_large(mcap)} · {emp_str}{ov['country']}</div>
        </div>""", unsafe_allow_html=True)
        _52w_bar(pd_.get("week_52_low"), pd_.get("week_52_high"), cur)

    with col_meta:
        q = st.columns(2)
        q[0].metric("EPS (TTM)",    _fv(prof_m.get("eps_ttm"), ".2f", "$"))
        q[1].metric("P/E (TTM)",    _fv(val_m.get("pe_ratio"),  ".1f", suffix="x"))
        q[0].metric("Div Yield",    _fp(div_m.get("dividend_yield")))
        q[1].metric("Beta",         _fv(tech_m.get("beta"), ".2f"))
        q[0].metric("RSI (14d)",    _fv(tech_m.get("rsi"), ".1f"))
        q[1].metric("Fwd P/E",      _fv(val_m.get("forward_pe"), ".1f", suffix="x"))

    # ── Chart ─────────────────────────────────────────────────────────────────
    _chart(hist, ticker)

    # ── At-a-glance ───────────────────────────────────────────────────────────
    scores = _compute_scores(val_m, prof_m, health_m, growth_m, div_m, tech_m)
    st.markdown("#### Overall Signal")
    aag_cols = st.columns(len(scores))
    for col, (cat, rating) in zip(aag_cols, scores.items()):
        col.markdown(
            f'<div class="aag-box">'
            f'<div class="aag-icon">{SCORE_ICON.get(rating,"⚪")}</div>'
            f'<div class="aag-cat">{cat}</div>'
            f'<div class="aag-r">{rating.title()}</div>'
            f'</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tabs = st.tabs([
        "📊 Valuation", "💰 Profitability", "🏦 Financial Health",
        "📈 Growth", "💵 Dividends", "📉 Technicals",
        "🎯 Analyst View", "ℹ️ Company",
    ])

    with tabs[0]:
        _note("Is the stock cheap or expensive? These ratios compare the market price to what the company earns, owns, or sells. Analysts use them together — no single ratio is definitive.")
        for name, val_str, (rating, interp_txt) in [
            ("P/E Ratio (Trailing 12M)",    _fv(val_m.get("pe_ratio"),   ".1f","","x"), interp.pe_ratio(val_m.get("pe_ratio"))),
            ("Forward P/E (Next 12M est.)", _fv(val_m.get("forward_pe"), ".1f","","x"), interp.forward_pe(val_m.get("forward_pe"))),
            ("PEG Ratio",                   _fv(val_m.get("peg_ratio"),  ".2f"),          interp.peg_ratio(val_m.get("peg_ratio"))),
            ("Price / Book (P/B)",          _fv(val_m.get("pb_ratio"),   ".2f","","x"), interp.pb_ratio(val_m.get("pb_ratio"))),
            ("Price / Sales (P/S)",         _fv(val_m.get("ps_ratio"),   ".2f","","x"), interp.ps_ratio(val_m.get("ps_ratio"))),
            ("EV / EBITDA",                 _fv(val_m.get("ev_ebitda"),  ".1f","","x"), interp.ev_ebitda(val_m.get("ev_ebitda"))),
        ]:
            _render_metric(name, val_str, rating, interp_txt)

    with tabs[1]:
        _note("How efficiently does the company turn sales into profit? Profitable companies can fund growth internally, pay dividends, and survive downturns without diluting shareholders.")
        eps_t = prof_m.get("eps_ttm"); eps_f = prof_m.get("eps_forward")
        for name, val_str, (rating, interp_txt) in [
            ("Revenue (Trailing 12M)",   fmt_large(prof_m.get("revenue")),              ("neutral", f"Annual revenue of {fmt_large(prof_m.get('revenue'))} over the past 12 months — the top line before any costs.")),
            ("Gross Margin",             _fp(prof_m.get("gross_margin")),               interp.gross_margin(prof_m.get("gross_margin"))),
            ("Operating Margin",         _fp(prof_m.get("operating_margin")),           interp.operating_margin(prof_m.get("operating_margin"))),
            ("Net Profit Margin",        _fp(prof_m.get("net_margin")),                 interp.net_margin(prof_m.get("net_margin"))),
            ("Return on Equity (ROE)",   _fp(prof_m.get("roe")),                        interp.roe(prof_m.get("roe"))),
            ("Return on Assets (ROA)",   _fp(prof_m.get("roa")),                        interp.roa(prof_m.get("roa"))),
            ("EPS — Trailing 12M",       _fv(eps_t,".2f","$"),                          ("neutral", f"The company earned ${eps_t:.2f} per share over the past year." if eps_t else "Not available.")),
            ("EPS — Forward (est.)",     _fv(eps_f,".2f","$"),                          ("neutral", f"Analysts estimate ${eps_f:.2f} per share over the next 12 months." if eps_f else "Not available.")),
        ]:
            _render_metric(name, val_str, rating, interp_txt)

    with tabs[2]:
        _note("A strong balance sheet means the company can fund itself, weather recessions, and seize opportunities — without raising outside capital at the worst time.")
        de = health_m.get("debt_to_equity")
        de_n = de/100 if (de and abs(de)>10) else de
        fcf = health_m.get("free_cash_flow")
        qr  = health_m.get("quick_ratio")
        csh = health_m.get("cash_per_share")
        for name, val_str, (rating, interp_txt) in [
            ("Cash & Equivalents",   fmt_large(health_m.get("total_cash")),    ("good",    f"Holds {fmt_large(health_m.get('total_cash'))} in cash — available for acquisitions, buybacks, or as a buffer against downturns." if health_m.get("total_cash") else "Not available.")),
            ("Total Debt",           fmt_large(health_m.get("total_debt")),    ("neutral", f"Total debt: {fmt_large(health_m.get('total_debt'))}. Compare to cash and EBITDA to judge manageability." if health_m.get("total_debt") else "Not available.")),
            ("Debt / Equity",        _fv(de_n,".2f","","x"),                  interp.debt_to_equity(de)),
            ("Current Ratio",        _fv(health_m.get("current_ratio"),".2f","","x"), interp.current_ratio(health_m.get("current_ratio"))),
            ("Quick Ratio",          _fv(qr,".2f","","x"),                    ("good" if (qr or 0)>=1 else "caution", f"Quick ratio {_fv(qr,'.2f','','x')}: excludes inventory. {'Covers bills without inventory sales.' if (qr or 0)>=1 else 'Below 1.0x — relies on inventory to cover short-term obligations.'}" if qr else "Not available.")),
            ("Free Cash Flow",       fmt_large(fcf),                           ("good" if (fcf or 0)>0 else "caution" if fcf is not None else "neutral", f"FCF {fmt_large(fcf)}: real cash left after capex. {'Positive FCF = self-funding, can pay dividends and buy back shares.' if (fcf or 0)>0 else 'Negative FCF = relies on external financing.'}" if fcf is not None else "Not available.")),
            ("Cash per Share",       _fv(csh,".2f","$"),                      ("neutral", f"${csh:.2f} in cash backs each share you own." if csh else "Not available.")),
        ]:
            _render_metric(name, val_str, rating, interp_txt)

    with tabs[3]:
        _note("Stock prices ultimately follow earnings growth over time. A company growing faster than its peers is more likely to deliver strong long-term returns — but make sure you're not overpaying for that growth.")
        for name, val_str, (rating, interp_txt) in [
            ("Revenue Growth (YoY)",            _fp(growth_m.get("revenue_growth")),            interp.revenue_growth(growth_m.get("revenue_growth"))),
            ("Earnings Growth (YoY)",           _fp(growth_m.get("earnings_growth")),           interp.earnings_growth(growth_m.get("earnings_growth"))),
            ("Quarterly Earnings Growth (MRQ)", _fp(growth_m.get("earnings_quarterly_growth")), interp.earnings_growth(growth_m.get("earnings_quarterly_growth"))),
        ]:
            _render_metric(name, val_str, rating, interp_txt)

    with tabs[4]:
        _note("A dividend is cash the company pays you just for holding the stock. Not all great companies pay dividends, but dividend-paying stocks provide income and signal financial confidence.")
        ex_div = div_m.get("ex_dividend_date")
        try:
            from datetime import datetime
            ex_str = datetime.fromtimestamp(float(ex_div)).strftime("%B %d, %Y") if isinstance(ex_div,(int,float)) else str(ex_div) if ex_div else "N/A"
        except Exception:
            ex_str = str(ex_div) if ex_div else "N/A"
        fyr = div_m.get("five_yr_avg_yield")
        for name, val_str, (rating, interp_txt) in [
            ("Dividend Yield",       _fp(div_m.get("dividend_yield")),         interp.dividend_yield(div_m.get("dividend_yield"))),
            ("Annual Dividend/Share",_fv(div_m.get("annual_dividend"),".2f","$"), ("neutral", f"${div_m['annual_dividend']:.2f}/share/year." if div_m.get("annual_dividend") else "No dividend paid.")),
            ("Payout Ratio",         _fp(div_m.get("payout_ratio")),           interp.payout_ratio(div_m.get("payout_ratio"))),
            ("Ex-Dividend Date",     ex_str,                                   ("neutral", "Own shares BEFORE this date to receive the next dividend payment.")),
            ("5-Year Avg Yield",     _fv(fyr,".2f","","%"),                    ("neutral", f"Avg yield over 5 years: {fyr:.2f}%. Current vs history helps spot yield traps." if fyr else "Not available.")),
        ]:
            _render_metric(name, val_str, rating, interp_txt)

    with tabs[5]:
        _note("Technical indicators are based on price and volume, not fundamentals. Professionals use them for timing. For long-term investors, they give useful context on momentum and volatility.")
        cross = tech_m.get("cross_signal","—")
        cross_r = "good" if "Golden" in (cross or "") else ("caution" if "Death" in (cross or "") else "neutral")
        cross_note = (
            "Golden Cross (50-day MA above 200-day MA) — historically a bullish trend confirmation."
            if "Golden" in (cross or "") else
            "Death Cross (50-day MA below 200-day MA) — historically a bearish trend warning."
            if "Death" in (cross or "") else
            "Crossover signal not yet available."
        )
        p50  = tech_m.get("pct_above_50"); p200 = tech_m.get("pct_above_200")
        s50  = tech_m.get("sma_50");       s200 = tech_m.get("sma_200")
        vrat = tech_m.get("volume_vs_avg")
        vrat_note = (
            (f"Today's volume is {vrat:.2f}x the average. " +
            ("Above-average volume confirms conviction behind today's move." if (vrat or 1)>1.5
             else "Normal to below-average volume today."))
            if vrat else "Not available."
        )
        for name, val_str, (rating, interp_txt) in [
            ("RSI — 14 Day",           _fv(tech_m.get("rsi"),".1f"),         interp.rsi(tech_m.get("rsi"))),
            ("Beta (vs S&P 500)",      _fv(tech_m.get("beta"),".2f"),        interp.beta(tech_m.get("beta"))),
            ("50-Day Moving Average",  _fv(s50,".2f","$"),                   ("good" if (p50 or 0)>0 else "caution",
                f"{p50:+.1f}% {'above' if (p50 or 0)>0 else 'below'} 50-Day MA (${s50:.2f}). {'Short-term bullish signal.' if (p50 or 0)>0 else 'Short-term weakness.'}" if p50 is not None else "Not available.")),
            ("200-Day Moving Average", _fv(s200,".2f","$"),                  ("good" if (p200 or 0)>0 else "caution",
                f"{p200:+.1f}% {'above' if (p200 or 0)>0 else 'below'} 200-Day MA (${s200:.2f}). {'Above 200-day = key long-term bullish threshold.' if (p200 or 0)>0 else 'Below 200-day = long-term downtrend — institutional investors reduce exposure.'}" if p200 is not None else "Not available.")),
            ("MA Crossover Signal",    cross or "—",                         (cross_r, cross_note)),
            ("Volume vs 30-Day Avg",   _fv(vrat,".2f","","x"),               ("neutral", vrat_note)),
        ]:
            _render_metric(name, val_str, rating, interp_txt)

    with tabs[6]:
        _note("Wall Street analysts at firms like JPMorgan, Goldman Sachs, and Morgan Stanley publish Buy/Hold/Sell ratings with 12-month price targets. Deep expertise, but potential conflicts of interest — use as one input among many.")
        rec   = analyst_m.get("recommendation","N/A")
        up    = analyst_m.get("upside_potential")
        n_an  = analyst_m.get("num_analysts")
        tgt_m = analyst_m.get("target_mean"); tgt_h = analyst_m.get("target_high"); tgt_l = analyst_m.get("target_low")
        sb = analyst_m.get("strong_buy_count",0); b = analyst_m.get("buy_count",0)
        h  = analyst_m.get("hold_count",0);       s = analyst_m.get("sell_count",0); ss = analyst_m.get("strong_sell_count",0)

        col_l, col_r = st.columns([3, 2])
        with col_l:
            rec_r, rec_interp = interp.analyst_rating(rec, up, n_an)
            _render_metric("Consensus Rating",  rec.replace("_"," ").title() if rec!="N/A" else "N/A", rec_r, rec_interp)
            tgt_r = "good" if (up or 0)>10 else "fair" if (up or 0)>0 else "caution"
            _render_metric("Avg 12M Price Target", _fv(tgt_m,".2f","$"), tgt_r,
                f"Analyst consensus target ${tgt_m:.2f} — implying {up:+.1f}% from current price." if tgt_m and up is not None else "No target available.")
            if tgt_l and tgt_h:
                _render_metric("Target Range", f"${tgt_l:.2f} → ${tgt_h:.2f}", "neutral",
                    f"Bear case ${tgt_l:.2f} / Bull case ${tgt_h:.2f}. Wide spread = high uncertainty.")
        with col_r:
            total = (sb or 0)+(b or 0)+(h or 0)+(s or 0)+(ss or 0)
            if total > 0:
                fig2 = go.Figure(go.Pie(
                    labels=["Buy / Strong Buy","Hold","Sell / Underperform"],
                    values=[(sb or 0)+(b or 0), h or 0, (s or 0)+(ss or 0)],
                    hole=0.62, marker_colors=["#22c55e","#f59e0b","#ef4444"],
                    textinfo="label+percent", showlegend=False, textfont_size=11,
                ))
                fig2.update_layout(height=220, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor="white")
                st.plotly_chart(fig2, use_container_width=True)
                if n_an: st.caption(f"{n_an} analyst{'s' if n_an!=1 else ''} covering this stock")

    with tabs[7]:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Sector",    ov.get("sector","—"))
            st.metric("Country",   ov.get("country","—"))
        with c2:
            st.metric("Industry",  ov.get("industry","—"))
            st.metric("Exchange",  ov.get("exchange","—"))
        with c3:
            st.metric("Employees", f"{ov['employees']:,}" if ov.get("employees") else "—")
            if ov.get("website"):
                st.markdown(f"🌐 [{ov['website']}]({ov['website']})")
        st.markdown("#### Business Description")
        st.write(ov.get("description","No description available."))
        st.markdown("""<div class="disclaimer">
        <b>Disclaimer:</b> This analysis is for informational purposes only and does not constitute
        financial advice or a recommendation to buy or sell any security. Data sourced from public
        market feeds and may be delayed or inaccurate. Consult a licensed financial advisor before
        making any investment decisions.
        </div>""", unsafe_allow_html=True)


# ─── Sidebar ─────────────────────────────────────────────────────────────────

def _sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="padding:8px 0 16px">
          <div style="color:#c9a240;font-size:.65em;font-weight:700;letter-spacing:2.5px;text-transform:uppercase">
            Equity Research
          </div>
          <div style="color:white;font-size:1.15em;font-weight:800;margin-top:2px;line-height:1.2">
            Stock Analysis<br>Platform
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        mode = st.radio(
            "Mode",
            ["🔍  Deep Dive — Single Stock",
             "⚖️  Compare Stocks",
             "🏗️  Portfolio Builder"],
            label_visibility="collapsed",
        )

        st.markdown("---")

        tickers_out = []

        if "Deep Dive" in mode:
            t = st.text_input("Ticker Symbol", placeholder="e.g. AAPL",
                              key="single_ticker")
            tickers_out = [t]
            st.markdown(
                '<div style="font-size:.72em;color:#8899bb;margin-top:-8px">'
                'Enter a US exchange–listed stock ticker</div>',
                unsafe_allow_html=True)

        elif "Compare" in mode:
            st.markdown(
                '<div style="font-size:.78em;color:#8899bb;margin-bottom:8px">'
                'Add 2–3 tickers to compare side-by-side</div>',
                unsafe_allow_html=True)
            t1 = st.text_input("Ticker 1 ✳", placeholder="e.g. AAPL", key="c1")
            t2 = st.text_input("Ticker 2 ✳", placeholder="e.g. MSFT", key="c2")
            t3 = st.text_input("Ticker 3 (optional)", placeholder="e.g. GOOGL", key="c3")
            tickers_out = [t for t in [t1, t2, t3] if t.strip()]
            if len(tickers_out) < 2:
                st.markdown(
                    '<div style="border:1.5px dashed #1e3d6e;border-radius:8px;padding:10px;'
                    'text-align:center;font-size:.75em;color:#4a6fa5;margin-top:4px">'
                    '⬆ Enter at least 2 tickers<br>to enable comparison</div>',
                    unsafe_allow_html=True)

        else:  # Portfolio Builder
            st.markdown(
                '<div style="font-size:.78em;color:#8899bb;line-height:1.6">'
                'Enter up to 10 ETF tickers and configure your risk profile and '
                'rebalancing horizon in the main panel.</div>',
                unsafe_allow_html=True)
            st.markdown(
                '<div style="border:1.5px dashed #1e3d6e;border-radius:8px;padding:12px;'
                'text-align:center;font-size:.75em;color:#c9a240;margin-top:8px">'
                '🏗️ Portfolio Builder<br>'
                '<span style="color:#8899bb">Configure inputs in the main panel →</span>'
                '</div>',
                unsafe_allow_html=True)

        st.markdown("&nbsp;", unsafe_allow_html=True)
        btn_label = "▶  Analyze" if "Portfolio" not in mode else "▶  Open Builder"
        go_btn = st.button(btn_label, use_container_width=True, type="primary")

        st.markdown("---")
        st.markdown("""
        <div style="font-size:.68em;color:#4a6080;line-height:1.6">
        <b style="color:#8899bb">About this tool</b><br>
        Professional-grade metrics explained in plain English. Data via Yahoo Finance.
        Not financial advice.
        </div>""", unsafe_allow_html=True)

    return mode, tickers_out, go_btn


# ─── Portfolio Builder ───────────────────────────────────────────────────────

def render_portfolio_builder():
    import plotly.express as px

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="background:linear-gradient(135deg,#00194e 0%,#003087 100%);
                border-radius:12px;padding:22px 28px;color:white;margin-bottom:24px;">
      <div style="font-size:.65em;letter-spacing:2.5px;text-transform:uppercase;
                  color:#c9a240;font-weight:700;margin-bottom:6px;">
        PORTFOLIO CONSTRUCTION · MEAN-VARIANCE OPTIMISATION
      </div>
      <div style="font-size:1.5em;font-weight:800;">ETF Portfolio Builder</div>
      <div style="font-size:.85em;opacity:.8;margin-top:6px;">
        Enter up to 10 ETF tickers · select your risk profile and horizon ·
        receive an optimised allocation with expense-ratio-adjusted returns,
        Sharpe / Sortino / Drawdown analysis, and analyst-grade rationale.
      </div>
    </div>
    """, unsafe_allow_html=True)

    if not SCIPY_AVAILABLE:
        st.warning("SciPy not found — falling back to heuristic allocation. "
                   "Run `pip3 install scipy` for full MVO optimisation.")

    # ── Input form ────────────────────────────────────────────────────────────
    with st.form("pb_form"):

        # Step 1 — ETF tickers
        st.markdown('<div class="pb-step"><div class="pb-step-num">1</div>'
                    '<div class="pb-step-label">Select ETFs &nbsp;<span style="font-weight:400;'
                    'color:#64748b;font-size:.85em">(enter 2 – 10 ticker symbols)</span></div></div>',
                    unsafe_allow_html=True)

        cols5 = st.columns(5)
        ticker_fields = []
        defaults = ["SPY","QQQ","AGG","GLD","VNQ","SCHD","TLT","IEMG","VIG","XLE"]
        for i in range(10):
            with cols5[i % 5]:
                t = st.text_input(f"ETF {i+1}", value=defaults[i] if i < len(defaults) else "",
                                  key=f"pb_etf_{i}", label_visibility="visible")
                ticker_fields.append(t)

        st.markdown("<br>", unsafe_allow_html=True)

        # Step 2 — Risk profile
        st.markdown('<div class="pb-step"><div class="pb-step-num">2</div>'
                    '<div class="pb-step-label">Risk Profile</div></div>',
                    unsafe_allow_html=True)

        profile_cols = st.columns(3)
        profile_descs = {
            "Conservative": ("🛡️", "Capital Preservation",
                "Minimises volatility · max 25% per ETF · tightest vol cap"),
            "Moderate": ("⚖️", "Balanced Growth",
                "Maximises Sharpe ratio · max 38% per ETF · balanced vol target"),
            "Aggressive": ("🚀", "Maximum Growth",
                "Maximises net return · max 55% per ETF · highest vol tolerance"),
        }
        for col, (prof, (icon, title, desc)) in zip(profile_cols, profile_descs.items()):
            with col:
                st.markdown(f"""
                <div style="background:white;border:1.5px solid #dde3ed;border-radius:10px;
                            padding:14px 16px;margin-bottom:8px;">
                  <div style="font-size:1.5em">{icon}</div>
                  <div style="font-weight:800;color:#00194e;font-size:.92em;margin:4px 0">{title}</div>
                  <div style="font-size:.73em;color:#64748b;line-height:1.5">{desc}</div>
                </div>""", unsafe_allow_html=True)

        risk_profile = st.radio("Risk Profile", list(profile_descs.keys()),
                                horizontal=True, label_visibility="collapsed",
                                key="pb_risk")

        st.markdown("<br>", unsafe_allow_html=True)

        # Step 3 — Time horizon
        st.markdown('<div class="pb-step"><div class="pb-step-num">3</div>'
                    '<div class="pb-step-label">Rebalancing Horizon</div></div>',
                    unsafe_allow_html=True)

        horizon_info = {
            "Quarterly":   "3-month hold · tightest vol cap · uses 2-year history",
            "Half-Yearly": "6-month hold · balanced vol cap · uses 3-year history",
            "Annual":      "12-month hold · widest vol cap · uses 5-year history",
        }
        for col, (h, desc) in zip(st.columns(3), horizon_info.items()):
            with col:
                st.markdown(f"""
                <div style="background:#f8fafc;border:1.5px solid #dde3ed;border-radius:8px;
                            padding:10px 14px;font-size:.8em;color:#475569;margin-bottom:6px;">
                  <b style="color:#00194e">{h}</b><br>{desc}
                </div>""", unsafe_allow_html=True)

        time_horizon = st.radio("Time Horizon", list(horizon_info.keys()),
                                horizontal=True, label_visibility="collapsed",
                                key="pb_horizon")

        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("▶  Build Optimal Portfolio",
                                          type="primary", use_container_width=True)

    if not submitted:
        return

    # ── Run optimisation ──────────────────────────────────────────────────────
    raw_tickers = [t.strip().upper() for t in ticker_fields if t.strip()]
    if len(raw_tickers) < 2:
        st.error("Enter at least 2 ETF tickers to build a portfolio.")
        return

    optimizer = ETFPortfolioOptimizer(raw_tickers, risk_profile, time_horizon)

    prog = st.progress(0, text="Initialising…")
    def _cb(ticker, idx, total):
        prog.progress((idx + 1) / total, text=f"Loading {ticker} ({idx+1}/{total})…")

    with st.spinner("Fetching ETF data and running optimisation…"):
        loaded = optimizer.load(progress_cb=_cb)
        prog.empty()

    if len(loaded) < 2:
        st.error("Could not load enough ETF data. Check your ticker symbols and try again.")
        return

    skipped = [t for t in raw_tickers if t not in loaded]
    if skipped:
        st.warning(f"Could not load data for: {', '.join(skipped)}. Proceeding with the rest.")

    metrics      = optimizer.compute_metrics()
    weights, pm  = optimizer.optimize(metrics)

    if not weights:
        st.error("Optimisation failed. Try different tickers or a different risk profile.")
        return

    frontier_df  = optimizer.simulate_frontier(n_sims=4000)

    # Sort by allocation descending
    sorted_tickers = sorted(weights.keys(), key=lambda t: weights[t], reverse=True)

    # ── Results header ────────────────────────────────────────────────────────
    cfg_col = PROFILE_CFG[risk_profile]["color"]
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:12px;margin:8px 0 20px">
      <div style="font-size:1.3em;font-weight:800;color:#00194e">
        Optimised Portfolio · {risk_profile} · {time_horizon}
      </div>
      <span class="optimizer-badge">{pm.get('optimizer','—')}</span>
    </div>""", unsafe_allow_html=True)

    # ── Portfolio metric cards ─────────────────────────────────────────────────
    def _pmc(label, value, sublabel="", color="#00194e"):
        return (f'<div class="port-metric-card">'
                f'<div class="pmc-label">{label}</div>'
                f'<div class="pmc-value" style="color:{color}">{value}</div>'
                f'<div class="pmc-sublabel">{sublabel}</div>'
                f'</div>')

    mc1, mc2, mc3, mc4, mc5, mc6 = st.columns(6)
    metric_pairs = [
        (mc1, "Expected Net Return", f"{pm['expected_return']*100:+.1f}%",
         "Annual, after fees", "#065f46" if pm["expected_return"] > 0 else "#991b1b"),
        (mc2, "Portfolio Volatility",  f"{pm['volatility']*100:.1f}%",
         f"Annualised std dev", "#1a56db"),
        (mc3, "Sharpe Ratio",          f"{pm['sharpe']:.2f}",
         "Return / risk (>1 = good)", "#003087"),
        (mc4, "Sortino Ratio",         f"{pm['sortino']:.2f}",
         "Downside-adj. return", "#003087"),
        (mc5, "Max Drawdown",          f"{pm['max_drawdown']*100:.1f}%",
         "Portfolio peak-to-trough", "#991b1b"),
        (mc6, "Wtd Expense Ratio",     f"{pm['weighted_expense_ratio']*100:.3f}%",
         "Annual fee drag", "#854d0e"),
    ]
    for col, label, val, sub, clr in metric_pairs:
        with col:
            st.markdown(_pmc(label, val, sub, clr), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Allocation donut + frontier ────────────────────────────────────────────
    col_donut, col_front = st.columns([1, 1])

    with col_donut:
        st.markdown("#### Allocation Breakdown")
        labels = [f"{t}<br>{weights[t]*100:.1f}%" for t in sorted_tickers]
        values = [weights[t] for t in sorted_tickers]
        colors = [ALLOC_COLORS[i % len(ALLOC_COLORS)] for i in range(len(sorted_tickers))]

        fig_donut = go.Figure(go.Pie(
            labels=[t for t in sorted_tickers],
            values=values,
            hole=0.55,
            marker=dict(colors=colors, line=dict(color="white", width=2)),
            textinfo="label+percent",
            textfont_size=11,
            hovertemplate="<b>%{label}</b><br>Allocation: %{percent}<extra></extra>",
        ))
        fig_donut.update_layout(
            height=380, margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor="white",
            legend=dict(orientation="v", x=1.02, y=0.5, font_size=11),
            annotations=[dict(
                text=f"<b>{len(sorted_tickers)}</b><br>ETFs",
                x=0.5, y=0.5, font_size=14, showarrow=False,
                font_color="#00194e",
            )],
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with col_front:
        st.markdown("#### Efficient Frontier")
        if not frontier_df.empty:
            port_ret = pm["expected_return"]
            port_vol = pm["volatility"]

            fig_ef = go.Figure()

            # Random portfolio cloud
            fig_ef.add_trace(go.Scatter(
                x=frontier_df["volatility"] * 100,
                y=frontier_df["return"]     * 100,
                mode="markers",
                marker=dict(
                    size=3.5, opacity=0.45,
                    color=frontier_df["sharpe"],
                    colorscale="Blues",
                    showscale=True,
                    colorbar=dict(title="Sharpe", thickness=10, len=0.6, x=1.02),
                ),
                name="Random Portfolios",
                hovertemplate="Vol: %{x:.1f}%<br>Ret: %{y:.1f}%<extra></extra>",
            ))

            # Individual ETF points
            for t in sorted_tickers:
                m = metrics[t]
                fig_ef.add_trace(go.Scatter(
                    x=[m["ann_vol"] * 100], y=[m["net_return"] * 100],
                    mode="markers+text",
                    marker=dict(size=9, color="#1a56db",
                                line=dict(color="white", width=1.5)),
                    text=[t], textposition="top center",
                    textfont=dict(size=9, color="#00194e"),
                    name=t,
                    showlegend=False,
                    hovertemplate=f"<b>{t}</b><br>Vol: %{{x:.1f}}%<br>Net Ret: %{{y:.1f}}%<extra></extra>",
                ))

            # Recommended portfolio star
            fig_ef.add_trace(go.Scatter(
                x=[port_vol * 100], y=[port_ret * 100],
                mode="markers+text",
                marker=dict(size=18, symbol="star", color="#c9a240",
                            line=dict(color="white", width=1.5)),
                text=["▶ Optimal"], textposition="top right",
                textfont=dict(size=10, color="#c9a240", family="Inter"),
                name="Optimal Portfolio",
                hovertemplate=(f"<b>Optimal Portfolio</b><br>"
                               f"Vol: {port_vol*100:.1f}%<br>"
                               f"Net Return: {port_ret*100:.1f}%<br>"
                               f"Sharpe: {pm['sharpe']:.2f}<extra></extra>"),
            ))

            fig_ef.update_layout(
                height=380, margin=dict(l=0, r=0, t=10, b=0),
                paper_bgcolor="white", plot_bgcolor="#fafafa",
                xaxis_title="Annualised Volatility (%)",
                yaxis_title="Expected Net Return (%)",
                font=dict(family="Inter,sans-serif", size=11),
                hovermode="closest",
                legend=dict(orientation="h", y=-0.15, font_size=10),
            )
            fig_ef.update_xaxes(gridcolor="#e2e8f0")
            fig_ef.update_yaxes(gridcolor="#e2e8f0")
            st.plotly_chart(fig_ef, use_container_width=True)

    # ── Allocation + risk metrics table ───────────────────────────────────────
    st.markdown("#### Full Risk & Return Breakdown")
    st.markdown('<div style="background:white;border-radius:10px;overflow:hidden;'
                'box-shadow:0 2px 10px rgba(0,25,78,.08);">',
                unsafe_allow_html=True)

    def _color_val(v, good_hi=True, neutral_zero=False):
        """Return a colour for a numeric metric cell."""
        if v is None:
            return "#64748b"
        if neutral_zero and abs(v) < 0.01:
            return "#64748b"
        return "#065f46" if (v > 0) == good_hi else "#991b1b"

    rows_html = ""
    for i, t in enumerate(sorted_tickers):
        m   = metrics[t]
        w   = weights[t]
        pct = w * 100
        bar_color = ALLOC_COLORS[i % len(ALLOC_COLORS)]
        alloc_bar = (f'<div class="at-bar-wrap">'
                     f'<div class="at-bar-fill" style="width:{min(pct,100):.1f}%;'
                     f'background:{bar_color}"></div></div>')

        def _fc(v, spec=".2f", suffix="", good_hi=True, pct_mult=1):
            if v is None: return '<span style="color:#94a3b8">—</span>'
            val = v * pct_mult
            clr = _color_val(v, good_hi)
            return f'<span style="color:{clr};font-weight:700">{val:{spec}}{suffix}</span>'

        rows_html += f"""
        <tr>
          <td style="font-weight:700;color:#003087;font-variant-numeric:tabular-nums;white-space:nowrap">
            {t}
          </td>
          <td style="color:#1e293b;max-width:160px;overflow:hidden;text-overflow:ellipsis;
                     white-space:nowrap;font-size:.8em">{m['name'][:32]}</td>
          <td style="color:#64748b;font-size:.77em">{m['category'][:20]}</td>
          <td>
            <span style="font-family:'SF Mono',monospace;font-weight:800;color:{bar_color}">
              {pct:.1f}%
            </span>
            {alloc_bar}
          </td>
          <td class="nv">{_fc(m['net_return'],   '.1f', '%', True,  100)}</td>
          <td class="nv">{_fc(m['ann_vol'],      '.1f', '%', False, 100)}</td>
          <td class="nv">{_fc(m['sharpe'],       '.2f', '',  True)}</td>
          <td class="nv">{_fc(m['sortino'],      '.2f', '',  True)}</td>
          <td class="nv">{_fc(m['max_drawdown'], '.1f', '%', False, 100)}</td>
          <td class="nv">{_fc(m['calmar'],       '.2f', '',  True)}</td>
          <td class="nv">{_fc(m['expense_ratio'],'.3f', '%', False, 100)}</td>
          <td class="nv">{_fc(m['beta'],         '.2f', '',  neutral=True) if False else
                          (f'<span style="font-family:monospace;font-weight:700">{m["beta"]:.2f}</span>'
                           if m["beta"] else "—")}</td>
          <td class="nv" style="color:#64748b">{
            fmt_large(m['aum']) if m.get('aum') else '—'}</td>
        </tr>"""

    table_html = f"""
    <table class="alloc-table">
      <thead>
        <tr>
          <th>Ticker</th>
          <th>Name</th>
          <th>Category</th>
          <th>Allocation</th>
          <th class="num">Net Return</th>
          <th class="num">Volatility</th>
          <th class="num">Sharpe</th>
          <th class="num">Sortino</th>
          <th class="num">Max DD</th>
          <th class="num">Calmar</th>
          <th class="num">Exp Ratio</th>
          <th class="num">Beta</th>
          <th class="num">AUM</th>
        </tr>
      </thead>
      <tbody>{rows_html}</tbody>
    </table>"""
    st.markdown(table_html, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Additional metric charts ───────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    col_bar1, col_bar2 = st.columns(2)

    with col_bar1:
        st.markdown("##### Sharpe vs Sortino by ETF")
        bar_tickers = sorted_tickers
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            name="Sharpe", x=bar_tickers,
            y=[metrics[t]["sharpe"] for t in bar_tickers],
            marker_color="#003087", opacity=0.85,
        ))
        fig_bar.add_trace(go.Bar(
            name="Sortino", x=bar_tickers,
            y=[metrics[t]["sortino"] for t in bar_tickers],
            marker_color="#c9a240", opacity=0.85,
        ))
        fig_bar.add_hline(y=1.0, line_dash="dot", line_color="#64748b",
                          annotation_text="Target = 1.0", annotation_font_size=10)
        fig_bar.update_layout(
            height=280, barmode="group", margin=dict(l=0,r=0,t=10,b=0),
            paper_bgcolor="white", plot_bgcolor="#fafafa",
            legend=dict(orientation="h", y=1.1),
            font=dict(family="Inter,sans-serif", size=10),
        )
        fig_bar.update_yaxes(gridcolor="#e2e8f0")
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_bar2:
        st.markdown("##### Expense Ratio vs Max Drawdown")
        fig_scat = go.Figure()
        for i, t in enumerate(sorted_tickers):
            m = metrics[t]
            clr = ALLOC_COLORS[i % len(ALLOC_COLORS)]
            fig_scat.add_trace(go.Scatter(
                x=[m["expense_ratio"] * 100],
                y=[abs(m["max_drawdown"]) * 100],
                mode="markers+text",
                marker=dict(size=max(8, weights[t] * 120), color=clr,
                            line=dict(color="white", width=1.5), opacity=0.85),
                text=[t], textposition="top center",
                textfont=dict(size=9),
                name=t, showlegend=False,
                hovertemplate=f"<b>{t}</b><br>Exp Ratio: {m['expense_ratio']*100:.3f}%<br>Max DD: {abs(m['max_drawdown'])*100:.1f}%<extra></extra>",
            ))
        fig_scat.update_layout(
            height=280, margin=dict(l=0,r=0,t=10,b=0),
            paper_bgcolor="white", plot_bgcolor="#fafafa",
            xaxis_title="Expense Ratio (%)", yaxis_title="Max Drawdown (%)",
            font=dict(family="Inter,sans-serif", size=10),
        )
        fig_scat.update_xaxes(gridcolor="#e2e8f0")
        fig_scat.update_yaxes(gridcolor="#e2e8f0")
        st.markdown('<div style="font-size:.72em;color:#94a3b8;margin-bottom:4px">'
                    'Bubble size ∝ portfolio allocation weight</div>', unsafe_allow_html=True)
        st.plotly_chart(fig_scat, use_container_width=True)

    # ── Per-ETF rationale cards ────────────────────────────────────────────────
    st.markdown("#### Allocation Rationale")
    st.markdown(
        '<div style="font-size:.8em;color:#64748b;margin-bottom:14px">'
        'Analyst-grade explanation of why each ETF received its weight, '
        'factoring in Sharpe ratio, expense ratio, volatility, drawdown, and Sortino.</div>',
        unsafe_allow_html=True)

    rat_cols = st.columns(2)
    for i, t in enumerate(sorted_tickers):
        rationale = optimizer.generate_rationale(t, weights[t], metrics, pm)
        m         = metrics[t]
        bar_color = ALLOC_COLORS[i % len(ALLOC_COLORS)]
        pct       = weights[t] * 100
        with rat_cols[i % 2]:
            st.markdown(f"""
            <div class="rationale-card" style="margin-bottom:12px;
                         border-left-color:{bar_color}">
              <div class="rat-header">
                <div>
                  <div class="rat-ticker">{t} · {m['category'][:22]}</div>
                  <div class="rat-name">{m['name'][:40]}</div>
                </div>
                <div class="rat-alloc" style="color:{bar_color}">{pct:.1f}%</div>
              </div>
              <div class="rat-body">{rationale}</div>
              <div style="display:flex;gap:14px;margin-top:10px;flex-wrap:wrap">
                <span style="font-size:.72em;color:#64748b">
                  Sharpe <b style="color:#00194e">{m['sharpe']:.2f}</b>
                </span>
                <span style="font-size:.72em;color:#64748b">
                  Sortino <b style="color:#00194e">{m['sortino']:.2f}</b>
                </span>
                <span style="font-size:.72em;color:#64748b">
                  Max DD <b style="color:#991b1b">{m['max_drawdown']*100:.1f}%</b>
                </span>
                <span style="font-size:.72em;color:#64748b">
                  Exp Ratio <b style="color:#854d0e">{m['expense_ratio']*100:.3f}%</b>
                </span>
                <span style="font-size:.72em;color:#64748b">
                  Beta <b style="color:#00194e">{m['beta']:.2f}</b>
                </span>
              </div>
            </div>""", unsafe_allow_html=True)

    # ── Portfolio-level secondary stats ───────────────────────────────────────
    st.markdown("#### Portfolio Summary Statistics")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Weighted Beta",       f"{pm['weighted_beta']:.2f}",
              help="Sensitivity to overall market moves")
    s2.metric("Weighted Div Yield",  f"{pm['weighted_yield']*100:.2f}%",
              help="Income generated by the portfolio")
    s3.metric("Calmar Ratio",        f"{pm['calmar']:.2f}",
              help="Annual return / Max drawdown (higher = better)")
    s4.metric("No. of ETFs",         str(pm.get("n_etfs", len(sorted_tickers))),
              help="ETFs with non-zero allocation")

    st.markdown("""
    <div class="disclaimer">
    <b>Disclaimer:</b> Portfolio optimisation is based on historical return and risk data sourced from
    public market feeds, which may be delayed or incomplete. Past performance is not indicative of
    future results. Mean-Variance Optimisation is sensitive to input assumptions and historical look-back
    period — results should be treated as a starting point for analysis, not a definitive recommendation.
    Expense ratios sourced from fund filings may not reflect the most current values.
    This tool does not constitute financial advice. Always consult a licensed financial advisor or
    registered investment professional before making portfolio allocation decisions.
    </div>""", unsafe_allow_html=True)


# ─── Entry point ─────────────────────────────────────────────────────────────

def main():
    mode, tickers, go_btn = _sidebar()

    # Portfolio Builder is self-contained (own form + button inside)
    if "Portfolio" in mode:
        render_portfolio_builder()
        return

    if not go_btn or not any(t.strip() for t in tickers):
        st.markdown("""
        <div style="text-align:center;padding:60px 20px 30px">
          <div style="font-size:3em;margin-bottom:16px">📊</div>
          <div style="font-size:1.6em;font-weight:800;color:#00194e">Equity Research Platform</div>
          <div style="font-size:1.0em;color:#64748b;margin-top:8px">
            Professional-grade analysis · Plain-English interpretations
          </div>
          <div style="margin-top:24px;display:flex;gap:16px;justify-content:center;flex-wrap:wrap">
        """, unsafe_allow_html=True)

        cols = st.columns(3)
        for col, (icon, title, desc) in zip(cols, [
            ("📊", "Valuation", "P/E, PEG, P/B, P/S, EV/EBITDA"),
            ("💰", "Profitability", "Margins, ROE, ROA, EPS growth"),
            ("🏦", "Balance Sheet", "Debt, liquidity, free cash flow"),
        ]):
            col.markdown(f"""
            <div style="background:white;border-radius:10px;padding:20px;text-align:center;
                        box-shadow:0 2px 8px rgba(0,25,78,.08)">
              <div style="font-size:2em">{icon}</div>
              <div style="font-weight:700;color:#00194e;margin:6px 0">{title}</div>
              <div style="font-size:.8em;color:#64748b">{desc}</div>
            </div>""", unsafe_allow_html=True)

        cols2 = st.columns(3)
        for col, (icon, title, desc) in zip(cols2, [
            ("📈", "Growth", "Revenue & earnings growth YoY"),
            ("📉", "Technicals", "RSI, Beta, Moving Averages"),
            ("⚖️", "Comparison", "Side-by-side multi-stock analysis"),
        ]):
            col.markdown(f"""
            <div style="background:white;border-radius:10px;padding:20px;text-align:center;
                        box-shadow:0 2px 8px rgba(0,25,78,.08)">
              <div style="font-size:2em">{icon}</div>
              <div style="font-weight:700;color:#00194e;margin:6px 0">{title}</div>
              <div style="font-size:.8em;color:#64748b">{desc}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("""
        <div style="margin-top:32px;font-size:.8em;color:#94a3b8;text-align:center">
          ← Enter a ticker in the sidebar and click <b>Analyze</b> to get started
        </div>""", unsafe_allow_html=True)
        return

    if "Deep Dive" in mode:
        render_single(tickers[0])
    elif "Compare" in mode:
        render_comparison(tickers)


if __name__ == "__main__":
    main()
