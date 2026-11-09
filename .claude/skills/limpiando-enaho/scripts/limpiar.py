"""Limpia la ENAHO 2024 (módulos 34 y 02), construye la base de personas y valida contra el INEI.

    uv run .claude/skills/limpiando-enaho/scripts/limpiar.py

Entra:  datos/966-Modulo34.zip y datos/966-Modulo02.zip (o sus carpetas descomprimidas)
Sale:   salidas/personas_2024.parquet, salidas/indicadores.csv, salidas/validacion.txt
Si una validación esencial falla, termina con código 1 y no guarda la base.
"""
import io
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[4]
DATOS, SALIDAS = RAIZ / "datos", RAIZ / "salidas"
LLAVES = ["conglome", "vivienda", "hogar"]
ANCHO = {"conglome": 6, "vivienda": 3, "hogar": 2, "codperso": 2}
REF = {"pobreza": 27.6, "residentes": 108_664, "departamentos": 25, "urbano": 24.8, "rural": 39.3}


def _buscar_dta(modulo: str, elegir) -> tuple[str, bytes]:
    """Devuelve (nombre, bytes) del .dta del módulo, desde el zip o la carpeta descomprimida."""
    candidatos = []
    z = DATOS / f"966-{modulo}.zip"
    if z.exists():
        with zipfile.ZipFile(z) as zf:
            candidatos = [(n, (lambda b: lambda _: b)(zf.read(n))) for n in zf.namelist() if n.lower().endswith(".dta")]
    else:
        candidatos = [(str(p), lambda n: Path(n).read_bytes()) for p in DATOS.rglob("*.dta") if modulo in str(p)]
    elegidos = [(n, leer) for n, leer in candidatos if elegir(Path(n).name.lower())]
    if not elegidos:
        sys.exit(f"ERROR: no encuentro el .dta del {modulo} en {DATOS}. Descarguen "
                 f"https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-{modulo}.zip a datos/.")
    n, leer = sorted(elegidos, key=lambda x: len(x[0]))[0]
    return n, leer(n)


def leer(modulo, elegir, columnas=None):
    nombre, contenido = _buscar_dta(modulo, elegir)
    df = pd.read_stata(io.BytesIO(contenido), convert_categoricals=False)
    df.columns = [c.lower().strip() for c in df.columns]           # 'aÑo' -> 'año'
    for k, w in ANCHO.items():                                      # llaves como texto, sin perder ceros
        if k in df.columns:
            s = df[k]
            if pd.api.types.is_numeric_dtype(s):
                s = s.astype("Int64").astype(str)
            df[k] = s.astype(str).str.strip().str.zfill(w)
    if "ubigeo" in df.columns:
        s = df["ubigeo"]
        if pd.api.types.is_numeric_dtype(s):
            s = s.astype("Int64").astype(str)
        df["ubigeo"] = s.astype(str).str.strip().str.zfill(6)
    if columnas:
        df = df[[c for c in columnas if c in df.columns]]
    return nombre, df


def wmean(x, w):
    return float(np.average(x, weights=w))


