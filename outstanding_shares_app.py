import streamlit as st
import requests
import openai
import time
import hmac
import hashlib
import base64
import json

# Streamlit setup
st.set_page_config(page_title="Outstanding Shares Finder", page_icon="📊")
st.title("📊 Outstanding Shares Finder (ETFs & Funds)")

# Load API keys from secrets
fmp_key = st.secrets["FMP_API_KEY"]
alpha_key = st.secrets["ALPHA_VANTAGE_API_KEY"]
openai.api_key = st.secrets["OPENAI_API_KEY"]
whale_shared_key = st.secrets["WHALE_WISDOM_SHARED_KEY"]
whale_secret_key = st.secrets["WHALE_WISDOM_SECRET_KEY"]

ticker = st.text_input("Enter an ETF or mutual fund ticker symbol (e.g., VOO, SPY, ARKK):").upper().strip()

# Helper functions
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
    except:
        return None

def get_from_alpha(symbol, api_key):
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={api_key}"
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        if data and data.get("SharesOutstanding"):
            return {
                "name": data.get("Name", symbol),
                "shares": int(data["SharesOutstanding"]),
                "market_cap": int(data.get("MarketCapitalization", 0)) if data.get("MarketCapitalization") else None,
                "price": None,
                "website": None,
                "source": "Alpha Vantage"
            }
        return None
    except:
        return None

def generate_signature(args_json, timestamp, secret_key):
    message = args_json + "\\n" + timestamp
    digest = hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha1).digest()
    return base64.b64encode(digest).decode()

def get_filer_id_from_ticker(symbol, shared_key, secret_key):
    url = "https://whalewisdom.com/shell/command.json"
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    args = {"command": f"fund --ticker={symbol}"}
    args_json = json.dumps(args)
    sig = generate_signature(args_json, timestamp, secret_key)
    params = {
        "args": args_json,
        "api_shared_key": shared_key,
        "timestamp": timestamp,
        "api_sig": sig
    }

    try:
        r = requests.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        return data.get("filer_id")
    except:
        return None

def get_from_whale_wisdom(symbol, shared_key, secret_key):
    filer_id = get_filer_id_from_ticker(symbol, shared_key, secret_key)
    if not filer_id:
        return None

    url = "https://whalewisdom.com/shell/command.json"
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    args = {"command": "holdings", "filer_ids": [filer_id], "columns": [14]}
    args_json = json.dumps(args)
    sig = generate_signature(args_json, timestamp, secret_key)
    params = {
        "args": args_json,
        "api_shared_key": shared_key,
        "timestamp": timestamp,
        "api_sig": sig
    }

    try:
        r = requests.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
            shares = data[0][0]  # column 14 should be first entry per single column request
            return {
                "name": symbol,
                "shares": int(shares),
                "market_cap": None,
                "price": None,
                "website": None,
                "source": "Whale Wisdom"
            }
        return None
    except:
        return None

def get_chatgpt_answer(symbol):
    prompt = f"How many shares outstanding does the ETF {symbol} have as of the most recent data? Include the fund name and source if known."
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=300
        )
        return response.choices[0].message.content
    except:
        return None

# Main logic
if ticker:
    with st.spinner("Looking up fund data..."):
        result = get_from_fmp(ticker, fmp_key)

        if not result or result["shares"] is None:
            result = get_from_alpha(ticker, alpha_key)

        if not result or result["shares"] is None:
            result = get_from_whale_wisdom(ticker, whale_shared_key, whale_secret_key)

        if result and result["shares"]:
            st.markdown(f"### 📄 Fund: **{result['name']} ({ticker})**")
            st.write(f"**Source:** {result['source']}")
            st.write(f"**Shares Outstanding:** {int(result['shares']):,}")
        else:
            gpt_response = get_chatgpt_answer(ticker)
            if gpt_response:
                st.markdown("### 🤖 ChatGPT Estimate")
                st.markdown(gpt_response)
            else:
                st.warning("❌ No data found from FMP, Alpha Vantage, Whale Wisdom, or ChatGPT.")

