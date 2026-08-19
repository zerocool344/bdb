import requests
import json

url = "https://api.github.com/repos/kovagent/congresskit/contents"
response = requests.get(url)
if response.status_code == 200:
    for item in response.json():
        print(item['name'], item['type'])
else:
    print(response.status_code, response.text)
