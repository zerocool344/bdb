import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}
url = "https://www.capitoltrades.com/politicians/P000197"
try:
    response = requests.get(url, headers=headers)
    print("CapitolTrades Status:", response.status_code)
    if response.status_code == 200:
        print("Length:", len(response.text))
        print("Is blocked?", "cloudflare" in response.text.lower())
except Exception as e:
    print("Error:", e)
