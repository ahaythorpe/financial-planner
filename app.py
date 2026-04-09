import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from datetime import date

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

def fmt(v):
    if v is None or (isinstance(v,float) and np.isnan(v)): return ""
    return f"${v:,.0f}" if v>=0 else f"(${abs(v):,.0f})"

def cc(v):
    if not isinstance(v,(int,float)) or np.isnan(v): return ""
    return "cell-pos" if v>0 else "cell-neg" if v<0 else ""

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
all_scenarios  = [(f"Scenario 1 — {s1_type}",s1r,s1p,S1_COLOR)] + \
                 [(f"Scenario 2 — {s2_type}",s2r,s2p,TEAL)] + \
                 [(e["scenario_name"],eo["results"],ep,EXTRA_COLORS[i%len(EXTRA_COLORS)]) for i,(e,eo,ep) in enumerate(extra_outputs)]

# ── Header ───────────────────────────────────────────────────────
if demo_mode:
    st.markdown('<div class="demo-banner">Viewing Sarah &amp; Daniel demonstration case — inputs are locked. Switch to New Client to enter your own figures.</div>', unsafe_allow_html=True)

st.markdown(f"""
<div class="report-header">
  <h1>Financial Scenario Planner</h1>
  <p>{client_name} &nbsp;·&nbsp; Age {age_1}/{age_2} &nbsp;·&nbsp; {date.today().strftime('%d %B %Y')} &nbsp;·&nbsp; Australian accumulation phase model</p>
</div>""", unsafe_allow_html=True)

# ── Tabs ─────────────────────────────────────────────────────────
t_about, t_dash, t_scen, t_shock, t_proj, t_leg, t_report = st.tabs([
    "About", "Client Dashboard", "Scenario Analysis",
    "Shock Analysis", "Projection", "Legislation", "Report"])

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

    col1,col2,col3 = st.columns(3)
    colors = [NAVY,S1_COLOR,TEAL]+EXTRA_COLORS[:len(extras)]
    lbs    = ["Base"]+[s1_type,s2_type]+[e["scenario_name"] for e in extras]
    sur_v  = [br["surplus"],s1r["surplus"],s2r["surplus"]]+[eo["results"]["surplus"] for _,eo,_ in extra_outputs]
    net_v  = [br["net_position"],s1r["net_position"],s2r["net_position"]]+[eo["results"]["net_position"] for _,eo,_ in extra_outputs]

    with col1:
        fig,ax=plt.subplots(figsize=(4,3.5))
        bars=ax.bar(lbs,sur_v,color=colors[:len(lbs)],width=.5,zorder=3)
        ax.set_title("Annual Surplus",fontweight="bold",color=NAVY,pad=8,fontsize=10)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_:f"${x/1000:.0f}k"))
        ax.set_ylim(0,max(sur_v)*1.3)
        for b,v in zip(bars,sur_v):
            ax.text(b.get_x()+b.get_width()/2,b.get_height()+max(sur_v)*.03,f"${v:,.0f}",ha="center",va="bottom",fontsize=7,fontweight="bold",color=NAVY)
        plt.xticks(fontsize=8); plt.tight_layout(); st.pyplot(fig); plt.close()

    with col2:
        fig,ax=plt.subplots(figsize=(4,3.5))
        bars=ax.bar(lbs,net_v,color=colors[:len(lbs)],width=.5,zorder=3)
        ax.axhline(0,color="#bbb",linewidth=.8,linestyle="--")
        ax.set_title("Net Position",fontweight="bold",color=NAVY,pad=8,fontsize=10)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_:f"${x/1000:.0f}k"))
        spread=max(abs(v) for v in net_v)
        for b,v in zip(bars,net_v):
            ax.text(b.get_x()+b.get_width()/2,v+spread*.05*(1 if v>=0 else -1),fmt(v),ha="center",va="bottom" if v>=0 else "top",fontsize=7,fontweight="bold",color=NAVY)
        plt.xticks(fontsize=8); plt.tight_layout(); st.pyplot(fig); plt.close()

    with col3:
        fig,ax=plt.subplots(figsize=(4,3.5))
        ax.pie([super_bal,invest,cash],labels=["Super","Invest","Cash"],
               colors=[NAVY,S1_COLOR,TEAL],autopct="%1.0f%%",startangle=90,
               wedgeprops={"linewidth":1.5,"edgecolor":"white"},textprops={"fontsize":8})
        ax.set_title("Asset Mix\n(Base Case)",fontweight="bold",color=NAVY,pad=8,fontsize=10)
        plt.tight_layout(); st.pyplot(fig); plt.close()

# ════════════════════════════════════════════════════════════════
# SHOCK ANALYSIS
# ════════════════════════════════════════════════════════════════
with t_shock:
    st.caption(f"Assumptions: {gr*100:.1f}% growth · {sg*100:.1f}% SG · ${rep:,} repayment · {yrs} yr projection · today's dollars · Age Pension not modelled")
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
    ax.set_title(f"Impact on year {min(yrs,20)} net worth vs base case",fontweight="bold",color=NAVY,pad=10)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_:fmt(x)))
    for bar,v in zip(bars,vals_s):
        ax.text(v+(max(abs(v) for v in vals_s)*.02)*(1 if v>=0 else -1),
                bar.get_y()+bar.get_height()/2,fmt(v),
                va="center",ha="left" if v>=0 else "right",fontsize=9,fontweight="bold",
                color=TXT_POS if v>=0 else TXT_NEG)
    plt.tight_layout(); st.pyplot(fig); plt.close()

    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
    th2 = "<th>Surplus impact</th><th>Net position impact</th><th>Year 20 impact</th>"
    html2 = f'<table class="word-table"><thead><tr><th>Shock</th>{th2}</tr></thead><tbody>'
    for label,nw in shocks:
        if "Income" in label:
            sc = create_scenario(base_client, {"income": int(income*(1-sh_inc/100))})
        elif "Expense" in label:
            sc = create_scenario(base_client, {"expenses": int(expenses*(1+sh_exp/100))})
        elif "Returns" in label:
            sc = base_client
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
    st.markdown("**Report preview**")
    st.markdown(f"Client: **{client_name}** · Generated: **{date.today().strftime('%d %B %Y')}** · Model: Accumulation phase · Growth rate: {gr*100:.1f}% · SG: {sg*100:.1f}% · Repayment: ${rep:,} p.a.")

    disclaimer = """This report has been prepared using the Financial Scenario Planner, an illustration tool for use by Australian financial planning professionals. All projections are indicative only and based on the assumptions stated above. This report does not constitute financial advice and should not be relied upon as such. Past performance is not indicative of future results. Legislative parameters are current as at 2024–25 and are subject to change. Recipients should obtain professional financial advice before making any financial decisions."""

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
<p class='disc'>{disclaimer}</p>
</body></html>"""

    st.download_button("⬇ Download HTML report", data=report_html.encode("utf-8"),
        file_name=f"Financial_Report_{client_name.replace(' ','_')}_{date.today()}.html",
        mime="text/html")

    if st.button("Copy disclaimer text"):
        st.code(disclaimer)
        st.info("Select all text above and copy.")

    st.markdown("---")
    st.markdown(f"<div style='font-size:11px;color:#888;line-height:1.7'>{disclaimer}</div>", unsafe_allow_html=True)
