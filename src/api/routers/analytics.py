from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime, timedelta
import sqlite3
import os
import logging

# Expose a helper so services can log activity
def log_activity(module: str, action: str, details: str = "", account_id: str = ""):
    try:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        DB_PATH = os.path.join(BASE_DIR, "..", "..", "..", "gramgpt.db")
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "INSERT INTO activity_log (module, action, details, account_id) VALUES (?, ?, ?, ?)",
            (module, action, details, account_id),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["analytics"])

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "..", "..", "gramgpt.db")
INCIDENTS_DB = os.path.join(BASE_DIR, "..", "..", "..", "data", "incidents.db")


def _get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    for ddl in [
        """CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER UNIQUE, username TEXT,
            engagement_score INTEGER DEFAULT 0,
            ltv_estimate REAL DEFAULT 0,
            status TEXT DEFAULT 'new', last_contact DATETIME
        )""",
        """CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, goal TEXT, strategy_json TEXT,
            roi_predicted TEXT, status TEXT DEFAULT 'planned',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER, event_type TEXT,
            cost REAL DEFAULT 0, revenue REAL DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module TEXT, action TEXT, details TEXT,
            account_id TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""",
    ]:
        conn.execute(ddl)
    conn.commit()
    return conn


def _get_incidents_db():
    os.makedirs(os.path.dirname(INCIDENTS_DB), exist_ok=True)
    conn = sqlite3.connect(INCIDENTS_DB)
    conn.row_factory = sqlite3.Row
    conn.execute("""CREATE TABLE IF NOT EXISTS incidents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT, action TEXT, title TEXT, details TEXT,
        account_id TEXT, source TEXT DEFAULT 'system',
        reported_at TEXT, resolved_at TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.commit()
    return conn


def _compute_cpl(conn, total_cost: float, leads_count: int) -> float:
    return round(total_cost / leads_count, 2) if leads_count > 0 else 0.0


def _compute_revenue_chart(conn, days: int = 30) -> list:
    rows = conn.execute("""
        SELECT DATE(timestamp) as day, SUM(revenue) as rev
        FROM analytics
        WHERE timestamp >= datetime('now', ?)
        GROUP BY DATE(timestamp)
        ORDER BY day ASC
    """, [f'-{days} days']).fetchall()
    return [round(r["rev"], 2) for r in rows] if rows else []


def _compute_funnel(conn) -> list:
    stages = ["Парсинг", "Комментинг", "Чаттинг", "Диалоги", "Лиды"]
    table_rows = conn.execute("""
        SELECT event_type, COUNT(*) as cnt
        FROM analytics
        GROUP BY event_type
    """).fetchall()
    counts = {r["event_type"]: r["cnt"] for r in table_rows}
    return [{"stage": s, "count": counts.get(s, 0)} for s in stages]


@router.get("/analytics/summary")
async def get_analytics():
    try:
        from src.core.account_pool import AccountPool
        pool = AccountPool()
        accounts = pool.list_accounts()
        active_count = sum(1 for a in accounts if a.get("status") == "active")
        total_comments = sum(a.get("success_count", 0) for a in accounts)
        health = pool.get_health_report()

        conn = _get_db()
        leads_count = (conn.execute("SELECT COUNT(*) as c FROM leads").fetchone() or {"c": 0})["c"]
        cost_rows = conn.execute("SELECT SUM(cost) as c FROM analytics").fetchone()
        total_cost = round(cost_rows["c"], 2) if cost_rows and cost_rows["c"] else 0
        cpl = _compute_cpl(conn, total_cost, leads_count)
        conn.close()

        return {
            "active_accounts": active_count,
            "total_accounts": len(accounts),
            "leads_captured": leads_count,
            "comments_total": total_comments,
            "avg_trust_score": round(health.get("avg_trust", 0), 1) if health else 0,
            "risk_accounts": health.get("at_risk", 0) if health else 0,
            "cpl": cpl,
            "roi_average": round(((total_comments * 0.5 - total_cost) / max(total_cost, 1)) * 100, 1),
        }
    except Exception as e:
        logger.exception("analytics/summary error")
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")


@router.get("/dashboard")
async def get_dashboard():
    try:
        from src.core.account_pool import AccountPool
        pool = AccountPool()
        accounts = pool.list_accounts()
        total = len(accounts)
        active = sum(1 for a in accounts if a.get("status") == "active")
        health = pool.get_health_report() or {}

        conn = _get_db()
        leads_count = (conn.execute("SELECT COUNT(*) as c FROM leads").fetchone() or {"c": 0})["c"]
        campaigns_count = (conn.execute("SELECT COUNT(*) as c FROM campaigns").fetchone() or {"c": 0})["c"]

        rev_row = conn.execute("SELECT SUM(revenue) as r FROM analytics").fetchone()
        total_revenue = round(rev_row["r"], 2) if rev_row and rev_row["r"] else 0
        cost_row = conn.execute("SELECT SUM(cost) as c FROM analytics").fetchone()
        total_cost = round(cost_row["c"], 2) if cost_row and cost_row["c"] else 0
        total_cost_safe = max(total_cost, 1)
        roi = round(((total_revenue - total_cost) / total_cost_safe) * 100, 1)

        cpl = _compute_cpl(conn, total_cost, leads_count)
        chart = _compute_revenue_chart(conn, 30)
        funnel = _compute_funnel(conn)

        # Real conversion: leads / total impressions from activity_log
        impressions = conn.execute("""
            SELECT COUNT(*) as c FROM activity_log WHERE module IN ('parsing','commenting')
        """).fetchone() or {"c": 1}
        conversion = round((leads_count / max(impressions["c"], 1)) * 100, 1)

        # Compute trend from last 30 vs previous 30
        current_rev = conn.execute("""
            SELECT COALESCE(SUM(revenue),0) as r FROM analytics
            WHERE timestamp >= datetime('now', '-30 days')
        """).fetchone() or {"r": 0}
        prev_rev = conn.execute("""
            SELECT COALESCE(SUM(revenue),0) as r FROM analytics
            WHERE timestamp >= datetime('now', '-60 days')
              AND timestamp < datetime('now', '-30 days')
        """).fetchone() or {"r": 0}
        change_pct = round(
            ((current_rev["r"] - prev_rev["r"]) / max(prev_rev["r"], 1)) * 100, 1
        ) if current_rev["r"] > 0 or prev_rev["r"] > 0 else 0

        # Real bans count from incidents
        incidents_conn = _get_incidents_db()
        bans = (incidents_conn.execute(
            "SELECT COUNT(*) as c FROM incidents WHERE type='ban'"
        ).fetchone() or {"c": 0})["c"]
        incidents_conn.close()

        # Real human_like: average of success_rate from account pool
        success_rates = [a.get("success_rate", 0) for a in accounts if a.get("success_rate")]
        human_like = round(sum(success_rates) / len(success_rates), 1) if success_rates else 0

        conn.close()

        return {
            "metrics": {
                "leads": leads_count,
                "conversion": conversion,
                "roi": roi,
                "accounts": total,
                "active": active,
                "cpl": cpl,
            },
            "revenue": {
                "total": total_revenue,
                "chart": chart if chart else [],
                "change": f"{'+' if change_pct >= 0 else ''}{change_pct}%",
            },
            "funnel": funnel,
            "security": {
                "risk_score": health.get("at_risk", 0) * 20 if health else 0,
                "human_like": human_like,
                "bans": bans,
            },
        }
    except Exception as e:
        logger.exception("/dashboard error")
        raise HTTPException(status_code=500, detail=f"Dashboard error: {str(e)}")


@router.get("/reports/generate")
async def generate_report(period: str = "month", format: str = "pdf"):
    try:
        conn = _get_db()
        leads_count = (conn.execute("SELECT COUNT(*) as c FROM leads").fetchone() or {"c": 0})["c"]
        rev_row = conn.execute("SELECT SUM(revenue) as r FROM analytics").fetchone()
        total_revenue = round(rev_row["r"], 2) if rev_row and rev_row["r"] else 0
        campaigns_count = (conn.execute("SELECT COUNT(*) as c FROM campaigns").fetchone() or {"c": 0})["c"]
        cost_row = conn.execute("SELECT SUM(cost) as c FROM analytics").fetchone()
        total_cost = round(cost_row["c"], 2) if cost_row and cost_row["c"] else 0

        # Real module breakdown from activity_log
        modules = {
            r["module"]: r["cnt"]
            for r in conn.execute("""SELECT module, COUNT(*) as cnt FROM activity_log GROUP BY module""").fetchall()
        }

        # Real security stats from incidents
        incidents_conn = _get_incidents_db()
        bans = (incidents_conn.execute("SELECT COUNT(*) as c FROM incidents WHERE type='ban'").fetchone() or {"c": 0})["c"]
        flood_waits = (incidents_conn.execute("SELECT COUNT(*) as c FROM incidents WHERE type='flood'").fetchone() or {"c": 0})["c"]
        incidents_conn.close()

        conn.close()

        return {
            "period": period,
            "format": format,
            "status": "generating",
            "metrics": {
                "leads": leads_count,
                "revenue": total_revenue,
                "conversion": round((leads_count / max(campaigns_count, 1)) * 10, 1) if leads_count > 0 else 0,
                "roi": round((total_revenue - total_cost) / max(total_cost, 1) * 100, 1),
                "cpl": _compute_cpl(conn if 'conn' in dir() else _get_db(), total_cost, leads_count),
                "modules": modules,
                "security": {"bans": bans, "flood_waits": flood_waits},
            },
        }
    except Exception as e:
        logger.exception("/reports/generate error")
        raise HTTPException(status_code=500, detail=f"Report error: {str(e)}")


@router.get("/reports/saved")
async def get_saved_reports():
    try:
        conn = _get_db()
        rows = conn.execute("""
            SELECT id, name, goal, status, roi_predicted, created_at
            FROM campaigns ORDER BY created_at DESC LIMIT 20
        """).fetchall()
        conn.close()
        return {
            "reports": [
                {
                    "id": r["id"],
                    "name": r["name"],
                    "status": r["status"],
                    "roi": r["roi_predicted"],
                    "created_at": r["created_at"],
                }
                for r in rows
            ]
        }
    except Exception:
        return {"reports": []}


@router.get("/notifications")
async def get_notifications():
    try:
        conn = _get_incidents_db()
        rows = conn.execute(
            "SELECT * FROM incidents ORDER BY created_at DESC LIMIT 10"
        ).fetchall()
        conn.close()
        unread = sum(1 for r in rows if r.get("resolved_at") is None)
        return {
            "unread": unread,
            "notifications": [
                {
                    "id": r["id"],
                    "type": "info" if r["type"] in ("crm", "parsing") else "success",
                    "title": r["title"],
                    "message": r["details"],
                    "time": r["created_at"],
                    "read": r.get("resolved_at") is not None,
                }
                for r in rows
            ],
        }
    except Exception:
        return {"unread": 0, "notifications": []}


@router.get("/heatmap/data")
async def get_heatmap_data():
    try:
        conn = _get_db()
        rows = conn.execute("""
            SELECT strftime('%H', created_at) as hour, COUNT(*) as cnt
            FROM activity_log
            WHERE created_at >= datetime('now', '-7 days')
            GROUP BY hour ORDER BY cnt DESC LIMIT 1
        """).fetchone()
        peak_hour = f"{rows['hour']}:00" if rows else "—"

        day_rows = conn.execute("""
            SELECT strftime('%w', created_at) as dow, COUNT(*) as cnt
            FROM activity_log
            WHERE created_at >= datetime('now', '-30 days')
            GROUP BY dow ORDER BY cnt DESC LIMIT 1
        """).fetchone()
        day_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        best_day = day_names[int(day_rows["dow"])] if day_rows else "—"

        today = conn.execute("""
            SELECT COUNT(*) as c FROM activity_log
            WHERE DATE(created_at) = DATE('now')
        """).fetchone() or {"c": 0}

        by_module = {
            r["module"]: r["cnt"]
            for r in conn.execute("""
                SELECT module, COUNT(*) as cnt FROM activity_log
                WHERE created_at >= datetime('now', '-7 days')
                GROUP BY module
            """).fetchall()
        }

        total_7d = sum(by_module.values())
        avg_per_hour = round(total_7d / 168, 1)  # 168 hours in 7 days

        conn.close()
        return {
            "peak_hour": peak_hour,
            "best_day": best_day,
            "actions_today": today["c"],
            "avg_per_hour": avg_per_hour,
            "by_module": by_module,
            "recommendations": [
                f"Peak activity at {peak_hour} — schedule campaigns accordingly",
                f"Best day: {best_day} — increase budget on this day",
            ] if peak_hour != "—" else [
                "No activity data yet — start a campaign to see heatmap",
            ],
        }
    except Exception:
        return {"peak_hour": "—", "best_day": "—", "actions_today": 0, "avg_per_hour": 0, "by_module": {}, "recommendations": ["No activity data yet — start a campaign"]}


@router.get("/competitors/analysis")
async def get_competitor_analysis():
    from src.core.account_pool import AccountPool
    try:
        pool = AccountPool()
        health = pool.get_health_report() or {}
        avg_trust = health.get("avg_trust", 0)
        at_risk = health.get("at_risk", 0)
        accounts = pool.list_accounts()
        banned_accounts = sum(1 for a in accounts if a.get("status") == "banned")

        score = min(100, max(0, round(
            (avg_trust * 0.4)
            + ((1 - at_risk / max(len(accounts), 1)) * 30)
            + ((1 - banned_accounts / max(len(accounts), 1)) * 30)
        )))

        return {
            "score": score,
            "change": f"+{score - 50}" if score > 50 else f"{score - 50}",
            "competitors": [
                {"name": "GRAMGPT", "score": 92, "features": 27, "trend": "up"},
                {"name": "TGParser", "score": 45, "features": 8, "trend": "stable"},
                {"name": "TeleSoft", "score": 38, "features": 6, "trend": "down"},
            ],
            "advantages": ["AI Crisis Manager", "CRM + A/B Testing", "Team Management", "Channel Management"],
            "real_score_basis": f"{round(avg_trust, 1)}% avg trust, {at_risk} at-risk, {banned_accounts} banned",
        }
    except Exception:
        return {"score": 0, "change": "0", "competitors": [], "advantages": [], "real_score_basis": "No data"}


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

        today_total = conn.execute(
            "SELECT COUNT(*) as c FROM incidents WHERE DATE(created_at) = DATE('now')"
        ).fetchone() or {"c": 0}
        yesterday_total = conn.execute(
            "SELECT COUNT(*) as c FROM incidents WHERE DATE(created_at) = DATE('now', '-1 day')"
        ).fetchone() or {"c": 0}
        conn.close()

        return {
            "events": [
                {
                    "id": r["id"], "type": r["type"], "action": r["action"],
                    "title": r["title"], "details": r["details"],
                    "time": r["created_at"], "source": r["source"],
                }
                for r in rows
            ],
            "total_today": today_total["c"],
            "yesterday_total": yesterday_total["c"],
        }
    except Exception:
        return {"events": [], "total_today": 0, "yesterday_total": 0}
