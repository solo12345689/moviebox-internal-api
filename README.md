# 🎬 MovieBox Pro — Unofficial Streaming Dashboard

A high-performance, browser-native streaming dashboard that reverse-engineers the MovieBox/AOneRoom mobile app API and exposes it through a local web dashboard. Supports H.264 & H.265 content, subtitles, watchlist, history, and external player integration.

---

## 📐 Architecture Overview

```
Browser (localhost:3001)
       │
       │  HTTP REST calls
       ▼
FastAPI Backend (localhost:8000)   ◄──► MovieBox/AOneRoom API Servers
       │                                  (api6.aoneroom.com, etc.)
       │
       ├── /proxy-media  ──────────────►  Raw CDN streams (CORS bypass)
       ├── /play-compat  ──────────────►  FFMPEG H.265→H.264 Transcode Pipe
       └── /download     ──────────────►  FFMPEG/HTTPX file download pipe
```

### Key Components

| Component | File | Purpose |
|---|---|---|
| **Backend API Server** | `moviebox_api_server.py` | FastAPI server, all endpoints |
| **MovieBox API Client** | `moviebox_api/client.py` | Signs & sends requests to AOneRoom |
| **Auth Module** | `moviebox_api/auth.py` | Login, session, OTP |
| **Content Module** | `moviebox_api/content.py` | Home, search, detail, episodes |
| **Stream Module** | `moviebox_api/stream.py` | Playback URLs, stream resolution |
| **Dashboard (Frontend)** | `dashboard/` | Next.js 16 web app |
| **Video Player** | `dashboard/components/VideoPlayer.tsx` | ArtPlayer-based video player |
| **Home Page** | `dashboard/app/page.tsx` | Main browsing UI |
| **Detail Page** | `dashboard/app/detail/[id]/page.tsx` | Movie/series details |
| **Watch Page** | `dashboard/app/watch/[id]/page.tsx` | Fullscreen player UI |

---

## 🚀 Setup & Running

### Prerequisites

- **Python 3.10+** — for the backend
- **Node.js 18+** — for the frontend
- **FFMPEG** — must be in system PATH (for H.265 transcoding and downloads)
  ```
  # Install via Scoop (Windows)
  scoop install ffmpeg
  ```

### Step 1: Start the Backend

```powershell
cd C:\Users\akshi\moviebox
python moviebox_api_server.py
```

Backend runs on **http://localhost:8000**

> Interactive API docs available at: **http://localhost:8000/docs**

### Step 2: Start the Frontend

```powershell
cd C:\Users\akshi\moviebox\dashboard
npm run dev -- --port 3001
```

Frontend runs on **http://localhost:3001**

---

## 🌐 Frontend Pages

| Route | Description |
|---|---|
| `http://localhost:3001/` | Home — Browse movies, anime, rankings, search |
| `http://localhost:3001/detail/{id}` | Detail — Poster, synopsis, cast, episode list, community posts |
| `http://localhost:3001/watch/{id}` | Watch — Full-screen player with subtitles, seeking, download |
| `http://localhost:3001/profile` | Profile — User account info |

### Watch Page Query Params

```
/watch/{subjectId}?s=1&e=5
  s = season number  (default: 1)
  e = episode number (default: 1)
```

---

## 📡 API Endpoints Reference

All endpoints are served from `http://localhost:8000`.

---

### 🔐 Authentication

#### `POST /login`
Authenticate with email/phone + password.

**Request Body (JSON):**
```json
{
  "account": "user@example.com",
  "password": "yourpassword",
  "authType": 1
}
```
**Response:**
```json
{
  "status": "success",
  "user": { "nickname": "...", "avatar": "..." }
}
```
> Sets a `session_id` cookie on success. All subsequent requests must include this cookie.

---

#### `POST /register`
Create a new MovieBox account.

**Request Body (JSON):**
```json
{
  "account": "user@example.com",
  "password": "yourpassword",
  "otp": "123456",
  "authType": 1
}
```

---

#### `POST /request-otp`
Send a verification code to email/phone.

**Request Body (JSON):**
```json
{
  "account": "user@example.com",
  "authType": 1,
  "type": 1
}
```
> `type`: `1` = Register, `2` = Login

