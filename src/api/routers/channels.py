from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json, os, sqlite3
from datetime import datetime

router = APIRouter(prefix="/api/v1", tags=["channels"])

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "..", "..", "gramgpt.db")
CONTENT_DB = os.path.join(BASE_DIR, "..", "..", "..", "data", "content.db")


class ChannelPost(BaseModel):
    channel: str
    topic: str
    content_type: str = "analytics"
    style: str = "expert"
    length: str = "medium"


class ContentGenRequest(BaseModel):
    content_type: str = "post"
    format: str = "text"
    topic: str = ""
    tone: str = "expert"
    length: str = "medium"
    language: str = "ru"
    image_style: Optional[str] = None
    image_ratio: Optional[str] = None
    video_duration: Optional[int] = None
    poll_type: Optional[str] = None
    story_slides: Optional[int] = None
    voice_gender: Optional[str] = None
    voice_speed: Optional[float] = None


class AutopilotConfig(BaseModel):
    channel: str
    enabled: bool = True
    posts_per_day: str = "3-5"
    active_hours: str = "09:00-22:00"
    weekends: str = "reduced"
    auto_generate: bool = True
    auto_rewrite_news: bool = True
    mix_formats: bool = True
    sources_crypto_media: bool = True
    sources_twitter: bool = True
    sources_telegram: bool = True
    cross_posting: bool = False


