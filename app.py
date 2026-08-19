import streamlit as st
import pandas as pd
import yfinance as yf
import time
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from bs4 import BeautifulSoup

# TauricResearch/TradingAgents multi-agent financial framework integration
from tradingagents import TradingAgentsGraph, DEFAULT_CONFIG
from tradingagents.ui import render_tradingagents_desk, create_radar_chart

st.set_page_config(page_title="The Tendie Tracker", layout="wide", page_icon="logo.png")

# ── Global Soft Gray Institutional Theme ──
st.markdown("""
<style>
    /* Soft gray background */
    .stApp { background-color: #F5F7FA; }
    
    /* Tab styling - steel blue underline on active */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; border-bottom: 2px solid #E2E8F0; }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        color: #64748B;
        font-weight: 600;
        font-size: 0.9rem;
        padding: 10px 18px;
        border-radius: 6px 6px 0 0;
    }
    .stTabs [aria-selected="true"] {
        color: #1E3A5F !important;
        border-bottom: 3px solid #3B82A0;
        background-color: rgba(59, 130, 160, 0.06);
    }
    .stTabs [data-baseweb="tab"]:hover { color: #1E3A5F; background-color: rgba(59, 130, 160, 0.04); }
    
    /* Metric cards with clean borders */
    [data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 12px 16px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
    }
    [data-testid="stMetricLabel"] { color: #64748B !important; font-size: 0.8rem; }
    [data-testid="stMetricValue"] { color: #1E293B !important; font-weight: 700; }
    
    /* Dataframe clean styling */
    .stDataFrame { border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
    
    /* Subheader styling */
    h1 { color: #1E293B !important; }
    h2, h3 { color: #334155 !important; letter-spacing: 0.3px; }
    
    /* Button styling */
    .stButton > button[kind="primary"] {
        background: linear-gradient(90deg, #3B82A0 0%, #2C6E8A 100%) !important;
        color: #FFFFFF !important;
        font-weight: 700;
        border: none;
    }
    .stButton > button { border: 1px solid #CBD5E1; background: #FFFFFF; color: #334155; }
    .stButton > button:hover { border-color: #3B82A0; color: #1E3A5F; }
    
    /* Container borders */
    [data-testid="stContainer"] { border-color: #E2E8F0 !important; }
    
    /* Input fields */
    .stTextInput input { background: #FFFFFF; border: 1px solid #CBD5E1; color: #1E293B; }
    .stSelectbox > div > div { background: #FFFFFF; }
    
    /* Neon sign - Subtle Ticker Style */
    @keyframes neon-flash {
        0%, 100% { text-shadow: 0 0 6px rgba(0, 255, 65, 0.8), 0 0 12px rgba(0, 255, 65, 0.3); color: #e2fce6; opacity: 1; }
        50% { text-shadow: 0 0 2px rgba(0, 255, 65, 0.6); color: #9be6a8; opacity: 0.8; }
    }
    .neon-sign {
        font-family: 'Courier New', Courier, monospace;
        font-size: 16px;
        font-weight: 500;
        letter-spacing: 1.5px;
        color: #e2fce6;
        animation: neon-flash 2.5s infinite alternate ease-in-out;
        padding: 5px 12px;
        border: 1px solid rgba(0, 255, 65, 0.6);
        border-radius: 6px;
        display: inline-block;
        box-shadow: 0 0 6px rgba(0, 255, 65, 0.25), inset 0 0 6px rgba(0, 255, 65, 0.15);
        background-color: rgba(10, 20, 15, 0.9);
    }
</style>
""", unsafe_allow_html=True)

# Master Watchlist
WATCHLIST = [
    "GOOGL", "CVS", "AMZN", "MSFT", "JPM", 
    "SNOW", "CRM", "NKE", "DIS", "BA", 
    "STX", "LNG", "U", "AAPL", "NVDA", "META"
]


col_logo, col_title, col_neon = st.columns([1, 7, 4])
with col_logo:
    st.image("logo.png", use_container_width=True)
