import json

try:
    with open('raw_music.json', 'r', encoding='utf-8-sig') as f:
        data = json.load(f)
    items = data.get('data', {}).get('list') or data.get('data', {}).get('subjects') or []
    for row in items:
        if 'SINGERS' in (row.get('title') or '').upper():
            inner = row.get('customData', {}).get('items') or []
            if inner:
                print("Sample Singer Item:", json.dumps(inner[0], indent=2))
                break
except Exception as e:
    print(f"Error: {e}")
