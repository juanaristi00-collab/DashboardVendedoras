import asyncio, sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.core.database import get_pool

async def main():
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:

            # 1. Ver el mapeo de sahira en confresoxusuario
            print("=== confresoxusuario WHERE IdUsuario LIKE '%sahira%' ===")
            await cur.execute("SELECT * FROM confresoxusuario WHERE LOWER(IdUsuario) LIKE '%sahira%'")
            for r in await cur.fetchall(): print(r)

            # 2. Ver TODOS los usuarios y su Vendedor_Asociado para detectar solapamientos
            print("\n=== Todos los usuarios con Vendedor_Asociado + NombreVendedor ===")
            await cur.execute("""
                SELECT C.IdUsuario, C.Vendedor_Asociado, V.Nombre
                FROM confresoxusuario C
                LEFT JOIN Vendedor V ON V.Codigo = C.Vendedor_Asociado
                WHERE C.Vendedor_Asociado IS NOT NULL AND C.Vendedor_Asociado <> ''
                ORDER BY C.IdUsuario
            """)
            for r in await cur.fetchall(): print(r)

            # 3. Buscar si existe algún vendedor con nombre Sahira
            print("\n=== Vendedores con 'sahira' o 'sahi' en el nombre ===")
            await cur.execute("SELECT * FROM Vendedor WHERE LOWER(Nombre) LIKE '%sahira%' OR LOWER(Nombre) LIKE '%sahi%'")
            for r in await cur.fetchall(): print(r)

            # 4. Cuántos usuarios apuntan al mismo Vendedor_Asociado (duplicados)
            print("\n=== Vendedor_Asociado compartidos entre múltiples usuarios ===")
            await cur.execute("""
                SELECT C.Vendedor_Asociado, V.Nombre, COUNT(*) as usuarios,
                       GROUP_CONCAT(C.IdUsuario ORDER BY C.IdUsuario) as logins
                FROM confresoxusuario C
                LEFT JOIN Vendedor V ON V.Codigo = C.Vendedor_Asociado
                WHERE C.Vendedor_Asociado <> ''
                GROUP BY C.Vendedor_Asociado
                HAVING usuarios > 1
            """)
            for r in await cur.fetchall(): print(r)

    pool.close()
    await pool.wait_closed()

asyncio.run(main())