with col_title:
    st.title("The Tendie Tracker")
    st.markdown("Automated equity screening for apes hunting deep effin' value. (Not financial advice—we just like the stock. 🐱📈)")

with col_neon:
    nc1, nc2 = st.columns([3, 1])
    with nc1:
        st.markdown("""
            <div style="display: flex; justify-content: flex-end; align-items: flex-start; margin-top: 15px;">
                <div class="neon-sign">WE LIKE THE STOCK!</div>
            </div>
        """, unsafe_allow_html=True)
    with nc2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄", help="Refresh all live data", use_container_width=True):
            from datetime import datetime, timezone, timedelta
            st.session_state["last_refreshed"] = datetime.now(timezone(timedelta(hours=-6))).strftime("%b %d, %Y • %I:%M %p CST")
            st.cache_data.clear()
            st.rerun()


@st.cache_data(ttl=3600, show_spinner=False)
def run_screener(watchlist):
    results = []
    
    for i, ticker_sym in enumerate(watchlist):
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
        time.sleep(0.1) # Small delay to respect rate limits
        
    return pd.DataFrame(results)

@st.cache_data(ttl=86400, show_spinner=False)
def get_chart_data(ticker_sym, period="1y"):
    try:
        stock = yf.Ticker(ticker_sym)
        hist = stock.history(period=period)
        if not hist.empty:
            return hist
    except Exception:
        pass
    return pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner=False)
def get_insider_data(ticker_sym):
    result = {"insider": pd.DataFrame()}
    try:
        stock = yf.Ticker(ticker_sym)
        # Fetch Insider Transactions
        insider = stock.insider_transactions
        if insider is not None and not insider.empty:
            result["insider"] = insider.head(10) # Top 10 recent
    except Exception as e:
        pass
    return result

def calculate_fundamental_score(info):
    score = 0
    flags = []
    
    # Simple Norn-style Fundamental Scoring
    roe = info.get('returnOnEquity', 0)
    if roe and roe > 0.15:
        score += 1
        flags.append("🟢 Strong ROE (>15%)")
    elif roe and roe < 0:
        flags.append("🔴 Negative ROE")
        
    debt_eq = info.get('debtToEquity', 0)
    if debt_eq and debt_eq < 100:
        score += 1
        flags.append("🟢 Low Debt (<100%)")
    elif debt_eq and debt_eq > 200:
        flags.append("🔴 High Debt Burden")
        
    margin = info.get('operatingMargins', 0)
    if margin and margin > 0.10:
        score += 1
        flags.append("🟢 Healthy Operating Margin")
        
    return score, flags

@st.cache_data(ttl=86400, show_spinner=False)
def get_pelosi_trades():
    try:
        # Pulling 2026 data directly from the raw GitHub parquet file (never gets blocked by Cloudflare/WAF)
        url = "https://raw.githubusercontent.com/kovagent/congresskit/main/data/year=2026/congress-2026.parquet"
        df = pd.read_parquet(url)
        pelosi = df[df['member_name'].str.contains('Pelosi', na=False, case=False)].copy()
        
        if pelosi.empty:
            return pd.DataFrame()
            
        def format_amount(row):
            try:
                low = float(row['amount_low']) if not pd.isna(row['amount_low']) else 0
                high = float(row['amount_high']) if not pd.isna(row['amount_high']) else 0
                def format_num(n):
                    if n >= 1e6: return f"${int(n/1e6)}M"
                    if n >= 1e3: return f"${int(n/1e3)}K"
                    return f"${int(n)}"
                return f"{format_num(low)} - {format_num(high)}"
            except:
                return "Unknown"
                
        pelosi['Size'] = pelosi.apply(format_amount, axis=1)
        pelosi['Action'] = pelosi['txn_type'].str.replace('_', ' ').str.title()
        
        pelosi['Date Traded'] = pd.to_datetime(pelosi['txn_date'], format='%Y%m%d', errors='coerce').dt.strftime('%Y-%m-%d')
        pelosi.loc[pelosi['Date Traded'].isna(), 'Date Traded'] = pelosi['txn_date']
        
        pelosi = pelosi.rename(columns={'ticker': 'Ticker'})
        pelosi = pelosi.dropna(subset=['Ticker'])
        pelosi = pelosi[pelosi['Ticker'] != '']
        
        final = pelosi[['Ticker', 'Action', 'Date Traded', 'Size']].sort_values(by='Date Traded', ascending=False)
        return final
    except Exception as e:
        return pd.DataFrame()

