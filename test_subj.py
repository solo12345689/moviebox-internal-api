import os
import json
import logging
from moviebox_api.client import MovieBoxClient
from moviebox_api.content import MovieBoxContent

# Silence logging
logging.getLogger("moviebox_api").setLevel(logging.ERROR)

def test_subject(type_id):
    client = MovieBoxClient()
    content = MovieBoxContent(client)
    
    print(f"--- Testing SubjTab Type: {type_id} ---")
    try:
        # We'll try the subject list POST vertical first
        res = content.get_subject_list(page=1, category_type=str(type_id))
        if res.get("code") == 0:
            data = res.get("data") or {}
            items = data.get("list") or data.get("items") or data.get("subjects") or []
            print(f"SUCCESS (Subject List): Found {len(items)} items.")
            if items:
                 print(f"Sample Item: {items[0].get('name') or items[0].get('title')}")
            return
        else:
            print(f"FAILED (Subject List): Code {res.get('code')} - {res.get('msg')}")
    except Exception as e:
        print(f"ERROR (Subject List): {e}")

    try:
        # Try tab-operating GET vertical
        res = content.get_categories(category_id=type_id, page=1)
        if res.get("code") == 0:
            data = res.get("data") or {}
            items = data.get("list") or data.get("items") or data.get("subjects") or []
            print(f"SUCCESS (Tab Operating): Found {len(items)} items.")
            return
        else:
            print(f"FAILED (Tab Operating): Code {res.get('code')} - {res.get('msg')}")
    except Exception as e:
        print(f"ERROR (Tab Operating): {e}")

if __name__ == "__main__":
    test_subject(28) # Nollywood
    test_subject(11) # Game
