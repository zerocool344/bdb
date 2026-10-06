import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import yfinance as yf
import time
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from bs4 import BeautifulSoup

# ── Resilient Yahoo fetch layer ──────────────────────────────────────────────
# Yahoo's quoteSummary / quote endpoints now return 401 without a crumb, and
# yfinance 1.7.0's crumb handshake is broken (KeyError 'A3'). The v8 chart
# endpoint still serves price + metadata without auth, so we use it directly.
_YF_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def _yf_chart(ticker_sym, range_="5d", interval="1d"):
    """Raw v8 chart result for a ticker; raises on any failure."""
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker_sym}"
        f"?range={range_}&interval={interval}"
    )
    resp = requests.get(url, headers=_YF_HEADERS, timeout=20)
    resp.raise_for_status()
    payload = resp.json()
    result = (payload.get("chart") or {}).get("result") or []
    if not result:
        err = ((payload.get("chart") or {}).get("error") or {}).get("description", "no data")
        raise ValueError(f"{ticker_sym}: {err}")
    return result[0]


def _chart_to_history(result):
    """Convert a v8 chart result to a yfinance-style OHLCV DataFrame."""
    ts = result.get("timestamp") or []
    quote = (result.get("indicators", {}).get("quote") or [{}])[0]
    adj = (result.get("indicators", {}).get("adjclose") or [{}])[0].get("adjclose")
    df = pd.DataFrame(
        {
            "Open": quote.get("open"),
            "High": quote.get("high"),
            "Low": quote.get("low"),
            "Close": quote.get("close"),
            "Volume": quote.get("volume"),
        },
        index=pd.to_datetime(ts, unit="s", utc=True).tz_convert("America/New_York").tz_localize(None)
        if ts
        else None,
    )
    df["Adj Close"] = adj if adj else df["Close"]
    return df.dropna(subset=["Close"])


def get_quote_snapshot(ticker_sym):
    """Live price + name from the auth-free chart endpoint. Raises on failure."""
    meta = _yf_chart(ticker_sym, range_="5d", interval="1d").get("meta", {})
    price = meta.get("regularMarketPrice")
    if price is None:
        raise ValueError(f"{ticker_sym}: no market price in response")
    return {
        "price": price,
        "name": meta.get("shortName") or meta.get("longName") or ticker_sym,
        "currency": meta.get("currency", "USD"),
        "previous_close": meta.get("chartPreviousClose"),
    }


def get_fundamentals(ticker_sym):
    """Analyst target / consensus / valuation via yfinance; {} when Yahoo 401s."""
    try:
        info = yf.Ticker(ticker_sym).info or {}
        return info if isinstance(info, dict) else {}
    except Exception:
        return {}


@st.cache_data(ttl=3600, show_spinner=False)
def get_price_history(ticker_sym, range_="1y"):
    """1y OHLCV history for factor computation; empty DataFrame on failure."""
    try:
        hist = _chart_to_history(_yf_chart(ticker_sym, range_=range_, interval="1d"))
        return hist
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=86400, show_spinner=False)
def get_sp500_universe():
    """S&P 500 tickers from Wikipedia (Yahoo needs '-' instead of '.')."""
    from io import StringIO
    try:
        html = requests.get(
            "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
            headers=_YF_HEADERS, timeout=20).text
        df = pd.read_html(StringIO(html))[0]
        col = "Symbol" if "Symbol" in df.columns else df.columns[0]
        return sorted({str(s).strip().replace(".", "-") for s in df[col] if str(s).strip()})
    except Exception:
        return []


def _finnhub(ticker_sym, endpoint, api_key):
    url = f"https://finnhub.io/api/v1{endpoint}?symbol={ticker_sym}&token={api_key}"
    resp = requests.get(url, headers=_YF_HEADERS, timeout=15)
    if resp.status_code != 200:
        return {}
    return resp.json()


