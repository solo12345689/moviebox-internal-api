from fastapi import FastAPI, HTTPException, Query, Response, Cookie, Request
from fastapi.responses import StreamingResponse
import httpx
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict
from pydantic import BaseModel
import uvicorn
import os
import subprocess
import base64
import json
import asyncio
import logging
import uuid
import re
from urllib.parse import quote
from moviebox_api import MovieBoxClient, MovieBoxAuth, MovieBoxContent, MovieBoxStream, MovieBoxUser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MovieBox Unofficial API Backend")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Multi-session management
# session_id -> {auth, client, content, stream, user}
sessions: Dict[str, Dict] = {}

def get_session(session_id: Optional[str] = None):
    # Check if session exists
    if session_id and session_id in sessions:
        return sessions[session_id]
        
    # Create new session
    sid = str(uuid.uuid4())
    auth = MovieBoxAuth()
    client = MovieBoxClient(auth=auth)
    sessions[sid] = {
        "id": sid,
        "auth": auth,
        "client": client,
        "content": MovieBoxContent(client),
        "stream": MovieBoxStream(client),
        "user": MovieBoxUser(client)
    }
    logger.info(f"Created new session: {sid}")
    return sessions[sid]

class LoginRequest(BaseModel):
    account: str
    password: str
    authType: int = 1

class RegisterRequest(BaseModel):
    account: str
    password: str
    otp: str
    authType: int = 1

class OtpRequest(BaseModel):
    account: str
    authType: int = 1
    type: int = 1 # 1: Register, 2: Login

