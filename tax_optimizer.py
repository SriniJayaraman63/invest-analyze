"""
tax_optimizer.py — Federal Tax Optimization Engine

Data sourced from IRS Rev. Proc. 2024-40 (2025 inflation-adjusted figures).
Covers: progressive income tax, FICA, NIIT, standard deductions,
        contribution limits for 401(k)/IRA/HSA/FSA/529.

All dollar amounts in USD. Tax year: 2025.
"""

from __future__ import annotations
import math

# ── 2025 Federal Income Tax Brackets ─────────────────────────────────────────
# Each entry: (upper_bound_inclusive, marginal_rate)
# Final entry uses math.inf as the ceiling.
TAX_BRACKETS: dict[str, list[tuple[float, float]]] = {
    "Single": [
        (11_925,    0.10),
        (48_475,    0.12),
        (103_350,   0.22),
        (197_300,   0.24),
        (250_525,   0.32),
        (626_350,   0.35),
        (math.inf,  0.37),
    ],
    "Married Filing Jointly": [
        (23_850,    0.10),
        (96_950,    0.12),
        (206_700,   0.22),
        (394_600,   0.24),
        (501_050,   0.32),
        (751_600,   0.35),
        (math.inf,  0.37),
    ],
    "Married Filing Separately": [
        (11_925,    0.10),
        (48_475,    0.12),
        (103_350,   0.22),
        (197_300,   0.24),
        (250_525,   0.32),
        (375_800,   0.35),
        (math.inf,  0.37),
    ],
    "Head of Household": [
        (17_000,    0.10),
        (64_850,    0.12),
        (103_350,   0.22),
        (197_300,   0.24),
        (250_500,   0.32),
        (626_350,   0.35),
        (math.inf,  0.37),
    ],
}

# ── 2025 Standard Deductions ──────────────────────────────────────────────────
STANDARD_DEDUCTIONS: dict[str, float] = {
    "Single":                    15_000,
    "Married Filing Jointly":    30_000,
    "Married Filing Separately": 15_000,
    "Head of Household":         22_500,
}

# Additional standard deduction for age 65+ or blind (per qualifying person)
SENIOR_BLIND_DEDUCTION = {
    "Single":                    2_000,   # single / HoH: $2,000 per condition
    "Head of Household":         2_000,
    "Married Filing Jointly":    1_600,   # $1,600 per qualifying spouse per condition
    "Married Filing Separately": 1_600,
}

# ── FICA (2025) ───────────────────────────────────────────────────────────────
SS_WAGE_BASE          = 176_100   # Social Security taxable wage ceiling
SS_EMPLOYEE_RATE      = 0.062
MEDICARE_EMPLOYEE_RATE= 0.0145
ADDL_MEDICARE_RATE    = 0.009    # Additional Medicare Tax on wages above threshold
ADDL_MEDICARE_THRESH: dict[str, float] = {
    "Single":                    200_000,
    "Married Filing Jointly":    250_000,
    "Married Filing Separately": 125_000,
    "Head of Household":         200_000,
}

# ── Net Investment Income Tax (NIIT) ──────────────────────────────────────────
NIIT_RATE = 0.038
NIIT_MAGI_THRESH: dict[str, float] = {
    "Single":                    200_000,
    "Married Filing Jointly":    250_000,
    "Married Filing Separately": 125_000,
    "Head of Household":         200_000,
}

# ── 2025 Contribution Limits ──────────────────────────────────────────────────
LIMITS: dict[str, float] = {
    "401k":               23_500,
    "401k_catchup_50":     7_500,   # age 50-59 and 64+
    "401k_catchup_6063":  11_250,   # age 60-63 (SECURE 2.0 super catch-up)
    "403b":               23_500,
    "403b_catchup_50":     7_500,
    "simple_ira":         16_500,
    "simple_catchup":      3_500,
    "ira":                 7_000,
    "ira_catchup":         1_000,   # age 50+
    "hsa_self":            4_300,
    "hsa_family":          8_550,
    "hsa_catchup":         1_000,   # age 55+
    "fsa_healthcare":      3_300,
    "fsa_dependent_care":  5_000,   # household limit
    "sep_ira_pct":         0.25,    # 25% of net self-employment income
    "sep_ira_max":        70_000,
}

