import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime

st.set_page_config(page_title="📈 Realistic Portfolio Tracker", layout="wide")
st.title("📈 Realistic Portfolio Auto-Tracker with Historical Entry Prices")

uploaded_file = st.file_uploader("Upload your portfolio CSV:", type=["csv"])
entry_date = st.date_input("Select your entry (purchase) date:", value=datetime(2024, 1, 2))

if uploaded_file and entry_date:
    df = pd.read_csv(uploaded_file)
    st.write("📄 Uploaded Portfolio:")
    st.dataframe(df)

    tickers = df["Ticker"].tolist()
    allocs = df["Allocation_USD"].values

    # Fetch historical entry prices
    entry_prices = []
    for ticker in tickers:
        hist = yf.download(ticker, start=entry_date, end=entry_date + pd.Timedelta(days=3))
        if not hist.empty:
            price = hist["Close"].iloc[0]
        else:
            price = np.nan
        entry_prices.append(price)

    df["Entry_Price"] = np.round(entry_prices, 2)
    df["Shares_Bought"] = np.round(allocs / df["Entry_Price"], 4)

    # Fetch current prices
    price_data = yf.download(tickers, period="1d", interval="1m", progress=False)
    if isinstance(price_data.columns, pd.MultiIndex) and "Close" in price_data.columns.levels[0]:
        live_prices = price_data["Close"].iloc[-1]
    elif isinstance(price_data, pd.DataFrame):
        live_prices = price_data.iloc[-1]
    else:
        st.error("❌ Failed to fetch live prices.")
        st.stop()

    df["Current_Price"] = np.round([live_prices.get(t, np.nan) for t in tickers], 2)
    df["Current_Value"] = np.round(df["Shares_Bought"] * df["Current_Price"], 2)
    df["Gain/Loss_%"] = np.round((df["Current_Value"] - allocs) / allocs * 100, 2)

    st.subheader("📊 Live Portfolio Snapshot")
    st.dataframe(df)

    total_current = df["Current_Value"].sum()
    total_initial = allocs.sum()
    total_gain = (total_current - total_initial) / total_initial * 100

    st.metric("💼 Total Portfolio Value", f"${total_current:,.2f}")
    st.metric("📈 Total Gain/Loss", f"{total_gain:.2f}%")
else:
    st.info("📤 Upload a CSV and choose an entry date to start.")
