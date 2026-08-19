import requests
import json

url = "https://bff.capitoltrades.com/trades?politician=P000197&pageSize=10"
headers = {'User-Agent': 'Mozilla/5.0'}
try:
    response = requests.get(url, headers=headers)
    print("Status:", response.status_code)
    if response.status_code == 200:
        data = response.json()
        print("Got trades:", len(data.get('data', [])))
        if data.get('data'):
            first = data['data'][0]
            print(json.dumps(first, indent=2))
except Exception as e:
    print("Error:", e)