# ── SALT Cap ──────────────────────────────────────────────────────────────────
SALT_CAP = 10_000

# ── IRA Deductibility Phase-outs (2025 MAGI) — active workplace plan ─────────
IRA_DEDUCT_PHASEOUT: dict[str, tuple[float, float]] = {
    "Single":                    (79_000,  89_000),
    "Married Filing Jointly":    (126_000, 146_000),
    "Married Filing Separately": (0,       10_000),
    "Head of Household":         (79_000,  89_000),
}
# MFJ — participant's non-covered spouse: $236k–$246k (handled separately)
IRA_NONCOVERED_SPOUSE_PHASEOUT = (236_000, 246_000)

# ── Roth IRA Contribution Phase-outs (2025 MAGI) ─────────────────────────────
ROTH_PHASEOUT: dict[str, tuple[float, float]] = {
    "Single":                    (150_000, 165_000),
    "Married Filing Jointly":    (236_000, 246_000),
    "Married Filing Separately": (0,       10_000),
    "Head of Household":         (150_000, 165_000),
}


# ── Pure tax math ─────────────────────────────────────────────────────────────

def compute_federal_tax(taxable_income: float, filing_status: str) -> float:
    """Progressive federal income tax. Returns 0 for negative taxable income."""
    if taxable_income <= 0:
        return 0.0
    brackets = TAX_BRACKETS[filing_status]
    tax, prev = 0.0, 0.0
    for ceiling, rate in brackets:
        if taxable_income <= prev:
            break
        taxable_at_rate = min(taxable_income, ceiling) - prev
        tax += taxable_at_rate * rate
        prev = ceiling
    return tax


def marginal_rate(taxable_income: float, filing_status: str) -> float:
    """Marginal federal income tax rate at the given taxable income."""
    if taxable_income <= 0:
        return 0.0
    for ceiling, rate in TAX_BRACKETS[filing_status]:
        if taxable_income <= ceiling:
            return rate
    return TAX_BRACKETS[filing_status][-1][1]


def effective_rate(federal_tax: float, gross_income: float) -> float:
    if gross_income <= 0:
        return 0.0
    return federal_tax / gross_income


def _phaseout_fraction(value: float, lo: float, hi: float) -> float:
    """Fraction of benefit remaining after phase-out (1.0 = full, 0.0 = phased out)."""
    if value <= lo:
        return 1.0
    if value >= hi:
        return 0.0
    return 1.0 - (value - lo) / (hi - lo)


# ── TaxOptimizer ──────────────────────────────────────────────────────────────

