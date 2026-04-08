import json

for enc in ['utf-16', 'utf-16le', 'utf-8-sig', 'utf-8']:
    try:
        with open('raw_music.json', 'r', encoding=enc) as f:
            data = json.load(f)
        items = data.get('data', {}).get('list') or data.get('data', {}).get('subjects') or []
        for row in items:
            print(f"Row Title: {row.get('title') or row.get('name')}")
    except: continue
