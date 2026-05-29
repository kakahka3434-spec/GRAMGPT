from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title="GRAMGPT API")

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
