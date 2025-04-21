import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from dimod import SimulatedAnnealingSampler

st.set_page_config(page_title="📈 Optimize & Track Portfolio", layout="wide")
st.title("📈 Simulated Annealing Optimizer + Realistic Portfolio Tracker")

st.header("1️⃣ Portfolio Optimization")

tickers_input = st.text_area("Enter tickers (comma-separated):", "AAPL,MSFT,NVDA,TSLA,GOOGL", height=100)
tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

if len(tickers) < 2:
    st.warning("Enter at least two tickers.")
    st.stop()

top_k = st.slider("Top-k Assets to Select", 1, len(tickers), min(5, len(tickers)))
risk_aversion = st.slider("Risk Aversion", 0.0, 1.0, 0.5)
portfolio_value = st.number_input("Total Portfolio Value (USD)", value=10000)

# Get 3 months of daily returns for optimization
end = datetime.today()
start = end - timedelta(days=90)

raw_data = yf.download(tickers, start=start, end=end)
if isinstance(raw_data.columns, pd.MultiIndex):
    price_data = raw_data["Adj Close"] if "Adj Close" in raw_data.columns.levels[0] else raw_data["Close"]
else:
    price_data = raw_data

returns = price_data.pct_change().dropna()

mean_returns = returns.mean().values
cov_matrix = returns.cov().values
n = len(tickers)
Q = {}

# Construct QUBO
for i in range(n):
    for j in range(n):
        if i == j:
            Q[(i, i)] = -mean_returns[i] + risk_aversion * cov_matrix[i][i]
        else:
            Q[(i, j)] = risk_aversion * cov_matrix[i][j]

penalty = 4.0
for i in range(n):
    Q[(i, i)] += penalty * (1 - 2 * top_k)
    for j in range(i+1, n):
        Q[(i, j)] += 2 * penalty

# Solve QUBO
if st.button("🔍 Optimize Portfolio"):
    sampler = SimulatedAnnealingSampler()
    result = sampler.sample_qubo(Q, num_reads=500)
    best = result.first.sample
    selection = np.array([best[i] for i in range(n)])
    if selection.sum() == 0:
        st.error("No assets selected.")
        st.stop()

    weights = selection / selection.sum()
    allocs = weights * portfolio_value

    st.success("✅ Optimized Portfolio:")
    selected = [tickers[i] for i in range(n) if selection[i] == 1]
    st.write(selected)

    df = pd.DataFrame({
        "Ticker": [tickers[i] for i in range(n)],
        "Weight": weights.round(3),
        "Allocation_USD": allocs.round(2),
        "Selected": selection
    }).query("Selected == 1").reset_index(drop=True)

    st.dataframe(df)

    st.header("2️⃣ Portfolio Tracker")

    entry_date = st.date_input("Select entry (purchase) date:", value=datetime(2024, 1, 2))

    # Fetch entry prices
    entry_prices = []
    for ticker in df["Ticker"]:
        hist = yf.download(ticker, start=entry_date, end=entry_date + timedelta(days=3))
        price = hist["Close"].iloc[0] if not hist.empty else np.nan
        entry_prices.append(price)

    df["Entry_Price"] = np.round(entry_prices, 2)
    df["Shares_Bought"] = np.round(df["Allocation_USD"] / df["Entry_Price"], 4)

    # Fetch current prices
    live = yf.download(df["Ticker"].tolist(), period="1d", interval="1m", progress=False)
    if isinstance(live.columns, pd.MultiIndex):
        current = live["Close"].iloc[-1]
    else:
        current = live.iloc[-1]

    df["Current_Price"] = [current.get(t, np.nan) for t in df["Ticker"]]
    df["Current_Value"] = np.round(df["Current_Price"] * df["Shares_Bought"], 2)
    df["Gain/Loss_%"] = np.round((df["Current_Value"] - df["Allocation_USD"]) / df["Allocation_USD"] * 100, 2)

    st.subheader("📊 Live Portfolio Snapshot")
    st.dataframe(df)

    total_current = df["Current_Value"].sum()
    total_initial = df["Allocation_USD"].sum()
    total_gain = (total_current - total_initial) / total_initial * 100

    st.metric("💼 Total Portfolio Value", f"${total_current:,.2f}")
    st.metric("📈 Total Gain/Loss", f"{total_gain:.2f}%")
