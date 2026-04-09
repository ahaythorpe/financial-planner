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
    page_title="Financial Scenario Planner",
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
  <h1>Financial Scenario Planner</h1>
  <p>{client_name} &nbsp;·&nbsp; Age {age_1}/{age_2} &nbsp;·&nbsp; {date.today().strftime('%d %B %Y')} &nbsp;·&nbsp; Australian accumulation phase model &nbsp;·&nbsp; v{APP_VERSION}</p>
</div>""", unsafe_allow_html=True)

# ── Tabs ─────────────────────────────────────────────────────────
t_about, t_dash, t_scen, t_shock, t_proj, t_life, t_leg, t_report = st.tabs([
    "About", "Client Dashboard", "Scenario Analysis",
    "Shock Analysis", "Projection", "Life Stage",
    "Legislation", "Report"])

# ════════════════════════════════════════════════════════════════
# ABOUT TAB
# ════════════════════════════════════════════════════════════════
with t_about:
    st.markdown("### Financial Scenario Planner — Australian Edition")
    st.caption("Illustration tool for financial planning professionals · Not financial advice")

    with st.expander("What this tool is and why it was built", expanded=True):
        st.markdown("""
This tool models the financial journey of an Australian client across three phases:

- **Accumulation** — building wealth while working
- **Pre-retirement** — checking readiness to stop working *(coming soon)*
- **Retirement drawdown** — managing drawdown of accumulated assets *(coming soon)*

It was built because financial planning concepts are often explained in isolation.
This tool shows how phases connect — how decisions made at 35 compound into outcomes at 65.

**This is an illustration tool.** It does not replace a Statement of Advice, licensed financial
advice, or superannuation fund projections. All outputs are indicative only.

**Sarah and Daniel are a locked demonstration case.** Their values cannot be changed.
They illustrate a typical Australian couple in the accumulation phase.
All other client inputs are fully editable via the sidebar.
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

**PRE-RETIREMENT PHASE** *(coming soon)*

Client is still working but retirement is within 15 years. Readiness check added on top of accumulation.

Target super at retirement = desired income ÷ 4%
*(Example: $80,000 target ÷ 0.04 = $2,000,000 needed)*

The 4% is the internationally recognised safe withdrawal rate — indicative only, not a guarantee.

---

