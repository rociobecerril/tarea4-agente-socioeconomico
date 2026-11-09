---
name: graficando-enaho
description: Hace gráficos de pobreza monetaria con la ENAHO 2024 del INEI — por área urbana y rural, por sexo, por grupo de edad o comparando departamentos — con estimaciones ponderadas, título, unidades y fuente. Úsala cuando pidan graficar, visualizar, comparar o hacer barras de pobreza con la ENAHO.
---
# Graficar la ENAHO 2024

1. Si no existe `salidas/personas_2024.parquet`, usa primero la skill `limpiando-enaho` y verifica que su
   validación haya pasado.
2. Elige el tipo según el pedido: `area` (urbano/rural), `sexo`, `edad` o `departamento`; `todos` para los cuatro.
3. Corre exactamente:
   `uv run .claude/skills/graficando-enaho/scripts/graficar.py --tipo <tipo>`
4. El script imprime la tabla graficada. Reporta esas cifras (ponderadas con facpob07) y la ruta
   `figuras/pobreza_<tipo>.png`.
5. Reglas que el script ya cumple: barras desde cero, un solo color, valor escrito en cada barra, línea del
   promedio nacional, título que dice qué y cuándo, unidad (% de personas) y fuente "INEI, ENAHO 2024".
6. Describe diferencias como asociaciones descriptivas, no como causas.
