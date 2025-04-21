import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np

st.set_page_config(page_title="📈 Live Portfolio Tracker", layout="wide")
st.title("📈 Live Portfolio Auto-Tracker")

uploaded_file = st.file_uploader("Upload your portfolio CSV:", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("🧾 Portfolio Input:")
    st.dataframe(df)

    tickers = df["Ticker"].tolist()
    shares = df["Shares_Bought"].values
    entry_prices = df["Entry_Price"].values

    # Fetch live prices
    price_data = yf.download(tickers, period="1d", interval="1m", progress=False)
    if isinstance(price_data.columns, pd.MultiIndex) and "Close" in price_data.columns.levels[0]:
        price_data = price_data["Close"].iloc[-1]
    elif isinstance(price_data, pd.DataFrame):
        price_data = price_data.iloc[-1]
    else:
        st.error("Failed to fetch live prices.")
        st.stop()

    live_prices = price_data.values
    current_value = shares * live_prices
    initial_value = shares * entry_prices
    gain_loss = (current_value - initial_value) / initial_value * 100

    df["Current_Price"] = live_prices.round(2)
    df["Current_Value"] = current_value.round(2)
    df["Gain/Loss_%"] = gain_loss.round(2)

    st.write("📊 Live Portfolio Snapshot:")
    st.dataframe(df)

    total_initial = initial_value.sum()
    total_current = current_value.sum()
    total_gain = (total_current - total_initial) / total_initial * 100

    st.metric("💼 Total Portfolio Value", f"${total_current:,.2f}")
    st.metric("📈 Total Gain/Loss", f"{total_gain:.2f}%")
else:
    st.info("📤 Please upload your portfolio CSV file to begin tracking.")
