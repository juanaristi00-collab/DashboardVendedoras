-- KPI: Ventas Month-To-Date — mes actual vs mismo período del año anterior
-- Agrupa por la identidad del usuario mapeado; no requiere parámetros externos (usa CurDate())
Select
    C.Vendedor_Asociado                                     As Vendedor,
    V.Nombre                                                As NombreVendedor,
    E.Usuario                                               As Usuario,
    R.Nombre                                                As NombreUsuario,

    -- Mes actual, días 1 → hoy
    Round(Sum(Case
        When Year(E.Fecha)  = Year(CurDate())
         And Month(E.Fecha) = Month(CurDate())
         And Day(E.Fecha)  <= Day(CurDate())
        Then D.Precio * D.Cantidad
             * ((100 - D.Descuento) / 100)
             * ((100 + D.Impuesto)  / 100)
        Else 0
    End), 2)                                                As VentaActual,

    -- Mismo rango del año anterior
    Round(Sum(Case
        When Year(E.Fecha)  = Year(CurDate()) - 1
         And Month(E.Fecha) = Month(CurDate())
         And Day(E.Fecha)  <= Day(CurDate())
        Then D.Precio * D.Cantidad
             * ((100 - D.Descuento) / 100)
             * ((100 + D.Impuesto)  / 100)
        Else 0
    End), 2)                                                As VentaAnterior,

    -- Clientes únicos facturados este mes
    Count(Distinct Case
        When Year(E.Fecha)  = Year(CurDate())
         And Month(E.Fecha) = Month(CurDate())
        Then E.Nit Else Null
    End)                                                    As ClientesActivos

From Enc_Ventas E
Left Join Det_Ventas D   Using(Prefijo, Numero)
INNER JOIN confresoxusuario C ON C.IdUsuario = E.Usuario 
Left Join Vendedor V     On V.Codigo = C.Vendedor_Asociado
Left Join Responsables R On R.Codigo = E.Usuario
Where (
    (   Year(E.Fecha)  = Year(CurDate())
        And Month(E.Fecha) = Month(CurDate())
        And Day(E.Fecha)  <= Day(CurDate())  )
    Or
    (   Year(E.Fecha)  = Year(CurDate()) - 1
        And Month(E.Fecha) = Month(CurDate())
        And Day(E.Fecha)  <= Day(CurDate())  )
)
Group By C.Vendedor_Asociado, V.Nombre, E.Usuario, R.Nombre
Order By VentaActual Desc
