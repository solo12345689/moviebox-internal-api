import os
import re

dir_path = r'C:\Users\akshi\moviebox\decoded_apk'
api_paths = set()

for root, _, files in os.walk(dir_path):
    if 'smali' not in root:
        continue
    for file in files:
        if file.endswith('.smali'):
            try:
                with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                    content = f.read()
                    strs = re.findall(r'"(/[a-zA-Z0-9\-]+/[a-zA-Z0-9\-\/]*)"', content)
                    for s in strs:
                        sl = s.lower()
                        if 'down' in sl or 'dl' in sl or 'off' in sl:
                            api_paths.add(s)
            except:
                pass

for p in sorted(api_paths):
    print("FOUND PATH:", p)
print('Done scanning')
