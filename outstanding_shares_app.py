import streamlit as st
import requests

st.set_page_config(page_title="Outstanding Shares Finder", page_icon="📊")
st.title("📊 Outstanding Shares Finder (ETFs & Funds)")

ticker = st.text_input("Enter an ETF or mutual fund ticker symbol (e.g., JHCB, SPY, VTI):").upper().strip()
api_key = st.secrets["FMP_API_KEY"]

def get_fund_profile(symbol, api_key):
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
                "market_cap": profile.get("mktCap"),
                "price": profile.get("price"),
                "website": profile.get("website"),
                "symbol": symbol
            }
        else:
            return None
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None

if ticker:
    with st.spinner("Looking up fund data..."):
        result = get_fund_profile(ticker, api_key)

        if result:
            fund_name = result["name"]
            shares_outstanding = result["shares_outstanding"]
            market_cap = result["market_cap"]
            price = result["price"]
            website = result["website"]

            st.markdown(f"### 📄 Fund: **{fund_name} ({ticker})**")

            if shares_outstanding:
                st.write(f"**Shares Outstanding:** {int(shares_outstanding):,}")
            else:
                st.info("Shares Outstanding data is not available.")

            if market_cap:
                st.write(f"**Market Cap:** ${int(market_cap):,}")
            else:
                st.info("Market Cap data is not available.")

            if price:
                st.write(f"**Price per Share:** ${price:,.2f}")
            else:
                st.info("Price data is not available.")

            if market_cap and shares_outstanding:
                nav = market_cap / shares_outstanding
                st.write(f"**Estimated NAV:** ${nav:,.4f}")
            else:
                st.info("NAV could not be calculated due to missing data.")

            if website:
                st.markdown(f"[🔗 Official Fund Page]({website})", unsafe_allow_html=True)
            else:
                google_search = f"https://www.google.com/search?q={ticker}+official+site"
                st.markdown(f"[🔍 Search for fund profile on Google]({google_search})", unsafe_allow_html=True)

        else:
            st.warning("❌ No data found for that ticker. Please check that it's a valid ETF or mutual fund.")
