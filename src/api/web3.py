from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/web3", tags=["web3"])

class PaymentRequest(BaseModel):
    chat_id: int
    amount_ton: float
    transaction_hash: str

@router.get("/ton/connect-params")
async def get_ton_connect_params():
    """Returns manifest URL and configuration for TON Connect."""
    return {
        "manifestUrl": "https://gptgram.io/ton-connect-manifest.json",
        "network": "mainnet"
    }

@router.post("/ton/verify-payment")
async def verify_ton_payment(req: PaymentRequest):
    """Verifies TON transaction on-chain (Skeleton)."""
    # Logic to check blockchain for transaction_hash
    # Update user subscription in DB on success
    return {"status": "processing", "message": "Transaction verification in progress"}

@router.get("/ton/balance/{wallet_address}")
async def get_wallet_balance(wallet_address: str):
    return {"address": wallet_address, "balance": "0.0 TON"}
