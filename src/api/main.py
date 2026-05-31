from fastapi import FastAPI, HTTPException, Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from src.api.web3 import router as web3_router
from src.api.routers.parsing import router as parsing_router
from src.api.routers.commenting import router as commenting_router
from src.api.routers.accounts import router as accounts_router
from src.api.routers.analytics import router as analytics_router
from src.api.routers.channels import router as channels_router
from src.api.routers.admin import router as admin_router
from src.api.routers.health import router as health_router
from src.api.routers.proxy import router as proxy_router
from src.core.auth_service import auth_service
from typing import Optional, List
import os
import hashlib
import hmac
import json
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

# ============ RATE LIMITING ============
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
app = FastAPI(title="GRAMGPT API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ============ CORS CONFIGURATION ============
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    os.getenv("FRONTEND_URL", "http://localhost:3000"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    expose_headers=["Content-Length", "X-Total-Count"],
    allow_headers=["Authorization", "Content-Type"],
)

# ============ TELEGRAM INIT DATA VALIDATION ============
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

def verify_telegram_init_data(init_data: str) -> Optional[dict]:
    if not BOT_TOKEN:
        return None
    try:
        parsed = dict(param.split("=", 1) for param in init_data.split("&"))
        hash_check = parsed.pop("hash", "")
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
        secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
        computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        if computed_hash == hash_check:
            return json.loads(parsed.get("user", "{}"))
    except Exception:
        pass
    return None

# ============ OPTIONAL JWT AUTH ============
security = HTTPBearer(auto_error=False)

async def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[dict]:
    if credentials is None:
        return None
    try:
        payload = auth_service.verify_token(credentials.credentials)
        return payload
    except Exception:
        return None

# ============ WEB SOCKET LIVE FEED ============
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        dead = []
        for conn in self.active_connections:
            try:
                await conn.send_json(message)
            except Exception:
                dead.append(conn)
        for d in dead:
            self.active_connections.remove(d)


manager = ConnectionManager()


@app.websocket("/ws/live")
async def websocket_live(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial ping
        await websocket.send_json({"type": "connected", "message": "Live feed active"})
        # Keep connection alive with periodic pings
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                # Client can send pings back
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
            except asyncio.TimeoutError:
                # Send keepalive ping
                try:
                    await websocket.send_json({"type": "keepalive"})
                except Exception:
                    break
    except (WebSocketDisconnect, Exception):
        manager.disconnect(websocket)


# Helper for services to push live events
async def push_live_event(event_type: str, title: str, message: str, module: str = "system"):
    await manager.broadcast({
        "type": event_type,
        "title": title,
        "message": message,
        "module": module,
        "timestamp": datetime.now().isoformat(),
    })


# Include routers (auth is optional - no token = limited data, token = full access)
app.include_router(web3_router)
app.include_router(parsing_router)
app.include_router(commenting_router)
app.include_router(accounts_router)
app.include_router(analytics_router)
app.include_router(channels_router)
app.include_router(admin_router)
app.include_router(health_router)
app.include_router(proxy_router)

# Static file paths
base_dir = os.path.dirname(__file__)
mini_app_path = os.path.join(base_dir, "static/mini-app")
landing_path = os.path.join(base_dir, "static/landing")

app.mount("/mini-app", StaticFiles(directory=mini_app_path, html=True), name="mini-app")
app.mount("/panel", StaticFiles(directory=mini_app_path, html=True), name="panel")
app.mount("/static", StaticFiles(directory=landing_path), name="landing-static")


# --- Landing Page Routes ---
@app.get("/")
async def landing_page():
    return FileResponse(os.path.join(landing_path, "index.html"))

@app.get("/robots.txt")
async def robots():
    return FileResponse(os.path.join(landing_path, "robots.txt"))

@app.get("/sitemap.xml")
async def sitemap():
    return FileResponse(os.path.join(landing_path, "sitemap.xml"))

@app.get("/blog")
async def blog_list():
    return FileResponse(os.path.join(landing_path, "blog.html"))

@app.get("/blog/{slug}")
async def blog_post(slug: str):
    return FileResponse(os.path.join(landing_path, "blog-post.html"))

@app.get("/functions")
async def functions_page():
    return FileResponse(os.path.join(landing_path, "functions.html"))

@app.get("/sw.js")
async def service_worker():
    resp = FileResponse(os.path.join(landing_path, "sw.js"))
    resp.headers["Service-Worker-Allowed"] = "/"
    resp.headers["Cache-Control"] = "no-cache"
    return resp
