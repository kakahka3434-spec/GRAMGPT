from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/api/v1", tags=["accounts"])


class AccountAdd(BaseModel):
    phone: str
    session_path: str = "data/sessions/default.session"
    proxy_id: Optional[int] = None


class AccountUpdateProxy(BaseModel):
    proxy_id: Optional[int] = None


class CrisisReportRequest(BaseModel):
    account_id: str
    incident_type: str
    details: Optional[str] = None


class CampaignRequest(BaseModel):
    name: str
    goal: str


@router.get("/accounts")
async def list_accounts():
    try:
        from src.core.account_pool import AccountPool
        pool = AccountPool()
        accounts = pool.list_accounts()

        # Enrich each account with proxy pool info
        proxies = pool.get_available_proxies()

        return {
            "accounts": accounts,
            "total": len(accounts),
            "available_proxies": proxies,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing accounts: {str(e)}")


@router.get("/accounts/available-proxies")
async def list_available_proxies():
    from src.core.account_pool import AccountPool
    pool = AccountPool()
    return {"proxies": pool.get_available_proxies()}


@router.post("/accounts/add")
async def add_account(data: AccountAdd):
    try:
        from src.core.account_pool import AccountPool
        pool = AccountPool()
        ok = pool.add_account(
            phone=data.phone,
            session_path=data.session_path,
            proxy_id=data.proxy_id,
        )
        if not ok:
            raise HTTPException(400, f"Account {data.phone} already exists")
        return {"status": "added", "phone": data.phone, "proxy_id": data.proxy_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=f"Error adding account: {str(e)}")


@router.delete("/accounts/{phone}")
async def delete_account(phone: str):
    try:
        from src.core.account_pool import AccountPool
        pool = AccountPool()
        ok = pool.remove_account(phone)
        if not ok:
            raise HTTPException(404, f"Account {phone} not found")
        return {"status": "deleted", "phone": phone}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=f"Error deleting account: {str(e)}")


@router.patch("/accounts/{phone}/proxy")
async def update_account_proxy(phone: str, data: AccountUpdateProxy):
    try:
        from src.core.account_pool import AccountPool
        pool = AccountPool()
        ok = pool.update_account_proxy(phone, data.proxy_id)
        if not ok:
            raise HTTPException(404, f"Account {phone} not found")
        return {"status": "updated", "phone": phone, "proxy_id": data.proxy_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=f"Error updating proxy: {str(e)}")


@router.get("/accounts/{phone}")
async def get_account(phone: str):
    try:
        from src.core.account_pool import AccountPool
        pool = AccountPool()
        for acc in pool.list_accounts():
            if acc["phone"] == phone:
                return acc
        raise HTTPException(404, f"Account {phone} not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.get("/campaigns/list")
async def list_campaigns():
    try:
        import os, sqlite3
        db_path = "data/campaigns.db"
        if not os.path.exists(db_path):
            return {"campaigns": [], "total": 0}
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM campaigns ORDER BY created_at DESC LIMIT 50").fetchall()
        conn.close()
        return {"campaigns": [dict(r) for r in rows], "total": len(rows)}
    except Exception as e:
        return {"campaigns": [], "total": 0, "error": str(e)}


@router.post("/campaigns/create")
async def create_campaign(req: CampaignRequest):
    from src.core.orchestrator import orchestrator
    strategy = await orchestrator.create_campaign_strategy(req.name, req.goal)
    return {"strategy": strategy}


@router.post("/crisis/report")
async def report_crisis(req: CrisisReportRequest):
    import os, sqlite3
    from datetime import datetime, timedelta
    from src.core.crisis_manager import crisis_manager

    incidents_db = "data/incidents.db"
    os.makedirs("data", exist_ok=True)
    with sqlite3.connect(incidents_db) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id TEXT, type TEXT, action TEXT, title TEXT,
                details TEXT, source TEXT DEFAULT 'system',
                reported_at TEXT, resolved_at TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute(
            "INSERT INTO incidents (account_id, type, details, reported_at) VALUES (?, ?, ?, ?)",
            (req.account_id, req.incident_type, req.details, datetime.now().isoformat())
        )
        conn.commit()

    with sqlite3.connect(incidents_db) as conn:
        cursor = conn.execute(
            "SELECT COUNT(*) FROM incidents WHERE account_id = ? AND reported_at > ?",
            (req.account_id, (datetime.now() - timedelta(hours=24)).isoformat())
        )
        incident_count = cursor.fetchone()[0]

    crisis_result = await crisis_manager.detect_crisis(req.account_id, incident_count)
    if crisis_result:
        return {"account_id": req.account_id, "action_taken": "paused", "incidents_24h": incident_count,
                "analysis": crisis_result.get("analysis", ""), "options": crisis_result.get("options", [])}
    return {"account_id": req.account_id, "action_taken": "monitoring", "incidents_24h": incident_count,
            "message": "Monitoring account, no action needed yet"}
