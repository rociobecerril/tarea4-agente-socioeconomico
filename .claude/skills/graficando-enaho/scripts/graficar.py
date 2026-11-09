"""Gráficos de pobreza monetaria ENAHO 2024, siempre ponderados con facpob07.

    uv run .claude/skills/graficando-enaho/scripts/graficar.py --tipo area|sexo|edad|departamento|todos

Entra: salidas/personas_2024.parquet (de limpiando-enaho). Sale: figuras/pobreza_<tipo>.png (200 dpi)
e imprime la tabla con las cifras graficadas.
"""
import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

RAIZ = Path(__file__).resolve().parents[4]
BASE = RAIZ / "salidas" / "personas_2024.parquet"
FIG = RAIZ / "figuras"
NOMBRES = {"01": "Amazonas", "02": "Áncash", "03": "Apurímac", "04": "Arequipa", "05": "Ayacucho",
           "06": "Cajamarca", "07": "Callao", "08": "Cusco", "09": "Huancavelica", "10": "Huánuco", "11": "Ica",
           "12": "Junín", "13": "La Libertad", "14": "Lambayeque", "15": "Lima", "16": "Loreto",
           "17": "Madre de Dios", "18": "Moquegua", "19": "Pasco", "20": "Piura", "21": "Puno",
           "22": "San Martín", "23": "Tacna", "24": "Tumbes", "25": "Ucayali"}
TITULOS = {"area": "La pobreza rural supera a la urbana", "sexo": "Pobreza monetaria según sexo",
           "edad": "Pobreza monetaria según grupo de edad",
           "departamento": "Pobreza monetaria por departamento: brechas territoriales amplias"}
COLUMNA = {"area": "area", "sexo": "sexo", "edad": "grupo_edad", "departamento": "departamento"}


def tabla(df, tipo):
    col = COLUMNA[tipo]
    t = (df.groupby(col, observed=True)
         .apply(lambda d: pd.Series({"pobreza_pct": np.average(d.pobre, weights=d.facpob07) * 100,
                                     "n_muestral": len(d)}), include_groups=False)
         .reset_index().rename(columns={col: "grupo"}))
    if tipo == "departamento":
        t["grupo"] = t.grupo.map(NOMBRES)
    return t.sort_values("pobreza_pct", ascending=(tipo == "departamento"))


def graficar(df, tipo):
    t = tabla(df, tipo)
    nac = np.average(df.pobre, weights=df.facpob07) * 100
    horizontal = tipo == "departamento"
    fig, ax = plt.subplots(figsize=(8, 8) if horizontal else (7, 4.5))
    if horizontal:
        barras = ax.barh(t.grupo, t.pobreza_pct, color="#8c2d04")
        ax.axvline(nac, color="gray", ls="--", lw=1)
        ax.text(nac, len(t) - .3, f" Perú {nac:.1f} %", color="gray", fontsize=8)
        ax.set_xlabel("% de personas en pobreza monetaria")
        ax.set_xlim(0, t.pobreza_pct.max() * 1.15)
    else:
        barras = ax.bar(t.grupo.astype(str), t.pobreza_pct, color="#8c2d04", width=.55)
        ax.axhline(nac, color="gray", ls="--", lw=1)
        ax.text(-.4, nac + .6, f"Perú {nac:.1f} %", color="gray", fontsize=8)
        ax.set_ylabel("% de personas en pobreza monetaria")
        ax.set_ylim(0, t.pobreza_pct.max() * 1.2)
    ax.bar_label(barras, fmt="%.1f %%", padding=3, fontsize=8)
    ax.set_title(f"{TITULOS[tipo]}\nPerú, 2024 · % de personas (estimación ponderada)", fontsize=11)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    fig.text(.01, .01, "Fuente: INEI, ENAHO 2024 (módulos 34 y 02), residentes habituales, ponderado con facpob07.",
             fontsize=7, color="gray")
    fig.tight_layout(rect=(0, .03, 1, 1))
    FIG.mkdir(exist_ok=True)
    ruta = FIG / f"pobreza_{tipo}.png"
    fig.savefig(ruta, dpi=200)
    plt.close(fig)
    print(f"\n{ruta.relative_to(RAIZ)}\n{t.round(2).to_string(index=False)}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--tipo", default="todos", choices=[*TITULOS, "todos"])
    a = p.parse_args()
    if not BASE.exists():
        sys.exit("ERROR: falta salidas/personas_2024.parquet. Ejecuten primero la skill limpiando-enaho.")
    df = pd.read_parquet(BASE)
    for tipo in (TITULOS if a.tipo == "todos" else [a.tipo]):
        graficar(df, tipo)
