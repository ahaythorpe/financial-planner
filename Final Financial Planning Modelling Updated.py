import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from datetime import date

APP_VERSION      = "1.0.0"
APP_BUILD_DATE   = "April 2026"
LEGISLATION_DATE = "2024-25 financial year"

st.set_page_config(
    page_title="Client Scenario Engine",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Palette ──────────────────────────────────────────────────────
NAVY     = "#1B2E4B"
S1_COLOR = "#6B3FA0"
TEAL     = "#1D9E75"
BG_POS   = "#E2F0D9"; TXT_POS = "#006100"
BG_NEG   = "#FCE4D6"; TXT_NEG = "#C00000"

EXTRA_COLORS = ["#2E86AB","#D85A30","#457B9D","#993556","#2D6A4F","#8B5E3C"]

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Serif+Display&display=swap');
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;}
.report-header{background:#1B2E4B;color:white;padding:1.5rem 2rem;border-radius:12px;margin-bottom:1.5rem;}
.report-header h1{font-family:'DM Serif Display',serif;font-size:1.8rem;font-weight:400;margin:0 0 0.2rem;color:white;}
.report-header p{margin:0;opacity:.7;font-size:.85rem;color:white;}
.metric-row{display:flex;gap:10px;margin-bottom:1.2rem;flex-wrap:wrap;}
.metric-card{background:white;border-radius:10px;padding:.9rem 1.1rem;flex:1;min-width:130px;border:.5px solid #E5E7EB;}
.metric-label{font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:#888;margin-bottom:5px;}
.metric-value{font-size:1.4rem;font-weight:600;font-variant-numeric:tabular-nums;}
.metric-value.pos{color:#006100;} .metric-value.neg{color:#C00000;}
.metric-sub{font-size:10px;color:#aaa;margin-top:3px;}
.badge{display:inline-block;padding:3px 10px;border-radius:20px;font-size:12px;font-weight:500;margin:2px 3px 2px 0;}
.badge-risk{background:#FCE4D6;color:#C00000;} .badge-ok{background:#E2F0D9;color:#006100;}
.word-table{width:100%;border-collapse:collapse;font-size:13px;background:white;}
.word-table th{background:#F2F2F2;color:#1B2E4B;font-weight:600;border-top:2px solid #1B2E4B;border-bottom:2px solid #1B2E4B;padding:9px 13px;text-align:right;font-size:11px;text-transform:uppercase;letter-spacing:.04em;}
.word-table th:first-child{text-align:left;}
.word-table td{border-bottom:.5px solid #E5E7EB;padding:8px 13px;text-align:right;font-variant-numeric:tabular-nums;color:#1B2E4B;}
.word-table td:first-child{text-align:left;}
.word-table tr.total td{font-weight:600;border-top:2px solid #1B2E4B;border-bottom:2px solid #1B2E4B;}
.word-table tr.divider td{border:none;padding:2px 0;}
.cell-pos{background:#E2F0D9!important;color:#006100!important;font-weight:500;}
.cell-neg{background:#FCE4D6!important;color:#C00000!important;font-weight:500;}
.cell-zero{background:#F5F5F5!important;color:#999!important;}
.demo-banner{background:#EFF6FF;border:1px solid #BFDBFE;border-radius:8px;padding:.75rem 1rem;margin-bottom:1rem;font-size:13px;color:#1E40AF;}
</style>
""", unsafe_allow_html=True)

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

def cc(v, zero_neutral=True):
    if not isinstance(v,(int,float)) or np.isnan(v): return ""
    if v > 0: return "cell-pos"
    if v < 0: return "cell-neg"
    return "" if zero_neutral else "cell-pos"

def render_insight(points):
    items = "".join(f"<li style='margin-bottom:8px'>{p}</li>" for p in points if p.strip())
    st.markdown(f"""<div style='background:#F8F7F4;
border-left:4px solid #1B2E4B;padding:1rem 1.25rem;
border-radius:0 8px 8px 0;font-size:16px;color:#1B2E4B;
margin-top:1rem;line-height:1.9'><span style='font-size:12px;
text-transform:uppercase;letter-spacing:.08em;color:#888;
display:block;margin-bottom:8px'>Planning observations</span>
<ul style='margin:0;padding-left:1.2rem'>{items}</ul></div>
<p style='font-size:13px;color:#aaa;margin-top:4px'>
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
            pts.append(f"Both strategies beat base case — {s1_type} by ${(s1_y-base_y)/1e6:.2f}M, {s2_type} by ${(s2_y-base_y)/1e6:.2f}M at year {yrs}.")
        elif s1_y > s2_y:
            pts.append(f"{s1_type} outperforms {s2_type} by ${(s1_y-s2_y)/1e6:.2f}M at year {yrs}.")
        else:
            pts.append(f"{s2_type} outperforms {s1_type} by ${(s2_y-s1_y)/1e6:.2f}M at year {yrs}.")
        base_sr = br["savings_rate"]
        s1_sr = s1r["savings_rate"]
        s2_sr = s2r["savings_rate"]
        best_sr_n = s1_type if s1_sr > s2_sr else s2_type
        best_sr_v = max(s1_sr, s2_sr)
        if best_sr_v > base_sr:
            pts.append(f"{best_sr_n} improves savings rate from {base_sr*100:.1f}% to {best_sr_v*100:.1f}% — an extra ${(best_sr_v-base_sr)*income:,.0f} reinvested annually.")
        base_dta = br["debt_to_assets"]*100
        s1_dta = s1r["debt_to_assets"]*100
        s2_dta = s2r["debt_to_assets"]*100
        best_dta_n = s1_type if s1_dta < s2_dta else s2_type
        best_dta_v = min(s1_dta, s2_dta)
        if best_dta_v < base_dta:
            pts.append(f"{best_dta_n} reduces leverage from {base_dta:.0f}% to {best_dta_v:.0f}% debt-to-assets — improving financial resilience.")
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
    elif section == "soa_intro":
        net    = br["net_position"]
        sur    = br["surplus"]
        sr     = br["savings_rate"]
        em     = br["emergency_months"]
        dta    = br["debt_to_assets"] * 100
        best_v = max(bp.iloc[-1]["Net Worth"], s1p.iloc[-1]["Net Worth"], s2p.iloc[-1]["Net Worth"])
        best_n = ("Base Case" if best_v == bp.iloc[-1]["Net Worth"]
                  else s1_type if best_v == s1p.iloc[-1]["Net Worth"] else s2_type)
        stage  = "accumulation" if income > 0 else "retirement drawdown"
        intro  = (
            f"{client_name} is currently in the {stage} phase with a "
            f"{'net deficit' if net < 0 else 'net positive position'} of {fmt(abs(net))}. "
            f"Annual income of {fmt(income)} generates a surplus of {fmt(sur)}, "
            f"representing a savings rate of {sr*100:.1f}%. "
        )
        if em < 3:
            intro += f"Emergency reserves stand at {em:.1f} months — below the recommended 3-month minimum. "
        if dta > 70:
            intro += f"Debt represents {dta:.0f}% of total assets, reflecting an active mortgage position. "
        intro += (
            f"Across the scenarios modelled, {best_n} produces the strongest long-term outcome, "
            f"projecting {fmt(best_v)} in net worth by year {yrs}. "
            f"This analysis is based on a {gr*100:.1f}% annual growth rate, "
            f"{sg*100:.1f}% superannuation guarantee, and ${rep:,} annual debt repayment."
        )
        return [intro]
    elif section == "soa_conclusion":
        net    = br["net_position"]
        sur    = br["surplus"]
        sr     = br["savings_rate"]
        em     = br["emergency_months"]
        dta    = br["debt_to_assets"] * 100
        best_v = max(bp.iloc[-1]["Net Worth"], s1p.iloc[-1]["Net Worth"], s2p.iloc[-1]["Net Worth"])
        best_n = ("Base Case" if best_v == bp.iloc[-1]["Net Worth"]
                  else s1_type if best_v == s1p.iloc[-1]["Net Worth"] else s2_type)
        pts = []
        pts.append(
            f"Based on the modelling presented, {client_name}'s financial position is "
            f"{'developing as expected for the accumulation stage' if net < 0 else 'healthy with assets exceeding liabilities'}. "
            f"The {best_n} strategy is recommended as the strongest long-term pathway, "
            f"projecting {fmt(best_v)} by year {yrs}."
        )
        if em < 3:
            pts.append(f"The most immediate priority is building emergency reserves from {em:.1f} months to 3 months (approximately {fmt(int(expenses/4))}).")
        if sr < 0.15:
            pts.append(f"A savings rate of {sr*100:.1f}% limits accumulation velocity. Reviewing discretionary expenses or increasing income should be explored.")
        if dta > 70:
            pts.append(f"Leverage of {dta:.0f}% is within expected range for this life stage but warrants monitoring as interest rates change.")
        pts.append("All projections are indicative only. This analysis does not constitute personal financial advice. The client should consider obtaining a Statement of Advice from a licensed financial adviser.")
        return pts
    return []


plt.rcParams.update({"font.family":"sans-serif","font.size":10,
    "figure.facecolor":"white","axes.facecolor":"white",
    "axes.spines.top":False,"axes.spines.right":False,
    "axes.grid":True,"grid.alpha":.2,"grid.linestyle":"--"})

# ── Sidebar ──────────────────────────────────────────────────────
with st.sidebar:
    mode = st.radio("Client mode", ["New client","Sarah & Daniel (demo)"], horizontal=True)
    demo_mode = mode == "Sarah & Daniel (demo)"
    st.markdown("---")

    PRESETS = {
        "Sarah & Daniel":  dict(income=160000,expenses=95000,super_balance=120000,investments=40000,cash=15000,debt=420000),
        "Young professional": dict(income=90000,expenses=60000,super_balance=25000,investments=5000,cash=8000,debt=0),
        "Pre-retirement couple": dict(income=200000,expenses=110000,super_balance=450000,investments=120000,cash=40000,debt=150000),
        "First home buyer": dict(income=110000,expenses=75000,super_balance=45000,investments=10000,cash=30000,debt=550000),
        "Custom": None,
    }
    if not demo_mode:
        preset = st.selectbox("Quick preset", list(PRESETS.keys()))
        p = PRESETS[preset]
    else:
        p = DEMO

    client_name = st.text_input("Client name", value=DEMO["name"] if demo_mode else "New Client", disabled=demo_mode)
    age_1 = st.number_input("Client 1 age", min_value=18, max_value=85, value=35, step=1, disabled=demo_mode)
    age_2 = st.number_input("Partner age (0 = no partner)", min_value=0, max_value=85, value=37, step=1, disabled=demo_mode)
    older_age = max(age_1, age_2) if age_2 > 0 else age_1

    if older_age >= 50:
        st.markdown("---")
        st.markdown("<div style='font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:#aaa;margin:8px 0 4px'>Pre-retirement inputs</div>", unsafe_allow_html=True)
        retirement_age = st.number_input("Target retirement age", min_value=55, max_value=75,
            value=67, step=1, disabled=demo_mode)
        target_income = st.number_input("Target retirement income ($ p.a.)", min_value=0,
            step=5000, value=80000, disabled=demo_mode)
    else:
        retirement_age = 67
        target_income  = 80000
    if older_age >= 65:
        drawdown_rate = st.slider("Drawdown rate (%)",
            2.0, 8.0, 4.0, 0.5,
            disabled=demo_mode) / 100
        desired_income = st.number_input(
            "Desired retirement income ($)",
            min_value=0, step=5000,
            value=80000, disabled=demo_mode)
    else:
        drawdown_rate  = 0.04
        desired_income = 80000

    st.markdown("<div style='font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:#aaa;margin:8px 0 4px'>Income & Expenses</div>", unsafe_allow_html=True)
    income   = st.number_input("Income ($)",   min_value=0,step=5000,  value=p["income"]        if p else 160000, disabled=demo_mode)
    expenses = st.number_input("Expenses ($)", min_value=0,step=1000,  value=p["expenses"]      if p else 95000,  disabled=demo_mode)

    st.markdown("<div style='font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:#aaa;margin:8px 0 4px'>Assets</div>", unsafe_allow_html=True)
    super_bal = st.number_input("Superannuation ($)", min_value=0,step=5000, value=p["super_balance"] if p else 120000, disabled=demo_mode)
    invest    = st.number_input("Investments ($)",    min_value=0,step=5000, value=p["investments"]   if p else 40000,  disabled=demo_mode)
    cash      = st.number_input("Cash & savings ($)", min_value=0,step=1000, value=p["cash"]          if p else 15000,  disabled=demo_mode)

    st.markdown("<div style='font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:#aaa;margin:8px 0 4px'>Liabilities</div>", unsafe_allow_html=True)
    debt = st.number_input("Mortgage / debt ($)", min_value=0,step=5000, value=p["debt"] if p else 420000, disabled=demo_mode)

    with st.expander("Model parameters"):
        gr  = st.slider("Growth rate (% p.a.)", 1.0,15.0,7.0,0.5) / 100
        sg  = st.slider("SG rate (%)", 5.0,15.0,11.5,0.5) / 100
        rep = st.slider("Annual debt repayment ($)", 0,100000,20000,1000)
        yrs = st.slider("Projection years", 5,40,20,5)

    st.markdown("---")
    st.markdown("<div style='font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:#aaa;margin:8px 0 4px'>Scenario 1</div>", unsafe_allow_html=True)
    s1_type = st.selectbox("Strategy", ["Income Improvement","Debt Reduction","Super Boost","Custom"], key="s1t")
    if s1_type=="Income Improvement":
        s1c = {"income": st.number_input("S1 income ($)",value=180000,step=5000,key="s1i"), "expenses": st.number_input("S1 expenses ($)",value=90000,step=1000,key="s1e")}
    elif s1_type=="Debt Reduction":
        s1c = {"debt": st.number_input("S1 debt ($)",value=350000,step=5000,key="s1d"), "cash": st.number_input("S1 cash ($)",value=10000,step=1000,key="s1c")}
    elif s1_type=="Super Boost":
        s1c = {"super_balance": st.number_input("S1 super ($)",value=int(super_bal*1.2),step=5000,key="s1s")}
    else:
        s1c = {"income":st.number_input("S1 income ($)",value=income,step=5000,key="s1ci"),
               "expenses":st.number_input("S1 expenses ($)",value=expenses,step=1000,key="s1ce"),
               "debt":st.number_input("S1 debt ($)",value=debt,step=5000,key="s1cd"),
               "cash":st.number_input("S1 cash ($)",value=cash,step=1000,key="s1cc")}

    st.markdown("<div style='font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:#aaa;margin:8px 0 4px'>Scenario 2</div>", unsafe_allow_html=True)
    s2_type = st.selectbox("Strategy ", ["Debt Reduction","Income Improvement","Super Boost","Custom"], key="s2t")
    if s2_type=="Debt Reduction":
        s2c = {"debt": st.number_input("S2 debt ($)",value=350000,step=5000,key="s2d"), "cash": st.number_input("S2 cash ($)",value=10000,step=1000,key="s2c")}
    elif s2_type=="Income Improvement":
        s2c = {"income": st.number_input("S2 income ($)",value=180000,step=5000,key="s2i"), "expenses": st.number_input("S2 expenses ($)",value=90000,step=1000,key="s2e")}
    elif s2_type=="Super Boost":
        s2c = {"super_balance": st.number_input("S2 super ($)",value=int(super_bal*1.2),step=5000,key="s2s")}
    else:
        s2c = {"income":st.number_input("S2 income ($)",value=income,step=5000,key="s2ci"),
               "expenses":st.number_input("S2 expenses ($)",value=expenses,step=1000,key="s2ce"),
               "debt":st.number_input("S2 debt ($)",value=debt,step=5000,key="s2cd"),
               "cash":st.number_input("S2 cash ($)",value=cash,step=1000,key="s2cc")}

    st.markdown("---")
    if "extra_scenarios" not in st.session_state:
        st.session_state.extra_scenarios = []
    if st.button("+ Add scenario"):
        st.session_state.extra_scenarios.append({"name":f"Scenario {len(st.session_state.extra_scenarios)+3}","type":"Custom","changes":{}})
    extras = []
    for idx, es in enumerate(st.session_state.extra_scenarios):
        st.markdown(f"<div style='font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:#aaa;margin:8px 0 4px'>Scenario {idx+3}</div>", unsafe_allow_html=True)
        ename = st.text_input("Name", value=es["name"], key=f"en{idx}")
        etype = st.selectbox("Strategy  ", ["Custom","Income Improvement","Debt Reduction","Super Boost"], key=f"et{idx}")
        if etype=="Income Improvement":
            ec={"income":st.number_input("Income ($)",value=income,step=5000,key=f"ei{idx}"),"expenses":st.number_input("Expenses ($)",value=expenses,step=1000,key=f"ee{idx}")}
        elif etype=="Debt Reduction":
            ec={"debt":st.number_input("Debt ($)",value=debt,step=5000,key=f"ed{idx}"),"cash":st.number_input("Cash ($)",value=cash,step=1000,key=f"ec{idx}")}
        elif etype=="Super Boost":
            ec={"super_balance":st.number_input("Super ($)",value=int(super_bal*1.2),step=5000,key=f"es{idx}")}
        else:
            ec={"income":st.number_input("Income ($) ",value=income,step=5000,key=f"eci{idx}"),
                "expenses":st.number_input("Expenses ($) ",value=expenses,step=1000,key=f"ece{idx}"),
                "debt":st.number_input("Debt ($) ",value=debt,step=5000,key=f"ecd{idx}"),
                "cash":st.number_input("Cash ($) ",value=cash,step=1000,key=f"ecc{idx}")}
        if st.button("Remove", key=f"rm{idx}"):
            st.session_state.extra_scenarios.pop(idx); st.rerun()
        extras.append(create_scenario({"name":client_name,"income":income,"expenses":expenses,
            "super_balance":super_bal,"investments":invest,"cash":cash,"debt":debt}, ec, name=ename))

    st.markdown("---")
    st.caption(f"v{APP_VERSION} · {APP_BUILD_DATE}")
    st.caption(f"Legislation: {LEGISLATION_DATE}")
    if date.today() >= date(2025, 7, 1):
        st.warning("SG rate has risen to 12%. Update Model Parameters.")

# ── Run model ────────────────────────────────────────────────────
base_client = dict(name=client_name,income=income,expenses=expenses,
    super_balance=super_bal,investments=invest,cash=cash,debt=debt)
s1 = create_scenario(base_client, s1c, name=f"Scenario 1 — {s1_type}")
s2 = create_scenario(base_client, s2c, name=f"Scenario 2 — {s2_type}")
bo = run_model(base_client); br = bo["results"]
s1o= run_model(s1);          s1r= s1o["results"]
s2o= run_model(s2);          s2r= s2o["results"]
bp = project_wealth(base_client,yrs,gr,sg,rep)
s1p= project_wealth(s1,yrs,gr,sg,rep)
s2p= project_wealth(s2,yrs,gr,sg,rep)
extra_outputs  = [(e, run_model(e), project_wealth(e,yrs,gr,sg,rep)) for e in extras]
bs_proj = project_balance_sheet(base_client, yrs, gr, sg, rep)
all_scenarios  = [(f"Scenario 1 — {s1_type}",s1r,s1p,S1_COLOR)] + \
                 [(f"Scenario 2 — {s2_type}",s2r,s2p,TEAL)] + \
                 [(e["scenario_name"],eo["results"],ep,EXTRA_COLORS[i%len(EXTRA_COLORS)]) for i,(e,eo,ep) in enumerate(extra_outputs)]

# ── Header ───────────────────────────────────────────────────────
if demo_mode:
    st.markdown('<div class="demo-banner">Viewing Sarah &amp; Daniel demonstration case — inputs are locked. Switch to New Client to enter your own figures.</div>', unsafe_allow_html=True)

st.markdown(f"""
<div class="report-header">
  <h1>Client Scenario Engine</h1>
  <p>{client_name} &nbsp;·&nbsp; Age {age_1}/{age_2} &nbsp;·&nbsp; {date.today().strftime('%d %B %Y')} &nbsp;·&nbsp; Australian accumulation phase model &nbsp;·&nbsp; v{APP_VERSION}</p>
</div>""", unsafe_allow_html=True)

# ── Tabs ─────────────────────────────────────────────────────────
t_about, t_demo, t_dash, t_scen, t_shock, t_proj, t_life, t_leg, t_model, t_report = st.tabs([
    "About", "Demo", "Client Dashboard", "Scenario Analysis",
    "Shock Analysis", "Projection", "Life Stage",
    "Legislation", "Model & Limitations", "Report"])

# ════════════════════════════════════════════════════════════════
# ABOUT TAB
# ════════════════════════════════════════════════════════════════
with t_about:
    st.markdown("### Client Scenario Engine")
    st.caption("Financial decision simulator for advice conversations · Not financial advice")

    with st.expander("What this engine does and who it's for", expanded=True):
        st.markdown("""
The Client Scenario Engine is a decision simulator built for financial advice conversations.
It models an Australian client's financial journey across three life phases:

- **Accumulation** — building wealth while working
- **Pre-retirement** — assessing readiness to stop working
- **Retirement drawdown** — managing sustainable income from accumulated assets

**Why it exists:** Financial planning concepts are often explained in isolation.
This engine shows how phases connect — how decisions made at 35 compound into outcomes at 65 —
so advisers can illustrate trade-offs in real time during client conversations.

**Built for advisers, not consumers.** This is a scenario modelling tool, not a Statement of Advice.
All outputs are indicative only and do not constitute personal financial advice.

**Sarah & Daniel** are a locked demonstration case illustrating a typical Australian couple
in the accumulation phase. Switch to New Client to enter your own figures.
        """)

    with st.expander("How to use this tool"):
        st.markdown("""
1. **Select client mode** in the sidebar — New Client or Sarah & Daniel demo
2. **Enter the client's details** — all inputs are whole dollar amounts
3. **All outputs update automatically** — no run button needed
4. **Green cells** = positive or healthy · **Red cells** = negative or flagged
5. **Compare scenarios** using the strategy dropdowns in the sidebar
6. **Add extra scenarios** with the + Add Scenario button
7. **Adjust model parameters** in the expander — growth rate, SG rate, repayment, years
8. **Run shock analysis** in the Shock Analysis tab
9. **Download report** from the Report tab
        """)

    with st.expander("The three life phases — accumulation, pre-retirement, retirement"):
        st.markdown("""
**ACCUMULATION PHASE** *(currently modelled)*

Client is working and building wealth. Each year:

| Component | Formula |
|---|---|
| Super (year end) | Prior balance × 1.07 + income × SG rate |
| Portfolio (year end) | Prior balance × 1.07 + reinvested surplus |
| Reinvested surplus | Income − expenses − debt repayment |
| Debt (year end) | Prior balance − repayment (minimum zero) |
| Net worth | Super + portfolio + cash − debt |

When debt reaches zero the repayment amount adds to reinvested surplus and accelerates growth.
This is why projection lines steepen in later years.

---

**PRE-RETIREMENT PHASE** *(unlocks at age 50)*

Client is still working but retirement is within 15 years. Readiness check added on top of accumulation.

Target super at retirement = desired income ÷ 4%
*(Example: $80,000 target ÷ 0.04 = $2,000,000 needed)*

The 4% is the internationally recognised safe withdrawal rate — indicative only, not a guarantee.

---

**RETIREMENT DRAWDOWN PHASE** *(unlocks at age 65)*

Client has stopped working. Model flips from accumulation to drawdown.

Each year: Assets × 1.07 − income drawn. Model runs to age 90 or asset depletion, whichever first.

**IMPORTANT:** Age Pension is not modelled. Australian clients may be eligible from age 67.
This must be assessed separately via Services Australia.
        """)

    with st.expander("Risk flag thresholds — exact triggers"):
        st.markdown("""
| Flag | Triggers when | Planner should consider |
|---|---|---|
| Low savings rate | Surplus ÷ income below 10% | Expense review, income strategy, debt consolidation |
| Low emergency buffer | Cash below expenses × 20% (~2.4 months) | Cash flow timing, liquidity risk, offset accounts |
| High leverage | Debt above total assets × 70% | LVR, serviceability buffer, rate sensitivity |
| Under-funded super | Super balance below annual income | Age context, salary sacrifice, catch-up rules |

These are planning benchmarks — they flag a condition worth discussing, not a financial emergency.
        """)

    with st.expander("How to enter a new client"):
        st.markdown("""
Sarah and Daniel are locked and cannot be edited. Switch to **New Client** in the sidebar.

**Input checklist:**
- Use gross annual income figures
- Include all household expenses including discretionary
- Include all debt not just primary mortgage
- Cross-check super balance against member statement
- Use actual P&I repayment for debt repayment field

**Adjust growth rate per risk profile:**

| Profile | Growth rate to use |
|---|---|
| Conservative | 5% |
| Balanced (default) | 7% |
| Growth | 8–9% |
        """)

# ════════════════════════════════════════════════════════════════
# DEMO TAB
# ════════════════════════════════════════════════════════════════
with t_demo:
    st.markdown("### Model Demo — What Each Phase Shows")
    st.caption("This page walks through each phase of the model using fixed demo clients. Switch to New Client in the sidebar to use your own figures.")

    # ── PHASE 1 — ACCUMULATION ───────────────────────────────────
    st.markdown("---")
    st.markdown("## Phase 1 — Accumulation (age 18–49)")
    st.markdown("""
**Who this applies to:** Any client who is working and building wealth before retirement.

**What the model does:**
- Super grows at your selected growth rate + SG contributions (currently 11.5%)
- Portfolio grows from reinvested surplus (income − expenses − debt repayment)
- Debt reduces by fixed annual repayment
- Net worth = super + portfolio + cash − debt

**Demo client — Sarah & Daniel, age 35/37:**
""")
    demo_acc = dict(name="Sarah & Daniel", income=160000, expenses=95000,
                    super_balance=120000, investments=40000, cash=15000, debt=420000)
    acc_r = calculate_financials(demo_acc)
    acc_p = project_wealth(demo_acc, 20, 0.07, 0.115, 20000)

    ac1, ac2, ac3, ac4 = st.columns(4)
    ac1.metric("Net Position", fmt(acc_r["net_position"]))
    ac2.metric("Annual Surplus", fmt(acc_r["surplus"]))
    ac3.metric("Savings Rate", f"{acc_r['savings_rate']*100:.1f}%")
    ac4.metric("Emergency Buffer", f"{acc_r['emergency_months']:.1f} months")

    fig_a, ax_a = plt.subplots(figsize=(14, 5))
    ax_a.plot(acc_p.index, acc_p["Net Worth"]/1e6, color=NAVY, linewidth=2.5)
    ax_a.axhline(0, color="#ccc", linewidth=0.8)
    ax_a.fill_between(acc_p.index, 0, acc_p["Net Worth"]/1e6, where=acc_p["Net Worth"]>0, alpha=0.07, color=NAVY)
    ax_a.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"${x:.1f}M"))
    ax_a.set_xlabel("Year", color=NAVY)
    ax_a.set_title("Accumulation Phase — 20-Year Net Worth Projection", fontweight="bold", color=NAVY, fontsize=11)
    cx_a = next((y for y in acc_p.index if acc_p.loc[y,"Net Worth"]>0), None)
    if cx_a:
        ax_a.axvline(cx_a, color=TEAL, linewidth=1, linestyle=":")
        ax_a.annotate(f"Net positive year {cx_a}", xy=(cx_a,0), xytext=(cx_a+0.5, acc_p["Net Worth"].max()/1e6*0.15), fontsize=8, color=TEAL, arrowprops=dict(arrowstyle="->", color=TEAL, lw=1))
    ax_a.annotate(f"  ${acc_p.iloc[-1]['Net Worth']/1e6:.2f}M", xy=(acc_p.index[-1], acc_p.iloc[-1]["Net Worth"]/1e6), fontsize=9, fontweight="bold", color=NAVY, va="center")
    plt.tight_layout(); st.pyplot(fig_a); plt.close()
    st.caption("Debt is $420,000. Net worth turns negative early then accelerates as debt clears and compounding takes over.")

    # ── PHASE 2 — PRE-RETIREMENT ─────────────────────────────────
    st.markdown("---")
    st.markdown("## Phase 2 — Pre-Retirement Readiness (age 50+)")
    st.markdown("""
**Who this applies to:** Clients within 15 years of their target retirement age.

**What the model does:**
- Projects super balance forward to retirement age at selected growth rate + SG
- Calculates target super needed = desired retirement income ÷ 4% (safe withdrawal rate)
- Shows readiness gap and years of extra contributions needed to close it
- Does NOT include Age Pension, catch-up contributions, or salary sacrifice optimisation

**Demo client — Margaret, age 55, retiring at 67, target income $80,000 p.a.:**
""")
    demo_pre = dict(name="Margaret", income=120000, expenses=70000,
                    super_balance=380000, investments=60000, cash=25000, debt=180000)
    pre_r = calc_pre_retirement(demo_pre, 55, 67, 80000, 0.07, 0.115, 15000)

    pc1, pc2, pc3 = st.columns(3)
    pc1.metric("Projected super at 67", fmt(pre_r["projected_super"]))
    pc2.metric("Target needed (÷4%)", fmt(pre_r["target_super_needed"]))
    gap_v = pre_r["readiness_gap"]
    pc3.metric("Readiness gap", fmt(gap_v), delta="On track" if gap_v>=0 else f"{pre_r['years_to_close']:.1f} yrs to close", delta_color="normal" if gap_v>=0 else "inverse")

    if pre_r["on_track"]:
        st.success(f"Margaret is on track. Projected super exceeds target by {fmt(pre_r['readiness_gap'])}.")
    else:
        st.error(f"Shortfall of {fmt(abs(pre_r['readiness_gap']))}. At current SG rate approximately {pre_r['years_to_close']:.1f} additional years needed.")
    st.markdown("""
    <div style='background:#E2F0D9;border-radius:10px;padding:1rem 1.25rem;margin:12px 0;border:1px solid #9FE1CB'>
    <div style='font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:#0F6E56;margin-bottom:6px'>About this demo — Pre-Retirement Phase</div>
    <div style='font-size:14px;color:#1B2E4B;line-height:1.8'>
    These are <strong>fixed demo figures for Margaret, age 55</strong> — they do not change with the sidebar.<br>
    This phase activates automatically when you set <strong>client age to 50+</strong> in the Life Stage tab.<br>
    The model projects super forward to retirement age using growth rate + SG contributions, then compares against the <strong>4% rule target</strong> (desired income ÷ 0.04 = super needed).<br>
    <strong>Target:</strong> $80,000 ÷ 4% = $2,000,000 needed. The gap or surplus shown is the readiness check.<br>
    <strong>Not included:</strong> Age Pension, catch-up contributions, salary sacrifice, contributions tax.<br>
    Switch to <strong>New Client</strong> and set age 50+ to run this for a real client.
    </div></div>
    """, unsafe_allow_html=True)

    pre_p = project_wealth(demo_pre, 12, 0.07, 0.115, 15000)
    fig_p, ax_p = plt.subplots(figsize=(14, 5))
    ax_p.plot(pre_p.index, pre_p["Net Worth"]/1e6, color=S1_COLOR, linewidth=2.5, label="Net Worth")
    ax_p.axhline(pre_r["target_super_needed"]/1e6, color=TEAL, linewidth=1.5, linestyle="--", label=f"Super target ${pre_r['target_super_needed']/1e6:.2f}M")
    ax_p.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"${x:.1f}M"))
    ax_p.set_xlabel("Year (0 = age 55, 12 = age 67)", color=NAVY)
    ax_p.set_title("Pre-Retirement — Net Worth vs Target", fontweight="bold", color=NAVY, fontsize=11)
    ax_p.legend(fontsize=9, framealpha=0.9)
    plt.tight_layout(); st.pyplot(fig_p); plt.close()

    # ── PHASE 3 — RETIREMENT DRAWDOWN ────────────────────────────
    st.markdown("---")
    st.markdown("## Phase 3 — Retirement Drawdown (age 65+)")
    st.markdown("""
**Who this applies to:** Clients who have stopped working and are drawing down accumulated assets.

**What the model does:**
- Applies 4% drawdown rule: assets × 4% = sustainable annual income
- Projects assets year by year: `assets × 1.07 − income drawn`
- Shows asset depletion year if desired income exceeds sustainable income
- Age Pension NOT modelled — must be assessed separately

**Demo client — Robert & Jan, age 67, $1.2M total assets, desired income $90,000 p.a.:**
""")
    demo_ret = dict(name="Robert & Jan", income=0, expenses=90000,
                    super_balance=900000, investments=200000, cash=100000, debt=0)
    ret_r = calc_retirement_drawdown(demo_ret, drawdown_rate=0.04, desired_income=90000, gr=0.07, years=25)

    rc1, rc2, rc3 = st.columns(3)
    rc1.metric("Sustainable income (4%)", fmt(ret_r["sustainable_income"]))
    rc2.metric("Desired income", fmt(ret_r["desired_income"]))
    shortfall = ret_r["shortfall"]
    rc3.metric("Surplus / shortfall", fmt(shortfall), delta="Sustainable" if shortfall>=0 else "Shortfall", delta_color="normal" if shortfall>=0 else "inverse")

    if ret_r["on_track"]:
        st.success("Assets sufficient — no depletion projected over 25-year drawdown period.")
    else:
        st.error(f"Assets depleted in year {ret_r['depleted_year']}. Consider reducing drawdown rate or supplementing with Age Pension.")

    ret_proj = ret_r["projection"]
    fig_r, ax_r = plt.subplots(figsize=(14, 5))
    ax_r.plot(ret_proj.index, ret_proj["Assets"]/1e6, color=NAVY, linewidth=2.5, label="Remaining assets")
    ax_r.axhline(0, color="#C00000", linewidth=0.8, linestyle="--")
    ax_r.fill_between(ret_proj.index, 0, ret_proj["Assets"]/1e6, alpha=0.07, color=NAVY)
    ax_r.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"${x:.1f}M"))
    ax_r.set_xlabel("Year in retirement", color=NAVY)
    ax_r.set_title("Retirement Drawdown — Asset Depletion Projection", fontweight="bold", color=NAVY, fontsize=11)
    ax_r.legend(fontsize=9, framealpha=0.9)
    plt.tight_layout(); st.pyplot(fig_r); plt.close()
    st.markdown("""
    <div style='background:#FAEEDA;border-radius:10px;padding:1rem 1.25rem;margin:12px 0;border:1px solid #FAC775'>
    <div style='font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:#854F0B;margin-bottom:6px'>About this demo — Retirement Drawdown Phase</div>
    <div style='font-size:14px;color:#1B2E4B;line-height:1.8'>
    These are <strong>fixed demo figures for Robert & Jan, age 67</strong> — they do not change with the sidebar.<br>
    This phase activates automatically when you set <strong>client age to 65+</strong> in the Life Stage tab.<br>
    The model runs assets through <strong>assets × 1.07 − income drawn</strong> each year until depletion or 25 years.<br>
    <strong>4% rule:</strong> $1.2M × 4% = $48,000 sustainable income. Robert & Jan want $90,000 — a $42,000 shortfall.<br>
    The chart shows how long assets last at that drawdown rate before depletion.<br>
    <strong>Not included:</strong> Age Pension (critical for this client), inflation, minimum drawdown rates, tax.<br>
    Switch to <strong>New Client</strong> and set age 65+ to run this for a real client.
    </div></div>
    """, unsafe_allow_html=True)

    # ── PHASE 4 — PENSION PHASE (PARTIAL) ────────────────────────
    st.markdown("---")
    st.markdown("## Phase 4 — Pension Phase (partial)")

    MIN_DRAWDOWN = {(0,64):0.04,(65,74):0.05,(75,79):0.06,(80,84):0.07,(85,89):0.09,(90,94):0.11,(95,120):0.14}
    def get_min_drawdown(age):
        for (lo,hi),rate in MIN_DRAWDOWN.items():
            if lo <= age <= hi: return rate
        return 0.04

    TRANSFER_BALANCE_CAP = 1_900_000

    if older_age >= 60:
        st.markdown(f"**Client age {older_age} — pension phase rules apply**")
        pension_assets = float(super_bal) + float(invest) + float(cash)
        min_dr = get_min_drawdown(older_age)
        min_income = round(pension_assets * min_dr)
        tbc_excess = max(0, pension_assets - TRANSFER_BALANCE_CAP)

        pp1, pp2, pp3 = st.columns(3)
        pp1.metric("Total pension assets", fmt(round(pension_assets)))
        pp2.metric(f"Min drawdown at age {older_age} ({min_dr*100:.0f}%)", fmt(min_income))
        pp3.metric("Transfer Balance Cap excess", fmt(round(tbc_excess)), delta="Within cap" if tbc_excess==0 else "Exceeds cap — review required", delta_color="normal" if tbc_excess==0 else "inverse")

        if tbc_excess > 0:
            st.error(f"Assets of {fmt(round(pension_assets))} exceed the Transfer Balance Cap of $1.9M by {fmt(round(tbc_excess))}. Excess must remain in accumulation phase (taxed at 15%) or be withdrawn. Seek licensed advice.")
        else:
            st.success(f"Assets are within the $1.9M Transfer Balance Cap. All {fmt(round(pension_assets))} can move to pension phase at 0% earnings tax.")

        st.caption(f"Minimum drawdown at age {older_age} is {min_dr*100:.0f}% = {fmt(min_income)} p.a. This is a legislative minimum — actual drawdown may be higher based on lifestyle needs.")

        st.markdown("""
**What is and is not modelled here:**
- ✓ Minimum drawdown rate calculated by age
- ✓ Transfer Balance Cap check against current assets
- ✗ Tax saving from 15% → 0% earnings tax not quantified
- ✗ Age Pension interaction not modelled
- ✗ Death benefit nominations not modelled
- ✗ Estate planning not modelled
        """)
    else:
        st.markdown("""
    <div style='background:#FCE4D6;border-radius:10px;padding:1rem 1.25rem;margin:12px 0;border:1px solid #F0997B'>
    <div style='font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:#993C1D;margin-bottom:6px'>About this demo — Pension Phase (partial)</div>
    <div style='font-size:14px;color:#1B2E4B;line-height:1.8'>
    This phase is <strong>partially built</strong> — minimum drawdown rates and Transfer Balance Cap check are live.<br>
    It activates automatically when you set <strong>client age to 60+</strong> in the Life Stage tab.<br>
    <strong>What works now:</strong> minimum drawdown % by age, Transfer Balance Cap check against $1.9M.<br>
    <strong>Not yet built:</strong> 0% earnings tax in pension phase, Age Pension means testing, death benefits, estate planning.<br>
    Full pension phase modelling requires significant additional build — see Model & Limitations tab for detail.<br>
    Switch to <strong>New Client</strong> and set age 60+ to see the partial pension phase for a real client.
    </div></div>
    """, unsafe_allow_html=True)
        st.info("""
**Not yet relevant — pension phase unlocks at age 60.**

When built fully this will cover:
- Transfer Balance Cap tracking ($1.9M)
- Minimum drawdown rates by age (4% → 14%)
- Tax switch from 15% accumulation to 0% pension phase
- Age Pension means testing interaction
        """)

# ════════════════════════════════════════════════════════════════
# CLIENT DASHBOARD
# ════════════════════════════════════════════════════════════════
with t_dash:
    st.caption(f"Assumptions: {gr*100:.1f}% growth · {sg*100:.1f}% SG · ${rep:,} repayment · {yrs} yr projection · today's dollars · Age Pension not modelled")
    if older_age >= 67:
        st.error("This client has reached retirement age (67). See the Life Stage tab for retirement drawdown analysis.")
    elif older_age >= 60:
        st.warning("This client is approaching retirement age. Pre-retirement analysis recommended.")
    elif older_age >= 50:
        st.info("This client is within 15 years of retirement. Consider pre-retirement planning conversations.")
    em = br["emergency_months"]; sr = br["savings_rate"]
    def mc(label,val,sub,pos):
        cls = "pos" if pos else "neg"
        return f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value {cls}">{val}</div><div class="metric-sub">{sub}</div></div>'
    cards = '<div class="metric-row">'
    cards += mc("Net position",   fmt(br["net_position"]),  "Assets minus liabilities",        br["net_position"]>0)
    cards += mc("Annual surplus", fmt(br["surplus"]),        "Income minus expenses",            br["surplus"]>0)
    cards += mc("Savings rate",   f"{sr*100:.1f}%",          "⚠ Below 10%" if sr<0.1 else "Healthy", sr>=0.1)
    cards += mc("Emergency buffer",f"{em:.1f} months",       "⚠ Below minimum" if em<3 else "Adequate", em>=3)
    cards += '</div>'
    st.markdown(cards, unsafe_allow_html=True)

    flags = bo["risk_flags"]
    badges = "".join(f'<span class="badge badge-risk">⚠ {f}</span>' for f in flags) if flags else '<span class="badge badge-ok">✓ No critical risk flags</span>'
    st.markdown(f"<div style='margin-bottom:1.2rem'>{badges}</div>", unsafe_allow_html=True)

    st.markdown("**Statement of financial position — base case**")
    bs_rows = [
        ("Superannuation",    super_bal,              super_bal,  False),
        ("Investments",       invest,                 invest,     False),
        ("Cash & Savings",    cash,                   cash,       False),
        ("TOTAL ASSETS",      br["total_assets"],     br["total_assets"], True),
        (None,None,None,False),
        ("Mortgage / Debt",   debt,                  -debt,      False),
        ("TOTAL LIABILITIES", debt,                  -debt,      True),
        (None,None,None,False),
        ("NET POSITION",      br["net_position"],     br["net_position"], True),
    ]
    html = '<table class="word-table"><thead><tr><th>Item</th><th>Amount</th></tr></thead><tbody>'
    for label,dv,nv,tot in bs_rows:
        if label is None:
            html += '<tr class="divider"><td colspan="2"></td></tr>'; continue
        html += f'<tr class="{"total" if tot else ""}"><td>{label}</td><td class="{cc(nv)}">{fmt(dv)}</td></tr>'
    html += '</tbody></table>'
    st.markdown(html, unsafe_allow_html=True)
    interp = []
    if br["savings_rate"] < 0.1:
        interp.append("Savings rate is below 10% — limited capacity to build wealth or absorb unexpected costs.")
    if cash < expenses * 0.2:
        interp.append("Cash reserves are below 3 months of expenses — building this buffer is typically the first planning priority.")
    if debt > br["total_assets"] * 0.7:
        interp.append("Debt exceeds 70% of total assets — normal at accumulation stage, but worth monitoring as interest rates change.")
    if super_bal < income:
        interp.append("Superannuation is below 1× annual income — consider reviewing contribution strategy.")
    if not interp:
        interp.append("No immediate risk flags. The projection shows wealth building steadily over the selected horizon.")
    st.info(" ".join(interp))

# ════════════════════════════════════════════════════════════════
# SCENARIO ANALYSIS
# ════════════════════════════════════════════════════════════════
with t_scen:
    st.caption(f"Assumptions: {gr*100:.1f}% growth · {sg*100:.1f}% SG · ${rep:,} repayment · {yrs} yr projection · today's dollars · Age Pension not modelled")
    s1l = f"Scenario 1 — {s1_type}"; s2l = f"Scenario 2 — {s2_type}"
    extra_labels = [e["scenario_name"] for e,_,_ in extra_outputs]
    all_labels   = [s1l, s2l] + extra_labels
    all_results  = [s1r, s2r] + [eo["results"] for _,eo,_ in extra_outputs]

    comp_rows = [
        ("Net Position ($)",          "currency", "net_position"),
        ("Annual Surplus ($)",        "currency", "surplus"),
        ("Savings Rate (%)",          "pct",      "savings_rate"),
        ("Debt-to-Assets (%)",        "pct",      "debt_to_assets"),
        ("Emergency Buffer (months)", "months",   "emergency_months"),
    ]
    def fmtc(v,k):
        if k=="currency": return fmt(v)
        if k=="pct":      return f"{v*100:.1f}%"
        return f"{v:.1f} mo"

    th = "".join(f"<th>{l}</th>" for l in ["Base Case"]+all_labels)
    html = f'<table class="word-table"><thead><tr><th>Metric</th>{th}</tr></thead><tbody>'
    for label,kind,key in comp_rows:
        bv = br[key]
        cells = f'<td class="{cc(bv)}">{fmtc(bv,kind)}</td>'
        for r in all_results:
            v = r[key]
            cells += f'<td class="{cc(v)}">{fmtc(v,kind)}</td>'
        html += f'<tr><td>{label}</td>{cells}</tr>'
    html += '</tbody></table>'
    st.markdown(html, unsafe_allow_html=True)
    st.caption("Green cells show the strongest outcome per metric. Use this to identify which strategy best improves cash flow versus long-term wealth and what trade-offs are involved.")
    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
    render_insight(generate_insight("scenarios",
        br,s1r,s2r,bp,s1p,s2p,s1_type,s2_type,
        yrs,income,expenses,rep,cash,debt,super_bal))

    # ── Row 1: Income Composition | Balance Sheet Dynamics ──────────
    scen_clients = [base_client, s1, s2] + [e for e,_,_ in extra_outputs]
    scen_labels  = ["Base", s1_type, s2_type] + [e["scenario_name"] for e in extras]
    scen_colors  = [NAVY, S1_COLOR, TEAL] + EXTRA_COLORS[:len(extras)]
    scen_projs   = [bp, s1p, s2p] + [ep for _,_,ep in extra_outputs]

    # ── Income Allocation (full width) ──────────────────────────
    from matplotlib.patches import Patch
    fig, ax = plt.subplots(figsize=(14, max(4, 0.9*len(scen_labels))))
    for i, sc in enumerate(scen_clients):
        inc = sc["income"] if sc["income"] else 1
        exp_pct = sc["expenses"] / inc
        rep_pct = min(rep / inc, max(0, 1 - exp_pct))
        sur_pct = max(0, 1 - exp_pct - rep_pct)
        ax.barh(i, exp_pct, color="#FCE4D6", edgecolor="#C00000", linewidth=0.8, zorder=3)
        ax.barh(i, rep_pct, left=exp_pct, color="#FFF3CD", edgecolor="#E8A838", linewidth=0.8, zorder=3)
        ax.barh(i, sur_pct, left=exp_pct+rep_pct, color="#E2F0D9", edgecolor="#006100", linewidth=0.8, zorder=3)
        if exp_pct > 0.08:
            ax.text(exp_pct/2, i, f"{exp_pct*100:.0f}%", ha="center", va="center", fontsize=8, color="#C00000", fontweight="bold")
        if rep_pct > 0.08:
            ax.text(exp_pct+rep_pct/2, i, f"{rep_pct*100:.0f}%", ha="center", va="center", fontsize=8, color="#7a5c00", fontweight="bold")
        if sur_pct > 0.08:
            ax.text(exp_pct+rep_pct+sur_pct/2, i, f"{sur_pct*100:.0f}%", ha="center", va="center", fontsize=8, color="#006100", fontweight="bold")
    ax.axvline(0.9, color=NAVY, linewidth=1, linestyle=":", zorder=4)
    ax.text(0.905, len(scen_labels)-0.55, "10% min", fontsize=8, color=NAVY, va="top")
    ax.set_yticks(range(len(scen_labels)))
    ax.set_yticklabels(scen_labels, fontsize=9)
    ax.set_xlim(0, 1.05)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"{x*100:.0f}%"))
    ax.set_title("Income Allocation by Scenario", fontweight="bold", color=NAVY, pad=8, fontsize=11)
    legend_els = [Patch(facecolor="#FCE4D6", edgecolor="#C00000", label="Expenses"),
                  Patch(facecolor="#FFF3CD", edgecolor="#E8A838", label="Debt repayment"),
                  Patch(facecolor="#E2F0D9", edgecolor="#006100", label="Surplus")]
    ax.legend(handles=legend_els, loc="lower center", bbox_to_anchor=(0.5,-0.12), ncol=3, fontsize=8, framealpha=0.9)
    plt.tight_layout(); st.pyplot(fig); plt.close()

    _inc_pts = []
    _surpluses = {lbl: max(0, 1 - sc["expenses"]/(sc["income"] if sc["income"] else 1) - rep/(sc["income"] if sc["income"] else 1)) for lbl, sc in zip(scen_labels, scen_clients)}
    _best_alloc = max(_surpluses, key=_surpluses.get)
    _worst_alloc = min(_surpluses, key=_surpluses.get)
    _base_exp_pct = scen_clients[0]["expenses"] / (scen_clients[0]["income"] if scen_clients[0]["income"] else 1) * 100
    _inc_pts.append(f"Base case allocates {_base_exp_pct:.0f}% to expenses — {'above' if _base_exp_pct > 50 else 'within'} the 50% guideline.")
    _inc_pts.append(f"{_best_alloc} has the highest surplus ratio at {_surpluses[_best_alloc]*100:.0f}% of income available for reinvestment.")
    if _surpluses[_best_alloc] != _surpluses[_worst_alloc]:
        _inc_pts.append(f"Surplus gap between best and worst scenario: {(_surpluses[_best_alloc] - _surpluses[_worst_alloc])*100:.0f} percentage points of income.")
    render_insight(_inc_pts)

    # ── Balance Sheet Dynamics (full width) ──────────────────────
    fig, ax = plt.subplots(figsize=(14, 6))
    yrs_idx = bs_proj.index
    assets_s = bs_proj["Assets"] / 1e6
    liab_s   = bs_proj["Liabilities"] / 1e6
    nw_s     = bs_proj["Net Worth"] / 1e6
    ax.fill_between(yrs_idx, 0, assets_s, alpha=0.15, color=NAVY)
    ax.fill_between(yrs_idx, 0, liab_s,   alpha=0.15, color="#C00000")
    ax.plot(yrs_idx, assets_s, color=NAVY,     linewidth=3,   label="Total assets")
    ax.plot(yrs_idx, liab_s,   color="#C00000", linewidth=2.5, linestyle="--", label="Total liabilities")
    ax.plot(yrs_idx, nw_s,     color=TEAL,     linewidth=3,   label="Net position")
    ax.axhline(0, color="#ccc", linewidth=0.8)
    crossover = next((y for y in yrs_idx if bs_proj.loc[y,"Net Worth"] > 0), None)
    if crossover is not None:
        ax.axvline(crossover, color=TEAL, linewidth=1, linestyle=":")
        y_ann = float(nw_s.max()) * 0.18
        ax.annotate("Net positive", xy=(crossover, 0),
                    xytext=(crossover+max(1,yrs*0.05), y_ann),
                    fontsize=9, color=TEAL,
                    arrowprops=dict(arrowstyle="->", color=TEAL, lw=1))
    ax.set_title("Balance Sheet Dynamics — Base Case", fontweight="bold", color=NAVY, pad=8, fontsize=11)
    ax.set_xlabel("Year", color=NAVY)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"${x:.1f}M"))
    ax.legend(loc="lower right", fontsize=9, framealpha=0.9)
    plt.tight_layout(); st.pyplot(fig); plt.close()

    render_insight(generate_insight("balance",
        br,s1r,s2r,bp,s1p,s2p,s1_type,s2_type,
        yrs,income,expenses,rep,cash,debt,super_bal))

    # ── Row 1b: Cash Flow Funnel (full width) ────────────────────
    reinvestable = max(0, income - expenses - rep)
    after_exp    = max(0, income - expenses)
    exp_pct_b    = expenses / income * 100 if income else 0
    rep_pct_b    = rep / income * 100 if income else 0
    sur_pct_b    = reinvestable / income * 100 if income else 0
    stages = [
        ("Reinvestable",   reinvestable, TEAL),
        ("After expenses", after_exp,    S1_COLOR),
        ("Gross income",   income,       NAVY),
    ]
    fig_f, ax_f = plt.subplots(figsize=(14, 3))
    for i, (label, val, clr) in enumerate(stages):
        w = val / income if income else 0
        left = (1 - w) / 2
        ax_f.barh(i, w, left=left, height=0.52, color=clr, zorder=3)
        dollar = fmt(val)
        pct = f"{w*100:.0f}% of income"
        ax_f.text(0.5, i, f"{label}  ·  {dollar}  ·  {pct}",
            ha="center", va="center", fontsize=9,
            fontweight="bold", color="white")
    ax_f.set_xlim(0, 1)
    ax_f.set_ylim(-0.6, 2.6)
    ax_f.set_xticks([]); ax_f.set_yticks([])
    for sp in ax_f.spines.values():
        sp.set_visible(False)
    ax_f.set_title("Cash Flow Funnel — Base Case",
        fontweight="bold", color=NAVY, pad=8, fontsize=10)
    plt.tight_layout(); st.pyplot(fig_f); plt.close()

    # ── Cashflow insight (data-driven) ───────────────────────────
    _sr = br["savings_rate"]
    _cf_pts = []
    if _sr >= 0.35:
        _cf_pts.append(f"Savings rate of {_sr*100:.1f}% is strong — well above the 10% minimum. At this rate ${reinvestable:,.0f} compounds annually into long-term wealth.")
    elif _sr >= 0.2:
        _cf_pts.append(f"Savings rate of {_sr*100:.1f}% is healthy. ${reinvestable:,.0f} is available each year for reinvestment after debt repayment.")
    elif _sr >= 0.1:
        _cf_pts.append(f"Savings rate of {_sr*100:.1f}% meets the minimum benchmark. Only ${reinvestable:,.0f} is available for reinvestment — any expense increase would put this at risk.")
    else:
        _cf_pts.append(f"Savings rate of {_sr*100:.1f}% is below the 10% benchmark. With only ${reinvestable:,.0f} reinvestable, wealth accumulation is constrained — review expense strategy.")
    _exp_diff = expenses - (income * 0.5)
    if _exp_diff > 0:
        _cf_pts.append(f"Expenses consume {exp_pct_b:.0f}% of gross income — above the 50% guideline by ${_exp_diff:,.0f}. Debt repayment takes a further {rep_pct_b:.0f}%.")
    else:
        _cf_pts.append(f"Expenses at {exp_pct_b:.0f}% of gross income are within the 50% guideline. Debt repayment takes a further {rep_pct_b:.0f}%, leaving {sur_pct_b:.0f}% reinvestable.")
    _best_s = s1_type if s1r["surplus"] > s2r["surplus"] else s2_type
    _best_v = max(s1r["surplus"], s2r["surplus"])
    if _best_v > br["surplus"]:
        _delta = _best_v - br["surplus"]
        _cf_pts.append(f"{_best_s} improves annual surplus by ${_delta:,.0f} to ${_best_v:,.0f} — the strongest cash flow outcome across all scenarios.")
    render_insight(_cf_pts)

    # ── Row 2: Milestone Comparison (full width) ─────────────────
    milestones_c = [y for y in [0,5,10,15,20] if y<=yrs]
    n_sc = len(scen_projs)
    bar_w = min(0.8/n_sc, 0.25)
    x_pos = np.arange(len(milestones_c))
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.set_facecolor("white")
    ax.yaxis.grid(True, color="#E5E7EB", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    for i, (proj, lbl, clr) in enumerate(zip(scen_projs, scen_labels, scen_colors)):
        vals = [proj.loc[y,"Net Worth"]/1e6 if y in proj.index else 0 for y in milestones_c]
        offset = (i - n_sc/2 + 0.5) * bar_w
        b3 = ax.bar(x_pos+offset, vals, width=bar_w*0.9, color=clr, label=lbl, zorder=3)
        for bar,v in zip(b3, vals):
            ypos = bar.get_height() + 0.04 if v >= 0 else bar.get_height() - 0.12
            ax.text(bar.get_x()+bar.get_width()/2, ypos,
                    f"${v:.1f}M", ha="center", va="bottom",
                    fontsize=9, fontweight="bold", color="white" if v < 0 else NAVY,
                    rotation=0, bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=clr, lw=0.8, alpha=0.85))
    ax.set_xticks(x_pos)
    ax.set_xticklabels([f"Year {y}" for y in milestones_c], fontsize=9)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"${x:.1f}M"))
    ax.set_title("Wealth Trajectory — Key Milestones", fontweight="bold", color=NAVY, pad=10, fontsize=11)
    ax.axhline(0, color="#ddd", linewidth=0.8)
    ax.legend(fontsize=9, framealpha=0.9)
    plt.tight_layout(); st.pyplot(fig); plt.close()

    st.caption("Income allocation shows proportion of gross income consumed by expenses, debt repayment, and available for reinvestment. Balance sheet dynamics shows the crossover point where net worth turns positive. Milestone chart shows wealth divergence across strategies at key intervals.")
    st.markdown("---")
    st.markdown("### Executive Summary")
    st.caption("Key charts and planning observations "
        "collated across all analyses")
    col_x,col_y,col_z = st.columns(3)
    with col_x:
        st.metric("Net Position",fmt(br["net_position"]))
    with col_y:
        st.metric("Annual Surplus",fmt(br["surplus"]))
    with col_z:
        best_ev=max(bp.iloc[-1]["Net Worth"],
            s1p.iloc[-1]["Net Worth"],
            s2p.iloc[-1]["Net Worth"])
        st.metric(f"Best Year {yrs}",
            f"${best_ev/1e6:.2f}M")
    flags=bo["risk_flags"]
    badges="".join(
        f'<span class="badge badge-risk">⚠ {f}</span>'
        for f in flags) if flags else \
        '<span class="badge badge-ok">✓ No risk flags</span>'
    st.markdown(f"<div style='margin:.75rem 0'>"
        f"{badges}</div>",unsafe_allow_html=True)
    st.markdown("---")

    # PANEL 1-3 — side by side summary row
    st.markdown("#### Key metrics at a glance")
    ec1, ec2, ec3 = st.columns(3)
    with ec1:
        st.markdown("##### Asset mix")
        fig,ax=plt.subplots(figsize=(5,4))
        ax.pie([super_bal,invest,cash],
            labels=["Super","Investments","Cash"],
            colors=[NAVY,S1_COLOR,TEAL],
            autopct="%1.0f%%",startangle=90,
            wedgeprops={"linewidth":1.5,"edgecolor":"white"},
            textprops={"fontsize":11})
        ax.set_title("Asset Mix — Base Case",
            fontweight="bold",color=NAVY,pad=10,fontsize=11)
        plt.tight_layout(); st.pyplot(fig); plt.close()
    ta=br["total_assets"]
    sp_pct=super_bal/ta*100 if ta else 0
    in_pct=invest/ta*100 if ta else 0
    ca_pct=cash/ta*100 if ta else 0
    pts1=[]
    if sp_pct>60:
        pts1.append(f"Super dominates at {sp_pct:.0f}% of total assets — high concentration in a single vehicle.")
    else:
        pts1.append(f"Superannuation is {sp_pct:.0f}% of total assets — reasonably diversified asset base.")
    if ca_pct<10:
        pts1.append(f"Cash is only {ca_pct:.0f}% of assets — limited liquidity outside super and investments.")
    else:
        pts1.append(f"Cash at {ca_pct:.0f}% provides reasonable liquidity for short-term needs.")
    if in_pct>0:
        pts1.append(f"Non-super investments ({in_pct:.0f}%) are accessible before preservation age.")
    pts1.append("Consider diversification across vehicles to reduce concentration risk.")
    # PANEL 2 — Net position by scenario
    nv=[br["net_position"],s1r["net_position"],
        s2r["net_position"]]+ \
        [eo["results"]["net_position"]
         for _,eo,_ in extra_outputs]
    nl=(["Base",s1_type,s2_type]+
        [e["scenario_name"] for e in extras])
    bc=[BG_NEG if v<0 else BG_POS for v in nv]
    be=[TXT_NEG if v<0 else TXT_POS for v in nv]
    with ec2:
        st.markdown("##### Net position")
        fig,ax=plt.subplots(figsize=(5,4))
        bars=ax.bar(nl,nv,color=bc,edgecolor=be,
            linewidth=1.5,width=0.5,zorder=3)
        ax.axhline(0,color="#C00000",
            linewidth=1,linestyle="--")
        sp=max(abs(v) for v in nv)
        for bar,v in zip(bars,nv):
            clr=TXT_POS if v>=0 else TXT_NEG
            ax.text(bar.get_x()+bar.get_width()/2,
                v+sp*.05*(1 if v>=0 else -1),
                fmt(v),ha="center",
                va="bottom" if v>=0 else "top",
                fontsize=8,fontweight="bold",color=clr)
        ax.set_title("Net Position by Scenario",
            fontweight="bold",color=NAVY,pad=10,fontsize=11)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(
            lambda x,_:f"${x/1000:.0f}k"))
        plt.xticks(fontsize=9)
        plt.tight_layout(); st.pyplot(fig); plt.close()
    best_n_idx=nv.index(max(nv))
    pts2=[]
    if br["net_position"]<0:
        pts2.append(f"Base case net deficit of {fmt(br['net_position'])} — liabilities exceed assets at this stage.")
    else:
        pts2.append(f"Net positive position of {fmt(br['net_position'])} — assets exceed liabilities.")
    if max(nv)>br["net_position"]:
        pts2.append(f"{nl[best_n_idx]} produces the strongest balance sheet outcome at {fmt(max(nv))}.")
    pts2.append("Red bars show negative net worth — expected at accumulation stage with an active mortgage.")
    pts2.append("Net position improves as debt reduces and investments compound over time.")
    # PANEL 3 — 20-year projection
    with ec3:
        st.markdown(f"##### {yrs}-year projection")
        fig,ax=plt.subplots(figsize=(5,4))
        ax.plot(bp.index,bp["Net Worth"]/1e6,
            color=NAVY,linewidth=2.5,label="Base Case",zorder=3)
        for label,r,proj,clr in all_scenarios:
            ls=("--" if "Income" in label
                else ":" if "Debt" in label else "-.")
            ax.plot(proj.index,proj["Net Worth"]/1e6,
                color=clr,linewidth=2,linestyle=ls,
                label=label,zorder=3)
        ax.axhline(0,color="#ddd",linewidth=0.8)
        ax.fill_between(bp.index,0,bp["Net Worth"]/1e6,
            where=bp["Net Worth"]>0,alpha=.05,color=NAVY)
        last=bp.index[-1]
        for proj,clr in ([(bp,NAVY)]+
            [(p,c) for _,_,p,c in all_scenarios]):
            v=proj.iloc[-1]["Net Worth"]
            ax.annotate(f"  ${v/1e6:.2f}M",
                xy=(last,v/1e6),fontsize=9,
                fontweight="bold",color=clr,va="center")
        ax.set_xlabel("Year",color=NAVY)
        ax.set_ylabel("Net Worth ($M)",color=NAVY)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(
            lambda x,_:f"${x:.1f}M"))
        ax.legend(framealpha=.9,fontsize=9,loc="upper left")
        ax.set_title(f"{yrs}-Year Net Worth Projection",
            fontweight="bold",color=NAVY,pad=10,fontsize=11)
        plt.tight_layout(); st.pyplot(fig); plt.close()
    st.markdown("---")
    # Per-chart insight boxes
    st.markdown("**Asset mix — observations**")
    render_insight(pts1)

    st.markdown("**Net position by scenario — observations**")
    render_insight(pts2)

    st.markdown("**Wealth projection — observations**")
    b20 = bp.iloc[-1]["Net Worth"]
    best20 = max(b20, s1p.iloc[-1]["Net Worth"], s2p.iloc[-1]["Net Worth"])
    best20n = ("Base Case" if best20 == b20
        else s1_type if best20 == s1p.iloc[-1]["Net Worth"] else s2_type)
    gap20 = best20 - min(b20, s1p.iloc[-1]["Net Worth"], s2p.iloc[-1]["Net Worth"])
    cx = next((int(y) for y, r in bp.iterrows() if r["Net Worth"] > 0), None)
    pts_proj = [f"{best20n} projects the strongest year {yrs} outcome at ${best20/1e6:.2f}M."]
    pts_proj.append(f"Scenario gap at year {yrs}: ${gap20/1e6:.2f}M — compounding amplifies early surplus differences.")
    if cx and cx > 0:
        pts_proj.append(f"Net worth turns positive in year {cx} — growth accelerates as debt clears.")
    render_insight(pts_proj)

    st.markdown("**Integrated summary — what this means for this client**")
    sr = br["savings_rate"]
    em = br["emergency_months"]
    dta = br["debt_to_assets"] * 100
    net = br["net_position"]
    sur = br["surplus"]
    pts_int = []
    pts_int.append(f"Current position: {'net deficit' if net < 0 else 'net positive'} of {fmt(abs(net))} with a {sr*100:.1f}% savings rate generating ${sur:,.0f} p.a. reinvestable surplus.")
    pts_int.append(f"Asset mix is {sp_pct:.0f}% concentrated in super — only accessible from preservation age. Liquid cash is {ca_pct:.0f}% ({em:.1f} months buffer).")
    pts_int.append(f"Debt is {dta:.0f}% of assets — high leverage expected at this stage but sensitive to rate rises and income shocks.")
    pts_int.append(f"Best long-term strategy is {best20n} at ${best20/1e6:.2f}M by year {yrs} — a ${gap20/1e6:.2f}M gap vs worst case.")
    if em < 3:
        pts_int.append(f"Immediate priority: emergency buffer is only {em:.1f} months — build to 3 months (${expenses/4:,.0f}) before accelerating investment.")
    elif sr < 0.15:
        pts_int.append(f"Savings rate of {sr*100:.1f}% limits accumulation speed — review expenses or income strategy.")
    else:
        pts_int.append(f"With {sr*100:.1f}% savings rate and {best20n} strategy, wealth trajectory is strong. Focus on maintaining surplus and reviewing super contributions.")
    render_insight(pts_int)

