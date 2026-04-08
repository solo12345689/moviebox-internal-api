import traceback
from moviebox_api.client import MovieBoxClient
try:
    c = MovieBoxClient()
    res = c.request('GET', '/wefeed-mobile-bff/tab-operating', params={'tabId': 13})
    print(res)
except Exception:
    print(traceback.format_exc())