def get_finnhub_fundamentals(ticker_sym, api_key):
    """Analyst target, consensus, P/E, ROE from Finnhub free tier; {} without a key."""
    if not api_key:
        return {}
    try:
        target = _finnhub(ticker_sym, "/stock/price-target", api_key)
        recs = _finnhub(ticker_sym, "/stock/recommendation", api_key)
        metric = _finnhub(ticker_sym, "/stock/metric", api_key).get("metric", {})
        rec0 = (recs[0] if isinstance(recs, list) and recs else {})
        return {
            "targetMeanPrice": target.get("targetMean"),
            "trailingPE": metric.get("peTTM") or metric.get("peNormalizedAnnual"),
            "roeTTM": metric.get("roeTTM") or metric.get("roeRfy"),
            "recommendationKey": _consensus_from_recs(rec0),
        }
    except Exception:
        return {}


def _consensus_from_recs(rec0):
    if not rec0:
        return "N/A"
    buy = rec0.get("buy", 0) + rec0.get("strongBuy", 0)
    sell = rec0.get("sell", 0) + rec0.get("strongSell", 0)
    if buy > sell and buy >= rec0.get("hold", 0):
        return "Buy"
    if sell > buy:
        return "Sell"
    return "Hold"

# TauricResearch/TradingAgents multi-agent financial framework integration
from tradingagents import TradingAgentsGraph, DEFAULT_CONFIG
from tradingagents.ui import render_tradingagents_desk, create_radar_chart

st.set_page_config(page_title="The Tendie Tracker", layout="wide", page_icon="logo.png")

