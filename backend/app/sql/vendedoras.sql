SELECT DISTINCT COALESCE(P.Usuario, E.Usuario) AS Vendedor
FROM Enc_Ventas E
LEFT JOIN enc_pedidos P ON P.Numero = E.Numero_Aso AND P.Prefijo = E.Prefijo_Aso
WHERE E.Fecha >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
  AND (E.Estado IS NULL OR E.Estado <> 'A')
  AND (E.Prefijo IN ('FE','POSE') OR (E.Prefijo = '0' AND (E.Prefijo_Aso IS NULL OR E.Prefijo_Aso = '')))
ORDER BY Vendedor
