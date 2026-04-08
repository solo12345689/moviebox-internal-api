
import sys
import os
import json
# Add current directory to path
sys.path.append(os.getcwd())
from moviebox_api.client import MovieBoxClient
from moviebox_api.content import MovieBoxContent

client = MovieBoxClient()
content = MovieBoxContent(client)
# Try rankings explicitly with prefix
print("Testing Rankings...")
res = content.get_rankings()
print(f"RANKINGS RESPONSE: {json.dumps(res, indent=2)}")

print("\nTesting Suggestions...")
res_s = content.get_search_suggestions()
print(f"SUGGESTIONS RESPONSE: {json.dumps(res_s, indent=2)}")
