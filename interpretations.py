"""
interpretations.py — Plain-English interpretations of financial metrics.

Each function returns a tuple: (rating, interpretation_text)
  rating: one of 'strong' | 'good' | 'fair' | 'caution' | 'weak' | 'neutral'
"""

import math


def _safe(v):
    if v is None:
        return None
    try:
        if math.isnan(float(v)):
            return None
    except (TypeError, ValueError):
        pass
    return v


# ─── Valuation ────────────────────────────────────────────────────────────────

def pe_ratio(pe):
    pe = _safe(pe)
    if pe is None:
        return "neutral", (
            "P/E ratio is not available — often because the company is currently unprofitable. "
            "Without earnings, we can't measure how 'expensive' the stock is on this metric alone."
        )
    if pe < 0:
        return "caution", (
            f"A negative P/E ({pe:.1f}x) means the company is losing money right now — spending more than it earns. "
            "Think of a startup that's burning cash to capture market share. Not automatically bad, "
            "but investors are essentially betting on future profitability."
        )
    if pe < 8:
        return "caution", (
            f"At {pe:.1f}x earnings, the stock looks very cheap — you'd pay just ${pe:.0f} for every $1 of annual profit. "
            "But 'cheap' can be a trap. Ask yourself: why is the market this pessimistic? "
            "Potential reasons include declining business, legal risk, or industry disruption."
        )
    if pe < 16:
        return "good", (
            f"A P/E of {pe:.1f}x is in value territory — you're paying ${pe:.0f} for every $1 of annual profit. "
            "This is below the historical S&P 500 average (~18-20x), suggesting solid value. "
            "Value investors like Warren Buffett often seek stocks in this range."
        )
    if pe < 22:
        return "fair", (
            f"At {pe:.1f}x earnings, this stock is priced near the historical market average (~18-20x). "
            f"You're paying ${pe:.0f} per $1 of profit — neither a bargain nor expensive. "
            "A fair price for a quality business."
        )
    if pe < 32:
        return "fair", (
            f"A P/E of {pe:.1f}x is above average. The market is paying a premium (${pe:.0f} per $1 earned) "
            "expecting meaningful growth ahead. If that growth materialises, the price is justified. "
            "If earnings disappoint, the stock could fall sharply."
        )
    if pe < 60:
        return "caution", (
            f"At {pe:.1f}x earnings, this is a 'growth premium' valuation — you're paying a lot up front "
            "for expected future profits. Common in high-growth tech or biotech. "
            "Higher potential return, but significantly higher risk if growth slows."
        )
    return "weak", (
        f"A P/E of {pe:.0f}x is very elevated — you're paying ${pe:.0f} for every $1 of current earnings. "
        "The company must execute near-perfectly for years to justify this. "
        "Any earnings miss or slowdown can trigger a sharp drop."
    )


def forward_pe(fpe):
    fpe = _safe(fpe)
    if fpe is None:
        return "neutral", (
            "Forward P/E is unavailable — no analyst earnings estimates exist for this stock. "
            "It's based on projected profits, so it gives a sense of how 'expensive' the stock is "
            "relative to where earnings are headed."
        )
    if fpe < 0:
        return "caution", (
            "Analysts expect the company to keep losing money over the next 12 months. "
            "Not a dealbreaker if the company has enough cash runway, but factor in the burn rate."
        )
    if fpe < 15:
        return "good", (
            f"Forward P/E of {fpe:.1f}x: if analysts are right, you're paying just ${fpe:.0f} per $1 of next year's earnings — "
            "attractive relative to expected profits. But analyst estimates can be wrong by 20-30%, "
            "so treat this as a directional signal, not a precise number."
        )
    if fpe < 25:
        return "fair", (
            f"A forward P/E of {fpe:.1f}x is in the normal to slightly elevated range. "
            "The market expects solid earnings growth. A reasonable valuation if the company delivers."
        )
    if fpe < 45:
        return "caution", (
            f"At {fpe:.1f}x forward earnings, investors are pricing in strong growth expectations. "
            "This valuation is very sensitive to earnings surprises — a miss could hurt the stock disproportionately."
        )
    return "weak", (
        f"A forward P/E of {fpe:.1f}x is stretched — everything needs to go right. "
        "High-risk, potentially high-reward."
    )


