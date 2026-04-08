import json
import logging
from moviebox_api.client import MovieBoxClient
from moviebox_api.content import MovieBoxContent

logging.getLogger("moviebox_api").setLevel(logging.ERROR)

def dump_tab_0():
    client = MovieBoxClient()
    content = MovieBoxContent(client)
    
    print("--- Dumping Tab 0 (Home Root) ---")
    res = content.get_categories(category_id=0, page=1)
    if res.get("code") == 0:
        data = res.get("data") or {}
        items = data.get("list") or data.get("items") or []
        for i in items:
            title = i.get("title") or i.get("name")
            tab_id = i.get("tabId") or i.get("id")
            print(f"Section: {title} | TabID: {tab_id}")
    else:
        print(f"Failed: {res}")

if __name__ == "__main__":
    dump_tab_0()