---

#### `POST /logout`
Invalidate the current session.

---

#### `GET /user-info`
Get the currently logged-in user's profile.

**Response:**
```json
{
  "logged_in": true,
  "user": { "nickname": "...", "avatar": "...", "email": "..." }
}
```

---

### 🏠 Content Discovery

#### `GET /home`
Fetch the main home feed with curated content sections.

**Response:**
```json
{
  "data": {
    "list": [
      {
        "title": "Trending Now",
        "type": "movies",
        "items": [ { "subjectId": "...", "title": "...", "cover": "..." } ]
      }
    ]
  }
}
```

---

#### `GET /anime`
Fetch anime content section.

---

#### `GET /rankings`
Fetch movie/series rankings.

---

#### `GET /discovery`
Fetch the "Discovery" / "For You" feed.

---

#### `GET /trending`
Fetch trending content.

---

#### `GET /movies`
Fetch the movies section.

---

#### `GET /search-suggestions?q={query}`
Get search autocomplete suggestions.

**Query Params:**
| Param | Default | Description |
|---|---|---|
| `q` | `""` | Partial search query |

---

#### `GET /search?q={query}`
Full-text search for movies and series.

**Query Params:**
| Param | Type | Description |
|---|---|---|
| `q` | string | Search query |

---

### 🎬 Content Detail

#### `GET /detail/{subject_id}`
Get full metadata for a movie or series.

**Response:**
```json
{
  "code": 0,
  "data": {
    "title": "Classroom of the Elite",
    "subjectId": "123456",
    "subjectType": 2,
    "cover": "https://...",
    "poster": "https://...",
    "score": "9.1",
    "runtime": "24",
    "releaseTime": "2022",
    "description": "...",
    "cast": [ { "name": "...", "role": "...", "avatar": "..." } ],
    "related": [ { "subjectId": "...", "title": "..." } ],
    "likeStatus": 1
  }
}
```

> `subjectType`: `1` = Movie, `2` = Series/Anime

---

#### `GET /episodes/{series_id}`
Get full season and episode list for a series.

**Response:**
```json
{
  "data": {
    "seasons": [
      {
        "seasonNumber": 1,
        "episodes": [
          { "episodeNumber": 1, "title": "Episode 1" }
        ]
      }
    ]
  }
}
```

---

### ▶️ Playback

#### `GET /stream/{subject_id}?season=1&episode=1&quality=720P`
Resolve the playback URL for a movie or episode.

**Query Params:**
| Param | Default | Description |
|---|---|---|
| `season` | `1` | Season number |
| `episode` | `1` | Episode number |
| `quality` | `720p` | Stream quality (360p, 480p, 720p, 1080p) |

**Response (Standard H.264 stream):**
```json
{
  "url": "https://cdn.example.com/video.mp4",
  "quality": "720P",
  "cookie": "signCookie=...",
  "subtitles": [ { "lanName": "English", "url": "..." } ],
  "streamId": "..."
}
```

**Response (Auto-transcoded H.265 stream):**
```json
{
  "url": "http://localhost:8000/play-compat/{subject_id}?season=1&episode=1&quality=720P",
  "cookie": "",
  "isTranscoded": true,
  "runtime": "24"
}
```

> When `isTranscoded: true`, the frontend automatically routes through the FFMPEG transcode pipe. No manual action needed.

---

#### `GET /play-compat/{subject_id}?season=1&episode=1&quality=720P&start_time=0`
**FFMPEG Live Transcode Pipe** — converts HEVC/H.265 to browser-native H.264 fMP4.

Streams video directly to the browser. Supports `HEAD` requests for range negotiation.

**Query Params:**
| Param | Default | Description |
|---|---|---|
| `season` | `1` | Season number |
| `episode` | `1` | Episode number |
| `quality` | `720P` | Quality level |
| `start_time` | `0` | Seek to this second before transcoding |

> **This endpoint requires FFMPEG to be installed** and in the system PATH.

---

#### `GET /proxy-media?url={url}&cookie={cookie}`
Universal media proxy. Forwards any CDN URL through the local server to bypass CORS restrictions.

