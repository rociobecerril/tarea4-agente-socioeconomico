# Referencia ENAHO 2024 (INEI)

## Archivos
| Módulo | Una fila por | Filas | Llaves | Factor | Descarga |
|---|---|---|---|---|---|
| 34 sumaria (`sumaria-2024.dta`) | hogar | 33,691 | conglome, vivienda, hogar | factor07 | https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo34.zip |
| 02 miembros (`enaho01-2024-200.dta`) | persona | 117,721 | + codperso | facpob07 | https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo02.zip |

## Reglas
- Leer con `pd.read_stata(..., convert_categoricals=False)`; llaves como texto con ceros a la izquierda
  (conglome 6, vivienda 3, hogar 2, codperso 2, ubigeo 6).
- Columnas a minúscula (`aÑo` → `año`).
- Residentes habituales: `((p204 == 1) & (p205 == 2)) | ((p204 == 2) & (p206 == 1))`.
- Unión personas → hogares: `merge(..., on=[conglome, vivienda, hogar], validate="m:1")`.
- `departamento = ubigeo[:2]` (01–25; Lima 15 y Callao 07 por separado).
- `area`: Urbana si `estrato <= 5`, Rural si 6–8.
- `pobre = pobreza <= 2` (1 extremo, 2 no extremo, 3 no pobre); `pobre_extremo = pobreza == 1`.
- Ponderar personas con `facpob07`; con la sumaria, `factor07 × mieperho`.

## Variables de la base limpia
`p207` sexo (1 hombre, 2 mujer) → `sexo`; `p208a` edad → `edad`, `grupo_edad` (0-13, 14-29, 30-59, 60+);
`dominio` (8 = Lima Metropolitana).

## Valores de referencia 2024
Pobreza 27.6 % (27.53 % personas/facpob07; 27.58 % sumaria) · extrema 5.5 % · urbana 24.8 % · rural 39.3 % ·
residentes habituales 108,664 · Lima Metropolitana 28.2 % · Cusco 18.5 % · Cajamarca 45.0 % · Ica 6.0 %.
