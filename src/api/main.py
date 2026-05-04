from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from src.api.web3 import router as web3_router
from typing import Dict, Any, List, Optional
from src.core.orchestrator import orchestrator
import os

app = FastAPI(title="GRAMGPT API")
app.include_router(web3_router)

# Static file paths
base_dir = os.path.dirname(__file__)
mini_app_path = os.path.join(base_dir, "static/mini-app")
landing_path = os.path.join(base_dir, "static/landing")

# Mount Mini App and Landing static files
app.mount("/panel", StaticFiles(directory=mini_app_path, html=True), name="panel")
app.mount("/static", StaticFiles(directory=landing_path), name="landing-static")


@app.get("/")
async def landing_page():
    return FileResponse(os.path.join(landing_path, "index.html"))

class CampaignRequest(BaseModel):
    name: str
    goal: str

@app.get("/api/v1/status")
async def root():
    return {"status": "GRAMGPT Engine Online"}

@app.post("/api/v1/campaigns/create")
async def create_campaign(req: CampaignRequest):
    strategy = await orchestrator.create_campaign_strategy(req.name, req.goal)
    return {"strategy": strategy}

@app.get("/api/v1/analytics/summary")
async def get_analytics():
    return {
        "active_accounts": 12,
        "leads_captured": 1247,
        "roi_average": "240%",
        "risk_status": "safe"
    }

# --- Marketplace & Agency Endpoints ---
@app.get("/api/v1/marketplace/templates")
async def list_templates():
    return [
        {"id": "crypto_1", "name": "Crypto Investor Funnel", "price_ton": 5.0},
        {"id": "design_1", "name": "Design Agency Outreach", "price_ton": 3.5},
        {"id": "saas_1", "name": "SaaS B2B Drip", "price_ton": 10.0}
    ]

@app.post("/api/v1/agency/clients/add")
async def add_agency_client(agency_id: int, client_name: str):
    return {"status": "client_added", "workspace_url": f"https://gramgpt.io/w/{client_name.lower()}"}

@app.get("/api/v1/agency/stats")
async def get_agency_stats(agency_id: int):
    return {
        "total_clients": 5,
        "total_revenue_ton": 450.5,
        "sub_resellers": 2
    }


# --- Parsing Endpoints ---
class ParseRequest(BaseModel):
    parser_type: str  # users, channels, messages, keywords
    target: str
    keywords: Optional[str] = None
    limit: int = 1000
    period: str = "7d"


@app.post("/api/v1/parsing/start")
async def start_parsing(req: ParseRequest):
    return {
        "status": "started",
        "task_id": "parse_001",
        "parser_type": req.parser_type,
        "target": req.target,
        "estimated_results": 1247
    }


@app.get("/api/v1/parsing/results/{task_id}")
async def get_parsing_results(task_id: str):
    return {
        "task_id": task_id,
        "status": "completed",
        "total_found": 1247,
        "results": [
            {"username": "@ivanpetrov", "name": "Иван Петров", "source": "Crypto Канал"},
            {"username": "@mivanova", "name": "Мария Иванова", "source": "DeFi Группа"},
            {"username": "@olegsidorov", "name": "Олег Сидоров", "source": "NFT Новости"},
        ]
    }


# --- Commenting Endpoints ---
class CommentingConfig(BaseModel):
    channels: List[str]
    tone: str = "expert"
    model: str = "gpt-4o"
    frequency: str = "every_2nd"


@app.post("/api/v1/commenting/start")
async def start_commenting(config: CommentingConfig):
    return {
        "status": "active",
        "channels": config.channels,
        "tone": config.tone,
        "model": config.model
    }


@app.get("/api/v1/commenting/logs")
async def get_commenting_logs():
    return [
        {"channel": "Крипто Новости", "comment": "Отличный анализ рынка!", "likes": 12, "replies": 3, "time": "2 мин назад"},
        {"channel": "DeFi Обзоры", "comment": "Интересная стратегия!", "likes": 8, "replies": 5, "time": "15 мин назад"},
        {"channel": "NFT Новости", "comment": "Перспективный проект!", "likes": 21, "replies": 7, "time": "32 мин назад"},
    ]


# --- Chatting Endpoints ---
class ChattingConfig(BaseModel):
    groups: List[str]
    strategy: str = "expert"
    max_per_hour: int = 10
    delay: str = "2-5min"


