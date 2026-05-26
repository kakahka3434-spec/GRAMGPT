from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any

router = APIRouter(prefix="/api/v1", tags=["channels"])


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


@router.get("/channel/list")
async def list_channels():
    return [
        {"username": "@gramgpt_channel", "subscribers": 12847, "growth_week": 340, "er": 8.4},
        {"username": "@crypto_daily", "subscribers": 5234, "growth_week": 120, "er": 6.2},
    ]


@router.post("/channel/generate-post")
async def generate_post(req: ChannelPost):
    return {
        "content": f"📊 AI-генерированный пост для {req.channel}\n\nТема: {req.topic}\nСтиль: {req.style}",
        "hashtags": ["#Crypto", "#DeFi", "#Analytics"],
        "estimated_reach": 4500,
    }


@router.get("/channel/content-plan")
async def get_content_plan():
    return {
        "today": [
            {"time": "09:00", "title": "Утренний обзор рынка", "type": "analytics", "status": "published"},
            {"time": "14:00", "title": "Разбор проекта DeFi", "type": "review", "status": "ready"},
            {"time": "20:00", "title": "Вечерний дайджест", "type": "digest", "status": "queued"},
        ],
        "tomorrow": [
            {"time": "10:00", "title": "Еженедельная аналитика", "type": "longread", "status": "queued"},
            {"time": "16:00", "title": "Опрос аудитории", "type": "poll", "status": "queued"},
        ],
    }


@router.get("/channel/analytics/{channel}")
async def get_channel_analytics(channel: str):
    return {
        "channel": channel, "subscribers": 12847, "growth_percent": 12.4, "engagement_rate": 8.4,
        "avg_views": 4521, "avg_reactions": 156,
        "top_posts": [
            {"title": "Обзор ETH 2.0", "views": 8920, "reactions": 456},
            {"title": "DeFi стратегии", "views": 6340, "reactions": 312},
        ],
    }


@router.get("/channel/trends")
async def get_channel_trends():
    return {
        "sources_count": 247, "last_updated": "3 мин назад",
        "trends": [
            {"rank": 1, "title": "Bitcoin пробил $150K", "sources": "CoinDesk, Bloomberg, 47 каналов", "heat": "hot", "age": "12 мин"},
            {"rank": 2, "title": "Новый L2 от Telegram", "sources": "TON Blog, Decrypt, 23 канала", "heat": "rising", "age": "34 мин"},
            {"rank": 3, "title": "SEC одобрила ETH ETF staking", "sources": "Reuters, CoinTelegraph, 18 каналов", "heat": "trending", "age": "1ч"},
            {"rank": 4, "title": "Airdrop нового DeFi протокола", "sources": "Twitter/X, 15 каналов", "heat": "new", "age": "2ч"},
        ],
    }


@router.post("/channel/autopilot/config")
async def update_autopilot_config(config: AutopilotConfig):
    return {"status": "updated", "channel": config.channel, "autopilot": config.enabled, "next_post_in": "2ч 14мин", "posts_scheduled_today": 5}


@router.get("/channel/autopilot/status")
async def get_autopilot_status():
    return {
        "enabled": True, "next_post_in": "2ч 14мин", "posts_today": 2, "posts_scheduled": 3,
        "trends_monitored": 247, "last_trend_update": "3 мин назад",
        "performance": {"auto_posts_views_avg": 4521, "manual_posts_views_avg": 3200, "auto_better_by": "+41%"},
    }


@router.get("/channel/top-posts")
async def get_top_posts():
    return {
        "period": "week",
        "posts": [
            {"title": "Bitcoin прогноз на Q3", "format": "text", "source": "ai", "views": 12450, "new_subs": 340},
            {"title": "DeFi инфографика", "format": "image", "source": "dall-e", "views": 8920, "new_subs": 210},
            {"title": "Опрос: Лучшая L2 сеть", "format": "poll", "source": "ai", "views": 6340, "votes": 847, "new_subs": 125},
        ],
    }


@router.post("/content/generate")
async def generate_content(req: ContentGenRequest):
    result: Dict[str, Any] = {"format": req.format, "type": req.content_type, "uniqueness": 94}
    if req.format == "text":
        result["content"] = f"AI-генерированный контент\n\nТема: {req.topic}\nТон: {req.tone}\nДлина: {req.length}"
        result["model"] = "GPT-4o"
    elif req.format == "image":
        result["model"] = "DALL-E 3"
        result["image_url"] = "https://placeholder.co/1024x1024"
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
        result["slides"] = req.story_slides or 5
        result["content"] = [{"slide": i + 1, "text": f"Слайд {i + 1}"} for i in range(req.story_slides or 5)]
    elif req.format == "voice":
        result["model"] = "TTS-1-HD"
        result["gender"] = req.voice_gender or "male"
        result["speed"] = req.voice_speed or 1.0
        result["duration_seconds"] = 42
        result["audio_url"] = "https://placeholder.co/audio.ogg"
    return result


@router.get("/content/history")
async def get_content_history():
    return {
        "total_generated": 2891,
        "history": [
            {"id": 1, "format": "image", "type": "banner", "title": "Крипто баннер для канала", "model": "DALL-E 3", "created": "30 мин назад"},
            {"id": 2, "format": "text", "type": "post", "title": "Обзор ETH 2.0", "tone": "expert", "views": 892, "created": "2 часа назад"},
            {"id": 3, "format": "poll", "type": "poll", "title": "Лучший L2 2026", "votes": 312, "created": "5 часов назад"},
        ],
    }
