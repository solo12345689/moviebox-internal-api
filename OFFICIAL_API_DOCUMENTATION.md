# MovieBox Pro - Official API & Protocol Documentation

This document outlines the internal communication protocol, authentication handshake, and endpoint structure of the official MovieBox Pro Android application (v16.2.1), discovered via deep-decompilation and traffic analysis.

## What's New in Version 4.0.02
As of the newly discovered v4.0.02 API, the following critical changes have been implemented:
*   **Identity Headers:** The `X-M-Version` must now be `"4.0.02"`, the `version_code` is `"50020126"`, and the package name changed to `com.community.oneroom`.
*   **Search API Changes:** The old `GET /wefeed-mobile-bff/subject-api/search` endpoint has been completely removed (returns 404). Searches MUST now be sent as `POST` requests to `/wefeed-mobile-bff/subject-api/search` with the JSON body payload containing `{"keyword": "...", "type": 0, "page": 1, "pageSize": 20}`.

## 1. Client Identity & Headers

The API servers utilize strict header-based filtering to block unauthorized web clients. Native playback and high-fidelity resolution (4K/1080p) require parity with the mobile identity.

### **Primary Request Headers**
| Header | Value / Format | Purpose |
| :--- | :--- | :--- |
| `User-Agent` | `MovieBoxPro/16.2.1 (Android 12; Pixel 6)` | Primary identity for BFF clusters. |
| `X-M-Version` | `16.2.1` | Version locking for metadata endpoints. |
| `Accept` | `application/json` | JSON response requirement. |
| `Content-Type` | `application/json;charset=UTF-8` | POST payload format. |
| `Referer` | `https://api6.aoneroom.com/` | Domain authority for DASH clusters. |
| `X-Client-Token` | `timestamp,md5(reversed_timestamp)` | Cryptographic guest verification token. |
| `x-tr-signature` | `timestamp|2|base64(hmac-md5(canonical))` | High-level request verification signature. |
| `X-Client-Info` | `{JSON}` | Serialized device, language, and network metadata. |
| `X-Client-Status` | `0` or client status flags | Runtime client operational state. |
| `X-Play-Mode` | `2` | Configures playback stream resolving context. |
| `Authorization` | `Bearer <Token>` | User session token (refreshed via response `x-user`). |

### **Cryptographic Token Handshake (`X-Client-Token` & Dynamic Guest Bootstrapping)**
To authorize requests without an active login session, the client can bootstrap credentials using either:
1. **Direct Visitor Login**: `POST /wefeed-mobile-bff/user-api/visitor-login` with payload `{}` to obtain a fresh guest `token` and `userId`.
2. **Dynamic Header Token Extraction**: Pinging `/wefeed-mobile-bff/tab-operating?host=api.inmoviebox.com&page=1&pageSize=24&tabId=1` to extract the issued guest token from the `x-user` response header.
3. **Session Bearer Injection**: The acquired token is injected as `Bearer <token>` inside the `Authorization` header for subsequent queries.
4. **Token Generation (`X-Client-Token`)**:
   * Get Unix epoch timestamp in milliseconds: `timestamp = str(int(time.time() * 1000))`
   * Reverse timestamp characters: `reversed = timestamp[::-1]`
   * Calculate MD5 hex digest: `hash = md5(reversed)`
   * Token format: `X-Client-Token: timestamp + "," + hash`


### **Cryptographic App Signature (`x-tr-signature`)**
For requests going to the Android BFF endpoints, the server validates a signature of the HTTP request payload and headers:
1. **Rebuild Sorted Query String**: Take all URL query parameters, sort them alphabetically by key, and concatenate them as `key=value` separated by `&`. Do not percent-encode values.
2. **Hash the Request Body**: If a request body exists, compute the MD5 hex hash of the first 100KB (`102,400` bytes) of the payload.
3. **Build the Canonical Request String**:
   ```
   [METHOD]\n
   [ACCEPT_HEADER]\n
   [CONTENT_TYPE_HEADER]\n
   [BODY_LENGTH]\n
   [TIMESTAMP_MS]\n
   [BODY_MD5_HASH]\n
   [CANONICAL_PATH_AND_QUERY]
   ```
4. **Sign the Canonical String**:
   * Decode the base64-encoded Gateway Secret Key (Default: `76iRl07s0xSN9jqmEWAt79EBJZulIQIsV64FZr2O`, Alt: `Xqn2nnO41/L92o1iuXhSLHTbXvY4Z5ZZ62m8mSLA`).
   * Sign the UTF-8 bytes of the Canonical String using **HMAC-MD5** with the decoded key.
5. **Format Signature**: Concatenate the signature timestamp, format version (`2`), and base64-encoded signature digest:
   `x-tr-signature: timestamp_ms + "|2|" + base64_encode(hmac_md5_digest)`

### **Device Metadata Header (`X-Client-Info`)**
Contains serialized JSON data that provides system, network, and region parity:
```json
{
  "package_name": "com.community.oneroom",
  "version_name": "3.0.03.0529.03",
  "version_code": 50020042,
  "os": "android",
  "os_version": "12",
  "install_ch": "ps",
  "device_id": "<32_char_hex_id>",
  "install_store": "ps",
  "gaid": "<google_advertising_id_uuid>",
  "brand": "Redmi",
  "model": "2201117TG",
  "system_language": "en",
  "net": "NETWORK_WIFI",
  "region": "US",
  "timezone": "America/New_York",
  "sp_code": "40401",
  "X-Play-Mode": "2"
}
```

### **Global vs. Regional App Identifiers**
* **Global App Variant**:
  * **Package Name**: `com.community.oneroom` (and `com.community.moviebox`)
  * **Target Version**: `3.0.11.1230.03` (Global users, excluding India)
  * **Base Domains**: `https://i-api.aoneroom.com` (Global BFF cluster) and `https://api.aoneroom.com`
  * **Deep Link Verification Hosts**:
    * `h5.inmoviebox.com`
    * `moviebox.ac`
    * `moviebox.ph`
* **Regional (India) App Variant**:
  * **Package Name**: `com.community.mbox.in` (SubRoom App wrapper)
  * **Target Version**: `3.0.15.0513.03`
  * **Base Domains**: `https://api.inmoviebox.com` and `https://api6.aoneroom.com`

### **Media Verifier Headers (FFmpeg/ExoPlayer)**
Used during media segment requests to bypass CDN-level 403 Forbidden errors.
*   **User-Agent**: `ExoPlayerLib/2.19.1` (or `MovieBoxPro/16.2.1`)
*   **Referer**: `https://www.movieboxpro.app/` (Specifically for `hakunaymatata` variants)

---

## 2. API Endpoints (BFF - Backend for Frontend)

The application primarily communicates with clusters like `api6.aoneroom.com` and `api5.aoneroom.com` under the `/wefeed-mobile-bff/` path.

### **Content & Metadata**
*   **Get Detail**: `GET /wefeed-mobile-bff/subject-api/get`
    *   *Params*: `subjectId`, `host`
    *   *Returns*: Detailed metadata, `resourceDetectors` (dub tracking), and cast info.
*   **Search**: `GET /wefeed-mobile-bff/subject-api/search`
    *   *Params*: `q`, `page`, `pageSize`
*   **Play Info (The Resolver)**: `GET /wefeed-mobile-bff/subject-api/play-info`
    *   *Params*: `subjectId`, `se` (Season), `ep` (Episode), `quality`, `resourceId`
    *   *Returns*: Stream URLs (`streamList`) and internal subtitles (`subTitleList`).
*   **Play Info V2**: `GET /wefeed-mobile-bff/subject-api/play-info/v2`
    *   *Params*: `subjectId`, `se` (Season), `ep` (Episode)
    *   *Returns*: Stream manifest URLs (`streams`), `displayResolutions`, and `cdnThrottleLevel`.
*   **Resource Mirror V2**: `GET /wefeed-mobile-bff/subject-api/resource/v2`
    *   *Params*: `subjectId`, `se`, `epFrom`, `epTo`, `page`, `perPage`, `resolution`, `isVip=true`, `pagerMode=2`
    *   *Returns*: User-generated and mirror resource streams filtered by episode range.
*   **Resource Position / Failover Recovery V2**: `GET /wefeed-mobile-bff/subject-api/resource-position/v2`
    *   *Params*: `subjectId`, `resourceId`, `failUrl`, `failCode=404`, `resourceNum=0`, `isVip=true`
    *   *Returns*: Alternate fallback stream URL when primary link fails or hits an anti-piracy trap video.
