-- KPI: Clientes en caída — compara dos ventanas de tiempo iguales
-- Período anterior: :fecha_anterior_inicio → :fecha_anterior_fin
-- Período reciente: :fecha_reciente_inicio → :fecha_reciente_fin
-- Solo muestra clientes que compraron bien antes y ahora compran menos
Select
    Antes.Vendedor,
    V.Nombre                                                As NombreVendedor,
    Antes.Nit,
    Cl.Nombre                                               As NombreCliente,
    Round(Antes.Total, 2)                                   As VentaAnterior,
    Round(Coalesce(Ahora.Total, 0), 2)                      As VentaReciente,
    Round(Coalesce(Ahora.Total, 0) - Antes.Total, 2)        As Diferencia,
    Round(
        (Coalesce(Ahora.Total, 0) - Antes.Total)
        / Nullif(Antes.Total, 0) * 100
    , 1)                                                    As PctCambio

From (
    Select
        E.Nit,
        CxU.Vendedor_Asociado As Vendedor,
        Sum(
            D.Precio * D.Cantidad
            * ((100 - D.Descuento) / 100)
            * ((100 + D.Impuesto)  / 100)
        )                                                   As Total
    From Enc_Ventas E
    Left Join Det_Ventas D Using(Prefijo, Numero)
    INNER JOIN confresoxusuario CxU ON CxU.IdUsuario = E.Usuario
    Where E.Fecha Between :fecha_anterior_inicio And :fecha_anterior_fin
    Group By E.Nit, CxU.Vendedor_Asociado
    Having Total >= :minimo_venta
) Antes

Left Join (
    Select
        E.Nit,
        Sum(
            D.Precio * D.Cantidad
            * ((100 - D.Descuento) / 100)
            * ((100 + D.Impuesto)  / 100)
        )                                                   As Total
    From Enc_Ventas E
    Left Join Det_Ventas D Using(Prefijo, Numero)
    INNER JOIN confresoxusuario CxU ON CxU.IdUsuario = E.Usuario
    Where E.Fecha Between :fecha_reciente_inicio And :fecha_reciente_fin
    Group By E.Nit
) Ahora On Ahora.Nit = Antes.Nit

Left Join Vendedor V On V.Codigo = Antes.Vendedor
Left Join clientes Cl On Cl.Nit = Antes.Nit

-- Solo los que cayeron
Where Coalesce(Ahora.Total, 0) < Antes.Total
Order By Diferencia Asc   -- los más negativos primero
Limit 50
