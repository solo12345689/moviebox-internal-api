import json
import os

files = ['raw_western_clean.json', 'raw_music.json']
for filename in files:
    if not os.path.exists(filename): continue
    print(f"--- {filename} ---")
    try:
        # Try different encodings
        content = None
        for enc in ['utf-8-sig', 'utf-16', 'utf-16le', 'utf-8']:
            try:
                with open(filename, 'r', encoding=enc) as f:
                    content = f.read()
                    break
            except: continue
        
        if content:
            data = json.loads(content)
            # Find the items
            items = []
            if isinstance(data, dict):
                inner_data = data.get('data', {})
                if isinstance(inner_data, dict):
                    items = inner_data.get('list') or inner_data.get('items') or inner_data.get('subjects') or []
            
            if items:
                # Look for 'Witcher' or just print first item
                target = None
                for i in items:
                    # In some rows it's nested
                    if isinstance(i, dict):
                         # Recursively check for Witcher
                         if 'Witcher' in str(i):
                             target = i
                             break
                
                if target:
                    print(json.dumps(target, indent=2))
                else:
                    print("Could not find Witcher, printing first item:")
                    print(json.dumps(items[0], indent=2))
    except Exception as e:
        print(f"Error reading {filename}: {e}")
