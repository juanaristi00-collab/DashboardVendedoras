-- KPI: Productos que un cliente dejó de comprar (o redujo significativamente)
-- Compara histórico (:fecha_hist_inicio → :fecha_hist_fin)
--         vs reciente (:fecha_rec_inicio  → :fecha_rec_fin)
-- Devuelve ordenado por Impacto (mayor pérdida de venta primero)
Select
    Hist.Producto,
    Prod.Nombre As NombreProducto,
    Round(Hist.TotalHistorico, 2)                           As TotalHistorico,
    Round(Coalesce(Rec.TotalReciente, 0), 2)                As TotalReciente,
    Hist.CantHistorica,
    Coalesce(Rec.CantReciente, 0)                           As CantReciente,
    Round(
        Hist.TotalHistorico - Coalesce(Rec.TotalReciente, 0)
    , 2)                                                    As Impacto,
    Round(
        (Coalesce(Rec.TotalReciente, 0) - Hist.TotalHistorico)
        / Nullif(Hist.TotalHistorico, 0) * 100
    , 1)                                                    As PctCambioValor,
    Round(
        (Coalesce(Rec.CantReciente, 0) - Hist.CantHistorica)
        / Nullif(Hist.CantHistorica, 0) * 100
    , 1)                                                    As PctCambioCant

From (
    Select
        D.Producto,
        Sum(D.Cantidad) As CantHistorica,
        Sum(
            D.Precio * D.Cantidad
            * ((100 - D.Descuento) / 100)
            * ((100 + D.Impuesto)  / 100)
        )                                                   As TotalHistorico
    From Enc_Ventas E
    Left Join Det_Ventas D Using(Prefijo, Numero)
    Left Join enc_pedidos P  ON P.Numero = E.Numero_Aso AND P.Prefijo = E.Prefijo_Aso
    INNER JOIN confresoxusuario CxU ON CxU.IdUsuario = COALESCE(P.Usuario, E.Usuario)
    Where E.Nit = :nit
      And E.Fecha Between :fecha_hist_inicio And :fecha_hist_fin
      And (E.Estado IS NULL OR E.Estado <> 'A')
      And (
          E.Prefijo IN ('FE', 'POSE')
          OR (E.Prefijo = '0' AND (E.Prefijo_Aso IS NULL OR E.Prefijo_Aso = ''))
      )
      {filtro_vendedor}
    Group By D.Producto
) Hist

Left Join (
    Select
        D.Producto,
        Sum(D.Cantidad) As CantReciente,
        Sum(
            D.Precio * D.Cantidad
            * ((100 - D.Descuento) / 100)
            * ((100 + D.Impuesto)  / 100)
        )                                                   As TotalReciente
    From Enc_Ventas E
    Left Join Det_Ventas D Using(Prefijo, Numero)
    Left Join enc_pedidos P  ON P.Numero = E.Numero_Aso AND P.Prefijo = E.Prefijo_Aso
    INNER JOIN confresoxusuario CxU ON CxU.IdUsuario = COALESCE(P.Usuario, E.Usuario)
    Where E.Nit = :nit
      And E.Fecha Between :fecha_rec_inicio And :fecha_rec_fin
      And (E.Estado IS NULL OR E.Estado <> 'A')
      And (
          E.Prefijo IN ('FE', 'POSE')
          OR (E.Prefijo = '0' AND (E.Prefijo_Aso IS NULL OR E.Prefijo_Aso = ''))
      )
      {filtro_vendedor}
    Group By D.Producto
) Rec On Rec.Producto = Hist.Producto

Left Join productos Prod On Prod.Codigo = Hist.Producto

-- Solo productos donde cayó la venta
Where Coalesce(Rec.TotalReciente, 0) < Hist.TotalHistorico
Order By Impacto Desc
Limit 20
