import json
from moviebox_api import MovieBoxClient, MovieBoxContent

def debug():
    client = MovieBoxClient()
    content = MovieBoxContent(client)
    
    # Check Home
    print("--- HOME ---")
    home = content.get_home()
    data = home.get("data", {})
    items = data.get("items", [])
    print(f"Items found: {len(items)}")
    if items:
        # Check first item structure for poster/cover
        item = items[0]
        print(f"Item Keys: {list(item.keys())}")
        print(f"Title: {item.get('title') or item.get('name')}")
        print(f"Poster Object: {json.dumps(item.get('poster'), indent=2)}")
        print(f"Cover: {item.get('cover')}")

    # Find a TV Show
    tv_show = next((i for i in items if i.get("subjectType") == 2), None)
    if tv_show:
        sid = tv_show.get("subjectId")
        print(f"\n--- TV SHOW ({sid}) ---")
        season_info = client.request("GET", "/wefeed-mobile-bff/subject-api/season-info", params={"subjectId": sid})
        print(f"Season Info Keys: {list(season_info.get('data', {}).keys())}")
        print(f"Seasons: {len(season_info.get('data', {}).get('seasons', []))}")
        
if __name__ == "__main__":
    debug()