- Auto-rewrites `.m3u8` HLS manifests to route segments through the proxy
- Converts `.srt` subtitles to WebVTT on the fly
- Adds `Access-Control-Allow-Origin: *` to all responses

**Query Params:**
| Param | Description |
|---|---|
| `url` | The CDN media URL to proxy (URL-encoded) |
| `cookie` | The `signCookie` from the stream response |
| `start_time` | (optional) Resume timestamp in seconds |

---

#### `GET /download/{subject_id}?season=1&episode=1&quality=720P&title=Movie`
Download a movie or episode file to disk.

- For MP4 streams: proxies raw bytes with correct headers (browser native download)
- For DASH/HLS streams: uses FFMPEG to remux to `.ts` and pipes to the browser

**Query Params:**
| Param | Default | Description |
|---|---|---|
| `season` | `1` | Season number |
| `episode` | `1` | Episode number |
| `quality` | `720p` | Quality level |
| `title` | `Movie` | Filename prefix for the download |

---

### 📝 Subtitles

#### `GET /subtitles/{subject_id}?se=1&ep=1`
Get subtitle tracks for a movie or episode.

**Response:**
```json
{
  "data": {
    "list": [
      { "id": "...", "lanName": "English", "url": "https://cdn.../sub.srt" }
    ]
  }
}
```

---

#### `GET /subtitles/stream/{stream_id}`
Get subtitles linked to a specific stream ID.

---

#### `GET /subtitles/external/{subject_id}?episode=1`
Fetch extended community captions from the official extended subtitles API.

---

#### `GET /subtitles/search?q={title}&season=1&episode=1`
Search OpenSubtitles for matching subtitle tracks.

---

### 📚 History & Watchlist

#### `GET /history`
Get the user's complete watch history.

**Response:**
```json
{
  "data": { "list": [ { "subjectId": "...", "title": "...", "seeTime": 1234 } ] }
}
```

---

#### `GET /watchlist`
Get the user's watchlist ("Want to Watch" list).

---

#### `POST /watchlist/toggle`
Add or remove a title from the watchlist.

**Query Params:**
| Param | Type | Description |
|---|---|---|
| `subject_id` | string | The movie/series ID |
| `add` | bool | `true` to add, `false` to remove |
| `subject_type` | int | `1` = Movie, `2` = Series |

---

#### `GET /history/position?subject_id={id}&stream_id={id}`
Get the saved playback position for a specific stream.

---

#### `POST /history/position`
Save a playback position.

**Query Params:**
| Param | Type | Description |
|---|---|---|
| `subject_id` | string | Movie/series ID |
| `stream_id` | string | Stream ID from `/stream` response |
| `position_ms` | int | Position in milliseconds |

---

#### `POST /history/seen`
Mark a subject as "have seen".

---

#### `POST /history/delete/{subject_id}`
Delete a specific item from watch history.

---

#### `POST /history/progress`
Report full playback progress (used for "Continue Watching" sync).

**Request Body (JSON):**
```json
{
  "subject_id": "...",
  "progress_ms": 150000,
  "total_ms": 1440000,
  "status": 1
}
```

---

### 📺 External Players

#### `POST /launch-player?player=mpv&url=...&cookie=...`
Launch MPV or VLC with the stream URL and subtitle file.

**Query Params:**
| Param | Default | Description |
|---|---|---|
| `player` | `mpv` | `mpv` or `vlc` |
| `url` | required | Stream URL |
| `cookie` | `""` | Authentication cookie |
| `start_time` | `0` | Resume timestamp in seconds |
| `subtitle_url` | `""` | Path or URL to subtitle file |
| `duration` | `0` | Total duration in seconds (for MPV timeline) |
| `title` | `""` | Media title shown in player |
| `subject_id` | `""` | Used to sync history |

---

### 💬 Community / Posts

#### `GET /post/list/{subject_id}`
Get community discussion posts for a movie/series.

#### `POST /post/create`
Post a review/comment.

**Query Params:**
| Param | Description |
|---|---|
| `subject_id` | The movie ID |
| `content` | Text content of the post |

#### `POST /post/like`
Like a post.