# Run the screener (will use cache unless refreshed)
with st.spinner("Running Live Market Screener..."):
    df = run_screener(WATCHLIST)

# Track last refresh timestamp
from datetime import datetime, timezone, timedelta
CST = timezone(timedelta(hours=-6))
if "last_refreshed" not in st.session_state:
    st.session_state["last_refreshed"] = datetime.now(CST).strftime("%b %d, %Y • %I:%M %p CST")

# Creator badge + Last refreshed strip
st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; 
                padding: 6px 12px; margin: 4px 0 12px 0; border-radius: 6px;
                background: linear-gradient(90deg, rgba(59,130,160,0.08), rgba(245,247,250,0)); 
                border: 1px solid #E2E8F0;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="background: #3B82A0; color: #FFFFFF; font-weight: 700; font-size: 0.75rem; 
                         padding: 3px 10px; border-radius: 20px; letter-spacing: 0.5px;">BUILT BY ZEROCOOL</span>
            <span style="color: #94A3B8; font-size: 0.78rem;">v2.0 • Multi-Agent Edition</span>
        </div>
        <div style="color: #64748B; font-size: 0.78rem;">
            🕐 Data refreshed: <strong style="color: #334155;">{st.session_state["last_refreshed"]}</strong>
        </div>
    </div>
