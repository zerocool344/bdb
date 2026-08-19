import requests
from bs4 import BeautifulSoup
import json

url = "https://www.capitoltrades.com/politicians/P000197"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

try:
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    next_data = soup.find("script", id="__NEXT_DATA__")
    if next_data:
        data = json.loads(next_data.string)
        # In CapitolTrades, trades are usually in props.pageProps.initialState.trades.data
        try:
            trades = data['props']['pageProps']['initialState']['trades']['data']
            print(f"Found {len(trades)} trades via __NEXT_DATA__")
            if trades:
                print("Sample Trade:")
                t = trades[0]
                print(f"Ticker: {t.get('issuer', {}).get('ticker')}")
                print(f"Type: {t.get('txType')}")
                print(f"Traded: {t.get('txDate')}")
                print(f"Size: {t.get('size')}")
        except KeyError as e:
            print("KeyError navigating JSON:", e)
    else:
        print("No __NEXT_DATA__ found.")
except Exception as e:
    print("Request failed:", e)
