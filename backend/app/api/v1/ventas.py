from datetime import date

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from app.crud.ventas import get_ventas_detalladas

router = APIRouter()


@router.get(
    "/raw",
    summary="Detalle de ventas por rango de fechas",
    response_description="Líneas de venta con campos mapeados a camelCase",
)
async def ventas_raw(
    fecha_inicial: date = Query(..., description="Fecha inicio — YYYY-MM-DD"),
    fecha_final: date = Query(..., description="Fecha fin   — YYYY-MM-DD"),
):
    if fecha_final < fecha_inicial:
        raise HTTPException(status_code=400, detail="fecha_final debe ser >= fecha_inicial")

    data = await get_ventas_detalladas(str(fecha_inicial), str(fecha_final))
    return JSONResponse(content={"total": len(data), "data": data})
