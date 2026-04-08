import json
from fastapi import Request, Response
from fastapi.testclient import TestClient
from moviebox_api_server import app

client = TestClient(app)

print("--- Testing /rankings ---")
res = client.get("/rankings")
print("Status Code:", res.status_code)
print("Data:", json.dumps(res.json(), indent=2))

print("\n--- Testing /search-suggestions ---")
res2 = client.get("/search-suggestions")
print("Status Code:", res2.status_code)
print("Data:", json.dumps(res2.json(), indent=2))
