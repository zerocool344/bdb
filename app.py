import streamlit as st
import pandas as pd
import yfinance as yf
import time

st.set_page_config(page_title="Daily Consensus Desk", layout="wide", page_icon="📈")

# Master Watchlist
WATCHLIST = [
    "GOOGL", "CVS", "AMZN", "MSFT", "JPM", 
    "SNOW", "CRM", "NKE", "DIS", "BA", 
    "STX", "LNG", "U", "AAPL", "NVDA", "META"
]

st.title("📈 Daily Consensus Desk (Live Screener)")
st.markdown("An autonomous equity research screening dashboard. Information is purely research and not financial advice.")

@st.cache_data(ttl=3600, show_spinner=False)
def run_screener(watchlist):
    results = []
    
    # Optional progress bar if running in Streamlit
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, ticker_sym in enumerate(watchlist):
        status_text.text(f"Screening {ticker_sym}...")
        try:
            stock = yf.Ticker(ticker_sym)
            info = stock.info
            
            # Fetch data fields
            name = info.get("shortName", ticker_sym)
            current_price = info.get("currentPrice")
            target_price = info.get("targetMeanPrice")
            rec_key = info.get("recommendationKey", "N/A")
            
            # Format recommendation string
            consensus = rec_key.replace("_", " ").title() if rec_key != "none" else "N/A"
            
            # Calculate Upside
            upside = None
            if current_price and target_price and current_price > 0:
                upside = round(((target_price - current_price) / current_price) * 100, 2)
            
            # Determine List Placement (NEAR vs FAR vs NEUTRAL)
            # FAR = High upside (e.g. > 25%), NEAR = Moderate upside (e.g. 10-25%)
            # This is a dynamic rule set based on upside.
            list_placement = "NEUTRAL"
            if upside is not None:
                if upside > 25.0:
                    list_placement = "FAR (Deep Value)"
                elif upside >= 10.0:
                    list_placement = "NEAR (Growth/Value)"
                else:
                    list_placement = "WATCH (Low Upside)"
                    
            results.append({
                "Ticker": ticker_sym,
                "Name": name,
                "List": list_placement,
                "Current Price": f"${current_price}" if current_price else "N/A",
                "Target Price": f"${target_price}" if target_price else "N/A",
                "Consensus": consensus,
                "Upside %": upside if upside is not None else 0.0,
                "Thesis": f"Dynamic rating: {consensus}. Target: {target_price}",
                "Risk": "Market volatility, execution risk."
            })
            
        except Exception as e:
            # Handle SSL or rate limit errors gracefully
            results.append({
                "Ticker": ticker_sym,
                "Name": "Data Fetch Error",
                "List": "ERROR",
                "Current Price": "N/A",
                "Target Price": "N/A",
                "Consensus": "N/A",
                "Upside %": 0.0,
                "Thesis": "Error fetching data.",
                "Risk": str(e)
            })
            
        # Update progress
        progress_bar.progress((i + 1) / len(watchlist))
        time.sleep(0.1) # Small delay to respect rate limits
        
    progress_bar.empty()
    status_text.empty()
    
    return pd.DataFrame(results)

@st.cache_data(ttl=86400, show_spinner=False)
def get_chart_data(ticker_sym):
    try:
        stock = yf.Ticker(ticker_sym)
        hist = stock.history(period="1y")
        if not hist.empty:
            return hist[['Close']]
    except Exception:
        pass
    return pd.DataFrame()

# Header with Refresh button
col1, col2 = st.columns([8, 1])
with col2:
    if st.button("🔄 Refresh Live Data", help="Clears cache and screens Yahoo Finance live"):
        st.cache_data.clear()
        st.rerun()

# Run the screener (will use cache unless refreshed)
with st.spinner("Running Live Market Screener..."):
    df = run_screener(WATCHLIST)

# Tabs
tab1, tab2 = st.tabs(["Live Overview (Consensus)", "Interactive Stock Insights"])

with tab1:
    st.subheader("NEAR | 1–2 Year Consensus (10% - 25% Upside)")
    near_df = df[df['List'] == 'NEAR (Growth/Value)'].drop(columns=['List']).sort_values('Upside %', ascending=False).reset_index(drop=True)
    st.dataframe(near_df, use_container_width=True)

    st.subheader("FAR | 2–5 Year Deep Value (>25% Upside)")
    far_df = df[df['List'] == 'FAR (Deep Value)'].drop(columns=['List']).sort_values('Upside %', ascending=False).reset_index(drop=True)
    st.dataframe(far_df, use_container_width=True)
    
    st.subheader("WATCH | Low Upside / Overvalued (<10% Upside)")
    watch_df = df[df['List'] == 'WATCH (Low Upside)'].drop(columns=['List']).sort_values('Upside %', ascending=False).reset_index(drop=True)
    st.dataframe(watch_df, use_container_width=True)

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
                c1, c2, c3, c4 = st.columns(4)
                
                c1.metric(label=f"**{row['Ticker']}** - {row['Name']}", value=row['Current Price'])
                c2.metric(label="Consensus Rating", value=row['Consensus'])
                c3.metric(label="Target Price (Mean)", value=row['Target Price'])
                c4.metric(label="Target Upside", value=f"{row['Upside %']}%" if row['Upside %'] != 0.0 else "N/A")
                
                st.markdown(f"**List Classification:** {row['List']}")
                st.markdown(f"**Dynamic Thesis:** {row['Thesis']}")
                st.markdown(f"**Risk:** {row['Risk']}")
                
                # Render Chart
                chart_data = get_chart_data(row['Ticker'])
                if not chart_data.empty:
                    st.markdown("**1-Year Price Trend**")
                    st.line_chart(chart_data, height=150)