# Auto-refresh the page every 10 minutes (600,000 ms)
st_autorefresh(interval=600_000, key="data_autorefresh")

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
    .stButton > button { 
        border: 1px solid #CBD5E1; 
        background: linear-gradient(180deg, #FFFFFF 0%, #F1F5F9 100%); 
        color: #334155; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.1);
        font-weight: 500;
        transition: all 0.2s ease;
    }
    .stButton > button:hover { 
        border-color: #94A3B8; 
        background: #FFFFFF; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.08);
        color: #0F172A; 
        transform: translateY(-1px);
    }
    
    /* Container borders */
    [data-testid="stContainer"] { border-color: #E2E8F0 !important; }
    
    /* Input fields */
    .stTextInput input { background: #FFFFFF; border: 1px solid #CBD5E1; color: #1E293B; }
    .stSelectbox > div > div { background: #FFFFFF; }
    
    /* ── Dot-Matrix LED Board + Climbing Kitty ── */
    .sign-wrapper-1 { position: relative; display: inline-flex; align-items: center; }
    .cat-climber-1 {
        position: absolute; top: -16px; right: 12px; font-size: 16px;
        animation: kittyClimbSign1 3s infinite ease-in-out;
    }
    @keyframes kittyClimbSign1 {
        0%, 100% { transform: translateY(8px); opacity: 0.3; }
        50% { transform: translateY(-3px) rotate(6deg); opacity: 1; }
    }
    .neon-sign-1 {
        font-family: 'Courier New', monospace; font-size: 15px; font-weight: 600; letter-spacing: 2px;
        color: #00ff66; background: #08140c; border: 1px solid #00ff66; border-radius: 6px;
        padding: 5px 12px; box-shadow: 0 0 8px rgba(0,255,102,0.3), inset 0 0 6px rgba(0,255,102,0.2);
        display: inline-flex; align-items: center; gap: 6px;
    }
    .led-dot { width: 7px; height: 7px; background-color: #00ff66; border-radius: 50%; box-shadow: 0 0 6px #00ff66; animation: blinkDot 1.2s infinite; }
    @keyframes blinkDot { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
</style>
""", unsafe_allow_html=True)

# Master Watchlist
WATCHLIST = [
    "GOOGL", "CVS", "AMZN", "MSFT", "JPM", 
    "SNOW", "CRM", "NKE", "DIS", "BA", 
    "STX", "LNG", "U", "AAPL", "NVDA", "META"
]

col_logo, col_title, col_actions = st.columns([1, 6, 5])
with col_logo:
    st.image("logo.png", use_container_width=True)

with col_title:
    st.title("The Tendie Tracker")
    st.markdown("Automated equity screening for apes hunting deep effin' value. (Not financial advice—we just like the stock. 🐱📈)")

with col_actions:
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    ac1, ac2 = st.columns([1.3, 1])
    with ac1:
        st.markdown("""
            <div style="display: flex; justify-content: flex-end; align-items: center; height: 38px;">
                <div class="sign-wrapper-1">
                    <div class="cat-climber-1">🐱</div>
                    <div class="neon-sign-1">
                        <span class="led-dot"></span> WE LIKE THE STOCK!
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    with ac2:
        if st.button("🔄 Refresh Live Data", help="Refresh all live market data", use_container_width=True):
            from datetime import datetime
            try:
                from zoneinfo import ZoneInfo
                central_tz = ZoneInfo("America/Chicago")
            except Exception:
                from datetime import timezone, timedelta
                central_tz = timezone(timedelta(hours=-5))
            st.session_state["last_refreshed"] = datetime.now(central_tz).strftime("%b %d, %Y • %I:%M %p %Z")
            st.cache_data.clear()
            st.rerun()


# ── Composite factor scoring engine ─────────────────────────────────────────
# Ranks a universe cross-sectionally on Value / Quality / Momentum / Low-Vol.
# Price-derived factors (momentum, volatility, trend) always work off the
# auth-free chart API. Value & Quality come from Finnhub when a key is given.


def _pct_rank(series):
    """Percentile rank in [0,1]; NaN stays NaN so a missing factor is renormalized out."""
    return series.rank(pct=True)


def _compute_price_factors(hist):
    """Momentum / volatility / trend from an OHLCV history DataFrame."""
    close = hist["Close"].astype(float).dropna()
    n = len(close)
    if n < 30:
        return None
    last = float(close.iloc[-1])

    def ago(days):
        return float(close.iloc[-1 - days]) if n > days else float(close.iloc[0])

    # Classic 6-1 & 12-1 momentum: skip the most recent (mean-reverting) month.
    px_1m, px_6m, px_12m = ago(21), ago(126), ago(252)
    mom_6_1 = (px_1m - px_6m) / px_6m if px_6m else None
    mom_12_1 = (px_1m - px_12m) / px_12m if px_12m else None

    rets = close.pct_change().dropna()
    vol = float(rets.tail(126).std() * (252 ** 0.5)) if len(rets) > 10 else None
    sma200 = float(close.tail(min(200, n)).mean())
    above_200 = 1.0 if last >= sma200 else 0.0

    out = {"price": last, "mom_6_1": mom_6_1, "mom_12_1": mom_12_1,
           "volatility": vol, "above_200d": above_200}
    return out if (mom_6_1 is not None or mom_12_1 is not None) else None


def build_composite_scores(rows, has_fundamentals):
    """rows: list of per-ticker dicts. Returns a ranked DataFrame."""
    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df["momentum_raw"] = df[["mom_6_1", "mom_12_1"]].mean(axis=1, skipna=True)
    df["Momentum"] = _pct_rank(df["momentum_raw"]) * 100
    df["LowVol"] = (1 - _pct_rank(df["volatility"])) * 100
    df["Trend"] = df["above_200d"] * 100

    if has_fundamentals and "value_raw" in df and df["value_raw"].notna().any():
        df["Value"] = _pct_rank(df["value_raw"]) * 100
        df["Quality"] = _pct_rank(df["quality_raw"]) * 100
        # Value 30 / Quality 30 / Momentum 25 / Low-Vol 10 / Trend 5
        weights = {"Value": 0.30, "Quality": 0.30, "Momentum": 0.25, "LowVol": 0.10, "Trend": 0.05}
    else:
        df["Value"] = pd.NA
        df["Quality"] = pd.NA
        # No fundamentals: momentum 55 / low-vol 30 / trend 15
        weights = {"Momentum": 0.55, "LowVol": 0.30, "Trend": 0.15}

    def combine(r):
        acc, wsum = 0.0, 0.0
        for k, w in weights.items():
            v = r[k]
            if pd.notna(v):
                acc += v * w
                wsum += w
        if not wsum:
            return None
        score = acc / wsum  # renormalize over present factors
        # Trend gate: don't let momentum chase names below their 200-day line.
        if r.get("above_200d") == 0.0:
            score *= 0.85
        return round(score, 1)

    df["Composite"] = df.apply(combine, axis=1)
    df["Rank"] = df["Composite"].rank(ascending=False, method="min").astype("Int64")

    n = len(df)
    top, next_ = max(1, round(n * 0.10)), max(2, round(n * 0.30))

    def tier(rk):
        if pd.isna(rk):
            return "WATCH"
        if rk <= top:
            return "STRONG (Top 10%)"
        if rk <= next_:
            return "NEAR (Top 30%)"
        return "WATCH"

    df["List"] = df["Rank"].apply(tier)
    return df.sort_values("Composite", ascending=False).reset_index(drop=True)


@st.cache_data(ttl=595, show_spinner=False)
def run_composite_screener(universe, finnhub_key=""):
    """Score & rank a universe. Returns (ranked_df, fetched_at_str, fundamentals_on)."""
    rows = []
    for ticker_sym in universe:
        try:
            snap = get_quote_snapshot(ticker_sym)
            hist = get_price_history(ticker_sym, "1y")
            if hist.empty:
                continue
            pf = _compute_price_factors(hist)
            if not pf:
                continue
            row = {"Ticker": ticker_sym, "Name": snap["name"], **pf}

            fund = get_finnhub_fundamentals(ticker_sym, finnhub_key)
            pe = fund.get("trailingPE")
            row["value_raw"] = (1.0 / pe) if (isinstance(pe, (int, float)) and pe > 0) else None
            roe = fund.get("roeTTM")
            row["quality_raw"] = roe if isinstance(roe, (int, float)) else None
            row["Target"] = fund.get("targetMeanPrice")
            row["Consensus"] = fund.get("recommendationKey", "N/A")
            rows.append(row)
        except Exception:
            continue

    has_fund = bool(finnhub_key) and any(r.get("value_raw") is not None for r in rows)
    ranked = build_composite_scores(rows, has_fund)

    from datetime import datetime as _dt
    try:
        from zoneinfo import ZoneInfo
        _tz = ZoneInfo("America/Chicago")
    except Exception:
        from datetime import timezone, timedelta
        _tz = timezone(timedelta(hours=-5))
    return ranked, _dt.now(_tz).strftime("%b %d, %Y • %I:%M %p %Z"), has_fund


@st.cache_data(ttl=595, show_spinner=False)
def run_screener(watchlist):
    results = []

    for i, ticker_sym in enumerate(watchlist):
        try:
            # Live price + name from the auth-free chart endpoint (always works).
            snap = get_quote_snapshot(ticker_sym)
            name = snap["name"]
            current_price = snap["price"]

            # Fundamentals: analyst target / consensus / valuation. Yahoo's
            # quoteSummary is currently 401-gated, so this may come back empty.
            info = get_fundamentals(ticker_sym)
            target_price = info.get("targetMeanPrice")
            rec_key = info.get("recommendationKey", "N/A")
            
            # Format recommendation string
            consensus = rec_key.replace("_", " ").title() if rec_key != "none" else "N/A"
            
            # Calculate Upside
            upside = None
            if current_price and target_price and current_price > 0:
                upside = round(((target_price - current_price) / current_price) * 100, 2)
            
            # Calculate True P/E (Enterprise Value / Earnings)
            ev = info.get("enterpriseValue")
            net_income = info.get("netIncomeToCommon")
            market_cap = info.get("marketCap")
            trailing_pe = info.get("trailingPE")
            
            true_pe = None
            if isinstance(ev, (int, float)) and ev > 0:
                if isinstance(net_income, (int, float)) and net_income > 0:
                    true_pe = round(ev / net_income, 2)
                elif isinstance(market_cap, (int, float)) and isinstance(trailing_pe, (int, float)) and trailing_pe > 0:
                    # Implied earnings from market cap and trailing PE
                    implied_earnings = market_cap / trailing_pe
                    if implied_earnings > 0:
                        true_pe = round(ev / implied_earnings, 2)

            # Determine List Placement (NEAR vs FAR vs NEUTRAL)
            # FAR = High upside (e.g. > 25%), NEAR = Moderate upside (e.g. 10-25%)
            # This is a dynamic rule set based on upside. When analyst targets
            # are unavailable (Yahoo 401), classify on live price action instead.
            list_placement = "NEUTRAL"
            if upside is not None:
                if upside > 25.0:
                    list_placement = "FAR (Deep Value)"
                elif upside >= 10.0:
                    list_placement = "NEAR (Growth/Value)"
                else:
                    list_placement = "WATCH (Low Upside)"
            else:
                prev_close = snap.get("previous_close")
                if prev_close and current_price and prev_close > 0:
                    day_move = ((current_price - prev_close) / prev_close) * 100
                    list_placement = "WATCH (Low Upside)" if day_move >= 0 else "NEAR (Growth/Value)"
                    
            results.append({
                "Ticker": ticker_sym,
                "Name": name,
                "List": list_placement,
                "Current Price": f"${current_price}" if current_price else "N/A",
                "Target Price": f"${target_price}" if target_price else "N/A",
                "Consensus": consensus,
                "Upside %": upside if upside is not None else 0.0,
                "True P/E": true_pe if true_pe is not None else "N/A",
                "Thesis": (
                    f"Dynamic rating: {consensus}. Target: {target_price}"
                    if target_price
                    else "Live price from Yahoo. Analyst targets temporarily unavailable."
                ),
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
                "True P/E": "N/A",
                "Thesis": "Error fetching data.",
                "Risk": str(e)
            })
            
        # Update progress
        time.sleep(0.1) # Small delay to respect rate limits
        
    out = pd.DataFrame(results)
    try:
        from zoneinfo import ZoneInfo
        _tz = ZoneInfo("America/Chicago")
    except Exception:
        from datetime import timezone, timedelta
        _tz = timezone(timedelta(hours=-5))
    from datetime import datetime as _dt
    out.attrs["fetched_at"] = _dt.now(_tz).strftime("%b %d, %Y • %I:%M %p %Z")
    return out

@st.cache_data(ttl=3600, show_spinner=False)
def _load_chart_data(ticker_sym, period="1y"):
    result = _yf_chart(ticker_sym, range_=period, interval="1d")
    hist = _chart_to_history(result)
    if hist.empty:
        # Raise so the empty result is NOT cached.
        raise ValueError(f"No price history returned for {ticker_sym}")
    return hist

def get_chart_data(ticker_sym, period="1y"):
    try:
        return _load_chart_data(ticker_sym, period)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner=False)
def get_insider_data(ticker_sym):
    result = {"insider": pd.DataFrame()}
    try:
        stock = yf.Ticker(ticker_sym)
        # Fetch Insider Transactions (best-effort; Yahoo quoteSummary is 401-gated)
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

@st.cache_data(ttl=21600, show_spinner=False)
def _load_pelosi_trades():
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
    except Exception:
        # Re-raise so st.cache_data does NOT cache the failure; the wrapper below handles it.
        raise

def get_pelosi_trades():
    try:
        return _load_pelosi_trades()
    except Exception:
        return pd.DataFrame()

# Run the screener (will use cache unless refreshed)
with st.spinner("Running Live Market Screener..."):
    df = run_screener(WATCHLIST)

# If any ticker failed to fetch, don't keep the failed result in cache -
# evict it so the next rerun (auto-refresh or interaction) retries.
_failed_tickers = df.loc[df["List"] == "ERROR"].shape[0]
if _failed_tickers:
    run_screener.clear()
    st.warning(f"⚠️ Could not fetch live data for {_failed_tickers} of {len(df)} tickers (Yahoo Finance may be rate-limiting). Will retry on the next refresh.")

# Enrich the overview with multi-factor composite scores (shares the 🎯 Screener's
# cache, so the "My Watchlist" scan is computed at most once per cache window).
_fetched_at = df.attrs.get("fetched_at")
try:
    _comp_df, _, _ = run_composite_screener(
        tuple(WATCHLIST),
        (st.session_state.get("finnhub_key_input") or "").strip())
    if not _comp_df.empty and "Ticker" in _comp_df.columns:
        df = df.merge(
            _comp_df[["Ticker", "Composite", "Rank", "Momentum", "LowVol", "Trend"]],
            on="Ticker", how="left")
except Exception:
    pass
if _fetched_at:
    df.attrs["fetched_at"] = _fetched_at

_sort_col = "Composite" if "Composite" in df.columns else "Upside %"

# Track last refresh timestamp in US Central Time
from datetime import datetime
try:
    from zoneinfo import ZoneInfo
    central_tz = ZoneInfo("America/Chicago")
except Exception:
    from datetime import timezone, timedelta
    central_tz = timezone(timedelta(hours=-5))

# Show when the data was actually fetched (not when the session started)
st.session_state["last_refreshed"] = df.attrs.get(
    "fetched_at", datetime.now(central_tz).strftime("%b %d, %Y • %I:%M %p %Z")
)

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
tab1, tab_screen, tab_tradingagents, tab4, tab5, tab6 = st.tabs([
    "📊 Overview",
    "🎯 Screener",
    "🧬 AI Desk",
    "🇺🇸 Pelosi",
    "📈 ETFs",
    "📚 Resources"
])

with tab1:
    main_col, side_col = st.columns([2.5, 1.5])
    with main_col:
            if "Composite" in df.columns:
                st.caption("Sorted by **Composite** — a 0–100 multi-factor score (momentum, trend, low-vol; plus Value & Quality when a Finnhub key is added on the 🎯 Screener tab). See the 🎯 Screener for the full ranked model.")
            st.subheader("NEAR | 1–2 Year Consensus (10% - 25% Upside)")
            near_df = df[df['List'] == 'NEAR (Growth/Value)'].drop(columns=['List']).sort_values(_sort_col, ascending=False).reset_index(drop=True)
            st.dataframe(near_df, use_container_width=True)
        
            st.subheader("FAR | 2–5 Year Deep Value (>25% Upside)")
            far_df = df[df['List'] == 'FAR (Deep Value)'].drop(columns=['List']).sort_values(_sort_col, ascending=False).reset_index(drop=True)
            st.dataframe(far_df, use_container_width=True)
            
            st.subheader("WATCH | Low Upside / Overvalued (<10% Upside)")
            watch_df = df[df['List'] == 'WATCH (Low Upside)'].drop(columns=['List']).sort_values(_sort_col, ascending=False).reset_index(drop=True)
            st.dataframe(watch_df, use_container_width=True)
            
            error_df = df[df['List'] == 'ERROR'].drop(columns=['List']).reset_index(drop=True)
            if not error_df.empty:
                st.error("⚠️ The following assets failed to pull live data (Rate limited or invalid ticker):")
                st.dataframe(error_df, use_container_width=True)
        

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
                        if 'Composite' in row.index and pd.notna(row['Composite']):
                            st.markdown(f"**Composite Score:** {row['Composite']:.0f} / 100  •  **Rank:** {row['Rank']}")
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
                            st.info(f"✅ Queued **{ticker}**! Switch to the '🧬 AI Desk' tab to view the AI Committee deliberation.")

with tab_screen:
    st.subheader("🎯 Multi-Factor Stock Screener")
    st.markdown(
        "Ranks the universe on a **composite of Value, Quality, Momentum, Trend & Low-Volatility** "
        "instead of a single analyst-target signal. Cross-sectional percentile ranks adapt to market conditions."
    )

    ctrl1, ctrl2, ctrl3 = st.columns([1.4, 1, 1.6])
    with ctrl1:
        universe_choice = st.radio(
            "Universe",
            ["My Watchlist", "S&P 500"],
            horizontal=True,
            help="S&P 500 fetches ~500 tickers; first run takes a few minutes then caches."
        )
    with ctrl2:
        top_n = st.slider("Show top N", 10, 100, 25, 5)
    with ctrl3:
        finnhub_key = st.text_input(
            "Finnhub API Key (optional — unlocks Value & Quality factors)",
            type="password",
            key="finnhub_key_input",
            help="Free key at finnhub.io. Without it the screener ranks on price momentum / trend / low-vol only."
        )

    universe = WATCHLIST if universe_choice == "My Watchlist" else get_sp500_universe()
    if not universe:
        st.error("Could not load the S&P 500 universe. Check connectivity.")
    else:
        if "composite_cache" not in st.session_state:
            st.session_state["composite_cache"] = {}

        run_scan = st.button("🚀 Run Factor Scan", type="primary", use_container_width=True)
        if run_scan:
            with st.spinner(f"Scoring {len(universe)} tickers across factors..."):
                _ranked, _fetched, _has_fund = run_composite_screener(tuple(universe), finnhub_key.strip())
                st.session_state["composite_cache"] = {
                    "ranked": _ranked, "fetched": _fetched,
                    "has_fund": _has_fund, "universe": universe_choice,
                }

        cache = st.session_state["composite_cache"]
        if not cache:
            st.info("👆 Click **Run Factor Scan** to rank the universe.")
        else:
            ranked, has_fund = cache["ranked"], cache["has_fund"]
            st.caption(
                f"Scored {len(ranked)} tickers • {cache['universe']} • refreshed {cache['fetched']} • "
                + ("Value & Quality factors: **on** (Finnhub)" if has_fund else "Value & Quality factors: **off** — add a Finnhub key"))
            if ranked.empty:
                st.warning("No tickers returned enough data to score.")
            else:
                show = ranked.head(top_n)
                disp_cols = ["Rank", "Ticker", "Name", "price", "Composite", "Momentum", "LowVol", "Trend"]
                if has_fund:
                    disp_cols += ["Value", "Quality"]
                disp = show.reindex(columns=[c for c in disp_cols if c in show.columns]).copy()
                disp = disp.rename(columns={"price": "Price", "mom_6_1": "6-1 Mo Mom", "mom_12_1": "12-1 Mo Mom"})
                if "Price" in disp:
                    disp["Price"] = disp["Price"].map(lambda v: f"${v:,.2f}" if pd.notna(v) else "N/A")
                for c in ["Composite", "Momentum", "LowVol", "Trend", "Value", "Quality"]:
                    if c in disp:
                        disp[c] = disp[c].map(lambda v: round(float(v), 1) if pd.notna(v) else "—")
                st.dataframe(disp, use_container_width=True, hide_index=True)

                with st.expander("📋 Full ranked list"):
                    st.dataframe(ranked, use_container_width=True, hide_index=True)

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
                hist = get_chart_data(t, period=fetch_period)
                if not hist.empty:
                    # Normalize to percentage return
                    first_close = hist['Close'].iloc[0]
                    hist = hist.copy()
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
