-- Matriz de clientes MTD: nombre, facturas, valor, para Pareto
-- Parámetros: :anio, :mes, :dia
Select
    E.Nit,
    Cl.Nombre                                                       As NombreCliente,
    Count(Distinct Concat(E.Prefijo, '-', E.Numero))                As CantFacturas,
    Round(Sum(
        D.Precio * D.Cantidad
        * ((100 - D.Descuento) / 100)
        * ((100 + D.Impuesto)  / 100)
    ), 2)                                                           As TotalVenta

From Enc_Ventas E
Left Join Det_Ventas D   Using(Prefijo, Numero)
Left Join clientes Cl    On Cl.Nit = E.Nit
Left Join enc_pedidos P  ON P.Numero = E.Numero_Aso AND P.Prefijo = E.Prefijo_Aso
INNER JOIN confresoxusuario C ON C.IdUsuario = COALESCE(P.Usuario, E.Usuario)

Where Year(E.Fecha)  = :anio
  And Month(E.Fecha) = :mes
  And Day(E.Fecha)  <= :dia
  And (E.Estado IS NULL OR E.Estado <> 'A')
  And (
      E.Prefijo IN ('FE', 'POSE')
      OR (E.Prefijo = '0' AND (E.Prefijo_Aso IS NULL OR E.Prefijo_Aso = ''))
  )
  {filtro_vendedor}

Group By E.Nit, Cl.Nombre
Having TotalVenta > 0
Order By TotalVenta Desc
