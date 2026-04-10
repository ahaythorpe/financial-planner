import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from datetime import date

APP_VERSION      = "1.0.0"
APP_BUILD_DATE   = "April 2026"
LEGISLATION_DATE = "2024-25 financial year"

# ── Palette ──────────────────────────────────────────────────────
NAVY     = "#1B2E4B"
S1_COLOR = "#6B3FA0"
TEAL     = "#1D9E75"
BG_POS   = "#E2F0D9"; TXT_POS = "#006100"
BG_NEG   = "#FCE4D6"; TXT_NEG = "#C00000"

EXTRA_COLORS = ["#2E86AB","#D85A30","#457B9D","#993556","#2D6A4F","#8B5E3C"]

# ── Demo client — locked ─────────────────────────────────────────
DEMO = dict(name="Sarah & Daniel", income=160000, expenses=95000,
            super_balance=120000, investments=40000, cash=15000, debt=420000)

# ── Model functions ──────────────────────────────────────────────
def calculate_financials(c):
    assets = c["cash"] + c["investments"] + c["super_balance"]
    liab   = c["debt"]
    net    = assets - liab
    sur    = c["income"] - c["expenses"]
    return dict(total_assets=assets, total_liabilities=liab,
                net_position=net, surplus=sur,
                savings_rate=sur/c["income"] if c["income"] else 0,
                debt_to_assets=liab/assets if assets else 0,
                emergency_months=(c["cash"]/c["expenses"])*12 if c["expenses"] else 0)

def assess_financial_risk(c, r):
    f = []
    if r["savings_rate"]  < 0.1:               f.append("Low savings rate (< 10%)")
    if c["cash"]          < c["expenses"]*0.2:  f.append("Low emergency buffer (< 20% of expenses)")
    if c["debt"]          > r["total_assets"]*0.7: f.append("High leverage (debt > 70% of assets)")
    if c["super_balance"] < c["income"]:        f.append("Under-funded superannuation")
    return f

def create_scenario(base, changes, name="Scenario"):
    s = base.copy(); s.update(changes); s["scenario_name"] = name; return s

def run_model(c):
    r = calculate_financials(c)
    return dict(results=r, risk_flags=assess_financial_risk(c, r))

def project_wealth(c, years=20, gr=0.07, sg=0.115, rep=20000):
    sup=float(c["super_balance"]); inv=float(c["investments"])
    cash=float(c["cash"]); debt=float(c["debt"])
    extra=max(0, c["income"]-c["expenses"]-rep)
    rows=[]
    for y in range(years+1):
        rows.append({"Year":y,"Net Worth":round(sup+inv+cash-debt)})
        if y<years:
            sup=sup*(1+gr)+c["income"]*sg
            inv=inv*(1+gr)+extra
            debt=max(0.0,debt-rep)
    return pd.DataFrame(rows).set_index("Year")

def project_balance_sheet(client, years=20, gr=0.07, sg=0.115, rep=20000):
    sup=float(client["super_balance"]); inv=float(client["investments"])
    cash_=float(client["cash"]); debt=float(client["debt"])
    extra=max(0,client["income"]-client["expenses"]-rep)
    rows=[]
    for y in range(years+1):
        assets=sup+inv+cash_
        rows.append({"Year":y,"Assets":round(assets),"Liabilities":round(debt),"Net Worth":round(assets-debt)})
        if y<years:
            sup=sup*(1+gr)+client["income"]*sg
            inv=inv*(1+gr)+extra
            debt=max(0.0,debt-rep)
    return pd.DataFrame(rows).set_index("Year")