**RETIREMENT DRAWDOWN PHASE** *(coming soon)*

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
# CLIENT DASHBOARD
# ════════════════════════════════════════════════════════════════
with t_dash:
    st.caption(f"Assumptions: {gr*100:.1f}% growth · {sg*100:.1f}% SG · ${rep:,} repayment · {yrs} yr projection · today's dollars · Age Pension not modelled")
    if older_age >= 67:
        st.error("This client has reached retirement age (67). Retirement drawdown modelling coming soon.")
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
        cells = f'<td class="{cc(bv) if kind=="currency" else ""}">{fmtc(bv,kind)}</td>'
        for r in all_results:
            v = r[key]
            cells += f'<td class="{cc(v) if kind=="currency" else ""}">{fmtc(v,kind)}</td>'
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

    col_a, col_b = st.columns(2)

    with col_a:
        from matplotlib.patches import Patch
        fig, ax = plt.subplots(figsize=(11, max(4, 0.9*len(scen_labels))))
        for i, sc in enumerate(scen_clients):
            inc = sc["income"] if sc["income"] else 1
            exp_pct = sc["expenses"] / inc
            rep_pct = min(rep / inc, max(0, 1 - exp_pct))
            sur_pct = max(0, 1 - exp_pct - rep_pct)
            ax.barh(i, exp_pct, color="#FCE4D6", edgecolor="#C00000", linewidth=0.8, zorder=3)
            ax.barh(i, rep_pct, left=exp_pct, color="#FFF3CD", edgecolor="#E8A838", linewidth=0.8, zorder=3)
            ax.barh(i, sur_pct, left=exp_pct+rep_pct, color="#E2F0D9", edgecolor="#006100", linewidth=0.8, zorder=3)
            if exp_pct > 0.08:
                ax.text(exp_pct/2, i, f"{exp_pct*100:.0f}%", ha="center", va="center", fontsize=7, color="#C00000", fontweight="bold")
            if rep_pct > 0.08:
                ax.text(exp_pct+rep_pct/2, i, f"{rep_pct*100:.0f}%", ha="center", va="center", fontsize=7, color="#7a5c00", fontweight="bold")
            if sur_pct > 0.08:
                ax.text(exp_pct+rep_pct+sur_pct/2, i, f"{sur_pct*100:.0f}%", ha="center", va="center", fontsize=7, color="#006100", fontweight="bold")
        ax.axvline(0.9, color=NAVY, linewidth=1, linestyle=":", zorder=4)
        ax.text(0.905, len(scen_labels)-0.55, "10% min", fontsize=7, color=NAVY, va="top")
        ax.set_yticks(range(len(scen_labels)))
        ax.set_yticklabels(scen_labels, fontsize=8)
        ax.set_xlim(0, 1.05)
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"{x*100:.0f}%"))
        ax.set_title("Income Allocation by Scenario", fontweight="bold", color=NAVY, pad=8, fontsize=10)
        legend_els = [Patch(facecolor="#FCE4D6", edgecolor="#C00000", label="Expenses"),
                      Patch(facecolor="#FFF3CD", edgecolor="#E8A838", label="Debt repayment"),
                      Patch(facecolor="#E2F0D9", edgecolor="#006100", label="Surplus")]
        ax.legend(handles=legend_els, loc="lower center", bbox_to_anchor=(0.5,-0.18), ncol=3, fontsize=7, framealpha=0.9)
        plt.tight_layout(); st.pyplot(fig); plt.close()
        st.markdown("**Cash flow funnel — base case**")
        stages = [
            ("Gross income",    income,                    NAVY),
            ("After expenses",  max(0,income-expenses),    S1_COLOR),
            ("Reinvestable",    max(0,income-expenses-rep),TEAL),
        ]
        fig_f, ax_f = plt.subplots(figsize=(11, 3))
        for i, (label, val, clr) in enumerate(stages):
            w = val/income if income else 0
            left = (1-w)/2
            ax_f.barh(i, w, left=left, height=0.55,
                color=clr, zorder=3)
            ax_f.text(0.5, i,
                f"{label}\n{fmt(val)}",
                ha="center", va="center",
                fontsize=9, fontweight="bold",
                color="white")
        ax_f.set_xlim(0, 1)
        ax_f.set_ylim(-0.5, 2.5)
        ax_f.set_xticks([])
        ax_f.set_yticks([])
        for sp in ax_f.spines.values():
            sp.set_visible(False)
        ax_f.set_title("Cash Flow Funnel — Base Case",
            fontweight="bold", color=NAVY,
            pad=8, fontsize=10)
        plt.tight_layout()
        st.pyplot(fig_f)
        plt.close()
        render_insight(generate_insight("cashflow",
            br,s1r,s2r,bp,s1p,s2p,s1_type,s2_type,
            yrs,income,expenses,rep,cash,debt,super_bal))

    with col_b:
        fig, ax = plt.subplots(figsize=(11, 5))
        yrs_idx = bs_proj.index
        assets_s = bs_proj["Assets"] / 1e6
        liab_s   = bs_proj["Liabilities"] / 1e6
        nw_s     = bs_proj["Net Worth"] / 1e6
        ax.fill_between(yrs_idx, 0, assets_s, alpha=0.15, color=NAVY)
        ax.fill_between(yrs_idx, 0, liab_s,   alpha=0.15, color="#C00000")
        ax.plot(yrs_idx, assets_s, color=NAVY,     linewidth=2,   label="Total assets")
        ax.plot(yrs_idx, liab_s,   color="#C00000", linewidth=2,   linestyle="--", label="Total liabilities")
        ax.plot(yrs_idx, nw_s,     color=TEAL,     linewidth=2.5, label="Net position")
        ax.axhline(0, color="#ccc", linewidth=0.8)
        crossover = next((y for y in yrs_idx if bs_proj.loc[y,"Net Worth"] > 0), None)
        if crossover is not None:
            ax.axvline(crossover, color=TEAL, linewidth=1, linestyle=":")
            y_ann = float(nw_s.max()) * 0.18
            ax.annotate("Net positive", xy=(crossover, 0),
                        xytext=(crossover+max(1,yrs*0.05), y_ann),
                        fontsize=8, color=TEAL,
                        arrowprops=dict(arrowstyle="->", color=TEAL, lw=1))
        ax.set_title("Balance Sheet Dynamics — Base Case", fontweight="bold", color=NAVY, pad=8, fontsize=10)
        ax.set_xlabel("Year", color=NAVY)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"${x:.1f}M"))
        ax.legend(loc="lower right", fontsize=8, framealpha=0.9)
        plt.tight_layout(); st.pyplot(fig); plt.close()
        render_insight(generate_insight("balance",
            br,s1r,s2r,bp,s1p,s2p,s1_type,s2_type,
            yrs,income,expenses,rep,cash,debt,super_bal))

    # ── Row 2: Milestone Comparison (full width) ─────────────────
    milestones_c = [y for y in [0,5,10,15,20] if y<=yrs]
    n_sc = len(scen_projs)
    bar_w = min(0.8/n_sc, 0.25)
    x_pos = np.arange(len(milestones_c))
    fig, ax = plt.subplots(figsize=(12, 5))
    for i, (proj, lbl, clr) in enumerate(zip(scen_projs, scen_labels, scen_colors)):
        vals = [proj.loc[y,"Net Worth"]/1e6 if y in proj.index else 0 for y in milestones_c]
        offset = (i - n_sc/2 + 0.5) * bar_w
        b3 = ax.bar(x_pos+offset, vals, width=bar_w*0.9, color=clr, label=lbl, zorder=3)
        for bar,v in zip(b3, vals):
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.01,
                    f"${v:.1f}M", ha="center", va="bottom",
                    fontsize=6.5, fontweight="bold", color=clr, rotation=40)
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

    # PANEL 1 — Asset mix
    st.markdown("#### Asset composition")
    p1c,p1i = st.columns([3,2])
    with p1c:
        fig,ax=plt.subplots(figsize=(6,4))
        ax.pie([super_bal,invest,cash],
            labels=["Super","Investments","Cash"],
            colors=[NAVY,S1_COLOR,TEAL],
            autopct="%1.0f%%",startangle=90,
            wedgeprops={"linewidth":1.5,"edgecolor":"white"},
            textprops={"fontsize":9})
        ax.set_title("Asset Mix — Base Case",
            fontweight="bold",color=NAVY,pad=10,fontsize=10)
        plt.tight_layout(); st.pyplot(fig); plt.close()
    with p1i:
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
        st.markdown("<div style='height:1rem'></div>",unsafe_allow_html=True)
        render_insight(pts1)
    st.markdown("---")

    # PANEL 2 — Net position by scenario
    st.markdown("#### Net position by scenario")
    p2c,p2i = st.columns([3,2])
    with p2c:
        nv=[br["net_position"],s1r["net_position"],
            s2r["net_position"]]+ \
            [eo["results"]["net_position"]
             for _,eo,_ in extra_outputs]
        nl=(["Base",s1_type,s2_type]+
            [e["scenario_name"] for e in extras])
        bc=[BG_NEG if v<0 else BG_POS for v in nv]
        be=[TXT_NEG if v<0 else TXT_POS for v in nv]
        fig,ax=plt.subplots(figsize=(6,4))
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
            fontweight="bold",color=NAVY,pad=10,fontsize=10)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(
            lambda x,_:f"${x/1000:.0f}k"))
        plt.xticks(fontsize=8)
        plt.tight_layout(); st.pyplot(fig); plt.close()
    with p2i:
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
        st.markdown("<div style='height:1rem'></div>",unsafe_allow_html=True)
        render_insight(pts2)
    st.markdown("---")

    # PANEL 3 — 20-year projection
    st.markdown(f"#### {yrs}-year wealth projection")
    p3c,p3i = st.columns([3,2])
    with p3c:
        fig,ax=plt.subplots(figsize=(6,4))
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
                xy=(last,v/1e6),fontsize=8,
                fontweight="bold",color=clr,va="center")
        ax.set_xlabel("Year",color=NAVY)
        ax.set_ylabel("Net Worth ($M)",color=NAVY)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(
            lambda x,_:f"${x:.1f}M"))
        ax.legend(framealpha=.9,fontsize=8,loc="upper left")
        ax.set_title(f"{yrs}-Year Net Worth Projection",
            fontweight="bold",color=NAVY,pad=10,fontsize=10)
        plt.tight_layout(); st.pyplot(fig); plt.close()
    with p3i:
        b20=bp.iloc[-1]["Net Worth"]
        best20=max(b20,s1p.iloc[-1]["Net Worth"],
            s2p.iloc[-1]["Net Worth"])
        best20n=("Base Case" if best20==b20
            else s1_type if best20==s1p.iloc[-1]["Net Worth"]
            else s2_type)
        gap20=best20-min(b20,s1p.iloc[-1]["Net Worth"],
            s2p.iloc[-1]["Net Worth"])
        cx=next((int(y) for y,r in bp.iterrows()
            if r["Net Worth"]>0),None)
        pts3=[]
        pts3.append(f"{best20n} projects the strongest year {yrs} outcome at ${best20/1e6:.2f}M.")
        pts3.append(f"Scenario gap at year {yrs}: ${gap20/1e6:.2f}M — compounding amplifies early surplus differences.")
        if cx and cx>0:
            pts3.append(f"Net worth turns positive in year {cx} — growth accelerates as debt clears.")
        pts3.append("Small strategy differences today create large wealth divergence over 20 years.")
        st.markdown("<div style='height:1rem'></div>",unsafe_allow_html=True)
        render_insight(pts3)

