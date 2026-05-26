from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/v1", tags=["admin"])


@router.get("/marketplace/templates")
async def list_templates():
    return [
        {"id": "crypto_1", "name": "Crypto Investor Funnel", "price_ton": 5.0},
        {"id": "design_1", "name": "Design Agency Outreach", "price_ton": 3.5},
        {"id": "saas_1", "name": "SaaS B2B Drip", "price_ton": 10.0},
    ]


@router.post("/agency/clients/add")
async def add_agency_client(agency_id: int, client_name: str):
    return {"status": "client_added", "workspace_url": f"https://gramgpt.io/w/{client_name.lower()}"}


@router.get("/agency/stats")
async def get_agency_stats(agency_id: int):
    return {"total_clients": 5, "total_revenue_ton": 450.5, "sub_resellers": 2}


@router.get("/autoresponder/scenarios")
async def get_autoresponder_scenarios():
    return {
        "scenarios": [
            {"id": 1, "name": "Приветствие", "trigger": "first_message", "enabled": True, "responses_today": 234},
            {"id": 2, "name": "Запрос цены", "trigger": "keywords", "keywords": ["цена", "стоимость"], "enabled": True, "responses_today": 156},
            {"id": 3, "name": "FAQ", "trigger": "ai_detect", "enabled": True, "responses_today": 312},
        ],
        "stats": {"total_today": 847, "accuracy": 94.2, "avg_response_time": 1.2},
    }


@router.post("/autoresponder/start")
async def start_autoresponder():
    return {"status": "active", "message": "AI Autoresponder activated", "monitoring": True}


@router.get("/crm/contacts")
async def get_crm_contacts():
    return {
        "total": 234,
        "pipeline": {"new": 12, "in_progress": 8, "hot": 5, "closed": 209},
        "contacts": [
            {"id": 1, "name": "Алексей К.", "username": "@alexk_crypto", "stage": "new", "tags": ["Крипто", "Парсинг"], "value": 0},
            {"id": 2, "name": "Иван П.", "username": "@ivan_trader", "stage": "in_progress", "tags": ["Трейдинг"], "value": 500},
            {"id": 3, "name": "Мария И.", "username": "@maria_inv", "stage": "hot", "tags": ["DeFi", "Инвестор"], "value": 1200},
        ],
    }


@router.get("/crm/contact/{contact_id}")
async def get_crm_contact(contact_id: int):
    return {
        "id": contact_id, "name": "Мария Иванова", "username": "@maria_inv", "phone": "+7 (999) 456-78-90",
        "stage": "hot", "tags": ["DeFi", "Инвестор", "Pro"], "value": 1200,
        "history": [
            {"action": "response", "text": "Ответила на предложение", "date": "2026-05-02T14:30:00"},
            {"action": "ai_offer", "text": "AI отправил оффер (Этап 3)", "date": "2026-05-02T12:15:00"},
        ],
    }


@router.get("/abtests")
async def get_ab_tests():
    return {
        "active": [
            {"id": 1, "name": "Тон комментариев", "status": "active", "days_running": 7,
             "variant_a": {"name": "Экспертный", "likes": 156, "replies": 43, "conversion": 12.4, "traffic_pct": 62},
             "variant_b": {"name": "Разговорный", "likes": 98, "replies": 67, "conversion": 15.1, "traffic_pct": 38},
             "winner": "B"},
        ],
        "completed": [
            {"id": 3, "name": "Стратегия чаттинга", "winner": "Networking", "improvement": "+18%"},
        ],
    }


@router.get("/templates")
async def get_templates():
    return {
        "templates": [
            {"id": 1, "name": "Crypto Investor Funnel", "niche": "crypto", "steps": 5, "roi": 340, "installs": 1200, "price": "free"},
            {"id": 2, "name": "E-commerce Outreach", "niche": "ecommerce", "steps": 3, "roi": 280, "installs": 890, "price": "free"},
            {"id": 3, "name": "SaaS B2B Drip", "niche": "saas", "steps": 7, "roi": 420, "installs": 456, "price": "5 TON"},
        ],
    }


@router.get("/referral/stats")
async def get_referral_stats():
    return {
        "total_earned": 342, "this_month": 87, "referrals": 23, "active_referrals": 17,
        "commission_rate": 30, "link": "t.me/gramgpt_bot?start=ref_u847291", "rank": 14,
        "leaderboard": [
            {"name": "Кирилл М.", "referrals": 89, "earned": 4230},
            {"name": "Анна Н.", "referrals": 67, "earned": 3150},
        ],
    }


@router.get("/proxy/pool")
async def get_proxy_pool():
    return {
        "total": 24, "active": 21, "uptime": 99.2, "avg_ping": 142,
        "proxies": [
            {"id": 1, "country": "US", "city": "New York", "type": "SOCKS5", "ip": "185.xx.xx.12:1080", "ping": 98, "status": "online", "accounts": 4, "uptime": 99.8},
            {"id": 2, "country": "DE", "city": "Frankfurt", "type": "HTTPS", "ip": "91.xx.xx.45:443", "ping": 67, "status": "online", "accounts": 2, "uptime": 100},
        ],
        "settings": {"auto_rotation": True, "auto_replace_banned": True, "geo_distribution": True},
    }


@router.post("/proxy/add")
async def add_proxy(proxy_type: str = "SOCKS5", host: str = "", port: int = 1080):
    return {"status": "added", "proxy_id": 5, "type": proxy_type, "host": host, "port": port}


@router.get("/team/members")
async def get_team_members():
    return {
        "total": 5, "online": 4, "actions_today": 847,
        "members": [
            {"id": 1, "name": "Вы (Владелец)", "username": "@your_username", "role": "owner", "status": "online", "actions_today": 234, "modules": ["all"]},
            {"id": 2, "name": "Анна Николаева", "username": "@anna_marketing", "role": "admin", "status": "online", "actions_today": 312, "modules": ["parsing", "commenting", "crm"]},
        ],
    }


@router.post("/team/invite")
async def invite_team_member(username: str, role: str = "viewer"):
    return {"status": "invited", "link": "gramgpt.io/invite/team_abc123", "username": username, "role": role}


@router.get("/status")
async def root():
    return {"status": "GRAMGPT Engine Online"}
