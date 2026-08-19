import requests
import json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://capitol.crnicholson.com/api/trades?person=Pelosi"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Accept': 'application/json'
}
try:
    response = requests.get(url, headers=headers, timeout=10, verify=False)
    print("Status Code:", response.status_code)
    if response.status_code == 200:
        data = response.json()
        print("Number of trades returned:", len(data))
        if data:
            print("First trade JSON:", json.dumps(data[0], indent=2))
except Exception as e:
    print("Error:", e)
