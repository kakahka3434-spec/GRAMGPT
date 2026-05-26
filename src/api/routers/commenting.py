from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from src.celery_app import celery_app

router = APIRouter(prefix="/api/v1", tags=["commenting"])


class CommentingConfig(BaseModel):
    channels: List[str]
    tone: str = "expert"
    model: str = "gpt-4o"
    frequency: str = "every_2nd"


class ChattingConfig(BaseModel):
    groups: List[str]
    strategy: str = "expert"
    max_per_hour: int = 10
    delay: str = "2-5min"


class ReactionsConfig(BaseModel):
    channels: List[str]
    emojis: List[str] = ["👍", "❤️", "🔥", "🚀"]
    mapping: str = "ai"
    per_post: str = "50-200"
    delay: str = "1-5s"


@router.post("/commenting/start")
async def start_commenting(config: CommentingConfig):
    celery_app.send_task("run_commenting_task", args=[config.channels, config.tone, config.model])
    return {
        "session_id": f"celery_{config.channels[0] if config.channels else 'unknown'}",
        "status": "queued",
        "channels": config.channels,
        "tone": config.tone,
        "model": config.model,
    }


@router.get("/commenting/logs")
async def get_commenting_logs():
    return [
        {"channel": "Крипто Новости", "comment": "Отличный анализ рынка!", "likes": 12, "replies": 3, "time": "2 мин назад"},
        {"channel": "DeFi Обзоры", "comment": "Интересная стратегия!", "likes": 8, "replies": 5, "time": "15 мин назад"},
        {"channel": "NFT Новости", "comment": "Перспективный проект!", "likes": 21, "replies": 7, "time": "32 мин назад"},
    ]


@router.post("/chatting/start")
async def start_chatting(config: ChattingConfig):
    return {"status": "active", "groups": config.groups, "strategy": config.strategy}


@router.get("/dialogs/active")
async def get_active_dialogs():
    return {
        "total_active": 12, "conversion_rate": 89, "leads": 23,
        "dialogs": [
            {"name": "Иван Петров", "stage": "hot", "last_msg": "2 мин", "status": "active"},
            {"name": "Мария Иванова", "stage": "warm", "last_msg": "15 мин", "status": "active"},
            {"name": "Олег Сидоров", "stage": "cold", "last_msg": "1 час", "status": "new"},
        ]
    }


@router.post("/dialogs/start")
async def start_dialogs():
    return {"status": "active", "ai_mode": "auto", "funnel_steps": 4}


@router.post("/reactions/start")
async def start_reactions(config: ReactionsConfig):
    return {"status": "active", "channels": config.channels, "emojis": config.emojis}


@router.get("/reactions/stats")
async def get_reactions_stats():
    return {"total": 12847, "today": 1456, "channels": 24}


@router.get("/warmup/accounts")
async def get_warmup_accounts():
    return [
        {"phone": "+7 (999) 123-45-67", "trust": 94, "status": "active", "dialogs": 24},
        {"phone": "+7 (999) 234-56-78", "trust": 78, "status": "warmup", "dialogs": 18},
        {"phone": "+7 (999) 345-67-89", "trust": 65, "status": "warmup", "dialogs": 12},
    ]


@router.post("/warmup/start")
async def start_warmup():
    return {"status": "active", "anti_ban": True, "human_emulation": True}
