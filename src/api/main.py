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
