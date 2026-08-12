import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="Daily Consensus Desk", layout="wide", page_icon="📈")

# Raw data from our research
DATA = [
    {"Ticker": "GOOGL", "Name": "Alphabet Inc.", "List": "NEAR", "Decline %": None, "Consensus": "Strong Buy", "Upside %": 22.5, "Thesis": "Strong Cloud and AI growth", "Risk": "Elevated capital expenditure"},
    {"Ticker": "CVS", "Name": "CVS Health", "List": "NEAR", "Decline %": None, "Consensus": "Strong Buy", "Upside %": 21.0, "Thesis": "Earnings beat and value", "Risk": "Elevated medical cost trends"},
    {"Ticker": "AMZN", "Name": "Amazon.com", "List": "NEAR", "Decline %": None, "Consensus": "Strong Buy", "Upside %": 19.5, "Thesis": "AWS expansion and margin growth", "Risk": "E-commerce margin pressure"},
    {"Ticker": "MSFT", "Name": "Microsoft Corp.", "List": "NEAR", "Decline %": None, "Consensus": "Buy", "Upside %": 13.0, "Thesis": "Durable AI infrastructure demand", "Risk": "AI capacity overbuild concerns"},
    {"Ticker": "JPM", "Name": "JPMorgan Chase", "List": "NEAR", "Decline %": None, "Consensus": "Buy", "Upside %": 4.0, "Thesis": "Resilient core banking profitability", "Risk": "Valuation fully priced"},
    {"Ticker": "SNOW", "Name": "Snowflake Inc.", "List": "FAR", "Decline %": 45.0, "Consensus": "Buy", "Upside %": 35.0, "Thesis": "Enterprise client adoption growth", "Risk": "Valuation multiples"},
    {"Ticker": "CRM", "Name": "Salesforce Inc.", "List": "FAR", "Decline %": 37.0, "Consensus": "Buy", "Upside %": 27.0, "Thesis": "Undervalued AI monetization", "Risk": "Slow organic revenue growth"},
    {"Ticker": "NKE", "Name": "Nike Inc.", "List": "FAR", "Decline %": 60.0, "Consensus": "Moderate Buy", "Upside %": 25.0, "Thesis": "Long-term brand normalization", "Risk": "Management execution"},
    {"Ticker": "DIS", "Name": "Walt Disney Co.", "List": "FAR", "Decline %": 16.3, "Consensus": "Buy", "Upside %": 25.0, "Thesis": "Streaming profitability inflection", "Risk": "Park attendance softness"},
    {"Ticker": "BA", "Name": "Boeing Co.", "List": "FAR", "Decline %": 10.0, "Consensus": "Buy", "Upside %": 17.0, "Thesis": "Production and cash flow recovery", "Risk": "Execution and safety risks"},
]

df = pd.DataFrame(DATA)

st.title("📈 Daily Consensus Desk")
st.markdown("An equity research screening dashboard. Information is purely research and not financial advice.")

# Caching to avoid hammering the Yahoo Finance API
@st.cache_data(ttl=3600)
def fetch_live_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d")
        if not data.empty:
            return round(data["Close"].iloc[-1], 2)
        return "N/A"
    except Exception:
        return "Error"

# Header with Refresh button
col1, col2 = st.columns([8, 1])
with col2:
    if st.button("🔄 Refresh Data", help="Clears cache and fetches latest prices from Yahoo Finance"):
        st.cache_data.clear()
        st.rerun()

# Tabs
tab1, tab2 = st.tabs(["Overview (Consensus)", "Stock Insights"])

with tab1:
    st.subheader("NEAR | 1–2 Year Consensus")
    near_df = df[df['List'] == 'NEAR'].drop(columns=['List', 'Decline %']).sort_values('Upside %', ascending=False).reset_index(drop=True)
    st.dataframe(near_df, use_container_width=True)

    st.subheader("FAR | 2–5 Year Deep Value")
    far_df = df[df['List'] == 'FAR'].drop(columns=['List']).sort_values('Upside %', ascending=False).reset_index(drop=True)
    st.dataframe(far_df, use_container_width=True)

with tab2:
    st.subheader("🔍 Interactive Stock Insights")
    search_query = st.text_input("Search by Ticker or Name (e.g. MSFT or Apple)", "")
    
    # Filter based on search query
    filtered_df = df[
        df['Ticker'].str.contains(search_query, case=False) | 
        df['Name'].str.contains(search_query, case=False)
    ]

    if filtered_df.empty:
        st.info("No stocks matched your search.")
    else:
        for index, row in filtered_df.iterrows():
            with st.container(border=True):
                # We use metric cards here
                c1, c2, c3, c4 = st.columns(4)
                live_price = fetch_live_price(row['Ticker'])
                
                c1.metric(label=f"**{row['Ticker']}** - {row['Name']}", value=f"${live_price}" if live_price != "N/A" else "N/A")
                
                # Color code the consensus
                cons_color = "normal"
                if "Buy" in row['Consensus']:
                    cons_color = "normal"
                
                c2.metric(label="Consensus Rating", value=row['Consensus'])
                c3.metric(label="Target Upside", value=f"{row['Upside %']}%")
                
                if pd.notna(row['Decline %']):
                    c4.metric(label="High Decline (FAR)", value=f"-{row['Decline %']}%")
                
                st.markdown(f"**Thesis:** {row['Thesis']}")
                st.markdown(f"**Risk:** {row['Risk']}")
