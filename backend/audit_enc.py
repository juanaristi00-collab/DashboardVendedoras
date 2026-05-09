import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.core.database import get_pool

async def main():
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute('SELECT Prefijo, Estado, Count(*), Sum(Neto) FROM Enc_Ventas WHERE Year(Fecha) = Year(CurDate()) And Month(Fecha) = Month(CurDate()) GROUP BY Prefijo, Estado')
            stats = await cur.fetchall()
            print("Stats (Prefijo, Estado, Count, Sum(Neto)):")
            for row in stats:
                print(row)

    await pool.close()
    await pool.wait_closed()

asyncio.run(main())
