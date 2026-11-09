"""Mapa coroplético de pobreza monetaria departamental, ENAHO 2024.

    uv run .claude/skills/mapeando-enaho/scripts/mapear.py

Une por código (ubigeo[:2] = FIRST_IDDP), nunca por nombre. Exige 25 departamentos con dato, Lima (15) y
Callao (07) separados, y compara con la referencia de la Sesión 16.
Sale: mapas/pobreza_departamento.png, salidas/pobreza_departamento.csv, salidas/comparacion_mapa.csv
"""
import sys
from pathlib import Path

import geopandas as gpd
import httpx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[3]
BASE = RAIZ / "salidas" / "personas_2024.parquet"
GEO = RAIZ / "datos" / "peru_departamental_simple.geojson"
URL_GEO = ("https://raw.githubusercontent.com/d2cml-ai/Data-Science-Python/main/sessions/06-geoespacial/"
           "lab/Data/peru_departamental_simple.geojson")
REFERENCIA = AQUI.parent / "referencia" / "pobreza_departamento_2024.csv"


def main():
    if not BASE.exists():
        sys.exit("ERROR: falta salidas/personas_2024.parquet. Ejecuten primero la skill limpiando-enaho.")
    if not GEO.exists():
        GEO.parent.mkdir(exist_ok=True)
        GEO.write_bytes(httpx.get(URL_GEO, timeout=60, follow_redirects=True).content)

    df = pd.read_parquet(BASE)
    dep = (df.groupby("departamento")
           .apply(lambda d: np.average(d.pobre, weights=d.facpob07) * 100, include_groups=False)
           .rename("pobreza_pct").reset_index())
    geo = gpd.read_file(GEO)
    geo["ccdd"] = geo["FIRST_IDDP"].astype(str).str.strip().str.zfill(2)
    mapa = geo.merge(dep, left_on="ccdd", right_on="departamento", how="left", validate="1:1")

    faltan = mapa[mapa.pobreza_pct.isna()]
    if len(mapa) != 25 or not faltan.empty:
        sys.exit(f"ERROR: el mapa tiene {len(mapa)} unidades y {len(faltan)} sin dato: {list(faltan.ccdd)}")
    if not {"07", "15"} <= set(mapa.ccdd):
        sys.exit("ERROR: Lima (15) y Callao (07) deben estar separados.")

    ref = pd.read_csv(REFERENCIA, dtype={"ccdd": str})
    comp = ref.merge(dep, left_on="ccdd", right_on="departamento", how="left")
    comp["calculado"] = comp.pobreza_pct_y.round(1)
    comp["diferencia"] = (comp.calculado - comp.pobreza_pct_x).round(1)
    comp = comp[["ccdd", "departamento_x", "pobreza_pct_x", "calculado", "diferencia"]]
    comp.columns = ["ccdd", "departamento", "referencia", "calculado", "diferencia"]
    (RAIZ / "salidas").mkdir(exist_ok=True)
    comp.to_csv(RAIZ / "salidas" / "comparacion_mapa.csv", index=False)
    dep.round(2).to_csv(RAIZ / "salidas" / "pobreza_departamento.csv", index=False)

    fig, ax = plt.subplots(figsize=(7, 9))
    mapa.plot(column="pobreza_pct", cmap="Reds", vmin=0, linewidth=.4, edgecolor="white", ax=ax, legend=True,
              legend_kwds={"label": "% de personas en pobreza monetaria", "shrink": .6})
    for _, f in mapa.iterrows():
        p = f.geometry.representative_point()
        ax.annotate(f"{f.pobreza_pct:.1f}", (p.x, p.y), ha="center", fontsize=6.5,
                    color="white" if f.pobreza_pct > 30 else "black")
    ax.set_axis_off()
    ax.set_title("Pobreza monetaria por departamento, Perú 2024\n% de personas (estimación ponderada)", fontsize=12)
    fig.text(.02, .02, "Fuente: INEI, ENAHO 2024 (módulos 34 y 02), ponderado con facpob07. "
             "Límites: repositorio del curso. Lima y Callao por separado.", fontsize=6.5, color="gray")
    (RAIZ / "mapas").mkdir(exist_ok=True)
    fig.savefig(RAIZ / "mapas" / "pobreza_departamento.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    print(f"Unidades territoriales con dato: {mapa.pobreza_pct.notna().sum()}/25")
    print(f"Máxima diferencia con la referencia: {comp.diferencia.abs().max():.1f} pp")
    print(comp.to_string(index=False))
    print("Guardado: mapas/pobreza_departamento.png, salidas/pobreza_departamento.csv, salidas/comparacion_mapa.csv")


if __name__ == "__main__":
    main()
