from fastapi import APIRouter, Path, Query
from fastapi.responses import JSONResponse

from app.crud.analytic import (
    get_clientes_caida,
    get_clientes_recuperados,
    get_productos_perdidos,
    get_ventas_mtd,
)

router = APIRouter(tags=["Analytics"])


# ── MTD ───────────────────────────────────────────────────────────────────────
@router.get(
    "/mtd",
    summary="Ventas MTD — mes actual vs mismo período año anterior",
)
async def ventas_mtd():
    data = await get_ventas_mtd()
    return JSONResponse({"total": len(data), "data": data})


# ── Clientes Recuperados ──────────────────────────────────────────────────────
@router.get(
    "/clientes/recuperados",
    summary="Clientes que regresan después de meses sin comprar",
)
async def clientes_recuperados(
    dias_recientes: int = Query(30,  ge=7,  le=90,  description="Ventana de compra reciente (días)"),
    meses_gap:      int = Query(6,   ge=1,  le=24,  description="Meses mínimos de ausencia para considerarse recuperado"),
):
    data = await get_clientes_recuperados(dias_recientes, meses_gap)
    return JSONResponse({"total": len(data), "data": data})


# ── Clientes en Caída ─────────────────────────────────────────────────────────
@router.get(
    "/clientes/caida",
    summary="Top clientes cuyas compras cayeron vs el período anterior",
)
async def clientes_caida(
    dias_comparar: int   = Query(90,      ge=30, le=365, description="Tamaño de cada ventana de comparación (días)"),
    minimo_venta:  float = Query(500_000, ge=0,          description="Venta mínima en el período anterior para incluir el cliente"),
):
    data = await get_clientes_caida(dias_comparar, minimo_venta)
    return JSONResponse({"total": len(data), "data": data})


# ── Productos Perdidos ────────────────────────────────────────────────────────
@router.get(
    "/productos/perdidos/{nit}",
    summary="Productos que un cliente dejó de comprar, ordenados por impacto",
)
async def productos_perdidos(
    nit:           str = Path(..., description="NIT del cliente"),
    dias_recientes: int = Query(90, ge=30, le=365, description="Ventana reciente vs histórico del año anterior"),
):
    data = await get_productos_perdidos(nit, dias_recientes)
    return JSONResponse({"total": len(data), "data": data})