""", unsafe_allow_html=True)

# Tabs
tab1, tab_tradingagents, tab4, tab5, tab6 = st.tabs([
    "📊 Overview",
    "🧬 AI Desk",
    "🇺🇸 Pelosi",
    "📈 ETFs",
    "📚 Resources"
])

with tab1:
    main_col, side_col = st.columns([2.5, 1.5])
    with main_col:
            st.subheader("NEAR | 1–2 Year Consensus (10% - 25% Upside)")
            near_df = df[df['List'] == 'NEAR (Growth/Value)'].drop(columns=['List']).sort_values('Upside %', ascending=False).reset_index(drop=True)
            st.dataframe(near_df, use_container_width=True)
        
            st.subheader("FAR | 2–5 Year Deep Value (>25% Upside)")
            far_df = df[df['List'] == 'FAR (Deep Value)'].drop(columns=['List']).sort_values('Upside %', ascending=False).reset_index(drop=True)
            st.dataframe(far_df, use_container_width=True)
            
            st.subheader("WATCH | Low Upside / Overvalued (<10% Upside)")
            watch_df = df[df['List'] == 'WATCH (Low Upside)'].drop(columns=['List']).sort_values('Upside %', ascending=False).reset_index(drop=True)
            st.dataframe(watch_df, use_container_width=True)
        

    with side_col:
            st.subheader("🔍 Stock Lookup")
            search_query = st.text_input("Search by Ticker or Name (e.g. MSFT or Apple)", "")
            
            if not search_query.strip():
                filtered_df = pd.DataFrame()
            else:
                # 1. First search the existing master list
                filtered_df = df[
                    df['Ticker'].str.contains(search_query, case=False) | 
                    df['Name'].str.contains(search_query, case=False)
                ]
                
                # 2. If not found, try to fetch it live as a ticker symbol
                if filtered_df.empty:
                    with st.spinner(f"Fetching live data for {search_query.upper()}..."):
                        dynamic_df = run_screener([search_query.upper()])
                        if not dynamic_df.empty and dynamic_df['List'].iloc[0] != 'ERROR':
                            filtered_df = dynamic_df
                            
                filtered_df = filtered_df.head(1)
        
            if not search_query.strip():
                st.info("Enter a ticker or company name above to view details.")
            elif filtered_df.empty:
                st.error(f"'{search_query}' not found in master list and is not a valid ticker symbol.")
            else:
                for index, row in filtered_df.iterrows():
                    with st.container(border=True):
                        c1, c2 = st.columns(2)
                        c3, c4 = st.columns(2)
                        
                        c1.metric(label=f"**{row['Ticker']}** - {row['Name']}", value=row['Current Price'])
                        c2.metric(label="Consensus Rating", value=row['Consensus'])
                        c3.metric(label="Target Price (Mean)", value=row['Target Price'])
                        c4.metric(label="Target Upside", value=f"{row['Upside %']}%" if row['Upside %'] != 0.0 else "N/A")
                        
                        st.markdown(f"**List Classification:** {row['List']}")
                        st.markdown(f"**Dynamic Thesis:** {row['Thesis']}")
                        st.markdown(f"**Risk:** {row['Risk']}")
                        
                        # Setup timeframe selection
                        ticker = row['Ticker']
                        key_name = f"period_{ticker}"
                        period_options = {"1D": "1d", "5D": "5d", "1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y", "5Y": "5y"}
                        
                        if key_name not in st.session_state:
                            st.session_state[key_name] = "1Y"
                        fetch_period = period_options[st.session_state[key_name]]
                        
                        # Render Chart
                        try:
                            chart_data = get_chart_data(ticker, period=fetch_period)
                            if not chart_data.empty:
                                st.markdown(f"**{st.session_state[key_name]} Price Trend**")
                                
                                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                                    vertical_spacing=0.03, row_width=[0.2, 0.7])
                                
                                fig.add_trace(go.Scatter(
                                    x=chart_data.index,
                                    y=chart_data['Close'],
                                    mode='lines',
                                    name="Price",
                                    line=dict(color='#3B82A0', width=2),
                                    fill='tozeroy',
                                    fillcolor='rgba(59, 130, 160, 0.1)'
                                ), row=1, col=1)
                                
                                fig.add_trace(go.Bar(
                                    x=chart_data.index, 
                                    y=chart_data['Volume'], 
                                    marker_color='rgba(128, 128, 128, 0.4)', 
                                    name="Volume"
                                ), row=2, col=1)
                                
                                fig.update_layout(
                                    xaxis_rangeslider_visible=False,
                                    height=250,
                                    margin=dict(l=0, r=0, t=10, b=0),
                                    showlegend=False,
                                    plot_bgcolor="rgba(0,0,0,0)",
                                    paper_bgcolor="rgba(0,0,0,0)"
                                )
                                fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
                                fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
                                
                                st.plotly_chart(fig, use_container_width=True)
                                
                                # Timeframe Toggle (Centered below graph)
                                st.markdown("<br>", unsafe_allow_html=True)
                                st.radio(
                                        f"Select Timeframe for {ticker}",
                                        options=list(period_options.keys()),
                                        horizontal=True,
                                        key=key_name,
                                        label_visibility="collapsed"
                                    )
                        except Exception as e:
                            st.error("Error loading chart.")
        
                        # 1-Click Multi-Agent Deliberation Launch
                        if st.button(f"🤖 Launch Multi-Agent Committee for {ticker}", key=f"btn_ta_tab2_{ticker}", use_container_width=True):
                            st.session_state["selected_ta_ticker"] = ticker
                            st.info(f"✅ Queued **{ticker}**! Switch to Tab 2 ('🤖 TradingAgents Desk') to view the AI Committee deliberation.")
        
with tab_tradingagents:
    render_tradingagents_desk(WATCHLIST)

with tab4:
    st.subheader("🇺🇸 Nancy Pelosi Trade Tracker")
    st.markdown("### ⚠️ DATA LAG NOTICE")
    st.warning("By law (The STOCK Act), members of Congress have up to 45 days to report their trades. The data below represents the most recent **publicly disclosed filings**, but it is not real-time to the day the trade was executed.")
    
    with st.spinner("Scraping latest public disclosures..."):
        pelosi_df = get_pelosi_trades()
        if not pelosi_df.empty:
            st.dataframe(pelosi_df, use_container_width=True, hide_index=True)
        else:
            st.error("Failed to scrape trades. The source website might be temporarily blocking automated requests.")

with tab5:
    st.subheader("📈 ETF Performance Tracking")
    st.markdown("Track the performance of **NANC** (Unusual Whales Subversive Democratic Trading ETF) against the broader market (**SPY**, **QQQ**, & **VOO**).")
    
    period_options = {"1D": "1d", "5D": "5d", "1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y", "5Y": "5y"}
    if "etf_period" not in st.session_state:
        st.session_state.etf_period = "1Y"
        
    with st.spinner("Fetching ETF benchmark data..."):
        try:
            tickers = ["NANC", "SPY", "QQQ", "VOO"]
            data_dict = {}
            fetch_period = period_options[st.session_state.etf_period]
            
            for t in tickers:
                hist = yf.Ticker(t).history(period=fetch_period)
                if not hist.empty:
                    # Normalize to percentage return
                    first_close = hist['Close'].iloc[0]
                    hist['Return'] = ((hist['Close'] - first_close) / first_close) * 100
                    data_dict[t] = hist
                    
            if data_dict:
                fig = go.Figure()
                colors = {"NANC": "#3B82A0", "SPY": "#E07A3A", "QQQ": "#7C5CBF", "VOO": "#64748B"}
                
                for t, df_t in data_dict.items():
                    fig.add_trace(go.Scatter(x=df_t.index, y=df_t['Return'], mode='lines', name=t, line=dict(color=colors.get(t))))
                    
                fig.update_layout(
                    title=f"{st.session_state.etf_period} Cumulative Return (%)",
                    yaxis_title="Return (%)",
                    xaxis_title="Date",
                    height=400,
                    margin=dict(l=0, r=0, t=40, b=0),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    hovermode="x unified"
                )
                fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
                fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)', ticksuffix="%")
                
                st.plotly_chart(fig, use_container_width=True)
                
            # Timeframe Toggle (Centered below graph)
            st.markdown("<br>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns([1, 4, 1])
            with col2:
                st.radio(
                    "Select Timeframe",
                    options=list(period_options.keys()),
                    horizontal=True,
                    key="etf_period",
                    label_visibility="collapsed"
                )
        except Exception as e:
            st.error(f"Could not load ETF data: {e}")

with tab6:
    st.subheader("📚 Curated Quant Resources & Master Lists")
    st.markdown("Explore the best open-source quantitative finance and alternative data stacks available on GitHub.")
    
    st.markdown("""
    ### 1. Alternative Data & Sentiment
    *   **[Stocksera](https://github.com/guanquann/Stocksera):** An open-source aggregator tracking Reddit sentiment (WallStreetBets), Failures to Deliver (FTDs), and dark pool volumes.
    *   **[Quiver Quantitative](https://github.com/Quiver-Quantitative):** While mostly known for their API, their GitHub shares open-source scripts tracking corporate lobbying, Wikipedia views, and Congress trades.
    
    ### 2. The "Ultimate" Open-Source Stack
    *   **[OpenBB Terminal](https://github.com/OpenBB-finance/OpenBBTerminal):** The absolute king of open-source finance. An entirely free alternative to the Bloomberg Terminal aggregating data from dozens of sources (crypto, macro, fundamentals) into one Python SDK.
    
    ### 3. Systematic Screeners
    *   **[Norn-StockScreener](https://github.com/zmcx16/Norn-StockScreener):** A robust screener that incorporates advanced fundamental flag modules to detect "earnings manipulation" or highlight pristine balance sheets.
    *   **[Insider-Trading-Analyzer](https://github.com/wescules/insider-trading-analyzer):** A specialized repository that scans SEC Form 4 filings to detect "cluster buys" by multiple executives, providing strong market timing signals.
    
    ### 4. The Master List
    *   **[Awesome Quant](https://github.com/wilsonfreitas/awesome-quant):** A continuously updated, master-curated list of hundreds of the best open-source libraries for algorithmic trading, backtesting, and data extraction. If you want to dive down the rabbit hole, start here.
    """)
