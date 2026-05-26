from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/v1", tags=["accounts"])


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
        return {"accounts": accounts, "total": len(accounts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing accounts: {str(e)}")


@router.post("/campaigns/create")
async def create_campaign(req: CampaignRequest):
    from src.core.orchestrator import orchestrator
    strategy = await orchestrator.create_campaign_strategy(req.name, req.goal)
    return {"strategy": strategy}


@router.post("/crisis/report")
async def report_crisis(req: CrisisReportRequest):
    import os, sqlite3, json
    from datetime import datetime, timedelta
    from src.core.crisis_manager import crisis_manager

    incidents_db = "data/incidents.db"
    os.makedirs("data", exist_ok=True)
    with sqlite3.connect(incidents_db) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT, account_id TEXT, type TEXT,
                details TEXT, reported_at TEXT, resolved_at TEXT
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
