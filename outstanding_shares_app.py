import streamlit as st
import requests

st.set_page_config(page_title="Outstanding Shares Finder", page_icon="📊")
st.title("📊 Outstanding Shares Finder (ETFs & Funds)")

# Input field for ticker
ticker = st.text_input("Enter an ETF or mutual fund ticker symbol (e.g., JHCB, SPY, VTI):").upper().strip()

# Fetch API key securely
api_key = st.secrets.get("FMP_API_KEY")

def get_outstanding_shares(symbol, api_key):
    url = f"https://financialmodelingprep.com/api/v3/profile/{symbol}?apikey={api_key}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, list) and len(data) > 0:
            profile = data[0]
            return {
                "name": profile.get("companyName", symbol),
                "shares_outstanding": profile.get("sharesOutstanding"),
                "symbol": symbol
            }
        else:
            return None
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None

if ticker:
    with st.spinner("Looking up shares outstanding..."):
        result = get_outstanding_shares(ticker, api_key)

        if result and result["shares_outstanding"]:
            shares = f"{int(result['shares_outstanding']):,}"
            st.success(f"✅ **{result['name']} ({result['symbol']})** has **{shares}** shares outstanding.")
        else:
            st.warning("❌ No data found for that ticker. Please check that it's a valid ETF or mutual fund.")

