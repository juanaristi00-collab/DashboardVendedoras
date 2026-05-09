SELECT 
    E.Fecha,
    E.Prefijo,
    E.Numero,
    -- Identidad Unificada: Usuario Gestión (Pedido o Factura)
    COALESCE(P.Usuario, E.Usuario) AS Id_Usuario_Gestion,
    R_Gest.Nombre AS Nombre_Usuario_Gestion,
    C_Gest.Vendedor_Asociado AS Codigo_Vendedor,
    V_Gest.Nombre AS Nombre_Vendedor,
    
    -- El que imprimió / facturó físicamente
    E.Usuario AS Id_Usuario_Factura,
    R_Fact.Nombre AS Nombre_Usuario_Factura,
    -- Producto y Totales
    D.Producto,
    SUM(D.Cantidad) AS Cantidad,
    SUM(D.Precio * D.Cantidad * ((100 - D.Descuento) / 100) * ((100 + D.Impuesto) / 100)) AS Total_Neto
FROM Enc_Ventas E
LEFT JOIN Det_Ventas D USING(Prefijo, Numero)
LEFT JOIN enc_pedidos P ON P.Numero = E.Numero_Aso AND P.Prefijo = E.Prefijo_Aso
-- Puente Usuario Gestión
LEFT JOIN confresoxusuario C_Gest ON C_Gest.IdUsuario = COALESCE(P.Usuario, E.Usuario)
LEFT JOIN Vendedor V_Gest ON V_Gest.Codigo = C_Gest.Vendedor_Asociado
LEFT JOIN Responsables R_Gest ON R_Gest.Codigo = COALESCE(P.Usuario, E.Usuario)
-- Puente Usuario Facturación
LEFT JOIN Responsables R_Fact ON R_Fact.Codigo = E.Usuario
WHERE E.Fecha >= :fecha_inicial AND E.Fecha <= :fecha_final
  AND (E.Estado IS NULL OR E.Estado <> 'A')
  AND (
      E.Prefijo IN ('FE', 'POSE')
      OR (E.Prefijo = '0' AND (E.Prefijo_Aso IS NULL OR E.Prefijo_Aso = ''))
  )
GROUP BY E.Numero, E.Prefijo, E.Fecha, COALESCE(P.Usuario, E.Usuario), R_Gest.Nombre, C_Gest.Vendedor_Asociado, V_Gest.Nombre, E.Usuario, R_Fact.Nombre, D.Producto
ORDER BY E.Fecha DESC;