@app.post("/api/v1/chatting/start")
async def start_chatting(config: ChattingConfig):
    return {"status": "active", "groups": config.groups, "strategy": config.strategy}


# --- Dialogs (Neuro-Dialogs) Endpoints ---
@app.get("/api/v1/dialogs/active")
async def get_active_dialogs():
    return {
        "total_active": 12,
        "conversion_rate": 89,
        "leads": 23,
        "dialogs": [
            {"name": "Иван Петров", "stage": "hot", "last_msg": "2 мин", "status": "active"},
            {"name": "Мария Иванова", "stage": "warm", "last_msg": "15 мин", "status": "active"},
            {"name": "Олег Сидоров", "stage": "cold", "last_msg": "1 час", "status": "new"},
        ]
    }


@app.post("/api/v1/dialogs/start")
async def start_dialogs():
    return {"status": "active", "ai_mode": "auto", "funnel_steps": 4}


# --- Reactions Endpoints ---
class ReactionsConfig(BaseModel):
    channels: List[str]
    emojis: List[str] = ["👍", "❤️", "🔥", "🚀"]
    mapping: str = "ai"
    per_post: str = "50-200"
    delay: str = "1-5s"


@app.post("/api/v1/reactions/start")
async def start_reactions(config: ReactionsConfig):
    return {"status": "active", "channels": config.channels, "emojis": config.emojis}


@app.get("/api/v1/reactions/stats")
async def get_reactions_stats():
    return {"total": 12847, "today": 1456, "channels": 24}


# --- Warmup Endpoints ---
@app.get("/api/v1/warmup/accounts")
async def get_warmup_accounts():
    return [
        {"phone": "+7 (999) 123-45-67", "trust": 94, "status": "active", "dialogs": 24},
        {"phone": "+7 (999) 234-56-78", "trust": 78, "status": "warmup", "dialogs": 18},
        {"phone": "+7 (999) 345-67-89", "trust": 65, "status": "warmup", "dialogs": 12},
    ]


@app.post("/api/v1/warmup/start")
async def start_warmup():
    return {"status": "active", "anti_ban": True, "human_emulation": True}


# --- Account Manager Endpoints ---
@app.get("/api/v1/accounts")
async def list_accounts():
    return [
        {"id": 1, "phone": "+7 (999) 123-45-67", "username": "@user_account_1", "trust": 94, "status": "active", "proxy": "US", "role": "commenter"},
        {"id": 2, "phone": "+7 (999) 234-56-78", "username": "@user_account_2", "trust": 78, "status": "warmup", "proxy": "DE", "role": "chatter"},
        {"id": 3, "phone": "+7 (999) 345-67-89", "username": "@user_account_3", "trust": 65, "status": "warmup", "proxy": "NL", "role": "reactor"},
    ]


# --- Channel Management Endpoints ---
class ChannelPost(BaseModel):
    channel: str
    topic: str
    content_type: str = "analytics"
    style: str = "expert"
    length: str = "medium"


@app.get("/api/v1/channel/list")
async def list_channels():
    return [
        {"username": "@gramgpt_channel", "subscribers": 12847, "growth_week": 340, "er": 8.4},
        {"username": "@crypto_daily", "subscribers": 5234, "growth_week": 120, "er": 6.2},
    ]


@app.post("/api/v1/channel/generate-post")
async def generate_post(req: ChannelPost):
    return {
        "content": f"📊 AI-генерированный пост для {req.channel}\n\nТема: {req.topic}\nСтиль: {req.style}",
        "hashtags": ["#Crypto", "#DeFi", "#Analytics"],
        "estimated_reach": 4500
    }


@app.get("/api/v1/channel/content-plan")
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
        ]
    }


@app.get("/api/v1/channel/analytics/{channel}")
async def get_channel_analytics(channel: str):
    return {
        "channel": channel,
        "subscribers": 12847,
        "growth_percent": 12.4,
        "engagement_rate": 8.4,
        "avg_views": 4521,
        "avg_reactions": 156,
        "top_posts": [
            {"title": "Обзор ETH 2.0", "views": 8920, "reactions": 456},
            {"title": "DeFi стратегии", "views": 6340, "reactions": 312},
        ]
    }