def peg_ratio(peg):
    peg = _safe(peg)
    if peg is None:
        return "neutral", (
            "PEG ratio is unavailable (usually because growth estimates aren't available). "
            "PEG adjusts the P/E for the company's growth rate — a P/E of 30 with 30% growth (PEG = 1.0) "
            "is very different from a P/E of 30 with 5% growth (PEG = 6.0)."
        )
    if peg < 0:
        return "neutral", "Negative PEG usually means negative earnings or negative growth expectations — not meaningful."
    if peg < 0.8:
        return "strong", (
            f"A PEG of {peg:.2f} suggests the stock may be undervalued relative to its growth. "
            "Legendary investor Peter Lynch said anything below 1.0 is potentially attractive. "
            "Below 0.8 is a strong value signal — you're getting growth at a discount."
        )
    if peg < 1.2:
        return "good", (
            f"A PEG of {peg:.2f} is close to 1.0 — the 'sweet spot' where you're paying roughly in line "
            "with the company's growth rate. Neither cheap nor expensive on this measure."
        )
    if peg < 2.0:
        return "fair", (
            f"A PEG of {peg:.2f} means you're paying a modest premium over the growth rate. "
            "The market believes this company has durable advantages — brand, margins, or market dominance — "
            "that justify a higher price."
        )
    return "caution", (
        f"A PEG of {peg:.2f} is elevated — you're paying significantly more than the growth rate warrants. "
        "You'd need very strong confidence in sustained above-average growth to be comfortable here."
    )


def pb_ratio(pb):
    pb = _safe(pb)
    if pb is None:
        return "neutral", "Price-to-Book isn't available."
    if pb < 0:
        return "caution", (
            "Negative P/B means the company has more liabilities than assets on its books (negative equity). "
            "This is a red flag for asset-heavy businesses, though it can occur after massive buybacks "
            "or large one-time losses (e.g., McDonald's has negative book value)."
        )
    if pb < 1.0:
        return "strong", (
            f"At {pb:.2f}x book value, the stock trades below the accounting value of the company's assets. "
            "In theory, if the company liquidated tomorrow, you'd get back more than you paid. "
            "Deep value investors target stocks below 1.0x book."
        )
    if pb < 3.0:
        return "good", (
            f"At {pb:.2f}x book value, you're paying a modest premium over accounting asset value — "
            "typical for solid, profitable companies with decent return on equity."
        )
    if pb < 8.0:
        return "fair", (
            f"A P/B of {pb:.2f}x is elevated, meaning the market values the company's brand, "
            "intellectual property, or earnings power well above physical assets. "
            "Common in tech, pharma, and consumer staples."
        )
    if pb < 20:
        return "caution", (
            f"At {pb:.1f}x book value, the stock is priced far above tangible assets. "
            "Normal for asset-light businesses (software, services), but the stock price depends almost "
            "entirely on future profitability expectations."
        )
    return "weak", (
        f"A P/B of {pb:.0f}x is very high — the stock price is almost entirely driven by intangibles "
        "and expected future profits, not current assets. High risk if the business outlook changes."
    )


def ps_ratio(ps):
    ps = _safe(ps)
    if ps is None:
        return "neutral", "Price-to-Sales isn't available."
    if ps < 1.0:
        return "strong", (
            f"At {ps:.2f}x sales, you're paying less than $1 for every $1 of revenue — historically 'deep value' territory. "
            "Ensure revenue is actually growing and margins aren't collapsing before concluding it's cheap."
        )
    if ps < 3.0:
        return "good", (
            f"A P/S of {ps:.2f}x is moderate — ${ps:.2f} for every $1 of revenue. "
            "Reasonable for established, profitable companies in most sectors."
        )
    if ps < 8.0:
        return "fair", (
            f"At {ps:.2f}x sales, the market is pricing in strong growth or exceptional future margins. "
            "Common in high-growth tech. The question is: when will revenue translate into profit?"
        )
    if ps < 20:
        return "caution", (
            f"A P/S of {ps:.1f}x is high. The company needs to grow substantially and dramatically improve "
            "margins to justify this — typical only for very early-stage or hypergrowth companies."
        )
    return "weak", (
        f"At {ps:.0f}x revenue, the valuation is very stretched. Even exceptional growth over many years "
        "may not be enough to justify this. Requires near-flawless execution."
    )


