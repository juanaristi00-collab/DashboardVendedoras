import asyncio
import aiomysql
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    db_host: str = '25.32.163.75'
    db_port: int = 3309
    db_user: str = 'consulta'
    db_password: str = 'C0nsult@24*'
    db_name: str = 'zoftkrates_papeleria'
    class Config:
        env_file = '.env'

settings = Settings()

async def main():
    pool = await aiomysql.create_pool(
        host=settings.db_host, 
        port=settings.db_port, 
        user=settings.db_user, 
        password=settings.db_password, 
        db=settings.db_name
    )
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute('SELECT IdUsuario, count(*) FROM confresoxusuario GROUP BY IdUsuario HAVING count(*) > 1')
            dupes = await cur.fetchall()
            print('Duplicates in confresoxusuario:', dupes)

            await cur.execute('SELECT COUNT(*) FROM confresoxusuario')
            total = await cur.fetchone()
            print('Total records in confresoxusuario:', total)

            # Let's see the sum with and without the JOIN for MTD
            sql_without_join = """
                Select Sum(D.Precio * D.Cantidad * ((100 - D.Descuento) / 100) * ((100 + D.Impuesto)  / 100))
                From Enc_Ventas E
                Left Join Det_Ventas D   Using(Prefijo, Numero)
                Where Year(E.Fecha)  = Year(CurDate())
                  And Month(E.Fecha) = Month(CurDate())
            """
            await cur.execute(sql_without_join)
            print('MTD Total WITHOUT confresoxusuario join:', await cur.fetchone())

            sql_with_join = """
                Select Sum(D.Precio * D.Cantidad * ((100 - D.Descuento) / 100) * ((100 + D.Impuesto)  / 100))
                From Enc_Ventas E
                Left Join Det_Ventas D   Using(Prefijo, Numero)
                INNER JOIN confresoxusuario C ON C.IdUsuario = E.Usuario
                Where Year(E.Fecha)  = Year(CurDate())
                  And Month(E.Fecha) = Month(CurDate())
            """
            await cur.execute(sql_with_join)
            print('MTD Total WITH confresoxusuario join:', await cur.fetchone())

    pool.close()
    await pool.wait_closed()

asyncio.run(main())