*   **External Subtitles**: `GET /wefeed-mobile-bff/subject-api/get-ext-captions`
    *   *Params*: `resourceId`, `subjectId`, `episode`
    *   *Notes*: Returns high-quality CloudFront-signed `.srt` tracks.
*   **Operating Module Item List (Curated Collection Grid)**: `POST /wefeed-mobile-bff/operating-module/item-list`
    *   *Params/Payload*: `tabId`, `tabCode`, `page`, `perPage` (or `pageSize`)
    *   *Notes*: Powers the dedicated vertical multi-column collection view (`OperateActivity` -> `SubTabFragment`) triggered when tapping 'All >' on thematic operational modules (e.g., 'Anime in Progress').

### **User, History & Watchlist**
*   **Fetch History (Watched)**: `GET /wefeed-mobile-bff/subject-api/see-list-v2`
    *   *Params*: `page`, `pageSize`, `seeType=2`
*   **Fetch Watchlist (Want to Watch)**: `GET /wefeed-mobile-bff/subject-api/see-list-v2`
    *   *Params*: `page`, `pageSize`, `seeType=1`
*   **Add/Remove from Watchlist**: `POST /wefeed-mobile-bff/subject-api/want-to-see`
    *   *Payload*: `{"subjectId": <ID>, "action": 1, "subjectType": 1}`
    *   *Action Codes*: `1` (Add), `2` (Remove).
*   **Report Progress / Save to History**: `POST /wefeed-mobile-bff/subject-api/have-seen`
    *   *Payload*: `{"list": [{"subjectId": <ID>, "seeTime": <MS>, "totalTime": <MS>, "status": 1}]}`
    *   *Usage*: Synchronizes "Continue Watching" across devices.
*   **Global User Info**: `GET /wefeed-mobile-bff/user-api/profile/v2`
    *   *Returns*: Avatar, account duration, VIP status, and login points.

---

## 3. The Authentication Handshake (Regional Escalation & Web Playback)

MovieBox utilizes a multi-phase resolution strategy to bypass regional geofencing and copyright-restricted mirrors (especially for Hindi/Hindi-Dubbed titles).

### **Phase 1: Carrier 301 Escalation (The "Legacy Link")**
For titles that return `code: 407` (Restricted) or empty `streamList` on primary clusters, the app falls back to:
*   **Endpoint**: `POST /index/video/v_detail`
*   **Payload**: `{'subjectId': ID, 'carrier': '301', 'quality': '720p'}`
*   **Logic**: This bypasses the BFF layer and hits the legacy resolution engine, which often yields raw MP4 mirrors that are geofence-ignorant.

### **Phase 2: CloudFront Signed Cookies & Prioritization**
Regional DASH manifests (e.g., `sacdn2.hakunaymatata.com`) require a three-part CloudFront signature passed via the `Cookie` header:
1.  `CloudFront-Policy`
2.  `CloudFront-Signature`
3.  `CloudFront-Key-Pair-Id`
*   **CRITICAL**: When resolving streams, the client MUST prioritize the stream-specific `signCookie` CloudFront triple returned from the API over the global user JWT token. Failing to do so (or passing the JWT token to the CDN) yields a `403 Forbidden` error.
*   **Web Integration**: Web players (e.g., `hls.js` and `dash.js`) must inject these cookies into all segment and manifest requests.
    *   **HLS (`hls.js`)**: Configured via the `xhrSetup` handler: `xhr.setRequestHeader('Cookie', cookie)`.
    *   **DASH (`dash.js`)**: Configured via extending the `RequestModifier` class: `xhr.setRequestHeader('Cookie', cookie)`.

### **Phase 3: GSLB (Global Server Load Balancing) Redirect**
The app performs a HEAD request (Handshake) to the CDN before playback. This triggers the issuance of a `signCookie` session token which validates the player's IP against the temporary media URL.

### **Phase 4: H.265 (HEVC) Auto-Failover & Local Transcoding**
Many regional streams are only served in the HEVC (H.265) compression format, which standard web browsers cannot natively decode.
*   **Browser Error Capture**: The web player registers event listeners to capture fatal codec playback failures (`dashjs.MediaPlayer.events.ERROR` or `Hls.Events.ERROR`).
*   **Transcode Failover Pipe**: On capture, the player automatically reroutes the stream source to the backend transcoding pipeline: `/play-compat/{id}?season={season}&episode={episode}&quality={quality}`.
*   **Subprocess Transcoding**: The backend uses an asynchronous `ffmpeg` subprocess to dynamically transcode the HEVC stream into a standard H.264 stream in real-time, allowing browser playback on any device.

### **Phase 5: Anti-Piracy Dummy Video Bypass (v4.0.02+)**
In newer versions, the API deliberately attempts to trap unofficial clients and scrapers.
*   **The Trap:** The `/wefeed-mobile-bff/subject-api/play-info` endpoint returns a valid-looking `url` field containing an `.mp4` stream. However, this is actually a fake 21-second "Please update your app" dummy video meant to break unofficial scrapers.
*   **Discovery Note:** This trap was reverse-engineered by observing a critical discrepancy in the `play-info` API response. The response returned a video `duration` of `1427` seconds (~23 minutes, the exact length of a standard anime episode), but the actual media player only played a 21-second video from the primary `url` field (`https://macdn.aoneroom.com/other/.../b164fbfb43477929...mp4`). The metadata proved the API knew the real video duration but was deliberately serving the wrong file link.
*   **The Secret Key:** The real streaming information is hidden inside the `signCookie` property within the stream object.
*   **The Bypass Algorithm:**
    1.  Parse the `signCookie` string and search for `urlprefix=`.
    2.  Extract the Base64 encoded string immediately following it. (e.g., `aHR0cHM6Ly9zYmNkbjIuaGFrdW5heW1hdGF0YS5jb20...`)
    3.  Decode the Base64 string to reveal the hidden base CDN server path (e.g., `https://sbcdn2.hakunaymatata.com/dash/.../`).
    4.  Append `index.mpd` (for MPEG-DASH streams) or `index.m3u8` (for HLS streams) to the end of that hidden path to construct the true, playable stream manifest URL, entirely ignoring the fake `url` field.

### **Phase 6: Resource Mirror VIP Parameter Spoofing (`isVip=true`)**
While primary playback resolvers strictly enforce subscription entitlements against the user account token, secondary mirror and failover endpoints rely on client-supplied query parameters:
*   **Target Endpoints**: `/wefeed-mobile-bff/subject-api/resource/v2` and `/wefeed-mobile-bff/subject-api/resource-position/v2`.
*   **Mechanism**: Include `isVip=true` in the URL query parameters when generating the canonical signature (`x-tr-signature`).
*   **Bypass Effect**: Unlocks 1080p/4K resolution tiers and direct fallback mirrors without requiring a paid VIP subscription or logged-in account status.

---

## 4. Internal Secrets (Static)
Discovered via `AndroidManifest.xml` and Smali string decryption.
*   **Gateway Secret**: `76iRl07s0xSN9jqmEWAt79EBJZulIQIsV64FZr2O` (Used for sign calculation in some clusters).
*   **ByteDance Gecko / Pangle SDK Access Key**: `f36c832c8dbb162c49b46a7a6dd47fbd` (Used during Pangle/Gecko dynamic asset loader initialization)
*   **Transsion WeFeed Service Secret**: `df70dbad6215444ca9e87ee1078cc681`
*   **Transsion BuzzBox Service Secret**: `a6b574246ecb4ab99cd00f74a621743a`
*   **Transsion Online Course Service Secret**: `c63c7b2a952c42ab9d5e3fccf0e213bf`

---

## 5. Subtitle Protocol
Official subtitles follow a signed-URL pattern stored on `cacdn.hakunaymatata.com`.
*   **Internal**: Bundled with `play-info` (Direct URLs).
*   **External**: Fetched via `resourceId` matching. 
*   **Formats**: Primary `.srt`, secondary `.vtt`. 
## 6. Other System Endpoints (Discovery)

Discovered endpoints that manage secondary application logic:

### **Tab & Layout**
*   `GET /wefeed-mobile-bff/tab-api/all`: Fetches the dynamic tab structure for the home screen.
*   `GET /wefeed-mobile-bff/tab-operating`: Fetches layout promotions and banners.
*   `GET /wefeed-mobile-bff/activity/embedded-h5-list/v2`: Lists dynamic layout templates and embedded H5 applications/promotional pages.
*   **Static Resource Configurations**: `https://infra-static.aoneroom.com/embedding/[yyyy]/[mm]/[dd]/[md5].json` (Hosts structural configuration parameters for components/regions).

