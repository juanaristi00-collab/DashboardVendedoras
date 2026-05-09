-- KPI: Ventas Month-To-Date — período seleccionado vs mismo período del año anterior
-- Parámetros: :anio (año), :mes (mes 1-12), :dia (día límite del mes)
-- Si es el mes actual, :dia = día de hoy. Si es mes pasado, :dia = último día del mes.
Select
    COALESCE(P.Usuario, E.Usuario)                          As Vendedor,
    COALESCE(P.Usuario, E.Usuario)                          As NombreVendedor,
    C_Gest.Vendedor_Asociado                                As CodigoAsesor,
    V_Gest.Nombre                                           As NombreAsesor,

    -- Período seleccionado: año/mes, días 1 → :dia
    Round(Sum(Case
        When Year(E.Fecha)  = :anio
         And Month(E.Fecha) = :mes
         And Day(E.Fecha)  <= :dia
        Then D.Precio * D.Cantidad
             * ((100 - D.Descuento) / 100)
             * ((100 + D.Impuesto)  / 100)
        Else 0
    End), 2)                                                As VentaActual,

    -- Mismo rango del año anterior
    Round(Sum(Case
        When Year(E.Fecha)  = :anio - 1
         And Month(E.Fecha) = :mes
         And Day(E.Fecha)  <= :dia
        Then D.Precio * D.Cantidad
             * ((100 - D.Descuento) / 100)
             * ((100 + D.Impuesto)  / 100)
        Else 0
    End), 2)                                                As VentaAnterior,

    -- Clientes únicos facturados en el período seleccionado
    Count(Distinct Case
        When Year(E.Fecha)  = :anio
         And Month(E.Fecha) = :mes
         And Day(E.Fecha)  <= :dia
        Then E.Nit Else Null
    End)                                                    As ClientesActivos

From Enc_Ventas E
Left Join Det_Ventas D   Using(Prefijo, Numero)
-- Enlace con Pedido para encontrar quién hizo la gestión comercial
Left Join enc_pedidos P  ON P.Numero = E.Numero_Aso AND P.Prefijo = E.Prefijo_Aso
-- Resolución Usuario Gestión (Fallback al usuario de la factura si no hay pedido)
Left Join confresoxusuario C_Gest ON C_Gest.IdUsuario = COALESCE(P.Usuario, E.Usuario)
Left Join Vendedor V_Gest         On V_Gest.Codigo = C_Gest.Vendedor_Asociado
Where (
    (   Year(E.Fecha)  = :anio
        And Month(E.Fecha) = :mes
        And Day(E.Fecha)  <= :dia  )
    Or
    (   Year(E.Fecha)  = :anio - 1
        And Month(E.Fecha) = :mes
        And Day(E.Fecha)  <= :dia  )
)
  And (E.Estado IS NULL OR E.Estado <> 'A')
  And (
      E.Prefijo IN ('FE', 'POSE')
      OR (E.Prefijo = '0' AND (E.Prefijo_Aso IS NULL OR E.Prefijo_Aso = ''))
  )
  {filtro_vendedor}
Group By COALESCE(P.Usuario, E.Usuario), C_Gest.Vendedor_Asociado, V_Gest.Nombre
Order By VentaActual Desc
