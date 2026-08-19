import requests

url = "https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/data/all_transactions.json"
try:
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        print("Success, found records:", len(data))
        # Find pelosi
        pelosi = [d for d in data if "Pelosi" in d.get("representative", "")]
        print("Pelosi trades found:", len(pelosi))
        if pelosi:
            print("Latest:", pelosi[0])
    else:
        print("Failed with status:", response.status_code)
except Exception as e:
    print("Error:", e)
