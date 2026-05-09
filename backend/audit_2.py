import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.core.database import get_pool

async def main():
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            # 1. Total E.Neto vs sum of Det_Ventas for valid docs
            q = """
                SELECT 
                    SUM(E.Neto) as SumEncNeto,
                    SUM(D.Precio * D.Cantidad * ((100 - D.Descuento) / 100) * ((100 + D.Impuesto) / 100)) as SumDetalles
                FROM Enc_Ventas E
                LEFT JOIN Det_Ventas D USING(Prefijo, Numero)
                INNER JOIN confresoxusuario CxU ON CxU.IdUsuario = E.Usuario
                WHERE Year(E.Fecha) = Year(CurDate()) 
                  And Month(E.Fecha) = Month(CurDate())
                  And (E.Estado IS NULL OR E.Estado <> 'A')
                  And E.Prefijo IN ('0', 'FE', 'POSE')
            """
            await cur.execute(q)
            print("Comparison (Sum E.Neto from detail join vs Sum Details):", await cur.fetchone())

            # 2. To avoid duplicate E.Neto summing, we shouldn't join Det_Ventas when just summing headers.
            q2 = """
                SELECT SUM(E.Neto)
                FROM Enc_Ventas E
                INNER JOIN confresoxusuario CxU ON CxU.IdUsuario = E.Usuario
                WHERE Year(E.Fecha) = Year(CurDate()) 
                  And Month(E.Fecha) = Month(CurDate())
                  And (E.Estado IS NULL OR E.Estado <> 'A')
                  And E.Prefijo IN ('0', 'FE', 'POSE')
            """
            await cur.execute(q2)
            print("True Sum of E.Neto (No D join):", await cur.fetchone())

            # 3. Could Prefijo 0 be double counted if it's invoiced as FE?
            # Let's see if FE documents have a DocRef or Remision that points to a Prefijo 0
            q3 = """
                SELECT E.Prefijo, COUNT(*), SUM(E.Neto)
                FROM Enc_Ventas E
                INNER JOIN confresoxusuario CxU ON CxU.IdUsuario = E.Usuario
                WHERE Year(E.Fecha) = Year(CurDate()) 
                  And Month(E.Fecha) = Month(CurDate())
                  And (E.Estado IS NULL OR E.Estado <> 'A')
                  And E.Prefijo IN ('0', 'FE', 'POSE')
                GROUP BY E.Prefijo
            """
            await cur.execute(q3)
            print("True Sum by Prefijo (No D join):", await cur.fetchall())

            # What if we only sum FE and POSE?
            # Let's check total for just FE and POSE
            q4 = """
                SELECT SUM(E.Neto)
                FROM Enc_Ventas E
                INNER JOIN confresoxusuario CxU ON CxU.IdUsuario = E.Usuario
                WHERE Year(E.Fecha) = Year(CurDate()) 
                  And Month(E.Fecha) = Month(CurDate())
                  And (E.Estado IS NULL OR E.Estado <> 'A')
                  And E.Prefijo IN ('FE', 'POSE')
            """
            await cur.execute(q4)
            print("Total E.Neto ONLY FE and POSE:", await cur.fetchone())
            
            # Check notes / devoluciones
            q5 = """
                SELECT E.Prefijo, SUM(E.Neto)
                FROM Enc_Ventas E
                INNER JOIN confresoxusuario CxU ON CxU.IdUsuario = E.Usuario
                WHERE Year(E.Fecha) = Year(CurDate()) 
                  And Month(E.Fecha) = Month(CurDate())
                  And (E.Estado IS NULL OR E.Estado <> 'A')
                  And E.Prefijo IN ('0-')
                GROUP BY E.Prefijo
            """
            await cur.execute(q5)
            print("Total Notas (0-):", await cur.fetchall())

    pool.close()
    await pool.wait_closed()

asyncio.run(main())