### **Account & Security**
*   `GET /wefeed-mobile-bff/user-api/info`: Fetches detailed user profile/plan data.
*   `GET /wefeed-mobile-bff/user-api/check-mail-account`: Validates email before registration.
*   `POST /wefeed-mobile-bff/user-api/reset-password`: Forgotten password flow.
## 7. Complete BFF Discovery Map

The following endpoints were extracted directly from the application's service mapping logic.

### **Core Subject APIs (`/subject-api/`)**
*   `/wefeed-mobile-bff/subject-api/cast`
*   `/wefeed-mobile-bff/subject-api/comment/list`
*   `/wefeed-mobile-bff/subject-api/comment/post`
*   `/wefeed-mobile-bff/subject-api/comment-v2/list`
*   `/wefeed-mobile-bff/subject-api/episode-list`
*   `/wefeed-mobile-bff/subject-api/episode-more`
*   `/wefeed-mobile-bff/subject-api/get`
*   `/wefeed-mobile-bff/subject-api/get-download-resource`
*   `/wefeed-mobile-bff/subject-api/get-ext-captions`
*   `/wefeed-mobile-bff/subject-api/get-stream-captions`
*   `/wefeed-mobile-bff/subject-api/have-seen`
*   `/wefeed-mobile-bff/subject-api/like`
*   `/wefeed-mobile-bff/subject-api/play-info`
*   `/wefeed-mobile-bff/subject-api/play-info/v2`: V2 video stream resolver with throttle and resolution metadata.
*   `/wefeed-mobile-bff/subject-api/play-next`
*   `/wefeed-mobile-bff/subject-api/play-url`
*   `/wefeed-mobile-bff/subject-api/ranking-list`
*   `/wefeed-mobile-bff/subject-api/rating`
*   `/wefeed-mobile-bff/subject-api/recommend`
*   `/wefeed-mobile-bff/subject-api/resource-status`
*   `/wefeed-mobile-bff/subject-api/search`
*   `/wefeed-mobile-bff/subject-api/search-rank`
*   `/wefeed-mobile-bff/subject-api/season-info`
*   `/wefeed-mobile-bff/subject-api/see-list-v2`
*   `/wefeed-mobile-bff/subject-api/start-download-resource`: Initialize download tracking.
*   `/wefeed-mobile-bff/subject-api/finish-download-resource`: Complete download reporting.
*   `/wefeed-mobile-bff/subject-api/resource`: Fetch raw resource metadata.
*   `/wefeed-mobile-bff/subject-api/resource/v2`: Filterable episode/season resource mirror query.
*   `/wefeed-mobile-bff/subject-api/search-rank`: High-conversion search suggestions.
*   `/wefeed-mobile-bff/subject-api/topic-list`
*   `/wefeed-mobile-bff/subject-api/trending/v2`
*   `/wefeed-mobile-bff/subject-api/want-to-see`
*   `/wefeed-mobile-bff/subject-api/bottom-tab`: Bottom tab layout configuration.
*   `/wefeed-mobile-bff/subject-api/detail-rec`: Contextual detail recommendations.
*   `/wefeed-mobile-bff/subject-api/dub-info`: Available audio dub languages.
*   `/wefeed-mobile-bff/subject-api/filter-items`: Filter parameters for categories.
*   `/wefeed-mobile-bff/subject-api/list`: Lists items within subjects.
*   `/wefeed-mobile-bff/subject-api/play-related-rec`: Related content suggestions post-resolution.
*   `/wefeed-mobile-bff/subject-api/resource-position`: Tracking position of static resources.
*   `/wefeed-mobile-bff/subject-api/resource-position/v2`: Failover stream link recovery for broken/dummy clips.
*   `/wefeed-mobile-bff/subject-api/search-rank/v2`: V2 query rank suggestions.
*   `/wefeed-mobile-bff/subject-api/search-suggest`: Instant search suggestions.
*   `/wefeed-mobile-bff/subject-api/search/v2`: Optimized V2 search endpoint.
*   `/wefeed-mobile-bff/subject-api/staff-info`: Cast & Crew detailed metadata.
*   `/wefeed-mobile-bff/subject-api/staff-related`: Content related to specific staff.
*   `/wefeed-mobile-bff/subject-api/staff-subject-list`: Catalog items associated with staff members.
*   `/wefeed-mobile-bff/subject-api/subtitle-search`: Subtitle track listing / search.
*   `/wefeed-mobile-bff/subject-api/want-to-see-staff`: Watchlist for specific staff updates.
*   `/wefeed-mobile-bff/subject-api/widget`: Dynamic UI widgets content.
*   `/wefeed-mobile-bff/subject-api/daily-movie-rec`: Daily curated movie recommendation cards.
*   `/wefeed-mobile-bff/subject-api/genre-top`: Top-ranked titles and items by genre.
*   `/wefeed-mobile-bff/subject-api/season-info/v2`: Optimized V2 series season and episode resolver.
*   `/wefeed-mobile-bff/subject-api/trending-by-sport`: Trending sports highlights and video reels.

### **User & Identity APIs (`/user-api/`)**
*   `/wefeed-mobile-bff/user-api/block`
*   `/wefeed-mobile-bff/user-api/check-mail-account`
*   `/wefeed-mobile-bff/user-api/check-phone-account`
*   `/wefeed-mobile-bff/user-api/check-sms-code`
*   `/wefeed-mobile-bff/user-api/get-sms-code`
*   `/wefeed-mobile-bff/user-api/info`
*   `/wefeed-mobile-bff/user-api/login`
*   `/wefeed-mobile-bff/user-api/logout`
*   `/wefeed-mobile-bff/user-api/modify`
*   `/wefeed-mobile-bff/user-api/register`
*   `/wefeed-mobile-bff/user-api/reset-password`
*   `/wefeed-mobile-bff/user-api/third-login`
*   `/wefeed-mobile-bff/user-api/unblock`
*   `/wefeed-mobile-bff/user-api/visitor-login`: Direct guest JWT and user identity bootstrap.
*   `/wefeed-mobile-bff/user-api/profile/v3`: Advanced user identity profile.
*   `/wefeed-mobile-bff/user-api/submit-prefer`: Save user category preferences.
*   `/wefeed-mobile-bff/user-api/device-sessions`: Query and revoke active logged-in device sessions.

### **User Profiles, Preferences & Location**
*   `/wefeed-mobile-bff/profile/consume-judge`: User subscription validation checks.
*   `/wefeed-mobile-bff/profile/preference-options`: Get default preferences list.
*   `/wefeed-mobile-bff/profile/preference-submit`: Submit user preferences layout.
*   `/wefeed-mobile-bff/location/near-address`: Geolocated user address lookups.

### **UGC (User Generated Content) APIs (`/ugc/`)**
*   `/wefeed-mobile-bff/ugc/category/lev1-sub-list`: UGC subcategory listings.
*   `/wefeed-mobile-bff/ugc/collection/download-list`: UGC download collection.
*   `/wefeed-mobile-bff/ugc/collection/play-list`: UGC playlists details.
*   `/wefeed-mobile-bff/ugc/collection/resolution`: UGC video resolution options.
*   `/wefeed-mobile-bff/ugc/operating/genre-top`: UGC trending genres.
*   `/wefeed-mobile-bff/ugc/operating/tab-operating`: UGC layouts and banners.
*   `/wefeed-mobile-bff/ugc/operating/tab-rank-list`: UGC trending ranking list.
*   `/wefeed-mobile-bff/ugc/search/everyone`: UGC public searches feed.
*   `/wefeed-mobile-bff/ugc/search/rank`: Popular UGC search terms.
*   `/wefeed-mobile-bff/ugc/search/result`: UGC search queries.
*   `/wefeed-mobile-bff/ugc/search/suggest`: UGC autocomplete search.
*   `/wefeed-mobile-bff/ugc/trending/by-download`: Most downloaded UGC items.
*   `/wefeed-mobile-bff/ugc/trending/by-hashtag`: UGC tagged content.
*   `/wefeed-mobile-bff/ugc/trending/by-ugc-video`: Trending video feed.
*   `/wefeed-mobile-bff/ugc/trending/channel`: UGC category channels.
*   `/wefeed-mobile-bff/ugc/trending/filter-edu`: UGC educational filter.
*   `/wefeed-mobile-bff/ugc/trending/home`: UGC main feed.
*   `/wefeed-mobile-bff/ugc/trending/immersive`: Fullscreen vertical UGC feed.
*   `/wefeed-mobile-bff/ugc/trending/subscribe`: Subscribed UGC creators.
*   `/wefeed-mobile-bff/ugc/video/download`: Fetch UGC video files.
*   `/wefeed-mobile-bff/ugc/video/first-by-subject`: Primary video file for subject.
*   `/wefeed-mobile-bff/ugc/video/get`: UGC video metadata.
*   `/wefeed-mobile-bff/ugc/video/list/by-my`: My uploaded UGC videos.
*   `/wefeed-mobile-bff/ugc/video/list/by-user`: User UGC uploads.
*   `/wefeed-mobile-bff/ugc-video/list/likes`: Liked UGC video collection.
*   `/wefeed-mobile-bff/favorite/ugc-video/list`: Bookmarked UGC videos.
*   `/wefeed-mobile-bff/favorite/ugc-video/toggle`: Favorite toggle logic.
*   `/wefeed-mobile-bff/comment/ugc-video`: Comments on UGC clips.

