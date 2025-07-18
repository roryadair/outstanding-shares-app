import streamlit as st
import requests

st.set_page_config(page_title="Outstanding Shares Finder", page_icon="\U0001F4C8")
st.title("Outstanding Shares Finder")

st.markdown("""
Enter a stock ticker symbol (e.g., `AAPL`, `MSFT`, `TSLA`) to fetch the current number of shares outstanding.

Your Alpha Vantage API key is securely loaded from `.streamlit/secrets.toml`.
""")

api_key = st.secrets["ALPHA_VANTAGE_API_KEY"]
ticker_input = st.text_input("Stock Ticker", placeholder="e.g., AAPL")

if ticker_input:
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker_input}&apikey={api_key}"

    try:
        response = requests.get(url)
        data = response.json()

        shares_outstanding = data.get("SharesOutstanding")

        if shares_outstanding:
            shares_formatted = f"{int(shares_outstanding):,}"
            st.success(f"**{ticker_input.upper()}** has **{shares_formatted}** shares outstanding.")
        else:
            st.warning("Could not retrieve outstanding shares data. Please check the ticker symbol or try another one.")

    except Exception as e:
        st.error(f"An error occurred: {e}")
