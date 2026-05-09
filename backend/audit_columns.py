import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.core.database import get_pool

async def main():
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute('SHOW COLUMNS FROM Det_Ventas')
            cols = await cur.fetchall()
            print("Columns Det_Ventas:", [row[0] for row in cols])
            await cur.execute('SELECT Precio, Cantidad, Descuento, Impuesto, SubTotal FROM Det_Ventas LIMIT 5')
            print("Sample Det_Ventas:", await cur.fetchall())
            
            # Check what total without discount/tax would be
            await cur.execute('SELECT Sum(Precio * Cantidad) FROM Det_Ventas INNER JOIN Enc_Ventas USING(Prefijo, Numero) WHERE Year(Fecha) = Year(CurDate()) And Month(Fecha) = Month(CurDate())')
            print("Total without tax/disc logic:", await cur.fetchone())

    pool.close()
    await pool.wait_closed()

asyncio.run(main())
