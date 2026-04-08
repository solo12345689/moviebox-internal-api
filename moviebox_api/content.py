from typing import Dict, Optional, List
from .client import MovieBoxClient

class MovieBoxContent:
    def __init__(self, client: MovieBoxClient):
        self.client = client

    def get_home(self, page: int = 1, page_size: int = 20) -> Dict:
        """Fetches the home feed recommendation."""
        return self.client.request(
            "POST",
            "/subject-api/daily-movie-rec",
            data={"page": page, "pageSize": page_size}
        )

    def search(self, keyword: str, page: int = 1, page_size: int = 20) -> Dict:
        """Searches for content based on keyword."""
        return self.client.request(
            "POST",
            "/subject-api/search",
            data={"keyword": keyword, "page": page, "pageSize": page_size}
        )

    def get_movie_detail(self, subject_id: str) -> Dict:
        """Fetches details for a specific movie or show."""
        return self.client.request(
            "GET",
            "/subject-api/get",
            params={"subjectId": subject_id}
        )

    def get_episode_list(self, series_id: str, page: int = 1, page_size: int = 50) -> Dict:
        """Fetches episodes for a series (via season-info)."""
        return self.client.request(
            "GET",
            "/subject-api/season-info",
            params={"subjectId": series_id}
        )

    def get_recommendations(self, subject_id: str) -> Dict:
        """Fetches similar recommendations (related)."""
        return self.client.request(
            "GET",
            "/subject-api/related",
            params={"subjectId": subject_id}
        )

    def get_categories(self, category_id: int = 1, page: int = 1) -> Dict:
        """Fetches content by category ID via Operating Tab."""
        return self.client.request(
            "GET",
            "/wefeed-mobile-bff/tab-operating",
            params={"tabId": category_id, "page": page, "pageSize": 24}
        )

    def get_home_list(self, category_id: int = 1, page: int = 1) -> Dict:
        """Fetches content for Home sections (Trending, Movie, Game, etc.) via POST."""
        return self.client.request(
            "POST",
            "/home/v2/get-list",
            data={"categoryId": category_id, "page": page, "pageSize": 24}
        )

    def get_rankings(self, path_variant: str = "/wefeed-mobile-bff/tab/ranking-list", tab_id: int = 1) -> Dict:
        """Fetches the global ranking lists via GET."""
        return self.client.request(
            "GET",
            path_variant,
            params={"tabId": tab_id, "categoryType": "all", "page": 1, "perPage": 20}
        )

    def get_search_suggestions(self) -> Dict:
        """Fetches trending search ranking/suggestions via GET."""
        return self.client.request(
            "GET",
            "/wefeed-mobile-bff/subject-api/search-rank",
            params={"page": 1, "pageSize": 10}
        )

    def get_playlist_content(self, playlist_id: str, page: int = 1) -> Dict:
        """Fetches contents of a specific playlist via GET."""
        return self.client.request(
            "GET",
            "/wefeed-mobile-bff/playlist/content",
            params={"playlistId": playlist_id, "page": page, "pageSize": 20}
        )

    def get_related_playback(self, subject_id: str) -> Dict:
        """Fetches related content specifically for the playback screen."""
        return self.client.request(
            "POST",
            "/wefeed-mobile-bff/subject-api/play-related-rec",
            data={"subjectId": subject_id}
        )

    def get_discovery(self) -> Dict:
        """Homepage Top Picks."""
        return self.client.request(
            "POST",
            "/wefeed-mobile-bff/subject-api/top-rec",
            data={}
        )

    def get_trending(self) -> Dict:
        """Trending Row."""
        return self.client.request(
            "POST",
            "/wefeed-mobile-bff/subject-api/trending/v2",
            data={}
        )

    def get_subject_list(self, page: int = 1, category_type: str = "1") -> Dict:
        """Fetches a general list of subjects (Movies/Series)."""
        return self.client.request(
            "POST",
            "/wefeed-mobile-bff/subject-api/list",
            data={"page": page, "pageSize": 20, "type": category_type}
        )

    def filter_items(self, filters: Dict, page: int = 1) -> Dict:
        """Advanced filtering for subjects via GET."""
        params = {"page": page, "pageSize": 24}
        params.update(filters)
        return self.client.request(
            "GET",
            "/wefeed-mobile-bff/subject-api/filter-items",
            params=params
        )

    # --- Live & Community (Rooms) ---
    def get_rooms(self, page: int = 1) -> Dict:
        """Fetches recommended communities/rooms."""
        return self.client.request(
            "GET",
            "/wefeed-mobile-bff/room-api/recommend",
            params={"page": page, "pageSize": 20}
        )

    def get_room_detail(self, room_id: str) -> Dict:
        """Fetches details for a specific room."""
        return self.client.request(
            "POST",
            "/wefeed-mobile-bff/room-api/get",
            data={"groupId": str(room_id)}
        )

    def get_room_posts(self, room_id: str, page: int = 1) -> Dict:
        """Fetches posts/feed within a room."""
        return self.client.request(
            "GET",
            "/wefeed-mobile-bff/post/list/subject",
            params={"subjectId": room_id, "page": page, "pageSize": 20}
        )

    # --- Live Sports ---
    def get_live_channels(self, page: int = 1) -> Dict:
        """Fetches current live TV channels/feeds."""
        return self.client.request(
            "GET",
            "/wefeed-mobile-bff/subject-api/live/list",
            params={"page": page, "pageSize": 20}
        )

    def get_sports_discovery(self) -> Dict:
        """Initial detection for live sports events (returns Web URLs)."""
        # This often comes from a specific 'OperateTab' id (e.g., 100) or config
        return self.client.request(
            "GET",
            "/wefeed-mobile-bff/tab-operating",
            params={"tabId": "live_sports", "page": 1}
        )
