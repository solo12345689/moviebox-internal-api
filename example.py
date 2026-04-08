import json
from moviebox_api import MovieBoxClient, MovieBoxAuth, MovieBoxContent, MovieBoxStream

def main():
    # 1. Initialize client (uses anonymous token by default)
    print("[*] Initializing MovieBox Client...")
    auth = MovieBoxAuth()
    client = MovieBoxClient(auth=auth)
    content_api = MovieBoxContent(client)
    stream_api = MovieBoxStream(client)

    # 2. Get Home feed
    print("[*] Fetching Home Feed...")
    home_feed = content_api.get_home(page=1)
    
    if not home_feed.get("data"):
        print("[!] No data returned from Home feed. Check if base_url is still valid.")
        return

    # 3. Find the first movie (search for one if home feed is empty)
    feed_data = home_feed.get("data", {})
    list_items = feed_data.get("list") or []
    first_item = list_items[0] if list_items else None
    
    if not first_item:
        print("[*] Home feed empty, searching for 'Deadpool'...")
        search_res = content_api.search("Deadpool")
        search_data = search_res.get("data", {})
        
        # In MovieBox, search results are in 'items'
        results = search_data.get("items") or search_data.get("list") or []
        if not results and search_data.get("verticalRanks"):
            # If 'list' is empty, look in the first vertical category
            for vr in search_data["verticalRanks"]:
                if vr.get("list"):
                    results = vr["list"]
                    break
        
        if not results:
            print(f"[!] No results found. Data keys: {list(search_data.keys())}")
            return
        first_item = results[0]
    
    # ID can be 'id' or 'subjectId', Title can be 'title' or 'name'
    content_id = first_item.get("subjectId") or first_item.get("id")
    content_title = first_item.get("title") or first_item.get("name")
    
    # Show poster URL (usually "cover")
    poster_url = first_item.get("cover") or first_item.get("poster")
    
    print(f"[*] Found content: '{content_title}' (ID: {content_id})")
    print(f"    - Poster: {poster_url}")

    # 4. Get and display details
    print("[*] Fetching detail...")
    detail = content_api.get_movie_detail(content_id)
    data = detail.get("data", {})
    
    print(f"    - Overview: {data.get('description', '')[:100]}...")
    print(f"    - Release Date: {data.get('releaseTime', 'N/A')}")
    print(f"    - Score: {data.get('score', '0.0')}")
    
    # Show season/episode if TV
    if data.get("subjectType") == 2: # TV Show
        print(f"    - Type: TV Series")
        print(f"    - Progress: Season {data.get('seasonNumber', 1)}, Ep {data.get('totalEpisode', 'N/A')}")
        
        # List Episodes
        print("[*] Fetching episodes...")
        ep_list = content_api.get_episode_list(content_id)
        eps = ep_list.get("data", {}).get("list", [])
        if eps:
            print(f"    - Found {len(eps)} episodes.")
            first_ep = eps[0]
            print(f"      [1] {first_ep.get('title')} (Ep: {first_ep.get('episodeNumber')})")

    # 5. Resolve streaming and playback info
    print(f"[*] Resolving stream for ID: {content_id}...")
    try:
        stream_data = stream_api.get_stream(content_id)
        
        print("\n--- RESOLVED PLAYABLE STREAM ---")
        print(f"URL: {stream_data['url']}")
        print(f"Cookie: {stream_data['headers'].get('Cookie', 'None')}")
        print(f"User-Agent: {stream_data['headers'].get('User-Agent')}")
        
        if stream_data.get("subtitles"):
            print(f"Found {len(stream_data['subtitles'])} subtitle(s).")
    except Exception as e:
        print(f"[!] Error resolving stream: {e}")

if __name__ == "__main__":
    main()
