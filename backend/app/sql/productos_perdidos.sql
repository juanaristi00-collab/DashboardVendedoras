-- KPI: Productos que un cliente dejó de comprar (o redujo significativamente)
-- Compara histórico (:fecha_hist_inicio → :fecha_hist_fin)
--         vs reciente (:fecha_rec_inicio  → :fecha_rec_fin)
-- Devuelve ordenado por Impacto (mayor pérdida de venta primero)
Select
    Hist.Producto,
    Round(Hist.TotalHistorico, 2)                           As TotalHistorico,
    Round(Coalesce(Rec.TotalReciente, 0), 2)                As TotalReciente,
    Round(
        Hist.TotalHistorico - Coalesce(Rec.TotalReciente, 0)
    , 2)                                                    As Impacto,
    Round(
        (Coalesce(Rec.TotalReciente, 0) - Hist.TotalHistorico)
        / Nullif(Hist.TotalHistorico, 0) * 100
    , 1)                                                    As PctCambio

From (
    Select
        D.Producto,
        Sum(
            D.Precio * D.Cantidad
            * ((100 - D.Descuento) / 100)
            * ((100 + D.Impuesto)  / 100)
        )                                                   As TotalHistorico
    From Enc_Ventas E
    Left Join Det_Ventas D Using(Prefijo, Numero)
    INNER JOIN confresoxusuario CxU ON CxU.IdUsuario = E.Usuario
    Where E.Nit = :nit
      And E.Fecha Between :fecha_hist_inicio And :fecha_hist_fin
    Group By D.Producto
) Hist

Left Join (
    Select
        D.Producto,
        Sum(
            D.Precio * D.Cantidad
            * ((100 - D.Descuento) / 100)
            * ((100 + D.Impuesto)  / 100)
        )                                                   As TotalReciente
    From Enc_Ventas E
    Left Join Det_Ventas D Using(Prefijo, Numero)
    INNER JOIN confresoxusuario CxU ON CxU.IdUsuario = E.Usuario
    Where E.Nit = :nit
      And E.Fecha Between :fecha_rec_inicio And :fecha_rec_fin
    Group By D.Producto
) Rec On Rec.Producto = Hist.Producto

-- Solo productos donde cayó la venta
Where Coalesce(Rec.TotalReciente, 0) < Hist.TotalHistorico
Order By Impacto Desc
Limit 20
