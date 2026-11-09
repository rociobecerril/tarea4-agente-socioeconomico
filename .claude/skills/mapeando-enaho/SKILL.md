---
name: mapeando-enaho
description: Construye el mapa coroplético de pobreza monetaria por departamento del Perú con la ENAHO 2024 del INEI, uniendo por código ubigeo con FIRST_IDDP (25 departamentos, Lima y Callao separados) y comparando con la referencia oficial. Úsala cuando pidan un mapa, mapear o ver la distribución territorial o regional de la pobreza.
---
# Mapear la pobreza departamental, ENAHO 2024

1. Si no existe `salidas/personas_2024.parquet`, usa primero la skill `limpiando-enaho` y verifica que su
   validación haya pasado.
2. Corre exactamente:
   `uv run .claude/skills/mapeando-enaho/scripts/mapear.py`
   (descarga el GeoJSON del curso a `datos/` si falta).
3. El script une `ubigeo[:2]` con `FIRST_IDDP` como texto (nunca por nombre), exige 25 unidades con dato y
   Lima (15) y Callao (07) separados. Si termina con error, informa el error; no lo maquilles.
4. Reporta: unidades con dato (25/25), la máxima diferencia con `referencia/pobreza_departamento_2024.csv`
   (salidas/comparacion_mapa.csv), los departamentos extremos y la ruta `mapas/pobreza_departamento.png`.
5. La escala es secuencial (Reds) desde 0 y la leyenda dice "% de personas en pobreza monetaria".
