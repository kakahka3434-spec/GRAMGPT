"""Minimal test app to check Render deployment"""
import uvicorn
from fastapi import FastAPI
import os

app = FastAPI(title="Test App")

@app.get("/")
async def root():
    return {"status": "ok", "message": "Test app running"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
