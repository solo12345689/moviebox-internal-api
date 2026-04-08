import os, re
out = open('all_smali_apis.txt', 'w', encoding='utf-8')
scan_dir = 'C:/Users/akshi/moviebox/decoded_apk'
found_routes = set()
for root, dirs, files in os.walk(scan_dir):
    for f in files:
        if f.endswith('.smali'):
            try:
                with open(os.path.join(root, f), 'r', encoding='utf-8', errors='ignore') as sf:
                    matches = re.findall(r'\"(/[^\"]+mobile-bff/[^\"]+)\"', sf.read())
                    for match in matches: found_routes.add(match)
            except Exception as e: pass
for route in sorted(list(found_routes)): out.write(route + '\n')
out.close()
