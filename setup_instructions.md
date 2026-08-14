# Daily Consensus Desk (Live Screener)

An autonomous equity research screening dashboard built for Streamlit Community Cloud. This dashboard operates entirely on free, open-source APIs without requiring any credentials or API keys.

## Features & Architecture

1. **Live Market Screener**
   - **Source:** Yahoo Finance API (`yfinance`)
   - **Functionality:** Queries a hardcoded watchlist to dynamically generate target price upside and sort tickers into `FAR (Deep Value)` (>25% upside), `NEAR (Growth)` (10-25% upside), and `WATCH` (<10% upside) lists.
   
2. **Interactive Stock Insights**
   - **Functionality:** A search bar providing interactive Plotly Candlestick charts overlaid with dynamic volume indicators. Modeled after E*TRADE's charting interfaces.
   
3. **Nancy Pelosi Trade Tracker**
   - **Source:** [CongressKit](https://github.com/kovagent/congresskit) (Raw Parquet Data via GitHub)
   - **Functionality:** Directly queries the `congress-2026.parquet` dataset hosted on GitHub using `pandas.read_parquet`. 
   - **WAF Avoidance Strategy:** We fetch raw files directly from GitHub's CDN to bypass aggressive Cloudflare web-application firewalls (WAFs) that typically block traditional HTML scraping (like `requests` + `BeautifulSoup`) on Streamlit Cloud datacenter IPs.
   
4. **ETF Performance Tracking**
   - **Source:** Yahoo Finance API (`yfinance`)
   - **Functionality:** Normalizes 1-Year historical data for NANC, SPY, and QQQ into percentage returns for easy side-by-side performance comparison on a multi-line Plotly chart.

## Setup Instructions

### Prerequisites
- Python 3.10+
- `pip` package manager

### Local Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/zerocool344/bdb.git
   cd bdb
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *Required packages include: `streamlit`, `pandas`, `yfinance`, `plotly`, `pyarrow` (required for parsing Parquet files), and `requests`.*

3. Run the application:
   ```bash
   streamlit run app.py
   ```

### Cloud Deployment
This app is designed to be hosted on **Streamlit Community Cloud**. 
1. Link the repository to your Streamlit Community Cloud account.
2. Select `app.py` as the Main file path.
3. Deploy! Streamlit will automatically install dependencies via `requirements.txt` and launch the application.

## Modifying the Watchlist
To change the stocks tracked in the Live Screener, open `app.py` and modify the `WATCHLIST` array near the top of the file:
```python
WATCHLIST = [
    "GOOGL", "CVS", "AMZN", "MSFT", "JPM", ...
]
```
