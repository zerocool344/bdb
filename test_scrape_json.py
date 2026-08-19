import requests
from bs4 import BeautifulSoup
import json

url = "https://www.capitoltrades.com/politicians/P000197"
headers = {'User-Agent': 'Mozilla/5.0'}

try:
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    next_data = soup.find("script", id="__NEXT_DATA__")
    if next_data:
        data = json.loads(next_data.text)
        # Dig into the props to find trades
        trades = data.get('props', {}).get('pageProps', {}).get('initialState', {}).get('trades', {}).get('data', [])
        print(f"Found {len(trades)} trades in JSON.")
        if trades:
            first = trades[0]
            print(json.dumps(first, indent=2))
except Exception as e:
    print("Error:", e)
