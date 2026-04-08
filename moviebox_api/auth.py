import json
import os
from .utils import generate_client_token, get_default_client_info, md5_hex

class MovieBoxAuth:
    def __init__(self, token: str = None, user_id: str = None):
        self.token = token
        self.user_id = user_id
        self.is_logged_in = True if token else False
        self.client_info = get_default_client_info()
        self.user_info = None
        # REMOVED: self.load_session() - We no longer use a global file for multiple sessions

    def login_guest(self):
        """Perform guest login (Reset back to anonymous state)."""
        self.token = None
        self.user_id = None
        self.is_logged_in = False
        self.user_info = None

    def update_session(self, token: str, user_id: str = None, user_info: dict = None):
        """Updates the session with a new bearer token and user metadata."""
        self.token = token
        if user_id:
            self.user_id = user_id
        if user_info:
            self.user_info = user_info
        self.is_logged_in = True

    def save_session(self):
        """No-op: Sessions are now managed in memory by the server per-user session ID."""
        pass

    def load_session(self):
        """No-op: Sessions are now managed in memory by the server per-user session ID."""
        pass

    def get_auth_headers(self) -> dict:
        """Returns the current auth headers based on state (Guest vs Authenticated)."""
        headers = {}
        if self.is_logged_in and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
            headers["X-Client-Status"] = "1"
        else:
            headers["X-Client-Token"] = generate_client_token()
            headers["X-Client-Status"] = "0"
        
        headers["X-Client-Info"] = json.dumps(self.client_info, separators=(',', ':'))
        return headers