def ev_ebitda(ev_eb):
    ev_eb = _safe(ev_eb)
    if ev_eb is None:
        return "neutral", (
            "EV/EBITDA isn't available. This is a favorite of M&A bankers and private equity — "
            "it compares the total company value (price + debt - cash) to cash operating profits, "
            "making it useful for comparing companies across different capital structures."
        )
    if ev_eb < 0:
        return "neutral", "Negative EV/EBITDA typically means negative EBITDA (operating losses)."
    if ev_eb < 8:
        return "strong", (
            f"EV/EBITDA of {ev_eb:.1f}x is low — potentially attractively priced relative to cash operating profits. "
            "Private equity buyers often target companies in the 5-8x range. "
            f"The S&P 500 average is typically 12-15x, so {ev_eb:.1f}x looks inexpensive."
        )
    if ev_eb < 14:
        return "good", (
            f"An EV/EBITDA of {ev_eb:.1f}x is in the 'normal' range for most established companies. "
            f"If you bought the entire business (including debt), it would take ~{ev_eb:.0f} years of current "
            "cash operating profits to recoup the purchase price."
        )
    if ev_eb < 22:
        return "fair", (
            f"At {ev_eb:.1f}x EBITDA, the company trades at a premium to the market average. "
            "Typical for companies with strong competitive moats or above-average growth."
        )
    if ev_eb < 40:
        return "caution", (
            f"EV/EBITDA of {ev_eb:.1f}x is elevated — the market expects significant EBITDA growth. "
            "Risk: if growth slows, this multiple can compress sharply."
        )
    return "weak", (
        f"An EV/EBITDA of {ev_eb:.0f}x is very high, implying exceptional growth expectations. "
        "Usually reserved for early-stage companies with low current profits but large future potential."
    )


# ─── Profitability ────────────────────────────────────────────────────────────

def gross_margin(gm):
    gm = _safe(gm)
    if gm is None:
        return "neutral", "Gross margin isn't available."
    pct = gm * 100
    if pct > 70:
        return "strong", (
            f"A gross margin of {pct:.1f}% is exceptional. For every $100 in revenue, the company keeps "
            f"${pct:.0f} after paying direct production costs. This level is typical of software, pharma, "
            "and luxury brands — businesses with strong pricing power and low per-unit costs."
        )
    if pct > 50:
        return "good", (
            f"At {pct:.1f}% gross margin, the company keeps a solid chunk of each revenue dollar before "
            "operating expenses. This suggests decent pricing power or efficient production."
        )
    if pct > 30:
        return "fair", (
            f"A {pct:.1f}% gross margin is moderate — typical for many manufacturing, retail, and services companies. "
            "Profitability depends heavily on how well the company controls operating expenses below this line."
        )
    if pct > 15:
        return "caution", (
            f"At {pct:.1f}% gross margin, the company operates with thin margins. "
            "Common in grocery retail, distribution, or commodity businesses. "
            "Small revenue drops can quickly create big profit problems."
        )
    return "weak", (
        f"A gross margin of {pct:.1f}% is very thin — the company keeps little of each dollar earned "
        "after direct costs. Highly vulnerable to any cost increases or pricing pressure."
    )


def operating_margin(om):
    om = _safe(om)
    if om is None:
        return "neutral", "Operating margin isn't available."
    pct = om * 100
    if pct > 25:
        return "strong", (
            f"An operating margin of {pct:.1f}% is excellent. For every $100 in sales, "
            f"the company earns ${pct:.0f} in operating profit — before interest and taxes. "
            "This signals strong pricing power and disciplined cost management."
        )
    if pct > 15:
        return "good", (
            f"At {pct:.1f}% operating margin, this company is solidly profitable at the core business level. "
            "This kind of steady profitability attracts long-term institutional investors."
        )
    if pct > 8:
        return "fair", (
            f"An operating margin of {pct:.1f}% is acceptable for many industries. "
            "The business is profitable, though there may be room to improve efficiency or pricing."
        )
    if pct > 0:
        return "caution", (
            f"At {pct:.1f}% operating margin, the company barely breaks even at the operating level. "
            "A small revenue decline or cost increase could quickly turn this negative."
        )
    return "weak", (
        f"A negative operating margin ({pct:.1f}%) means the company loses money from its core operations. "
        "Acceptable for early-stage companies investing heavily in growth, but unsustainable long-term."
    )


