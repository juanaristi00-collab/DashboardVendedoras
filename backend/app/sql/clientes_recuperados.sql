-- KPI: Clientes recuperados
-- Definición: compraron en los últimos dias_recientes días
--             PERO su compra anterior fue hace más de dias_gap días (default 180 = 6 meses)
Select
    Rec.Nit,
    Cl.Nombre                               As NombreCliente,
    Rec.Vendedor,
    V.Nombre                                As NombreVendedor,
    Rec.UltimaCompra,
    Round(Rec.TotalReciente, 2)             As TotalReciente,
    Hist.UltimaCompraPrevia,
    -- Días que estuvo sin comprar
    DateDiff(Rec.UltimaCompra, Hist.UltimaCompraPrevia) As DiasAusente

From (
    -- Clientes que SÍ compraron en el período reciente
    Select
        E.Nit,
        CxU.Vendedor_Asociado As Vendedor,
        Max(E.Fecha)                        As UltimaCompra,
        Sum(
            D.Precio * D.Cantidad
            * ((100 - D.Descuento) / 100)
            * ((100 + D.Impuesto)  / 100)
        )                                   As TotalReciente
    From Enc_Ventas E
    Left Join Det_Ventas D Using(Prefijo, Numero)
    Left Join enc_pedidos P  ON P.Numero = E.Numero_Aso AND P.Prefijo = E.Prefijo_Aso
    INNER JOIN confresoxusuario CxU ON CxU.IdUsuario = COALESCE(P.Usuario, E.Usuario)
    Where E.Fecha Between :fecha_reciente_inicio And :fecha_reciente_fin
      And (E.Estado IS NULL OR E.Estado <> 'A')
      And (
          E.Prefijo IN ('FE', 'POSE')
          OR (E.Prefijo = '0' AND (E.Prefijo_Aso IS NULL OR E.Prefijo_Aso = ''))
      )
      {filtro_vendedor}
    Group By E.Nit, CxU.Vendedor_Asociado
) Rec

Inner Join (
    -- De esos clientes, solo los que llevaban mucho tiempo sin comprar
    Select
        E.Nit,
        Max(E.Fecha)                        As UltimaCompraPrevia
    From Enc_Ventas E
    Left Join enc_pedidos P  ON P.Numero = E.Numero_Aso AND P.Prefijo = E.Prefijo_Aso
    INNER JOIN confresoxusuario CxU ON CxU.IdUsuario = COALESCE(P.Usuario, E.Usuario)
    Where E.Fecha < :fecha_reciente_inicio
      And (E.Estado IS NULL OR E.Estado <> 'A')
      And (
          E.Prefijo IN ('FE', 'POSE')
          OR (E.Prefijo = '0' AND (E.Prefijo_Aso IS NULL OR E.Prefijo_Aso = ''))
      )
      {filtro_vendedor}
    Group By E.Nit
    Having Max(E.Fecha) < :fecha_limite_gap
) Hist On Hist.Nit = Rec.Nit

Left Join Vendedor V On V.Codigo = Rec.Vendedor
Left Join clientes Cl On Cl.Nit = Rec.Nit
Order By DiasAusente Desc, Rec.TotalReciente Desc