# ════════════════════════════════════════════════════════════════
# SHOCK ANALYSIS
# ════════════════════════════════════════════════════════════════
with t_shock:
    st.caption(f"Assumptions: {gr*100:.1f}% growth · {sg*100:.1f}% SG · ${rep:,} repayment · {yrs} yr projection · today's dollars · Age Pension not modelled")
    st.markdown("### Shock Analysis")
    st.caption("Each bar shows the isolated impact of a single adverse event on year 20 net worth vs the base case. Shocks are independent — each runs against the base case only, not combined. Use sliders to adjust magnitude. The longest bar identifies this client's biggest financial vulnerability.")
    with st.expander("How each shock is calculated"):
        st.markdown("""
| Shock | Formula applied | What it models |
|---|---|---|
| **Income reduction** | `income × (1 − pct/100)` | Permanently lower income → less surplus every year → less compounding for full projection |
| **Expense increase** | `expenses × (1 + pct/100)` | Higher costs reduce reinvestable surplus by same amount annually |
| **Returns drop** | Growth rate: `7% → X%` | Applied to portfolio and super compounding — small % change creates large end difference via compounding |
| **Job loss** | `income × (1 − months/12)` | Zero income averaged across year 1 only — not a true month-by-month model |
| **Rate rise** | `expenses += debt × rate%` | Treated as permanent extra annual cost — not a true mortgage P&I recalculation |
| **Super paused** | `super_balance − (income × SG × years)` | Removes missed contributions as lump sum from starting balance — loses all future compounding on those amounts |
| **Debt increase** | `debt × (1 + pct/100)` | Higher starting debt reduces net worth immediately and raises total interest over repayment term |

**Important limitations:** Each shock runs independently against base case only — shocks are not combined. Job loss and rate rise are approximations, not true cash flow models. All shocks apply from year 0.
        """)
    st.markdown("**Adjust shock magnitudes**")
    st.caption("Each slider sets the size of a single adverse event. The formula below each slider explains exactly how the model applies it — so you can see what a '20%' or '3 year' figure actually means in practice.")

    c1,c2 = st.columns(2)
    with c1:
        sh_inc = st.slider("Income reduction (%)", 5, 50, 20, 5)
        st.caption(f"Applied as: income × (1 − {sh_inc/100:.2f}) = ${income*(1-sh_inc/100):,.0f} p.a. "
                   f"Reduces annual surplus by ${income*sh_inc/100:,.0f} — that shortfall stops compounding for every remaining year.")

        sh_exp = st.slider("Expense increase (%)", 5, 50, 20, 5)
        st.caption(f"Applied as: expenses × (1 + {sh_exp/100:.2f}) = ${expenses*(1+sh_exp/100):,.0f} p.a. "
                   f"Surplus falls by ${expenses*sh_exp/100:,.0f} — less reinvested each year for the full projection.")

        sh_ret = st.slider("Investment returns drop — use % p.a.", 1, 6, 3, 1)
        st.caption(f"Applied as: growth rate drops from {gr*100:.1f}% → {max(0,gr*100-sh_ret):.1f}% p.a. "
                   f"Even 1% less return materially erodes a large portfolio via compounding over {yrs} years.")

        sh_job = st.slider("Job loss (months)", 1, 24, 6, 1)
        st.caption(f"Applied as: income × (1 − {sh_job}/12) = ${income*(1-sh_job/12):,.0f} annualised. "
                   f"Models {sh_job} months of zero income averaged across year 1, removing ${income*sh_job/12:,.0f} from that year's saving.")

    with c2:
        sh_rate = st.slider("Interest rate rise (%)", 1, 5, 2, 1)
        st.caption(f"Applied as: expenses += debt × {sh_rate/100:.2f} = extra ${debt*sh_rate/100:,.0f} p.a. "
                   f"Treats the rate rise as a permanent annual cost increase — reduces surplus and reinvestment capacity every year.")

        sh_sup = st.slider("Super paused (years)", 1, 10, 3, 1)
        st.caption(f"Applied as: super_balance − (income × SG × {sh_sup}) = −${income*sg*sh_sup:,.0f} removed. "
                   f"Missed contributions forfeit both the deposit and all compounding on those amounts for the rest of the projection.")

        sh_dbt = st.slider("Debt increase (%)", 5, 30, 10, 5)
        st.caption(f"Applied as: debt × (1 + {sh_dbt/100:.2f}) = ${debt*(1+sh_dbt/100):,.0f} total. "
                   f"Higher principal reduces net worth immediately by ${debt*sh_dbt/100:,.0f} and raises total interest paid over the repayment term.")

    base_y20 = bp.loc[min(yrs,20),"Net Worth"] if yrs>=20 else bp.iloc[-1]["Net Worth"]

    def shock_nw(changes, alt_gr=None):
        sc = create_scenario(base_client, changes)
        return project_wealth(sc,yrs,alt_gr or gr,sg,rep).iloc[-1]["Net Worth"]

    shocks = [
        (f"Income −{sh_inc}%",     shock_nw({"income":int(income*(1-sh_inc/100))})),
        (f"Expenses +{sh_exp}%",   shock_nw({"expenses":int(expenses*(1+sh_exp/100))})),
        (f"Returns drop to {sh_ret}%", shock_nw({}, alt_gr=sh_ret/100)),
        (f"Job loss {sh_job} mo",  shock_nw({"income":int(income*(1-sh_job/12))})),
        (f"Rate rise +{sh_rate}%", shock_nw({"expenses":expenses+int(debt*sh_rate/100)})),
        (f"Super paused {sh_sup}y",shock_nw({"super_balance":max(0,super_bal-int(income*sg*sh_sup))})),
        (f"Debt +{sh_dbt}%",       shock_nw({"debt":int(debt*(1+sh_dbt/100))})),
    ]
    deltas = [(label, nw-base_y20) for label,nw in shocks]
    deltas.sort(key=lambda x:x[1])

    fig,ax=plt.subplots(figsize=(14,5))
    labels_s=[d[0] for d in deltas]; vals_s=[d[1] for d in deltas]
    bar_colors=[BG_NEG if v<0 else BG_POS for v in vals_s]
    bar_edge  =[TXT_NEG if v<0 else TXT_POS for v in vals_s]
    bars=ax.barh(labels_s,vals_s,color=bar_colors,edgecolor=bar_edge,linewidth=1,zorder=3)
    ax.axvline(0,color="#bbb",linewidth=.8)
    min_v = min(vals_s)
    max_v = max(vals_s) if max(vals_s) > 0 else 0
    ax.set_xlim(min_v * 1.25, max_v * 1.25 + abs(min_v)*0.15)
    ax.set_title(f"Impact on year {min(yrs,20)} net worth vs base case",fontweight="bold",color=NAVY,pad=10)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_:fmt(x)))
    for bar, v in zip(bars, vals_s):
        spread = max(abs(x) for x in vals_s)
        offset = spread * 0.03
        ax.text(
            v - offset if v < 0 else v + offset,
            bar.get_y() + bar.get_height() / 2,
            fmt(v),
            va="center",
            ha="right" if v < 0 else "left",
            fontsize=8, fontweight="bold",
            color=TXT_NEG if v < 0 else TXT_POS,
            clip_on=False)
    plt.tight_layout(); st.pyplot(fig); plt.close()

    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    # ── Year-by-year shocked net worth paths ─────────────────────
    st.markdown("**Year-by-year net worth path under each shock vs base case**")
    st.caption("Each line shows how net worth develops over time if that single shock is applied from year 0. "
               "The gap between a shock line and the base case widens over time because compound growth amplifies early differences.")
    shock_scenarios = [
        (f"Income −{sh_inc}%",      {"income": int(income*(1-sh_inc/100))},        None,           "#D85A30"),
        (f"Expenses +{sh_exp}%",    {"expenses": int(expenses*(1+sh_exp/100))},     None,           "#993556"),
        (f"Returns {max(0,gr*100-sh_ret):.0f}%", {},                               sh_ret/100,     "#457B9D"),
        (f"Job loss {sh_job} mo",   {"income": int(income*(1-sh_job/12))},          None,           "#8B5E3C"),
        (f"Rate +{sh_rate}%",       {"expenses": expenses+int(debt*sh_rate/100)},   None,           "#2D6A4F"),
        (f"Super −{sh_sup}y",       {"super_balance": max(0,super_bal-int(income*sg*sh_sup))}, None,"#6B3FA0"),
        (f"Debt +{sh_dbt}%",        {"debt": int(debt*(1+sh_dbt/100))},             None,           "#2E86AB"),
    ]
    fig2, ax2 = plt.subplots(figsize=(14, 6))
    ax2.plot(bp.index, bp["Net Worth"]/1e6, color=NAVY, linewidth=2.5, label="Base Case", zorder=4)
    ax2.fill_between(bp.index, 0, bp["Net Worth"]/1e6, where=bp["Net Worth"]>0, alpha=0.05, color=NAVY)
    for s_label, s_changes, s_alt_gr, s_clr in shock_scenarios:
        s_proj = project_wealth(create_scenario(base_client, s_changes), yrs, s_alt_gr or gr, sg, rep)
        ax2.plot(s_proj.index, s_proj["Net Worth"]/1e6, color=s_clr, linewidth=2,
                 linestyle="--", label=s_label, zorder=3, alpha=0.9)
        end_v = s_proj.iloc[-1]["Net Worth"]
        ax2.annotate(f"  ${end_v/1e6:.2f}M", xy=(s_proj.index[-1], end_v/1e6),
                     fontsize=7.5, color=s_clr, va="center")
    base_end = bp.iloc[-1]["Net Worth"]
    ax2.annotate(f"  ${base_end/1e6:.2f}M", xy=(bp.index[-1], base_end/1e6),
                 fontsize=8.5, fontweight="bold", color=NAVY, va="center")
    ax2.axhline(0, color="#ccc", linewidth=0.8)
    ax2.set_xlabel("Year", color=NAVY)
    ax2.set_ylabel("Net Worth ($M)", color=NAVY)
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"${x:.1f}M"))
    ax2.set_title(f"Net Worth Trajectory Under Each Shock — {client_name}", fontweight="bold",
                  color=NAVY, pad=10, fontsize=11)
    ax2.legend(fontsize=8, framealpha=0.9, loc="upper left", ncol=2)
    plt.tight_layout(); st.pyplot(fig2); plt.close()

    th2 = "<th>Surplus impact</th><th>Net position impact</th><th>Year 20 impact</th>"
    html2 = f'<table class="word-table"><thead><tr><th>Shock</th>{th2}</tr></thead><tbody>'
    for label,nw in shocks:
        if "Income" in label and "Job" not in label:
            sc = create_scenario(base_client, {"income": int(income*(1-sh_inc/100))})
        elif "Expense" in label:
            sc = create_scenario(base_client, {"expenses": int(expenses*(1+sh_exp/100))})
        elif "Job" in label:
            sc = create_scenario(base_client, {"income": int(income*(1-sh_job/12))})
        elif "Rate" in label:
            sc = create_scenario(base_client, {"expenses": expenses+int(debt*sh_rate/100)})
        elif "Super" in label:
            sc = create_scenario(base_client, {"super_balance": max(0,super_bal-int(income*sg*sh_sup))})
        elif "Debt +" in label:
            sc = create_scenario(base_client, {"debt": int(debt*(1+sh_dbt/100))})
        else:
            sc = base_client
        sr2  = calculate_financials(sc)
        ds   = sr2["surplus"] - br["surplus"]
        dn   = sr2["net_position"] - br["net_position"]
        dy20 = nw - base_y20
        def cz(v): return "cell-pos" if v>0 else "cell-neg" if v<0 else "cell-zero"
        html2 += f'<tr><td>{label}</td><td class="{cz(ds)}">{fmt(ds)}</td><td class="{cz(dn)}">{fmt(dn)}</td><td class="{cz(dy20)}">{fmt(dy20)}</td></tr>'
    html2 += '</tbody></table>'
    st.markdown(html2, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Base vs Shocked — side by side comparison")
    st.caption("Select a shock to compare base case inputs and outputs directly against the shocked scenario. Red = worse than base, green = better.")

    shock_options = [s[0] for s in shocks]
    selected_shock = st.selectbox("Select shock to compare", shock_options, key="shock_compare")

    shock_map = {
        f"Income −{sh_inc}%":         {"income": int(income*(1-sh_inc/100))},
        f"Expenses +{sh_exp}%":        {"expenses": int(expenses*(1+sh_exp/100))},
        f"Returns drop to {sh_ret}%":  {},
        f"Job loss {sh_job} mo":       {"income": int(income*(1-sh_job/12))},
        f"Rate rise +{sh_rate}%":      {"expenses": expenses+int(debt*sh_rate/100)},
        f"Super paused {sh_sup}y":     {"super_balance": max(0,super_bal-int(income*sg*sh_sup))},
        f"Debt +{sh_dbt}%":            {"debt": int(debt*(1+sh_dbt/100))},
    }
    alt_gr_map = {f"Returns drop to {sh_ret}%": sh_ret/100}

    sc_sel = create_scenario(base_client, shock_map.get(selected_shock, {}))
    sc_sel_r = calculate_financials(sc_sel)
    sc_sel_y20 = project_wealth(sc_sel, yrs, alt_gr_map.get(selected_shock, gr), sg, rep).iloc[-1]["Net Worth"]

    comp_rows = [
        ("Annual income",         fmt(income),                        fmt(sc_sel.get("income", income))),
        ("Annual expenses",       fmt(expenses),                      fmt(sc_sel.get("expenses", expenses))),
        ("Debt",                  fmt(debt),                          fmt(sc_sel.get("debt", debt))),
        ("Super balance",         fmt(super_bal),                     fmt(sc_sel.get("super_balance", super_bal))),
        ("Annual surplus",        fmt(br["surplus"]),                  fmt(sc_sel_r["surplus"])),
        ("Savings rate",          f"{br['savings_rate']*100:.1f}%",   f"{sc_sel_r['savings_rate']*100:.1f}%"),
        ("Emergency buffer",      f"{br['emergency_months']:.1f} mo", f"{sc_sel_r['emergency_months']:.1f} mo"),
        ("Debt to assets",        f"{br['debt_to_assets']*100:.0f}%", f"{sc_sel_r['debt_to_assets']*100:.0f}%"),
        (f"Year {yrs} net worth", fmt(base_y20),                      fmt(sc_sel_y20)),
        ("Year 20 difference",    "—",                                fmt(sc_sel_y20 - base_y20)),
    ]

    def parse_fmt(s):
        try: return float(s.replace("$","").replace(",","").replace("(","").replace(")","").replace("%","").replace(" mo","")) * (-1 if "(" in s else 1)
        except: return None

    comp_html = '<table class="word-table"><thead><tr><th>Metric</th><th>Base case</th><th>Shocked case</th><th>Change</th></tr></thead><tbody>'
    for label, bv, sv in comp_rows:
        rb = parse_fmt(bv); rs = parse_fmt(sv)
        if rb is not None and rs is not None and bv != "—":
            diff = rs - rb
            diff_cls = "cell-neg" if diff < 0 else "cell-pos" if diff > 0 else ""
            diff_str = fmt(diff) if abs(diff) > 0 else "—"
            sv_cls = "cell-neg" if rs < rb else "cell-pos" if rs > rb else ""
        else:
            diff_cls = "cell-neg"; diff_str = sv; sv_cls = "cell-neg"
        comp_html += f'<tr><td>{label}</td><td>{bv}</td><td class="{sv_cls}">{sv}</td><td class="{diff_cls}">{diff_str}</td></tr>'
    comp_html += '</tbody></table>'
    st.markdown(comp_html, unsafe_allow_html=True)

    fig_c, ax_c = plt.subplots(figsize=(14, 6))
    bp_sel = project_wealth(sc_sel, yrs, alt_gr_map.get(selected_shock, gr), sg, rep)
    ax_c.plot(bp.index, bp["Net Worth"]/1e6, color=NAVY, linewidth=3, label="Base Case", zorder=3)
    ax_c.plot(bp_sel.index, bp_sel["Net Worth"]/1e6, color="#C00000", linewidth=2.5, linestyle="--", label=f"Shocked: {selected_shock}", zorder=3)
    ax_c.fill_between(bp.index, bp["Net Worth"]/1e6, bp_sel["Net Worth"]/1e6, alpha=0.1, color="#C00000", label="Gap")
    ax_c.axhline(0, color="#ccc", linewidth=0.8)
    ax_c.set_xlabel("Year", color=NAVY)
    ax_c.set_ylabel("Net Worth ($M)", color=NAVY)
    ax_c.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"${x:.1f}M"))
    ax_c.legend(fontsize=9, framealpha=0.9)
    ax_c.set_title(f"Base Case vs {selected_shock} — Net Worth Trajectory", fontweight="bold", color=NAVY, pad=10, fontsize=11)
    ax_c.annotate(f"  ${bp.iloc[-1]['Net Worth']/1e6:.2f}M", xy=(bp.index[-1], bp.iloc[-1]["Net Worth"]/1e6), fontsize=9, fontweight="bold", color=NAVY, va="center")
    ax_c.annotate(f"  ${bp_sel.iloc[-1]['Net Worth']/1e6:.2f}M", xy=(bp_sel.index[-1], bp_sel.iloc[-1]["Net Worth"]/1e6), fontsize=9, fontweight="bold", color="#C00000", va="center")
    plt.tight_layout(); st.pyplot(fig_c); plt.close()

    shock_vals = dict(shocks)
    worst_label = min(shock_vals, key=shock_vals.get)
    worst_delta = shock_vals[worst_label]
    i_key = f"Income \u2212{sh_inc}%"
    r_key = f"Rate rise +{sh_rate}%"
    s_key = f"Super paused {sh_sup}y"
    i_d = shock_vals.get(i_key, 0)
    r_d = shock_vals.get(r_key, 0)
    s_d = shock_vals.get(s_key, 0)
    b1 = f"Largest vulnerability: {worst_label} reduces year 20 wealth by {fmt(abs(worst_delta))}."
    b2 = (f"Income risk is the primary driver — a {sh_inc}% reduction costs {fmt(abs(i_d))} by year 20."
          if abs(i_d) >= abs(r_d)
          else f"Rate sensitivity is significant — a {sh_rate}% rise costs {fmt(abs(r_d))} by year 20.")
    b3 = f"Super continuity matters — pausing {sh_sup} years costs {fmt(abs(s_d))} in long-term compounding."
    render_insight([b1, b2, b3])

