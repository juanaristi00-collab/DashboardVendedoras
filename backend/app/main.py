from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.analytic import router as analytic_router
from app.api.v1.ventas   import router as ventas_router
from app.core.database   import close_pool

# ── CORS ──────────────────────────────────────────────────────────────────────
# David debe configurar FRONTEND_URL en el .env del servidor.
# Ejemplo: FRONTEND_URL=https://dashboard-vendedoras-ad.vercel.app
_FRONTEND_URL = os.getenv("FRONTEND_URL", "https://dashboard-vendedoras-ad.vercel.app")

# Permitir localhost para desarrollo local
_ALLOWED_ORIGINS = [
    _FRONTEND_URL,
    "http://localhost:8000",
    "http://localhost:3000",
    "http://127.0.0.1:8000",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_pool()


app = FastAPI(
    title="Saanye CRM API",
    description="Dashboard comercial Saanye — Zoftkrates ERP",
    version="0.3.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],              # Incluye Authorization para JWT futuro
    expose_headers=["Content-Length"],
)

# ── API routes ────────────────────────────────────────────────────────────────
app.include_router(ventas_router,   prefix="/api/v1/ventas",     tags=["Ventas"])
app.include_router(analytic_router, prefix="/api/v1/analytics",  tags=["Analytics"])

# ── Health check (para Docker healthcheck y monitoreo de David) ───────────────
@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "version": "0.3.0", "frontend": _FRONTEND_URL}