def net_margin(nm):
    nm = _safe(nm)
    if nm is None:
        return "neutral", "Net profit margin isn't available."
    pct = nm * 100
    if pct > 20:
        return "strong", (
            f"A net margin of {pct:.1f}% is outstanding — the company keeps {pct:.0f} cents of every revenue dollar "
            "as pure profit after all costs, taxes, and interest. Very few companies sustain margins this high."
        )
    if pct > 10:
        return "good", (
            f"At {pct:.1f}% net margin, this company is meaningfully profitable. "
            "The S&P 500 average is roughly 10-12%, so this is solidly average to above-average — "
            "a sign of a healthy, well-run business."
        )
    if pct > 5:
        return "fair", (
            f"A {pct:.1f}% net profit margin is modest but positive. "
            "Common in competitive industries with pricing pressure or high capital requirements."
        )
    if pct > 0:
        return "caution", (
            f"At {pct:.1f}% net margin, profit is thin. Any headwinds — rising costs, slower sales — "
            "could push the company into the red. Watch quarterly earnings closely."
        )
    return "weak", (
        f"A negative net margin ({pct:.1f}%) means the company is losing money overall. "
        "Check the trend — is it improving? Does the company have enough cash to fund continued losses?"
    )


def roe(r):
    r = _safe(r)
    if r is None:
        return "neutral", "Return on Equity (ROE) isn't available."
    pct = r * 100
    if pct > 25:
        return "strong", (
            f"ROE of {pct:.1f}% is exceptional — for every $100 shareholders have invested, the company generates "
            f"${pct:.0f} in annual profit. Warren Buffett's benchmark is 15%+, so {pct:.0f}% is outstanding. "
            "It signals management deploys capital brilliantly."
        )
    if pct > 15:
        return "good", (
            f"At {pct:.1f}% ROE, the company generates solid returns on shareholder capital — "
            "above the market average and a sign management allocates capital effectively."
        )
    if pct > 8:
        return "fair", (
            f"An ROE of {pct:.1f}% is modest. The company earns a positive but unremarkable return on "
            "shareholder investment. Compare to industry peers for context."
        )
    if pct > 0:
        return "caution", (
            f"An ROE of {pct:.1f}% is low — barely earning back what shareholders put in. "
            "Could indicate poor capital allocation or a struggling business."
        )
    return "weak", (
        f"Negative ROE ({pct:.1f}%) means the company is losing money relative to shareholder equity — "
        "a warning sign, though it can be temporary during heavy investment phases."
    )


def roa(r):
    r = _safe(r)
    if r is None:
        return "neutral", "Return on Assets (ROA) isn't available."
    pct = r * 100
    if pct > 10:
        return "strong", (
            f"An ROA of {pct:.1f}% means the company generates {pct:.0f} cents of profit for every $1 of assets it owns. "
            "This is excellent asset efficiency — the company extracts maximum value from what it owns."
        )
    if pct > 5:
        return "good", (
            f"At {pct:.1f}% ROA, the company generates solid returns from its asset base. "
            "Most well-run companies land in the 5-10% range."
        )
    if pct > 2:
        return "fair", (
            f"An ROA of {pct:.1f}% is moderate — typical for capital-intensive businesses like "
            "manufacturing, utilities, or airlines where you need a lot of assets to generate revenue."
        )
    if pct > 0:
        return "caution", (
            f"At {pct:.1f}% ROA, the company generates very little profit relative to its assets. "
            "Either assets are underutilised, or the business has very thin margins."
        )
    return "weak", (
        f"Negative ROA ({pct:.1f}%) — the company is losing money relative to its total asset base. "
        "Worth investigating what's driving the losses."
    )


# ─── Financial Health ─────────────────────────────────────────────────────────

