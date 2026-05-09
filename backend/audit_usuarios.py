import asyncio
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.core.database import get_pool

async def main():
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:

            # 1. Buscar tablas con "usu" o "user" en el nombre
            print("=== TABLAS con 'usu' o 'user' ===")
            await cur.execute("""
                SELECT TABLE_NAME 
                FROM information_schema.TABLES 
                WHERE TABLE_SCHEMA = DATABASE()
                  AND (LOWER(TABLE_NAME) LIKE '%usu%' OR LOWER(TABLE_NAME) LIKE '%user%')
                ORDER BY TABLE_NAME
            """)
            for t in await cur.fetchall():
                print(t)

            # 2. TODAS las tablas de la BD
            print("\n=== TODAS las tablas ===")
            await cur.execute("""
                SELECT TABLE_NAME 
                FROM information_schema.TABLES 
                WHERE TABLE_SCHEMA = DATABASE()
                ORDER BY TABLE_NAME
            """)
            for t in await cur.fetchall():
                print(t)

            # 3. Estructura de confresoxusuario
            print("\n=== COLUMNAS confresoxusuario ===")
            await cur.execute("DESCRIBE confresoxusuario")
            for row in await cur.fetchall():
                print(row)

            # 4. Muestra de confresoxusuario
            print("\n=== MUESTRA confresoxusuario (10 filas) ===")
            await cur.execute("SELECT * FROM confresoxusuario LIMIT 10")
            for row in await cur.fetchall():
                print(row)

    pool.close()
    await pool.wait_closed()

asyncio.run(main())
