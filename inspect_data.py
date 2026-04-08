from moviebox_api.client import MovieBoxClient
from moviebox_api.content import MovieBoxContent
import json

client = MovieBoxClient()
content = MovieBoxContent(client)

# Naruto Subject ID from user screenshot is likely found via search
print("Searching for Naruto...")
res = content.search("Naruto")
items = res.get("data", {}).get("list") or []

if items:
    first_id = items[0].get("subjectId") or items[0].get("id")
    print(f"Found ID: {first_id}")
    print("Full Metadata for FIRST item in SEARCH:")
    print(json.dumps(items[0], indent=2))
    
    print("\nFetching Full Detail...")
    detail = content.get_movie_detail(first_id)
    print("Full DETAIL Response:")
    print(json.dumps(detail, indent=2))
else:
    print("No items found.")
