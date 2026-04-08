import json

with open('raw_music.json', 'r', encoding='utf-16le') as f:
    data = json.load(f)

# Find the Topic "TOP SINGERS MIX"
items = data.get('data', {}).get('list') or data.get('data', {}).get('subjects') or []
for row in items:
    if 'TOP SINGERS' in (row.get('title') or row.get('name') or ''):
        inner = row.get('customData', {}).get('items') or []
        if inner:
            print("Keys in Singer Item:", inner[0].keys())
            print("Sample Singer Item:", json.dumps(inner[0], indent=2))
        break
