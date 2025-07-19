import streamlit as st
import requests
import openai

st.set_page_config(page_title="Outstanding Shares Finder", page_icon="📊")
st.title("📊 Outstanding Shares Finder (ETFs & Funds)")

# Required secrets
fmp_key = st.secrets["FMP_API_KEY"]
alpha_key = st.secrets["ALPHA_VANTAGE_API_KEY"]
openai.api_key = st.secrets["OPENAI_API_KEY"]

ticker = st.text_input("Enter an ETF or mutual fund ticker symbol (e.g., VOO, SPY, ARKK):").upper().strip()

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
        st.error(f"FMP API error: {e}")
        return None

def get_from_alpha(symbol, api_key):
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={api_key}"
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()

        if data and data.get("SharesOutstanding"):
            try:
                shares = int(data.get("SharesOutstanding"))
            except ValueError:
                shares = None
            return {
                "name": data.get("Name", symbol),
                "shares": shares,
                "market_cap": int(data.get("MarketCapitalization", 0)) if data.get("MarketCapitalization") else None,
                "price": None,
                "website": None,
                "source": "Alpha Vantage"
            }
        return None
    except Exception as e:
        st.error(f"Alpha Vantage API error: {e}")
        return None

def get_chatgpt_answer(symbol):
    prompt = f"How many shares outstanding does the ETF {symbol} have as of the most recent data? Include the fund name and source if known."
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"ChatGPT fallback failed: {e}")
        return None

if ticker:
    with st.spinner("Looking up fund data..."):
        result = get_from_fmp(ticker, fmp_key)

        if not result or result["shares"] is None:
            alpha_result = get_from_alpha(ticker, alpha_key)
            if alpha_result and alpha_result["shares"]:
                result = alpha_result
            else:
                result = result  # show FMP even if incomplete

        if result and result["name"]:
            st.markdown(f"### 📄 Fund: **{result['name']} ({ticker})**")
            st.write(f"**Data Source:** {result['source']}")

            if result["shares"]:
                st.write(f"**Shares Outstanding:** {int(result['shares']):,}")
            else:
                st.warning("Shares Outstanding not available from either source.")

            if result["market_cap"]:
                st.write(f"**Market Cap:** ${int(result['market_cap']):,}")

            if result["price"]:
                st.write(f"**Price per Share:** ${result['price']:,.2f}")

            if result["market_cap"] and result["shares"]:
                nav = result["market_cap"] / result["shares"]
                st.write(f"**Estimated NAV:** ${nav:,.4f}")

            if result["website"]:
                st.markdown(f"[🔗 Official Fund Page]({result['website']})", unsafe_allow_html=True)
            else:
                st.markdown(f"[🔍 Google the fund]({'https://www.google.com/search?q=' + ticker + '+fund'})", unsafe_allow_html=True)

            # Final fallback to ChatGPT if still no shares
            if not result["shares"]:
                gpt_response = get_chatgpt_answer(ticker)
                if gpt_response:
                    st.markdown("### 🤖 ChatGPT Estimate")
                    st.markdown(gpt_response)
        else:
            gpt_response = get_chatgpt_answer(ticker)
            if gpt_response:
                st.markdown("### 🤖 ChatGPT Estimate")
                st.markdown(gpt_response)
            else:
                st.warning("❌ No data found from any source.")
