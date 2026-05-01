import re
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import aiomysql

from app.core.database import get_pool

# ── Helpers compartidos ───────────────────────────────────────────────────────
_SQL_DIR = Path(__file__).parent.parent / "sql"


def _load_sql(filename: str) -> str:
    raw = (_SQL_DIR / filename).read_text(encoding="utf-8")
    return re.sub(r":(\w+)", r"%(\1)s", raw)


def _to_camel(s: str) -> str:
    """PascalCase → camelCase (NombreVendedor → nombreVendedor)."""
    return s[0].lower() + s[1:] if s else s


def _coerce(value):
    """Normaliza tipos para JSON: Decimal→float, date→iso, None→None."""
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def _map_row(row: dict) -> dict:
    return {_to_camel(k): _coerce(v) for k, v in row.items()}


# ── Caché con TTL configurable ────────────────────────────────────────────────
_cache: dict[str, tuple[list[dict], datetime]] = {}


def _cache_get(key: str) -> list[dict] | None:
    entry = _cache.get(key)
    if entry:
        data, exp = entry
        if datetime.utcnow() < exp:
            return data
        del _cache[key]
    return None


def _cache_set(key: str, data: list[dict], ttl_minutes: int = 60) -> None:
    _cache[key] = (data, datetime.utcnow() + timedelta(minutes=ttl_minutes))


async def _run_query(sql: str, params: dict) -> list[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(sql, params)
            rows = await cur.fetchall()
    return [_map_row(dict(r)) for r in rows]


# ── KPI 1: MTD ────────────────────────────────────────────────────────────────
async def get_ventas_mtd() -> list[dict]:
    """
    Ventas del mes actual (días 1→hoy) vs mismo período del año anterior.
    Caché 30 min porque los datos cambian durante el día.
    """
    key = f"mtd:{date.today().strftime('%Y-%m')}"
    if (cached := _cache_get(key)) is not None:
        return cached

    sql = _load_sql("ventas_mtd.sql")
    # Sin parámetros externos: usa CurDate() internamente
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(sql)
            rows = await cur.fetchall()

    result = [_map_row(dict(r)) for r in rows]
    _cache_set(key, result, ttl_minutes=30)
    return result


# ── KPI 2: Clientes Recuperados ───────────────────────────────────────────────
async def get_clientes_recuperados(
    dias_recientes: int = 30,
    meses_gap: int = 6,
) -> list[dict]:
    """
    Clientes que compraron en los últimos `dias_recientes` días
    pero su compra anterior fue hace más de `meses_gap` meses.
    """
    today = date.today()
    fecha_reciente_inicio = today - timedelta(days=dias_recientes)
    fecha_reciente_fin    = today
    fecha_limite_gap      = today - timedelta(days=meses_gap * 30)

    key = f"recuperados:{fecha_reciente_inicio}:{meses_gap}"
    if (cached := _cache_get(key)) is not None:
        return cached

    params = {
        "fecha_reciente_inicio": str(fecha_reciente_inicio),
        "fecha_reciente_fin":    str(fecha_reciente_fin),
        "fecha_limite_gap":      str(fecha_limite_gap),
    }
    result = await _run_query(_load_sql("clientes_recuperados.sql"), params)
    _cache_set(key, result)
    return result


# ── KPI 3: Clientes en Caída ──────────────────────────────────────────────────
async def get_clientes_caida(
    dias_comparar: int = 90,
    minimo_venta: float = 500_000,
) -> list[dict]:
    """
    Compara dos ventanas de `dias_comparar` días consecutivas.
    Solo devuelve clientes cuya venta cayó respecto al período anterior.
    `minimo_venta` filtra clientes de volumen muy bajo (ruido).
    """
    today = date.today()
    fecha_reciente_fin    = today
    fecha_reciente_inicio = today - timedelta(days=dias_comparar)
    fecha_anterior_fin    = fecha_reciente_inicio
    fecha_anterior_inicio = fecha_reciente_inicio - timedelta(days=dias_comparar)

    key = f"caida:{fecha_anterior_inicio}:{fecha_reciente_fin}:{minimo_venta}"
    if (cached := _cache_get(key)) is not None:
        return cached

    params = {
        "fecha_anterior_inicio": str(fecha_anterior_inicio),
        "fecha_anterior_fin":    str(fecha_anterior_fin),
        "fecha_reciente_inicio": str(fecha_reciente_inicio),
        "fecha_reciente_fin":    str(fecha_reciente_fin),
        "minimo_venta":          minimo_venta,
    }
    result = await _run_query(_load_sql("clientes_caida.sql"), params)
    _cache_set(key, result)
    return result


# ── KPI 4: Productos Perdidos ─────────────────────────────────────────────────
async def get_productos_perdidos(
    nit: str,
    dias_recientes: int = 90,
) -> list[dict]:
    """
    Para un cliente (`nit`), compara qué compraba en el año previo
    vs los últimos `dias_recientes` días.
    Devuelve los productos con mayor caída, ordenados por impacto en pesos.
    """
    today = date.today()
    fecha_rec_inicio  = today - timedelta(days=dias_recientes)
    fecha_rec_fin     = today
    fecha_hist_inicio = today - timedelta(days=365)
    fecha_hist_fin    = fecha_rec_inicio

    key = f"perdidos:{nit}:{fecha_rec_inicio}"
    if (cached := _cache_get(key)) is not None:
        return cached

    params = {
        "nit":               nit,
        "fecha_hist_inicio": str(fecha_hist_inicio),
        "fecha_hist_fin":    str(fecha_hist_fin),
        "fecha_rec_inicio":  str(fecha_rec_inicio),
        "fecha_rec_fin":     str(fecha_rec_fin),
    }
    result = await _run_query(_load_sql("productos_perdidos.sql"), params)
    _cache_set(key, result)
    return result