class TaxOptimizer:
    """
    Analyses a household's tax situation from W-2 inputs and current
    tax-advantaged account usage, then generates ranked recommendations.
    """

    def __init__(
        self,
        # ── W-2 data ──
        w2_box1: float,              # Wages after pre-tax payroll deductions
        w2_box2: float,              # Federal income tax withheld
        w2_box12_retirement: float,  # 401k/403b/SIMPLE contributions (Box 12 D/E/S)
        w2_box12_hsa: float,         # Employer + employee HSA via payroll (Box 12 W)
        # ── Household ──
        filing_status: str,
        age: int,
        spouse_age: int,
        spouse_w2_box1: float,       # 0 if not applicable
        num_dependents: int,
        # ── Current tax-advantaged accounts ──
        current_ira_trad: float,
        current_ira_roth: float,
        current_hsa_self: float,     # contributions outside payroll
        hsa_coverage: str,           # "None", "Self", "Family"
        current_fsa_health: float,
        current_fsa_dep: float,
        current_529: float,
        # ── Other income & deductions ──
        investment_income: float,    # interest + dividends + capital gains
        other_income: float,         # freelance, rental, etc.
        mortgage_interest: float,
        charitable_cash: float,
        charitable_noncash: float,
        state_local_taxes: float,    # actual amount paid (before SALT cap)
        other_itemized: float,       # medical > 7.5% AGI, etc.
        # ── Plan details ──
        has_workplace_plan: bool,    # covered by employer retirement plan
        plan_type: str,              # "401(k)", "403(b)", "SIMPLE IRA", "None"
        has_hdhp: bool,              # HSA-eligible health plan
    ):
        self.w2_box1               = w2_box1
        self.w2_box2               = w2_box2
        self.w2_box12_ret          = w2_box12_retirement
        self.w2_box12_hsa          = w2_box12_hsa
        self.filing_status         = filing_status
        self.age                   = age
        self.spouse_age            = spouse_age
        self.spouse_w2             = spouse_w2_box1
        self.num_dependents        = num_dependents
        self.current_ira_trad      = current_ira_trad
        self.current_ira_roth      = current_ira_roth
        self.current_hsa_self      = current_hsa_self
        self.hsa_coverage          = hsa_coverage
        self.current_fsa_health    = current_fsa_health
        self.current_fsa_dep       = current_fsa_dep
        self.current_529           = current_529
        self.investment_income     = investment_income
        self.other_income          = other_income
        self.mortgage_interest     = mortgage_interest
        self.charitable_cash       = charitable_cash
        self.charitable_noncash    = charitable_noncash
        self.state_local_taxes     = state_local_taxes
        self.other_itemized        = other_itemized
        self.has_workplace_plan    = has_workplace_plan
        self.plan_type             = plan_type
        self.has_hdhp              = has_hdhp

        # ── Derived base values ──
        # Gross wages = W2 Box1 + current pre-tax retirement + payroll HSA already excluded
        self.total_wages = w2_box1 + spouse_w2_box1
        self.gross_income = self.total_wages + investment_income + other_income

        # MAGI approximation (simplified: add back IRA deduction, student loan interest)
        self.magi = self.gross_income   # conservative; above-the-line not yet deducted

        # Current pre-tax retirement total
        self.retirement_pretax = w2_box12_retirement   # already reflected in Box 1

        # Itemized deductions (SALT-capped)
        salt_allowed = min(state_local_taxes, SALT_CAP)
        self.itemized = (
            salt_allowed
            + mortgage_interest
            + charitable_cash
            + charitable_noncash
            + other_itemized
        )
        self.std_ded = STANDARD_DEDUCTIONS[filing_status]
        # Senior / blind additions
        if age >= 65:
            self.std_ded += SENIOR_BLIND_DEDUCTION.get(filing_status, 0)
        if filing_status == "Married Filing Jointly" and spouse_age >= 65:
            self.std_ded += SENIOR_BLIND_DEDUCTION["Married Filing Jointly"]

        self.deduction = max(self.std_ded, self.itemized)
        self.uses_itemized = self.itemized > self.std_ded

        # Current above-the-line deductions (IRA trad, HSA self)
        self.current_atl = current_ira_trad + current_hsa_self

        # Current AGI
        self.current_agi = max(0.0, self.gross_income - self.current_atl)

        # Current taxable income
        self.current_taxable = max(0.0, self.current_agi - self.deduction)

        # Current federal tax
        self.current_fed_tax = compute_federal_tax(self.current_taxable, filing_status)
        self.current_marginal = marginal_rate(self.current_taxable, filing_status)

    # ── Retirement plan limits ─────────────────────────────────────────────────
    def _retirement_limit(self) -> float:
        if self.plan_type == "SIMPLE IRA":
            base = LIMITS["simple_ira"]
            return base + (LIMITS["simple_catchup"] if self.age >= 50 else 0)
        base = LIMITS["403b"] if self.plan_type == "403(b)" else LIMITS["401k"]
        if 60 <= self.age <= 63:
            return base + LIMITS["401k_catchup_6063"]
        if self.age >= 50:
            return base + LIMITS["401k_catchup_50"]
        return base

    def _ira_limit(self) -> float:
        return LIMITS["ira"] + (LIMITS["ira_catchup"] if self.age >= 50 else 0)

    def _hsa_limit(self) -> float:
        base = LIMITS["hsa_family"] if self.hsa_coverage == "Family" else LIMITS["hsa_self"]
        return base + (LIMITS["hsa_catchup"] if self.age >= 55 else 0)

    # ── IRA deductibility ─────────────────────────────────────────────────────
    def _ira_deductible_fraction(self) -> float:
        if not self.has_workplace_plan:
            if self.filing_status == "Married Filing Jointly" and self.spouse_w2 > 0:
                # Not covered, but spouse is — use non-covered-spouse phase-out
                lo, hi = IRA_NONCOVERED_SPOUSE_PHASEOUT
                return _phaseout_fraction(self.magi, lo, hi)
            return 1.0
        lo, hi = IRA_DEDUCT_PHASEOUT.get(self.filing_status, (0, 0))
        return _phaseout_fraction(self.magi, lo, hi)

    def _can_contribute_roth(self) -> bool:
        lo, hi = ROTH_PHASEOUT.get(self.filing_status, (0, 0))
        return self.magi < hi

    # ── Generate recommendations ──────────────────────────────────────────────
    def generate_recommendations(self) -> list[dict]:
        recs = []
        mr = self.current_marginal

        # 1. Maximize workplace retirement plan
        if self.has_workplace_plan and self.plan_type != "None":
            limit    = self._retirement_limit()
            current  = self.w2_box12_ret
            room     = max(0.0, limit - current)
            if room > 0:
                # 401k also saves FICA on SS-taxable portion
                fica_save = min(room, max(0, SS_WAGE_BASE - self.total_wages)) * SS_EMPLOYEE_RATE
                recs.append({
                    "id":          "max_retirement",
                    "category":    "Retirement",
                    "strategy":    f"Maximize {self.plan_type} contributions",
                    "detail":      (f"Increase pre-tax {self.plan_type} from "
                                   f"${current:,.0f} to ${limit:,.0f}/yr. "
                                   f"Reduces federal taxable income dollar-for-dollar."),
                    "current":     current,
                    "recommended": limit,
                    "deduction":   room,
                    "fed_saving":  round(room * mr),
                    "fica_saving": round(fica_save),
                    "priority":    "High",
                    "note":        (f"2025 limit: ${limit:,.0f}. "
                                   + ("Includes super catch-up (age 60-63)." if 60 <= self.age <= 63 else
                                      "Includes catch-up contribution (age 50+)." if self.age >= 50 else "")),
                })

        # 2. Traditional IRA (deductible portion)
        ira_limit   = self._ira_limit()
        ira_used    = self.current_ira_trad + self.current_ira_roth
        ira_room    = max(0.0, ira_limit - ira_used)
        ded_frac    = self._ira_deductible_fraction()
        ded_room    = ira_room * ded_frac
        if ded_room > 0:
            recs.append({
                "id":          "trad_ira",
                "category":    "Retirement",
                "strategy":    "Traditional IRA (deductible)",
                "detail":      (f"Contribute ${ded_room:,.0f} to a Traditional IRA "
                                f"({ded_frac*100:.0f}% deductible at your income level). "
                                f"Above-the-line deduction — reduces AGI directly."),
                "current":     self.current_ira_trad,
                "recommended": self.current_ira_trad + ded_room,
                "deduction":   ded_room,
                "fed_saving":  round(ded_room * mr),
                "fica_saving": 0,
                "priority":    "High" if ded_frac >= 0.9 else "Medium",
                "note":        (f"2025 IRA limit: ${ira_limit:,.0f}. "
                                + (f"Partially phased out at your MAGI." if ded_frac < 1.0 else "")),
            })
        elif ira_room > 0 and not self._can_contribute_roth():
            # Income too high for deductible IRA and Roth → Backdoor Roth
            recs.append({
                "id":          "backdoor_roth",
                "category":    "Retirement",
                "strategy":    "Backdoor Roth IRA",
                "detail":      ("Your income exceeds both the Traditional IRA deductibility "
                                "and Roth IRA contribution phase-outs. A Backdoor Roth "
                                "(non-deductible IRA → Roth conversion) provides tax-free "
                                "growth with no immediate deduction."),
                "current":     ira_used,
                "recommended": ira_limit,
                "deduction":   0,
                "fed_saving":  0,
                "fica_saving": 0,
                "priority":    "Medium",
                "note":        "No current-year deduction, but future qualified withdrawals are tax-free.",
            })
        elif ira_room > 0 and self._can_contribute_roth():
            # Roth IRA available
            lo, hi = ROTH_PHASEOUT.get(self.filing_status, (0, 0))
            frac = _phaseout_fraction(self.magi, lo, hi)
            roth_room = ira_room * frac
            if roth_room > 0:
                recs.append({
                    "id":          "roth_ira",
                    "category":    "Retirement",
                    "strategy":    "Roth IRA contribution",
                    "detail":      (f"Contribute ${roth_room:,.0f} to a Roth IRA. "
                                   "No deduction now, but all growth and withdrawals are "
                                   "tax-free in retirement. Best when current rate < future rate."),
                    "current":     self.current_ira_roth,
                    "recommended": self.current_ira_roth + roth_room,
                    "deduction":   0,
                    "fed_saving":  0,
                    "fica_saving": 0,
                    "priority":    "Medium",
                    "note":        "No immediate tax saving; long-term tax-free growth benefit.",
                })

        # 3. HSA — triple tax advantage
        if self.has_hdhp and self.hsa_coverage != "None":
            hsa_limit   = self._hsa_limit()
            hsa_current = self.w2_box12_hsa + self.current_hsa_self
            hsa_room    = max(0.0, hsa_limit - hsa_current)
            if hsa_room > 0:
                recs.append({
                    "id":          "hsa",
                    "category":    "Healthcare",
                    "strategy":    "Maximize HSA contributions",
                    "detail":      (f"Contribute ${hsa_room:,.0f} more to your HSA "
                                   f"(current: ${hsa_current:,.0f}, limit: ${hsa_limit:,.0f}). "
                                   "Triple tax advantage: deductible, grows tax-free, "
                                   "withdrawals tax-free for medical expenses. "
                                   "After 65, withdrawals for any purpose taxed as ordinary income."),
                    "current":     hsa_current,
                    "recommended": hsa_limit,
                    "deduction":   hsa_room,
                    "fed_saving":  round(hsa_room * mr),
                    "fica_saving": round(hsa_room * (SS_EMPLOYEE_RATE + MEDICARE_EMPLOYEE_RATE)),
                    "priority":    "High",
                    "note":        f"2025 HSA limit ({self.hsa_coverage}): ${hsa_limit:,.0f}.",
                })

        # 4. Healthcare FSA
        fsa_room = max(0.0, LIMITS["fsa_healthcare"] - self.current_fsa_health)
        if fsa_room > 0 and not self.has_hdhp:
            recs.append({
                "id":          "fsa_health",
                "category":    "Healthcare",
                "strategy":    "Contribute to Healthcare FSA",
                "detail":      (f"Add ${fsa_room:,.0f} to a Healthcare FSA "
                                f"(current: ${self.current_fsa_health:,.0f}, "
                                f"limit: ${LIMITS['fsa_healthcare']:,.0f}). "
                                "Pre-tax dollars for medical, dental, and vision expenses. "
                                "Note: use-it-or-lose-it (up to $640 rollover in 2025)."),
                "current":     self.current_fsa_health,
                "recommended": LIMITS["fsa_healthcare"],
                "deduction":   fsa_room,
                "fed_saving":  round(fsa_room * mr),
                "fica_saving": round(fsa_room * (SS_EMPLOYEE_RATE + MEDICARE_EMPLOYEE_RATE)),
                "priority":    "Medium",
                "note":        "Cannot combine FSA + HSA (unless Limited-Purpose FSA).",
            })

        # 5. Dependent Care FSA
        if self.num_dependents > 0:
            dep_room = max(0.0, LIMITS["fsa_dependent_care"] - self.current_fsa_dep)
            if dep_room > 0:
                recs.append({
                    "id":          "fsa_dep",
                    "category":    "Childcare",
                    "strategy":    "Dependent Care FSA",
                    "detail":      (f"Contribute ${dep_room:,.0f} more to a Dependent Care FSA "
                                   f"(current: ${self.current_fsa_dep:,.0f}, "
                                   f"limit: ${LIMITS['fsa_dependent_care']:,.0f}/household). "
                                   "Covers daycare, after-school care, summer day camp. "
                                   "Reduces AGI and avoids FICA on contributed amount."),
                    "current":     self.current_fsa_dep,
                    "recommended": LIMITS["fsa_dependent_care"],
                    "deduction":   dep_room,
                    "fed_saving":  round(dep_room * mr),
                    "fica_saving": round(dep_room * (SS_EMPLOYEE_RATE + MEDICARE_EMPLOYEE_RATE)),
                    "priority":    "High",
                    "note":        "Household cap $5,000 (MFJ). Coordinates with Child & Dependent Care Credit.",
                })

        # 6. 529 Education Savings
        if self.num_dependents > 0 and self.current_529 < 10_000:
            recs.append({
                "id":          "plan_529",
                "category":    "Education",
                "strategy":    "529 Education Savings Plan",
                "detail":      ("Contributions to a 529 plan grow tax-free and withdrawals are "
                                "tax-free for qualified education expenses. Many states offer a "
                                "state income tax deduction. No federal deduction, but "
                                "significant long-term compounding advantage."),
                "current":     self.current_529,
                "recommended": self.current_529 + 5_000,
                "deduction":   0,
                "fed_saving":  0,
                "fica_saving": 0,
                "priority":    "Medium",
                "note":        "State deduction varies. Check your state's 529 plan for deductibility.",
            })

        # 7. Itemized vs Standard deduction gap
        gap = self.itemized - self.std_ded
        if -5_000 < gap < 0:
            needed = abs(gap)
            recs.append({
                "id":          "itemize_gap",
                "category":    "Deductions",
                "strategy":    "Bundle deductions to exceed standard deduction",
                "detail":      (f"Your itemized deductions (${self.itemized:,.0f}) are "
                                f"${needed:,.0f} below the standard deduction (${self.std_ded:,.0f}). "
                                "Consider bunching charitable donations into a Donor-Advised Fund "
                                "(DAF) in alternate years, or prepaying deductible expenses, "
                                "to exceed the threshold in high-income years."),
                "current":     self.itemized,
                "recommended": self.std_ded + needed,
                "deduction":   needed,
                "fed_saving":  round(needed * mr),
                "fica_saving": 0,
                "priority":    "Medium",
                "note":        "Bunching strategy: itemize in one year, take standard deduction the next.",
            })
        elif gap > 0:
            # Already itemizing — note SALT cap impact
            salt_lost = max(0.0, self.state_local_taxes - SALT_CAP)
            if salt_lost > 0:
                recs.append({
                    "id":          "salt_cap",
                    "category":    "Deductions",
                    "strategy":    "SALT cap — consider pass-through entity workaround",
                    "detail":      (f"You are losing ${salt_lost:,.0f} of state/local tax deduction "
                                   "due to the $10,000 SALT cap. If you own a pass-through business "
                                   "(S-corp, partnership), many states allow a PTET election that "
                                   "effectively deducts state taxes at the entity level, bypassing "
                                   "the personal SALT cap."),
                    "current":     SALT_CAP,
                    "recommended": min(self.state_local_taxes, SALT_CAP),
                    "deduction":   0,
                    "fed_saving":  0,
                    "fica_saving": 0,
                    "priority":    "Medium",
                    "note":        "Consult a tax advisor regarding your state's PTET election.",
                })

        # 8. Charitable giving — Donor-Advised Fund
        if (self.charitable_cash + self.charitable_noncash) >= 2_000 and self.uses_itemized:
            recs.append({
                "id":          "daf",
                "category":    "Charitable",
                "strategy":    "Donor-Advised Fund (DAF) for appreciated assets",
                "detail":      ("Donate appreciated securities to a DAF instead of cash. "
                                "You receive a deduction for the full fair market value, "
                                "avoid capital gains tax on the appreciation, and can "
                                "recommend grants to charities over time."),
                "current":     self.charitable_cash,
                "recommended": self.charitable_cash,
                "deduction":   0,
                "fed_saving":  round(self.charitable_cash * 0.20 * mr),
                "fica_saving": 0,
                "priority":    "Low",
                "note":        ("Estimated saving assumes 20% embedded gain in donated assets. "
                                "Actual saving depends on asset appreciation."),
            })

        # 9. Mega Back-Door Roth (after-tax 401k) — high income
        if self.gross_income > 150_000 and self.has_workplace_plan:
            ret_limit = self._retirement_limit()
            total_401k_limit = min(70_000, self.total_wages)
            after_tax_room = max(0.0, total_401k_limit - ret_limit)
            if after_tax_room > 2_000:
                recs.append({
                    "id":          "mega_backdoor",
                    "category":    "Retirement",
                    "strategy":    "Mega Backdoor Roth (after-tax 401k)",
                    "detail":      (f"If your plan allows after-tax 401(k) contributions and "
                                   f"in-service withdrawals/conversions, you can contribute up to "
                                   f"${after_tax_room:,.0f} in after-tax dollars and convert to Roth. "
                                   "No current deduction, but significant tax-free growth opportunity."),
                    "current":     0,
                    "recommended": after_tax_room,
                    "deduction":   0,
                    "fed_saving":  0,
                    "fica_saving": 0,
                    "priority":    "Medium",
                    "note":        "Plan must explicitly allow after-tax contributions and in-service Roth conversion. Verify with plan administrator.",
                })

        # 10. NIIT / high-investment-income alert
        niit_thresh = NIIT_MAGI_THRESH.get(self.filing_status, 200_000)
        if self.investment_income > 0 and self.gross_income > niit_thresh * 0.85:
            niit_exposure = max(0.0, self.investment_income - max(0, niit_thresh - self.total_wages))
            if niit_exposure > 0:
                niit_cost = round(niit_exposure * NIIT_RATE)
                recs.append({
                    "id":          "niit",
                    "category":    "Investments",
                    "strategy":    "Reduce NIIT exposure via tax-exempt / tax-deferred investments",
                    "detail":      (f"You may owe the 3.8% Net Investment Income Tax on "
                                   f"~${niit_exposure:,.0f} of investment income (est. ${niit_cost:,}/yr). "
                                   "Strategies: shift taxable investments to municipal bonds "
                                   "(tax-exempt income), max tax-deferred accounts, use "
                                   "tax-loss harvesting to offset capital gains."),
                    "current":     niit_exposure,
                    "recommended": 0,
                    "deduction":   niit_exposure,
                    "fed_saving":  niit_cost,
                    "fica_saving": 0,
                    "priority":    "High" if niit_cost > 1_000 else "Medium",
                    "note":        f"NIIT threshold: ${niit_thresh:,.0f} (MAGI). Rate: 3.8% on net investment income.",
                })

        return recs

    # ── Project tax with selected recommendations ─────────────────────────────
    def projected_tax(self, selected_ids: set) -> dict:
        """
        Recalculate federal tax with selected recommendations applied.
        Returns dict with projected figures and total savings.
        """
        recs = {r["id"]: r for r in self.generate_recommendations()}

        additional_deductions = sum(
            recs[rid]["deduction"] for rid in selected_ids if rid in recs
        )
        niit_reduction = 0.0
        if "niit" in selected_ids:
            niit_reduction = recs["niit"]["fed_saving"] if "niit" in recs else 0.0

        proj_agi      = max(0.0, self.current_agi - additional_deductions)
        proj_taxable  = max(0.0, proj_agi - self.deduction)
        proj_fed_tax  = compute_federal_tax(proj_taxable, self.filing_status)

        # NIIT saving is additive (separate calculation)
        proj_fed_tax  = max(0.0, proj_fed_tax - niit_reduction)

        total_fica    = sum(recs[rid]["fica_saving"] for rid in selected_ids if rid in recs)
        fed_saving    = self.current_fed_tax - proj_fed_tax
        total_saving  = fed_saving + total_fica

        return {
            "proj_agi":         proj_agi,
            "proj_taxable":     proj_taxable,
            "proj_fed_tax":     proj_fed_tax,
            "proj_marginal":    marginal_rate(proj_taxable, self.filing_status),
            "proj_effective":   effective_rate(proj_fed_tax, self.gross_income),
            "fed_saving":       fed_saving,
            "fica_saving":      total_fica,
            "total_saving":     total_saving,
            "additional_deductions": additional_deductions,
        }

    # ── Current situation summary ─────────────────────────────────────────────
    def current_summary(self) -> dict:
        return {
            "gross_income":     self.gross_income,
            "above_the_line":   self.current_atl,
            "current_agi":      self.current_agi,
            "deduction_type":   "Itemized" if self.uses_itemized else "Standard",
            "deduction_amount": self.deduction,
            "taxable_income":   self.current_taxable,
            "federal_tax":      self.current_fed_tax,
            "withheld":         self.w2_box2,
            "refund_or_owe":    self.w2_box2 - self.current_fed_tax,
            "marginal_rate":    self.current_marginal,
            "effective_rate":   effective_rate(self.current_fed_tax, self.gross_income),
        }