# --- Autoresponder Endpoints ---
@app.get("/api/v1/autoresponder/scenarios")
async def get_autoresponder_scenarios():
    return {
        "scenarios": [
            {"id": 1, "name": "Приветствие", "trigger": "first_message", "enabled": True, "responses_today": 234},
            {"id": 2, "name": "Запрос цены", "trigger": "keywords", "keywords": ["цена", "стоимость", "сколько"], "enabled": True, "responses_today": 156},
            {"id": 3, "name": "FAQ", "trigger": "ai_detect", "enabled": True, "responses_today": 312},
            {"id": 4, "name": "Оффлайн-режим", "trigger": "off_hours", "enabled": True, "responses_today": 89},
            {"id": 5, "name": "Негатив/Спам", "trigger": "sentiment", "enabled": True, "responses_today": 56},
        ],
        "stats": {"total_today": 847, "accuracy": 94.2, "avg_response_time": 1.2}
    }


@app.post("/api/v1/autoresponder/start")
async def start_autoresponder():
    return {"status": "active", "message": "AI Autoresponder activated", "monitoring": True}


# --- CRM Endpoints ---
@app.get("/api/v1/crm/contacts")
async def get_crm_contacts():
    return {
        "total": 234,
        "pipeline": {
            "new": 12,
            "in_progress": 8,
            "hot": 5,
            "closed": 209
        },
        "contacts": [
            {"id": 1, "name": "Алексей К.", "username": "@alexk_crypto", "stage": "new", "tags": ["Крипто", "Парсинг"], "value": 0},
            {"id": 2, "name": "Иван П.", "username": "@ivan_trader", "stage": "in_progress", "tags": ["Трейдинг"], "value": 500},
            {"id": 3, "name": "Мария И.", "username": "@maria_inv", "stage": "hot", "tags": ["DeFi", "Инвестор"], "value": 1200},
        ]
    }


@app.get("/api/v1/crm/contact/{contact_id}")
async def get_crm_contact(contact_id: int):
    return {
        "id": contact_id,
        "name": "Мария Иванова",
        "username": "@maria_inv",
        "phone": "+7 (999) 456-78-90",
        "stage": "hot",
        "tags": ["DeFi", "Инвестор", "Pro"],
        "value": 1200,
        "history": [
            {"action": "response", "text": "Ответила на предложение", "date": "2026-05-02T14:30:00"},
            {"action": "ai_offer", "text": "AI отправил оффер (Этап 3)", "date": "2026-05-02T12:15:00"},
            {"action": "ai_warmup", "text": "AI провёл прогрев (5 сообщений)", "date": "2026-05-01T18:00:00"},
            {"action": "parsed", "text": "Спарсена из группы DeFi Трейдеры", "date": "2026-04-29T10:00:00"},
        ]
    }


# --- A/B Testing Endpoints ---
@app.get("/api/v1/abtests")
async def get_ab_tests():
    return {
        "active": [
            {
                "id": 1, "name": "Тон комментариев", "status": "active", "days_running": 7,
                "variant_a": {"name": "Экспертный", "likes": 156, "replies": 43, "conversion": 12.4, "traffic_pct": 62},
                "variant_b": {"name": "Разговорный", "likes": 98, "replies": 67, "conversion": 15.1, "traffic_pct": 38},
                "winner": "B"
            },
            {
                "id": 2, "name": "Время постинга", "status": "active", "days_running": 5,
                "variant_a": {"name": "Утро (9:00)", "views": 4521, "er": 8.2},
                "variant_b": {"name": "Вечер (20:00)", "views": 5890, "er": 11.4},
                "winner": "B"
            }
        ],
        "completed": [
            {"id": 3, "name": "Стратегия чаттинга", "winner": "Networking", "improvement": "+18%"},
            {"id": 4, "name": "Эмодзи реакции", "winner": "AI подбор", "improvement": "+42%"},
        ]
    }


# --- Templates Endpoints ---
@app.get("/api/v1/templates")
async def get_templates():
    return {
        "templates": [
            {"id": 1, "name": "Crypto Investor Funnel", "niche": "crypto", "steps": 5, "roi": 340, "installs": 1200, "price": "free"},
            {"id": 2, "name": "E-commerce Outreach", "niche": "ecommerce", "steps": 3, "roi": 280, "installs": 890, "price": "free"},
            {"id": 3, "name": "SaaS B2B Drip", "niche": "saas", "steps": 7, "roi": 420, "installs": 456, "price": "5 TON"},
            {"id": 4, "name": "Онлайн-курсы", "niche": "education", "steps": 4, "roi": 310, "installs": 678, "price": "free"},
            {"id": 5, "name": "Agency Multi-Client", "niche": "agency", "steps": 10, "roi": 550, "installs": 234, "price": "10 TON"},
            {"id": 6, "name": "NFT Community Builder", "niche": "nft", "steps": 6, "roi": 380, "installs": 567, "price": "3 TON"},
        ]
    }


