import json
from moviebox_api.client import MovieBoxClient
from moviebox_api.content import MovieBoxContent

res = MovieBoxContent(MovieBoxClient()).get_categories(8)
with open('raw_anime.json', 'w') as f:
    json.dump(res, f, indent=2)