def calc_pre_retirement(client, current_age, retirement_age,
        target_income, gr=0.07, sg=0.115, rep=20000):
    years_to_retire = max(0, retirement_age - current_age)
    sup   = float(client["super_balance"])
    inv   = float(client["investments"])
    cash_ = float(client["cash"])
    debt  = float(client["debt"])
    extra = max(0, client["income"] - client["expenses"] - rep)
    for y in range(years_to_retire):
        sup  = sup*(1+gr) + client["income"]*sg
        inv  = inv*(1+gr) + extra
        debt = max(0.0, debt - rep)
    projected_super     = round(sup)
    projected_total     = round(sup + inv + cash_)
    target_super_needed = round(target_income / 0.04)
    readiness_gap       = projected_super - target_super_needed
    annual_super_growth = client["income"] * sg
    if readiness_gap < 0 and annual_super_growth > 0:
        years_to_close = abs(readiness_gap) / annual_super_growth
    else:
        years_to_close = 0
    return {
        "years_to_retire":     years_to_retire,
        "projected_super":     projected_super,
        "projected_total":     projected_total,
        "target_super_needed": target_super_needed,
        "readiness_gap":       readiness_gap,
        "years_to_close":      round(years_to_close, 1),
        "on_track":            readiness_gap >= 0,
    }

def calc_retirement_drawdown(client,
    drawdown_rate=0.04, desired_income=80000,
    gr=0.07, years=25):
    total=(float(client["super_balance"])+
           float(client["investments"])+
           float(client["cash"]))
    sustainable=round(total*drawdown_rate)
    rows=[]; depleted=None
    for y in range(years+1):
        rows.append({"Year":y,"Assets":round(total),
            "Income":round(total*drawdown_rate)})
        if total<=0 and depleted is None:
            depleted=y
        if y<years:
            total=max(0,total*(1+gr)-total*drawdown_rate)
    return {
        "sustainable_income":sustainable,
        "desired_income":desired_income,
        "shortfall":sustainable-desired_income,
        "depleted_year":depleted,
        "on_track":depleted is None,
        "projection":pd.DataFrame(rows).set_index("Year"),
    }

def fmt(v):
    if v is None or (isinstance(v,float) and np.isnan(v)): return ""
    return f"${v:,.0f}" if v>=0 else f"(${abs(v):,.0f})"

def cc(v):
    if not isinstance(v,(int,float)) or np.isnan(v): return ""
    return "cell-pos" if v>0 else "cell-neg" if v<0 else ""

def render_insight(points):
    items = "".join(f"<li>{p}</li>" for p in points if p.strip())
    st.markdown(f"""<div style='background:#F8F7F4;
border-left:4px solid #1B2E4B;padding:1rem 1.25rem;
border-radius:0 8px 8px 0;font-size:13px;color:#1B2E4B;
margin-top:1rem;line-height:1.9'><span style='font-size:10px;
text-transform:uppercase;letter-spacing:.08em;color:#888;
display:block;margin-bottom:8px'>Planning observations</span>
<ul style='margin:0;padding-left:1.2rem'>{items}</ul></div>
<p style='font-size:11px;color:#aaa;margin-top:4px'>
For planner reference only — not personal financial advice.
</p>""", unsafe_allow_html=True)


