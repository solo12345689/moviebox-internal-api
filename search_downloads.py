import os
import re

dir_path = r'C:\Users\akshi\moviebox\decoded_apk'
for root, _, files in os.walk(dir_path):
    if 'smali' not in root:
        continue
    for file in files:
        if file.endswith('.smali'):
            try:
                with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                    content = f.read()
                    matches = re.findall(r'(/[a-zA-Z0-9\-\/]*down[a-zA-Z0-9\-\/]*)', content.lower())
                    for m in set(matches): print('Found down:', m)
                    matches2 = re.findall(r'(/[a-zA-Z0-9\-\/]*offl[a-zA-Z0-9\-\/]*)', content.lower())
                    for m in set(matches2): print('Found offline:', m)
            except Exception:
                pass
