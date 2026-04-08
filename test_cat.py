import traceback
from moviebox_api.client import MovieBoxClient
from moviebox_api.content import MovieBoxContent

try:
    c = MovieBoxClient()
    co = MovieBoxContent(c)
    res = co.get_categories(category_id=13, page=1)
    print(res)
except Exception:
    print(traceback.format_exc())