def generate_insight(section, br, s1r, s2r,
        bp, s1p, s2p, s1_type, s2_type,
        yrs, income, expenses, rep,
        cash, debt, super_bal):
    if section == "cashflow":
        sr = br["savings_rate"]
        inv = max(0, income - expenses - rep)
        exp_pct = expenses / income * 100 if income else 0
        pts = []
        if sr >= 0.35:
            pts.append(f"Strong savings rate of {sr*100:.1f}% — well above the 10% minimum benchmark.")
        elif sr >= 0.2:
            pts.append(f"Savings rate of {sr*100:.1f}% is healthy and supports steady accumulation.")
        elif sr >= 0.1:
            pts.append(f"Savings rate of {sr*100:.1f}% meets minimum but leaves limited buffer.")
        else:
            pts.append(f"Savings rate of {sr*100:.1f}% is below the 10% benchmark — wealth accumulation constrained.")
        best_s = s1_type if s1r["surplus"] > s2r["surplus"] else s2_type
        best_v = max(s1r["surplus"], s2r["surplus"])
        if best_v > br["surplus"]:
            pts.append(f"{best_s} improves annual surplus to ${best_v:,.0f} — the strongest cash flow outcome.")
        pts.append(f"Expenses represent {exp_pct:.0f}% of gross income. ${inv:,.0f} available for reinvestment after debt repayment.")
        return pts
    elif section == "balance":
        dta = br["debt_to_assets"] * 100
        base_y = bp.iloc[-1]["Net Worth"]
        pts = []
        if dta > 200:
            pts.append(f"Debt is {dta:.0f}% of total assets — high leverage expected with a large mortgage at this stage.")
        elif dta > 70:
            pts.append(f"Debt is {dta:.0f}% of total assets — approaching the 70% risk threshold.")
        else:
            pts.append(f"Debt is {dta:.0f}% of total assets — within acceptable planning benchmarks.")
        crossover = next((int(y) for y, r in bp.iterrows() if r["Net Worth"] > 0), None)
        if crossover and crossover > 0:
            pts.append(f"Net worth projected to turn positive in year {crossover} as debt reduces and investments compound.")
        elif crossover == 0:
            pts.append("Net worth is already positive — assets exceed liabilities.")
        else:
            pts.append("Net worth remains negative throughout projection — review surplus and debt levels.")
        pts.append(f"Base case projects ${base_y/1e6:.2f}M net worth by year {yrs}.")
        return pts
    elif section == "scenarios":
        base_y = bp.iloc[-1]["Net Worth"]
        s1_y   = s1p.iloc[-1]["Net Worth"]
        s2_y   = s2p.iloc[-1]["Net Worth"]
        best_v = max(base_y, s1_y, s2_y)
        best_n = ("Base Case" if best_v == base_y
                  else s1_type if best_v == s1_y else s2_type)
        gap    = best_v - min(base_y, s1_y, s2_y)
        pts    = [f"{best_n} produces the strongest year {yrs} outcome at ${best_v/1e6:.2f}M."]
        if gap > 0:
            pts.append(f"Gap between best and worst scenario: ${gap/1e6:.2f}M — compounding amplifies early differences.")
        if s1_y > base_y and s2_y > base_y:
            pts.append("Both strategies improve on base case — consider which best matches client priorities.")
        elif s1_y > s2_y:
            pts.append(f"{s1_type} outperforms {s2_type} over the full projection horizon.")
        else:
            pts.append(f"{s2_type} outperforms {s1_type} over the full projection horizon.")
        return pts
    elif section == "summary":
        net    = br["net_position"]
        sur    = br["surplus"]
        sr     = br["savings_rate"]
        best_v = max(bp.iloc[-1]["Net Worth"],
                     s1p.iloc[-1]["Net Worth"],
                     s2p.iloc[-1]["Net Worth"])
        best_n = ("Base Case" if best_v == bp.iloc[-1]["Net Worth"]
                  else s1_type if best_v == s1p.iloc[-1]["Net Worth"]
                  else s2_type)
        pts = []
        if net < 0:
            pts.append(f"Currently in net deficit of ${abs(net):,.0f} — expected at accumulation stage with active mortgage.")
        else:
            pts.append(f"Net positive position of ${net:,.0f} — assets exceed liabilities.")
        pts.append(f"Annual surplus of ${sur:,.0f} supports accumulation at {sr*100:.1f}% savings rate.")
        pts.append(f"{best_n} produces strongest long-term outcome at ${best_v/1e6:.2f}M by year {yrs}.")
        if br["emergency_months"] < 3:
            pts.append("Priority action: build emergency buffer to 3 months of expenses before accelerating investment.")
        elif sr < 0.1:
            pts.append("Priority action: review expenses to improve savings rate above 10% minimum benchmark.")
        elif br["debt_to_assets"] > 0.7:
            pts.append("Priority action: monitor leverage and consider debt reduction to improve financial resilience.")
        else:
            pts.append("Priority action: review superannuation contribution strategy to maximise tax-effective wealth.")
        pts.append("These observations are for planner reference only and do not constitute personal financial advice.")
        return pts
    return []


plt.rcParams.update({"font.family":"sans-serif","font.size":10,
    "figure.facecolor":"white","axes.facecolor":"white",
    "axes.spines.top":False,"axes.spines.right":False,
    "axes.grid":True,"grid.alpha":.2,"grid.linestyle":"--"})