### **Shorts, Dubs & Reels System**
*   `/wefeed-mobile-bff/shorts/dub-info`: Dub translations for shorts.
*   `/wefeed-mobile-bff/shorts/favorite`: Favorite shorts.
*   `/wefeed-mobile-bff/shorts/favorite-list`: List of saved short films.
*   `/wefeed-mobile-bff/shorts/get-info`: Short series metadata.
*   `/wefeed-mobile-bff/shorts/get-mini-captions`: Quick subtitles for shorts.
*   `/wefeed-mobile-bff/shorts/mini-list`: Short video feeds collection.
*   `/wefeed-mobile-bff/shorts/most-trending`: Trending shorts index.
*   `/wefeed-mobile-bff/shorts/reel`: Video reel highlights.

### **Social, Community & Group APIs (`/group/` / `/post/`)**
*   `/wefeed-mobile-bff/group/list/community-entrance`: Group entrance layouts.
*   `/wefeed-mobile-bff/group/list/my/v2`: Current user joined groups.
*   `/wefeed-mobile-bff/group/list/subject`: Groups associated with specific films.
*   `/wefeed-mobile-bff/group/list/user`: Groups belonging to a user.
*   `/wefeed-mobile-bff/community/tab`: Community hub home config.
*   `/wefeed-mobile-bff/community/trending-entrance`: Dynamic entries for buzzbox posts.
*   `/wefeed-mobile-bff/post/count/subject`: Comments count for moments posts.
*   `/wefeed-mobile-bff/post/create`: Write new post.
*   `/wefeed-mobile-bff/post/delete`: Delete community post.
*   `/wefeed-mobile-bff/post/explore`: Browse hot community topics.
*   `/wefeed-mobile-bff/post/get`: Retrieve specific post.
*   `/wefeed-mobile-bff/post/list-by-tab`: Filter posts by category tab.
*   `/wefeed-mobile-bff/post/list-trending/group`: Trending posts in group.
*   `/wefeed-mobile-bff/post/list/correlation`: Contextual posts matching content.
*   `/wefeed-mobile-bff/post/list/group`: Posts in a particular group.
*   `/wefeed-mobile-bff/post/list/immersive`: Fullscreen content view.
*   `/wefeed-mobile-bff/post/list/immersive/v2`: V2 fullscreen feed.
*   `/wefeed-mobile-bff/post/list/likes`: Posts liked by user.
*   `/wefeed-mobile-bff/post/list/user`: User posts list.
*   `/wefeed-mobile-bff/post/list/user/my`: My community posts.
*   `/wefeed-mobile-bff/post/nearby`: Geolocated user posts feed.
*   `/wefeed-mobile-bff/interactive/post/like`: Like/Unlike community post.
*   `/wefeed-mobile-bff/group/class`: Group categorization and topic tags.
*   `/wefeed-mobile-bff/post/negative-feedback`: "Not Interested" / report action on community posts.
*   `/wefeed-mobile-bff/post/negative-feedback/config`: Reason tags and options for post negative feedback.
*   `/wefeed-mobile-bff/post/list-trending/sport`: Sports community trending moments and discussions.

### **In-App Messaging & Notifications (`/message/`)**
*   `/wefeed-mobile-bff/message/internal/has-new`: Unread message flags.
*   `/wefeed-mobile-bff/message/internal/list`: In-app notification center.
*   `/wefeed-mobile-bff/message/notify-bar/v2`: V2 banner/toast notifications list.
*   `/wefeed-mobile-bff/message/push/local/list`: Local client-triggered push schedules.
*   `/wefeed-mobile-bff/message/report`: Read receipt reports.
*   `/wefeed-mobile-bff/message/remind`: Scheduled alerts and reminders.

### **User Follow & Subscriptions (`/subscription/`)**
*   `/wefeed-mobile-bff/subscription/feed`: Updates from subscribed creators/interests.
*   `/wefeed-mobile-bff/subscription/stats`: Engagement stats of subscription.
*   `/wefeed-mobile-bff/subscription/status`: Subscribed flag checker.
*   `/wefeed-mobile-bff/subscription/subscription`: Creator subscribe action.
*   `/wefeed-mobile-bff/subscription/v1/followings`: List of followed accounts.

### **Check-In & Welfare Center Activities**
*   `/wefeed-mobile-bff/activity/ad-dada-set-default`: Configure ad providers preferences.
*   `/wefeed-mobile-bff/activity/ad-task-list`: Ad tasks available.
*   `/wefeed-mobile-bff/activity/entrance`: Activities dashboard gateway.
*   `/wefeed-mobile-bff/activity/fission/bind`: Bind referral code.
*   `/wefeed-mobile-bff/activity/lottery/prize-redeem`: Confirm prize ticket code.
*   `/wefeed-mobile-bff/activity/welfare-center`: Task hub landing page.
*   `/wefeed-mobile-bff/activity/marketing/sku-promotion`: Marketing campaign discounts and promotional plan offers.

### **General Feedback Systems**
*   `/wefeed-mobile-bff/feedback/commit`: Submit user tickets.
*   `/wefeed-mobile-bff/feedback/label/list`: Classification labels.
*   `/wefeed-mobile-bff/feedback/report`: Report dynamic issues.

### **System & Operational APIs**
*   `/wefeed-mobile-bff/category/list`: Browse by genre.
*   `/wefeed-mobile-bff/config/get`: Remote app configuration.
*   `/wefeed-mobile-bff/feedback/post`: User support tickets.
*   `/wefeed-mobile-bff/index/home`: Main landing page feed.
*   `/wefeed-mobile-bff/notice/list`: Internal system notifications.
*   `/wefeed-mobile-bff/ott-api/check-v2`: Smart TV / Firestick parity check.
*   `/wefeed-mobile-bff/post/list/subject`: User posts (Moments) for content.
*   `/wefeed-mobile-bff/statistics/user-operation`: Analytics tracking.
*   `/wefeed-mobile-bff/tab-api/all`: Home screen layout.
*   `/wefeed-mobile-bff/vip/member/detail`: Subscription details.
*   `/wefeed-mobile-bff/vip/member/rights-check`: High-resolution entitlement check.
*   `/wefeed-mobile-bff/vip/member/rewards-receive`: Claim VIP birthday/loyalty gifts.
*   `/wefeed-mobile-bff/activity/check-in`: Daily login rewards.
*   `/wefeed-mobile-bff/activity/check-in-info`: Current streak and history.
*   `/wefeed-mobile-bff/activity/task-list`: Daily/Weekly operational tasks.
*   `/wefeed-mobile-bff/activity/global-task`: Milestones and long-term quests.
*   `/wefeed-mobile-bff/activity/rewards-receive`: Trigger reward distribution.
*   `/wefeed-mobile-bff/activity/fission/reward-list`: Referral and social growth rewards.
*   `/wefeed-mobile-bff/activity/download-task-receive`: Rewards for offline consumption.
*   `/wefeed-mobile-bff/activity/promo-code-bind`: Promotional code redemption.
*   `/wefeed-mobile-bff/money/coin-log`: Virtual currency transaction history.
*   `/wefeed-mobile-bff/money/sku-list/get`: Fetch available coin/VIP packages.
*   `/wefeed-mobile-bff/money/exchange/order`: Finalize coin-to-VIP exchange.
*   `/wefeed-mobile-bff/ad/config`: Static configuration for client-side ad placements.
*   `/wefeed-mobile-bff/app/config`: Global application properties and overrides.
*   `/wefeed-mobile-bff/sniff/config`: Configuration rules for external source streaming discovery.
*   `/wefeed-mobile-bff/app/check-update`: Client app version verification and OTA update manifest.
*   `/wefeed-mobile-bff/get-op-byid`: Fetches content, items, and layout of a specific operational CMS block by `opId`.
*   `/wefeed-mobile-bff/operating-module/item-list`: Paginated catalog grid fetch for thematic operational collections (e.g. 'Anime in Progress', curated lists when clicking 'All >').
*   `/wefeed-mobile-bff/tab-operating-page`: Standalone dynamic layout payload for operational campaign pages.
*   `/wefeed-mobile-bff/tab-operating-ranklistmulti`: Multi-dimension operational rankings and leaderboards.

