# How the model works — plain English

This document explains every calculation behind the Client Scenario Engine. It is aimed at a planner or analyst who wants to understand *why* the numbers on screen look the way they do, without reading the Python.

All formulas live in `helpers.py`. The app file `app.py` only collects inputs and renders charts — it does not change any numbers.

---

## 1. Inputs the planner provides

For each client (or demo client "Sarah & Daniel"):

| Input | What it represents |
|---|---|
| `income` | Gross household income per year |
| `expenses` | Total household spending per year |
| `super_balance` | Combined superannuation balance today |
| `investments` | Non-super investments (shares, ETFs, managed funds, property equity) |
| `cash` | Liquid savings / offset / emergency fund |
| `debt` | Outstanding debt (typically mortgage) |

Two optional **scenarios** can override any of those values — for example, "income up by $20k" or "debt reduced by $50k".

---

## 2. The headline numbers (today's snapshot)

`calculate_financials()` computes six figures from the inputs:

1. **Total assets** = `cash + investments + super_balance`
2. **Total liabilities** = `debt`
3. **Net position** = `assets − liabilities`
4. **Annual surplus** = `income − expenses`
5. **Savings rate** = `surplus ÷ income`
6. **Debt-to-assets ratio** = `liabilities ÷ assets`
7. **Emergency buffer (months)** = `cash ÷ expenses × 12` — how many months of spending the cash pile would cover

These power the Statement of Financial Position and the metric cards at the top of the report.

---

## 3. Risk flags

`assess_financial_risk()` raises a flag when any of these conditions are true:

| Flag | Trigger |
|---|---|
| Low savings rate | Savings rate below **10%** |
| Low emergency buffer | Cash less than **20%** of annual expenses (~2.4 months) |
| High leverage | Debt above **70%** of total assets |
| Under-funded super | Super balance below one year of household income |

Flags are heuristics — they are conversation starters for the planner, not formal advice.

---

## 4. The 20-year projection (the engine room)

`project_wealth()` and `project_balance_sheet()` step the household forward one year at a time. The default assumptions are:

- **Investment / super growth rate (`gr`)**: 7% p.a.
- **Superannuation Guarantee (`sg`)**: 11.5% of income contributed to super each year
- **Annual debt repayment (`rep`)**: $20,000 per year

Each year:

1. **Super grows**: `super = super × 1.07 + income × 11.5%`
   *Old balance compounds, then the year's SG contribution is added.*
2. **Investments grow and absorb the leftover surplus**:
   `investments = investments × 1.07 + extra`
   where `extra = max(0, income − expenses − repayment)` — i.e. anything left after spending and mortgage repayments is reinvested.
3. **Cash stays flat.** It is treated as a held buffer, not a growth asset.
4. **Debt reduces**: `debt = max(0, debt − 20,000)`. Once the debt hits zero, repayments stop being deducted.
5. **Net worth that year** = `super + investments + cash − debt`.

The projection is **deterministic** — there is no Monte Carlo, no return volatility, no inflation adjustment, and no tax modelling. Numbers are nominal dollars at the assumed growth rate.

The same loop is run three times — once for the base case and once for each scenario — and the resulting net-worth lines are charted side-by-side.

---

## 5. Pre-retirement readiness

`calc_pre_retirement()` answers: *"By the time the client retires, will their super be enough?"*

1. Run the same yearly loop as the projection, but only for `years_to_retire = retirement_age − current_age` years.
2. Take the projected super balance at retirement.
3. Compare it to a target: **`target_super_needed = desired_retirement_income ÷ 4%`** — this is the classic 4% safe-withdrawal-rate inversion, e.g. $80k of income needs roughly $2M in super.
4. The gap is `projected_super − target_super_needed`.
5. If the gap is negative, estimate how many extra years of SG contributions would close it: `gap ÷ (income × 11.5%)`.

The "on track" badge simply means projected super ≥ target super.

---

## 6. Retirement drawdown

`calc_retirement_drawdown()` simulates the drawdown phase:

- Total pot at retirement = `super + investments + cash`.
- **Sustainable income** = `pot × 4%` (or whatever drawdown rate the planner sets).
- Each year of retirement: pot grows at 7%, then the planner withdraws `pot × drawdown_rate`. Repeat for 25 years by default.
- If the pot ever hits zero, that year is recorded as the **depletion year**.
- "On track" = pot never depletes within the horizon **and** sustainable income meets the desired income.

---

## 7. Scenario comparison

A scenario is just a copy of the base inputs with one or more values overridden (`create_scenario()`). The model is then re-run on the overridden inputs. The difference between scenarios is therefore *purely mechanical* — it reflects what the same engine produces with different starting conditions, no behavioural assumptions are layered on top.

---

## 8. The "Planning observations" boxes

`generate_insight()` writes the bullet points under each chart. They are **rule-based**, not AI-generated. Examples:

- *Cashflow*: thresholds at 35%, 20%, 10% savings rate trigger different wording. The strongest scenario surplus is named.
- *Balance sheet*: debt-to-assets buckets at >200%, >70%, ≤70%. The first year net worth crosses zero is called out.
- *Scenarios*: ranks the three projections by year-20 net worth and reports the gap between best and worst.
- *Summary*: synthesises net position, surplus, savings rate, and the strongest scenario into one priority action.

If you change a threshold in the code, the on-screen narrative changes accordingly.

---

## 9. What the model does NOT do

Be explicit with the client about these limits:

- **No tax.** Gross income is used everywhere. Super contributions are not taxed at 15%, investment returns are not adjusted for CGT, and franking credits are ignored.
- **No inflation.** All dollars are nominal. A $2M projection in 20 years is *not* equivalent to $2M today's purchasing power.
- **No return volatility.** A flat 7% every year — real markets don't behave this way.
- **No salary growth.** Income is held flat unless the planner overrides it in a scenario.
- **No expense growth.** Spending is held flat too.
- **No life events.** Children, redundancy, downsizing, inheritance, divorce, age pension — all out of scope unless modelled by hand in a scenario.
- **No personal advice.** Every screen carries the disclaimer "for planner reference only".

The intended use is a *fast comparative tool* — show a client how strategy A vs. strategy B changes the trajectory, given identical assumptions. Absolute numbers should not be quoted as forecasts.

---

## 10. Default assumptions reference

| Parameter | Default | Where used |
|---|---|---|
| Investment / super growth | 7% p.a. | All projections |
| SG contribution rate | 11.5% of income | Super accumulation |
| Annual debt repayment | $20,000 | Debt amortisation |
| Drawdown rate | 4% | Retirement income |
| Retirement horizon | 25 years | Drawdown projection |
| Projection horizon | 20 years | Wealth projection |
| Legislation reference | 2024-25 financial year | SG rate, displayed in footer |

All can be overridden by passing different keyword arguments to the helper functions, or by adding sliders to the UI.
