from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import sqlite3, os

router = APIRouter(prefix="/api/v1", tags=["admin"])

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "..", "..", "gramgpt.db")


def _get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/marketplace/templates")
async def list_templates():
    try:
        conn = _get_db()
        rows = conn.execute("SELECT * FROM campaigns ORDER BY created_at DESC LIMIT 10").fetchall()
        conn.close()
        return [
            {
                "id": f"camp_{r['id']}",
                "name": r["name"],
                "price_ton": 0,
                "roi": r.get("roi_predicted", "N/A"),
            }
            for r in rows
        ]
    except Exception:
        return []


@router.post("/agency/clients/add")
async def add_agency_client(agency_id: int, client_name: str):
    return {"status": "client_added", "workspace_url": f"https://gramgpt.io/w/{client_name.lower()}"}


@router.get("/agency/stats")
async def get_agency_stats(agency_id: int):
    try:
        conn = _get_db()
        campaigns = conn.execute("SELECT COUNT(*) as c FROM campaigns").fetchone()
        leads = conn.execute("SELECT COUNT(*) as c FROM leads").fetchone()
        conn.close()
        return {
            "total_clients": campaigns["c"] if campaigns else 0,
            "total_revenue_ton": 0,
            "sub_resellers": 0,
        }
    except Exception:
        return {"total_clients": 0, "total_revenue_ton": 0, "sub_resellers": 0}


@router.get("/autoresponder/scenarios")
async def get_autoresponder_scenarios():
    return {
        "scenarios": [],
        "stats": {"total_today": 0, "accuracy": 0, "avg_response_time": 0},
    }


@router.post("/autoresponder/start")
async def start_autoresponder():
    return {"status": "active", "message": "AI Autoresponder placeholder", "monitoring": True}


@router.get("/crm/contacts")
async def get_crm_contacts():
    try:
        conn = _get_db()
        rows = conn.execute("SELECT * FROM leads ORDER BY last_contact DESC").fetchall()
        total = conn.execute("SELECT COUNT(*) as c FROM leads").fetchone()
        conn.close()
        pipeline = {"new": 0, "in_progress": 0, "hot": 0, "closed": 0}
        contacts = []
        for r in rows:
            status = r["status"] or "new"
            if status in pipeline:
                pipeline[status] += 1
            contacts.append({
                "id": r["id"],
                "name": r["username"] or f"User #{r['tg_id']}",
                "username": f"@{r['username']}" if r["username"] else "",
                "stage": status,
                "tags": [],
                "value": round(r["ltv_estimate"] or 0, 2),
            })
        return {"total": total["c"] if total else 0, "pipeline": pipeline, "contacts": contacts}
    except Exception:
        return {"total": 0, "pipeline": {"new": 0, "in_progress": 0, "hot": 0, "closed": 0}, "contacts": []}


@router.get("/crm/contact/{contact_id}")
async def get_crm_contact(contact_id: int):
    try:
        conn = _get_db()
        r = conn.execute("SELECT * FROM leads WHERE id = ?", (contact_id,)).fetchone()
        conn.close()
        if not r:
            raise HTTPException(status_code=404, detail="Contact not found")
        return {
            "id": r["id"],
            "name": r["username"] or f"User #{r['tg_id']}",
            "username": f"@{r['username']}" if r["username"] else "",
            "phone": "",
            "stage": r["status"] or "new",
            "tags": [],
            "value": round(r["ltv_estimate"] or 0, 2),
            "history": [],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/abtests")
async def get_ab_tests():
    return {"active": [], "completed": []}


@router.get("/templates")
async def get_templates():
    return {"templates": []}


@router.get("/referral/stats")
async def get_referral_stats():
    try:
        conn = _get_db()
        rows = conn.execute("SELECT COUNT(*) as c FROM referrals").fetchone()
        active = conn.execute("SELECT COUNT(*) as c FROM referrals WHERE status = 'active'").fetchone()
        conn.close()
        return {
            "total_earned": 0,
            "this_month": 0,
            "referrals": rows["c"] if rows else 0,
            "active_referrals": active["c"] if active else 0,
            "commission_rate": 30,
            "link": "t.me/gramgpt_bot?start=ref",
            "rank": 0,
            "leaderboard": [],
        }
    except Exception:
        return {"total_earned": 0, "this_month": 0, "referrals": 0, "active_referrals": 0,
                "commission_rate": 30, "link": "", "rank": 0, "leaderboard": []}





@router.get("/team/members")
async def get_team_members():
    return {
        "total": 1,
        "online": 1,
        "actions_today": 0,
        "members": [
            {"id": 1, "name": "Вы (Владелец)", "username": "@owner", "role": "owner",
             "status": "online", "actions_today": 0, "modules": ["all"]},
        ],
    }


@router.post("/team/invite")
async def invite_team_member(username: str, role: str = "viewer"):
    return {"status": "invited", "link": "", "username": username, "role": role}


@router.get("/status")
async def root():
    return {"status": "GRAMGPT Engine Online"}
