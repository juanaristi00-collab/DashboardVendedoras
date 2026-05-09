import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.core.database import get_pool

async def main():
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT Codigo, Nombre FROM productos LIMIT 5")
            print("Sample productos:", await cur.fetchall())

    pool.close()
    await pool.wait_closed()

asyncio.run(main())
