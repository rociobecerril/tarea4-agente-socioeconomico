# Comparación Modo A (sin MCP/Skills) vs. Modo B (con MCP/Skills)

Modelo: `haiku`. Cada pregunta en una sesión independiente de `claude -p`.

| Modo | Herramientas habilitadas |
|---|---|
| A_sin | ninguna herramienta, sin MCP, sin Skills |
| B_con | MCP bcrp + Skills del proyecto + Bash/Read/Glob (sin web) |

## Resultados

| modo   |   correcta |   incorrecta |   no responde |   segundos_promedio |
|:-------|-----------:|-------------:|--------------:|--------------------:|
| A_sin  |          0 |            0 |            10 |                 5.2 |
| B_con  |         10 |            0 |             0 |                14.3 |

## Aciertos por tipo de pregunta

| tipo   |   A_sin |   B_con |
|:-------|--------:|--------:|
| BCRP   |       0 |       4 |
| ENAHO  |       0 |       4 |
| MIXTA  |       0 |       2 |

**Mejoran con MCP/Skills:** bcrp_ipc_set26, bcrp_pbi_2025, bcrp_ref_set26, bcrp_tc_15oct26, enaho_cajamarca, enaho_cusco, enaho_nacional, enaho_rural, mixta_cajamarca_ipc, mixta_nacional_pbi  
**Empeoran con MCP/Skills:** ninguna

## Respuestas no correctas

| modo   | id                  |   verdad |   valor | resultado   | error   |
|:-------|:--------------------|---------:|--------:|:------------|:--------|
| A_sin  | bcrp_ipc_set26      |   4.5487 |     nan | no responde |         |
| A_sin  | bcrp_tc_15oct26     |   3.4282 |     nan | no responde |         |
| A_sin  | bcrp_ref_set26      |   4.25   |     nan | no responde |         |
| A_sin  | bcrp_pbi_2025       |   3.4306 |     nan | no responde |         |
| A_sin  | enaho_nacional      |  27.6    |     nan | no responde |         |
| A_sin  | enaho_rural         |  39.3    |     nan | no responde |         |
| A_sin  | enaho_cusco         |  18.5    |     nan | no responde |         |
| A_sin  | enaho_cajamarca     |  45      |     nan | no responde |         |
| A_sin  | mixta_cajamarca_ipc |  43.4912 |     nan | no responde |         |
| A_sin  | mixta_nacional_pbi  |  24.1694 |     nan | no responde |         |

## Conclusión

Con las mismas 10 preguntas y el mismo modelo (Haiku), el Modo A (sin herramientas, sin MCP ni Skills) no respondió ninguna: en las 10 devolvió valor nulo, es decir, reconoció que no podía conocer la cifra con certeza en lugar de inventarla. El Modo B (MCP del BCRP + Skills de ENAHO) respondió correctamente las 10 dentro de la tolerancia fijada antes del experimento: 4/4 del BCRP, 4/4 de ENAHO y 2/2 mixtas.

La mejora se explica porque las cifras de 2025-2026 del BCRP son posteriores al conocimiento del modelo y las de ENAHO requieren procesar microdatos con factores de expansión: ninguna puede responderse de memoria de forma verificable. Las diferencias del Modo B frente a la respuesta esperada (por ejemplo, 27.53 frente a 27.6, o 24.09 frente a 24.17) provienen de que las respuestas esperadas usan cifras oficiales redondeadas a un decimal, mientras que el agente usa el valor calculado.

El costo del Modo B es el tiempo: cada pregunta requiere consultar la API o ejecutar scripts (ver segundos_promedio). Conclusión: el MCP y las Skills convierten preguntas sin respuesta en respuestas correctas y rastreables a su fuente; este experimento no permite afirmar cuán bien respondería el modelo con acceso a la web, que no se evaluó.