def debt_to_equity(de):
    de = _safe(de)
    if de is None:
        return "neutral", "Debt-to-Equity ratio isn't available."
    # yfinance returns D/E multiplied by 100 (e.g., 150 = 1.5x)
    de_ratio = de / 100 if abs(de) > 10 else de

    if de_ratio < 0:
        return "caution", (
            "Negative D/E means the company has more liabilities than assets — technically balance-sheet insolvent. "
            "Can occur after large buybacks or accumulated losses (e.g., McDonald's). "
            "Check free cash flow to see if it's financially functional despite the optics."
        )
    if de_ratio < 0.3:
        return "strong", (
            f"D/E of {de_ratio:.2f}x — very little debt. For every $1 of shareholder money, "
            f"there's only {de_ratio*100:.0f} cents of debt. A very conservative, low-risk balance sheet."
        )
    if de_ratio < 1.0:
        return "good", (
            f"At {de_ratio:.2f}x D/E, the company has more equity than debt — a healthy balance. "
            "Using modest leverage to boost returns without taking on excessive risk."
        )
    if de_ratio < 2.0:
        return "fair", (
            f"A D/E of {de_ratio:.2f}x means more debt than equity. Manageable for businesses with "
            "predictable cash flows (utilities, consumer staples), but adds risk in downturns."
        )
    if de_ratio < 4.0:
        return "caution", (
            f"At {de_ratio:.2f}x D/E, the company is significantly leveraged. "
            "High debt amplifies both gains and losses. An economic downturn could create stress."
        )
    return "weak", (
        f"D/E of {de_ratio:.2f}x is very high — substantial debt that could become unmanageable "
        "if business conditions worsen. Check interest coverage and free cash flow carefully."
    )


def current_ratio(cr):
    cr = _safe(cr)
    if cr is None:
        return "neutral", "Current ratio isn't available."
    if cr >= 2.0:
        return "good", (
            f"A current ratio of {cr:.2f}x means the company has {cr:.1f}x more short-term assets than "
            "short-term bills due. Think of it like having $2 in your checking account for every $1 in upcoming bills — "
            "very comfortable. (Very high ratios can sometimes indicate idle cash that could be put to work.)"
        )
    if cr >= 1.5:
        return "strong", (
            f"At {cr:.2f}x, the company has strong near-term financial health — {cr:.1f}x more liquid assets than "
            "obligations due within a year. Solid cushion to weather short-term disruptions."
        )
    if cr >= 1.0:
        return "fair", (
            f"A current ratio of {cr:.2f}x means the company can cover short-term debts, but the cushion is thin. "
            "Technically solvent in the near term, but any cash burn or revenue slowdown bears watching."
        )
    return "weak", (
        f"At {cr:.2f}x, current liabilities exceed current assets — like having less in your account than upcoming bills. "
        "A potential liquidity risk. Check whether the company has credit lines or other financing available."
    )


# ─── Growth ───────────────────────────────────────────────────────────────────

def revenue_growth(rg):
    rg = _safe(rg)
    if rg is None:
        return "neutral", "Revenue growth data isn't available."
    pct = rg * 100
    doubling_yrs = round(70 / pct, 1) if pct > 0 else None
    if pct > 30:
        return "strong", (
            f"Revenue grew {pct:.1f}% year-over-year — exceptional growth. "
            f"At this rate, revenue would double in roughly {doubling_yrs} years. "
            "This kind of growth justifies premium valuations, but watch for signs of slowing."
        )
    if pct > 15:
        return "good", (
            f"At {pct:.1f}% revenue growth, this company is expanding meaningfully faster than the economy (~2-3%). "
            "This is the kind of consistent growth that creates long-term shareholder value."
        )
    if pct > 5:
        return "fair", (
            f"Revenue grew {pct:.1f}% — solid, steady expansion. "
            "Better than inflation, suggesting genuine growth rather than just raising prices."
        )
    if pct > 0:
        return "caution", (
            f"Revenue is growing only {pct:.1f}% — barely above flat. "
            "Acceptable for a mature company focused on profitability, but investors expecting expansion may be disappointed."
        )
    return "weak", (
        f"Revenue declined {abs(pct):.1f}% year-over-year. "
        "Shrinking revenue is a red flag. Investigate: is this temporary (lost contract, economic cycle) "
        "or a structural decline in the business?"
    )


