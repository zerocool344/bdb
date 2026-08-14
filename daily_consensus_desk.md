# Daily Consensus Desk - Methodology

This document outlines the methodology for the autonomous Daily Consensus Desk Streamlit application. The dashboard has been migrated from a static, manually updated markdown report to a dynamic live screener.

## Core Philosophy
The objective of this screener is to surface high-conviction, strong-buy candidates and categorize them based on their implied upside relative to analyst price targets.

## Data Sourcing
*   **Provider**: Data is fetched on-demand using the public Yahoo Finance API (`yfinance` library).
*   **Metrics Tracked**:
    *   Current Price
    *   Target Mean Price (Aggregated analyst consensus target)
    *   Recommendation Key (Buy, Strong Buy, Hold, etc.)
*   **Security**: The application operates without API keys or authentication, ensuring completely anonymous data scraping with zero risk to personal financial data.

## Classification Logic
The dashboard automatically classifies stocks into three primary lists based on the calculated upside percentage `((Target Price - Current Price) / Current Price) * 100`:

1.  **FAR (Deep Value)**: 
    *   *Threshold*: > 25% Implied Upside.
    *   *Profile*: Stocks that are typically undergoing a turnaround, have been heavily discounted from their highs, or present massive long-term (2-5 year) value opportunities.
2.  **NEAR (Growth/Value)**: 
    *   *Threshold*: 10% - 25% Implied Upside.
    *   *Profile*: Stable, near-term (1-2 year) consensus picks that offer strong, realistic growth trajectories without relying on massive turnaround bets.
3.  **WATCH (Low Upside)**:
    *   *Threshold*: < 10% Implied Upside.
    *   *Profile*: Stocks that are likely fully valued or overvalued according to current analyst price targets.

## Execution
To run the screener, launch the Streamlit application and click the **"Refresh Live Data"** button. The application will iterate through the configured `WATCHLIST` and dynamically generate the tables.
