import streamlit as st
import requests

st.set_page_config(page_title="Outstanding Shares Finder", page_icon="📊")
st.title("📊 Outstanding Shares Finder (ETFs & Funds)")

ticker = st.text_input("Enter an ETF or mutual fund ticker symbol (e.g., JHCB, SPY, VTI):").upper().strip()
fmp_key = st.secrets["FMP_API_KEY"]
alpha_key = st.secrets["ALPHA_VANTAGE_API_KEY"]

def get_from_fmp(symbol, api_key):
    url = f"https://financialmodelingprep.com/api/v3/profile/{symbol}?apikey={api_key}"
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list) and len(data) > 0:
            p = data[0]
            return {
                "name": p.get("companyName", symbol),
                "shares": p.get("sharesOutstanding"),
                "market_cap": p.get("mktCap"),
                "price": p.get("price"),
                "website": p.get("website"),
                "source": "FMP"
            }
        return None
    except Exception as e:
        return None

def get_from_alpha(symbol, api_key):
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={api_key}"
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        if "SharesOutstanding" in data:
            return {
                "name": data.get("Name", symbol),
                "shares": int(data["SharesOutstanding"]),
                "market_cap": int(data.get("MarketCapitalization", 0)),
                "price": None,
                "website": None,
                "source": "Alpha Vantage"
            }
        return None
    except Exception as e:
        return None

if ticker:
    with st.spinner("Looking up fund data..."):
        result = get_from_fmp(ticker, fmp_key)

        # fallback if FMP fails or lacks share data
        if not result or result["shares"] is None:
            result = get_from_alpha(ticker, alpha_key)

        if result:
            st.markdown(f"### 📄 Fund: **{result['name']} ({ticker})**")
            st.write(f"**Data Source:** {result['source']}")

            if result["shares"]:
                st.write(f"**Shares Outstanding:** {int(result['shares']):,}")
            else:
                st.info("Shares Outstanding data is not available.")

            if result["market_cap"]:
                st.write(f"**Market Cap:** ${int(result['market_cap']):,}")
            else:
                st.info("Market Cap data is not available.")

            if result["price"]:
                st.write(f"**Price per Share:** ${result['price']:,.2f}")

            if result["market_cap"] and result["shares"]:
                nav = result["market_cap"] / result["shares"]
                st.write(f"**Estimated NAV:** ${nav:,.4f}")

            if result["website"]:
                st.markdown(f"[🔗 Official Fund Page]({result['website']})", unsafe_allow_html=True)
            else:
                st.markdown(f"[🔍 Google the fund]({'https://www.google.com/search?q=' + ticker + '+fund'})", unsafe_allow_html=True)
        else:
            st.warning("❌ No data found for that ticker in either FMP or Alpha Vantage.")
