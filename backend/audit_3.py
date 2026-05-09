import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.core.database import get_pool

async def main():
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            # 1. Total FE/POSE that have Remision associated
            q1 = """
                SELECT COUNT(*), SUM(Neto) 
                FROM Enc_Ventas 
                WHERE Year(Fecha) = Year(CurDate()) 
                  And Month(Fecha) = Month(CurDate()) 
                  And (Estado IS NULL OR Estado <> 'A') 
                  And Prefijo IN ('FE', 'POSE') 
                  And Remision IS NOT NULL AND Remision <> ''
            """
            await cur.execute(q1)
            print("FE/POSE with Remision:", await cur.fetchone())

            # 2. Total Prefijo 0 that have DocRef associated
            q2 = """
                SELECT COUNT(*), SUM(Neto) 
                FROM Enc_Ventas 
                WHERE Year(Fecha) = Year(CurDate()) 
                  And Month(Fecha) = Month(CurDate()) 
                  And (Estado IS NULL OR Estado <> 'A') 
                  And Prefijo = '0' 
                  And DocRef IS NOT NULL AND DocRef <> ''
            """
            await cur.execute(q2)
            print("Prefijo 0 with DocRef:", await cur.fetchone())

            # 3. Total Prefijo 0 that have Facturado flag? Let's check if there's any other field
            q3 = """
                SELECT COUNT(*), SUM(Neto) 
                FROM Enc_Ventas 
                WHERE Year(Fecha) = Year(CurDate()) 
                  And Month(Fecha) = Month(CurDate()) 
                  And (Estado IS NULL OR Estado <> 'A') 
                  And Prefijo = '0' 
                  And (Prefijo_Aso IS NOT NULL AND Prefijo_Aso <> '')
            """
            await cur.execute(q3)
            print("Prefijo 0 with Prefijo_Aso:", await cur.fetchone())

            # 4. Check if some Prefijo 0 are entirely duplicate with FE (same Total, same Nit, same date?)
            q4 = """
                SELECT SUM(E1.Neto) 
                FROM Enc_Ventas E1
                INNER JOIN Enc_Ventas E2 ON E1.Nit = E2.Nit AND E1.Neto = E2.Neto
                WHERE Year(E1.Fecha) = Year(CurDate()) And Month(E1.Fecha) = Month(CurDate())
                  AND E1.Prefijo = '0' AND E2.Prefijo IN ('FE', 'POSE')
                  And (E1.Estado IS NULL OR E1.Estado <> 'A')
                  And (E2.Estado IS NULL OR E2.Estado <> 'A')
            """
            await cur.execute(q4)
            print("Prefijo 0 that match an FE exactly by Nit and Neto:", await cur.fetchone())

    await pool.close()
    await pool.wait_closed()

asyncio.run(main())
