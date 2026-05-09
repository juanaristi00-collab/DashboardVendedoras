from fastapi import APIRouter, Path, Query
from fastapi.responses import JSONResponse

from app.crud.analytic import (
    get_clientes_caida,
    get_clientes_mtd,
    get_clientes_recuperados,
    get_productos_perdidos,
    get_ventas_mtd,
    get_vendedoras,
)
import json
import os
import httpx

router = APIRouter(tags=["Analytics"])

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") # Usamos la service role para poder escribir
ADMIN_PIN = "1234" # Hardcoded simple PIN for metas


# ── MTD ───────────────────────────────────────────────────────────────────────
@router.get(
    "/mtd",
    summary="Ventas MTD — período seleccionado vs mismo período año anterior",
)
async def ventas_mtd(
    anio: int | None = Query(None, ge=2020, le=2030, description="Año (default: actual)"),
    mes:  int | None = Query(None, ge=1,    le=12,   description="Mes 1-12 (default: actual)"),
    vendedor: str | None = Query(None, description="Filtrar por vendedor"),
):
    data = await get_ventas_mtd(anio=anio, mes=mes, vendedor=vendedor)
    return JSONResponse({"total": len(data), "data": data})


# ── Clientes MTD — Pareto ─────────────────────────────────────────────────────
@router.get(
    "/clientes/mtd",
    summary="Matriz de clientes del período — para análisis Pareto",
)
async def clientes_mtd(
    anio: int | None = Query(None, ge=2020, le=2030, description="Año (default: actual)"),
    mes:  int | None = Query(None, ge=1,    le=12,   description="Mes 1-12 (default: actual)"),
    vendedor: str | None = Query(None, description="Filtrar por vendedor"),
):
    data = await get_clientes_mtd(anio=anio, mes=mes, vendedor=vendedor)
    return JSONResponse({"total": len(data), "data": data})


# ── Clientes Recuperados ──────────────────────────────────────────────────────
@router.get(
    "/clientes/recuperados",
    summary="Clientes que regresan después de meses sin comprar",
)
async def clientes_recuperados(
    dias_recientes: int = Query(30,  ge=7,  le=90,  description="Ventana de compra reciente (días)"),
    meses_gap:      int = Query(6,   ge=1,  le=24,  description="Meses mínimos de ausencia para considerarse recuperado"),
    vendedor: str | None = Query(None, description="Filtrar por vendedor"),
):
    data = await get_clientes_recuperados(dias_recientes, meses_gap, vendedor=vendedor)
    return JSONResponse({"total": len(data), "data": data})


# ── Clientes en Caída ─────────────────────────────────────────────────────────
@router.get(
    "/clientes/caida",
    summary="Top clientes cuyas compras cayeron vs el período anterior",
)
async def clientes_caida(
    dias_comparar: int   = Query(90,      ge=30, le=365, description="Tamaño de cada ventana de comparación (días)"),
    minimo_venta:  float = Query(500_000, ge=0,          description="Venta mínima en el período anterior para incluir el cliente"),
    vendedor: str | None = Query(None, description="Filtrar por vendedor"),
):
    data = await get_clientes_caida(dias_comparar, minimo_venta, vendedor=vendedor)
    return JSONResponse({"total": len(data), "data": data})


# ── Productos Perdidos ────────────────────────────────────────────────────────
@router.get(
    "/productos/perdidos/{nit}",
    summary="Productos que un cliente dejó de comprar, ordenados por impacto",
)
async def productos_perdidos(
    nit:           str = Path(..., description="NIT del cliente"),
    dias_recientes: int = Query(90, ge=30, le=365, description="Ventana reciente vs histórico del año anterior"),
    vendedor: str | None = Query(None, description="Filtrar por vendedor"),
):
    data = await get_productos_perdidos(nit, dias_recientes, vendedor=vendedor)
    return JSONResponse({"total": len(data), "data": data})

# ── Vendedoras y Metas ────────────────────────────────────────────────────────
@router.get("/vendedoras", summary="Lista de vendedoras")
async def vendedoras():
    data = await get_vendedoras()
    return JSONResponse({"total": len(data), "data": data})

@router.get("/metas", summary="Obtener metas de vendedoras")
async def obtener_metas():
    if not SUPABASE_URL or not SUPABASE_KEY:
        # Fallback local (si existe)
        METAS_FILE = os.path.join(os.path.dirname(__file__), "../../../metas.json")
        if os.path.exists(METAS_FILE):
            with open(METAS_FILE, "r") as f:
                return JSONResponse(json.load(f))
        return JSONResponse({})
        
    try:
        async with httpx.AsyncClient() as client:
            headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}"
            }
            res = await client.get(f"{SUPABASE_URL}/rest/v1/vendedoras_metas", headers=headers)
            if res.status_code == 200:
                rows = res.json()
                # Convertir lista de filas a objeto JSON compatible con el frontend
                # De: [{"vendedor": "dorava", "meta_mensual": 500}, ...]
                # A: {"dorava": {"meta_mensual": 500}, ...}
                result = {row["vendedor"]: {"meta_mensual": row["meta_mensual"]} for row in rows}
                return JSONResponse(result)
    except Exception as e:
        print("Error fetching metas from Supabase:", e)
    return JSONResponse({})

@router.post("/metas", summary="Guardar metas de vendedoras")
async def guardar_metas(metas: dict, pin: str = Query(..., description="PIN de acceso")):
    if pin != ADMIN_PIN:
        return JSONResponse({"error": "PIN incorrecto"}, status_code=403)
        
    if not SUPABASE_URL or not SUPABASE_KEY:
        # Fallback local
        METAS_FILE = os.path.join(os.path.dirname(__file__), "../../../metas.json")
        with open(METAS_FILE, "w") as f:
            json.dump(metas, f, indent=2)
        return JSONResponse({"status": "ok (local fallback)"})
        
    try:
        # Transformar objeto del frontend a lista de filas para Supabase
        rows = [{"vendedor": k, "meta_mensual": v["meta_mensual"]} for k, v in metas.items()]
        
        async with httpx.AsyncClient() as client:
            headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "resolution=merge-duplicates" # Upsert (insertar o actualizar)
            }
            res = await client.post(f"{SUPABASE_URL}/rest/v1/vendedoras_metas", headers=headers, json=rows)
            if res.status_code in (200, 201):
                return JSONResponse({"status": "ok"})
            else:
                print(f"Supabase error {res.status_code}: {res.text}")
    except Exception as e:
        print("Error saving metas to Supabase:", e)
        return JSONResponse({"error": "Error de conexión con Supabase"}, status_code=500)
        
    return JSONResponse({"error": "Error al guardar en Supabase"}, status_code=500)
