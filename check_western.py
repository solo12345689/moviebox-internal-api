import json
try:
    with open('raw_western_clean.json', 'r', encoding='utf-16le') as f:
        data = json.load(f)
    # Print the first item's structure
    items = data.get('data', {}).get('list') or data.get('data', {}).get('subjects') or []
    if items:
        print(json.dumps(items[0], indent=2))
except Exception as e:
    print(f"Error: {e}")