# ════════════════════════════════════════════════════════════════
# PROJECTION
# ════════════════════════════════════════════════════════════════
with t_proj:
    st.caption(f"Assumptions: {gr*100:.1f}% growth · {sg*100:.1f}% SG · ${rep:,} repayment · {yrs} yr projection · today's dollars · Age Pension not modelled")
    fig,ax=plt.subplots(figsize=(11,5))
    ax.plot(bp.index,bp["Net Worth"]/1e6,color=NAVY,linewidth=3,label="Base Case",zorder=3)
    for label,r,proj,clr in all_scenarios:
        ax.plot(proj.index,proj["Net Worth"]/1e6,color=clr,linewidth=2.5,linestyle="--",label=label,zorder=3)
    ax.axhline(0,color="#ddd",linewidth=1)
    ax.fill_between(bp.index,0,bp["Net Worth"]/1e6,where=bp["Net Worth"]>0,alpha=.05,color=NAVY)
    last_yr = bp.index[-1]
    for proj,clr in [(bp,NAVY)]+[(p,c) for _,_,p,c in all_scenarios]:
        v = proj.iloc[-1]["Net Worth"]
        ax.annotate(f"  ${v/1e6:.2f}M",xy=(last_yr,v/1e6),fontsize=9,fontweight="bold",color=clr,va="center")
    ax.set_title(f"{yrs}-Year Net Worth Projection  —  {client_name}",fontsize=11,fontweight="bold",color=NAVY,pad=10)
    ax.set_xlabel("Year",color=NAVY); ax.set_ylabel("Net Worth ($M)",color=NAVY)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_:f"${x:.1f}M"))
    ax.legend(framealpha=.9,fontsize=9,loc="upper left")
    plt.tight_layout(); st.pyplot(fig); plt.close()

    milestones = [y for y in [0,5,10,15,20,25,30,35,40] if y<=yrs]
    th3 = "".join(f"<th>{l}</th>" for l in ["Base Case"]+[l for l,_,_,_ in all_scenarios])
    html3 = f'<table class="word-table"><thead><tr><th>Year</th>{th3}</tr></thead><tbody>'
    for y in milestones:
        bv = bp.loc[y,"Net Worth"]
        cells = f'<td class="{cc(bv)}">{fmt(bv)}</td>'
        for _,_,proj,_ in all_scenarios:
            if y in proj.index:
                v=proj.loc[y,"Net Worth"]; cells+=f'<td class="{cc(v)}">{fmt(v)}</td>'
            else:
                cells+="<td>—</td>"
        html3 += f'<tr><td>Year {y}</td>{cells}</tr>'
    html3 += '</tbody></table>'
    st.markdown(html3, unsafe_allow_html=True)
    st.caption(f"Projections assume consistent {gr*100:.0f}% annual returns. Real returns vary year to year. These figures illustrate the compounding effect of strategic decisions — not guaranteed outcomes. Age Pension and contributions tax are not modelled.")

