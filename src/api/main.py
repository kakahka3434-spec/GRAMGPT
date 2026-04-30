from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from src.api.web3 import router as web3_router
from typing import Dict, Any
from src.core.orchestrator import orchestrator
import os

app = FastAPI(title="GPTGRAM Ultimate API Gateway")
app.include_router(web3_router)

# Mount Mini App static files
static_path = os.path.join(os.path.dirname(__file__), "static/mini-app")
app.mount("/panel", StaticFiles(directory=static_path, html=True), name="panel")

class CampaignRequest(BaseModel):
    name: str
    goal: str

@app.get("/api/v1/status")
async def root():
    return {"status": "GPTGRAM Ultimate Engine Online"}

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