#### `GET /post/count/{subject_id}`
Get the total post count for a title.

#### `GET /groups/trending`
Get trending community groups.

#### `GET /groups/interactive`
Get interactive groups.

---

## 🎛️ Player Features (Frontend)

### Virtual Timeline Engine
When playing a **transcoded H.265 stream**, the standard browser `currentTime` API reports only the local pipe position (starts at 0). The `VideoPlayer.tsx` component implements a **Virtual Timeline Engine** that:

1. **Intercepts** the native `video.currentTime` getter/setter via `Object.defineProperty`
2. **Adds a seek offset** so the progress bar shows the true global time (e.g., `15:23 / 24:00`)
3. **Re-tunes the transcode pipe** when seeking by calling `/play-compat/{id}?start_time={seconds}`

### Subtitle Switching (Silent)
Subtitles can be toggled on/off and switched between languages without reloading the video. The player uses:
```ts
art.subtitle.url = newSubtitleVttUrl;
art.subtitle.show = true;
```
The backend's `/proxy-media` endpoint auto-converts `.srt` to WebVTT.

### Silent Background Download
Clicking **"Offline Mirror"** triggers a silent `<a>` element download instead of opening a new tab:
```ts
const link = document.createElement('a');
link.href = downloadUrl;
link.setAttribute('download', filename);
link.click();
```

---

## 🛠️ Troubleshooting

### Video doesn't play / "No supported sources"
- Check the backend logs for `500` errors on `/stream/{id}`
- The stream may be HEVC-only — the system will auto-route to `/play-compat`
- Ensure FFMPEG is installed: `ffmpeg -version`

### Seeking restarts from 00:00
- This happens on transcoded streams. The Virtual Timeline Engine should handle it.
- Check browser console for `[VIRTUAL VOD]` logs to confirm it's active.

### Duration shows "00:10" instead of full movie length
- The backend `/play-compat` response includes a `runtime` field (in minutes)
- The frontend reads this and passes it as `duration` (in seconds) to the player plugin

### Subtitles not showing
- Ensure the subtitle URL is proxied through `/proxy-media` (for CORS)
- The backend auto-detects `.srt` and converts to WebVTT

### MPV shows wrong duration
- Duration is now passed as `--length={seconds}` via the `/launch-player` endpoint
- Ensure your frontend passes `duration` in the axios POST to `/launch-player`

### CORS errors in browser console
- Ensure the backend is running on port 8000
- The `CORSMiddleware` allows `localhost:3000` and `localhost:3001`

---

## 📦 Tech Stack

| Layer | Technology |
|---|---|
| Frontend Framework | Next.js 16.2 (App Router) |
| UI Styling | Tailwind CSS v4 |
| Video Player | ArtPlayer v5 + hls.js + dash.js |
| HTTP Client (Frontend) | Axios |
| Backend Framework | FastAPI |
| Media Proxy | HTTPX (async) |
| Transcoding | FFMPEG (subprocess pipe) |
| Auth | Cookie-based session (httpOnly) |

---

## 📁 Project Structure

```
moviebox/
├── moviebox_api_server.py     # Main FastAPI server (all endpoints)
├── moviebox_api/
│   ├── __init__.py            # Module exports
│   ├── auth.py                # Login, register, OTP
│   ├── client.py              # Signed HTTP client for AOneRoom API
│   ├── content.py             # Home, search, movie detail
│   ├── stream.py              # Stream/playback URL resolution
│   ├── user.py                # User profile, history, watchlist
│   └── utils.py               # Request signing utilities
├── dashboard/
│   ├── app/
│   │   ├── page.tsx           # Home page
│   │   ├── detail/[id]/page.tsx  # Detail page
│   │   ├── watch/[id]/page.tsx   # Watch/player page
│   │   └── profile/page.tsx   # Profile page
│   ├── components/
│   │   ├── VideoPlayer.tsx    # ArtPlayer-based video player
│   │   └── MovieCard.tsx      # Movie card UI component
│   └── lib/
│       └── api.ts             # Frontend API client (axios wrappers)
├── local_history.json         # Local watch history cache (auto-created)
└── README.md                  # This file
```
