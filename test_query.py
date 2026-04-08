import requests

res = requests.get("http://localhost:8000/rankings")
print("RANKINGS API RESPONSE", res.json())

res2 = requests.get("http://localhost:8000/search-suggestions")
print("SEARCH SUGGESTIONS RESPONSE", res2.json())
