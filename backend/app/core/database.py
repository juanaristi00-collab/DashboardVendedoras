import aiomysql
from app.core.config import settings

_pool: aiomysql.Pool | None = None


async def get_pool() -> aiomysql.Pool:
    global _pool
    if _pool is None:
        _pool = await aiomysql.create_pool(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            db=settings.DB_NAME_SAANYE,
            charset="utf8mb4",
            autocommit=True,
            minsize=0,          # Crítico en Serverless para no dejar conexiones huérfanas
            maxsize=2,          
            connect_timeout=5,  # Si no conecta en 5 segundos, que falle rápido en lugar de colgar Vercel
        )
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        await _pool.wait_closed()
        _pool = None
