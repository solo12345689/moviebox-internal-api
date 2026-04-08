from moviebox_api.client import MovieBoxClient
from moviebox_api.content import MovieBoxContent
import json

client = MovieBoxClient()
content = MovieBoxContent(client)

def explore():
    # Try all homepage-like endpoints
    print("--- CATEGORY 0 (Home) ---")
    home = content.get_home()
    items = home.get("data", {}).get("items", []) or home.get("data", {}).get("list", [])
    if items:
        print(f"Found {len(items)} items in home")
        sid = items[0].get("id") or items[0].get("subjectId")
        detail = content.get_movie_detail(sid)
        print(f"Subject {sid} Keys: {list(detail.get('data', {}).keys())}")
        print(f"Detail Sample: {json.dumps(detail.get('data'), indent=2)[:1000]}")
    else:
        print("Home feed empty")

    print("\n--- DISCOVERY ---")
    disc = content.get_discovery()
    items = disc.get("data", {}).get("list", [])
    if items:
        print(f"Found {len(items)} items in discovery")
    else:
        print("Discovery empty")

    print("\n--- TRENDING ---")
    trend = content.get_trending()
    # It might be in data['list'] or data['items']
    items = trend.get("data", {}).get("list", []) or trend.get("data", {}).get("items", [])
    if items:
        print(f"Found {len(items)} items in trending")
    else:
        print("Trending empty")

if __name__ == "__main__":
    explore()