def earnings_growth(eg):
    eg = _safe(eg)
    if eg is None:
        return "neutral", "Earnings growth data isn't available."
    pct = eg * 100
    if pct > 25:
        return "strong", (
            f"Earnings grew {pct:.1f}% year-over-year — outstanding. "
            "The company is growing revenue AND keeping more of each dollar. That compounding effect is what drives stock prices."
        )
    if pct > 10:
        return "good", (
            f"At {pct:.1f}% earnings growth, profits are compounding at a healthy clip. "
            "Over time, consistent earnings growth is the single biggest driver of stock returns."
        )
    if pct > 0:
        return "fair", (
            f"Earnings grew {pct:.1f}% — positive but modest. "
            "The company is profitable and improving, just not at an exciting pace."
        )
    return "weak", (
        f"Earnings declined {abs(pct):.1f}%. Falling profits are concerning. "
        "Check whether this is due to one-time charges (restructuring, write-downs) or a recurring downward trend."
    )


# ─── Dividends ────────────────────────────────────────────────────────────────

def dividend_yield(dy):
    dy = _safe(dy)
    if dy is None or dy == 0:
        return "neutral", (
            "This company doesn't pay a dividend. Many great companies — Amazon in its growth years, "
            "Alphabet, Berkshire Hathaway — prefer to reinvest profits rather than pay them out. "
            "What matters is how effectively the company reinvests that capital."
        )
    pct = dy * 100
    if pct > 6:
        return "caution", (
            f"A {pct:.2f}% yield sounds attractive, but yields this high often signal a 'yield trap.' "
            "The stock price may have fallen sharply (which mechanically raises the yield) because the market "
            "fears a dividend cut. Always check the payout ratio and free cash flow sustainability first."
        )
    if pct > 3:
        return "good", (
            f"A {pct:.2f}% dividend yield is attractive — better than most savings accounts. "
            "If the dividend is sustainable, this provides solid income while you wait for potential price appreciation."
        )
    if pct > 1.5:
        return "fair", (
            f"At {pct:.2f}%, this company pays a modest but meaningful dividend. "
            "It signals the company generates enough cash to return money to shareholders. "
            "A small but consistently growing dividend can be very rewarding over decades."
        )
    return "fair", (
        f"The {pct:.2f}% yield is low — income contribution is minimal, so you're primarily investing for capital appreciation. "
        "Check if the dividend is growing year over year — even a small growing dividend signals financial health."
    )


def payout_ratio(pr):
    pr = _safe(pr)
    if pr is None:
        return "neutral", "Payout ratio isn't available."
    pct = pr * 100
    if pct > 100:
        return "weak", (
            f"A payout ratio above 100% ({pct:.0f}%) means the company is paying out MORE than it earns. "
            "This is unsustainable — the company is burning cash or borrowing to fund the dividend. "
            "A dividend cut is a real risk. Check free cash flow for a fuller picture."
        )
    if pct > 75:
        return "caution", (
            f"At {pct:.0f}%, the company pays out {pct:.0f} cents of every dollar earned. "
            "Little room for investment or cushion during downturns. "
            "The dividend could be at risk if earnings decline even modestly."
        )
    if pct > 50:
        return "fair", (
            f"A {pct:.0f}% payout ratio is moderate — roughly splitting earnings between dividends "
            "and reinvesting in the business. Sustainable for most stable, mature companies."
        )
    if pct > 20:
        return "good", (
            f"At {pct:.0f}%, the company returns a meaningful dividend while keeping plenty to reinvest for growth. "
            "A healthy, sustainable payout level."
        )
    return "good", (
        f"A low payout ratio ({pct:.0f}%) means the company retains most earnings for growth. "
        "The dividend is very safe, and there's significant room to grow it over time."
    )


# ─── Technical ───────────────────────────────────────────────────────────────

