# Tarea 4 – Agente de investigación socioeconómica (MCP del BCRP + Skills de ENAHO 2024)

**Estudiante:** Fiorella del Rocío Becerril Mercado · Curso Python Intermedio (d2cml-ai)

## 1. Objetivo
Construir un agente en Claude Code que responda preguntas socioeconómicas del Perú con herramientas
verificables: un servidor MCP con series oficiales del BCRP y tres Skills que procesan, grafican y mapean
los microdatos de la ENAHO 2024 del INEI. Ninguna cifra sale de la memoria del modelo.

**Pregunta de investigación:** ¿Cómo evolucionó la inflación de Lima Metropolitana entre 2020 y 2025, y qué
diferencias territoriales y por área urbana/rural presentaba la pobreza monetaria en 2024?

## 2. Arquitectura
```
Pregunta en lenguaje natural
        │
   Claude Code  ── CLAUDE.md (reglas del agente: plan, citar fuente, no inventar)
   ├── MCP bcrp (mcp/server.py, FastMCP, stdio vía .mcp.json)
   │     buscar_series · serie · resumen · correlacion · graficar_serie
   │     recurso bcrp://serie/{codigo} · prompt informe(tema)
   └── Skills (.claude/skills/)
         limpiando-enaho → salidas/personas_2024.parquet, validacion.txt, indicadores.csv
         graficando-enaho → figuras/pobreza_*.png      (si falta la base, llama a limpiando-enaho)
         mapeando-enaho  → mapas/pobreza_departamento.png (si falta la base, llama a limpiando-enaho)
        │
   informes/informe_final.md  ·  evaluacion/ (Modo A vs. Modo B)
```

## 3. Herramientas MCP (`mcp/server.py`)
| Herramienta | Qué hace |
|---|---|
| `buscar_series` | Busca códigos en el catálogo oficial del BCRP por palabras clave y frecuencia |
| `serie` | Descarga una serie (diaria, mensual, trimestral o anual) entre dos fechas; normaliza periodos (`2025-01`, `2026-10-01`, `2025-T1`, `2025`); reintenta si la API devuelve HTML |
| `resumen` | Primero, último, cambio, variación %, promedio, máximo y mínimo con periodo — calculados en Python |
| `correlacion` *(propia)* | Pearson entre dos series de igual frecuencia; alinea periodos, descarta faltantes e informa cuáles; exige ≥6 pares; rechaza frecuencias distintas |
| `graficar_serie` | Guarda un PNG de la serie en `figuras/bcrp_<codigo>.png` con fuente y código |
| Recurso `bcrp://serie/{codigo}` | Ficha descriptiva de la serie |
| Prompt `informe(tema)` | Plantilla de informe que obliga a citar código, periodo y fuente |

## 4. Skills
| Skill | Script | Qué hace |
|---|---|---|
| `limpiando-enaho` | `scripts/limpiar.py` | Lee módulos 34 y 02 (llaves como texto con ceros), normaliza columnas, filtra residentes habituales, une con `validate="m:1"`, construye pobreza/departamento/área/sexo/edad, pondera con `facpob07`, valida y escribe `salidas/validacion.txt`; si falla una validación esencial se detiene (exit 1) |
| `graficando-enaho` | `scripts/graficar.py --tipo area\|sexo\|edad\|departamento\|todos` | Barras ponderadas con título analítico, periodo, unidad, línea nacional y fuente |
| `mapeando-enaho` | `scripts/mapear.py` | Coroplético por `ubigeo[:2]` = `FIRST_IDDP`, 25 unidades, Lima y Callao separados, escala secuencial desde 0, compara con la referencia de la Sesión 16 |

## 5. Datos (no se suben al repositorio)
Descargar a `datos/`:
- ENAHO 2024 módulo 34: https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo34.zip
- ENAHO 2024 módulo 02: https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo02.zip
- GeoJSON departamental (se descarga solo): https://raw.githubusercontent.com/d2cml-ai/Data-Science-Python/main/sessions/06-geoespacial/lab/Data/peru_departamental_simple.geojson
- BCRP: https://estadisticas.bcrp.gob.pe/estadisticas/series/ (API consultada por el MCP; el catálogo se guarda en `datos/`)

## 6. Instalación
```bash
uv sync
```

## 7. Conectar el MCP a Claude Code
El archivo `.mcp.json` ya lo declara. Alternativa: `claude mcp add --scope project bcrp -- uv run mcp/server.py`.
Al abrir `claude` en esta carpeta, aprobar el servidor `bcrp` y comprobar con `/mcp`; las skills con `/skills`.

## 8. Reproducir
```bash
uv run pytest -q                                              # 10 pruebas del MCP
uv run .claude/skills/limpiando-enaho/scripts/limpiar.py      # base + validacion.txt
uv run .claude/skills/graficando-enaho/scripts/graficar.py --tipo todos
uv run .claude/skills/mapeando-enaho/scripts/mapear.py
claude "$(cat agente/pregunta_investigacion.md)"              # ejecución integrada del agente → informes/informe_final.md
uv run evaluacion/evaluar.py                                  # experimento Modo A vs. Modo B
```

## 9. Resultados
- Pruebas MCP: ver `evidencias_ia/mcp/` (salida de `pytest`).
- Validación ENAHO: `salidas/validacion.txt`.
- Evaluación: `evaluacion/resultados.csv` y `evaluacion/comparacion.md`.
- Informe: `informes/informe_final.md`.

## 10. Limitaciones
- La inflación del BCRP es de Lima Metropolitana y mensual; la pobreza es anual, nacional y departamental:
  se comparan descriptivamente, sin inferir causalidad.
- Las estimaciones de ENAHO tienen error muestral; no se reportan intervalos de confianza.
- La API del BCRP limita pedidos seguidos (se reintenta con espera) y requiere conexión.
- Las respuestas esperadas de las preguntas mixtas combinan cifras oficiales redondeadas, por eso su tolerancia.
- El Modo B necesita que exista la base procesada o tarda más al correr la limpieza.

## 11. Ejemplo de ejecución completa
Ver `evidencias_ia/integracion/` (exportación de la sesión de Claude Code que ejecutó
`agente/pregunta_investigacion.md` usando `buscar_series`, `resumen`, `correlacion`, `graficar_serie` y las
skills `limpiando-enaho`, `graficando-enaho`, `mapeando-enaho`).

## 12. Evidencias del uso de IA
Carpeta `evidencias_ia/`: conversaciones exportadas (Markdown/TXT) del desarrollo con Claude (claude.ai) y de
las sesiones de Claude Code (`/export`), organizadas en `mcp/`, `skills/`, `integracion/` y `evaluacion/`, sin
claves ni datos sensibles.
