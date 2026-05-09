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

def _inject_vendedor(sql: str, vendedor: str | None) -> str:
    filtro = "AND COALESCE(P.Usuario, E.Usuario) = %(vendedor)s" if vendedor else ""
    return sql.replace("{filtro_vendedor}", filtro)

async def get_vendedoras() -> list[dict]:
    """Obtiene la lista de vendedoras de los últimos 6 meses."""
    sql = _load_sql("vendedoras.sql")
    return await _run_query(sql, {})


# ── KPI 1: MTD ────────────────────────────────────────────────────────────────
async def get_ventas_mtd(
    anio: int | None = None,
    mes:  int | None = None,
    dia:  int | None = None,
    vendedor: str | None = None,
) -> list[dict]:
    """
    Ventas del período seleccionado (anio/mes, días 1→dia)
    vs mismo período del año anterior.
    - Si no se pasan parámetros usa el mes actual.
    - Para meses pasados, :dia = último día del mes (mes completo).
    - Para el mes actual, :dia = hoy.
    Caché 30 min para el mes actual; 120 min para históricos.
    """
    today = date.today()

    # Defaults inteligentes
    if anio is None: anio = today.year
    if mes  is None: mes  = today.month

    # Si es mes actual: usar día de hoy. Si es pasado: último día del mes.
    if anio == today.year and mes == today.month:
        dia_efectivo = dia if dia else today.day
        ttl = 30
    else:
        # Calcular último día del mes seleccionado
        import calendar
        dia_efectivo = dia if dia else calendar.monthrange(anio, mes)[1]
        ttl = 120

    key = f"mtd:{anio}-{mes:02d}-{dia_efectivo}:{vendedor}"
    if (cached := _cache_get(key)) is not None:
        return cached

    sql = _load_sql("ventas_mtd.sql")
    sql = _inject_vendedor(sql, vendedor)
    params = {"anio": anio, "mes": mes, "dia": dia_efectivo, "vendedor": vendedor}
    result = await _run_query(sql, params)
    _cache_set(key, result, ttl_minutes=ttl)
    return result


# ── KPI 1b: Clientes MTD (para Pareto) ───────────────────────────────────────
async def get_clientes_mtd(
    anio: int | None = None,
    mes:  int | None = None,
    vendedor: str | None = None,
) -> list[dict]:
    """
    Matriz de clientes del período: NIT, nombre, cant. facturas, valor total.
    Ordenado por TotalVenta DESC para Pareto.
    """
    import calendar
    today = date.today()
    if anio is None: anio = today.year
    if mes  is None: mes  = today.month

    if anio == today.year and mes == today.month:
        dia_efectivo = today.day
        ttl = 30
    else:
        dia_efectivo = calendar.monthrange(anio, mes)[1]
        ttl = 120

    key = f"clientes_mtd:{anio}-{mes:02d}-{dia_efectivo}:{vendedor}"
    if (cached := _cache_get(key)) is not None:
        return cached

    sql = _load_sql("clientes_mtd.sql")
    sql = _inject_vendedor(sql, vendedor)
    params = {"anio": anio, "mes": mes, "dia": dia_efectivo, "vendedor": vendedor}
    result = await _run_query(sql, params)
    _cache_set(key, result, ttl_minutes=ttl)
    return result


# ── KPI 2: Clientes Recuperados ───────────────────────────────────────────────
async def get_clientes_recuperados(
    dias_recientes: int = 30,
    meses_gap: int = 6,
    vendedor: str | None = None,
) -> list[dict]:
    """
    Clientes que compraron en los últimos `dias_recientes` días
    pero su compra anterior fue hace más de `meses_gap` meses.
    """
    today = date.today()
    fecha_reciente_inicio = today - timedelta(days=dias_recientes)
    fecha_reciente_fin    = today
    fecha_limite_gap      = today - timedelta(days=meses_gap * 30)

    key = f"recuperados:{fecha_reciente_inicio}:{meses_gap}:{vendedor}"
    if (cached := _cache_get(key)) is not None:
        return cached

    params = {
        "fecha_reciente_inicio": str(fecha_reciente_inicio),
        "fecha_reciente_fin":    str(fecha_reciente_fin),
        "fecha_limite_gap":      str(fecha_limite_gap),
        "vendedor":              vendedor,
    }
    sql = _load_sql("clientes_recuperados.sql")
    sql = _inject_vendedor(sql, vendedor)
    result = await _run_query(sql, params)
    _cache_set(key, result)
    return result


# ── KPI 3: Clientes en Caída ──────────────────────────────────────────────────
async def get_clientes_caida(
    dias_comparar: int = 90,
    minimo_venta: float = 500_000,
    vendedor: str | None = None,
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

    key = f"caida:{fecha_anterior_inicio}:{fecha_reciente_fin}:{minimo_venta}:{vendedor}"
    if (cached := _cache_get(key)) is not None:
        return cached

    params = {
        "fecha_anterior_inicio": str(fecha_anterior_inicio),
        "fecha_anterior_fin":    str(fecha_anterior_fin),
        "fecha_reciente_inicio": str(fecha_reciente_inicio),
        "fecha_reciente_fin":    str(fecha_reciente_fin),
        "minimo_venta":          minimo_venta,
        "vendedor":              vendedor,
    }
    sql = _load_sql("clientes_caida.sql")
    sql = _inject_vendedor(sql, vendedor)
    result = await _run_query(sql, params)
    _cache_set(key, result)
    return result


# ── KPI 4: Productos Perdidos ─────────────────────────────────────────────────
async def get_productos_perdidos(
    nit: str,
    dias_recientes: int = 90,
    vendedor: str | None = None,
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

    key = f"perdidos:{nit}:{fecha_rec_inicio}:{vendedor}"
    if (cached := _cache_get(key)) is not None:
        return cached

    params = {
        "nit":               nit,
        "fecha_hist_inicio": str(fecha_hist_inicio),
        "fecha_hist_fin":    str(fecha_hist_fin),
        "fecha_rec_inicio":  str(fecha_rec_inicio),
        "fecha_rec_fin":     str(fecha_rec_fin),
        "vendedor":          vendedor,
    }
    sql = _load_sql("productos_perdidos.sql")
    sql = _inject_vendedor(sql, vendedor)
    result = await _run_query(sql, params)
    _cache_set(key, result)
    return result