# --- Reports Endpoints ---
@app.get("/api/v1/reports/generate")
async def generate_report(period: str = "month", format: str = "pdf"):
    return {
        "period": period,
        "format": format,
        "status": "generating",
        "metrics": {
            "leads": 1247,
            "revenue": 2135,
            "conversion": 89,
            "roi": 340,
            "modules": {
                "parsing": 2450,
                "commenting": 1890,
                "chatting": 1120,
                "dialogs": 847,
                "reactions": 3456
            },
            "security": {"bans": 0, "flood_waits": 3, "human_like": 97}
        }
    }


@app.get("/api/v1/reports/saved")
async def get_saved_reports():
    return {
        "reports": [
            {"id": 1, "name": "Отчёт март 2026", "format": "pdf", "size": "2.4 MB", "date": "2026-03-31"},
            {"id": 2, "name": "Отчёт февраль 2026", "format": "excel", "size": "1.8 MB", "date": "2026-02-28"},
            {"id": 3, "name": "Отчёт январь 2026", "format": "pdf", "size": "3.1 MB", "date": "2026-01-31"},
        ]
    }


# --- Referral Endpoints ---
@app.get("/api/v1/referral/stats")
async def get_referral_stats():
    return {
        "total_earned": 342,
        "this_month": 87,
        "referrals": 23,
        "active_referrals": 17,
        "commission_rate": 30,
        "link": "t.me/gramgpt_bot?start=ref_u847291",
        "rank": 14,
        "leaderboard": [
            {"name": "Кирилл М.", "referrals": 89, "earned": 4230},
            {"name": "Анна Н.", "referrals": 67, "earned": 3150},
            {"name": "Дмитрий К.", "referrals": 45, "earned": 2080},
        ]
    }


# --- Competitor Analysis Endpoints ---
@app.get("/api/v1/competitors/analysis")
async def get_competitor_analysis():
    return {
        "score": 92,
        "change": "+8",
        "competitors": [
            {"name": "GRAMGPT", "score": 92, "features": 27, "trend": "up"},
            {"name": "gramgpt.io", "score": 71, "features": 8, "trend": "stable"},
            {"name": "TGParser", "score": 45, "features": 5, "trend": "down"},
            {"name": "TeleSoft", "score": 38, "features": 4, "trend": "down"},
        ],
        "advantages": ["AI Crisis Manager", "CRM + A/B Testing", "Team Management", "Channel Management"]
    }


# --- Heatmap Endpoints ---
@app.get("/api/v1/heatmap/data")
async def get_heatmap_data():
    return {
        "peak_hour": "14:00",
        "best_day": "Wednesday",
        "actions_today": 3847,
        "avg_per_hour": 23.4,
        "by_module": {
            "parsing": 2450,
            "commenting": 1890,
            "reactions": 3456,
            "chatting": 1120,
            "dialogs": 847
        },
        "recommendations": [
            "Increase evening activity (19-21) — competitors less active, 34% higher conversion",
            "Wednesday is your best day — consider increasing limits",
            "Activate auto-mode for weekends"
        ]
    }


# --- Proxy Manager Endpoints ---
@app.get("/api/v1/proxy/pool")
async def get_proxy_pool():
    return {
        "total": 24,
        "active": 21,
        "uptime": 99.2,
        "avg_ping": 142,
        "proxies": [
            {"id": 1, "country": "US", "city": "New York", "type": "SOCKS5", "ip": "185.xx.xx.12:1080", "ping": 98, "status": "online", "accounts": 4, "uptime": 99.8},
            {"id": 2, "country": "DE", "city": "Frankfurt", "type": "HTTPS", "ip": "91.xx.xx.45:443", "ping": 67, "status": "online", "accounts": 2, "uptime": 100},
            {"id": 3, "country": "NL", "city": "Amsterdam", "type": "SOCKS5", "ip": "77.xx.xx.89:9050", "ping": 112, "status": "online", "accounts": 3, "uptime": 98.5},
            {"id": 4, "country": "UK", "city": "London", "type": "HTTP", "ip": "45.xx.xx.23:8080", "ping": 340, "status": "slow", "accounts": 1, "uptime": 92.1},
        ],
        "settings": {"auto_rotation": True, "auto_replace_banned": True, "geo_distribution": True}
    }


