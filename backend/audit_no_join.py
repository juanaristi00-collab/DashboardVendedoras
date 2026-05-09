import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.core.database import get_pool

async def main():
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            q = """
                SELECT E.Prefijo, SUM(E.Neto) 
                FROM Enc_Ventas E 
                WHERE Year(E.Fecha) = Year(CurDate()) 
                  And Month(E.Fecha) = Month(CurDate()) 
                  And (E.Estado IS NULL OR E.Estado <> 'A') 
                  And E.Prefijo IN ('0', 'FE', 'POSE') 
                GROUP BY E.Prefijo
            """
            await cur.execute(q)
            print("Total NO JOIN by Prefijo:", await cur.fetchall())

            q2 = """
                SELECT SUM(E.Neto) 
                FROM Enc_Ventas E 
                WHERE Year(E.Fecha) = Year(CurDate()) 
                  And Month(E.Fecha) = Month(CurDate()) 
                  And (E.Estado IS NULL OR E.Estado <> 'A') 
                  And E.Prefijo IN ('0', 'FE', 'POSE') 
            """
            await cur.execute(q2)
            print("Total NO JOIN Overall:", await cur.fetchone())

            q3 = """
                SELECT SUM(E.Neto) 
                FROM Enc_Ventas E 
                WHERE Year(E.Fecha) = Year(CurDate()) 
                  And Month(E.Fecha) = Month(CurDate()) 
                  And (E.Estado IS NULL OR E.Estado <> 'A') 
                  And E.Prefijo IN ('FE', 'POSE') 
            """
            await cur.execute(q3)
            print("Total NO JOIN (ONLY FE/POSE):", await cur.fetchone())

    await pool.close()
    await pool.wait_closed()

asyncio.run(main())
