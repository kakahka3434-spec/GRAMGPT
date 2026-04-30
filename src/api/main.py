from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from src.core.orchestrator import orchestrator
from src.db.database import db

app = FastAPI(title="GPTGRAM Ultimate API Gateway")

class CampaignRequest(BaseModel):
    name: str
    goal: str

@app.get("/")
async def root():
    return {"status": "GPTGRAM Ultimate Engine Online"}

@app.post("/campaigns/create")
async def create_campaign(req: CampaignRequest):
    strategy = await orchestrator.create_campaign_strategy(req.name, req.goal)
    return {"strategy": strategy}

@app.get("/analytics")
async def get_analytics():
    # Mock analytics summary
    return {
        "active_accounts": 12,
        "leads_captured": 450,
        "conversion_rate": "8.5%",
        "risk_level": "low"
    }

@app.get("/leads")
async def get_leads():
    # Return last 10 leads from DB
    return {"leads": []} # Placeholder for db query
