import asyncio, sys, os, re
from pathlib import Path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.core.database import get_pool

async def main():
    # Carga el nuevo SQL con los usuarios
    sql_path = Path(__file__).parent / "app" / "sql" / "ventas_mtd.sql"
    sql = sql_path.read_text(encoding="utf-8")

    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            rows = await cur.fetchall()

    print(f"\n{'='*80}")
    print(f"  RESULTADO: {len(rows)} usuarios con ventas este período")
    print(f"{'='*80}")
    print(f"{'Usuario':<20} {'Asesor':<20} {'Venta Actual':>18} {'Venta Anterior':>18} {'Clientes':>10}")
    print(f"{'-'*80}")

    total_actual = 0
    total_anterior = 0
    total_clientes = 0

    for r in rows:
        usuario     = str(r[0] or '—')
        asesor      = str(r[3] or r[2] or '—')  # NombreAsesor o CodigoAsesor
        venta_act   = float(r[4] or 0)
        venta_ant   = float(r[5] or 0)
        clientes    = int(r[6] or 0)
        total_actual   += venta_act
        total_anterior += venta_ant
        total_clientes += clientes
        print(f"{usuario:<20} {asesor:<20} {venta_act:>18,.0f} {venta_ant:>18,.0f} {clientes:>10}")

    print(f"{'-'*80}")
    print(f"{'TOTAL':<20} {'':<20} {total_actual:>18,.0f} {total_anterior:>18,.0f} {total_clientes:>10}")
    print(f"\n  Venta Actual  = ${total_actual:>20,.2f}")
    print(f"  Venta Ant.    = ${total_anterior:>20,.2f}")
    pool.close()
    await pool.wait_closed()

asyncio.run(main())
