import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.core.database import get_pool

async def main():
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            # combination 1: FE + POSE + 0 (without Prefijo_Aso)
            q1 = """
                SELECT SUM(Neto) 
                FROM Enc_Ventas 
                WHERE Year(Fecha) = Year(CurDate()) And Month(Fecha) = Month(CurDate()) 
                  And (Estado IS NULL OR Estado <> 'A') 
                  And (
                        Prefijo IN ('FE', 'POSE')
                        OR (Prefijo = '0' AND (Prefijo_Aso IS NULL OR Prefijo_Aso = ''))
                  )
            """
            await cur.execute(q1)
            print("FE + POSE + 0(No Aso):", await cur.fetchone())

            # combination 2: What if we subtract 0-
            q2 = """
                SELECT SUM(CASE WHEN Prefijo = '0-' THEN -Neto ELSE Neto END) 
                FROM Enc_Ventas 
                WHERE Year(Fecha) = Year(CurDate()) And Month(Fecha) = Month(CurDate()) 
                  And (Estado IS NULL OR Estado <> 'A') 
                  And (
                        Prefijo IN ('FE', 'POSE', '0-')
                        OR (Prefijo = '0' AND (Prefijo_Aso IS NULL OR Prefijo_Aso = ''))
                  )
            """
            await cur.execute(q2)
            print("FE + POSE + 0(No Aso) - 0-:", await cur.fetchone())

            # combination 3: What if we subtract 0- but KEEP all 0?
            q3 = """
                SELECT SUM(CASE WHEN Prefijo = '0-' THEN -Neto ELSE Neto END) 
                FROM Enc_Ventas 
                WHERE Year(Fecha) = Year(CurDate()) And Month(Fecha) = Month(CurDate()) 
                  And (Estado IS NULL OR Estado <> 'A') 
                  And Prefijo IN ('0', 'FE', 'POSE', '0-')
            """
            await cur.execute(q3)
            print("FE + POSE + All 0 - 0-:", await cur.fetchone())

            # combination 4: FE + POSE + 0 where Facturado something else?
            q4 = """
                SELECT SUM(Neto) 
                FROM Enc_Ventas 
                WHERE Year(Fecha) = Year(CurDate()) And Month(Fecha) = Month(CurDate()) 
                  And (Estado IS NULL OR Estado <> 'A') 
                  And (
                        Prefijo IN ('FE', 'POSE')
                        OR (Prefijo = '0' AND (DocRef IS NULL OR DocRef = ''))
                  )
            """
            await cur.execute(q4)
            print("FE + POSE + 0(No DocRef):", await cur.fetchone())

    await pool.close()
    await pool.wait_closed()

asyncio.run(main())