@app.post("/api/v1/proxy/add")
async def add_proxy(proxy_type: str = "SOCKS5", host: str = "", port: int = 1080):
    return {"status": "added", "proxy_id": 5, "type": proxy_type, "host": host, "port": port}


# --- Team Endpoints ---
@app.get("/api/v1/team/members")
async def get_team_members():
    return {
        "total": 5,
        "online": 4,
        "actions_today": 847,
        "members": [
            {"id": 1, "name": "Вы (Владелец)", "username": "@your_username", "role": "owner", "status": "online", "actions_today": 234, "modules": ["all"]},
            {"id": 2, "name": "Анна Николаева", "username": "@anna_marketing", "role": "admin", "status": "online", "actions_today": 312, "modules": ["parsing", "commenting", "crm"]},
            {"id": 3, "name": "Дмитрий Козлов", "username": "@dmitry_sales", "role": "manager", "status": "online", "actions_today": 189, "modules": ["dialogs", "chatting"]},
            {"id": 4, "name": "Елена Смирнова", "username": "@elena_content", "role": "manager", "status": "online", "actions_today": 112, "modules": ["channel", "content"]},
            {"id": 5, "name": "Михаил Попов", "username": "@mikhail_tech", "role": "viewer", "status": "offline", "last_seen": "2 часа назад", "actions_today": 0, "modules": []},
        ]
    }


@app.post("/api/v1/team/invite")
async def invite_team_member(username: str, role: str = "viewer"):
    return {"status": "invited", "link": "gramgpt.io/invite/team_abc123", "username": username, "role": role}


# --- AI Content Generator Endpoints ---
class ContentGenRequest(BaseModel):
    content_type: str = "post"
    format: str = "text"  # text, image, video, poll, story, voice
    topic: str = ""
    tone: str = "expert"
    length: str = "medium"
    language: str = "ru"
    image_style: Optional[str] = None  # realistic, art, infographic, meme, banner, sticker
    image_ratio: Optional[str] = None  # 1:1, 16:9, 9:16
    video_duration: Optional[int] = None  # 15, 30, 60
    poll_type: Optional[str] = None  # normal, quiz
    story_slides: Optional[int] = None  # 3, 5, 7, 10
    voice_gender: Optional[str] = None  # male, female
    voice_speed: Optional[float] = None  # 0.8, 1.0, 1.2


@app.post("/api/v1/content/generate")
async def generate_content(req: ContentGenRequest):
    result: Dict[str, Any] = {
        "format": req.format,
        "type": req.content_type,
        "uniqueness": 94,
    }
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


@app.get("/api/v1/content/history")
async def get_content_history():
    return {
        "total_generated": 2891,
        "history": [
            {"id": 1, "format": "image", "type": "banner", "title": "Крипто баннер для канала", "model": "DALL-E 3", "created": "30 мин назад"},
            {"id": 2, "format": "text", "type": "post", "title": "Обзор ETH 2.0", "tone": "expert", "views": 892, "created": "2 часа назад"},
            {"id": 3, "format": "poll", "type": "poll", "title": "Лучший L2 2026", "votes": 312, "created": "5 часов назад"},
            {"id": 4, "format": "video", "type": "circle", "title": "Кружочек: Утренний обзор", "views": 1247, "created": "Вчера"},
            {"id": 5, "format": "voice", "type": "voice", "title": "Голосовое: Дневной дайджест", "listens": 890, "created": "Вчера"},
        ]
    }


# --- Channel Autopilot Endpoints ---
@app.get("/api/v1/channel/trends")
async def get_channel_trends():
    return {
        "sources_count": 247,
        "last_updated": "3 мин назад",
        "trends": [
            {"rank": 1, "title": "Bitcoin пробил $150K", "sources": "CoinDesk, Bloomberg, 47 каналов", "heat": "hot", "age": "12 мин"},
            {"rank": 2, "title": "Новый L2 от Telegram", "sources": "TON Blog, Decrypt, 23 канала", "heat": "rising", "age": "34 мин"},
            {"rank": 3, "title": "SEC одобрила ETH ETF staking", "sources": "Reuters, CoinTelegraph, 18 каналов", "heat": "trending", "age": "1ч"},
            {"rank": 4, "title": "Airdrop нового DeFi протокола", "sources": "Twitter/X, 15 каналов", "heat": "new", "age": "2ч"},
        ]
    }


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


