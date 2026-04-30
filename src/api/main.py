from fastapi import FastAPI
from src.core.account_manager import account_manager

app = FastAPI(title="GPTGRAM Ultimate API")

@app.get("/")
async def root():
    return {"status": "GPTGRAM Ultimate is running"}

@app.get("/accounts")
async def get_accounts():
    return {"accounts_count": len(account_manager.accounts)}

@app.post("/accounts/add")
async def add_account(phone: str, proxy: str = None):
    account_manager.add_account(phone, proxy)
    return {"message": f"Account {phone} added"}
