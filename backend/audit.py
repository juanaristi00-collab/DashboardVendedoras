import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_pool

async def main():
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute('SELECT IdUsuario, count(*) FROM confresoxusuario GROUP BY IdUsuario HAVING count(*) > 1')
            dupes = await cur.fetchall()
            print('Duplicates in confresoxusuario (IdUsuario):', dupes)

            await cur.execute('SELECT * FROM confresoxusuario LIMIT 5')
            sample = await cur.fetchall()
            print('Sample confresoxusuario:', sample)

            # check total sum without join
            sql1 = """
                Select Sum(D.Precio * D.Cantidad * ((100 - D.Descuento) / 100) * ((100 + D.Impuesto)  / 100))
                From Enc_Ventas E
                Left Join Det_Ventas D   Using(Prefijo, Numero)
                Where Year(E.Fecha)  = Year(CurDate())
                  And Month(E.Fecha) = Month(CurDate())
            """
            await cur.execute(sql1)
            print('MTD Total WITHOUT join:', await cur.fetchone())

            sql2 = """
                Select Sum(D.Precio * D.Cantidad * ((100 - D.Descuento) / 100) * ((100 + D.Impuesto)  / 100))
                From Enc_Ventas E
                Left Join Det_Ventas D   Using(Prefijo, Numero)
                INNER JOIN confresoxusuario C ON C.IdUsuario = E.Usuario
                Where Year(E.Fecha)  = Year(CurDate())
                  And Month(E.Fecha) = Month(CurDate())
            """
            await cur.execute(sql2)
            print('MTD Total WITH join:', await cur.fetchone())

    await pool.close()
    await pool.wait_closed()

asyncio.run(main())
