from typing import Dict, Optional
from .client import MovieBoxClient

class MovieBoxUser:
    def __init__(self, client: MovieBoxClient):
        self.client = client

    def get_profile(self) -> Dict:
        """Fetches comprehensive user profile."""
        return self.client.request(
            "GET", 
            "/wefeed-mobile-bff/user-api/profile/v2"
        )

    def get_history(self, page: int = 1, per_page: int = 20) -> Dict:
        """
        Fetches watch history ('Watched').
        Uses seeType 2.
        """
        return self.client.request(
            "GET",
            "/wefeed-mobile-bff/subject-api/see-list-v2",
            params={
                "page": str(page),
                "pageSize": str(per_page),
                "seeType": "2"
            }
        )

    def get_watchlist(self, page: int = 1, per_page: int = 20) -> Dict:
        """
        Fetches watchlist ('Want to Watch').
        Uses seeType 1.
        """
        return self.client.request(
            "GET",
            "/wefeed-mobile-bff/subject-api/see-list-v2",
            params={
                "page": str(page),
                "pageSize": str(per_page),
                "seeType": "1"
            }
        )

    def toggle_watchlist(self, subject_id: str, action: int = 1, subject_type: int = 1) -> Dict:
        """
        Toggles watchlist.
        Action: 1 (Add), 2 (Remove)
        CRITICAL: Must use 'data=' for MovieBoxClient.request to ensure JSON body is sent.
        """
        sid = str(subject_id)
        
        # 1. Primary want-to-see (BFF modern sync)
        # We pass exhaustive keys to satisfy different server versions
        payload = {
            "subjectId": sid,
            "SubjectId": sid,
            "Subject": sid,
            "subject": sid,
            "action": int(action),
            "subjectType": int(subject_type),
            "SubjectType": int(subject_type)
        }
        
        bff_res = self.client.request(
            "POST", 
            "/wefeed-mobile-bff/subject-api/want-to-see",
            data=payload
        )
        
        # 2. Account Profile Collect (Legacy sync)
        self.client.request(
            "POST",
            "/wefeed-mobile-bff/subject-api/collect",
            data={
                "subjectId": sid,
                "Subject": sid,
                "SubjectId": sid,
                "status": 1 if action == 1 else 0,
                "subjectType": int(subject_type)
            }
        )
        
        return bff_res

    def report_history(self, subject_id: str, progress_ms: int, total_ms: int, status: int = 1) -> Dict:
        """Reports playback progress."""
        endpoint = "/wefeed-mobile-bff/subject-api/have-seen"
        payload = {
            "list": [
                {
                    "subjectId": str(subject_id),
                    "id": str(subject_id),
                    "seeTime": int(progress_ms),
                    "totalTime": int(total_ms),
                    "status": status
                }
            ]
        }
        return self.client.request("POST", endpoint, data=payload)