def rsi(r):
    r = _safe(r)
    if r is None:
        return "neutral", "RSI isn't available — insufficient price history."
    if r > 80:
        return "weak", (
            f"RSI of {r:.1f} is strongly overbought. The stock has surged fast recently. "
            "Many technical traders see this as a signal to wait for a pullback before buying, "
            "or to take partial profits if you already own it."
        )
    if r > 70:
        return "caution", (
            f"RSI of {r:.1f} signals the stock is overbought in the short term — like a rubber band "
            "stretched too far upward. It often snaps back. Not a reason to panic-sell a great business, "
            "but new buyers may want to wait for a better entry price."
        )
    if r > 55:
        return "good", (
            f"An RSI of {r:.1f} shows upward momentum without being overextended — "
            "a comfortable zone for holding or adding to positions."
        )
    if r > 45:
        return "fair", (
            f"At RSI {r:.1f}, the stock shows neutral momentum. "
            "Not at any extreme — watch whether it finds support or continues to drift lower."
        )
    if r > 30:
        return "fair", (
            f"RSI of {r:.1f} shows mild weakness. The stock has been selling off. "
            "Not yet 'oversold' territory, but trending downward. Monitor for a stabilisation."
        )
    if r > 20:
        return "good", (
            f"An RSI of {r:.1f} suggests the stock is oversold — heavily sold in the short term. "
            "Like a stretched rubber band in the other direction, this often (not always) precedes a bounce. "
            "A potential buying opportunity if the underlying fundamentals are solid."
        )
    return "strong", (
        f"RSI of {r:.1f} is extremely oversold — the stock has been hammered. "
        "Historically high probability of a short-term bounce, but verify the fundamentals still support owning it."
    )


def beta(b):
    b = _safe(b)
    if b is None:
        return "neutral", "Beta isn't available."
    if b < 0:
        return "neutral", (
            f"A negative beta ({b:.2f}) means this stock tends to move opposite to the market — "
            "rising when markets fall. Very rare; often seen in gold miners or certain volatility ETFs."
        )
    if b < 0.5:
        return "good", (
            f"Beta of {b:.2f} — very low volatility. If the S&P 500 drops 10%, this stock historically "
            f"drops only about {b*10:.0f}%. Great for conservative, income-focused investors."
        )
    if b < 0.9:
        return "good", (
            f"At beta {b:.2f}, this stock is less volatile than the overall market — "
            "moves with the market but with smaller swings. A bit more defensive than average."
        )
    if b < 1.2:
        return "fair", (
            f"Beta of {b:.2f} — this stock moves roughly in line with the market. "
            f"A 10% market move typically means about a {b*10:.0f}% move in this stock."
        )
    if b < 1.8:
        return "caution", (
            f"At beta {b:.2f}, this stock amplifies market moves. "
            f"A 10% market drop typically means this stock drops about {b*10:.0f}%. "
            "Higher potential upside in bull markets, but steeper drawdowns in corrections."
        )
    return "weak", (
        f"Beta of {b:.2f} — extreme volatility. A 10% market drop historically means "
        f"this stock falls about {b*10:.0f}%. Only suitable for risk-tolerant, long-horizon investors."
    )


# ─── Analyst ─────────────────────────────────────────────────────────────────

def analyst_rating(rec_key, upside, num_analysts):
    if not rec_key or rec_key == "N/A":
        return "neutral", "No analyst consensus data available for this stock."

    map_ = {
        "strong_buy":   ("strong", "Strong Buy"),
        "buy":          ("good",   "Buy"),
        "hold":         ("fair",   "Hold"),
        "underperform": ("caution","Underperform"),
        "sell":         ("weak",   "Sell"),
    }
    rating, label = map_.get(rec_key.lower(), ("neutral", rec_key.title()))

    upside_str = (
        f" The average analyst price target implies a **{upside:+.1f}% {'upside' if upside > 0 else 'downside'}** from current levels."
        if upside is not None else ""
    )
    analysts_str = f" ({num_analysts} analyst{'s' if num_analysts != 1 else ''} covering this stock)" if num_analysts else ""

    return rating, (
        f"Wall Street consensus: **{label}**.{upside_str}{analysts_str}\n\n"
        "Keep in mind: analysts sometimes have conflicts of interest — their banks do business with the companies they cover. "
        "Use ratings as one data point among many, not as the final word."
    )