def main():
    SALIDAS.mkdir(exist_ok=True)
    chequeos, lineas = [], []

    def check(nombre, ok, detalle, esencial=True):
        chequeos.append((nombre, bool(ok), esencial))
        lineas.append(f"[{'OK   ' if ok else 'FALLA'}] {nombre}: {detalle}{'' if esencial else ' (informativo)'}")

    n34, hog = leer("Modulo34", lambda n: n.startswith("sumaria") and "12g" not in n,
                    LLAVES + ["ubigeo", "dominio", "estrato", "pobreza", "factor07", "mieperho"])
    n02, per = leer("Modulo02", lambda n: "200" in n,
                    LLAVES + ["codperso", "p203", "p204", "p205", "p206", "p207", "p208a", "facpob07"])
    lineas += [f"Archivos: {n34} ({len(hog):,} hogares) | {n02} ({len(per):,} personas)", ""]

    # 1. llaves únicas
    check("Llave de hogar única en sumaria", not hog.duplicated(LLAVES).any(),
          f"{hog.duplicated(LLAVES).sum()} duplicados")
    check("Llave de persona única en módulo 02", not per.duplicated(LLAVES + ["codperso"]).any(),
          f"{per.duplicated(LLAVES + ['codperso']).sum()} duplicados")

    # 2. residentes habituales
    res = per[((per.p204 == 1) & (per.p205 == 2)) | ((per.p204 == 2) & (per.p206 == 1))].copy()
    check("Residentes habituales = 108,664", len(res) == REF["residentes"],
          f"{len(res):,} de {len(per):,} filas")

    # 3. unión m:1 sin perder ni duplicar
    base = res.merge(hog, on=LLAVES, how="left", validate="m:1", indicator=True)
    check("Unión m:1 sin duplicar filas", len(base) == len(res), f"{len(res):,} -> {len(base):,}")
    sin_hogar = int((base._merge != "both").sum())
    check("Toda persona encuentra su hogar", sin_hogar == 0, f"{sin_hogar} sin hogar")
    base = base.drop(columns="_merge")

    # 4. indicadores
    base["departamento"] = base.ubigeo.str[:2]
    base["area"] = np.where(base.estrato <= 5, "Urbana", "Rural")
    base["pobre"] = (base.pobreza <= 2).astype(int)
    base["pobre_extremo"] = (base.pobreza == 1).astype(int)
    base["sexo"] = base.p207.map({1: "Hombre", 2: "Mujer"})
    base["edad"] = base.p208a
    base["grupo_edad"] = pd.cut(base.edad, [-1, 13, 29, 59, 200], labels=["0-13", "14-29", "30-59", "60+"])
    base["anio"] = 2024

    # 5. factores de expansión
    check("facpob07 sin nulos y positivo", base.facpob07.notna().all() and (base.facpob07 > 0).all(),
          f"{int(base.facpob07.isna().sum())} nulos")
    w = base.facpob07
    pob = wmean(base.pobre, w) * 100
    simple = base.pobre.mean() * 100
    check("Pobreza nacional ponderada (facpob07) a ≤0.1 pp de 27.6 %", abs(pob - REF["pobreza"]) <= 0.1,
          f"{pob:.2f} % (sin ponderar sería {simple:.2f} %)")
    hog_pob = wmean((hog.pobreza <= 2).astype(int), hog.factor07 * hog.mieperho) * 100
    check("Pobreza con sumaria (factor07 × mieperho)", abs(hog_pob - REF["pobreza"]) <= 0.1, f"{hog_pob:.2f} %")
    deps = sorted(base.departamento.unique())
    check("25 códigos departamentales (01–25)", deps == [f"{i:02d}" for i in range(1, 26)], f"{len(deps)}: {deps}")
    urb = wmean(base.pobre[base.area == "Urbana"], w[base.area == "Urbana"]) * 100
    rur = wmean(base.pobre[base.area == "Rural"], w[base.area == "Rural"]) * 100
    check("Pobreza urbana ≈ 24.8 %", abs(urb - REF["urbano"]) <= 0.15, f"{urb:.2f} %", esencial=False)
    check("Pobreza rural ≈ 39.3 %", abs(rur - REF["rural"]) <= 0.15, f"{rur:.2f} %", esencial=False)
    ext = wmean(base.pobre_extremo, w) * 100
    check("Pobreza extrema ≈ 5.5 %", abs(ext - 5.5) <= 0.15, f"{ext:.2f} %", esencial=False)

    # 6. indicadores.csv (todos ponderados con facpob07)
    filas = [{"dimension": "nacional", "grupo": "Perú", "pobreza_pct": pob, "n_muestral": len(base),
              "poblacion_expandida": w.sum()}]
    for dim in ["area", "sexo", "grupo_edad", "departamento"]:
        for g, d in base.groupby(dim, observed=True):
            filas.append({"dimension": dim, "grupo": g, "pobreza_pct": wmean(d.pobre, d.facpob07) * 100,
                          "n_muestral": len(d), "poblacion_expandida": d.facpob07.sum()})
    ind = pd.DataFrame(filas)
    ind["pobreza_pct"] = ind.pobreza_pct.round(2)
    ind["poblacion_expandida"] = ind.poblacion_expandida.round(0).astype(int)

    esenciales_ok = all(ok for _, ok, es in chequeos if es)
    resumen = (f"\nAprobadas {sum(ok for _, ok, _ in chequeos)}/{len(chequeos)}. "
               f"{'TODAS LAS ESENCIALES APROBADAS' if esenciales_ok else 'FALLÓ UNA VALIDACIÓN ESENCIAL: base NO guardada'}")
    texto = "VALIDACIÓN ENAHO 2024 (INEI) — limpiando-enaho\n" + "\n".join(lineas) + resumen + "\n"
    (SALIDAS / "validacion.txt").write_text(texto, encoding="utf-8")
    print(texto)
    if not esenciales_ok:
        sys.exit(1)
    cols = LLAVES + ["codperso", "ubigeo", "departamento", "dominio", "estrato", "area", "sexo", "edad",
                     "grupo_edad", "pobreza", "pobre", "pobre_extremo", "facpob07", "factor07", "anio"]
    base[cols].to_parquet(SALIDAS / "personas_2024.parquet", index=False)
    ind.to_csv(SALIDAS / "indicadores.csv", index=False)
    print("Guardado: salidas/personas_2024.parquet, salidas/indicadores.csv, salidas/validacion.txt")


if __name__ == "__main__":
    main()
