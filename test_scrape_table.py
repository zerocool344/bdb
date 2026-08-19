import pandas as pd
import requests
from bs4 import BeautifulSoup

url = "https://www.capitoltrades.com/politicians/P000197"
headers = {'User-Agent': 'Mozilla/5.0'}

try:
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Try finding tables
    tables = soup.find_all('table')
    print("Found tables:", len(tables))
    if len(tables) > 0:
        df = pd.read_html(str(tables[0]))[0]
        print(df.head())
        df.to_csv("pelosi_trades.csv", index=False)
    else:
        # Capitol Trades might use div-based rows or Next.js JSON state
        print("No table found. Checking for __NEXT_DATA__")
        next_data = soup.find("script", id="__NEXT_DATA__")
        if next_data:
            print("Found Next.js JSON blob. Length:", len(next_data.text))
except Exception as e:
    print("Error:", e)
