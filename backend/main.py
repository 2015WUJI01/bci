import logging
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.database import init_db
from backend.routers import ws as ws_router, auth as auth_router, market as market_router, company as company_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FRONTEND_DIR = Path(os.path.dirname(os.path.dirname(__file__))) / "frontend"
MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("Database initialized")
    # Start global market engine
    from backend.game_engine import init_global_market
    await init_global_market()
    logger.info("Global market started")
    yield
    # Cancel background tasks on shutdown
    import asyncio
    for task in asyncio.all_tasks():
        if task is not asyncio.current_task() and task._coro.__name__ in (
            "price_tick_loop", "ai_trading_loop", "npc_trading_loop",
            "inst_trading_loop", "hot_money_trading_loop",
        ):
            task.cancel()
    logger.info("Background tasks cancelled")


app = FastAPI(title="大猫投资 - 股票模拟交易", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API and WebSocket routes
app.include_router(auth_router.router)
app.include_router(market_router.router)
app.include_router(ws_router.router)
app.include_router(company_router.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)


# Frontend static file serving (middleware, not catch-all route, so it doesn't block API methods)
@app.middleware("http")
async def serve_static_or_fallback(request: Request, call_next):
    response = await call_next(request)
    if response.status_code == 404:
        path = request.url.path.lstrip("/")
        safe_path = path.replace("\\", "/")
        file_path = (FRONTEND_DIR / safe_path).resolve()
        if str(file_path).startswith(str(FRONTEND_DIR.resolve())) and file_path.is_file():
            suffix = file_path.suffix.lower()
            media_type = MIME_TYPES.get(suffix, "application/octet-stream")
            return FileResponse(str(file_path), media_type=media_type)
        # SPA fallback: serve index.html for non-file paths
        # Don't intercept API 404s — let them return JSON
        if path.startswith("api/"):
            return response
        if not path or "." not in path:
            index_path = FRONTEND_DIR / "index.html"
            if index_path.is_file():
                return FileResponse(str(index_path), media_type="text/html; charset=utf-8")
    return response
