"""
Financial Planner — Streamlit Application
Client scenario analysis: balance sheet, comparison, charts, and projections.
"""

import io
import base64
import datetime
import warnings

warnings.filterwarnings("ignore")

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import streamlit as st

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Financial Planner",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Colour palette ────────────────────────────────────────────────────────────
NAVY     = "#1B2E4B"
S1_COLOR = "#6B3FA0"
TEAL     = "#1D9E75"
BG_POS   = "#E2F0D9"
TXT_POS  = "#006100"
BG_NEG   = "#FCE4D6"
TXT_NEG  = "#C00000"
EXTRA_COLORS = ["#4E79A7", "#B07AA1", "#9C755F", "#76B7B2", "#D7B5A6", "#499894"]

plt.rcParams.update({
    "font.family":       "sans-serif",
    "font.size":         10,
    "figure.facecolor":  "white",
    "axes.facecolor":    "white",
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.grid":         True,
    "grid.alpha":        0.25,
    "grid.linestyle":    "--",
})

TOTAL_ROWS = {"TOTAL ASSETS", "TOTAL LIABILITIES", "NET POSITION"}

WORD_STYLES = [
    {"selector": "caption",
     "props": "font-size:13pt; font-weight:bold; text-align:left; "
              "padding:10px 0 6px 0; color:" + NAVY + ";"},
    {"selector": "table",
     "props": "border-collapse:collapse; background-color:white; width:100%;"},
    {"selector": "thead th",
     "props": ("background:#F2F2F2; color:" + NAVY + "; font-weight:bold; "
               "border-top:2px solid " + NAVY + "; border-bottom:2px solid " + NAVY + "; "
               "border-left:1px solid #D0D0D0; border-right:1px solid #D0D0D0; "
               "padding:8px 14px; font-size:10pt;")},
    {"selector": "th.col_heading",
     "props": "text-align:center; color:" + NAVY + ";"},
    {"selector": "th.row_heading",
     "props": ("text-align:left; color:" + NAVY + "; font-weight:bold; "
               "background:white; border:1px solid #D0D0D0; padding:8px 14px;")},
    {"selector": "td",
     "props": ("border:1px solid #D0D0D0; padding:8px 14px; text-align:right; "
               "font-variant-numeric:tabular-nums; font-size:10pt; color:" + NAVY + ";")},
]

# ── Preset profiles ───────────────────────────────────────────────────────────
PRESETS = {
    "Young Professional": dict(
        client_name="Alex Chen",
        income=80_000, expenses=55_000,
        super_balance=25_000, investments=10_000, cash=8_000, debt=0,
    ),
    "Sarah & Daniel": dict(
        client_name="Sarah & Daniel",
        income=160_000, expenses=95_000,
        super_balance=120_000, investments=40_000, cash=15_000, debt=420_000,
    ),
    "Pre-Retiree": dict(
        client_name="Margaret & Tom",
        income=140_000, expenses=80_000,
        super_balance=450_000, investments=120_000, cash=40_000, debt=150_000,
    ),
    "High Net Worth": dict(
        client_name="James & Claire",
        income=300_000, expenses=120_000,
        super_balance=600_000, investments=500_000, cash=80_000, debt=200_000,
    ),
}

# ── Life stage configuration ──────────────────────────────────────────────────
LIFE_STAGES = [
    "Early Accumulation (25\u201335)",
    "Accumulation (35\u201350)",
    "Pre-retirement (50\u201365)",
    "Retirement (65+)",
    "Custom",
]

LIFE_STAGE_CONFIG = {
    "Early Accumulation (25\u201335)": dict(
        income=65_000, expenses=45_000,
        super_balance=15_000, investments=5_000, cash=5_000, debt=0,
        proj_years=35,
        description="Building foundations \u2014 longer time horizon, lower starting balances.",
    ),
    "Accumulation (35\u201350)": dict(
        income=160_000, expenses=95_000,
        super_balance=120_000, investments=40_000, cash=15_000, debt=420_000,
        proj_years=20,
        description="Peak earning and wealth-building years \u2014 balance growth with debt reduction.",
    ),
    "Pre-retirement (50\u201365)": dict(
        income=150_000, expenses=80_000,
        super_balance=400_000, investments=100_000, cash=30_000, debt=100_000,
        proj_years=15,
        description="Consolidation phase \u2014 maximise super and eliminate debt before retirement.",
    ),
    "Retirement (65+)": dict(
        income=30_000, expenses=60_000,
        super_balance=600_000, investments=150_000, cash=40_000, debt=0,
        proj_years=20,
        description="Drawdown phase \u2014 projecting asset depletion at 4% annual withdrawal.",
    ),
    "Custom": dict(
        income=160_000, expenses=95_000,
        super_balance=120_000, investments=40_000, cash=15_000, debt=420_000,
        proj_years=20,
        description="All values set manually \u2014 no defaults applied.",
    ),
}


def _apply_preset(name):
    p = PRESETS[name]
    st.session_state.update(p)
    st.session_state.update(dict(
        s1_income=p["income"],       s1_expenses=p["expenses"],
        s1_debt=p["debt"],           s1_cash=p["cash"],
        s1_super=p["super_balance"], s1_inv=p["investments"],
        s2_income=p["income"],       s2_expenses=p["expenses"],
        s2_debt=p["debt"],           s2_cash=p["cash"],
        s2_super=p["super_balance"], s2_inv=p["investments"],
    ))


def _apply_life_stage(stage_name):
    cfg = LIFE_STAGE_CONFIG[stage_name]
    if stage_name != "Custom":
        st.session_state.update({
            "income":        cfg["income"],
            "expenses":      cfg["expenses"],
            "super_balance": cfg["super_balance"],
            "investments":   cfg["investments"],
            "cash":          cfg["cash"],
            "debt":          cfg["debt"],
        })
    st.session_state["proj_years"] = cfg["proj_years"]


def _on_life_stage_change():
    _apply_life_stage(st.session_state["life_stage"])


# ── Session state defaults ────────────────────────────────────────────────────
_BASE = PRESETS["Sarah & Daniel"]
_SS_DEFAULTS = {
    **_BASE,
    "s1_strategy": "Income Improvement", "s1_name": "Income Improvement",
    "s1_income": 180_000, "s1_expenses": 90_000,
    "s1_debt": _BASE["debt"],             "s1_cash": _BASE["cash"],
    "s1_super": _BASE["super_balance"],   "s1_inv": _BASE["investments"],
    "s2_strategy": "Debt Reduction",      "s2_name": "Debt Reduction",
    "s2_income": _BASE["income"],         "s2_expenses": _BASE["expenses"],
    "s2_debt": 350_000,                   "s2_cash": 10_000,
    "s2_super": _BASE["super_balance"],   "s2_inv": _BASE["investments"],
    "extra_scenarios": [],
    "scenario_id_counter": 3,
    "life_stage":            "Accumulation (35\u201350)",
    "proj_years":            20,
    "growth_rate_param":     7.0,
    "sg_rate_param":         11.5,
    "debt_repayment_param":  20_000,
    "inflation_adj":         False,
}
for _k, _v in _SS_DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ── Model functions ───────────────────────────────────────────────────────────
def calculate_financials(client):
    ta  = client["cash"] + client["investments"] + client["super_balance"]
    tl  = client["debt"]
    sur = client["income"] - client["expenses"]
    sr  = sur / client["income"] if client["income"] else 0.0
    dta = tl / ta if ta else 0.0
    em  = (client["cash"] / client["expenses"]) * 12 if client["expenses"] else 0.0
    return dict(
        total_assets=ta, total_liabilities=tl, net_position=ta - tl,
        surplus=sur, savings_rate=sr, debt_to_assets=dta, emergency_months=em,
    )