### **Auxiliary & Shared APIs**
*   `/wefeed-mobile-bff/music/like`: Like audio track.
*   `/wefeed-mobile-bff/music/like-list`: List of saved/liked audio.
*   `/wefeed-mobile-bff/comment`: Add subject comment.
*   `/wefeed-mobile-bff/comment/like`: Like subject comment.
*   `/wefeed-mobile-bff/comment/list`: Fetch comments for content.
*   `/wefeed-mobile-bff/comment/user/list`: List comments made by user.
*   `/wefeed-mobile-bff/playlist/content`: Subject playlist list of titles.
*   `/wefeed-mobile-bff/share/longurl`: Create web sharing links.
*   `/wefeed-mobile-bff/share/shorturl`: Create short links.
*   `/wefeed-mobile-bff/search-anaylze/seek`: Telemetry search query telemetry analysis.
*   `/wefeed-mobile-bff/live/match-detail`: Live sports event matches information.
*   `/wefeed-mobile-bff/live/sub-upcomming-match`: Subscribe to upcoming live sports event reminders.

### **Live TV & Television Broadcast APIs (`/live/`, `/tv-channel`)**
*   `/wefeed-mobile-bff/live/tv-country-list`: Lists countries offering linear/broadcast TV streams.
*   `/wefeed-mobile-bff/live/tv-channel-list-by-country`: Fetch television channels for a given country.
*   `/wefeed-mobile-bff/live/tv-channel`: Fetch channel metadata and live stream manifest URL.
*   `/wefeed-mobile-bff/tv-channel-operating`: Layout and promotional configurations for live TV channels.

### **Sports, Matches & Live Scores APIs (`/sport/`, `/sport-news/`)**
*   `/wefeed-mobile-bff/sport/league-tab`: Tournament and league category tabs (EPL, IPL, UCL, etc.).
*   `/wefeed-mobile-bff/sport/match-list`: All active, live, and upcoming matches.
*   `/wefeed-mobile-bff/sport/match-range-list`: Matches queried by custom date/time ranges.
*   `/wefeed-mobile-bff/sport/match-detail`: Real-time match overview, lineups, live scores, and team info.
*   `/wefeed-mobile-bff/sport/match-resource-list`: Resolves playable live CDN streaming links for sports matches.
*   `/wefeed-mobile-bff/sport/match-event-data`: Detailed real-time match events (goals, cards, timeline).
*   `/wefeed-mobile-bff/sport/match-flow`: Live text-based commentary stream.
*   `/wefeed-mobile-bff/sport/match-flow-has-new`: Fast polling endpoint to check for incoming commentary updates.
*   `/wefeed-mobile-bff/sport/match-vote`: Match polls and winner prediction votes.
*   `/wefeed-mobile-bff/sport/match-sub`: Subscribe to match notifications and kickoff alerts.
*   `/wefeed-mobile-bff/sport/match-sub-cancel`: Unsubscribe from match alerts.
*   `/wefeed-mobile-bff/sport/match-sub-list`: List of user's actively subscribed match alerts.
*   `/wefeed-mobile-bff/sport-news/tab-news`: Categorized sports news feed.
*   `/wefeed-mobile-bff/sport-news/trending`: Trending sports news headlines.

### **VIP & Membership**
*   `GET /wefeed-mobile-bff/vip/member/detail`: Check subscription status and expiry.
*   `GET /wefeed-mobile-bff/vip/member/rights-check`: Validates if the user can stream 4K/1080p.
*   `GET /wefeed-mobile-bff/vip/all-member-rights`: Complete feature matrix and entitlement breakdown across membership tiers.
*   `GET /wefeed-mobile-bff/vip/check-access`: Checks user access/permissions for given stream resolutions.
*   `POST /wefeed-mobile-bff/vip/entitlement-consume`: Consumes a trial token or single-view entitlement pass.
*   `GET /wefeed-mobile-bff/vip/member-goods`: Available VIP subscription SKUs and package options.
*   `POST /wefeed-mobile-bff/vip/migrate-assets`: Migrates legacy subscriptions, coins, or assets to modern account scheme.
*   `POST /wefeed-mobile-bff/vip/upgrade-rights`: Calculates and processes subscription plan tier upgrades.

---

## 8. Category & Vertical Feed Analysis

The application uses a modular category-based system to populate its vertical tabs.

### **Primary Endpoint: Home Category List**
*   **Route**: `POST /home/v2/get-list`
*   **Data Payload**: `{"categoryId": <ID>, "page": <PAGE>, "pageSize": 24}`

