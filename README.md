# Client Scenario Engine

A Streamlit web app for financial scenario analysis, built around the Sarah & Daniel demo client model.

## What it does

The app lets a financial planner enter a client's current financial position and compare the outcome of different strategies side by side.

**Inputs**
- Client name and basic profile (income, expenses, super, investments, cash, debt)
- Two optional scenarios (e.g. income increase, debt reduction) with custom labels

**Outputs**
- Statement of Financial Position (assets, liabilities, net position)
- Scenario comparison table across key metrics: net position, annual surplus, savings rate, debt-to-assets ratio, emergency buffer
- Bar charts comparing surplus and net position across scenarios
- 20-year net worth projection chart
- 5-year milestone table

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open `http://localhost:8501`.

## Deploy to Streamlit Community Cloud

This repo is configured to deploy directly to [Streamlit Community Cloud](https://streamlit.io/cloud) (free tier).

1. Push the repo to GitHub (already at `ahaythorpe/financial-planner`).
2. Go to <https://share.streamlit.io> and sign in with GitHub.
3. Click **New app** and select:
   - Repository: `ahaythorpe/financial-planner`
   - Branch: `main`
   - Main file path: `app.py`
4. Click **Deploy**. The app will install from `requirements.txt` and use the Python version pinned in `runtime.txt`.

Theme and server defaults live in `.streamlit/config.toml`.

> **Note:** Vercel does not host long-running Streamlit servers. Use Streamlit Cloud, Hugging Face Spaces, Render, or Railway instead.

## How the model works

See [`docs/MODEL.md`](docs/MODEL.md) for a plain-English walkthrough of every calculation — inputs, the 20-year projection loop, retirement readiness, drawdown, risk flags, and what the model does *not* model (tax, inflation, volatility).

## Project layout

```
app.py                      # main Streamlit app
helpers.py                  # shared calculation helpers
requirements.txt            # Python dependencies
runtime.txt                 # Python version pin for Streamlit Cloud
.streamlit/config.toml      # theme + server settings
.devcontainer/              # Codespaces / VS Code dev container
docs/MODEL.md               # plain-English explanation of the calculations
```

## Notes

- All projections are illustrative only and do not constitute financial advice.
- Default growth assumptions: 7% p.a. investment/super growth, 11.5% SG contributions, $20,000 annual debt repayment.
- Australian legislation reference: 2024-25 financial year.
