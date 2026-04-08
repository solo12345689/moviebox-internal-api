@dataclass
class VideoStream:
    url: str
    quality: str
    format: str

@dataclass
class PlayInfoResponse:
    url: str
    sign_cookie: str
    subtitles: List[Dict] = field(default_factory=list)

@dataclass
class MovieDetail:
    id: str
    title: str
    poster: str  # JSON key "cover"
    description: str
    release_date: str # JSON key "releaseTime"
    rating: float # JSON key "score"
    genres: List[str] = field(default_factory=list)
    season: Optional[int] = None
    episode: Optional[int] = None
    total_episodes: Optional[int] = None
