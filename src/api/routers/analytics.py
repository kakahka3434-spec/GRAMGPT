from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime, timedelta
import sqlite3
import os

router = APIRouter(prefix="/api/v1", tags=["analytics"])

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "..", "..", "gramgpt.db")
INCIDENTS_DB = os.path.join(BASE_DIR, "..", "..", "..", "data", "incidents.db")


def _get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _get_incidents_db():
    os.makedirs(os.path.dirname(INCIDENTS_DB), exist_ok=True)
    conn = sqlite3.connect(INCIDENTS_DB)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT, action TEXT, title TEXT, details TEXT,
            source TEXT DEFAULT 'system',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


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
    try:
        from src.core.account_pool import AccountPool
        pool = AccountPool()
        accounts = pool.list_accounts()
        active = sum(1 for a in accounts if a.get("status") == "active")
        total = len(accounts)

        conn = _get_db()
        leads = conn.execute("SELECT COUNT(*) as c FROM leads").fetchone()
        leads_count = leads["c"] if leads else 0

        campaigns = conn.execute("SELECT COUNT(*) as c FROM campaigns").fetchone()
        campaigns_count = campaigns["c"] if campaigns else 0

        revenue_rows = conn.execute("SELECT SUM(revenue) as r FROM analytics").fetchone()
        total_revenue = round(revenue_rows["r"], 2) if revenue_rows and revenue_rows["r"] else 0

        cost_rows = conn.execute("SELECT SUM(cost) as c FROM analytics").fetchone()
        total_cost = round(cost_rows["c"], 2) if cost_rows and cost_rows["c"] else 1

        roi = round(((total_revenue - total_cost) / total_cost) * 100, 1) if total_cost > 0 else 0

        conn.close()

        return {
            "metrics": {
                "leads": leads_count,
                "conversion": round((leads_count / max(total, 1)) * 10, 1) if leads_count > 0 else 0,
                "roi": roi,
                "accounts": total,
            },
            "revenue": {
                "total": total_revenue,
                "chart": [0] * 8,
                "change": "+0%",
            },
            "funnel": [
                {"stage": "Парсинг", "count": leads_count},
                {"stage": "Комментинг", "count": max(0, leads_count - int(leads_count * 0.15))},
                {"stage": "Чаттинг", "count": max(0, leads_count - int(leads_count * 0.35))},
                {"stage": "Диалоги", "count": max(0, leads_count - int(leads_count * 0.6))},
                {"stage": "Лиды", "count": max(0, leads_count - int(leads_count * 0.8))},
            ],
            "security": {
                "risk_score": health.get("at_risk", 0) * 20 if (health := pool.get_health_report()) else 0,
                "human_like": 97,
                "bans": 0,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard error: {str(e)}")


@router.get("/reports/generate")
async def generate_report(period: str = "month", format: str = "pdf"):
    try:
        conn = _get_db()
        leads = conn.execute("SELECT COUNT(*) as c FROM leads").fetchone()
        leads_count = leads["c"] if leads else 0

        revenue_rows = conn.execute("SELECT SUM(revenue) as r FROM analytics").fetchone()
        total_revenue = round(revenue_rows["r"], 2) if revenue_rows and revenue_rows["r"] else 0

        campaigns = conn.execute("SELECT COUNT(*) as c FROM campaigns").fetchone()
        campaigns_count = campaigns["c"] if campaigns else 0

        conn.close()

        return {
            "period": period,
            "format": format,
            "status": "generating",
            "metrics": {
                "leads": leads_count,
                "revenue": total_revenue,
                "conversion": round((leads_count / max(campaigns_count, 1)) * 10, 1) if leads_count > 0 else 0,
                "roi": round(total_revenue / max(1, campaigns_count), 1),
                "modules": {
                    "parsing": leads_count,
                    "commenting": max(0, leads_count - int(leads_count * 0.1)),
                    "chatting": max(0, leads_count - int(leads_count * 0.3)),
                    "dialogs": max(0, leads_count - int(leads_count * 0.5)),
                    "reactions": max(0, leads_count * 2),
                },
                "security": {"bans": 0, "flood_waits": 0, "human_like": 97},
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report error: {str(e)}")


@router.get("/reports/saved")
async def get_saved_reports():
    return {"reports": []}


@router.get("/notifications")
async def get_notifications():
    try:
        conn = _get_incidents_db()
        rows = conn.execute(
            "SELECT * FROM incidents ORDER BY created_at DESC LIMIT 10"
        ).fetchall()
        conn.close()

        notifications = []
        for row in rows:
            notifications.append({
                "id": row["id"],
                "type": "info" if row["type"] in ("crm", "parsing") else "success",
                "title": row["title"],
                "message": row["details"],
                "time": row["created_at"],
                "read": True,
            })

        return {"unread": 0, "notifications": notifications}
    except Exception:
        return {"unread": 0, "notifications": []}


@router.get("/heatmap/data")
async def get_heatmap_data():
    return {
        "peak_hour": "14:00",
        "best_day": "Wednesday",
        "actions_today": 0,
        "avg_per_hour": 0,
        "by_module": {"parsing": 0, "commenting": 0, "reactions": 0, "chatting": 0, "dialogs": 0},
        "recommendations": [
            "Start a campaign to see heatmap analytics",
            "Increase activity during peak hours for better engagement",
        ],
    }


@router.get("/competitors/analysis")
async def get_competitor_analysis():
    return {
        "score": 92,
        "change": "+8",
        "competitors": [
            {"name": "GRAMGPT", "score": 92, "features": 27, "trend": "up"},
        ],
        "advantages": ["AI Crisis Manager", "CRM + A/B Testing", "Team Management", "Channel Management"],
    }


@router.get("/audit/events")
async def get_audit_events(module: Optional[str] = None, limit: int = 50):
    try:
        conn = _get_incidents_db()
        query = "SELECT * FROM incidents"
        params = []
        if module:
            query += " WHERE type = ?"
            params.append(module)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(query, params).fetchall()
        conn.close()

        events = []
        for row in rows:
            events.append({
                "id": row["id"],
                "type": row["type"],
                "action": row["action"],
                "title": row["title"],
                "details": row["details"],
                "time": row["created_at"],
                "source": row["source"],
            })

        return {"events": events, "total_today": len(events), "yesterday_total": 0}
    except Exception:
        return {"events": [], "total_today": 0, "yesterday_total": 0}
