# Financial Planner

A Streamlit web app for financial scenario analysis, based on the Sarah & Daniel client model.

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

## How to run

```
pip install -r requirements.txt
streamlit run app.py
```

Open your browser at `http://localhost:8501`

## Notes

- All projections are illustrative only and do not constitute financial advice.
- Default growth assumptions: 7% p.a. investment/super growth, 11.5% SG contributions, $20,000 annual debt repayment.

---
app_file: app.py
sdk: streamlit
sdk_version: 1.32.0