@app.post("/api/v1/channel/autopilot/config")
async def update_autopilot_config(config: AutopilotConfig):
    return {
        "status": "updated",
        "channel": config.channel,
        "autopilot": config.enabled,
        "next_post_in": "2ч 14мин",
        "posts_scheduled_today": 5
    }


@app.get("/api/v1/channel/autopilot/status")
async def get_autopilot_status():
    return {
        "enabled": True,
        "next_post_in": "2ч 14мин",
        "posts_today": 2,
        "posts_scheduled": 3,
        "trends_monitored": 247,
        "last_trend_update": "3 мин назад",
        "performance": {
            "auto_posts_views_avg": 4521,
            "manual_posts_views_avg": 3200,
            "auto_better_by": "+41%"
        }
    }


@app.get("/api/v1/channel/top-posts")
async def get_top_posts():
    return {
        "period": "week",
        "posts": [
            {"title": "Bitcoin прогноз на Q3", "format": "text", "source": "ai", "views": 12450, "new_subs": 340},
            {"title": "DeFi инфографика", "format": "image", "source": "dall-e", "views": 8920, "new_subs": 210},
            {"title": "Опрос: Лучшая L2 сеть", "format": "poll", "source": "ai", "views": 6340, "votes": 847, "new_subs": 125},
        ]
    }


# --- Audit Log Endpoints ---
@app.get("/api/v1/audit/events")
async def get_audit_events(module: Optional[str] = None, limit: int = 50):
    events = [
        {"id": 1, "type": "crm", "action": "lead_converted", "title": "Новый лид конвертирован", "details": "Мария Иванова → Горячий", "time": "14:30", "source": "auto"},
        {"id": 2, "type": "dialogs", "action": "ai_offer", "title": "AI отправил оффер", "details": "Этап 3 → @maria_inv", "time": "12:15", "source": "ai"},
        {"id": 3, "type": "security", "action": "flood_wait", "title": "Flood Wait обнаружен", "details": "Account #3 — пауза 120 сек", "time": "11:45", "source": "crisis_manager"},
        {"id": 4, "type": "commenting", "action": "viral", "title": "AI комментарий стал вирусным", "details": "NFT Новости — 21 лайк", "time": "10:32", "source": "ai"},
        {"id": 5, "type": "parsing", "action": "completed", "title": "Парсинг завершён", "details": "DeFi Группы — 456 пользователей", "time": "09:15", "source": "system"},
        {"id": 6, "type": "warmup", "action": "completed", "title": "Прогрев завершён", "details": "Account #2 — trust 78% → 82%", "time": "08:00", "source": "system"},
    ]
    if module:
        events = [e for e in events if e["type"] == module]
    return {"events": events[:limit], "total_today": 847, "yesterday_total": 847}


# --- Dashboard Endpoints ---
@app.get("/api/v1/dashboard")
async def get_dashboard():
    return {
        "metrics": {"leads": 1247, "conversion": 89, "roi": 340, "accounts": 8},
        "revenue": {
            "total": 2135,
            "chart": [120, 180, 95, 240, 320, 280, 410, 490],
            "change": "+23%"
        },
        "funnel": [
            {"stage": "Парсинг", "count": 2450},
            {"stage": "Комментинг", "count": 2080},
            {"stage": "Чаттинг", "count": 1590},
            {"stage": "Диалоги", "count": 980},
            {"stage": "Лиды", "count": 490}
        ],
        "security": {"risk_score": 12, "human_like": 97, "bans": 0}
    }


# --- Notifications Endpoints ---
@app.get("/api/v1/notifications")
async def get_notifications():
    return {
        "unread": 2,
        "notifications": [
            {"id": 1, "type": "success", "title": "Новый лид конвертирован", "message": "Иван Петров перешёл на этап Горячий", "time": "2 мин", "read": False},
            {"id": 2, "type": "info", "title": "AI комментарий стал вирусным", "message": "21 лайк и 7 ответов в NFT Новости", "time": "15 мин", "read": False},
            {"id": 3, "type": "success", "title": "Прогрев завершён", "message": "Account #2 — trust score 82%", "time": "32 мин", "read": True},
            {"id": 4, "type": "info", "title": "Пост опубликован", "message": "@gramgpt_channel — 892 просмотра", "time": "1 час", "read": True},
        ]
    }
