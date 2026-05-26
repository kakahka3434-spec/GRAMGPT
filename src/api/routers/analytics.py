from fastapi import APIRouter, HTTPException
from typing import Optional

router = APIRouter(prefix="/api/v1", tags=["analytics"])


@router.get("/analytics/summary")
async def get_analytics():
    try:
        from src.core.account_pool import AccountPool
        pool = AccountPool()
        accounts = pool.list_accounts()
        active_count = sum(1 for a in accounts if a.get("status") == "active")
        total_comments = sum(a.get("success_count", 0) for a in accounts)
        health = pool.get_health_report()
        return {
            "active_accounts": active_count,
            "total_accounts": len(accounts),
            "comments_total": total_comments,
            "avg_trust_score": round(health.get("avg_trust", 0), 1),
            "risk_accounts": health.get("at_risk", 0),
            "roi_average": "N/A (real tracking needed)",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")


@router.get("/dashboard")
async def get_dashboard():
    return {
        "metrics": {"leads": 1247, "conversion": 89, "roi": 340, "accounts": 8},
        "revenue": {"total": 2135, "chart": [120, 180, 95, 240, 320, 280, 410, 490], "change": "+23%"},
        "funnel": [
            {"stage": "Парсинг", "count": 2450},
            {"stage": "Комментинг", "count": 2080},
            {"stage": "Чаттинг", "count": 1590},
            {"stage": "Диалоги", "count": 980},
            {"stage": "Лиды", "count": 490},
        ],
        "security": {"risk_score": 12, "human_like": 97, "bans": 0},
    }


@router.get("/reports/generate")
async def generate_report(period: str = "month", format: str = "pdf"):
    return {
        "period": period, "format": format, "status": "generating",
        "metrics": {
            "leads": 1247, "revenue": 2135, "conversion": 89, "roi": 340,
            "modules": {"parsing": 2450, "commenting": 1890, "chatting": 1120, "dialogs": 847, "reactions": 3456},
            "security": {"bans": 0, "flood_waits": 3, "human_like": 97},
        },
    }


@router.get("/reports/saved")
async def get_saved_reports():
    return {
        "reports": [
            {"id": 1, "name": "Отчёт март 2026", "format": "pdf", "size": "2.4 MB", "date": "2026-03-31"},
            {"id": 2, "name": "Отчёт февраль 2026", "format": "excel", "size": "1.8 MB", "date": "2026-02-28"},
            {"id": 3, "name": "Отчёт январь 2026", "format": "pdf", "size": "3.1 MB", "date": "2026-01-31"},
        ]
    }


@router.get("/notifications")
async def get_notifications():
    return {
        "unread": 2,
        "notifications": [
            {"id": 1, "type": "success", "title": "Новый лид конвертирован", "message": "Иван Петров → Горячий", "time": "2 мин", "read": False},
            {"id": 2, "type": "info", "title": "AI комментарий стал вирусным", "message": "21 лайк в NFT Новости", "time": "15 мин", "read": False},
            {"id": 3, "type": "success", "title": "Прогрев завершён", "message": "Account #2 — trust score 82%", "time": "32 мин", "read": True},
            {"id": 4, "type": "info", "title": "Пост опубликован", "message": "@gramgpt_channel — 892 просмотра", "time": "1 час", "read": True},
        ],
    }


@router.get("/heatmap/data")
async def get_heatmap_data():
    return {
        "peak_hour": "14:00", "best_day": "Wednesday", "actions_today": 3847, "avg_per_hour": 23.4,
        "by_module": {"parsing": 2450, "commenting": 1890, "reactions": 3456, "chatting": 1120, "dialogs": 847},
        "recommendations": [
            "Increase evening activity (19-21) — competitors less active, 34% higher conversion",
            "Wednesday is your best day",
            "Activate auto-mode for weekends",
        ],
    }


@router.get("/competitors/analysis")
async def get_competitor_analysis():
    return {
        "score": 92, "change": "+8",
        "competitors": [
            {"name": "GRAMGPT", "score": 92, "features": 27, "trend": "up"},
            {"name": "gramgpt.io", "score": 71, "features": 8, "trend": "stable"},
            {"name": "TGParser", "score": 45, "features": 5, "trend": "down"},
            {"name": "TeleSoft", "score": 38, "features": 4, "trend": "down"},
        ],
        "advantages": ["AI Crisis Manager", "CRM + A/B Testing", "Team Management", "Channel Management"],
    }


@router.get("/audit/events")
async def get_audit_events(module: Optional[str] = None, limit: int = 50):
    events = [
        {"id": 1, "type": "crm", "action": "lead_converted", "title": "Новый лид конвертирован", "details": "Мария Иванова → Горячий", "time": "14:30", "source": "auto"},
        {"id": 2, "type": "dialogs", "action": "ai_offer", "title": "AI отправил оффер", "details": "Этап 3 → @maria_inv", "time": "12:15", "source": "ai"},
        {"id": 3, "type": "security", "action": "flood_wait", "title": "Flood Wait обнаружен", "details": "Account #3 — пауза 120 сек", "time": "11:45", "source": "crisis_manager"},
        {"id": 4, "type": "commenting", "action": "viral", "title": "AI комментарий стал вирусным", "details": "NFT Новости — 21 лайк", "time": "10:32", "source": "ai"},
        {"id": 5, "type": "parsing", "action": "completed", "title": "Парсинг завершён", "details": "DeFi Группы — 456 пользователей", "time": "09:15", "source": "system"},
    ]
    if module:
        events = [e for e in events if e["type"] == module]
    return {"events": events[:limit], "total_today": 847, "yesterday_total": 847}
