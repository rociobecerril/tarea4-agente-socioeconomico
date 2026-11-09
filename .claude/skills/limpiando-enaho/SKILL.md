---
name: limpiando-enaho
description: Limpia y une los módulos 34 (sumaria) y 02 (miembros) de la ENAHO 2024 del INEI, filtra residentes habituales, construye pobreza monetaria, departamento y área, y valida contra las cifras oficiales (27.6 %, 108,664 personas, 25 departamentos). Úsala cuando pidan limpiar, unir, procesar o analizar la ENAHO, o calcular pobreza nacional, por región, departamento, área urbana/rural, sexo o edad.
---
# Limpiar la ENAHO 2024

1. Verifica que existan `datos/966-Modulo34.zip` y `datos/966-Modulo02.zip`. Si faltan, pide al usuario
   descargarlos del INEI (código 966 = 2024; enlaces en `reference.md`). No inventes datos.
2. Corre exactamente:
   `uv run .claude/skills/limpiando-enaho/scripts/limpiar.py`
3. Lee `salidas/validacion.txt`. Si el script termina con error o dice "FALLÓ UNA VALIDACIÓN ESENCIAL",
   detente e informa cuál falló. Nunca ajustes cifras para que coincidan con la referencia.
4. Resultado: `salidas/personas_2024.parquet` (una fila por residente habitual) y `salidas/indicadores.csv`.
5. Toda cifra que reportes debe estar ponderada con `facpob07` (nunca promedio simple) y citar
   "INEI, ENAHO 2024".
6. Para responder una pregunta puntual (p. ej. pobreza de Cusco), lee `salidas/indicadores.csv` o calcula con
   pandas sobre el parquet con `np.average(pobre, weights=facpob07)`.
7. Antes de usar una variable que no está en la base, lee `reference.md`.