# ════════════════════════════════════════════════════════════════
# LIFE STAGE
# ════════════════════════════════════════════════════════════════
with t_life:
    st.markdown("### Life Stage Analysis")
    st.caption("Australian financial life stage modelling — accumulation phase active")

    st.markdown(f"""
    <div style='background:#E6F1FB;border-radius:10px;padding:1rem 1.25rem;margin-bottom:12px;
    border:1px solid #B5D4F4'>
    <div style='font-size:11px;text-transform:uppercase;letter-spacing:.08em;
    color:#185FA5;margin-bottom:4px'>Active — Accumulation phase</div>
    <div style='font-size:14px;font-weight:500;color:#1B2E4B'>Building wealth while working</div>
    <div style='font-size:13px;color:#444;margin-top:8px;line-height:1.8'>
    <b>Active now (age 18–49):</b> Accumulation — super grows at {gr*100:.1f}% + SG, portfolio grows from reinvested surplus, debt reduces by ${rep:,} p.a.<br>
    <b>Unlocks at age 50:</b> Pre-Retirement readiness check — projected super vs target, gap, years to close shortfall.<br>
    <b>Unlocks at age 65:</b> Retirement Drawdown — sustainable income, asset depletion year, shortfall vs desired income.<br>
    <b>Not yet built:</b> Pension phase — Transfer Balance Cap, 0% earnings tax, Age Pension means testing.
    </div></div>""", unsafe_allow_html=True)

    if older_age >= 50:
        pr = calc_pre_retirement(
            base_client, older_age, retirement_age, target_income, gr, sg, rep)

        st.markdown("---")
        st.markdown("#### Pre-Retirement Readiness")
        st.caption(f"Based on target retirement age {retirement_age} and income ${target_income:,} p.a.")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Projected super at retirement", fmt(pr["projected_super"]))
        with col2:
            st.metric("Target super needed", fmt(pr["target_super_needed"]),
                help="Desired income ÷ 4% safe withdrawal rate")
        with col3:
            gap_val = pr["readiness_gap"]
            st.metric("Readiness gap", fmt(gap_val),
                delta="On track" if gap_val >= 0 else "Shortfall",
                delta_color="normal" if gap_val >= 0 else "inverse")

        if pr["on_track"]:
            st.success(f"On track for retirement at age {retirement_age}. "
                f"Projected super exceeds target by {fmt(pr['readiness_gap'])}.")
        else:
            st.error(f"Projected shortfall of {fmt(abs(pr['readiness_gap']))} "
                f"against retirement target. At current SG rate approximately "
                f"{pr['years_to_close']:.1f} additional years of contributions needed to close gap.")

        st.caption(
            "Target super = desired retirement income ÷ 4% (safe withdrawal rate). "
            "Age Pension not included — assess separately via Services Australia. "
            "Catch-up contributions and salary sacrifice not modelled.")

    else:
        st.markdown("""
        <div style='background:#F8F7F4;border-radius:10px;padding:1rem 1.25rem;
        margin-bottom:12px;border:1px solid #D1D5DB;opacity:1'>
        <div style='font-size:11px;text-transform:uppercase;letter-spacing:.08em;
        color:#888;margin-bottom:4px'>Available from age 50 — Pre-Retirement phase</div>
        <div style='font-size:15px;color:#555'>
        Switch to New Client in the sidebar and set age to 50+ to activate this section.
        Shows: projected super at retirement, target super needed (desired income ÷ 4%),
        readiness gap, and years of extra contributions needed to close any shortfall.
        </div></div>""", unsafe_allow_html=True)

    if older_age>=65:
        rd=calc_retirement_drawdown(base_client,
            drawdown_rate,desired_income,gr)
        st.markdown("---")
        st.markdown("#### Retirement Drawdown Analysis")
        c1,c2,c3=st.columns(3)
        with c1:
            st.metric("Sustainable income p.a.",
                fmt(rd["sustainable_income"]))
        with c2:
            st.metric("Desired income",
                fmt(rd["desired_income"]))
        with c3:
            st.metric("Surplus / shortfall",
                fmt(rd["shortfall"]),
                delta_color="normal" if rd["shortfall"]>=0
                    else "inverse")
        if rd["on_track"]:
            st.success("Assets projected to last "
                "beyond the 25-year planning horizon.")
        else:
            st.error(f"Assets projected to deplete in "
                f"year {rd['depleted_year']}. Consider "
                f"reducing drawdown rate.")
        proj=rd["projection"]
        fig,ax=plt.subplots(figsize=(11,4))
        ax.fill_between(proj.index,
            proj["Assets"]/1e6,alpha=.15,color=NAVY)
        ax.plot(proj.index,proj["Assets"]/1e6,
            color=NAVY,linewidth=2.5,
            label="Remaining assets")
        ax.axhline(0,color="#C00000",
            linewidth=1,linestyle="--")
        if rd["depleted_year"]:
            ax.axvline(rd["depleted_year"],
                color="#C00000",linewidth=1,linestyle=":")
            ax.annotate(
                f"Depleted year {rd['depleted_year']}",
                xy=(rd["depleted_year"],0),
                fontsize=8,color="#C00000",
                fontweight="bold")
        ax.set_title("Asset Drawdown Projection",
            fontweight="bold",color=NAVY,pad=10)
        ax.set_xlabel("Year in retirement")
        ax.set_ylabel("Assets ($M)")
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(
            lambda x,_:f"${x:.1f}M"))
        ax.legend(fontsize=9)
        plt.tight_layout(); st.pyplot(fig); plt.close()
        st.caption("Age Pension not modelled — eligible "
            "from age 67 for most Australians. "
            "Assess via Services Australia. "
            "Projections illustrative only.")
    else:
        st.markdown("""
    <div style='background:#F8F7F4;border-radius:10px;padding:1rem 1.25rem;
    margin-bottom:12px;border:1px solid #D1D5DB;opacity:1'>
    <div style='font-size:11px;text-transform:uppercase;letter-spacing:.08em;
    color:#888;margin-bottom:4px'>Available from age 65 — Retirement Drawdown phase</div>
    <div style='font-size:15px;color:#555'>
    Switch to New Client and set age to 65+ to activate this section.
    Shows: sustainable annual income from your assets using the 4% rule,
    projected asset depletion year, and shortfall vs desired income.
    Age Pension is not modelled — assess separately via Services Australia.
    </div></div>""", unsafe_allow_html=True)

    st.markdown("""
    <div style='background:#F8F7F4;border-radius:10px;padding:1rem 1.25rem;
    border:1px solid #D1D5DB;opacity:1'>
    <div style='font-size:11px;text-transform:uppercase;letter-spacing:.08em;
    color:#888;margin-bottom:4px'>Not yet modelled — Pension Phase</div>
    <div style='font-size:15px;color:#555'>
    Not built. Would require: Transfer Balance Cap tracking ($1.9M limit),
    switching investment earnings tax from 15% to 0% in pension phase,
    minimum drawdown rates by age, and Age Pension means testing.
    Raise this with your developer when ready to build.
    </div></div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# LEGISLATION
# ════════════════════════════════════════════════════════════════
with t_leg:
    st.markdown("### Australian Legislative Parameters")
    st.caption("Current as at 2024–25 financial year · Review annually and after Federal Budget")
    st.warning("Always verify current rates at ato.gov.au and legislation.gov.au before use in client conversations.")

    with st.expander("Superannuation Guarantee"):
        st.markdown("""
| | |
|---|---|
| **Current rate** | 11.5% (2024–25) |
| **Rising to** | 12.0% from 1 July 2025 |
| **In this model** | 11.5% applied throughout — does not auto-update |
| **Action required** | Update sg_rate = 0.12 in model parameters from July 2025 |
| **Legislative reference** | Superannuation Guarantee (Administration) Act 1992 |
        """)

    with st.expander("Contribution caps"):
        st.markdown("""
| Cap | Amount | Status in model |
|---|---|---|
| Concessional (employer + salary sacrifice + personal deductible) | $30,000 p.a. | **NOT CHECKED** — breach not flagged |
| Non-concessional | $120,000 p.a. | **NOT MODELLED** |
| Bring-forward rule | $360,000 over 3 years | **NOT MODELLED** |
| Catch-up contributions (balance below $500k) | Up to 5 years carried forward | **NOT MODELLED** |

**Note:** At $160,000 income the SG alone = $18,400 — leaving $11,600 before the concessional cap is breached.
        """)

    with st.expander("Preservation and access rules"):
        st.markdown("""
| Rule | Detail | Status in model |
|---|---|---|
| Preservation age | Age 60 for anyone born after 1 July 1964 | Not enforced — planner must verify |
| Conditions of release | Retirement, terminal illness, severe financial hardship | Not modelled |
| Transition to retirement | Income stream from preservation age while still working | Not modelled |
        """)

    with st.expander("Retirement phase"):
        st.markdown("""
| Rule | Detail | Status in model |
|---|---|---|
| Transfer Balance Cap | $1.9 million (2024–25, indexed annually) | **NOT MODELLED** |
| Pension phase earnings tax | 0% (vs 15% in accumulation) | **NOT MODELLED** |
| Account-based pension | Minimum drawdown rates apply from age 60 | **NOT MODELLED** |

**Minimum annual drawdown rates by age (legislated):**

| Age | Minimum drawdown % |
|---|---|
| Under 65 | 4% |
| 65–74 | 5% |
| 75–79 | 6% |
| 80–84 | 7% |
| 85–89 | 9% |
| 90–94 | 11% |
| 95+ | 14% |

**Transfer Balance Cap — what triggers it:**
- When super moves from accumulation to pension phase, the total transferred cannot exceed $1.9M
- Earnings in pension phase are tax-free (0%) vs 15% in accumulation
- Excess above cap must remain in accumulation or be withdrawn
- Cap is indexed annually in $100k increments

**What changes phase by phase:**

| Phase | Earnings tax | Drawdown required | Contributions allowed |
|---|---|---|---|
| Accumulation | 15% | None | Yes — up to concessional cap |
| Transition to Retirement | 15% | Min 4%, max 10% | Yes |
| Pension (retirement) | 0% | Min rates above apply | No further concessional |
| Post-Transfer Balance Cap excess | 15% | None | No |
        """)

    with st.expander("Age Pension — NOT MODELLED"):
        st.error("Age Pension is not included in this model. This significantly affects retirement sustainability for many Australian clients.")
        st.markdown("""
| | |
|---|---|
| **Eligibility age** | 67 (born after 1 January 1957) |
| **Assets test** | Homeowners: $314,000 (single) / $470,000 (couple) full pension threshold |
| **Income test** | $204 p.f. (single) / $360 p.f. (couple) free area |
| **Action** | Assess separately via [Services Australia](https://www.servicesaustralia.gov.au) |
        """)

    with st.expander("Tax on super contributions"):
        st.markdown("""
| | |
|---|---|
| **Standard rate** | 15% on concessional contributions |
| **High income** | 30% for income above $250,000 (Division 293) |
| **Earnings tax** | 15% on investment earnings in accumulation phase |
| **In this model** | **NOT DEDUCTED** — contributions treated as gross |
| **Impact** | Actual super growth will be lower than modelled, especially for high income clients |
        """)

    with st.expander("What IS and IS NOT modelled"):
        col1,col2=st.columns(2)
        with col1:
            st.markdown("**✓ Is modelled**")
            st.markdown("""
- SG contributions at 11.5%
- 7% investment growth (net of fees assumption)
- Annual principal debt repayment
- Accumulation compounding over time
- Basic risk flag thresholds
            """)
        with col2:
            st.markdown("**✗ Not modelled**")
            st.markdown("""
- Contributions tax (15%)
- Division 293 tax
- Fund management fees explicitly
- Concessional cap breach
- Catch-up contributions
- Age Pension
- Transfer Balance Cap
- Pension phase tax treatment
- Inflation
- Income growth
- Sequence of returns risk
- Interest rate changes on mortgage
- SG rise to 12% (July 2025)
            """)

    with st.expander("Review triggers — when to update this tool"):
        st.markdown("""
| Trigger | When |
|---|---|
| Federal Budget | May annually |
| SG rate rise to 12% | **1 July 2025** |
| Contribution cap indexation | Check each July |
| Transfer Balance Cap indexation | Check each July |
| Any superannuation legislation change | As announced |
        """)

# ════════════════════════════════════════════════════════════════
# MODEL & LIMITATIONS
# ════════════════════════════════════════════════════════════════
with t_model:
    st.markdown("### Understanding This Model & Its Limitations")
    st.caption("This tab explains exactly how the model works, what it does well, where it approximates, and what it does not model at all. Read before using outputs in client conversations.")

    st.info(f"Model snapshot: {gr*100:.1f}% growth · {sg*100:.1f}% SG · ${rep:,} repayment · {yrs} yr projection · today's dollars · v{APP_VERSION} {APP_BUILD_DATE}")

    # ── WHAT THIS MODEL IS ───────────────────────────────────────
    with st.expander("What this model is — and what it is not", expanded=True):
        st.markdown("""
This is an **accumulation-phase illustration tool** for Australian financial planning conversations.

It is designed to show clients how strategic decisions compound over time — not to produce guaranteed projections or replace a Statement of Advice.

**It is appropriate for:**
- Illustrating the long-run impact of income, expense, and debt strategies
- Comparing scenarios side by side in a planning conversation
- Identifying which financial vulnerabilities matter most (shock analysis)
- Supporting a pre-retirement readiness conversation

**It is not appropriate for:**
- Producing legally compliant projections for a Statement of Advice
- Tax advice or superannuation fund-specific modelling
- Replacing actuary or specialist retirement income modelling
- Clients with complex structures (SMSF, trusts, multiple properties, business assets)
        """)

    # ── HOW THE NUMBERS WORK ─────────────────────────────────────
    with st.expander("How the numbers work — formulas and assumptions"):
        st.markdown(f"""
Every projection runs the same annual loop from year 0 to year {yrs}:

| Component | Formula | Current value |
|---|---|---|
| Super (year end) | `prior × (1 + gr) + income × sg` | gr={gr*100:.1f}%, sg={sg*100:.1f}% |
| Portfolio (year end) | `prior × (1 + gr) + reinvested surplus` | Surplus = ${max(0,income-expenses-rep):,.0f} p.a. |
| Reinvested surplus | `income − expenses − debt repayment` | ${income:,} − ${expenses:,} − ${rep:,} |
| Debt (year end) | `max(0, prior − repayment)` | ${rep:,} p.a. fixed reduction |
| Net worth | `super + portfolio + cash − debt` | Snapshot each year end |

**Key behaviours:**
- When debt reaches zero, the repayment amount adds to reinvested surplus — this is why projection lines steepen in later years
- Growth rate applies identically to super and portfolio — no asset allocation differentiation
- Cash balance is held flat — not invested or grown
- All figures compound annually, not monthly
        """)

    # ── WHAT IS APPROXIMATED ────────────────────────────────────
    with st.expander("What is approximated — and how"):
        st.markdown(f"""
| Item | How modelled | What this misses | Impact |
|---|---|---|---|
| **Job loss** | Income × (1 − months/12) averaged across year 1 | Not month-by-month — misses cash flow crunch, emergency draw-down timing | Low–medium |
| **Rate rise** | Added to expenses permanently as `debt × rate%` | Not a true P&I recalculation — overstates long-run cost as debt reduces | Medium |
| **Super paused** | Lump sum removed from starting balance | Timing of missed contributions not modelled year by year | Low |
| **Debt repayment** | Fixed ${rep:,} annual principal reduction | Not amortising — interest component not separated from principal | Medium |
| **Compounding** | Annual only | Funds compound monthly or daily — model slightly understates growth | Low |
| **Investment returns** | Single flat {gr*100:.1f}% rate forever | No sequence of returns risk — bad years early hurt far more than modelled | High |
| **Income** | Flat — no growth modelled | Real incomes typically grow with CPI or career progression | Medium |
| **Expenses** | Flat — no inflation | Real costs rise ~2–3% p.a. — model understates long-run expense pressure | Medium |
        """)

    # ── WHAT IS NOT MODELLED ─────────────────────────────────────
    with st.expander("What is not modelled — material omissions"):
        st.error("These omissions are significant. Outputs should be presented as indicative only and caveated accordingly in all client conversations.")
        st.markdown(f"""
| Omission | Why it matters | Workaround |
|---|---|---|
| **Contributions tax (15%)** | Super projections overstated by ~15% for all clients | Mentally discount super figures by ~15% |
| **Division 293 tax** | High-income clients (>$250k) pay 30% on contributions — not 15% | Flag separately for high-income clients |
| **Fund management fees** | Assumed zero — real fees 0.5–1.5% p.a. reduce returns | Reduce growth rate input by estimated fee |
| **Inflation** | All figures in today's dollars — nominal future values higher | Use as relative comparison only, not absolute targets |
| **Age Pension** | Not modelled — significantly affects retirement sustainability | Assess separately via Services Australia calculator |
| **Transfer Balance Cap** | Check only — no tax consequence modelling | Flag for clients approaching $1.9M |
| **Pension phase 0% tax** | Tax saving from moving to pension phase not quantified | Estimate manually: pension assets × {gr*100:.1f}% × 15% = annual saving |
| **Salary sacrifice** | Not modelled as a strategy | Can be approximated by increasing super balance manually |
| **Catch-up contributions** | Not modelled | Relevant for clients with balance below $500k and unused cap space |
| **Insurance** | Not modelled | Life, TPD, income protection not included |
| **Estate planning** | Not modelled | Death benefit nominations, tax on super to non-dependants not included |
| **SMSF** | Not modelled | Use only for MySuper/industry/retail fund clients |
| **Multiple properties** | Not modelled | Investment property cash flow, depreciation, CGT not included |
        """)

    # ── DYNAMIC ACCURACY INDICATORS ──────────────────────────────
    with st.expander("Live accuracy indicators for this client", expanded=True):
        st.markdown("These flags are calculated from the current client inputs and identify where this model's approximations are most likely to affect accuracy.")

        acc_flags = []
        if income > 250000:
            acc_flags.append(("High", "Division 293 applies — super contributions taxed at 30%, not 15%. Super projections materially overstated.", "🔴"))
        else:
            acc_flags.append(("Medium", f"Contributions tax (15%) not deducted — super projection overstated by approximately {fmt(int(super_bal*0.15))} on current balance.", "🟡"))

        if gr > 0.08:
            acc_flags.append(("Medium", f"Growth rate of {gr*100:.1f}% is above long-run Australian balanced fund average (~7%). Projections may be optimistic.", "🟡"))
        else:
            acc_flags.append(("Low", f"Growth rate of {gr*100:.1f}% is within typical long-run range for a balanced fund.", "🟢"))

        if debt > 0:
            acc_flags.append(("Medium", f"Debt repayment modelled as flat ${rep:,} p.a. — not a true P&I amortising schedule. Year-by-year interest not separated.", "🟡"))

        if older_age >= 55:
            acc_flags.append(("High", "Client approaching retirement — Age Pension not modelled. This significantly affects retirement sustainability assessment.", "🔴"))

        if income > 0:
            acc_flags.append(("Medium", "Income held flat for full projection — no career progression or CPI growth modelled. Surplus likely understated in later years.", "🟡"))

        acc_flags.append(("Medium", "Sequence of returns risk not modelled — a bad decade early has far greater impact than shown. Treat year 20 figure as best-case trajectory.", "🟡"))

        for severity, msg, icon in acc_flags:
            colour = "#FCE4D6" if icon=="🔴" else "#FFF3CD" if icon=="🟡" else "#E2F0D9"
            border = "#C00000" if icon=="🔴" else "#E8A838" if icon=="🟡" else "#006100"
            st.markdown(f"<div style='background:{colour};border-left:4px solid {border};padding:10px 14px;border-radius:0 8px 8px 0;font-size:14px;margin-bottom:8px;color:#1B2E4B'>{icon} <strong>{severity} impact:</strong> {msg}</div>", unsafe_allow_html=True)

    # ── INDUSTRY BENCHMARKS ──────────────────────────────────────
    with st.expander("Industry benchmarks used in this model"):
        st.markdown(f"""
| Benchmark | Value used | Source | Current client |
|---|---|---|---|
| Minimum savings rate | 10% of gross income | General planning guidance | {br['savings_rate']*100:.1f}% {"✓" if br['savings_rate']>=0.1 else "✗"} |
| Emergency buffer minimum | 3 months expenses | General planning guidance | {br['emergency_months']:.1f} months {"✓" if br['emergency_months']>=3 else "✗"} |
| High leverage threshold | Debt > 70% of assets | General planning guidance | {br['debt_to_assets']*100:.0f}% {"✓" if br['debt_to_assets']<=0.7 else "✗"} |
| Under-funded super | Balance < 1× annual income | General planning guidance | {"✓" if super_bal>=income else "✗"} |
| Safe withdrawal rate | 4% p.a. | Bengen (1994), widely adopted | Used in pre-retirement and drawdown |
| SG rate | 11.5% (2024–25) | Superannuation Guarantee (Administration) Act 1992 | {sg*100:.1f}% in model |
| Growth rate — conservative | 5% p.a. | General planning guidance | — |
| Growth rate — balanced | 7% p.a. | General planning guidance | {gr*100:.1f}% in model |
| Growth rate — growth | 8–9% p.a. | General planning guidance | — |
| Transfer Balance Cap | $1.9M | ATO 2024–25 | — |
| Concessional contributions cap | $30,000 p.a. | ATO 2024–25 | Not checked in model |

*All benchmarks are planning guidelines only — not guarantees or regulatory requirements unless stated.*
        """)

    # ── HOW TO PRESENT TO CLIENTS ────────────────────────────────
    with st.expander("How to present these outputs to clients"):
        st.markdown("""
**Language to use:**

- *"This shows the direction and order of magnitude — not a guaranteed outcome."*
- *"The gap between these two strategies at year 20 is what we're trying to capture — the exact dollar amount will differ but the relative difference is meaningful."*
- *"This assumes your returns are consistent year to year — in reality they won't be, which is why we hold a buffer."*
- *"The shock analysis shows which risks matter most for your situation specifically — not in general."*

**Language to avoid:**

- ❌ *"You will have $X in 20 years"* — replace with *"the model projects approximately $X under these assumptions"*
- ❌ *"This is what your super will be"* — contributions tax not deducted, actual will be lower
- ❌ *"You're on track for retirement"* — Age Pension and tax not modelled
- ❌ *"This is financial advice"* — this tool produces general information only

**Compliance note:**
This tool does not produce a Statement of Advice. Any recommendation to a client must be made through a licensed financial adviser and documented in a compliant SOA. Always read the disclaimer at the bottom of the Report tab before sharing outputs.
        """)

# ════════════════════════════════════════════════════════════════
# REPORT
# ════════════════════════════════════════════════════════════════
with t_report:
    practice_name = st.text_input(
        "Practice name (for report header)",
        value="[Practice Name]")
    st.markdown("### Pre-Report Checklist")
    st.caption("Review every item below before downloading or sharing this report with a client.")

    checklist_items = [
        ("Growth rate", f"{gr*100:.1f}% p.a.", gr >= 0.05 and gr <= 0.09, "Within typical range (5–9%)" if gr >= 0.05 and gr <= 0.09 else f"⚠ {gr*100:.1f}% is {'above' if gr > 0.09 else 'below'} typical range — consider adjusting or noting in report"),
        ("SG rate", f"{sg*100:.1f}%", sg >= 0.115, "Current for 2024–25" if sg >= 0.115 else "⚠ Below current legislated rate of 11.5% — update in Model Parameters"),
        ("Projection years", f"{yrs} years", yrs >= 10, "Adequate horizon" if yrs >= 10 else "⚠ Short projection — consider extending for long-term planning"),
        ("Emergency buffer", f"{br['emergency_months']:.1f} months", br['emergency_months'] >= 3, "Adequate" if br['emergency_months'] >= 3 else "⚠ Below 3-month minimum — flag with client"),
        ("Savings rate", f"{br['savings_rate']*100:.1f}%", br['savings_rate'] >= 0.1, "Above 10% minimum" if br['savings_rate'] >= 0.1 else "⚠ Below 10% benchmark — wealth accumulation constrained"),
        ("Debt to assets", f"{br['debt_to_assets']*100:.0f}%", br['debt_to_assets'] <= 0.7, "Within benchmark" if br['debt_to_assets'] <= 0.7 else "⚠ Above 70% threshold — note leverage risk"),
        ("Super vs income", f"${super_bal:,} vs ${income:,}", super_bal >= income, "Super above 1× income" if super_bal >= income else "⚠ Super below 1× annual income — review contribution strategy"),
        ("Contributions tax", "Not deducted", False, "⚠ Always note: super projections are gross — actual ~15% lower after contributions tax"),
        ("Age Pension", "Not modelled", False, "⚠ Always note: Age Pension not included — assess via Services Australia for clients 55+"),
        ("Inflation", "Not modelled", False, "⚠ All figures in today's dollars — present as relative comparison, not absolute targets"),
        ("Sequence of returns", "Not modelled", False, "⚠ Flat return assumption overstates certainty — note volatility risk in conversation"),
        ("Division 293", f"Income ${income:,}", income <= 250000, "Not applicable" if income <= 250000 else "⚠ Income above $250k — Division 293 applies, super taxed at 30% not 15%"),
        ("Client age", f"Age {older_age}", True, f"{'Pre-retirement readiness check recommended' if older_age >= 50 else 'Accumulation phase'} {'— drawdown modelling available' if older_age >= 65 else ''}"),
        ("Practice name", practice_name, practice_name != "[Practice Name]", "✓ Set" if practice_name != "[Practice Name]" else "⚠ Practice name not set — update above before downloading"),
    ]

    all_pass = all(ok for _,_,ok,_ in checklist_items if _ != "")
    if all_pass:
        st.success("All checks passed — report is ready to download.")
    else:
        st.warning("Some items require attention before sharing this report with a client. Review red items below.")

    check_html = '<table class="word-table"><thead><tr><th>Check</th><th>Current value</th><th>Status</th><th>Note for consideration</th></tr></thead><tbody>'
    for label, val, ok, note in checklist_items:
        status = "<span style='color:#006100;font-weight:500'>✓ Pass</span>" if ok else "<span style='color:#C00000;font-weight:500'>⚠ Review</span>"
        row_bg = "" if ok else "background:#FFF9F9"
        check_html += f'<tr style="{row_bg}"><td>{label}</td><td>{val}</td><td>{status}</td><td style="font-size:12px;color:#555">{note}</td></tr>'
    check_html += '</tbody></table>'
    st.markdown(check_html, unsafe_allow_html=True)
    st.markdown("---")

    with st.expander("Notes for consideration in analysis — read before client conversation"):
        st.markdown(f"""
**1. Super projections are gross figures**
Contributions tax of 15% (or 30% for Division 293 clients above $250k) is not deducted.
The super balance at year {yrs} should be mentally discounted by approximately 15% when discussing with clients.
Current projected super balance is overstated by this amount.

**2. All figures are in today's dollars**
Inflation is not modelled. A projected net worth of $3M in year {yrs} is $3M in today's purchasing power terms — the nominal figure will be higher but buys the same amount.
Present figures as relative comparisons between scenarios, not as absolute wealth targets.

**3. Returns are assumed constant**
The model uses a flat {gr*100:.1f}% p.a. return every year.
In reality, a bad sequence of returns early in retirement can deplete assets far faster than shown.
The year {yrs} figure represents a best-case smooth trajectory.

**4. Debt repayment is simplified**
The model reduces debt by ${rep:,} p.a. as a fixed principal reduction — not a true P&I amortising schedule.
Actual mortgage repayments include an interest component that reduces over time.
This means the model slightly overstates how quickly the client's net worth improves.

**5. Age Pension not included**
For clients aged 55+, Age Pension eligibility can significantly improve retirement sustainability.
The assets test threshold for homeowners is approximately $314k (single) or $470k (couple) for full pension.
Assess separately via the Services Australia website or a specialist.

**6. Shock analysis shocks are independent**
Each shock runs against the base case only — they are not combined.
In real adverse scenarios (e.g. job loss during a rate rise), the combined impact is worse than any single bar shows.
Use the shock analysis to identify the most material individual vulnerability, then discuss combined scenarios qualitatively.

**7. Income is held flat**
No income growth is modelled. For younger clients, actual income growth over {yrs} years will likely improve outcomes.
The model is conservative in this respect — actual surplus and savings rate will tend to improve over time.

**8. This is not a Statement of Advice**
These outputs are general information only.
Any recommendation must be made through a licensed financial adviser and documented in a compliant SOA.
The disclaimer text is available below and must accompany any client-facing output.
        """)

    st.markdown("---")
    st.markdown("**Report preview**")
    st.markdown(f"Client: **{client_name}** · Generated: **{date.today().strftime('%d %B %Y')}** · Model: Accumulation phase · Growth rate: {gr*100:.1f}% · SG: {sg*100:.1f}% · Repayment: ${rep:,} p.a.")

    disclaimer = (
        f"This report has been prepared by {practice_name} "
        f"using the Client Scenario Engine "
        f"(Version {APP_VERSION}, {APP_BUILD_DATE}). "
        "It contains general financial information only "
        "and does not take into account your individual "
        "objectives, financial situation or needs. "
        "Before acting on this information you should "
        "consider its appropriateness having regard to "
        "your circumstances and seek personal financial "
        "advice from a licensed financial adviser. "
        "Past performance is not a reliable indicator "
        "of future performance. All projections are "
        "based on assumptions stated in this report "
        "and are illustrative only."
    )

    assumptions_block = (
        f"Assumptions: Investment return {gr*100:.1f}% p.a. · "
        f"SG rate {sg*100:.1f}% · "
        f"Annual debt repayment ${rep:,} · "
        f"Projection {yrs} years · "
        "Figures in today's dollars · "
        "Age Pension not modelled · "
        "Contributions tax not deducted."
    )

    leg_block = (
        f"Legislative parameters current as at "
        f"{LEGISLATION_DATE}. Subject to change. "
        "Verify current rates at ato.gov.au before "
        "use in client conversations."
    )

    soa_intro = generate_insight("soa_intro", br,s1r,s2r,bp,s1p,s2p,s1_type,s2_type,yrs,income,expenses,rep,cash,debt,super_bal)
    soa_conc  = generate_insight("soa_conclusion", br,s1r,s2r,bp,s1p,s2p,s1_type,s2_type,yrs,income,expenses,rep,cash,debt,super_bal)
    soa_obs   = generate_insight("summary", br,s1r,s2r,bp,s1p,s2p,s1_type,s2_type,yrs,income,expenses,rep,cash,debt,super_bal)

    risk_html = "".join(f"<span style='background:#FCE4D6;color:#C00000;padding:3px 10px;border-radius:12px;font-size:11px;margin-right:6px'>{f}</span>" for f in bo["risk_flags"]) if bo["risk_flags"] else "<span style='background:#E2F0D9;color:#006100;padding:3px 10px;border-radius:12px;font-size:11px'>No critical risk flags</span>"

    report_html = f"""<html><head><meta charset='utf-8'>
<style>
body{{font-family:'Helvetica Neue',Arial,sans-serif;color:#1B2E4B;padding:48px;max-width:900px;margin:0 auto;line-height:1.7;}}
.header{{background:#1B2E4B;color:white;padding:28px 32px;border-radius:10px;margin-bottom:32px;}}
.header h1{{font-size:24px;margin:0 0 6px;font-weight:400;letter-spacing:.02em;}}
.header p{{margin:0;opacity:.7;font-size:13px;}}
h2{{font-size:15px;border-bottom:2px solid #1B2E4B;padding-bottom:6px;margin-top:36px;text-transform:uppercase;letter-spacing:.06em;}}
h3{{font-size:13px;color:#555;margin-top:24px;}}
p{{font-size:13px;color:#333;}}
.metrics{{display:flex;gap:16px;margin:20px 0;flex-wrap:wrap;}}
.metric{{background:#F8F7F4;border-radius:8px;padding:12px 16px;flex:1;min-width:120px;border:.5px solid #E5E7EB;}}
.metric .label{{font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:#888;margin-bottom:4px;}}
.metric .value{{font-size:18px;font-weight:600;color:#1B2E4B;}}
.insight{{background:#F8F7F4;border-left:4px solid #1B2E4B;padding:14px 18px;border-radius:0 8px 8px 0;margin:16px 0;font-size:13px;}}
.insight ul{{margin:8px 0 0;padding-left:1.2rem;}}
.insight li{{margin-bottom:6px;}}
table{{width:100%;border-collapse:collapse;margin:16px 0;font-size:12px;}}
th{{background:#F2F2F2;border-top:2px solid #1B2E4B;border-bottom:2px solid #1B2E4B;padding:8px 12px;text-align:right;text-transform:uppercase;font-size:10px;letter-spacing:.04em;}}
th:first-child{{text-align:left;}}
td{{border-bottom:.5px solid #E5E7EB;padding:8px 12px;text-align:right;}}
td:first-child{{text-align:left;}}
.pos{{background:#E2F0D9;color:#006100;font-weight:500;}}
.neg{{background:#FCE4D6;color:#C00000;font-weight:500;}}
.disc{{font-size:11px;color:#888;line-height:1.7;margin-top:32px;border-top:1px solid #eee;padding-top:16px;}}
.flag{{display:inline-block;padding:3px 10px;border-radius:12px;font-size:11px;margin-right:6px;}}
</style></head><body>
<div class='header'>
  <h1>Financial Scenario Analysis</h1>
  <p>{client_name} &nbsp;·&nbsp; {date.today().strftime('%d %B %Y')} &nbsp;·&nbsp; Prepared by {practice_name}</p>
</div>

<h2>Introduction</h2>
<p>{"".join(soa_intro)}</p>

<h2>Current Financial Position</h2>
<div class='metrics'>
  <div class='metric'><div class='label'>Net Position</div><div class='value'>{fmt(br["net_position"])}</div></div>
  <div class='metric'><div class='label'>Annual Surplus</div><div class='value'>{fmt(br["surplus"])}</div></div>
  <div class='metric'><div class='label'>Savings Rate</div><div class='value'>{br["savings_rate"]*100:.1f}%</div></div>
  <div class='metric'><div class='label'>Emergency Buffer</div><div class='value'>{br["emergency_months"]:.1f} mo</div></div>
  <div class='metric'><div class='label'>Debt to Assets</div><div class='value'>{br["debt_to_assets"]*100:.0f}%</div></div>
</div>
<p><strong>Risk flags:</strong> {risk_html}</p>

<h2>Balance Sheet — Base Case</h2>{html}

<h2>Scenario Comparison</h2>{html2 if 'html2' in locals() else '<p>No scenarios configured.</p>'}

<h2>Projection Milestones</h2>{html3}

<h2>Planning Observations</h2>
<div class='insight'><ul>{"".join(f"<li>{p}</li>" for p in soa_obs)}</ul></div>

<h2>Conclusion and Recommendations</h2>
<div class='insight'><ul>{"".join(f"<li>{p}</li>" for p in soa_conc)}</ul></div>

<p class='disc'>{assumptions_block}</p>
<p class='disc'>{leg_block}</p>
<p class='disc'>{disclaimer}</p>
</body></html>"""

    st.download_button("⬇ Download HTML report", data=report_html.encode("utf-8"),
        file_name=f"Financial_Report_{client_name.replace(' ','_')}_{date.today()}.html",
        mime="text/html")

    if st.button("Copy disclaimer text"):
        st.code(disclaimer)
        st.info("Select all text above and copy.")

    st.markdown("---")
    st.markdown(f"<div style='font-size:11px;color:#888;line-height:1.7'>{assumptions_block}</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:11px;color:#888;line-height:1.7;margin-top:6px'>{leg_block}</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:11px;color:#888;line-height:1.7;margin-top:6px'>{disclaimer}</div>", unsafe_allow_html=True)
