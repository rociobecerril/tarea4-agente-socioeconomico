# Registro de uso de IA – Tarea 4 (desarrollo con Claude)

**Estudiante:** Fiorella del Rocío Becerril Mercado (@rociobecerril)
**Fecha:** 8 de noviembre de 2026

## 1. Solicitud inicial

Se pidió a Claude desarrollar la Tarea 4 (issue #201 de d2cml-ai/Data-Science-Python) a partir del enunciado.

## 2. Proyecto generado (`tarea_4.zip`)

Claude armó la estructura completa: servidor MCP del BCRP, skills de gráficos y mapas ENAHO, scripts `limpiar.py`, `graficar.py` y `mapear.py`, pruebas y evaluación. Su entorno no tenía acceso a INEI ni al BCRP, así que solo verificó lo que no necesitaba red: el servidor MCP carga con su recurso y su prompt, la conversión de fechas del BCRP funciona, y los gráficos y el mapa funcionan con datos de prueba (25/25 unidades). Las cifras reales se generaron localmente.

## 3. Pasos de ejecución local

1. Descomprimir el proyecto, descargar los zip del INEI en `datos/` y correr `uv sync`.
2. Correr `pytest` (10/10), `limpiar.py` (validación: 27.5 % de pobreza y 108,664 personas), `graficar.py` y `mapear.py`.
3. Hacer la ejecución integrada en Claude Code con el MCP `bcrp` y la pregunta de `agente/pregunta_investigacion.md`, que genera `informes/informe_final.md`.
4. Correr `evaluacion/evaluar.py` (20 llamadas con Haiku, sin MCP/Skills y con MCP/Skills) y redactar la conclusión en `comparacion.md`.

Las respuestas esperadas de `preguntas.csv` vienen del archivo de la Sesión 04 (BCRP) y de las referencias del curso (ENAHO). Las preguntas mixtas tienen su fuente anotada en el CSV.

## 4. Repositorio

Se creó el repositorio público `rociobecerril/tarea4-agente-socioeconomico` y Claude subió el commit.

## 5. Entrega

Claude redactó el comentario del issue con el formato pedido. Resultados:

- Pruebas MCP: 10/10
- Pobreza nacional 2024: 27.5 %
- Residentes habituales: 108,664
- Unidades territoriales: 25/25
- Evaluación sin MCP/Skills: 0/10 (el modelo no inventó cifras)
- Evaluación con MCP/Skills: 10/10

Al final se agregaron a `evidencias_ia/` la conversación de desarrollo y los registros de evaluación.
