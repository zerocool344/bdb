import requests

# Test 1: Full User-Agent
url1 = "https://www.capitoltrades.com/politicians/P000197"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
try:
    r1 = requests.get(url1, headers=headers)
    print("CapitolTrades Status:", r1.status_code)
except Exception as e:
    print("Error 1:", e)

# Test 2: HouseStockWatcher API
url2 = "https://housestockwatcher.com/api"
try:
    r2 = requests.get(url2)
    print("HouseStockWatcher Status:", r2.status_code)
except Exception as e:
    print("Error 2:", e)
