# MovieBox Pro - Official API & Protocol Documentation

This document outlines the internal communication protocol, authentication handshake, and endpoint structure of the official MovieBox Pro Android application (v16.2.1), discovered via deep-decompilation and traffic analysis.

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
*   **External Subtitles**: `GET /wefeed-mobile-bff/subject-api/get-ext-captions`
    *   *Params*: `resourceId`, `subjectId`, `episode`
    *   *Notes*: Returns high-quality CloudFront-signed `.srt` tracks.

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

## 3. The Authentication Handshake (Regional Escalation)

MovieBox utilizes a multi-phase resolution strategy to bypass regional geofencing and copyright-restricted mirrors (especially for Hindi/Hindi-Dubbed titles).

### **Phase 1: Carrier 301 Escalation (The "Legacy Link")**
For titles that return `code: 407` (Restricted) or empty `streamList` on primary clusters, the app falls back to:
*   **Endpoint**: `POST /index/video/v_detail`
*   **Payload**: `{'subjectId': ID, 'carrier': '301', 'quality': '720p'}`
*   **Logic**: This bypasses the BFF layer and hits the legacy resolution engine, which often yields raw MP4 mirrors that are geofence-ignorant.

### **Phase 2: CloudFront Signed Cookies**
Regional DASH manifests (e.g., `sacdn2.hakunaymatata.com`) require a three-part CloudFront signature passed via the `Cookie` header:
1.  `CloudFront-Policy`
2.  `CloudFront-Signature`
3.  `CloudFront-Key-Pair-Id`
**CRITICAL**: These must be preserved with exact whitespace and semicolons. Corruption of these tokens results in an immediate 403 Forbidden.

### **Phase 3: GSLB (Global Server Load Balancing) Redirect**
The app performs a HEAD request (Handshake) to the CDN before playback. This triggers the issuance of a `signCookie` session token which validates the player's IP against the temporary media URL.

---

## 4. Internal Secrets (Static)
Discovered via `AndroidManifest.xml` and Smali string decryption.
*   **Gateway Secret**: `76iRl07s0xSN9jqmEWAt79EBJZulIQIsV64FZr2O` (Used for sign calculation in some clusters).

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
*   `/wefeed-mobile-bff/subject-api/search-rank`: High-conversion search suggestions.
*   `/wefeed-mobile-bff/subject-api/topic-list`
*   `/wefeed-mobile-bff/subject-api/trending/v2`
*   `/wefeed-mobile-bff/subject-api/want-to-see`

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

### **VIP & Membership**
*   `GET /wefeed-mobile-bff/vip/member/detail`: Check subscription status and expiry.
*   `GET /wefeed-mobile-bff/vip/member/rights-check`: Validates if the user can stream 4K/1080p.

---

## 8. Category & Vertical Feed Analysis

The application uses a modular category-based system to populate its vertical tabs.

### **Primary Endpoint: Home Category List**
*   **Route**: `POST /home/v2/get-list`
*   **Data Payload**: `{"categoryId": <ID>, "page": <PAGE>, "pageSize": 24}`

### **Category ID Mapping**
| Section Name | Category ID | Tab Code | Description |
| :--- | :--- | :--- | :--- |
| Trending | 1 | Trending | Hot/Popular feed |
| Movie | 2 | Movie | Feature films |
| Education | 3 | Education | Courses and tutorials |
| Music | 4 | Music | Music videos and tracks |
| TV/Series | 5 | TVshow | Television shows and series |
| Anime | 8 | Animation | Animation and Anime content |
| Game | 11 | Game | Gaming related content |
| ShortTV | 13 | ShortTV_Discover | Short-form vertical video series |
| Asian | 18 | KDrama | K-Dramas and Asian series |
| Western | 19 | WesternTv | US/UK and International series |
| Kids | 23 | Kids | Children's content |
| Nollywood | 28 | Nollywood | Regional/African content |
| BuzzBox | 30 | Community | Social community/forum feed |

### **Summary of Home Feed Components**
| Component | Endpoint | Method |
| :--- | :--- | :--- |
| **Carousel** | `/subject-api/daily-movie-rec` | POST |
| **Discover** | `/wefeed-mobile-bff/subject-api/top-rec` | POST |
| **Trending** | `/wefeed-mobile-bff/subject-api/trending/v2` | POST |
| **Rankings** | `/wefeed-mobile-bff/tab/ranking-list` | GET |

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
*   **Primary Partner**: `sportslivetoday.com`
*   **Integration Method**: Custom Internal WebView.
*   **Usage**: Surfaced via Top-level banners for major events (Cricket, Football).

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
```

### **Native Handling**
*   **Activity**: Launched via `com.community.oneroom.H5GameActivity`.
*   **Rendering**: Uses a specialized WebView with **WebGL/Canvas Hardware Acceleration** enabled.
*   **Deep Link**: Internal banners use `oneroom://h5_game?url=<URL>&orientation=1`.
*   **User Persistence**: The user's `session_id` is passed as a query parameter or cookie to the H5 game to enable leaderboards and cross-device score syncing.