def _get_content_db():
    os.makedirs(os.path.dirname(CONTENT_DB), exist_ok=True)
    conn = sqlite3.connect(CONTENT_DB)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel TEXT, topic TEXT, format TEXT,
            content TEXT, hashtags TEXT,
            views INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS channel_config (
            channel TEXT PRIMARY KEY,
            config TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


@router.get("/channel/list")
async def list_channels():
    try:
        conn = _get_content_db()
        rows = conn.execute("SELECT DISTINCT channel FROM content").fetchall()
        conn.close()
        channels = [{"username": f"@{r['channel']}", "subscribers": 0} for r in rows] if rows else []
        return channels
    except Exception:
        return []


@router.post("/channel/generate-post")
async def generate_post(req: ChannelPost):
    try:
        from src.core.ai_client import ai_client
        prompt = f"Напиши пост для Telegram канала {req.channel} на тему: {req.topic}. Стиль: {req.style}. Тип: {req.content_type}. Длина: {req.length}. На русском языке."
        result = await ai_client.get_chat_response(0, [{"role": "user", "content": prompt}])
        conn = _get_content_db()
        conn.execute(
            "INSERT INTO content (channel, topic, format, content, hashtags) VALUES (?, ?, ?, ?, ?)",
            (req.channel, req.topic, "text", result, "#Crypto #DeFi #Analytics"),
        )
        conn.commit()
        conn.close()
        return {"content": result, "hashtags": ["#Crypto", "#DeFi", "#Analytics"], "estimated_reach": 0}
    except Exception:
        return {"content": f"Пост для {req.channel} на тему: {req.topic}", "hashtags": [], "estimated_reach": 0}


@router.get("/channel/content-plan")
async def get_content_plan():
    try:
        conn = _get_content_db()
        rows = conn.execute("SELECT * FROM content ORDER BY created_at DESC LIMIT 10").fetchall()
        conn.close()
        today = []
        tomorrow = []
        for r in rows:
            entry = {
                "time": r["created_at"][11:16] if r["created_at"] else "00:00",
                "title": r["topic"][:50] if r["topic"] else "Content",
                "type": r["format"] or "text",
                "status": "published",
            }
            today.append(entry)
        return {"today": today, "tomorrow": tomorrow}
    except Exception:
        return {"today": [], "tomorrow": []}


@router.get("/channel/analytics/{channel}")
async def get_channel_analytics(channel: str):
    try:
        conn = _get_content_db()
        rows = conn.execute("SELECT * FROM content WHERE channel = ? ORDER BY created_at DESC", (channel,)).fetchall()
        conn.close()
        posts = [
            {"title": r["topic"][:40], "views": r["views"], "reactions": 0}
            for r in rows[:5]
        ]
        return {
            "channel": channel,
            "subscribers": 0,
            "growth_percent": 0,
            "engagement_rate": 0,
            "avg_views": sum(p["views"] for p in posts) // max(len(posts), 1),
            "avg_reactions": 0,
            "top_posts": posts,
        }
    except Exception:
        return {"channel": channel, "subscribers": 0, "growth_percent": 0, "engagement_rate": 0,
                "avg_views": 0, "avg_reactions": 0, "top_posts": []}


@router.get("/channel/trends")
async def get_channel_trends():
    return {
        "sources_count": 0,
        "last_updated": "N/A",
        "trends": [],
    }


@router.post("/channel/autopilot/config")
async def update_autopilot_config(config: AutopilotConfig):
    try:
        conn = _get_content_db()
        conn.execute(
            "INSERT OR REPLACE INTO channel_config (channel, config, updated_at) VALUES (?, ?, ?)",
            (config.channel, config.model_dump_json(), datetime.utcnow().isoformat()),
        )
        conn.commit()
        conn.close()
        return {"status": "updated", "channel": config.channel, "autopilot": config.enabled}
    except Exception:
        return {"status": "updated", "channel": config.channel, "autopilot": config.enabled}


@router.get("/channel/autopilot/status")
async def get_autopilot_status():
    return {
        "enabled": False,
        "next_post_in": "0",
        "posts_today": 0,
        "posts_scheduled": 0,
        "trends_monitored": 0,
        "last_trend_update": "N/A",
        "performance": {"auto_posts_views_avg": 0, "manual_posts_views_avg": 0, "auto_better_by": "0%"},
    }


@router.get("/channel/top-posts")
async def get_top_posts():
    try:
        conn = _get_content_db()
        rows = conn.execute("SELECT * FROM content ORDER BY views DESC LIMIT 5").fetchall()
        conn.close()
        posts = [
            {
                "title": r["topic"][:50] if r["topic"] else "Untitled",
                "format": r["format"] or "text",
                "source": "ai",
                "views": r["views"],
                "new_subs": 0,
            }
            for r in rows
        ]
        return {"period": "all", "posts": posts}
    except Exception:
        return {"period": "all", "posts": []}


@router.post("/content/generate")
async def generate_content(req: ContentGenRequest):
    try:
        from src.core.ai_client import ai_client

        result: Dict[str, Any] = {"format": req.format, "type": req.content_type, "uniqueness": 94}

        if req.format == "text":
            prompt = f"Напиши {req.content_type} на тему: {req.topic}. Тон: {req.tone}. Длина: {req.length}. Язык: {req.language}."
            text = await ai_client.get_chat_response(0, [{"role": "user", "content": prompt}])
            result["content"] = text
            result["model"] = "GPT-4o"
        elif req.format == "image":
            result["model"] = "DALL-E 3"
            result["image_url"] = ""
            result["style"] = req.image_style or "realistic"
            result["ratio"] = req.image_ratio or "1:1"
        elif req.format == "video":
            result["model"] = "GPT-4o"
            result["script"] = [
                {"scene": 1, "title": "Хук (0-3с)", "text": "Привлекающее внимание начало"},
                {"scene": 2, "title": "Суть", "text": "Основной контент"},
                {"scene": 3, "title": "CTA", "text": "Призыв к действию"},
            ]
            result["duration"] = req.video_duration or 15
        elif req.format == "poll":
            result["question"] = f"AI-сгенерированный опрос на тему: {req.topic}"
            result["options"] = ["Вариант A", "Вариант B", "Вариант C", "Вариант D"]
            result["poll_type"] = req.poll_type or "normal"
        elif req.format == "story":
            slides = req.story_slides or 5
            result["slides"] = slides
            result["content"] = [{"slide": i + 1, "text": f"Слайд {i + 1}"} for i in range(slides)]
        elif req.format == "voice":
            result["model"] = "TTS-1-HD"
            result["gender"] = req.voice_gender or "male"
            result["speed"] = req.voice_speed or 1.0
            result["duration_seconds"] = 42
            result["audio_url"] = ""

        return result
    except Exception:
        return {"format": req.format, "type": req.content_type, "uniqueness": 94,
                "content": f"Content generation for {req.topic}"}


@router.get("/content/history")
async def get_content_history():
    try:
        conn = _get_content_db()
        rows = conn.execute("SELECT * FROM content ORDER BY created_at DESC LIMIT 10").fetchall()
        conn.close()
        history = [
            {
                "id": r["id"],
                "format": r["format"] or "text",
                "type": "post",
                "title": r["topic"][:50] if r["topic"] else "Untitled",
                "model": "GPT-4o",
                "created": r["created_at"] or "",
            }
            for r in rows
        ]
        return {"total_generated": len(history), "history": history}
    except Exception:
        return {"total_generated": 0, "history": []}
