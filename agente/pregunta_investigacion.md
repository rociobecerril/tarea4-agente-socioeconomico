Pregunta de investigación: ¿Cómo evolucionó la inflación de Lima Metropolitana entre 2020 y 2025, y qué
diferencias territoriales (por departamento) y por área urbana/rural presentaba la pobreza monetaria en 2024?

Desarrolla la investigación como agente, en una sola ejecución:

1. Escribe un plan breve de análisis (qué series del BCRP, qué indicadores de ENAHO, qué figuras).
2. BCRP (servidor MCP bcrp):
   - Usa buscar_series para hallar la inflación interanual (IPC Lima, variación 12 meses) y la tasa de
     referencia de política monetaria.
   - Usa resumen sobre la inflación 2020-01 a 2025-12 (promedio, máximo con su periodo, mínimo, valor final).
   - Usa correlacion entre la inflación 12 meses y la tasa de referencia (mensual, 2020-01 a 2025-12).
   - Usa graficar_serie para guardar el gráfico de la inflación 2020-01 a 2025-12 en figuras/.
3. ENAHO (skills): usa limpiando-enaho (si no hay base procesada), graficando-enaho (tipo area y
   departamento) y mapeando-enaho.
4. Escribe informes/informe_final.md con estas secciones: 1. Pregunta de investigación; 2. Fuentes y
   metodología; 3. Resultados (al menos 3 hallazgos con cifras y su fuente); 4. Visualizaciones (enlaza
   ../figuras/bcrp_<codigo>.png, ../figuras/pobreza_area.png o pobreza_departamento.png y
   ../mapas/pobreza_departamento.png); 5. Interpretación; 6. Limitaciones (periodos y niveles de
   agregación distintos, Lima Metropolitana vs. nacional, asociación ≠ causalidad, error muestral);
   7. Verificación: tabla con al menos 3 afirmaciones numéricas (al menos una del BCRP y una de ENAHO) con
   valor calculado, procedimiento de verificación, referencia y si coincide; 8. Reproducibilidad (scripts,
   comandos, códigos de serie y archivos).
5. Al final lista qué herramientas MCP y qué skills usaste en esta ejecución.