def assess_financial_risk(client, results, life_stage="Accumulation (35\u201350)"):
    flags = []
    if results["savings_rate"] < 0.1:
        flags.append("Low savings rate")
    if client["cash"] < client["expenses"] * 0.2:
        flags.append("Low emergency buffer")
    if client["debt"] > results["total_assets"] * 0.7:
        flags.append("High leverage")
    if life_stage == "Pre-retirement (50\u201365)":
        if client["super_balance"] < client["income"] * 5:
            flags.append("Low super for pre-retiree (target: 5\u00d7 income)")
    elif life_stage != "Retirement (65+)":
        if client["super_balance"] < client["income"]:
            flags.append("Low super balance (below 1\u00d7 income)")
    return flags


def run_model(client, life_stage="Accumulation (35\u201350)"):
    r = calculate_financials(client)
    return {"results": r, "risk_summary": assess_financial_risk(client, r, life_stage)}


def project_wealth(client, years=20, growth_rate=0.07, sg_rate=0.115, debt_repayment=20_000):
    sup   = float(client["super_balance"])
    inv   = float(client["investments"])
    cash  = float(client["cash"])
    debt  = float(client["debt"])
    extra = max(0.0, client["income"] - client["expenses"] - debt_repayment)
    rows  = []
    for y in range(years + 1):
        rows.append({"Year": y, "Net Worth": round(sup + inv + cash - debt)})
        if y < years:
            sup  = sup  * (1 + growth_rate) + client["income"] * sg_rate
            inv  = inv  * (1 + growth_rate) + extra
            debt = max(0.0, debt - debt_repayment)
    return pd.DataFrame(rows).set_index("Year")


def project_drawdown(client, years=20, growth_rate=0.07):
    """Retirement drawdown: assets grow but are drawn down to cover expenses net of income."""
    assets      = float(client["super_balance"]) + float(client["investments"]) + float(client["cash"])
    income      = float(client["income"])
    expenses    = float(client["expenses"])
    rows        = []
    depleted_yr = None
    for y in range(years + 1):
        rows.append({"Year": y, "Net Worth": round(max(0.0, assets))})
        if y < years:
            net_draw = max(0.0, expenses - income)
            assets   = assets * (1 + growth_rate) - net_draw
            if assets <= 0 and depleted_yr is None:
                depleted_yr = y + 1
                assets = 0.0
    return pd.DataFrame(rows).set_index("Year"), depleted_yr


def _run_projection(client, years, growth_rate, sg_rate, debt_repayment, is_retirement):
    if is_retirement:
        df, depl = project_drawdown(client, years=years, growth_rate=growth_rate)
        return df, depl
    return project_wealth(client, years=years, growth_rate=growth_rate,
                          sg_rate=sg_rate, debt_repayment=debt_repayment), None


# ── Formatting helpers ────────────────────────────────────────────────────────
def fmt_currency(v):
    if pd.isna(v):
        return ""
    return f"${v:,.0f}" if v >= 0 else f"(${abs(v):,.0f})"


def sign_style(v):
    if not isinstance(v, (int, float)) or pd.isna(v):
        return "color:" + NAVY + ";"
    if v < 0:
        return "background-color:" + BG_NEG + "; color:" + TXT_NEG + ";"
    if v > 0:
        return "background-color:" + BG_POS + "; color:" + TXT_POS + ";"
    return "color:" + NAVY + ";"


def _tbl(styler):
    return '<div style="overflow-x:auto; margin-bottom:1.5rem;">' + styler.to_html() + "</div>"


def _metric_card(label, value, subtext, healthy):
    bg  = BG_POS if healthy else BG_NEG
    bdr = TXT_POS if healthy else TXT_NEG
    vc  = TXT_POS if healthy else TXT_NEG
    return (
        '<div style="background:' + bg + '; border-left:4px solid ' + bdr + '; '
        'border-radius:6px; padding:16px 20px;">'
        '<div style="font-size:10pt; font-weight:600; color:' + NAVY + ';">' + label + '</div>'
        '<div style="font-size:18pt; font-weight:bold; color:' + vc + '; margin-top:6px;">' + value + '</div>'
        '<div style="font-size:8.5pt; color:' + NAVY + '; opacity:0.7; margin-top:4px;">' + subtext + '</div>'
        '</div>'
    )


# ── Chart builders ────────────────────────────────────────────────────────────
def _fig_to_b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


def make_scenario_charts(base_r, s1_r, s2_r, base_client, s1_lbl, s2_lbl):
    names  = ["Base Case", s1_lbl, s2_lbl]
    colors = [NAVY, S1_COLOR, TEAL]
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    ax   = axes[0]
    vals = [base_r["surplus"], s1_r["surplus"], s2_r["surplus"]]
    ymax = max(max(vals) * 1.3, 1)
    bars = ax.bar(names, vals, color=colors, width=0.5, zorder=3)
    ax.set_ylim(0, ymax)
    ax.set_title("Annual Surplus", fontweight="bold", color=NAVY, pad=10)
    ax.set_ylabel("Amount ($)", color=NAVY)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax.tick_params(colors=NAVY)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, v + ymax * 0.02,
                f"${v:,.0f}", ha="center", va="bottom", fontsize=9, fontweight="bold", color=NAVY)

    ax   = axes[1]
    vals = [base_r["net_position"], s1_r["net_position"], s2_r["net_position"]]
    spread = max((abs(v) for v in vals), default=1) or 1
    bars = ax.bar(names, vals, color=colors, width=0.5, zorder=3)
    ax.axhline(0, color="#999", linewidth=0.8, linestyle="--")
    ax.set_title("Net Position", fontweight="bold", color=NAVY, pad=10)
    ax.set_ylabel("Amount ($)", color=NAVY)
    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda x, _: f"${x:,.0f}" if x >= 0 else f"(${abs(x):,.0f})")
    )
    ax.tick_params(colors=NAVY)
    for bar, v in zip(bars, vals):
        lbl = f"${v:,.0f}" if v >= 0 else f"(${abs(v):,.0f})"
        if v >= 0:
            ax.text(bar.get_x() + bar.get_width() / 2, v + spread * 0.02, lbl,
                    ha="center", va="bottom", fontsize=9, fontweight="bold", color=NAVY)
        else:
            ax.text(bar.get_x() + bar.get_width() / 2, v + spread * 0.05, lbl,
                    ha="center", va="bottom", fontsize=9, fontweight="bold", color="white")

    ax    = axes[2]
    sizes = [base_client["super_balance"], base_client["investments"], base_client["cash"]]
    lbls  = ["Superannuation", "Investments", "Cash"]
    if sum(sizes) > 0:
        _, _, autotexts = ax.pie(
            sizes, labels=lbls, colors=colors, autopct="%1.0f%%", startangle=90,
            wedgeprops={"linewidth": 1.5, "edgecolor": "white"},
            textprops={"fontsize": 9},
        )
        for at in autotexts:
            at.set_fontweight("bold")
    else:
        ax.text(0.5, 0.5, "No assets entered", ha="center", va="center",
                transform=ax.transAxes, color=NAVY)
    ax.set_title("Asset Composition\n(Base Case)", fontweight="bold", color=NAVY, pad=10)

    plt.tight_layout()
    return fig, _fig_to_b64(fig)


