import requests
from bs4 import BeautifulSoup
import pandas as pd

url = "https://www.capitoltrades.com/politicians/P000197"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

try:
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    trades = []
    # Find all table rows
    rows = soup.find_all('tr')
    for row in rows:
        ticker_span = row.find('span', class_='issuer-ticker')
        if not ticker_span: continue
        
        ticker = ticker_span.text.split(':')[0] # e.g. NVDA:US -> NVDA
        
        type_span = row.find('span', class_='tx-type')
        tx_type = type_span.text.strip().title() if type_span else "Unknown"
        
        # There are multiple dates (traded, reported). First one is usually traded.
        dates = row.find_all('div', class_='text-size-3 font-medium')
        traded_date = dates[0].text.strip() if len(dates) > 0 else "Unknown"
        
        size_span = row.find('span', class_='mt-1 text-size-2 text-txt-dimmer hover:text-foreground')
        size = size_span.text.strip() if size_span else "Unknown"
        
        # Clean up encoding artifacts in size (e.g. '250K\ufffd500K' -> '250K-500K')
        size = size.replace('', '-')
        
        trades.append({
            "Ticker": ticker,
            "Type": tx_type,
            "Date Traded": traded_date,
            "Size": size
        })
        
    df = pd.DataFrame(trades)
    print(df.head(10))
except Exception as e:
    print("Error:", e)
