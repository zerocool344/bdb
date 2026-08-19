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

# Master Watchlist
WATCHLIST = [
    "GOOGL", "CVS", "AMZN", "MSFT", "JPM", 
    "SNOW", "CRM", "NKE", "DIS", "BA", 
    "STX", "LNG", "U", "AAPL", "NVDA", "META"
]


col_logo, col_title = st.columns([1, 10])
with col_logo:
    st.image("logo.png", use_container_width=True)
with col_title:
    st.title("The Tendie Tracker")
    st.markdown("Automated equity screening for apes hunting deep effin' value. (Not financial advice—we just like the stock. 🐱📈)")

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
tab1, tab_tradingagents, tab3, tab4, tab5, tab6 = st.tabs([
    "Live Overview (Consensus)",
    "🤖 TradingAgents Desk",
    "🧬 Deep Insights",
    "🇺🇸 Pelosi Tracker",
    "📈 ETF Benchmarks",
    "📚 Master Lists"
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
            
            # Filter based on search query and take only the top match
            if not search_query.strip():
                filtered_df = pd.DataFrame()
            else:
                filtered_df = df[
                    df['Ticker'].str.contains(search_query, case=False) | 
                    df['Name'].str.contains(search_query, case=False)
                ].head(1)
        
            if not search_query.strip():
                st.info("Enter a ticker or company name above to view details.")
            elif filtered_df.empty:
                st.info("No stocks matched your search.")
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
                                
                                fig.add_trace(go.Candlestick(x=chart_data.index,
                                                open=chart_data['Open'],
                                                high=chart_data['High'],
                                                low=chart_data['Low'],
                                                close=chart_data['Close'],
                                                name="Price"), row=1, col=1)
                                
                                colors = ['#26a69a' if close >= open_p else '#ef5350' for open_p, close in zip(chart_data['Open'], chart_data['Close'])]
                                fig.add_trace(go.Bar(x=chart_data.index, y=chart_data['Volume'], marker_color=colors, name="Volume"), row=2, col=1)
                                
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

with tab3:
    st.subheader("🧬 Deep Insights & Alternative Data")
    insight_query = st.text_input("Enter Ticker for Deep Dive (e.g. AAPL, MSFT)", "AAPL")
    
    if insight_query:
        ticker = insight_query.upper()
        # Fetch deeper insights (Insider only now)
        with st.spinner(f"Pulling deep insights for {ticker}..."):
            extra_data = get_insider_data(ticker)
            
            # Deep Dive Sections
            try:
                f_info = yf.Ticker(ticker).info
                score, flags = calculate_fundamental_score(f_info)
                
                f1, f2, f3 = st.columns([1, 1.5, 1])
                with f1:
                    st.markdown("**Fundamentals (Norn-Style)**")
                    st.write(f"**Health Score:** {score}/3")
                    for f in flags:
                        st.write(f)
                        
                with f2:
                    st.markdown("**SEC Insider Trading**")
                    if not extra_data["insider"].empty:
                        # Cleanup columns if they exist
                        idf = extra_data["insider"].copy()
                        cols = [c for c in ['Start Date', 'Insider', 'Position', 'Transaction', 'Value'] if c in idf.columns]
                        if cols:
                            st.dataframe(idf[cols].head(5), hide_index=True, use_container_width=True)
                        else:
                            st.dataframe(idf.head(5), hide_index=True, use_container_width=True)
                    else:
                        st.info("No recent insider transactions filed.")
                        
                with f3:
                    st.markdown("**Alternative Data Links**")
                    st.markdown(f"Use the following open-source platforms to dive deeper into {ticker}'s alternative data points:")
                    st.link_button(f"🔎 View {ticker} on Stocksera (Retail Sentiment)", f"https://stocksera.pythonanywhere.com/ticker/?quote={ticker}", use_container_width=True)
                    st.link_button(f"🌍 View {ticker} on OpenBB (Macro & Terminals)", "https://openbb.co/", use_container_width=True)
                    
            except Exception as e:
                st.error("Error loading deep insights.")

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
                colors = {"NANC": "#1f77b4", "SPY": "#2ca02c", "QQQ": "#ff7f0e", "VOO": "#d62728"}
                
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
