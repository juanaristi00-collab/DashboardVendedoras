import asyncio, sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.core.database import get_pool

async def main():
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            # 1. Ejemplo factura→pedido con usuarios distintos
            await cur.execute("""
                SELECT 
                    E.Prefijo, E.Numero, E.Usuario AS UserFactura,
                    E.Prefijo_Aso, E.Numero_Aso,
                    P.Usuario AS UserPedido,
                    P.Vendedor AS VendedorPedido,
                    P.Neto AS NetoPedido
                FROM Enc_Ventas E
                INNER JOIN enc_pedidos P 
                    ON P.Numero = E.Numero_Aso AND P.Prefijo = E.Prefijo_Aso
                WHERE Year(E.Fecha) = 2025 AND Month(E.Fecha) = 4
                  AND E.Prefijo IN ('FE','POSE')
                LIMIT 20
            """)
            joined = await cur.fetchall()
            print("=== Factura -> Pedido (usuarios) ===")
            diff_count = 0
            for r in joined:
                diff = "** DIF" if r[2] != r[5] else "== SAME"
                if r[2] != r[5]: diff_count += 1
                print(f"  Fact {r[0]}-{r[1]} (User={r[2]}) -> Ped {r[3]}-{r[4]} (User={r[5]}, Vend={r[6]}) Neto={r[7]} {diff}")
            print(f"\n  >>> {diff_count} de {len(joined)} con usuario DIFERENTE")

            # 2. Los que NO tienen pedido - test con LEFT JOIN
            await cur.execute("""
                SELECT 
                    count(*) as total,
                    sum(case when P.Numero IS NOT NULL then 1 else 0 end) as con_pedido,
                    sum(case when P.Numero IS NULL then 1 else 0 end) as sin_pedido
                FROM Enc_Ventas E
                LEFT JOIN enc_pedidos P 
                    ON P.Numero = E.Numero_Aso AND P.Prefijo = E.Prefijo_Aso
                WHERE Year(E.Fecha) = 2025 AND Month(E.Fecha) = 4
                  AND E.Prefijo IN ('FE','POSE')
                  AND (E.Estado IS NULL OR E.Estado <> 'A')
            """)
            stats = await cur.fetchone()
            print(f"\n=== Cobertura de Pedidos ===")
            print(f"  Total facturas activas: {stats[0]}")
            print(f"  CON pedido enlazado:    {stats[1]} ({round(stats[1]/stats[0]*100,1)}%)")
            print(f"  SIN pedido:             {stats[2]} ({round(stats[2]/stats[0]*100,1)}%)")

            # 3. Campos Numero_Aso de Enc_Ventas - cuántos están vacíos
            await cur.execute("""
                SELECT 
                    count(*) as total,
                    sum(case when E.Numero_Aso IS NOT NULL AND E.Numero_Aso <> '' then 1 else 0 end) as con_aso,
                    sum(case when E.Numero_Aso IS NULL OR E.Numero_Aso = '' then 1 else 0 end) as sin_aso
                FROM Enc_Ventas E
                WHERE Year(E.Fecha) = 2025 AND Month(E.Fecha) = 4
                  AND E.Prefijo IN ('FE','POSE')
                  AND (E.Estado IS NULL OR E.Estado <> 'A')
            """)
            aso = await cur.fetchone()
            print(f"\n=== Enc_Ventas.Numero_Aso ===")
            print(f"  Con valor: {aso[1]},  Vacio: {aso[2]}")

            # 4. Verificar confresoxusuario para usuarios de pedido
            await cur.execute("""
                SELECT P.Usuario, C.IdUsuario, C.Vendedor_Asociado, V.Nombre
                FROM enc_pedidos P
                LEFT JOIN confresoxusuario C ON C.IdUsuario = P.Usuario
                LEFT JOIN Vendedor V ON V.Codigo = C.Vendedor_Asociado
                WHERE Year(P.Fecha) = 2025 AND Month(P.Fecha) = 4
                LIMIT 10
            """)
            conf = await cur.fetchall()
            print(f"\n=== enc_pedidos.Usuario -> confresoxusuario ===")
            for r in conf:
                found = "OK" if r[1] else "XX NO ENCONTRADO"
                print(f"  PedUser={r[0]} -> confreso={r[1]}, VendAsoc={r[2]}, NombreVend={r[3]} {found}")

            # 5. Mes actual (mayo 2025) - cobertura
            await cur.execute("""
                SELECT 
                    count(*) as total,
                    sum(case when E.Numero_Aso IS NOT NULL AND E.Numero_Aso <> '' then 1 else 0 end) as con_aso
                FROM Enc_Ventas E
                WHERE Year(E.Fecha) = Year(CurDate()) AND Month(E.Fecha) = Month(CurDate())
                  AND E.Prefijo IN ('FE','POSE')
                  AND (E.Estado IS NULL OR E.Estado <> 'A')
            """)
            now = await cur.fetchone()
            print(f"\n=== Mes actual: cobertura Numero_Aso ===")
            print(f"  Total: {now[0]}, Con Aso: {now[1]} ({round(now[1]/max(now[0],1)*100,1)}%)")

    await pool.close()
    await pool.wait_closed()

asyncio.run(main())