def make_projection_chart(base_proj, s1_proj, s2_proj, client_name,
                          s1_lbl, s2_lbl, proj_years, extra_projections=None):
    fig, ax = plt.subplots(figsize=(12, 6))

    ax.plot(base_proj.index, base_proj["Net Worth"] / 1e6,
            color=NAVY, linewidth=2.5, label="Base Case", zorder=3)
    ax.plot(s1_proj.index, s1_proj["Net Worth"] / 1e6,
            color=S1_COLOR, linewidth=2.5, linestyle="--", label=s1_lbl, zorder=3)
    ax.plot(s2_proj.index, s2_proj["Net Worth"] / 1e6,
            color=TEAL, linewidth=2.5, linestyle=":", label=s2_lbl, zorder=3)

    _extra_styles = ["-.", (0, (3, 1, 1, 1)), (0, (5, 2, 1, 2)), "-", "--"]
    for i, (proj, lbl, color) in enumerate(extra_projections or []):
        ax.plot(proj.index, proj["Net Worth"] / 1e6,
                color=color, linewidth=2.0,
                linestyle=_extra_styles[i % len(_extra_styles)],
                label=lbl, zorder=3)
        v = proj.loc[proj_years, "Net Worth"]
        ax.annotate(f"  ${v / 1e6:.2f}M", xy=(proj_years, v / 1e6),
                    fontsize=9, fontweight="bold", color=color, va="center")

    ax.axhline(0, color="#ccc", linewidth=1.0)
    ax.fill_between(base_proj.index, 0, base_proj["Net Worth"] / 1e6,
                    where=(base_proj["Net Worth"] > 0), alpha=0.06, color=NAVY)

    for proj, color in [(base_proj, NAVY), (s1_proj, S1_COLOR), (s2_proj, TEAL)]:
        v = proj.loc[proj_years, "Net Worth"]
        ax.annotate(f"  ${v / 1e6:.2f}M", xy=(proj_years, v / 1e6),
                    fontsize=9, fontweight="bold", color=color, va="center")

    ax.set_title(f"Wealth Projection \u2014 {client_name}",
                 fontsize=12, fontweight="bold", color=NAVY, pad=12)
    ax.set_xlabel("Year", color=NAVY)
    ax.set_ylabel("Net Worth ($M)", color=NAVY)
    _tick_step = max(2, (proj_years // 10) * 2)
    ax.set_xticks(range(0, proj_years + 1, _tick_step))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:.1f}M"))
    ax.legend(framealpha=0.9, fontsize=9, loc="upper left")
    ax.tick_params(colors=NAVY)
    plt.tight_layout()
    return fig, _fig_to_b64(fig)


# ── HTML report builder ───────────────────────────────────────────────────────
def _card_html(label, value, subtext, healthy):
    bg  = BG_POS if healthy else BG_NEG
    bdr = TXT_POS if healthy else TXT_NEG
    vc  = TXT_POS if healthy else TXT_NEG
    return (
        '<div style="background:' + bg + '; border-left:4px solid ' + bdr + '; '
        'border-radius:6px; padding:14px 18px;">'
        '<div style="font-size:10pt; font-weight:600; color:' + NAVY + ';">' + label + '</div>'
        '<div style="font-size:17pt; font-weight:bold; color:' + vc + '; margin-top:6px;">' + value + '</div>'
        '<div style="font-size:8.5pt; color:' + NAVY + '; opacity:0.65; margin-top:4px;">' + subtext + '</div>'
        '</div>'
    )


def build_html_report(client_name, today, base_r, base_client, flags,
                      bal_html, comp_html, milestone_html,
                      charts_b64, proj_b64, s1_lbl, s2_lbl):
    sr_str = "{:.1f}%".format(base_r["savings_rate"] * 100)
    em_str = "{:.1f} months".format(base_r["emergency_months"])
    em_ok  = base_client["cash"] >= base_client["expenses"] * 0.2
    card1 = _card_html("Net Position",    fmt_currency(base_r["net_position"]),
                       "Total assets minus liabilities", base_r["net_position"] >= 0)
    card2 = _card_html("Annual Surplus",  fmt_currency(base_r["surplus"]),
                       "Income minus expenses", base_r["surplus"] > 0)
    card3 = _card_html("Savings Rate",    sr_str, "Target: >= 10%", base_r["savings_rate"] >= 0.1)
    card4 = _card_html("Emergency Buffer", em_str, "Threshold: 2.4 months", em_ok)
    badges = "".join(
        '<span style="background:' + BG_NEG + '; color:' + TXT_NEG + '; border:1px solid ' + TXT_NEG + '; '
        'border-radius:12px; padding:3px 12px; font-size:9pt; font-weight:600; '
        'margin-right:6px; display:inline-block;">&#9888; ' + flag + '</span>'
        for flag in flags
    )
    flag_section = (
        '<h2 style="color:' + NAVY + ';">Risk Flags</h2>' + badges
        if flags else
        '<p style="color:' + TXT_POS + '; font-weight:600;">&#10003; No risk flags identified.</p>'
    )
    return (
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
        "  <meta charset=\"UTF-8\">\n"
        "  <title>Financial Report \u2014 " + client_name + "</title>\n"
        "  <style>\n"
        "    body { font-family: Arial, sans-serif; color: " + NAVY + "; "
        "max-width: 1100px; margin: 40px auto; padding: 0 24px; line-height: 1.5; }\n"
        "    h1 { color: " + NAVY + "; border-bottom: 2px solid " + NAVY + "; "
        "padding-bottom: 8px; margin-bottom: 4px; }\n"
        "    h2 { color: " + NAVY + "; margin-top: 2rem; font-size: 13pt; }\n"
        "    .meta { color: " + NAVY + "; opacity: 0.7; font-size: 11pt; margin: 0; }\n"
        "    .metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); "
        "gap: 16px; margin: 1rem 0; }\n"
        "    .footnote { font-size: 9pt; color: " + NAVY + "; opacity: 0.65; "
        "margin-top: 2.5rem; border-top: 1px solid #D0D0D0; padding-top: 1rem; }\n"
        "  </style>\n</head>\n<body>\n"
        "  <h1>Financial Scenario Analysis</h1>\n"
        "  <p class=\"meta\">" + client_name + " &nbsp;&middot;&nbsp; " + today + "</p>\n"
        "  <h2>Key Metrics \u2014 Base Case</h2>\n"
        "  <div class=\"metric-grid\">\n"
        "    " + card1 + "\n    " + card2 + "\n    " + card3 + "\n    " + card4 + "\n"
        "  </div>\n"
        "  " + flag_section + "\n"
        "  <h2>Statement of Financial Position</h2>\n  " + bal_html + "\n"
        "  <h2>Scenario Comparison</h2>\n  " + comp_html + "\n"
        "  <h2>Scenario Analysis Charts</h2>\n"
        "  <img src=\"data:image/png;base64," + charts_b64 + "\" style=\"max-width:100%;\" alt=\"Charts\"/>\n"
        "  <h2>Wealth Projection</h2>\n"
        "  <img src=\"data:image/png;base64," + proj_b64 + "\" style=\"max-width:100%;\" alt=\"Projection\"/>\n"
        "  <h2>Projected Net Worth \u2014 Milestones</h2>\n  " + milestone_html + "\n"
        "  <div class=\"footnote\">\n"
        "    <strong>Model Assumptions:</strong> "
        "Investment and superannuation growth: 7.0% p.a. | "
        "Superannuation guarantee: 11.5% of income p.a. | "
        "Annual debt repayment: $20,000 | "
        "Surplus above repayment reinvested into portfolio | "
        "Income and expenses held constant in real terms. "
        "Projections are illustrative only and do not constitute financial advice.\n"
        "  </div>\n</body>\n</html>"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
extra_scenario_changes = {}

with st.sidebar:
    st.markdown("## \u2699\ufe0f Client Inputs")

    # ── Life stage selector ───────────────────────────────────────────────────
    st.markdown("**Life Stage**")
    st.selectbox(
        "Select life stage",
        options=LIFE_STAGES,
        key="life_stage",
        on_change=_on_life_stage_change,
        label_visibility="collapsed",
    )
    st.caption(LIFE_STAGE_CONFIG[st.session_state["life_stage"]]["description"])

    st.divider()

    # ── Preset profiles ───────────────────────────────────────────────────────
    st.markdown("**Quick Profiles**")
    _pcols = st.columns(2)
    for _pi, _pn in enumerate(PRESETS):
        if _pcols[_pi % 2].button(_pn, use_container_width=True, key="btn_" + _pn):
            _apply_preset(_pn)
            st.rerun()

    st.divider()

    client_name = st.text_input("Client Name", key="client_name")

    st.markdown("**Income & Expenses**")
    income   = st.number_input("Annual Income ($)",   min_value=0, step=1000, key="income")
    expenses = st.number_input("Annual Expenses ($)", min_value=0, step=1000, key="expenses")

    st.markdown("**Assets**")
    super_balance = st.number_input("Superannuation ($)", min_value=0, step=1000, key="super_balance")
    investments   = st.number_input("Investments ($)",    min_value=0, step=1000, key="investments")
    cash          = st.number_input("Cash & Savings ($)", min_value=0, step=1000, key="cash")

    st.markdown("**Liabilities**")
    debt = st.number_input("Mortgage / Debt ($)", min_value=0, step=1000, key="debt")

    # ── Model Parameters ──────────────────────────────────────────────────────
    with st.expander("Model Parameters"):
        st.slider(
            "Growth rate (%)",
            min_value=1.0, max_value=15.0, step=0.5,
            key="growth_rate_param",
            help=(
                "Annual return assumed for investments and superannuation. "
                "The long-run historical average for a balanced portfolio is around 7%. "
                "Higher values produce more optimistic projections."
            ),
        )
        st.slider(
            "Super guarantee rate (%)",
            min_value=5.0, max_value=15.0, step=0.5,
            key="sg_rate_param",
            help=(
                "The Superannuation Guarantee is the percentage of income your employer "
                "must contribute to super each year by law. "
                "The legislated rate is 11.5% in 2024\u201325, rising to 12% in July 2025."
            ),
        )
        st.slider(
            "Annual debt repayment ($)",
            min_value=0, max_value=100_000, step=1_000,
            key="debt_repayment_param",
            help=(
                "The estimated annual reduction in your mortgage or debt principal. "
                "This is separate from interest \u2014 it is the portion that reduces what you owe."
            ),
        )
        st.slider(
            "Projection years",
            min_value=5, max_value=40, step=5,
            key="proj_years",
            help=(
                "How many years to project forward. "
                "The life stage selector sets a sensible default \u2014 "
                "you can override it here."
            ),
        )
        st.toggle(
            "Inflation-adjusted returns",
            key="inflation_adj",
            help=(
                "When on, reduces the growth rate by 2.5% p.a. to show wealth in "
                "today\u2019s purchasing power (real terms). "
                "When off, projections are in nominal (face-value) dollars."
            ),
        )

    st.divider()

    # ── Scenario 1 ───────────────────────────────────────────────────────────
    st.markdown("**Scenario 1**")
    s1_name  = st.text_input("Label", key="s1_name")
    s1_strat = st.selectbox("Strategy",
                            ["Income Improvement", "Debt Reduction", "Super Boost", "Custom"],
                            key="s1_strategy")
    if s1_strat == "Income Improvement":
        _a = st.number_input("Income ($)",   min_value=0, step=1000, key="s1_income")
        _b = st.number_input("Expenses ($)", min_value=0, step=1000, key="s1_expenses")
        s1_changes = {"income": _a, "expenses": _b}
    elif s1_strat == "Debt Reduction":
        _a = st.number_input("Debt ($)", min_value=0, step=1000, key="s1_debt")
        _b = st.number_input("Cash ($)", min_value=0, step=1000, key="s1_cash")
        s1_changes = {"debt": _a, "cash": _b}
    elif s1_strat == "Super Boost":
        _a = st.number_input("Superannuation ($)", min_value=0, step=1000, key="s1_super")
        s1_changes = {"super_balance": _a}
    else:
        _a = st.number_input("Income ($)",        min_value=0, step=1000, key="s1_income")
        _b = st.number_input("Expenses ($)",       min_value=0, step=1000, key="s1_expenses")
        _c = st.number_input("Debt ($)",           min_value=0, step=1000, key="s1_debt")
        _d = st.number_input("Cash ($)",           min_value=0, step=1000, key="s1_cash")
        _e = st.number_input("Superannuation ($)", min_value=0, step=1000, key="s1_super")
        _f = st.number_input("Investments ($)",    min_value=0, step=1000, key="s1_inv")
        s1_changes = {"income": _a, "expenses": _b, "debt": _c,
                      "cash": _d, "super_balance": _e, "investments": _f}

    st.divider()

    # ── Scenario 2 ───────────────────────────────────────────────────────────
    st.markdown("**Scenario 2**")
    s2_name  = st.text_input("Label", key="s2_name")
    s2_strat = st.selectbox("Strategy",
                            ["Income Improvement", "Debt Reduction", "Super Boost", "Custom"],
                            key="s2_strategy")
    if s2_strat == "Income Improvement":
        _a = st.number_input("Income ($)",   min_value=0, step=1000, key="s2_income")
        _b = st.number_input("Expenses ($)", min_value=0, step=1000, key="s2_expenses")
        s2_changes = {"income": _a, "expenses": _b}
    elif s2_strat == "Debt Reduction":
        _a = st.number_input("Debt ($)", min_value=0, step=1000, key="s2_debt")
        _b = st.number_input("Cash ($)", min_value=0, step=1000, key="s2_cash")
        s2_changes = {"debt": _a, "cash": _b}
    elif s2_strat == "Super Boost":
        _a = st.number_input("Superannuation ($)", min_value=0, step=1000, key="s2_super")
        s2_changes = {"super_balance": _a}
    else:
        _a = st.number_input("Income ($)",        min_value=0, step=1000, key="s2_income")
        _b = st.number_input("Expenses ($)",       min_value=0, step=1000, key="s2_expenses")
        _c = st.number_input("Debt ($)",           min_value=0, step=1000, key="s2_debt")
        _d = st.number_input("Cash ($)",           min_value=0, step=1000, key="s2_cash")
        _e = st.number_input("Superannuation ($)", min_value=0, step=1000, key="s2_super")
        _f = st.number_input("Investments ($)",    min_value=0, step=1000, key="s2_inv")
        s2_changes = {"income": _a, "expenses": _b, "debt": _c,
                      "cash": _d, "super_balance": _e, "investments": _f}

    st.divider()

    # ── Dynamic extra scenarios ───────────────────────────────────────────────
    for _sc in list(st.session_state["extra_scenarios"]):
        _id = _sc["id"]
        _sc_defaults = {
            "ex_{}_name".format(_id):     "Scenario {}".format(_id),
            "ex_{}_strategy".format(_id): "Income Improvement",
            "ex_{}_income".format(_id):   income,
            "ex_{}_expenses".format(_id): expenses,
            "ex_{}_debt".format(_id):     debt,
            "ex_{}_cash".format(_id):     cash,
            "ex_{}_super".format(_id):    super_balance,
            "ex_{}_inv".format(_id):      investments,
        }
        for _dk, _dv in _sc_defaults.items():
            if _dk not in st.session_state:
                st.session_state[_dk] = _dv

        _ex_cols = st.columns([4, 1])
        _ex_cols[0].markdown("**Scenario {}**".format(_id))
        if _ex_cols[1].button("\u2715", key="remove_{}".format(_id)):
            st.session_state["extra_scenarios"] = [
                s for s in st.session_state["extra_scenarios"] if s["id"] != _id
            ]
            for _sfx in ["name", "strategy", "income", "expenses", "debt", "cash", "super", "inv"]:
                _k = "ex_{}_{}".format(_id, _sfx)
                if _k in st.session_state:
                    del st.session_state[_k]
            st.rerun()

        _ex_name  = st.text_input("Label", key="ex_{}_name".format(_id))
        _ex_strat = st.selectbox(
            "Strategy",
            ["Income Improvement", "Debt Reduction", "Super Boost", "Custom"],
            key="ex_{}_strategy".format(_id),
        )
        if _ex_strat == "Income Improvement":
            _a = st.number_input("Income ($)",   min_value=0, step=1000, key="ex_{}_income".format(_id))
            _b = st.number_input("Expenses ($)", min_value=0, step=1000, key="ex_{}_expenses".format(_id))
            extra_scenario_changes[_id] = {"income": _a, "expenses": _b}
        elif _ex_strat == "Debt Reduction":
            _a = st.number_input("Debt ($)", min_value=0, step=1000, key="ex_{}_debt".format(_id))
            _b = st.number_input("Cash ($)", min_value=0, step=1000, key="ex_{}_cash".format(_id))
            extra_scenario_changes[_id] = {"debt": _a, "cash": _b}
        elif _ex_strat == "Super Boost":
            _a = st.number_input("Superannuation ($)", min_value=0, step=1000, key="ex_{}_super".format(_id))
            extra_scenario_changes[_id] = {"super_balance": _a}
        else:
            _a = st.number_input("Income ($)",        min_value=0, step=1000, key="ex_{}_income".format(_id))
            _b = st.number_input("Expenses ($)",       min_value=0, step=1000, key="ex_{}_expenses".format(_id))
            _c = st.number_input("Debt ($)",           min_value=0, step=1000, key="ex_{}_debt".format(_id))
            _d = st.number_input("Cash ($)",           min_value=0, step=1000, key="ex_{}_cash".format(_id))
            _e = st.number_input("Superannuation ($)", min_value=0, step=1000, key="ex_{}_super".format(_id))
            _f = st.number_input("Investments ($)",    min_value=0, step=1000, key="ex_{}_inv".format(_id))
            extra_scenario_changes[_id] = {
                "income": _a, "expenses": _b, "debt": _c,
                "cash": _d, "super_balance": _e, "investments": _f,
            }
        st.divider()

    if st.button("+ Add Scenario", use_container_width=True):
        _new_id = st.session_state["scenario_id_counter"]
        st.session_state["scenario_id_counter"] += 1
        st.session_state["extra_scenarios"].append({"id": _new_id})
        st.session_state["ex_{}_name".format(_new_id)]     = "Scenario {}".format(_new_id)
        st.session_state["ex_{}_strategy".format(_new_id)] = "Income Improvement"
        st.session_state["ex_{}_income".format(_new_id)]   = income
        st.session_state["ex_{}_expenses".format(_new_id)] = expenses
        st.session_state["ex_{}_debt".format(_new_id)]     = debt
        st.session_state["ex_{}_cash".format(_new_id)]     = cash
        st.session_state["ex_{}_super".format(_new_id)]    = super_balance
        st.session_state["ex_{}_inv".format(_new_id)]      = investments
        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# BUILD CLIENTS & RUN MODEL
# ═══════════════════════════════════════════════════════════════════════════════
life_stage    = st.session_state["life_stage"]
is_retirement = (life_stage == "Retirement (65+)")

_eff_growth = (st.session_state["growth_rate_param"] / 100.0) - (
    0.025 if st.session_state["inflation_adj"] else 0.0
)
_eff_sg     = st.session_state["sg_rate_param"] / 100.0
_eff_repay  = st.session_state["debt_repayment_param"]
_proj_years = st.session_state["proj_years"]

base_client = dict(
    name=client_name, income=income, expenses=expenses,
    super_balance=super_balance, investments=investments,
    cash=cash, debt=debt,
)

s1_lbl = (s1_name or "Scenario 1").strip() or "Scenario 1"
s2_lbl = (s2_name or "Scenario 2").strip() or "Scenario 2"
if s1_lbl == s2_lbl:
    s2_lbl += " (2)"

scenario_1 = {**base_client, **s1_changes}
scenario_2 = {**base_client, **s2_changes}

base_out = run_model(base_client, life_stage)
s1_out   = run_model(scenario_1,  life_stage)
s2_out   = run_model(scenario_2,  life_stage)

base_r = base_out["results"]
s1_r   = s1_out["results"]
s2_r   = s2_out["results"]
flags  = base_out["risk_summary"]

base_proj, base_depl = _run_projection(base_client, _proj_years, _eff_growth, _eff_sg, _eff_repay, is_retirement)
s1_proj,   s1_depl   = _run_projection(scenario_1,  _proj_years, _eff_growth, _eff_sg, _eff_repay, is_retirement)
s2_proj,   s2_depl   = _run_projection(scenario_2,  _proj_years, _eff_growth, _eff_sg, _eff_repay, is_retirement)

depletion_warnings = []
for _dlbl, _dyr in [("Base Case", base_depl), (s1_lbl, s1_depl), (s2_lbl, s2_depl)]:
    if _dyr:
        depletion_warnings.append("{}: assets depleted at year {}".format(_dlbl, _dyr))

extra_scenarios_computed = []
_used_labels = {"Base Case", s1_lbl, s2_lbl}
for _i, _sc in enumerate(st.session_state["extra_scenarios"]):
    _id = _sc["id"]
    if _id not in extra_scenario_changes:
        continue
    _raw_lbl = (st.session_state.get("ex_{}_name".format(_id)) or "Scenario {}".format(_id)).strip()
    _lbl  = _raw_lbl or "Scenario {}".format(_id)
    _dedup  = _lbl
    _suffix = 2
    while _dedup in _used_labels:
        _dedup  = "{} ({})".format(_lbl, _suffix)
        _suffix += 1
    _used_labels.add(_dedup)

    _sc_client = {**base_client, **extra_scenario_changes[_id]}
    _sc_out    = run_model(_sc_client, life_stage)
    _sc_proj, _sc_depl = _run_projection(_sc_client, _proj_years, _eff_growth, _eff_sg, _eff_repay, is_retirement)
    if _sc_depl:
        depletion_warnings.append("{}: assets depleted at year {}".format(_dedup, _sc_depl))
    _color = EXTRA_COLORS[_i % len(EXTRA_COLORS)]

    extra_scenarios_computed.append({
        "id": _id, "label": _dedup,
        "client": _sc_client,
        "results": _sc_out["results"],
        "risk_summary": _sc_out["risk_summary"],
        "proj": _sc_proj,
        "color": _color,
    })

today = datetime.date.today().strftime("%d %B %Y")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT — TABS
# ═══════════════════════════════════════════════════════════════════════════════
tab_about, tab_analysis = st.tabs(["About & Assumptions", "Analysis"])


# ── TAB 1: About & Assumptions ────────────────────────────────────────────────
with tab_about:
    st.markdown(
        '<h2 style="color:' + NAVY + '; margin-bottom:4px;">About This App</h2>'
        '<p style="color:' + NAVY + '; opacity:0.65; font-size:11pt;">'
        'A guide for financial planners and their clients.</p>',
        unsafe_allow_html=True,
    )

    with st.expander("How to use this app", expanded=True):
        st.markdown("""
**Getting started**

This app helps you compare a client's current financial position against alternative
strategies, so you can have a clear, visual conversation about the impact of
different decisions.

---

**Step 1 \u2014 Choose a life stage**

Select a life stage at the top of the sidebar. This automatically loads sensible
starting values for that stage of life. Available stages:

- **Early Accumulation (25\u201335)** \u2014 building foundations, 35-year horizon
- **Accumulation (35\u201350)** \u2014 peak earning years, 20-year horizon
- **Pre-retirement (50\u201365)** \u2014 consolidation phase, 15-year horizon
- **Retirement (65+)** \u2014 drawdown phase, assets modelled as declining over time
- **Custom** \u2014 enter all values manually, no defaults applied

---

**Step 2 \u2014 Enter the client's details**

Use the sidebar to enter the client's financial information:

- **Annual Income** \u2014 total combined gross income before tax
- **Annual Expenses** \u2014 total yearly living costs (housing, food, transport, etc.)
- **Superannuation** \u2014 combined super balance
- **Investments** \u2014 non-super portfolio (shares, managed funds, property trusts)
- **Cash & Savings** \u2014 money in bank accounts or offset accounts
- **Mortgage / Debt** \u2014 total outstanding debt balance, not monthly repayments

All amounts should be entered as whole numbers with no commas or symbols.

---

**Step 3 \u2014 Adjust model parameters (optional)**

Open the **Model Parameters** section in the sidebar to override the default assumptions:

- **Growth rate** \u2014 annual investment return (default 7%)
- **Super guarantee rate** \u2014 employer super contribution (default 11.5%)
- **Annual debt repayment** \u2014 how much principal is repaid each year (default $20,000)
- **Projection years** \u2014 how far forward to project (set by life stage, overrideable)
- **Inflation-adjusted returns** \u2014 toggle on to show results in today\u2019s dollars

---

**Step 4 \u2014 Build scenarios**

Scenarios let you model \u201cwhat if\u201d changes. For example: what happens if the client
increases their income, reduces their debt, or boosts their super?

- Use the **Scenario 1** and **Scenario 2** sections in the sidebar
- Give each scenario a label (e.g. "Salary Increase")
- Choose a strategy from the dropdown \u2014 only the relevant fields will appear
- Click **+ Add Scenario** to compare more than two strategies
- Click the **\u2715** button next to any extra scenario to remove it

---

**Step 5 \u2014 Read the results**

Switch to the **Analysis** tab to see the full output:

- **Metric cards** \u2014 quick snapshot of net position, surplus, savings rate, and emergency buffer
- **Risk flags** \u2014 automatic warnings when any indicator falls below a safe threshold
- **Balance sheet** \u2014 full statement of assets and liabilities for the base case
- **Scenario comparison table** \u2014 side-by-side figures for all five key metrics
- **Charts** \u2014 bar charts for surplus and net position, pie chart of asset composition
- **Projection chart** \u2014 how net worth grows (or is drawn down in retirement) over time
- **Milestone table** \u2014 net worth at 5-year intervals across all scenarios

**Reading the colour coding**

A cell or card with a **green background** means the value is positive or above the
safe threshold. A cell or card with a **red background** means the value is negative
or below the threshold and needs attention. Chart lines use navy, purple, and teal only
\u2014 never red or green.

---

**Step 6 \u2014 Download the report**

Click **Download HTML Report** at the bottom of the Analysis tab to save a
standalone file with all tables and charts. Open it in any browser and print to PDF.
""")

    with st.expander("Model assumptions"):
        st.markdown("""
**7% annual growth rate**

The model assumes investments and superannuation grow at 7% per year, before fees and taxes.
This is broadly consistent with the long-run historical average for a balanced or growth
portfolio across Australian and global shares and property.

It is not guaranteed. In any given year returns could be significantly higher or lower.
You can adjust the growth rate using the **Model Parameters** slider in the sidebar.

---

**11.5% Superannuation Guarantee (SG)**

The Superannuation Guarantee is the percentage of an employee\u2019s income that their
employer must contribute to super each year, as set by law.

The current legislated rate is **11.5%** for the 2024\u201325 financial year. It is scheduled
to rise to **12%** on 1 July 2025. This model uses 11.5% as the default and does not
automatically apply the July 2025 increase. Use the **SG rate** slider in Model Parameters
to set 12% when modelling from July 2025 onwards.

---

**$20,000 annual principal repayment**

The model assumes $20,000 of debt principal is repaid each year. This is the portion of
mortgage repayments that reduces the loan balance, as opposed to interest payments which
are already included in annual expenses. You can adjust this amount in Model Parameters.

---

**Income and expenses held flat in real terms**

The model does not project income growth or expense increases over time. Both are held
constant at the values entered for the full projection period.

This is a simplifying assumption. In practice, incomes typically grow with inflation and
career progression. Turning on the **Inflation-adjusted returns** toggle partially addresses
this by expressing wealth in today\u2019s purchasing power rather than future dollar values.

---

**Emergency buffer threshold: 20% of annual expenses**

A risk flag is triggered when the client\u2019s cash balance is below 20% of their annual
expenses \u2014 equivalent to approximately 2.4 months of living costs. This is the minimum
considered prudent to cover unexpected expenses or a short period of income disruption.

---

**Savings rate threshold: 10% of income**

A savings rate below 10% of gross income is flagged as a risk. Savings rate is calculated
as annual surplus (income minus expenses) divided by income. Below 10% indicates limited
capacity to build wealth or absorb financial shocks.

---

**Leverage threshold: debt above 70% of total assets**

If total debt exceeds 70% of total assets, the model flags high leverage. This indicates
the asset base is predominantly funded by borrowing, which increases vulnerability if
asset values fall or income is disrupted.

---

**Super balance thresholds**

For clients in the accumulation phase, a super balance below **1\u00d7 annual income** is flagged.
For pre-retirement clients (50\u201365), the threshold rises to **5\u00d7 annual income** to reflect
the shorter time remaining to build an adequate retirement balance.

For retirement clients, the model switches to a drawdown projection and will flag if
projected assets are fully depleted before the end of the projection period.

---

**Retirement drawdown model**

When the **Retirement (65+)** life stage is selected, the projection switches from an
accumulation model to a drawdown model. Each year, the remaining assets grow at the
selected growth rate, then the net annual shortfall (expenses minus income) is withdrawn.
If assets reach zero, a depletion warning is shown indicating the year funds run out.
""")

    with st.expander("Known limitations"):
        st.markdown("""
The following factors are **not modelled** in the current version.
Be aware of these when interpreting results with clients.

---

**Concessional contributions cap not applied**

The model adds employer SG contributions to super each year without checking whether the
annual concessional contributions cap ($30,000 per year as of 2024\u201325) has been reached.
If a client is close to or above the cap, the projected super balance may be overstated.

---

**15% contributions tax not deducted**

Super contributions are taxed at 15% when they enter the fund (or 30% for high earners
under Division 293). This model does not deduct contributions tax, so projected super
balances will be slightly higher than actual after-tax figures.

---

**Fund fees not modelled**

Investment and administration fees charged by super funds and managed funds are not
deducted. These typically range from 0.1% to 1.5% per year. To approximate the effect,
reduce the growth rate slider by the estimated fee level.

---

**SG rate increase not applied automatically**

The Super Guarantee is legislated to rise from 11.5% to 12% on 1 July 2025. This model
does not apply that change automatically. Set the SG rate slider to 12% in Model
Parameters when modelling from July 2025 onwards.

---

**Income growth not modelled**

The model holds income constant at the entered value for the full projection period.
Real-world income typically grows over a career. This means projections may understate
long-run wealth for younger clients with significant future earnings growth.
""")


# ── TAB 2: Analysis ───────────────────────────────────────────────────────────
with tab_analysis:

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(
        '<h1 style="color:' + NAVY + '; margin-bottom:2px;">Financial Scenario Analysis</h1>'
        '<p style="color:' + NAVY + '; opacity:0.65; margin-top:0; font-size:11pt;">'
        + base_client["name"] + " &nbsp;&middot;&nbsp; " + today
        + " &nbsp;&middot;&nbsp; " + life_stage + "</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    # ── Metric cards ──────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4, gap="small")
    c1.markdown(_metric_card(
        "Net Position", fmt_currency(base_r["net_position"]),
        "Total assets minus liabilities", base_r["net_position"] >= 0,
    ), unsafe_allow_html=True)
    c2.markdown(_metric_card(
        "Annual Surplus", fmt_currency(base_r["surplus"]),
        "Income minus expenses", base_r["surplus"] > 0,
    ), unsafe_allow_html=True)
    c3.markdown(_metric_card(
        "Savings Rate", "{:.1f}%".format(base_r["savings_rate"] * 100),
        "Target >= 10%", base_r["savings_rate"] >= 0.1,
    ), unsafe_allow_html=True)
    c4.markdown(_metric_card(
        "Emergency Buffer", "{:.1f} months".format(base_r["emergency_months"]),
        "Threshold: 2.4 months of expenses", cash >= expenses * 0.2,
    ), unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Risk badges ───────────────────────────────────────────────────────────
    _all_flags = list(flags)
    if depletion_warnings:
        _all_flags += depletion_warnings

    if _all_flags:
        _badge_html = "".join(
            '<span style="background:' + BG_NEG + '; color:' + TXT_NEG + '; '
            'border:1px solid ' + TXT_NEG + '; border-radius:12px; '
            'padding:4px 14px; font-size:9pt; font-weight:600; '
            'margin-right:8px; display:inline-block; margin-bottom:4px;">&#9888; ' + f + '</span>'
            for f in _all_flags
        )
        st.markdown(
            '<div style="font-weight:600; color:' + NAVY + '; margin-bottom:6px;">'
            'Risk Flags \u2014 Base Case</div>' + _badge_html,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span style="color:' + TXT_POS + '; font-weight:600; font-size:10pt;">'
            '\u2713 No risk flags identified.</span>',
            unsafe_allow_html=True,
        )
    st.divider()

    # ── Table 1 — Balance Sheet ───────────────────────────────────────────────
    st.markdown('<h3 style="color:' + NAVY + '; margin-bottom:8px;">Statement of Financial Position</h3>',
                unsafe_allow_html=True)

    _bal_rows = [
        ("Superannuation",    super_balance,                    super_balance),
        ("Investments",       investments,                      investments),
        ("Cash & Savings",    cash,                             cash),
        ("TOTAL ASSETS",      base_r["total_assets"],           base_r["total_assets"]),
        ("_div1",             None,                             None),
        ("Mortgage / Debt",   debt,                            -debt),
        ("TOTAL LIABILITIES", base_r["total_liabilities"],     -base_r["total_liabilities"]),
        ("_div2",             None,                             None),
        ("NET POSITION",      base_r["net_position"],           base_r["net_position"]),
    ]
    _bal_items = [r[0] for r in _bal_rows]
    bal_disp = pd.DataFrame({"Amount": [fmt_currency(r[1]) for r in _bal_rows]}, index=_bal_items)
    bal_num  = pd.DataFrame({"Amount": [r[2]              for r in _bal_rows]},  index=_bal_items)
    bal_disp.index.name = "Item"
    bal_disp = bal_disp.rename(index={"_div1": " ", "_div2": "  "})
    bal_num  = bal_num.rename( index={"_div1": " ", "_div2": "  "})

    def _style_balance(styler):
        styler.set_caption("Statement of Financial Position \u2014 Base Case")
        styler.set_table_styles(WORD_STYLES)
        def cell_colour(col):
            return [sign_style(v) for v in bal_num[col.name]]
        styler.apply(cell_colour, axis=0)
        def row_fmt(row):
            n = row.name
            if n in (" ", "  "):
                return ["border:none; padding:3px 0; background:white; color:" + NAVY + ";"] * len(row)
            if n == "NET POSITION":
                return ["font-weight:bold; font-size:12pt; "
                        "border-top:2px solid " + NAVY + "; border-bottom:2px solid " + NAVY + ";"] * len(row)
            if n in TOTAL_ROWS:
                return ["font-weight:bold; border-top:2px solid " + NAVY + "; "
                        "border-bottom:2px solid " + NAVY + ";"] * len(row)
            return [""] * len(row)
        styler.apply(row_fmt, axis=1)
        return styler

    st.markdown(_tbl(bal_disp.style.pipe(_style_balance)), unsafe_allow_html=True)

    # ── Table 2 — Scenario Comparison ────────────────────────────────────────
    st.markdown('<h3 style="color:' + NAVY + '; margin-bottom:8px;">Scenario Comparison</h3>',
                unsafe_allow_html=True)

    CURRENCY_ROWS = ["Net Position ($)", "Annual Surplus ($)"]
    PCT_ROWS      = ["Savings Rate (%)", "Debt-to-Assets (%)"]
    MONTH_ROWS    = ["Emergency Buffer (months)"]
    ALL_ROWS      = CURRENCY_ROWS + PCT_ROWS + MONTH_ROWS

    def _fmt_cell(v, metric):
        if pd.isna(v): return ""
        if metric in CURRENCY_ROWS: return fmt_currency(v)
        if metric in PCT_ROWS:      return "{:.1f}%".format(v)
        return "{:.1f} months".format(v)

    def _sc_row(r):
        return [
            r["net_position"], r["surplus"],
            r["savings_rate"] * 100, r["debt_to_assets"] * 100,
            r["emergency_months"],
        ]

    _comp_data = {"Base Case": _sc_row(base_r), s1_lbl: _sc_row(s1_r), s2_lbl: _sc_row(s2_r)}
    for _ex in extra_scenarios_computed:
        _comp_data[_ex["label"]] = _sc_row(_ex["results"])

    comp_num = pd.DataFrame(_comp_data, index=ALL_ROWS)
    comp_num.index.name = "Metric"

    comp_fmt = comp_num.copy().astype(object)
    for _m in comp_num.index:
        for _col in comp_num.columns:
            comp_fmt.loc[_m, _col] = _fmt_cell(comp_num.loc[_m, _col], _m)

    def _style_comparison(styler):
        styler.set_caption("Financial Scenario Comparison")
        styler.set_table_styles(WORD_STYLES)
        def cell_colour(col):
            return [sign_style(v) for v in comp_num[col.name]]
        styler.apply(cell_colour, axis=0)
        return styler

    st.markdown(_tbl(comp_fmt.style.pipe(_style_comparison)), unsafe_allow_html=True)

    _all_scenario_flags = [(s1_lbl, s1_out), (s2_lbl, s2_out)]
    for _ex in extra_scenarios_computed:
        _all_scenario_flags.append((_ex["label"], {"risk_summary": _ex["risk_summary"]}))
    for _lbl, _out in _all_scenario_flags:
        _fl = _out["risk_summary"]
        if _fl:
            st.markdown(
                '<span style="font-size:9pt; color:' + NAVY + ';">&#9888; <strong>'
                + _lbl + '</strong>: ' + ", ".join(_fl) + '</span>',
                unsafe_allow_html=True,
            )

    st.divider()

    # ── Charts ────────────────────────────────────────────────────────────────
    st.markdown('<h3 style="color:' + NAVY + '; margin-bottom:8px;">Scenario Analysis Charts</h3>',
                unsafe_allow_html=True)
    charts_fig, charts_b64 = make_scenario_charts(base_r, s1_r, s2_r, base_client, s1_lbl, s2_lbl)
    st.pyplot(charts_fig)
    plt.close(charts_fig)

    # ── Projection chart ──────────────────────────────────────────────────────
    _drawdown_note = " (Drawdown Mode)" if is_retirement else ""
    st.markdown(
        '<h3 style="color:' + NAVY + '; margin-bottom:8px;">'
        + str(_proj_years) + "-Year Wealth Projection" + _drawdown_note + "</h3>",
        unsafe_allow_html=True,
    )
    if st.session_state["inflation_adj"]:
        st.caption("Returns shown in real terms (inflation-adjusted at \u22122.5% p.a.)")

    _extra_proj_args = [(e["proj"], e["label"], e["color"]) for e in extra_scenarios_computed]
    proj_fig, proj_b64 = make_projection_chart(
        base_proj, s1_proj, s2_proj, base_client["name"],
        s1_lbl, s2_lbl, _proj_years, _extra_proj_args,
    )
    st.pyplot(proj_fig)
    plt.close(proj_fig)

    if depletion_warnings:
        for _w in depletion_warnings:
            st.markdown(
                '<span style="background:' + BG_NEG + '; color:' + TXT_NEG + '; '
                'border:1px solid ' + TXT_NEG + '; border-radius:6px; '
                'padding:6px 14px; font-size:9pt; font-weight:600; '
                'display:inline-block; margin-top:4px;">'
                '&#9888; ' + _w + '</span>',
                unsafe_allow_html=True,
            )

    # ── Table 3 — Milestones ──────────────────────────────────────────────────
    st.markdown(
        '<h3 style="color:' + NAVY + '; margin-bottom:8px;">'
        'Projected Net Worth \u2014 Milestones</h3>',
        unsafe_allow_html=True,
    )

    _milestones = list(range(0, _proj_years + 1, 5))
    if _milestones[-1] != _proj_years:
        _milestones.append(_proj_years)

    _proj_data = {
        "Base Case ($)": [base_proj.loc[y, "Net Worth"] for y in _milestones],
        s1_lbl + " ($)": [s1_proj.loc[y,   "Net Worth"] for y in _milestones],
        s2_lbl + " ($)": [s2_proj.loc[y,   "Net Worth"] for y in _milestones],
    }
    for _ex in extra_scenarios_computed:
        _proj_data[_ex["label"] + " ($)"] = [_ex["proj"].loc[y, "Net Worth"] for y in _milestones]

    proj_num = pd.DataFrame(_proj_data, index=["Year {}".format(y) for y in _milestones])
    proj_num.index.name = "Year"

    def _style_milestones(styler):
        styler.set_caption("Projected Net Worth \u2014 Milestones")
        styler.set_table_styles(WORD_STYLES)
        styler.format(fmt_currency)
        styler.map(sign_style)
        return styler

    st.markdown(_tbl(proj_num.style.pipe(_style_milestones)), unsafe_allow_html=True)
    st.divider()

    # ── Download report ───────────────────────────────────────────────────────
    html_report = build_html_report(
        client_name=base_client["name"],
        today=today,
        base_r=base_r,
        base_client=base_client,
        flags=flags,
        bal_html=bal_disp.style.pipe(_style_balance).to_html(),
        comp_html=comp_fmt.style.pipe(_style_comparison).to_html(),
        milestone_html=proj_num.style.pipe(_style_milestones).to_html(),
        charts_b64=charts_b64,
        proj_b64=proj_b64,
        s1_lbl=s1_lbl,
        s2_lbl=s2_lbl,
    )
    _safe_name = base_client["name"].replace(" ", "_").replace("&", "and")
    st.download_button(
        label="\u2b07  Download HTML Report",
        data=html_report.encode("utf-8"),
        file_name="financial_report_{}.html".format(_safe_name),
        mime="text/html",
    )

    # ── Footnote ──────────────────────────────────────────────────────────────
    _infl_note = " Returns shown inflation-adjusted (\u22122.5% p.a.)." if st.session_state["inflation_adj"] else ""
    st.markdown(
        '<p style="font-size:9pt; color:' + NAVY + '; opacity:0.6; margin-top:1rem;">'
        '<strong>Model assumptions</strong> \u2014 '
        'Growth rate: {:.1f}% p.a. | '.format(st.session_state["growth_rate_param"])
        + 'SG rate: {:.1f}% p.a. | '.format(st.session_state["sg_rate_param"])
        + 'Annual debt repayment: {} | '.format(fmt_currency(st.session_state["debt_repayment_param"]))
        + 'Projection: {} years | '.format(_proj_years)
        + 'Surplus above repayment reinvested into portfolio | '
        'Income and expenses held constant in real terms.'
        + _infl_note
        + ' Projections are illustrative only and do not constitute financial advice.'
        '</p>',
        unsafe_allow_html=True,
    )
