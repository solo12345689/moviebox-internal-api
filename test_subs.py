
import sys, os, json
sys.path.append(os.getcwd())
import logging
logging.getLogger('moviebox_api').setLevel(logging.CRITICAL)
from moviebox_api.client import MovieBoxClient
from moviebox_api import MovieBoxAuth

client = MovieBoxClient(auth=MovieBoxAuth())
hdrs = {'User-Agent': 'MovieBox/11.7.0 (iPhone; iOS 16.6; Scale/3.00)', 'X-M-Version': '11.7.0'}

ids = ['864148001923679056', '3325889774849773352', '1295107631744466896']

for sid in ids:
    print(f"\n--- ID: {sid} ---")
    res = client.request('GET', '/wefeed-mobile-bff/subject-api/get', params={'subjectId': sid}, headers=hdrs)
    data = res.get('data', {})
    detectors = data.get('resourceDetectors', [])
    if detectors:
        rid = detectors[0].get('resourceId')
        print(f"ResourceId: {rid}")
        
        # Test 1: use rid
        r1 = client.request('GET', '/wefeed-mobile-bff/subject-api/get-ext-captions', 
                           params={'resourceId': rid, 'subjectId': sid, 'episode': 1}, headers=hdrs)
        c1 = r1.get('data', {}).get('extCaptions') or []
        print(f"ExtCaptions (rid) count: {len(c1)}")
        if c1:
             print(f"Sample caption: {c1[0].get('lanName')} -> {c1[0].get('subPath')}")

        # Test 2: use sid as resourceId
        r2 = client.request('GET', '/wefeed-mobile-bff/subject-api/get-ext-captions', 
                           params={'resourceId': sid, 'subjectId': sid, 'episode': 1}, headers=hdrs)
        c2 = r2.get('data', {}).get('extCaptions') or []
        print(f"ExtCaptions (sid) count: {len(c2)}")
    else:
        print("No detectors")