@app.post("/request-otp")
def request_otp(req: OtpRequest, session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    res = s["client"].request_otp(req.account, req.authType, req.type)
    if res["status"] == "error":
        raise HTTPException(status_code=400, detail=res["message"])
    return res

@app.post("/login")
def login(req: LoginRequest, response: Response, session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    res = s["client"].login(req.account, req.password, req.authType)
    if res["status"] == "error":
        raise HTTPException(status_code=400, detail=res["message"])
    
    # Always set/refresh the session cookie on login
    response.set_cookie(
        key="session_id", 
        value=s["id"], 
        httponly=True, 
        samesite="lax",
        max_age=3600 * 24 * 30 # 30 days
    )
    return res

@app.post("/register")
def register(req: RegisterRequest, session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    res = s["client"].register(req.account, req.password, req.otp, req.authType)
    if res["status"] == "error":
        raise HTTPException(status_code=400, detail=res["message"])
    return res

@app.post("/logout")
def logout(response: Response, session_id: Optional[str] = Cookie(None)):
    if session_id in sessions:
        sessions[session_id]["client"].logout()
        del sessions[session_id]
    response.delete_cookie("session_id")
    return {"status": "success"}

@app.get("/user-info")
def get_user_info(response: Response, session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    
    # If no session_id was provided, set the newly created one
    if not session_id:
        response.set_cookie(key="session_id", value=s["id"], httponly=True, samesite="lax")

    if not s["auth"].is_logged_in:
        return {"logged_in": False, "mode": "Guest Access", "session_id": s["id"]}
        
    return {
        "logged_in": True,
        "mode": "Official Account", 
        "user": s["auth"].user_info,
        "session_id": s["id"]
    }

def map_actor(actor: dict):
    avatar = actor.get("avatarUrl") or actor.get("avatar") or actor.get("photo") or actor.get("poster") or ""
    if isinstance(avatar, dict): avatar = avatar.get("url") or ""
    if isinstance(avatar, str) and avatar.startswith("//"): avatar = "https:" + avatar
    return {
        "name": actor.get("name") or actor.get("actorName") or "Unknown",
        "role": actor.get("character") or actor.get("role") or "Cast",
        "avatar": avatar
    }

def map_room(src: dict):
    """Maps Community/Room data to local format."""
    return {
        "id": str(src.get("groupId") or src.get("id")),
        "name": src.get("name") or "Community Room",
        "title": src.get("name") or "Community Room",
        "avatar": src.get("cover", {}).get("url") if isinstance(src.get("cover"), dict) else src.get("avatar") or "",
        "description": src.get("description") or "",
        "members": src.get("userCount") or 0,
        "posts": src.get("postCount") or 0,
        "tags": src.get("tags") or []
    }

def map_item(src: dict, depth: int = 0):
    if "subject" in src and isinstance(src["subject"], dict):
        item = src["subject"]
    else:
        item = src

    sid = str(item.get("subjectId") or item.get("id") or "")
    # Title mapping: favor specific names, then check wrappers
    title = (
        item.get("title") or 
        item.get("name") or 
        item.get("subjectName") or 
        item.get("subject_name") or
        item.get("categoryName") or
        item.get("content") or 
        item.get("keyword") or
        item.get("keywordName") or
        item.get("itemName") or
        item.get("show_name") or
        item.get("showTitle") or
        item.get("titleName") or
        item.get("title_en") or
        item.get("tag") or
        item.get("label") or
        item.get("extra") or
        item.get("subtitle") or
        item.get("tabName") or
        item.get("tab_name") or
        item.get("searchName") or
        item.get("promotionName") or
        src.get("title") or
        src.get("name") or
        src.get("content") or
        src.get("keyword") or
        src.get("label") or
        "Unknown"
    )
    
    # Final effort: try to infer from deepLink if still unknown
    dlink = str(item.get("deepLink") or src.get("deepLink") or "")
    action_type = "movie" # Default
    category_id = None
    
    if dlink:
        if "/home/category" in dlink:
            action_type = "category"
            if "categoryType=" in dlink:
                category_id = dlink.split("categoryType=")[1].split("&")[0]
        elif "/playlist/detail" in dlink:
            action_type = "playlist"
        elif "/movie/detail" in dlink:
            action_type = "movie"

    if title == "Unknown":
        if action_type == "category" and category_id:
             title = f"Category {category_id}" # Still unknown, but better than "Unknown"
        pass
    
    poster = item.get("poster")
    poster_url = ""
    if isinstance(poster, dict): poster_url = poster.get("url")
    elif isinstance(poster, str): poster_url = poster
    
    if not poster_url:
        cover = item.get("cover")
        poster_url = cover.get("url") if isinstance(cover, dict) else cover

    # Aggressive Deep Search for Images
    if not poster_url:
        img_terms = ["image", "img", "thumb", "thumbnail", "poster", "cover", "icon", "banner", "pic", "picture"]
        # Priority 1: Check standard nested objects
        for term in img_terms:
            val = item.get(term)
            if isinstance(val, dict) and val.get("url"):
                poster_url = val.get("url")
                break
            elif isinstance(val, str) and (val.startswith("http") or val.startswith("//")):
                poster_url = val
                break
        
        # Priority 2: Check keys with _url or _path suffix
        if not poster_url:
            for k, v in item.items():
                if any(t in k.lower() for t in img_terms) and isinstance(v, str) and (v.startswith("http") or v.startswith("//")):
                    poster_url = v
                    break

    if not poster_url:
        hp = item.get("horizontalPoster") or item.get("horizontalCover")
        poster_url = hp.get("url") if isinstance(hp, dict) else hp

    if not poster_url:
        # Final fallback - check for a banner object
        banner = item.get("banner")
        if isinstance(banner, dict):
            poster_url = banner.get("image", {}).get("url") or banner.get("url")

    if isinstance(poster_url, str) and poster_url.startswith("//"):
        poster_url = "https:" + poster_url

    score = item.get("imdbRatingValue") or item.get("imdbRate") or item.get("starRating") or item.get("score") or "N/A"
    
    # Year mapping fix using official releaseDate field
    release_date = item.get("releaseDate") or item.get("releaseTime") or item.get("year") or ""
    display_year = release_date[:4] if release_date and len(release_date) >= 4 else "N/A"

    runtime = item.get("duration") or item.get("runtime") or item.get("minute")
    if isinstance(runtime, int): runtime = f"{runtime}m"

    return {
        "subjectId": sid,
        "id": sid,
        "title": title,
        "cover": poster_url,
        "poster": poster_url,
        "score": str(score),
        "releaseTime": display_year,
        "subjectType": item.get("subjectType") or item.get("type") or item.get("subject_type") or (2 if item.get("episodeCount") or item.get("seasonCount") else 1),
        "runtime": runtime,
        "season": item.get("season"),
        "episode": item.get("episode") or item.get("ep"),
        "seeTime": item.get("seeTime"),
        "seenStatus": item.get("seenStatus"),
        # Map ALL variations of favorite/like status across ALL regional API versions
        # Standard: isFavorite, isLike
        # Legacy: collected, collectedStatus, is_favorite, fav, is_fav, isCollect
        "likeStatus": 1 if (
            item.get("isFavorite") == 1 or 
            item.get("is_favorite") == 1 or
            item.get("fav") == 1 or
            item.get("is_fav") == 1 or
            item.get("isLike") == 1 or 
            item.get("is_like") == 1 or
            item.get("wantToSee") == 1 or
            item.get("likeStatus") == 1 or
            item.get("collected") == 1 or
            item.get("isCollect") == 1 or
            item.get("collectedStatus") == 1 or
            str(item.get("likeType")) == "1" or
            item.get("isCollect") is True or
            item.get("isFavorite") is True
        ) else 0,
        "description": item.get("description") or "",
        "actionType": action_type,
        "categoryId": category_id,
        "deepLink": dlink
    }

@app.get("/home")
def get_home(page: int = 1, session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    try:
        # Category ID 1 corresponds to "Trending", which is the primary "Home" feed in the app.
        res = s["content"].get_categories(category_id=1, page=page)
        data = res.get("data") or {}
        items = data.get("list") or data.get("items") or data.get("subjects") or []
        
        # We can format it identically to all other robust sections we built
        return {"code": 0, "data": {"list": format_tab_sections(items)}}
    except Exception as e:
        logger.error(f"Home error: {e}")
        return {"code": 500, "message": str(e), "data": {"list": []}}

@app.get("/anime")
def get_anime(page: int = 1, session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    try:
        res = s["content"].get_categories(category_id=8, page=page)
        data = res.get("data") or {}
        items = data.get("list") or data.get("items") or data.get("subjects") or []
        return {"code": 0, "data": {"list": format_tab_sections(items)}}
    except Exception as e:
        logger.error(f"Anime error: {e}")
        return {"code": 1, "data": []}

@app.get("/rankings")
def get_rankings(response: Response, tabId: int = 1, session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    # Ensure session persists even for guest GET requests
    response.set_cookie(key="session_id", value=s["id"], httponly=True, samesite="lax")
    # The official path from Smali class zm/c is /wefeed-mobile-bff/tab/ranking-list
    variants = ["/wefeed-mobile-bff/tab/ranking-list", "/tab/ranking-list", "/subject-api/ranking-list"]
    
    for v in variants:
        try:
            res = s["content"].get_rankings(v, tab_id=tabId)
            logger.info(f"RANKINGS RAW ({v}): {json.dumps(res)}")
            data = res.get("data")
            if not data: continue
            
            formatted = []
            # RankAllData format: 'subjects' contains the items
            if "subjects" in data and isinstance(data["subjects"], list):
                items = data["subjects"]
                if items:
                    formatted.append({"title": "Top Rankings", "items": [map_item(i) for i in items[:10]]})
            else:
                lists = data.get("lists") or data.get("list") 
                if isinstance(lists, list):
                    for l in lists:
                        if not isinstance(l, dict): continue
                        title = l.get("name") or l.get("title") or "Rankings"
                        items = l.get("items") or l.get("list") or []
                        if items:
                            formatted.append({"title": title, "items": [map_item(i) for i in items[:10]]})
            
            if formatted: return {"code": 0, "data": formatted}
        except Exception as e:
            logger.error(f"Error parsing rankings variant {v}: {e}")
            continue
        
    return {"code": 0, "data": []}

@app.get("/discovery")
def get_discovery(session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    try:
        res = s["content"].get_discovery()
        logger.info(f"DISCOVERY RAW: {json.dumps(res)[:1000]}")
        data = res.get("data") or {}
        items = data.get("list") or data.get("items") or []
        return {"code": 0, "data": [map_item(i) for i in items[:20]]}
    except Exception as e:
        logger.error(f"Discovery error: {e}")
        return {"code": 1, "data": []}

@app.get("/trending")
def get_trending(session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    try:
        res = s["content"].get_trending()
        logger.info(f"TRENDING RAW: {json.dumps(res)[:1000]}")
        data = res.get("data") or {}
        items = data.get("list") or data.get("items") or []
        return {"code": 0, "data": [map_item(i) for i in items[:20]]}
    except Exception as e:
        logger.error(f"Trending error: {e}")
        return {"code": 1, "data": []}

@app.get("/movies")
def get_movies(page: int = 1, session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    try:
        res = s["content"].get_categories(category_id=2, page=page)
        data = res.get("data") or {}
        items = data.get("list") or data.get("items") or data.get("subjects") or []
        return {"code": 0, "data": {"list": format_tab_sections(items)}}
    except Exception as e:
        logger.error(f"Movies error: {e}")
        return {"code": 1, "data": []}

def format_tab_sections(items: list):
    sections = []
    
    # Catch-all if it's already a direct movie list (no inner sections)
    is_direct_movies = True
    for row in items:
        if isinstance(row, dict) and (row.get("list") or row.get("items") or row.get("subjects") or row.get("movieList") or row.get("customData") or row.get("banner")):
            is_direct_movies = False
            break
            
    if is_direct_movies and items:
         mapped = [map_item(m) for m in items if m.get("subjectId") or m.get("id")]
         if mapped: return [{"title": "Content", "items": mapped}]

    for row in items:
        if not isinstance(row, dict): continue
        title = row.get("title") or row.get("name") or "Section"
        
        inner = []
        if isinstance(row.get("list"), list) and row.get("list"): inner = row.get("list")
        elif isinstance(row.get("items"), list) and row.get("items"): inner = row.get("items")
        elif isinstance(row.get("subjects"), list) and row.get("subjects"): inner = row.get("subjects")
        elif isinstance(row.get("movieList"), list) and row.get("movieList"): inner = row.get("movieList")
        elif isinstance(row.get("customData"), dict) and isinstance(row["customData"].get("items"), list) and row["customData"]["items"]:
            inner = row["customData"]["items"]
        elif isinstance(row.get("banner"), dict) and isinstance(row["banner"].get("banners"), list) and row["banner"]["banners"]:
            inner = row["banner"]["banners"]
            
        real_movies = []
        for i in inner:
            if not isinstance(i, dict): continue
            if isinstance(i.get("subject"), dict):
                 real_movies.append(i["subject"])
            elif i.get("subjectId") or i.get("id"):
                 real_movies.append(i)
        
        if real_movies:
            mapped = [map_item(m) for m in real_movies]
            sections.append({
                "title": title,
                "type": row.get("subjectType") or row.get("type") or "SUBJECTS_MOVIE",
                "items": mapped
            })
    return sections

@app.get("/short-tv")
def get_short_tv(page: int = 1, session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    try:
        res = s["content"].get_categories(category_id=13, page=page)
        data = res.get("data") or {}
        items = data.get("list") or data.get("items") or data.get("subjects") or []
        return {"code": 0, "data": {"list": format_tab_sections(items)}}
    except Exception as e:
        logger.error(f"ShortTV error: {e}")
        return {"code": 1, "data": []}

@app.get("/kids")
def get_kids(page: int = 1, session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    try:
        res = s["content"].get_categories(category_id=23, page=page)
        data = res.get("data") or {}
        items = data.get("list") or data.get("items") or data.get("subjects") or []
        return {"code": 0, "data": {"list": format_tab_sections(items)}}
    except Exception as e:
        logger.error(f"Kids error: {e}")
        return {"code": 1, "data": []}

@app.get("/education")
def get_education(page: int = 1, session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    try:
        res = s["content"].get_categories(category_id=3, page=page)
        data = res.get("data") or {}
        items = data.get("list") or data.get("items") or data.get("subjects") or []
        return {"code": 0, "data": {"list": format_tab_sections(items)}}
    except Exception as e:
        logger.error(f"Education error: {e}")
        return {"code": 1, "data": []}

@app.get("/music")
def get_music(page: int = 1, session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    try:
        res = s["content"].get_categories(category_id=4, page=page)
        data = res.get("data") or {}
        items = data.get("list") or data.get("items") or data.get("subjects") or []
        return {"code": 0, "data": {"list": format_tab_sections(items)}}
    except Exception as e:
        logger.error(f"Music error: {e}")
        return {"code": 1, "data": []}

@app.get("/asian")
def get_asian(page: int = 1, session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    try:
        res = s["content"].get_categories(category_id=18, page=page)
        data = res.get("data") or {}
        items = data.get("list") or data.get("items") or data.get("subjects") or []
        return {"code": 0, "data": {"list": format_tab_sections(items)}}
    except Exception as e:
        logger.error(f"Asian error: {e}")
        return {"code": 1, "data": []}

@app.get("/western")
def get_western(page: int = 1, session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    try:
        res = s["content"].get_categories(category_id=19, page=page)
        data = res.get("data") or {}
        items = data.get("list") or data.get("items") or data.get("subjects") or []
        return {"code": 0, "data": {"list": format_tab_sections(items)}}
    except Exception as e:
        logger.error(f"Western error: {e}")
        return {"code": 1, "data": []}

@app.get("/nollywood")
def get_nollywood(page: int = 1, session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    try:
        # Reverting to tab-operating GET vertical for tabId 28
        res = s["content"].get_categories(category_id=28, page=page)
        if not isinstance(res, dict):
             return {"code": 1, "message": "Invalid response format", "data": {"list": []}}
        
        data = res.get("data") or {}
        items = data.get("list") or data.get("items") or data.get("subjects") or []
        
        # Log detected items to verify if we are getting Home content
        if items:
            sample = items[0].get('name') or items[0].get('title') or "Unknown"
            logger.info(f"Nollywood Detection: First item is '{sample}'")
            
        return {"code": 0, "data": {"list": format_tab_sections(items)}}
    except Exception as e:
        logger.error(f"Nollywood error: {e}")
        return {"code": 1, "message": str(e), "data": {"list": []}}

@app.get("/game")
def get_game(page: int = 1, session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    try:
        # Reverting to tab-operating GET vertical for tabId 11
        res = s["content"].get_categories(category_id=11, page=page)
        if not isinstance(res, dict):
             return {"code": 1, "message": "Invalid response format", "data": {"list": []}}
             
        data = res.get("data") or {}
        items = data.get("list") or data.get("items") or data.get("subjects") or []
        
        if items:
            sample = items[0].get('name') or items[0].get('title') or "Unknown"
            logger.info(f"Game Detection: First item is '{sample}'")
            
        return {"code": 0, "data": {"list": format_tab_sections(items)}}
    except Exception as e:
        logger.error(f"Game error: {e}")
        return {"code": 1, "message": str(e), "data": {"list": []}}

@app.get("/search-suggestions")
def get_search_suggestions(response: Response, q: Optional[str] = None, session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    # Ensure session persists even for guest GET requests
    response.set_cookie(key="session_id", value=s["id"], httponly=True, samesite="lax")
    try:
        if q:
            # If there's a query, use actual search logic for autocomplete suggestions
            res = s["content"].search(q, page=1)
            data = res.get("data", {})
            items = data.get("list") or data.get("items") or data.get("movie") or data.get("subjects") or []
        else:
            res = s["content"].get_search_suggestions()
            logger.info(f"SEARCH SUGGESTIONS RAW: {json.dumps(res)}")
            data = res.get("data") if isinstance(res, dict) else {}
            if not isinstance(data, dict):
                return {"code": 0, "data": []}
            items = data.get("list") or data.get("items") or data.get("movie") or data.get("subjects") or []
            
        suggestions = []
        for i in items:
            if isinstance(i, str):
                suggestions.append(i)
            elif isinstance(i, dict):
                suggestions.append(i.get("keyword") or i.get("title") or i.get("name"))
        
        return {"code": 0, "data": [s for s in suggestions if s]}
    except Exception as e:
        logger.error(f"Search suggestions error: {e}")
        return {"code": 0, "data": []}

@app.get("/search")
def search(q: str, page: int = 1, session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    try:
        res = s["content"].search(q, page=page)
        data = res.get("data", {})
        # Search API returns 'list' or 'items' depending on version/carrier
        items = data.get("list") or data.get("items") or res.get("list") or res.get("items") or []
        
        return {"code": 0, "data": {"items": [map_item(i) for i in items]}}
    except Exception as e:
        logger.error(f"Search failed for {q}: {e}")
        return {"code": 0, "data": {"items": []}}

@app.get("/rooms/recommend")
def get_rooms(page: int = 1, session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    try:
        res = s["content"].get_rooms(page=page)
        data = res.get("data") or {}
        items = data.get("list") or data.get("items") or []
        return {"code": 0, "data": [map_room(r) for r in items]}
    except Exception as e:
        logger.error(f"Rooms error: {e}")
        return {"code": 1, "data": []}

@app.get("/rooms/{room_id}")
def get_room_detail(room_id: str, session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    try:
        res = s["content"].get_room_detail(room_id)
        data = res.get("data") or {}
        return {"code": 0, "data": map_room(data)}
    except Exception as e:
        logger.error(f"Room detail error: {e}")
        return {"code": 1, "data": {}}

@app.get("/sports/live")
def get_sports_live(session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    try:
        # 1. Fetch live channels from MovieBox BFF
        res = s["content"].get_live_channels()
        data = res.get("data") or {}
        items = data.get("list") or data.get("items") or []
        channels = [map_item(c) for c in items]
        
        # 2. Append the specialized external aggregator link
        # This is for sportslivetoday integration
        channels.append({
            "id": "external_sports_aggregator",
            "title": "Live Sports Aggregator (Cricket/Football)",
            "name": "Live Sports Today",
            "type": "external_web",
            "url": "https://sportslivetoday.com/live/detail?id=3552262265162844888&sportType=cricket",
            "cover": "https://img.icons8.com/color/48/000000/cricket.png",
            "tag": "LIVE"
        })
        
        return {"code": 0, "data": channels}
    except Exception as e:
        logger.error(f"Sports live error: {e}")
        return {"code": 1, "data": []}

@app.get("/detail/{subject_id}")
def get_detail(subject_id: str, depth: int = 0, session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    res = s["content"].get_movie_detail(subject_id)
    data = res.get("data", {})
    
    is_collection = False
    items = []

    # 1. Check if it's a category ID (If standard detail fails or has no title)
    if not data or not (data.get("title") or data.get("name")):
        try:
           # Try as category
           cat_res = s["content"].get_categories(category_id=subject_id, page=1)
           cat_data = cat_res.get("data", {})
           items = cat_data.get("list") or cat_data.get("items") or cat_data.get("subjects") or []
           if items:
               is_collection = True
               # Synthesize a "Movie" object for the collection
               data = {
                   "subjectId": subject_id,
                   "title": f"Collection {subject_id}",
                   "isCollection": True,
                   "items": items
               }
        except: pass

    if not data: return {"code": 1, "msg": "Not found"}
    
    # Logic to force status sync: Check the actual list if cloud detail is stale
    try:
        wl_res = s["user"].get_watchlist(page=1, per_page=50) # Check first page of favorites
        wl_items = wl_res.get("data", {}).get("items") or wl_res.get("data", {}).get("list") or []
        for item in wl_items:
            if str(item.get("subject_id") or item.get("id") or item.get("subjectId")) == str(subject_id):
                data["isFavorite"] = 1 # Force it
                break
    except: pass

    # Existing field cross-check
    status_fields = ["isFavorite", "is_favorite", "fav", "is_fav", "collected", "isLike", "wantToSee", "likeStatus"]
    for f in status_fields:
        if f in res and f not in data:
            data[f] = res[f]

    # Fetch Community Post Count
    try:
        post_res = s["client"].request("GET", "/wefeed-mobile-bff/post/count/subject", params={"subjectId": subject_id})
        data["postCount"] = post_res.get("data", {}).get("count") or "0"
    except:
        data["postCount"] = "0"

    mapped = map_item(data, depth=depth)
    mapped["postCount"] = data.get("postCount", "0")
    mapped["isCollection"] = is_collection
    
    if is_collection and depth == 0:
        mapped["collectionItems"] = [map_item(i, depth=depth+1) for i in items[:24]]
        # Use first item's poster as collection poster
        if items and not mapped.get("poster"):
            first = map_item(items[0], depth=depth+1)
            mapped["poster"] = first.get("poster")
            mapped["cover"] = first.get("cover")

    raw_cast = data.get("staffList") or data.get("actorList") or []
    mapped["cast"] = [map_actor(a) for a in raw_cast]
    
    # Fetch Available Languages / Dubs (Consolidated)
    all_languages = []
    
    # 1. Check for Dubs list (Versions linked via different Subject IDs)
    raw_dubs = data.get("dubs") or []
    for dub in raw_dubs:
        all_languages.append({
            "id": None, 
            "subjectId": dub.get("subjectId"), 
            "name": dub.get("lanName") or "Custom Dub",
            "type": "dub"
        })
        
    # 2. Check for Resource Detectors (Tracks within the same/similar ID)
    try:
        det_res = s["client"].request('GET', '/wefeed-mobile-bff/subject-api/get', params={'subjectId': subject_id})
        detectors = (det_res.get('data') or {}).get('resourceDetectors') or []
        for d in detectors:
            # Avoid duplicates if we already have it link-wise
            d_name = d.get("name") or "Resource"
            all_languages.append({
                "id": d.get("resourceId"),
                "subjectId": subject_id, 
                "name": d_name,
                "type": "resource"
            })
    except:
        pass
        
    mapped["languages"] = all_languages
    return {"code": 0, "data": mapped}

@app.get("/episodes/{series_id}")
def get_episodes(series_id: str, session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    res = s["content"].get_episode_list(series_id)
    logger.info(f"EPISODES CLOUD RAW: {json.dumps(res)[:2000]}")
    data = res.get("data") or {}
    # Handle data wrapper vs top-level
    raw_seasons = data.get("seasons") or res.get("seasons") or []
    if not raw_seasons:
        # Check deep nested fields if first layer failed
        raw_seasons = data.get("seasonList") or data.get("list") or []
        
    mapped_seasons = []
    for s_raw in raw_seasons:
        num = s_raw.get("se") or s_raw.get("seasonNumber") or 1
        eps = []
        
        # Check all possible list/string fields for episodes
        for key in ["allEp", "epList", "episodeList", "episodes", "list", "items"]:
            pool = s_raw.get(key)
            if not pool: continue
            
            if isinstance(pool, str):
                for e_num in pool.split(","):
                    if e_num: eps.append({"episodeNumber": e_num, "title": f"Episode {e_num}", "id": f"{series_id}_{num}_{e_num}"})
            elif isinstance(pool, list):
                for item in pool:
                    if isinstance(item, dict):
                        en = item.get("ep") or item.get("episodeNumber") or item.get("episode_number")
                        if en: eps.append({"episodeNumber": str(en), "title": item.get("title") or f"Episode {en}", "id": f"{series_id}_{num}_{en}"})
                    else:
                        eps.append({"episodeNumber": str(item), "title": f"Episode {item}", "id": f"{series_id}_{num}_{item}"})
            
            if eps: break # Stop once we found a pool

        # FALLBACK: If no explicit pool found, but maxEp is set, generate sequence [1..maxEp]
        if not eps:
            max_ep = s_raw.get("maxEp") or s_raw.get("max_ep") or 0
            if isinstance(max_ep, str) and max_ep.isdigit(): max_ep = int(max_ep)
            if max_ep and isinstance(max_ep, int):
                for i in range(1, max_ep + 1):
                    eps.append({"episodeNumber": str(i), "title": f"Episode {i}", "id": f"{series_id}_{num}_{i}"})

        if eps:
            mapped_seasons.append({"seasonNumber": num, "episodes": eps})
    return {"code": 0, "data": {"seasons": mapped_seasons}}

@app.get("/stream/{subject_id}")
def get_stream(subject_id: str, season: int = 1, episode: int = 1, quality: Optional[str] = "720p", resource_id: Optional[str] = None, session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    # 0. Detect subject type to avoid se/ep for movies
    try:
        subject_detail = s["content"].get_movie_detail(subject_id).get("data") or {}
        is_movie = (str(subject_detail.get("subjectType") or subject_detail.get("type")) == "1")
    except: is_movie = False

    logger.info(f"RESOLVING STREAM: ID={subject_id} Type={'Movie' if is_movie else 'Series'} Resource={resource_id}")
    
    # If it's a movie, se and ep MUST be None for the official play-info API to respond correctly in some regions
    res_se = None if is_movie else season
    res_ep = None if is_movie else episode
    
    # PRE-FLIGHT: Force Carrier 301 for regional titles (fixes 407 restricted issues for guests)
    if not resource_id and int(subject_id) > 4000000000000000000:
        logger.info(f"Regional title detected by ID range. Escalating to Carrier 301 for {subject_id}")
        c_res = s["client"].request('POST', '/index/video/v_detail', data={'subjectId': subject_id, 'carrier': '301'})
        c_data = c_res.get("data")
        if isinstance(c_data, dict):
            c_st = c_data.get("streamList") or []
            if c_st:
                r3 = c_st[0]
                logger.info(f"CARRIER 301 RECOVERY SUCCESS: {r3.get('url')[:60]}...")
                # Deep cookie recovery from carrier response
                recovery_cookie = c_data.get("signCookie") or r3.get("signCookie") or c_res.get("signCookie") or ""
                return {
                    "code": 0,
                    "url": r3.get("url"),
                    "quality": r3.get("quality"),
                    "cookie": recovery_cookie,
                    "duration": r3.get("duration", 0),
                    "title": subject_detail.get("title", "")
                }
        else:
            logger.info(f"Carrier 301 returned non-dict data: {type(c_data)}")

    res = s["stream"].get_play_info(subject_id, season=res_se, episode=res_ep, resource_id=resource_id)
    data = res.get("data", {})
    streams = data.get("streamList") or data.get("streams") or []
    # signCookie can be in root, in data, or in the session cookies
    # FALLBACK: If all else fails, the signCookie is often just the user token
    global_cookie = res.get("signCookie") or data.get("signCookie") or s["client"].session.cookies.get("signCookie") or s["auth"].token
    logger.info(f"Phase 1 - Primary Result: {len(streams)} streams found (code: {res.get('code')}) (Cookie: {'YES' if global_cookie else 'NO'})")
    import requests
    
    # Silent Failover Logic - Mobile Handshake Enforcement
    working_stream = None
    working_cookie = None
    
    # Normalize quality for official API (expects lowercase)
    official_quality = quality.lower() if quality else "720p"
    
    # Try current stream list first (Strict Codec Enforcement)
    # Browsers generally FAIL to play H.265 (HEVC) or complex HEV1 DASH manifests.
    # We strictly prioritize H.264 (AVC) MP4 > HLS > (Anything else).
    
    def prioritize_h264(st):
        u = st.get("url", "").lower()
        if "h265" in u or "x265" in u or "hev1" in u: return 10 # Very low priority
        if ".mp4" in u: return 0  # Highest priority
        if ".m3u8" in u: return 1 # Good priority
        return 5 # DASH is risky but better than H265
    
    prioritized_streams = sorted(streams, key=prioritize_h264)

    for st in prioritized_streams:
        url = st.get("url")
        if not url: continue
        
        # FINAL BLOCKADE: If the only stream is H265, we must search other clusters
        if any(bad in url.lower() for bad in ["h265", "x265", "hev1"]):
            logger.info(f"Skipping H265/HEVC stream: browser will not play this ({url})")
            continue
            
        cookie = global_cookie or st.get("signCookie") or ""
        try:
            head_res = requests.head(url, headers={"User-Agent": "ExoPlayerLib/2.18.7", "Cookie": cookie}, timeout=3, verify=False)
            if head_res.status_code in [200, 206, 302]:
                working_stream = st
                working_cookie = cookie
                break
        except: continue
            
    # SILENT FALLBACK: Cloud Mirror -> Resource Mirror Rotation
    subtitles_source = data.get("subTitleList", [])
    
    # PROIRITY: Resource Mirrors (UGC/Dubs like eyosi_as_iam)
    if not working_stream:
        logger.info(f"Primary Cloud Offline for {subject_id}. Engaing Resource Mirror Rotation...")
        try:
            hdrs = {
                "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 13; SM-S918B Build/TP1A.220624.014)",
                "X-M-Version": "11.7.0"
            }
            
            # PHASE 1: Resource Discovery via Metadata (High Parity with Subtitles)
            r_ids = []
            try:
                det_res = s["client"].request('GET', '/wefeed-mobile-bff/subject-api/get', params={'subjectId': subject_id}, headers=hdrs)
                logger.info(f"Metadata Probe Result: {det_res.get('code')} - {len(det_res.get('data', {}).get('resourceDetectors', []))} detectors found")
                detectors = (det_res.get('data') or {}).get('resourceDetectors') or []
                for d in detectors:
                    if d.get('resourceId'): r_ids.append(d.get('resourceId'))
            except Exception as ex: 
                logger.error(f"Metadata Probe Crash: {ex}")

            # PHASE 2: Fallback to See-List (UGC Discoverability)
            if not r_ids:
                try:
                    res_list = s["client"].request('GET', '/wefeed-mobile-bff/subject-api/see-list-v2', params={'subjectId': subject_id, 'page': 1, 'pageSize': 20, 'seeType': 1}, headers=hdrs)
                    logger.info(f"See-List Probe Result: {res_list.get('code')}")
                    r_items = (res_list.get('data') or {}).get('items') or []
                    for item in r_items:
                        if item.get('id'): r_ids.append(item.get('id'))
                except: pass

            # PHASE 3: Iterative Recovery
            for r_id in r_ids:
                logger.info(f"Probing Resource: {r_id} for {subject_id}")
                # USE BOTH FULL AND ABBREVIATED PARAMS
                # ALSO PROBE WITHOUT QUALITY (UGC often fails if quality mismatch)
                p_params = {
                    'subjectId': subject_id, 
                    'resourceId': r_id
                }
                if not is_movie:
                    p_params.update({'se': season, 'ep': episode, 'season': season, 'episode': episode})
                
                # First attempt: With quality
                q_params = p_params.copy()
                q_params['quality'] = official_quality
                p_info = s["client"].request('GET', '/wefeed-mobile-bff/subject-api/play-info', params=q_params, headers=hdrs)
                p_data = p_info.get('data') or {}
                p_streams = p_data.get('streamList') or p_data.get('streams') or []
                
                # Second attempt: Without quality (Discovery mode)
                if not p_streams:
                    logger.info(f"Retrying probe {r_id} without quality constraint...")
                    p_info = s["client"].request('GET', '/wefeed-mobile-bff/subject-api/play-info', params=p_params, headers=hdrs)
                    p_data = p_info.get('data') or {}
                    p_streams = p_data.get('streamList') or p_data.get('streams') or []

                logger.info(f"Probe {r_id} Result: {len(p_streams)} streams recovered")
                if p_streams:
                    working_stream = p_streams[0]
                    
                    # PROACTIVE PING: Force a session handshake with the media CDN
                    if "hakunaymatata" in working_stream.get("url", ""):
                        try:
                            import requests
                            logger.info(f"Ping session for CDN handshake: {working_stream.get('url')[:60]}")
                            # Matches Android okhttp behavior: HEAD with timeout
                            requests.head(working_stream.get("url"), headers={"User-Agent": "ExoPlayerLib/2.19.1"}, timeout=3, cookies=s["client"].session.cookies)
                        except: pass

                    # DEEP CAPTURE: Check body, then individual stream, then session cookies, then fallback
                    working_cookie = (
                        p_info.get('signCookie') or 
                        p_data.get('signCookie') or 
                        working_stream.get('signCookie') or # EMBEDDED IN STREAM OBJECT (CRITICAL)
                        s["client"].session.cookies.get("signCookie") or 
                        global_cookie or ""
                    )
                    
                    # If still NO cookie for a protected CDN, we have a failover issue
                    if not working_cookie and "hakunaymatata" in working_stream.get("url", ""):
                        logger.warning("PROTECTED CDN DETECTED WITH NO COOKIE AFTER PING! Attempting session flush...")
                        working_cookie = s["client"].session.cookies.get("signCookie") or ""

                    subtitles_source = p_data.get("subTitleList", []) or subtitles_source
                    logger.info(f"RESOURCE MIRROR SUCCESS: Recovered stream via User-Resource {r_id} (Cookie: {'YES' if working_cookie else 'NO'})")
                    break
        except Exception as e:
            logger.warning(f"Resource Mirror Lookup Failed: {e}")

    # PROACTIVE AUTO-FAILOVER: Scan for HEVC/H.265 and trigger transcode 
    # Browser standard support is H.264 (AVC) and VP9/AV1.
    is_hevc = any("h265" in st.get("url", "").lower() or "x265" in st.get("url", "").lower() or "hev1" in st.get("url", "").lower() or "h.265" in st.get("url", "").lower() for st in streams)
    
    # We also check for 'hev1' codec signatures in manifest URLs if found
    h265_candidate = next((st for st in streams if any(bad in st.get("url", "").lower() for bad in ["h265", "x265", "hev1", "h.265"])), None)
    
    if is_hevc and h265_candidate:
        logger.info(f"Detected HEVC/H.265. Directly serving RAW stream for Native Player support...")
        working_stream = h265_candidate
        working_cookie = global_cookie or working_stream.get("signCookie") or ""

    # SECONDARY FALLBACK: API Cluster Rotation
    if not working_stream:
        logger.info(f"Entering Phase 4 Cluster Rotation for {subject_id}")
        
        clusters = [
            ("https://api6.aoneroom.com", "/wefeed-mobile-bff/subject-api/play-info"),
            ("https://api5.aoneroom.com", "/wefeed-mobile-bff/subject-api/play-info"),
            ("https://api-sin.aoneroom.com", "/wefeed-mobile-bff/subject-api/play-info"),
            ("https://v-ios.aoneroom.com", "/wefeed-mobile-bff/subject-api/play-info"),
            ("https://h5-api.aoneroom.com", "/wefeed-h5api-bff/subject/detail-rec"),
            ("https://h5.aoneroom.com", "/index/video/v_detail")
        ]
        
        hdrs = {
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 13; SM-S918B Build/TP1A.220624.014)",
            "X-M-Version": "11.7.0"
        }
        
        orig_base = s["client"].BASE_URL
        for cluster_url, endpoint in clusters:
            try:
                logger.info(f"ROTATING CLUSTER: {cluster_url} -> {endpoint}")
                s["client"].BASE_URL = cluster_url
                
                # Standard params
                pms = {'subjectId': subject_id, 'se': season, 'ep': episode, 'quality': official_quality}
                if "detail-rec" in endpoint:
                    pms["perPage"] = 12
                    pms["page"] = 1
                
                method = 'POST' if "v_detail" in endpoint else 'GET'
                
                fb_res = s["client"].request(method, endpoint, params=pms if method=='GET' else None, data=pms if method=='POST' else None, headers=hdrs)
                if not isinstance(fb_res, dict):
                    logger.warning(f"Cluster {cluster_url} returned invalid response type: {type(fb_res)}")
                    continue
                fb_data = fb_res.get('data', {})
                srcs = fb_data.get('streamList') or fb_data.get('streams') or []
                
                if not srcs and "detail-rec" in endpoint:
                    items = fb_data.get('items') or []
                    if items:
                         # Try to find a playable resource in items
                         logger.info(f"H5 Detail contains {len(items)} sibling items, probing first...")
                
                logger.info(f"Cluster {cluster_url} Result: {len(srcs)} streams found")
                
                # Handshake validation for any candidate found
                if not srcs and fb_data.get('url'): srcs = [fb_data]
                
                for cand in srcs:
                    url = cand.get('url')
                    if not url: continue
                    cookie = cand.get('signCookie') or fb_res.get('signCookie') or fb_data.get('signCookie') or s["client"].session.cookies.get("signCookie") or global_cookie or ""
                    try:
                        v_res = requests.head(url, headers={"User-Agent": "ExoPlayerLib/2.18.7", "Cookie": cookie}, timeout=3, verify=False)
                        if v_res.status_code in [200, 206]:
                            working_stream = cand
                            working_cookie = cookie
                            subtitles_source = fb_data.get("subTitleList", []) or subtitles_source
                            logger.info(f"CLUSTER SUCCESS: Recovered stream via {cluster_url} Cluster")
                            break
                    except: continue
                if working_stream: break
            except Exception as e:
                logger.warning(f"Cluster {cluster_url} failed: {e}")
            finally:
                s["client"].BASE_URL = orig_base
    
    if not working_stream and streams:
        working_stream = streams[0]
        working_cookie = global_cookie or working_stream.get("signCookie") or ""

    if not working_stream:
        logger.error(f"RESOLUTION FAILURE: No usable streams found for subject {subject_id}")
        raise HTTPException(status_code=404, detail="No streams found.")

    # CALCULATE METADATA DURATION FOR FRONTEND OVERRIDE
    total_duration = 0
    source_method = "metadata"
    try:
        subject_detail = s["content"].get_movie_detail(subject_id).get("data") or {}
        runtime_str = subject_detail.get("runtime") or subject_detail.get("duration") or subject_detail.get("totalDuration") or "0"
        
        # Deep probe for episode-specific runtime if possible (Strict String Comparison)
        for sl in subject_detail.get("seasonList", []):
            if str(sl.get("season")) == str(season):
                for ep_item in sl.get("episodeList", []):
                    if str(ep_item.get("episode")) == str(episode):
                        runtime_str = ep_item.get("runtime") or ep_item.get("duration") or ep_item.get("totalDuration") or runtime_str
                        break
        
        runtime_str = str(runtime_str)
        if ":" in runtime_str:
            parts = [int(p) for p in runtime_str.split(':')]
            if len(parts) == 3: total_duration = parts[0] * 3600 + parts[1] * 60 + parts[2]
            elif len(parts) == 2: total_duration = parts[0] * 60 + parts[1]
        else:
            total_duration = int(''.join(filter(str.isdigit, runtime_str))) * 60
    except Exception as e:
        logger.error(f"Metadata duration extraction failed: {e}")
    
    # ADVANCED PROBE: Native HLS Parsing (Fast & Accurate for .m3u8)
    if (total_duration < 600 or total_duration > 15000) and working_stream.get("url", "").lower().endswith(".m3u8"):
        try:
           target_v = working_stream.get("url")
           logger.info(f"Metadata suspicious. Engaging HLS Parse for {target_v[:60]}...")
           h_res = httpx.get(target_v, headers={"User-Agent": "ExoPlayerLib/2.18.7", "Cookie": working_cookie}, verify=False, timeout=5)
           if h_res.status_code == 200:
              lines = h_res.text.splitlines()
              h_dur = sum(float(line.split(":")[1].split(",")[0]) for line in lines if line.startswith("#EXTINF:"))
              if h_dur > 0:
                 total_duration = int(h_dur)
                 source_method = "hls-parse"
        except Exception as he:
           logger.warning(f"HLS duration parse failed: {he}")

    # ADVANCED PROBE: ffprobe for absolute accuracy for MP4/Others
    if source_method == "metadata" and (total_duration < 600 or total_duration > 15000):
        try:
           target_v = working_stream.get("url")
           if target_v:
              logger.info(f"Metadata suspicious ({total_duration}s). Engaging FFPROBE for {target_v[:60]}...")
              ff_cmd = [
                  'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                  '-of', 'default=noprint_wrappers=1:nokey=1',
                  '-headers', f'Cookie: {working_cookie}\r\nUser-Agent: ExoPlayerLib/2.18.7\r\n',
                  target_v
              ]
              ff_proc = subprocess.run(ff_cmd, capture_output=True, text=True, timeout=5)
              if ff_proc.returncode == 0 and ff_proc.stdout.strip():
                  f_dur = float(ff_proc.stdout.strip())
                  if f_dur > 0:
                      total_duration = int(f_dur)
                      source_method = "ffprobe"
        except Exception as fe:
           logger.warning(f"FFPROBE duration probe failed: {fe}")

    if total_duration < 60: # Final fallback
        total_duration = 3600 # 1 hour default

    logger.info(f"DURATION LOCK [{source_method}]: {subject_id} S{season}E{episode} -> {total_duration}s (Source: {runtime_str})")

    # SUBTITLE DISCOVERY: Combine stream-internal and external BFF captions
    all_subtitles = subtitles_source
    try:
        ext_hdrs = {"User-Agent": "Dalvik/2.1.0 (Linux; U; Android 13; SM-S918B Build/TP1A.220624.014)", "X-M-Version": "11.7.0"}
        # Resolve Resource ID for External Subtitles
        sub_resource_id = subject_id
        try:
            sd_res = s["client"].request('GET', '/wefeed-mobile-bff/subject-api/get', params={'subjectId': subject_id}, headers=ext_hdrs)
            sd_detectors = sd_res.get('data', {}).get('resourceDetectors', [])
            if sd_detectors:
                sub_resource_id = sd_detectors[0].get('resourceId') or subject_id
        except: pass
        
        ext_res = s["client"].request('GET', '/wefeed-mobile-bff/subject-api/get-ext-captions', 
                                    params={'resourceId': sub_resource_id, 'subjectId': subject_id, 'episode': episode}, 
                                    headers=ext_hdrs)
        ext_list = ext_res.get("data", {}).get("extCaptions") or ext_res.get("data", {}).get("list") or []
        for esub in ext_list:
            if not any(x.get("url") == esub.get("url") for x in all_subtitles):
                all_subtitles.append(esub)
    except Exception as se:
        logger.warning(f"External subtitle probe failed: {se}")

    # PICK BEST SUBTITLE FOR MPV (Default to English if found)
    best_sub = next((s.get("url") for s in all_subtitles if s.get("lan") == "en" or "english" in (s.get("lanName") or "").lower()), None)

    # DIRECT NATIVE LINK (No Proxy)
    return {
        "url": working_stream.get("url", ""),
        "cookie": working_cookie,
        "duration": total_duration,
        "subtitles": all_subtitles,
        "subtitle_url": best_sub,
        "isHls": False, 
        "streamId": working_stream.get("id"),
        "qualityList": list(set([st.get("quality") for st in streams if st.get("quality")])),
        "episode": episode,
        "season": season
    }

    return {
        "url": working_stream.get("url"),
        "quality": working_stream.get("quality") or quality or "Auto",
        "cookie": working_cookie,
        "headers": {"User-Agent": "ExoPlayerLib/2.18.7", "Cookie": working_cookie or ""},
        "subtitles": subtitles_source,
        "isHls": working_stream.get("url", "").lower().endswith(".m3u8") or ".m3u8" in working_stream.get("url", "").lower(),
        "streamId": working_stream.get("id"),
        "qualityList": list(set([st.get("quality") for st in streams if st.get("quality")])),
        "duration": total_duration
    }

import os

def load_local_history():
    try:
        import json
        if os.path.exists("local_history.json"):
            with open("local_history.json", "r") as f:
                return json.load(f)
    except: pass
    return {}

def save_local_history(data):
    try:
        import json
        with open("local_history.json", "w") as f:
            json.dump(data, f)
    except: pass

@app.get("/download/{subject_id}")
async def proxy_download(
    request: Request,
    subject_id: str, 
    season: int = 1, 
    episode: int = 1, 
    quality: str = "720p", 
    title: str = "Movie",
    session_id: Optional[str] = Cookie(None)
):
    s = get_session(session_id)
    
    # PRIORITY 1: Carrier 301 (Legacy Mirror) specifically for raw MP4s
    logger.info(f"Targeting Carrier 301 Raw Mirrors for {subject_id}...")
    c_res = s["client"].request('POST', '/index/video/v_detail', data={'subjectId': subject_id, 'carrier': '301', 'quality': quality})
    data = c_res.get("data")
    if not isinstance(data, dict): data = {}
    streams = data.get("streamList") or data.get("streams") or []
    
    # PRIORITY 2: Mobile Protocol (DASH/HLS) if MP4 is missing
    if not streams:
        res = s["stream"].get_play_info(subject_id, season=season, episode=episode)
        data = res.get("data", {})
        streams = data.get("streamList") or data.get("streams") or []
    
    if not streams: 
        raise HTTPException(status_code=404, detail="No downloadable mirrors found")
    
    match = None
    for st in streams:
        if ".mp4" in st.get("url", "").lower():
            match = st
            break
    if not match: match = streams[0]
            
    url = match.get("url")
    cookie = data.get("signCookie") or match.get("signCookie") or ""
    if not url: raise HTTPException(status_code=404)
    
    clean_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
    
    # CASE 1: Native MP4 stream (Fully seekable via HTTPX byte ranges)
    if ".mp4" in url.lower():
        import httpx
        req_hdrs = {"User-Agent": "ExoPlayerLib/2.18.7", "Cookie": cookie}
        range_header = request.headers.get("Range")
        if range_header: req_hdrs["Range"] = range_header
            
        client = httpx.AsyncClient(verify=False)
        req = client.build_request("GET", url, headers=req_hdrs)
        r = await client.send(req, stream=True)
        
        filename = f"{clean_title}_S{season}_E{episode}.mp4"
        headers = {
            "Content-Disposition": f"attachment; filename=\"{filename}\"",
            "Accept-Ranges": r.headers.get("Accept-Ranges", "bytes"),
            "Content-Length": r.headers.get("Content-Length", ""),
            "Content-Range": r.headers.get("Content-Range", ""),
            "Content-Type": "video/mp4"
        }
        
        async def stream_generator():
            async for chunk in r.aiter_bytes(chunk_size=1024 * 1024): yield chunk

        return StreamingResponse(
            stream_generator(),
            status_code=r.status_code,
            headers={k: v for k, v in headers.items() if v},
            background=httpx.AsyncClient().aclose
        )
        
    # CASE 2: DASH (.mpd) or HLS (.m3u8) needs FFMPEG demuxing
    # We pipe as MPEG-TS (.ts) because it is inherently seekable without needing a faststart moov atom!
    import subprocess
    filename = f"{clean_title}_S{season}_E{episode}.ts"
    
    def iter_ffmpeg():
        cmd = [
            'ffmpeg', '-y', '-hide_banner', '-loglevel', 'error',
            '-headers', f'Cookie: {cookie}\r\nUser-Agent: ExoPlayerLib/2.18.7\r\n',
            '-i', url,
            '-c', 'copy', '-f', 'mpegts', '-'
        ]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            while True:
                chunk = process.stdout.read(2048 * 1024)
                if not chunk: break
                yield chunk
        finally:
            process.terminate()

    return StreamingResponse(
        iter_ffmpeg(), 
        media_type="video/mp2t",
        headers={
            "Content-Disposition": f"attachment; filename=\"{filename}\""
        }
    )
@app.get("/subtitles/{subject_id}")
def get_subtitles(subject_id: str, se: int = 1, ep: int = 1, session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    try:
        hdrs = {"User-Agent": "Dalvik/2.1.0 (Linux; U; Android 13; SM-S918B Build/TP1A.220624.014)", "X-M-Version": "11.7.0"}
        
        # Resolve actual resourceId for content mapping parity
        resource_id = subject_id
        try:
            det_res = s["client"].request('GET', '/wefeed-mobile-bff/subject-api/get', params={'subjectId': subject_id}, headers=hdrs)
            detectors = det_res.get('data', {}).get('resourceDetectors', [])
            if detectors:
                resource_id = detectors[0].get('resourceId') or subject_id
        except: pass

        # Fetch using high-parity external captions endpoint
        res = s["client"].request('GET', '/wefeed-mobile-bff/subject-api/get-ext-captions', 
                                    params={'resourceId': resource_id, 'subjectId': subject_id, 'episode': ep}, 
                                    headers=hdrs)
        data = res.get("data", {})
        if not isinstance(data, dict): data = {}
        ls = data.get("extCaptions") or data.get("list") or []
        return {"code": 0, "data": {"list": ls}}
    except:
        return {"code": 0, "data": {"list": []}}

# --- NEW: Cloud Sync & Advanced Subtitles ---

@app.get("/history/position")
def get_history_position(subject_id: str, resource_id: str, session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    res = s["client"].request('GET', '/wefeed-mobile-bff/subject-api/resource-position', params={'subjectId': subject_id, 'resourceId': resource_id})
    return res

@app.post("/history/position")
def save_history_position(subject_id: str, resource_id: str, position: int, session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    res = s["client"].request('POST', '/wefeed-mobile-bff/subject-api/resource-position', data={'subjectId': subject_id, 'resourceId': resource_id, 'position': position})
    return res

@app.post("/history/seen")
def mark_have_seen(subject_id: str = None, progress: int = 0, total: int = 0, session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    if not subject_id: return {"code": -1, "msg": "Missing ID"}
    res = s["user"].report_history(subject_id, progress, total)
    return res
@app.post("/analytics/operation")
def track_operation(action: str, target: str, session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    res = s["client"].request('POST', '/wefeed-mobile-bff/statistics/user-operation', data={'action': action, 'target': target})
    return res

@app.get("/subtitles/search")
def subtitle_search(query: str, session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    try:
        hdrs = {"User-Agent": "Dalvik/2.1.0 (Linux; U; Android 13; SM-S918B Build/TP1A.220624.014)", "X-M-Version": "11.7.0"}
        # Parameter 'q' is mandatory for v11.7.0 BFF search
        res = s["client"].request('GET', '/wefeed-mobile-bff/subject-api/subtitle-search', params={'q': query}, headers=hdrs)
        data = res.get("data", {})
        if not isinstance(data, dict): data = {}
        ls = data.get("items") or data.get("list") or []
        return {"code": 0, "data": {"list": ls}}
    except: return {"code": 0, "data": {"list": []}}


@app.get("/history")
def get_history(page: int = 1, session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    h = load_local_history()
    
    # Merge both guest/default history and user-specific history
    default_history = h.get("default", [])
    user_specific = h.get(session_id, []) if session_id else []
    blacklist = set(h.get("blacklist", []))
    
    # Combine uniquely by subjectId
    combined_history_dict = {str(x.get("subjectId") or x.get("id")): x for x in default_history + user_specific}
    user_history = list(combined_history_dict.values())
    
    try:
        res = s["user"].get_history(page=page)
        data = res.get("data", {})
        if not isinstance(data, dict): data = {}
        cloud_list = data.get("items") or data.get("list") or []
        
        seen_ids = set(combined_history_dict.keys())
        for c in cloud_list:
            sid_str = str(c.get("subjectId"))
            # CRITICAL FIX: Only add from cloud if NOT in our local blacklist
            if sid_str not in seen_ids and sid_str not in blacklist:
                mapped = map_item(c)
                mapped["seeTime"] = c.get("seeTime") or c.get("updateTime") or c.get("progress") or 0
                mapped["subjectId"] = c.get("subjectId")
                mapped["id"] = c.get("subjectId")
                user_history.append(mapped)
    except Exception as e:
        pass
        
    user_history = [x for x in user_history if x.get("subjectId") and str(x.get("subjectId")) != "None"]
    # AND filter out anything in blacklist again to be 100% sure
    user_history = [x for x in user_history if str(x.get("subjectId")) not in blacklist]
    
    # Sort history by seeTime/updateTime descending
    user_history.sort(key=lambda x: int(x.get("seeTime", 0) or 0), reverse=True)
    
    return {"code": 0, "data": {"list": user_history}}


@app.get("/watchlist")
def get_watchlist(page: int = 1, session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    try:
        res = s["user"].get_watchlist(page=page)
        data = res.get("data", {})
        if not isinstance(data, dict): data = {}
        cloud_list = data.get("items") or data.get("list") or []
        return {"code": 0, "data": {"list": [map_item(x) for x in cloud_list]}}
    except:
        return {"code": 0, "data": {"list": []}}

@app.post("/history/delete/{subject_id}")
def delete_history_item(subject_id: str, session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    # Clear local history
    h = load_local_history()
    
    # 1. Update Blacklist (Tombstone) to prevent cloud re-sync
    if "blacklist" not in h: h["blacklist"] = []
    if str(subject_id) not in h["blacklist"]:
        h["blacklist"].append(str(subject_id))

    # 2. Cleanup existing occurrences
    if "default" in h:
        h["default"] = [x for x in h["default"] if str(x.get("subjectId")) != str(subject_id)]
        
    s_id = session_id or "default"
    if s_id in h and s_id != "default":
        h[s_id] = [x for x in h[s_id] if str(x.get("subjectId")) != str(subject_id)]
        
    save_local_history(h)
    
    # 3. Attempt cloud clear
    res = s["user"].report_history(subject_id, 0, 0, status=0) 
    return {"status": "success", "raw": res}


@app.post("/watchlist/toggle")
def toggle_watchlist(subject_id: str, active: bool, subject_type: int = 1, session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    action = 1 if active else 0
    res = s["user"].toggle_watchlist(subject_id, action=action, subject_type=subject_type)
    return {"status": "success", "raw": res}

class ProgressReport(BaseModel):
    subject_id: str
    progress_ms: int
    total_ms: int
    status: int = 1

@app.post("/history/progress")
def report_progress(req: ProgressReport, session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    return s["user"].report_history(req.subject_id, req.progress_ms, req.total_ms, req.status)

@app.post("/launch-player")
def launch_player(player: str, url: str, cookie: Optional[str] = None, subject_id: Optional[str] = None, resource_id: Optional[str] = None, season: Optional[int] = None, episode: Optional[int] = None, title: Optional[str] = None, cover: Optional[str] = None, start_time: int = 0, subtitle_url: Optional[str] = None, duration: int = 0, session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    # Record History!
    if subject_id:
        try:
            s["client"].request('POST', '/wefeed-mobile-bff/subject-api/have-seen', data={'subjectId': subject_id})
        except: pass

        # 1. Update our Local Storage so Continue Watching yields instant responses
        h = load_local_history()
        s_id = session_id or "default"
        if s_id not in h: h[s_id] = []
        
        # CLEAR FROM BLACKLIST if re-watching
        if "blacklist" in h:
            h["blacklist"] = [x for x in h["blacklist"] if str(x) != str(subject_id)]

        h[s_id] = [x for x in h[s_id] if x.get("subjectId") != subject_id]

        
        h[s_id].insert(0, {
            "subjectId": subject_id,
            "id": subject_id,
            "title": title or "Unknown",
            "cover": cover or "",
            "poster": cover or "",
            "subjectType": 2 if season and episode else 1,
            "season": season,
            "episode": episode,
            "seeTime": int(start_time) * 1000 
        })
        save_local_history(h)
        
        # 2. Sync to Official MovieBox Servers
        try:
            # Report progress starting point to continue watching
            s["user"].report_history(subject_id, int(start_time) * 1000, 6000000, status=1)
        except Exception as e:
            print("History sync failed:", e)

    import subprocess
    
    if (not url or "bridge" in url or "compat" in url or "proxy" in url) and subject_id:
        try:
            logger.info(f"Resolving RAW stream for native launch: {subject_id} S{season}E{episode} (Resource: {resource_id})")
            stream_info = get_stream(subject_id, season=season or 1, episode=episode or 1, resource_id=resource_id, session_id=session_id)
            url = stream_info.get("url")
            cookie = stream_info.get("cookie")
            duration = stream_info.get("duration", duration)
            if not subtitle_url:
                subtitle_url = stream_info.get("subtitle_url")
            if url: logger.info(f"SUCCESS: Resolved {url[:60]}...")
        except Exception as e:
            logger.error(f"Native Resolution failed: {e}")

    if not url:
        return {"status": "error", "message": "Empty URL"}

    # ENSURE COOKIE FORMAT is correct for MPV (signCookie=...)
    if cookie:
        cookie = cookie.strip().rstrip(';')
        if "signCookie=" not in cookie:
            # If it already looks like a CloudFront triple, don't wrap it in signCookie
            if "CloudFront-Policy" in cookie:
                pass 
            else:
                cookie = f"signCookie={cookie}"
    else:
        # FAILOVER: If cookie is empty, try session first
        cookie = s["client"].session.cookies.get("signCookie") or ""
        # Only use auth token fallback for regional titles
        if not cookie and ("hakunaymatata" in url or "hindi" in (title or "").lower()):
            cookie = s["auth"].token or ""
            # LAST RESORT: Generate a dummy guest signature if still empty
            if not cookie:
                import time
                cookie = f"guest_{int(time.time())}_{subject_id}"
                logger.info("Using Generated Guest Signature")
        
        if cookie and "signCookie=" not in cookie:
            cookie = f"signCookie={cookie}"
    
    # SECURITY: If URL already has a 'sign=' parameter, DO NOT inject signCookie 
    # This prevents authentication collision on BCDN mirrors
    if "sign=" in url:
        logger.info("SIGN PARAMETER DETECTED IN URL: Suppressing external cookie injection.")
        cookie = None

    # HIGH PARITY HEADERS matching latest app behavior
    ua = "ExoPlayerLib/2.19.1"
    
    # Referer varies by CDN
    if "sacdn2.hakunaymatata.com" in url:
        referer = "https://api6.aoneroom.com/" # REQUIRED FOR SACDN2
    elif "hakunaymatata.com" in url:
        referer = "https://www.movieboxpro.app/" # PROVEN REFERER FOR HAKUNA
    else:
        referer = "https://api6.aoneroom.com/"
    
    if player.lower() == "mpv":
        cmd = ["mpv", f"--user-agent={ua}", f"--referrer={referer}", "--cache=yes"]
        # Regional titles sometimes need ytdl disabled, but standard content needs it enabled
        if "hakunaymatata.com" in url:
            cmd.append("--ytdl=no")
        if title: cmd.append(f'--force-media-title={title}')
        if duration > 0: cmd.append(f"--length={duration}")
        if cookie:
            cmd.append(f"--http-header-fields=Cookie: {cookie}")
            # For DASH (.mpd), ensure the demuxer layer also has the headers
            if ".mpd" in url:
                cmd.append(f"--demuxer-lavf-o=headers=Cookie: {cookie}")
        if start_time > 0: cmd.append(f"--start={start_time}")
        if subtitle_url: cmd.append(f'--sub-file={subtitle_url}')
        cmd.append(url)
    else:
        cmd = ["vlc", f"--http-user-agent={ua}", f"--http-referrer={referer}", "--network-caching=5000"]
        if cookie: cmd.append(f':http-header-fields=Cookie: {cookie}')
        if start_time > 0: cmd.append(f"--start-time={start_time}")
        if subtitle_url: cmd.append(f'--sub-file={subtitle_url}')
        cmd.append(url)
    
    # WINDOWS SHELL QUOTING FIX: Rebuild command string with proper quotes for the shell
    def win_quote(s):
        if ' ' in s or '&' in s or '?' in s or '=' in s:
            return f'"{s}"'
        return s
    
    cmd_str = ' '.join(map(win_quote, cmd))
    logger.info(f"EXEC CMD (WIN): {cmd_str}")
    
    # On Windows, we use shell=True and CREATE_NEW_PROCESS_GROUP
    subprocess.Popen(cmd_str, shell=True, creationflags=0x00000200)
    return {"status": "success", "url": url}

@app.get("/post/count/{subject_id}")
def get_post_count(subject_id: str, session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    try:
        res = s["client"].request("GET", "/wefeed-mobile-bff/post/count/subject", params={"subjectId": subject_id})
        count = res.get("data", {}).get("count") or "0"
        return {"code": 0, "count": count}
    except:
        return {"code": 0, "count": "0"}

@app.get("/groups/trending")
def get_trending_groups(session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    try:
        res = s["client"].request("POST", "/wefeed-mobile-bff/group/list/trending-entrance", data={})
        data = res.get("data", {})
        items = data.get("items") or []
        return {"code": 0, "data": items}
    except:
        return {"code": 0, "data": []}

@app.post("/post/like")
def like_post(post_id: str, session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    try:
        res = s["client"].request("POST", "/wefeed-mobile-bff/interactive/post/like", data={"postId": post_id})
        return res
    except Exception as e:
        return {"code": 1, "msg": str(e)}

@app.post("/post/create")
def create_post(subject_id: str, content: str, session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    try:
        # /post/create logic from Smali
        data = {
            "subjectId": subject_id,
            "content": content,
            "type": "1" # Public post
        }
        res = s["client"].request("POST", "/wefeed-mobile-bff/post/create", data=data)
        return res
    except Exception as e:
        return {"code": 1, "msg": str(e)}

@app.get("/groups/interactive")
def get_interactive_posts(session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    try:
        # Pull from public interactive ranking feed
        res = s["client"].request("POST", "/wefeed-mobile-bff/interactive/post/list", 
                                 data={"page": 1, "pageSize": 20})
        return res
    except Exception as e:
        return {"code": 1, "msg": str(e)}

@app.get("/post/list/{subject_id}")
def get_subject_posts(subject_id: str, page: int = 1, session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    try:
        # subject-specific post list
        res = s["client"].request("POST", "/wefeed-mobile-bff/post/list/subject", 
                                 data={"subjectId": subject_id, "page": page, "pageSize": 10})
        return res
    except Exception as e:
        return {"code": 1, "msg": str(e)}

@app.get("/debug_history")
def debug_history(session_id: Optional[str] = Cookie(None)):
    s = get_session(session_id)
    results = {}
    for i in range(1, 6):
        try:
            res = s["client"].request(
                "GET",
                "/wefeed-mobile-bff/subject-api/see-list-v2",
                params={"page": "1", "pageSize": "10", "seeType": str(i)}
            )
            data = res.get("data", {})
            if not isinstance(data, dict): data = {}
            lst = data.get("list") or data.get("items") or res.get("list") or []
            results[f"seeType_{i}_count"] = len(lst)
            if len(lst) > 0:
                results[f"seeType_{i}_sample_keys"] = list(lst[0].keys())
        except Exception as e:
            results[f"seeType_{i}_error"] = str(e)
            
    try:
        results["tab_record"] = s["client"].request("GET", "/wefeed-mobile-bff/tab/play-record")
    except: pass
    return results

# DIRECT NATIVE PLAYBACK ONLY (PROXIES REMOVED)

@app.get("/sub-proxy")
async def subtitle_proxy(u: str):
    """Proxies external subtitles to bypass CORS blocking."""
    async with httpx.AsyncClient(verify=False) as client:
        res = await client.get(u, headers={"User-Agent": "ExoPlayerLib/2.18.7"}, follow_redirects=True)
        return Response(content=res.content, media_type="text/vtt", headers={"Access-Control-Allow-Origin": "*"})

if __name__ == "__main__":
    # DISABLE RELOAD: Prevents Windows-specific crash loops during active streaming/editing
    uvicorn.run("moviebox_api_server:app", host="0.0.0.0", port=8000, reload=False)