### **tabId Mapping**
| tabId | True Category | Highlights / Raw Sections Found |
| :--- | :--- | :--- |
| 0, 1, 6, 10, 27, 30, 31, 35 | 🏠 Main Home / Feed | Banners: Neagley, Haiwaan. Sections: Football Live, Trending Movies, Netflix WWE Live, Top Anime, K-Drama Shorts. |
| 2, 12, 23 | 🎬 Movies | Bollywood Love Stories, One-Person Army Action, Laugh Out Loud. |
| 3 | 📚 Education & Kids | Class 9 Maths, NEET Biology, Pre-primary, Kids Cartoon. |
| 4 | 🎵 Music | Most-Watched Music Videos, Evergreen Bollywood Hits, Pop/HipHop. |
| 5, 20 | 📺 Indian Web Series | Series In Progress, Indian Firepower, Reality-TV Shows (Bigg Boss). |
| 7, 13 | 📱 ShortTV | ShortTV deep links (vskit://), Playlists. |
| 8, 22, 24, 25 | 🎌 Anime | Trending Now (Bleach, JoJo), Anime in Progress. |
| 9 | 🔞 Adult / 18+ | UllU Drama List, Hentai Anime, Vivamax Movies, Porn Top Videos. |
| 11 | 🎮 Games | Popular Games 🔥 |
| 18 | 🌏 Asian Drama | Descendants of the Sun, Our Sticky Love, Girl From Nowhere. |
| 19 | 🤠 Western TV Series | Reacher, House of the Dragon, The Boys, S.W.A.T. |
| 28 | 🇳🇬 Nollywood / African | RuthKadiri247, Maurice Sam TV, LizzyGold Tv, IBAKATV. |
| 32 | 📱 General Shorts | Just a single [SPORT_POST_LIST] called "Shorts". |
| 33 | 🏅 Sports Shorts | Just a single [SPORT_POST_LIST] called "Sports Shorts Hub". |
| 37 | 🤼 Wrestling / Combat | WWE Must Watch Matches, Women’s Ring Showdowns. |
| 38 | 🍳 Cooking / Recipes | Christmas Bites, Recipe Filter, How to make Street Food. |
| 40 | 🎓 Courses / EdTech | PW Lesson, NEEV 3.0 (Class 9th), Excel Skills for Business. |

### **Summary of Home Feed Components**
| Component | Endpoint | Method |
| :--- | :--- | :--- |
| **Carousel** | `/subject-api/daily-movie-rec` | POST |
| **Discover** | `/wefeed-mobile-bff/subject-api/top-rec` | POST |
| **Trending** | `/wefeed-mobile-bff/subject-api/trending/v2` | POST |
| **Rankings** | `/wefeed-mobile-bff/tab/ranking-list` | GET |
| **Collection Grid** | `/wefeed-mobile-bff/operating-module/item-list` | POST |

---

## 9. Region Discovery & Content Localization

The official application employs two layers of regional detection to personalize content and enforce licensing geofences.

### **Layer 1: Carrier-Based Discovery (Device Native)**
The app utilizes the Android `TelephonyManager` to extract the **Mobile Country Code (MCC)** from the inserted SIM card. This is matched against an internal mapping file:
*   **Asset**: `assets/local_mcc.json`
*   **Logic**: Maps MCC (e.g., `404` for India) to ISO codes (`in`) and Country Names. This ensures that even on a VPN, the app knows the user's "home" region.

### **Layer 2: Server-Side Geolocation**
During the initial handshake (`GET /wefeed-mobile-bff/config/get`), the server geolocates the request IP address. The response contains regional pointers that overwrite the local discovery if necessary.

### **Layer 3: Region-Aware Filtering**
Content lists are requested via `home/v2/get-list` with a nested `filterType` object. The app dynamically prioritizes categories based on the discovered region:

*   **Bollywood Preference**: Triggered if Region == `India`.
    *   *Filter*: `{"country":"India", "sort":"ForYou"}`
*   **Nollywood Preference**: Triggered if Region == `Nigeria` (MCC `621`).
    *   *Filter*: `{"genre":"Nollywood", "sort":"ForYou"}`
*   **Hollywood (Default)**: Triggered if Region == `US/GB` or MCC is missing.
    *   *Filter*: `{"country":"United States", "sort":"ForYou"}`

### **Regional Manifest Redirects**
Streaming manifests (`.m3u8` / `.mpd`) are geolocated at the CDN level. If the `signCookie` region doesn't match the IP region, the server issues a `302 Redirect` to the appropriate regional cluster (e.g., `api-af` for Africa, `api-in` for India).

---

## 10. Live & Community (BuzzBox) Architecture

The "Live" section (internally referred to as `BuzzBox` or `RoomSystem`) enables social movie watching and real-time community engagement.

### **Orchestration Endpoints**
*   **Room Recommendation**: `GET /wefeed-mobile-bff/room-api/recommend`
*   **Room Detail**: `POST /wefeed-mobile-bff/room-api/get`
*   **Join/Exit Room**: `POST /wefeed-mobile-bff/room-api/join` | `/leave`
*   **User Posts (Feeds)**: `GET /wefeed-mobile-bff/post/list/subject`

### **Technology Stack**
*   **Playback Infrastructure**: Powered by **Alibaba Cloud (AliCloud)**. 
    *   *Native Library*: `libalivcffmpeg.so`
    *   *Protocol*: RTMP/HLS for live streams.
*   **Real-time Engagement**: Uses **WebSockets (Chat-API)** for synchronized playback and live commenting.
    *   *Endpoint*: `/chat-api/v1/room/sync`
*   **Analytics & Ads**: Integrated with **ByteDance (Pangle)** and **APM Insight** (`libpglarmor.so`, `libapminsighta.so`) for live event monitoring.

### **Functional Logic**
1.  **Discovery**: High-engagement rooms are surfaced via `room_recommend.json` presets or dynamic BFF fetches.
2.  **Session Creation**: Upon joining, the app receives a `roomId` and a `chatToken`.
3.  **Real-time Sync**: The `saasCorePlayer` hooks into the WebSocket feed to trigger "seek" events for all users in the room, enabling synchronized "Watch Together" sessions.

---

## 11. Live Sports & External Services

MovieBox aggregates third-party live content (Live Sports, Events) using a specialized **WebView Bridge**.

### **Live Sports Aggregators**
*   **Partners**: `sportslivetoday.com`, `sportsnow.top`
*   **Integration Method**: Custom Internal WebView.
*   **Usage**: Surfaced via Top-level banners for major events (Cricket, Football, e.g. FIFA World Cup).

### **WebView Protocol**
When an external sports link is triggered, the app employs the following security/bypass protocol:
1.  **Identity Spoofing**: The WebView **MUST** inject the official `User-Agent`:
    *   `MovieBoxPro/16.2.1 (Android 12; Pixel 6)`
2.  **Deep-link Wrapping**: External URLs are often wrapped in internal deep-links:
    *   `oneroom://webview?url=https://sportslivetoday.com/live/detail?id=<EVENT_ID>&sportType=<TYPE>`
3.  **Cross-Origin Bridge**: The app injects `moviebox_bridge.js` into the session. This bridge allows the third-party website to call native player functions (`openNativePlayer(url)`) if the web-player is too slow or lacks hardware acceleration.
4.  **Auto-Auth**: For VIP-only sports events, the app passes the `session_id` cookie directly to the partner domain's handshake endpoint.

---

## 12. Game Center Architecture

The MovieBox Game Center is an **H5-Native hybrid system** that allows users to play casual games without leaving the application.

### **Core Endpoints**
*   **Game List (Discovery)**: `GET /wefeed-mobile-bff/tab-operating?tabId=11`
*   **Game Detail (Launch)**: `GET /wefeed-mobile-bff/subject-api/get?subjectId=<ID>`
*   **Sync Progress**: `POST /wefeed-mobile-bff/game-api/report-score`

### **Game Payload Structure**
Unlike movies, a "Game" subject contains an `h5_play` metadata block:
```json
{
  "subjectId": "232588",
  "name": "Super Cricket 2026",
  "subjectType": 10,
  "playUrl": "https://pacdn.aoneroom.com/game/cricket/index.html",
  "orientation": "LANDSCAPE",
  "isH5": true
}
---

## 13. Multi-Language & Dubbing Protocol

In the official MovieBox application (reverse-engineered from the Android APK), the "Select Language" feature is powered by a two-phase handshake:

### **Phase 1: Discovery (Metadata Endpoint)**
To get the list of available dubs and regional languages for a title, the app fetches the detailed metadata.
*   **Path**: `/wefeed-mobile-bff/subject-api/get`
*   **Method**: `GET`
*   **Key Field**: The response contains a `resourceDetectors` array.
*   **Data Structure**:
```json
"resourceDetectors": [
  { "resourceId": "658838553874178...", "name": "Hindi dub" },
  { "resourceId": "658838553874179...", "name": "English dub" }
]
```

### **Phase 2: Resolution (Playback Endpoint)**
When the user selects a specific language (e.g., "Hindi dub"), the app does not call a separate "Selection" API. Instead, it passes the chosen `resourceId` directly to the playback resolver.
*   **Path**: `/wefeed-mobile-bff/subject-api/play-info`
*   **Method**: `GET`
*   **Parameters**:
    *   `subjectId`: The unique ID of the movie or show.
    *   `resourceId`: The ID obtained from the `resourceDetectors` list in Phase 1.
    *   `se` / `ep`: Season and Episode numbers (for TV series).
*   **Result**: The server returns a `streamList` specifically tailored to that language/resource group.

### **Native Handling**
*   **Activity**: Launched via `com.community.oneroom.H5GameActivity`.
*   **Rendering**: Uses a specialized WebView with **WebGL/Canvas Hardware Acceleration** enabled.
*   **Deep Link**: Internal banners use `oneroom://h5_game?url=<URL>&orientation=1`.
*   **User Persistence**: The user's `session_id` is passed as a query parameter or cookie to the H5 game to enable leaderboards and cross-device score syncing.

---

## 14. UGC (User Generated Content) Video Platform

The application hosts a secondary UGC short-video sharing platform backed by AliCloud OSS buckets.

### **UGC Endpoints**
*   **Play Short Video**: `GET /wefeed-mobile-bff/ugc/video/play` (resolves playback URL)
*   **Multi-Video Resolution**: `GET /wefeed-mobile-bff/ugc/video/play-multi`
*   **Like UGC Video**: `POST /wefeed-mobile-bff/interactive/ugc-video/like`
*   **Upload Token**: `POST /wefeed-mobile-bff/upload/sts-token/v2`
    *   *Returns*: Temporary AWS/AliCloud STS credentials (`AccessKeyId`, `SecretAccessKey`, `SessionToken`) to upload videos directly to the cloud CDN storage.
*   **UGC Download Handshake**:
    *   Initialize: `POST /wefeed-mobile-bff/ugc/video/start-download`
    *   Complete: `POST /wefeed-mobile-bff/ugc/video/finish-download`
*   **UGC Captions**: `GET /wefeed-mobile-bff/ugc/video/caption`

---

## 15. Third-Party Payment & Ad Mediation

Payment orchestration and ad network services are directly compiled into the core app's networking bridge.

### **Paynicorn Payment Gateway**
*   **Host**: `https://api.paynicorn.com`
*   **BFF Orders**:
    *   Create order: `POST /wefeed-mobile-bff/money/paynicorn-trading-order/create`
    *   Poll payment status: `GET /wefeed-mobile-bff/money/paynicorn-purchase-result/polling`
*   **Google Play Billing**:
    *   Create Play order: `POST /wefeed-mobile-bff/money/gp-trading-order/create`
    *   Poll Play receipt: `GET /wefeed-mobile-bff/money/gp-purchase-result/polling`

### **Ad Integration Gateways**
*   **Pangle / TikTok Ad Service**:
    *   Endpoints: `/api/ad/union/sdk/get_ads/`, `/api/ad/union/sdk/reward_video/reward/`, `/api/ad/union/sdk/settings/`
    *   Host: `https://api16-access-sg.pangle.io`
*   **Vungle Ad Network**:
    *   Hosts: `https://adx.ads.vungle.com/api/ads`, `https://config.ads.vungle.com/`, `https://logs.ads.vungle.com/sdk/error_logs`
*   **Hisavana Traffic Dispatch**:
    *   Endpoints: `/hisavana/traffic-dispatch/v1/consumer-not-login/addispatch/query/getAdData`
    *   Host: `https://api.test.hisavana.com`

---

## 16. Third-Party Subtitles (OpenSubtitles)

For titles lacking official `.vtt`/`.srt` assets on `hakunaymatata.com`, the app queries OpenSubtitles API directly.

*   **Subtitle Query**: `GET https://vip-api.opensubtitles.com/api/v1/subtitles?query=<title>`
*   **Download Track**: `GET https://vip-api.opensubtitles.com/api/v1/download`

---

## 17. In-App Lottery & Promotion System

The app utilizes gamified tasks and lotteries to drive user engagement and VIP registrations.

*   **User Streaks**: `GET /wefeed-mobile-bff/activity/check-in-info`
*   **Lottery Profile**: `GET /wefeed-mobile-bff/activity/lottery/user-info`
*   **Lottery Streaks**: `GET /wefeed-mobile-bff/activity/lottery/user-activity-info`
*   **Draw Lottery Ticket**: `POST /wefeed-mobile-bff/activity/lottery/draw`
*   **Claim Prizes**: `POST /wefeed-mobile-bff/activity/lottery/prize-claim`
*   **Redeem Code**: `POST /wefeed-mobile-bff/activity/lottery/draw-code-redeem`

---

## 18. Client Telemetry & Logs

*   **Retrieve Logs Config**: `GET /wefeed-mobile-bff/client_logs_retrieve/config`
*   **Bug Report Upload**: `POST /wefeed-mobile-bff/retrieve_client_logs/report`

---

## 19. App Update Service

*   **Check Updates**: `GET /{appPath}/app/check-update`

---

## 20. Short Dramas & TV Vertical BFF (`wefeed-fm-bff`)

The Short TV vertical uses a separate bff service domain path pattern:
*   **Fetch Shorts Playlist Content**: `GET /wefeed-fm-bff/shorts/playlist/content`
*   **Filter Shorts Subjects**: `GET /wefeed-fm-bff/shorts/subject/filter-items`
*   **List Shorts Series**: `GET /wefeed-fm-bff/shorts/subject/list`
*   **Shorts Captions**: `GET /wefeed-short-bff/shorts/get-mini-captions`

---

## 21. Deep Link Routing Protocols (`oneroom://`)

The application responds to intent schemas starting with `oneroom://`.

### **Supported Scheme Actions**
*   **Webview Bridge**: `oneroom://webview?url=<Url>` (opens in-app customized browser).
*   **Subject/Movie Detail**: `oneroom://com.community.oneroom?type=/movie/detail&id=<SubjectId>` (launches catalog detail screen).
*   **Activity Detail**: `oneroom://com.community.oneroom?type=/ab/detail&id=<ActivityId>&channel=push`
*   **Game Center**: `oneroom://com.community.oneroom?type=/commercial/gamecenter`
*   **Points / Rewards Dashboard**: `oneroom://member/adtask` or `oneroom://com.community.oneroom?type=/download/panel_activity`
*   **Section Header 'All >' Navigation (`moviebox://`)**:
    *   Full Top 100 Leaderboards: `moviebox://home/rank_all?tabId={id}&rankingListId={id}` (opens `RankAllActivity` -> `/wefeed-mobile-bff/tab/ranking-list`)
    *   Curated Thematic Grid: `moviebox://home/operate_more?tabId={id}&tabCode={code}` (opens `OperateActivity` -> `/wefeed-mobile-bff/operating-module/item-list`)
*   **Tab Navigation Override**:
    *   Home Tab: `oneroom://com.community.oneroom?type=/main/tab&bottomTab=home`
    *   Top Tab Target: `oneroom://com.community.oneroom?type=/main/tab&bottomTab=home&topTab=<TabName>`
    *   Index Selection: `oneroom://com.community.oneroom?type=/main/tab&tabIndex=0`
*   **Search Overlay Launcher**: `oneroom://com.community.oneroom?type=/search/activity/search_manager&type=3`

---

## 22. BuzzBox Group Orchestration APIs (Complete Mapping)

*   **Create Group**: `POST /wefeed-mobile-bff/group/create`
*   **Check Group Existence**: `GET /wefeed-mobile-bff/group/exist`
*   **Get Group Details**: `GET /wefeed-mobile-bff/group/get`
*   **Join Group Session**: `POST /wefeed-mobile-bff/group/join`
*   **Leave Group Session**: `POST /wefeed-mobile-bff/group/leave`
*   **Get Nearby Active Groups**: `GET /wefeed-mobile-bff/group/list/nearby`
*   **Search Group Directory**: `GET /wefeed-mobile-bff/group/list/search`
*   **Get Group Categories**: `GET /wefeed-mobile-bff/group/list/class`
*   **Global Group Rankings**: `GET /wefeed-mobile-bff/group/rank`
*   **Update Group Metadata**: `POST /wefeed-mobile-bff/group/update`
*   **Report Group Visit**: `POST /wefeed-mobile-bff/group/visit`

---

## 23. Local P2P Wi-Fi Media Transfer System

Used to share downloaded movies offline between nearby devices running the native player client.

*   **P2P Transfer Actions**:
    *   Host Server Initialization: `POST /client/notifyServerCreate`
    *   File Payload Transfer handshake: `GET /client/fetchFile` (or `fetchFile?file=`)
    *   Transfer Session Completion: `POST /client/notifyServerSendComplete`
    *   Queue Status List: `GET /client/getTransferFilesList`
    *   Transfer Task Finished: `POST /client/notifyFileTaskFinish`
    *   Task Error Notification: `POST /client/notifyFileTaskError`
    *   Client Closed Signal: `POST /client/notifyClientClose`
*   **Wi-Fi P2P Socket Setup**:
    *   Create Network Socket: `POST /transfer/wifi_create`
    *   Connect to Socket: `POST /transfer/wifi_connect`
    *   Sync Status: `GET /transfer/status`

---

## 24. E-Learning & Course Platform APIs

Endpoints managing the educational section vertical and playlists:
*   **Add Educational Course**: `POST /wefeed-mobile-bff/learning/add-course`
*   **My Enrolled Courses**: `GET /wefeed-mobile-bff/learning/my-course`
*   **Category Filter Options**: `GET /wefeed-mobile-bff/learning/prefer-options`
*   **Save Learning Preferences**: `POST /wefeed-mobile-bff/learning/submit-prefer`
*   **List Courses**: `GET /edu/courseList`
*   **Course Watch History**: `GET /edu/history`

---

## 25. Auxiliary SDK & Integration Hosts

These hosts support underlying monetization, analytics, and dynamic configuration setups:
*   **Configuration & Ads Dispatch**: `https://api.eagllwin.com` (and `https://api.test.eagllwin.com`)
*   **Mini-App Platform CDN**: `https://api.byte-app.com` (and `https://api-static.byte-app.com`)
*   **Auth Support Handshake**: `https://api.sunnbird.com`
*   **Telemetry Analytics Upload**: `https://api16-access-ttp.tiktokpangle.us`
*   **Dynamic Asset Repositories**: `https://app-oss.byte-app.com`
    *   *Smali Class*: `Lcom/transsion/api/gateway/config/b;` (Gateway dynamic configurations setup)
*   **MiniApp European Edge CDN**: `https://transsion-miniapp-android-cdn.oss-eu-central-1.aliyuncs.com`
*   **Transsion OneID user tracking/identity platform**: `https://ire-oneid.shalltry.com`
    *   *Smali Class*: `Lcom/transsion/base/infras_config/a;` (Infrastructure configuration init)
*   **Web Search & Video Downloader Service**: `https://m.mvbrowse.com`
    *   *Smali Class*: `Lcom/transsion/lib_web/download_render/data/config/ConfigData;`
*   **Game Center Integration BFF**: `https://api.ahagamecenter.com/bff/game.moviebox` (and `https://tapi.ahagamecenter.com`)
    *   *Smali Class*: `Lcom/transsion/mb/config/manager/ConfigBean;`

---

## 26. Emulator & Sandbox Detection Mechanics

To protect request endpoints and restrict usage to official physical devices, the application implements multi-layered environment checks.

### **I. QEMU and Hypervisor File Probing**
The application scans for virtual hardware signatures and standard debug layers inside the Android system directories:
*   **Daemon Port check:** `/dev/socket/qemud` (Checks for the QEMU messaging socket).
*   **Virtual Malloc Debug Library:** `/system/lib/libc_malloc_debug_qemu.so` (Flags the presence of emulator-specific memory allocation trackers).
*   **CPU Information Probes:** Parses `/proc/cpuinfo` and `/sys/devices/system/cpu/` to identify generic x86 architectures or hypervisor details.

### **II. Device Property & Hardware Analysis (`com.transsion.athena`)**
The telemetry engine (`com.transsion.athena.taaneh.athena`) validates physical parameters:
*   **Serial Number Verification:** Queries `Build.getSerial()` (or `Build.SERIAL` on API < 26) and falls back to reflection:
    ```java
    Class<?> cls = Class.forName("android.os.SystemProperties");
    String serial = (String) cls.getMethod("get", String.class).invoke(cls, "ro.serialno");
    ```
    If `ro.serialno` is null, empty, or equals `"unknown"`, it triggers sandbox warnings.
*   **Network Provider Verification:** Queries `telephonyManager.getSimOperator()` and active cell towers (`getAllCellInfo()`). The absence of real base station identity flags an emulated environment.

### **III. root Status Checks**
Since most developer emulators are rooted, the app searches for active superuser binary paths:
*   `/data/local/su`
*   `/system/bin/su`
*   `/system/xbin/su`
*   `/system/app/Superuser.apk`

### **IV. Consequences of Sandbox/Emulator Detection**
When the application identifies that it is running inside an emulator or virtual container, it enforces a locking sequence:
1.  **Request Signature Invalidation:** Standard telemetry and API requests fail validation at the remote API Gateway (`api6.aoneroom.com`) because the system properties and carrier variables compiled in headers do not match realistic physical devices.
2.  **Redirection to `NotAvailableActivity`:** On launch or playback request failure, the app routes the user to `com.transsion.subroom.activity.NotAvailableActivity` displaying a geofence error (`"Not Available in current region"`).
3.  **Application Process Termination:** A background coroutine (`NotAvailableActivity$welcomeMovieBox$1`) is invoked, sleeping for 2 seconds before executing:
    ```java
    Process.killProcess(Process.myPid());
    System.exit(0);
    ```

### **V. Developer Bypass Easter Egg & Laboratory Settings**
Tapping the `"Not Available"` text on the lockout screen **10 times** opens a secret password verification dialog (`LabPwdDialog`).

#### **1. Password Cryptographic Verification**
The dialog implements verification using a hardcoded MD5 target hash and salt:
*   **Salt:** `-321`
*   **Target MD5:** `031A68C3912D796E235A72EE0BF89C16`

The validation logic calculates:
```java
MD5(userInput.toLowerCase() + SALT) == TARGET_MD5
```
Decryption of the hash resolves the salted input to `"or666-321"`. Consequently, the raw developer bypass password is **`or666`**.

#### **2. Local Sandbox Override variables (MMKV)**
Once the password is correct, the application bypasses regional and emulator verification by writing custom carrier variables directly into local **MMKV** key-value storage:
```java
MMKV mmkvC = mg.a.f66344a.c();
if (mmkvC != null) {
    mmkvC.putString("sp_code", "90101").commit(); // Custom Test MCC
    mmkvC.putString("custom_local_iso", "us").commit(); // Country ISO
    mmkvC.putString("custom_local_country", "United States").commit();
    mmkvC.putString("custom_country_code", "1").commit();
}
```

#### **3. Regional Carrier Simulation (`MccActivity`)**
Entering the correct password also unlocks access to `com.transsion.usercenter.laboratory.MccActivity`. This activity allows testers to override carrier/region parameters manually:
*   Selecting any country from the RecyclerView updates the local MMKV configurations (`sp_code`, `custom_local_iso`, `custom_local_country`, `custom_country_code`) to simulate the corresponding mobile network carrier (e.g., setting `sp_code` to `"310"` to mimic a US SIM).
*   During subsequently initiated API handshakes, the client retrieves these MMKV values to populate header fields such as `X-Client-Info`, bypassing the server-side geofencing and emulator validation controls.

### **VI. Verified Network Behaviors (HAR Analysis)**
Network trace audits verify the following API behaviors during bypassed states:
*   **Target Domains:**
    *   API Endpoint: `https://api.inmoviebox.com` (falls back to `https://apii.inmoviebox.com`)
    *   Graphic Assets: `https://pbcdn.aoneroom.com`
    *   Media CDN Streams: `https://macdn.hakunaymatata.com`
    *   Subtitles CDN: `https://cacdn.hakunaymatata.com`
*   **Bypassed Response (HTTP 200):**
    When the custom test MCC (`"sp_code":"90101"`) is applied to the headers, the endpoints return status `200 OK` allowing standard operations:
    *   `/wefeed-mobile-bff/vip/member/rights-check` returns `{"isPassed":true, "vipEnable":true}`.
    *   `/wefeed-mobile-bff/subject-api/season-info` successfully resolves the episode listings.
    *   `/wefeed-mobile-bff/subject-api/resource` returns the raw CDN URLs.

---

## 27. HTTPS Proxy & SSL Pinning Bypass Mechanics

To prevent sniffing, debugging, or tampering with API requests via tools like Burp Suite or Charles Proxy, the application implements environment checks at the OkHttp and XML configuration levels.

### **I. Proxy Restrictions & Decryption Protection**
By default in production builds, the app prevents standard proxy interception:
1.  **Forced direct Connection (`Proxy.NO_PROXY`):**
    During client building in `kg.c`, unless the debug proxy state is toggled, the app sets:
    ```java
    clientBuilder.proxy(Proxy.NO_PROXY);
    ```
    This completely ignores system Wi-Fi proxy settings and global ADB proxies, forcing direct TCP connections.
2.  **System-Only trust anchors (`network_security_config.xml`):**
    The app configures `<certificates src="system" />` as the only trusted anchor for `aoneroom.com` domains. Outgoing requests routed through a user CA certificate (e.g., Burp Suite's CA) fail with `SSLHandshakeException`.

### **II. Developer Proxy Bypass Mechanics**
Developers and testers can bypass these restrictions using the built-in laboratory:
1.  **Host Mocking Dialog (`LabHttpHostDialog`):**
    Unlocking the lab allows access to the host settings dialog. Entering a domain or IP (such as a Burp Suite listener) writes the value to MMKV key **`mock_host_key`**.
2.  **URL Overwrite Engine (`CacheIpPool`):**
    During request formulation, the resolution pool checks for the presence of the mock key:
    ```java
    String mockHost = mmkv.getString("mock_host_key", "");
    if (!TextUtils.isEmpty(mockHost)) {
        CacheIpPool.e = mockHost;
    }
    ```
    All subsequent API calls are rewritten dynamically as `https://[mockHost]/[path]` to redirect traffic to the debug listener.
3.  **Debug CA trust anchor:**
    The network configuration contains a debug override directive:
    ```xml
    <debug-overrides>
        <trust-anchors>
            <certificates overridePins="true" src="user" />
        </trust-anchors>
    </debug-overrides>
    ```
    Repackaging the app with `android:debuggable="true"` in the `AndroidManifest.xml` forces Android to trust user store CA certificates (like Burp CA) and allows decrypters to capture the TLS traffic.

---

## 28. Embedded H5 & Offline Caching (Instant Loading & Bundle Integrity)

To optimize load times and ensure offline usability for interactive components (such as Game Center H5 mini-games or Welfare Center reward tasks), the application implements a pre-fetching and caching architecture.

### I. Caching Manifest Format
The pre-fetch engine queries CDN configurations containing bundle descriptions in the following format:
*   **Endpoint Path:** `https://infra-static.aoneroom.com/embedding/[yyyy]/[mm]/[dd]/[md5].json`
*   **JSON Structure:**
    ```json
    {
      "files": [
        "https://infra-static.aoneroom.com/games/cricket/index.html",
        "https://infra-static.aoneroom.com/games/cricket/main.js"
      ],
      "filteredResources": [
        { "url": "https://ezjobsbangla.com/favicon.ico", "type": "other" }
      ],
      "bundleHash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "failedResources": []
    }
    ```

### II. Dynamic Discovery & Manifest Loading
1.  **H5 Targets List:** The client requests `/wefeed-mobile-bff/activity/embedded-h5-list/v2` to receive active H5 applications and campaigns.
2.  **Manifest Fetching:** For each target, the background download worker retrieves its corresponding manifest file from the CDN.
3.  **Local Storage Caching:**
    *   Assets specified in `files` are downloaded and stored locally in `/offline_cache` or `/net_cache`.
    *   The worker computes the checksum of the package and verifies it against the `bundleHash` to prevent MITM tampering or corrupted file runs.
4.  **Zero-Latency Native Execution:** When the user triggers an H5 deep-link (e.g., `oneroom://h5_game?url=...`), the WebView interceptor redirects network requests for the assets to the local cache directory, loading the page instantly even when offline.









