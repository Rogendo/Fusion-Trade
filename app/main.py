"""FusionTrade AI — FastAPI application entry point."""
from __future__ import annotations

import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.core.database import init_db
from app.core.deps import limiter
from app.api.v1 import auth, fusion, journal, ml, newsletter


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialise SQLite tables on startup
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request.state.request_id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "service": settings.APP_NAME,
    }


# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(auth.router,    prefix="/api/v1/auth",    tags=["Auth"])
app.include_router(fusion.router,  prefix="/api/v1/fusion",  tags=["Fusion Intelligence"])
app.include_router(journal.router, prefix="/api/v1/journal", tags=["Trading Journal"])
app.include_router(ml.router,          prefix="/api/v1/ml",          tags=["ML Management"])
app.include_router(newsletter.router,  prefix="/api/v1/newsletter",  tags=["Newsletter"])
