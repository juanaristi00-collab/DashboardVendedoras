import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.core.database import get_pool

async def main():
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SHOW TABLES LIKE '%prod%'")
            tables = await cur.fetchall()
            print("Tables matching prod:", tables)
            
            for t in tables:
                table_name = t[0]
                await cur.execute(f"SHOW COLUMNS FROM {table_name}")
                cols = await cur.fetchall()
                print(f"Columns for {table_name}:", [row[0] for row in cols])

    pool.close()
    await pool.wait_closed()

asyncio.run(main())
