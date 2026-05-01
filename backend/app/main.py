from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.analytic import router as analytic_router
from app.api.v1.ventas   import router as ventas_router
from app.core.database   import close_pool

# Rutas absolutas para el frontend
_FRONTEND     = Path(__file__).parent.parent.parent / "frontend"
_STATIC_DIR   = _FRONTEND
_DASHBOARD    = _FRONTEND / "index.html"


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_pool()


app = FastAPI(
    title="Saanye CRM API",
    description="Dashboard comercial Saanye — Zoftkrates ERP",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # restringir a IPs de red local cuando haya auth
    allow_methods=["GET"],
    allow_headers=["*"],
)

# ── API routes ────────────────────────────────────────────────────────────────
app.include_router(ventas_router,   prefix="/api/v1/ventas",     tags=["Ventas"])
app.include_router(analytic_router, prefix="/api/v1/analytics",  tags=["Analytics"])

# ── Static files (CSS / JS) — debe ir DESPUÉS de los routers ─────────────────
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

# ── UI ────────────────────────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def serve_dashboard():
    return FileResponse(str(_DASHBOARD))

@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "version": "0.2.0"}
