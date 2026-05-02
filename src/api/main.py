from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from src.api.web3 import router as web3_router
from typing import Dict, Any
from src.core.orchestrator import orchestrator
import os

app = FastAPI(title="GRAMGPT API")
app.include_router(web3_router)

# Mount Mini App static files
static_path = os.path.join(os.path.dirname(__file__), "static/mini-app")
app.mount("/panel", StaticFiles(directory=static_path, html=True), name="panel")

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
    return {"status": "client_added", "workspace_url": f"https://gptgram.io/w/{client_name.lower()}"}

@app.get("/api/v1/agency/stats")
async def get_agency_stats(agency_id: int):
    return {
        "total_clients": 5,
        "total_revenue_ton": 450.5,
        "sub_resellers": 2
    }
