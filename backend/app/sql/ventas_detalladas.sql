SELECT 
    E.Fecha,
    E.Prefijo,
    E.Numero,
    -- Identidad Unificada: Usamos el Vendedor Asociado a ese Usuario específico
    C.Vendedor_Asociado AS Codigo_Vendedor,
    V.Nombre AS Nombre_Vendedor,
    E.Usuario AS Id_Usuario,
    R.Nombre AS Nombre_Usuario,
    -- Producto y Totales
    D.Producto,
    SUM(D.Cantidad) AS Cantidad,
    SUM(D.Precio * D.Cantidad * ((100 - D.Descuento) / 100) * ((100 + D.Impuesto) / 100)) AS Total_Neto
FROM Enc_Ventas E
LEFT JOIN Det_Ventas D USING(Prefijo, Numero)
-- El Puente: une el digitador con su código de asesor comercial
INNER JOIN confresoxusuario C ON C.IdUsuario = E.Usuario 
LEFT JOIN Vendedor V ON V.Codigo = C.Vendedor_Asociado
LEFT JOIN Responsables R ON R.Codigo = E.Usuario
WHERE E.Fecha >= :fecha_inicial AND E.Fecha <= :fecha_final
GROUP BY E.Numero, E.Prefijo, E.Fecha, C.Vendedor_Asociado, V.Nombre, E.Usuario, R.Nombre, D.Producto
ORDER BY E.Fecha DESC;
