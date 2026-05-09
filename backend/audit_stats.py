import os
import asyncio
import aiomysql
from dotenv import load_dotenv

load_dotenv()

async def check_stats():
    try:
        conn = await aiomysql.connect(
            host=os.getenv('DB_HOST'),
            port=int(os.getenv('DB_PORT', 3306)),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            db=os.getenv('DB_NAME_SAANYE')
        )
        async with conn.cursor() as cur:
            tables = ['Enc_Ventas', 'Det_Ventas', 'enc_pedidos', 'clientes', 'Vendedor']
            for table in tables:
                try:
                    await cur.execute(f"SELECT COUNT(*) FROM {table}")
                    count = await cur.fetchone()
                    print(f"Table {table}: {count[0]} rows")
                except Exception as e:
                    print(f"Table {table}: Error {e}")
        conn.close()
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    asyncio.run(check_stats())