# ════════════════════════════════════════════════════════════════
# SHOCK ANALYSIS
# ════════════════════════════════════════════════════════════════
with t_shock:
    st.caption(f"Assumptions: {gr*100:.1f}% growth · {sg*100:.1f}% SG · ${rep:,} repayment · {yrs} yr projection · today's dollars · Age Pension not modelled")
    st.markdown("### Shock Analysis")
    st.caption("Each bar shows the isolated impact of a single adverse event on year 20 net worth vs the base case. Shocks are independent — each runs against the base case only, not combined. Use sliders to adjust magnitude. The longest bar identifies this client's biggest financial vulnerability.")
    st.markdown("**Adjust shock magnitudes**")
    c1,c2 = st.columns(2)
    with c1:
        sh_inc = st.slider("Income reduction (%)",   5,50,20,5)
        sh_exp = st.slider("Expense increase (%)",   5,50,20,5)
        sh_ret = st.slider("Investment returns drop — use % p.a.",1,6,3,1)
        sh_job = st.slider("Job loss (months)",      1,24,6,1)
    with c2:
        sh_rate= st.slider("Interest rate rise (%)", 1,5,2,1)
        sh_sup = st.slider("Super paused (years)",   1,10,3,1)
        sh_dbt = st.slider("Debt increase (%)",      5,30,10,5)

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

    fig,ax=plt.subplots(figsize=(10,4))
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
        html2 += f'<tr><td>{label}</td><td class="{cc(ds)}">{fmt(ds)}</td><td class="{cc(dn)}">{fmt(dn)}</td><td class="{cc(dy20)}">{fmt(dy20)}</td></tr>'
    html2 += '</tbody></table>'
    st.markdown(html2, unsafe_allow_html=True)
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
    ax.plot(bp.index,bp["Net Worth"]/1e6,color=NAVY,linewidth=2.5,label="Base Case",zorder=3)
    for label,r,proj,clr in all_scenarios:
        ls = "--" if "Income" in label else ":" if "Debt" in label else "-."
        ax.plot(proj.index,proj["Net Worth"]/1e6,color=clr,linewidth=2,linestyle=ls,label=label,zorder=3)
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

    st.markdown("""
    <div style='background:#E6F1FB;border-radius:10px;padding:1rem 1.25rem;margin-bottom:12px;
    border:1px solid #B5D4F4'>
    <div style='font-size:11px;text-transform:uppercase;letter-spacing:.08em;
    color:#185FA5;margin-bottom:4px'>Active — Accumulation phase</div>
    <div style='font-size:14px;font-weight:500;color:#1B2E4B'>Building wealth while working</div>
    <div style='font-size:12px;color:#444;margin-top:6px'>
    Super grows at 7% + SG contributions. Portfolio grows from reinvested surplus.
    Debt reduces by annual repayment.
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
        margin-bottom:12px;border:0.5px solid #E5E7EB;opacity:0.7'>
        <div style='font-size:11px;text-transform:uppercase;letter-spacing:.08em;
        color:#aaa;margin-bottom:4px'>Coming soon — Pre-Retirement phase</div>
        <div style='font-size:13px;color:#888'>
        Available when client age reaches 50. Models retirement readiness —
        target super, readiness gap, and years to close shortfall.
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
    margin-bottom:12px;border:0.5px solid #E5E7EB;opacity:0.7'>
    <div style='font-size:11px;text-transform:uppercase;letter-spacing:.08em;
    color:#aaa;margin-bottom:4px'>Coming soon — Retirement Drawdown phase</div>
    <div style='font-size:13px;color:#888'>
    Models sustainable income from accumulated assets.
    4% drawdown rule · asset depletion age · sustainable income level.
    Age Pension not modelled.
    </div></div>""", unsafe_allow_html=True)

    st.markdown("""
    <div style='background:#F8F7F4;border-radius:10px;padding:1rem 1.25rem;
    border:0.5px solid #E5E7EB;opacity:0.7'>
    <div style='font-size:11px;text-transform:uppercase;letter-spacing:.08em;
    color:#aaa;margin-bottom:4px'>Planned — Pension Phase</div>
    <div style='font-size:13px;color:#888'>
    Transfer Balance Cap management · tax-free pension phase · Age Pension interaction.
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
# REPORT
# ════════════════════════════════════════════════════════════════
with t_report:
    practice_name = st.text_input(
        "Practice name (for report header)",
        value="[Practice Name]")
    st.markdown("**Report preview**")
    st.markdown(f"Client: **{client_name}** · Generated: **{date.today().strftime('%d %B %Y')}** · Model: Accumulation phase · Growth rate: {gr*100:.1f}% · SG: {sg*100:.1f}% · Repayment: ${rep:,} p.a.")

    disclaimer = (
        f"This report has been prepared by {practice_name} "
        f"using the Financial Scenario Planner "
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

    report_html = f"""<html><head><meta charset='utf-8'>
<style>body{{font-family:sans-serif;color:#1B2E4B;padding:40px;}}
h1{{font-size:22px;}}h2{{font-size:15px;border-bottom:2px solid #1B2E4B;padding-bottom:5px;margin-top:28px;}}
table{{width:100%;border-collapse:collapse;margin-bottom:20px;font-size:12px;}}
th{{background:#F2F2F2;border-top:2px solid #1B2E4B;border-bottom:2px solid #1B2E4B;padding:7px 11px;text-align:right;}}
th:first-child{{text-align:left;}}td{{border-bottom:.5px solid #E5E7EB;padding:7px 11px;text-align:right;}}
td:first-child{{text-align:left;}}.pos{{background:#E2F0D9;color:#006100;font-weight:500;}}
.neg{{background:#FCE4D6;color:#C00000;font-weight:500;}}.disc{{font-size:11px;color:#888;line-height:1.7;margin-top:28px;border-top:1px solid #eee;padding-top:14px;}}
</style></head><body>
<h1>Financial Scenario Analysis</h1>
<p><strong>{client_name}</strong> · {date.today().strftime('%d %B %Y')}</p>
<p style='font-size:12px;color:#888'>Growth rate: {gr*100:.1f}% · SG rate: {sg*100:.1f}% · Annual repayment: ${rep:,} · Projection: {yrs} years</p>
<h2>Balance Sheet — Base Case</h2>{html}
<h2>Scenario Comparison</h2>{html2 if 'html2' in locals() else ''}
<h2>Projection Milestones</h2>{html3}
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
