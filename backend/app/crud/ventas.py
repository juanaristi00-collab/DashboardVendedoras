import re
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import aiomysql

from app.core.database import get_pool

# ── Seguridad: los campos internos de la BD nunca salen en crudo ─────────────
FIELD_MAP: dict[str, str] = {
    "TipoDoc":         "tipoDoc",
    "Numero":          "numero",
    "Prefijo":         "prefijo",
    "Fecha":           "fecha",
    "Vendedor":        "vendedor",
    "Nombre_Vendedor": "nombreVendedor",
    "Bodega":          "bodega",
    "Nit":             "nit",
    "Usuario":         "usuario",
    "Nombre_Usuario":  "nombreUsuario",
    "Producto":        "producto",
    "TCantidad":       "totalCantidad",
    "TNeto":           "totalNeto",
}

# ── Caché en memoria (TTL 1 hora) ─────────────────────────────────────────────
_cache: dict[str, tuple[list[dict], datetime]] = {}
_TTL = timedelta(hours=1)

_SQL_DIR = Path(__file__).parent.parent / "sql"


def _cache_get(key: str) -> list[dict] | None:
    entry = _cache.get(key)
    if entry:
        data, exp = entry
        if datetime.utcnow() < exp:
            return data
        del _cache[key]
    return None


def _cache_set(key: str, data: list[dict]) -> None:
    _cache[key] = (data, datetime.utcnow() + _TTL)


# ── Helpers ───────────────────────────────────────────────────────────────────
def _load_sql(filename: str) -> str:
    """Lee el .sql y convierte :param → %(param)s para aiomysql."""
    raw = (_SQL_DIR / filename).read_text(encoding="utf-8")
    return re.sub(r":(\w+)", r"%(\1)s", raw)


def _map_row(row: dict) -> dict:
    """Aplica FIELD_MAP y normaliza tipos para serialización JSON segura."""
    result: dict = {}
    for db_key, value in row.items():
        out_key = FIELD_MAP.get(db_key, db_key)  # campo desconocido pasa sin cambio

        if value is None:
            result[out_key] = None
        elif isinstance(value, (date, datetime)):
            result[out_key] = value.isoformat()
        elif isinstance(value, Decimal):
            result[out_key] = round(float(value), 2)
        elif db_key == "TNeto":
            result[out_key] = round(float(value), 2)
        elif db_key == "TCantidad":
            result[out_key] = int(value)
        else:
            result[out_key] = value

    return result


# ── Consulta pública ──────────────────────────────────────────────────────────
async def get_ventas_detalladas(fecha_inicial: str, fecha_final: str) -> list[dict]:
    key = f"ventas:{fecha_inicial}:{fecha_final}"

    if (cached := _cache_get(key)) is not None:
        return cached

    sql = _load_sql("ventas_detalladas.sql")
    pool = await get_pool()

    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(sql, {"fecha_inicial": fecha_inicial, "fecha_final": fecha_final})
            rows = await cur.fetchall()

    result = [_map_row(dict(r)) for r in rows]
    _cache_set(key, result)
    return result
