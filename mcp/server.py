"""Servidor MCP del BCRP — Tarea 4.

    uv run pytest mcp -q                                  # 10 pruebas (8 originales + 2 propias)
    uv run mcp/server.py                                  # el servidor, por stdio
    claude mcp add --scope project bcrp -- uv run mcp/server.py

Herramientas: buscar_series, serie, resumen, correlacion (propia) y graficar_serie.
Recurso: bcrp://serie/{codigo}. Prompt: informe(tema).
Todas las cuentas las hace Python, no el modelo: cada cifra sale de una llamada repetible.
"""
import re
import time
import unicodedata
from functools import cache
from pathlib import Path

import httpx
import pandas as pd
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

AQUI = Path(__file__).parent
RAIZ = AQUI.parent
CATALOGO = RAIZ / "datos" / "catalogo_bcrp.csv"
FIGURAS = RAIZ / "figuras"
URL_CATALOGO = "https://estadisticas.bcrp.gob.pe/estadisticas/series/metadata"
API = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api"
SOLO_LECTURA = {"readOnlyHint": True, "openWorldHint": True}

MESES = {"ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6, "jul": 7, "ago": 8,
         "set": 9, "sep": 9, "oct": 10, "nov": 11, "dic": 12}

mcp = FastMCP("bcrp", instructions=(
    "Series oficiales del Banco Central de Reserva del Perú (BCRP). Primero busca el código con buscar_series; "
    "luego usa resumen para variaciones, promedios y extremos, serie para los datos, correlacion para asociar "
    "dos series y graficar_serie para guardar un gráfico. No calcules a mano: cita siempre el código de la "
    "serie, el periodo y la fuente."))


def _sin_tildes(s):
    return unicodedata.normalize("NFD", str(s).lower()).encode("ascii", "ignore").decode()


@cache
def catalogo():
    """El catálogo oficial (unas 17 mil series). Se baja una vez y queda en datos/."""
    if not CATALOGO.exists():
        CATALOGO.parent.mkdir(exist_ok=True)
        r = httpx.get(URL_CATALOGO, timeout=120)
        r.raise_for_status()
        CATALOGO.write_text(r.content.decode("latin-1"), encoding="utf-8")
    df = pd.read_csv(CATALOGO, sep=";", dtype=str).fillna("")
    df = df.rename(columns={"Código de serie": "codigo", "Categoría de serie": "categoria", "Grupo de serie": "grupo",
                            "Nombre de serie": "nombre", "Frecuencia": "frecuencia",
                            "Fecha de actualización": "actualizada", "Fecha de inicio": "inicio"})
    df["texto"] = (df.categoria + " " + df.grupo + " " + df.nombre).map(_sin_tildes)
    return df


def _ficha(codigo):
    fila = catalogo().query("codigo == @codigo")
    if fila.empty:
        raise ToolError(f"No existe el código de serie {codigo!r}. Búsquenlo con buscar_series.")
    f = fila.iloc[0]
    return {"codigo": f.codigo, "nombre": f"{f.grupo} - {f.nombre}", "categoria": f.categoria,
            "frecuencia": f.frecuencia, "inicio": f.inicio, "actualizada": f.actualizada}


# ---------------------------------------------------------------- fechas
def _frecuencia(ficha):
    f = _sin_tildes(ficha["frecuencia"])
    for clave in ("diaria", "mensual", "trimestral", "anual"):
        if clave in f:
            return clave
    raise ToolError(f"Frecuencia no soportada: {ficha['frecuencia']!r}")


def _fecha_api(fecha: str, frec: str, fin: bool) -> str:
    """Convierte '2025-01', '2026-10-01', '2025-T1' o '2025' al formato que pide la API."""
    s = str(fecha).strip().upper()
    m = re.fullmatch(r"(\d{4})(?:-(T?)(\d{1,2}))?(?:-(\d{1,2}))?", s)
    if not m:
        raise ToolError(f"Fecha no reconocida: {fecha!r}. Usen 2025-01, 2026-10-01, 2025-T1 o 2025.")
    anio, _, parte, dia = m.groups()
    if frec == "anual":
        return anio
    if frec == "trimestral":
        return f"{anio}-{int(parte) if parte else (4 if fin else 1)}"
    if frec == "mensual":
        return f"{anio}-{int(parte) if parte else (12 if fin else 1)}"
    # diaria
    mes = int(parte) if parte else (12 if fin else 1)
    if dia:
        d = int(dia)
    else:
        d = pd.Period(f"{anio}-{mes:02d}", "M").days_in_month if fin else 1
    return f"{anio}-{mes:02d}-{d:02d}"


def _periodo(nombre: str, frec: str) -> str:
    """'Ene.2025' -> '2025-01'; '01.Oct.26' -> '2026-10-01'; 'T1.25' -> '2025-T1'; '2025' -> '2025'."""
    n = nombre.strip()
    if frec == "anual":
        return n
    if frec == "trimestral":
        t, a = n.split(".")
        return f"{2000 + int(a) if len(a) == 2 else a}-{t.upper()}"
    if frec == "mensual":
        mes, anio = n.split(".")
        return f"{anio}-{MESES[_sin_tildes(mes)[:3]]:02d}"
    dia, mes, anio = n.split(".")
    anio = 2000 + int(anio) if len(anio) == 2 else int(anio)
    return f"{anio}-{MESES[_sin_tildes(mes)[:3]]:02d}-{int(dia):02d}"


@cache
def _descargar(codigo: str, desde: str, hasta: str) -> tuple:
    url = f"{API}/{codigo}/json/{desde}/{hasta}"
    for intento in range(5):
        r = httpx.get(url, timeout=60, follow_redirects=True)
        try:
            return url, r.json()
        except ValueError:      # la API devuelve HTML cuando recibe muchos pedidos seguidos
            time.sleep(2 + 2 * intento)
    raise ToolError(f"La API del BCRP no devolvió JSON para {codigo} ({url}). Reintenten en unos segundos.")


def _datos(codigo, desde, hasta):
    ficha = _ficha(codigo)
    frec = _frecuencia(ficha)
    url, js = _descargar(codigo, _fecha_api(desde, frec, False), _fecha_api(hasta, frec, True))
    datos = []
    for p in js.get("periods", []):
        v = p["values"][0]
        try:
            datos.append({"periodo": _periodo(p["name"], frec), "valor": float(v)})
        except (ValueError, TypeError):
            continue    # 'n.d.'
    if not datos:
        raise ToolError(f"La serie {codigo} no tiene datos entre {desde} y {hasta}.")
    return ficha, url, datos


# ---------------------------------------------------------------- herramientas
@mcp.tool(annotations=SOLO_LECTURA)
def buscar_series(texto: str, frecuencia: str | None = None, limite: int = 10) -> list[dict]:
    """Busca series del BCRP por palabras: todas deben aparecer en la categoría, el grupo o el nombre.

    Ejemplos: "ipc 12 meses", "tipo de cambio interbancario venta", "reservas internacionales netas",
    "tasa de referencia", "cobre precio", "pbi variacion". frecuencia: "Diaria", "Mensual", "Trimestral" o
    "Anual". Devuelve el código, el nombre completo, la frecuencia y desde cuándo hay datos. Si no hay
    resultados, prueben con menos palabras.
    """
    df = catalogo()
    m = pd.Series(True, index=df.index)
    for palabra in _sin_tildes(texto).split():
        m &= df.texto.str.contains(re.escape(palabra))
    if frecuencia:
        m &= df.frecuencia.str.lower() == frecuencia.lower()
    sel = df[m]
    orden = sel.assign(vieja=sel.actualizada < "2025", largo=(sel.grupo + sel.nombre).str.len())
    return [_ficha(c) for c in orden.sort_values(["vieja", "largo"]).head(limite).codigo]


@mcp.tool(annotations=SOLO_LECTURA)
def serie(codigo: str, desde: str, hasta: str) -> dict:
    """Descarga los datos oficiales de una serie del BCRP entre dos fechas.

    Fechas: "2025-01" (mensual), "2026-10-01" (diaria), "2025-T1" (trimestral) o "2025" (anual).
    Devuelve codigo, nombre, frecuencia, datos [{periodo, valor}] y la URL de la fuente. Omite los "n.d.".
    """
    ficha, url, datos = _datos(codigo, desde, hasta)
    return {"codigo": codigo, "nombre": ficha["nombre"], "frecuencia": ficha["frecuencia"],
            "datos": datos, "fuente": url}


@mcp.tool(annotations=SOLO_LECTURA)
def resumen(codigo: str, desde: str, hasta: str) -> dict:
    """Resume una serie del BCRP en un periodo, calculado en Python: primero, ultimo, cambio (último − primero),
    variacion_pct ((último/primero − 1)×100), promedio, maximo y minimo (con su periodo) y n observaciones.
    Úsenla en lugar de hacer cuentas a mano.
    """
    ficha, url, datos = _datos(codigo, desde, hasta)
    df = pd.DataFrame(datos)
    i_max, i_min = df.valor.idxmax(), df.valor.idxmin()
    primero, ultimo = datos[0], datos[-1]
    var = None if primero["valor"] == 0 else round((ultimo["valor"] / primero["valor"] - 1) * 100, 4)
    return {"codigo": codigo, "nombre": ficha["nombre"], "frecuencia": ficha["frecuencia"],
            "n": len(df), "primero": primero, "ultimo": ultimo,
            "cambio": round(ultimo["valor"] - primero["valor"], 6), "variacion_pct": var,
            "promedio": round(float(df.valor.mean()), 6),
            "maximo": {"periodo": df.periodo[i_max], "valor": float(df.valor[i_max])},
            "minimo": {"periodo": df.periodo[i_min], "valor": float(df.valor[i_min])},
            "fuente": url}


@mcp.tool(annotations=SOLO_LECTURA)
def correlacion(codigo_a: str, codigo_b: str, desde: str, hasta: str) -> dict:
    """Correlación de Pearson entre dos series del BCRP de la MISMA frecuencia, alineando periodos.

    Descarga ambas, conserva solo los periodos con dato en las dos (descarta faltantes y lo informa), exige al
    menos 6 pares y devuelve r, n, el primer y último periodo usado, los periodos descartados y las fuentes.
    Es una asociación descriptiva: no demuestra causalidad.
    """
    fa, fb = _ficha(codigo_a), _ficha(codigo_b)
    if _frecuencia(fa) != _frecuencia(fb):
        raise ToolError(f"Frecuencias distintas: {codigo_a} es {fa['frecuencia']} y {codigo_b} es "
                        f"{fb['frecuencia']}. Elijan series de la misma frecuencia.")
    _, url_a, da = _datos(codigo_a, desde, hasta)
    _, url_b, db = _datos(codigo_b, desde, hasta)
    a = pd.DataFrame(da).set_index("periodo").valor.rename("a")
    b = pd.DataFrame(db).set_index("periodo").valor.rename("b")
    juntos = pd.concat([a, b], axis=1)
    pares = juntos.dropna()
    if len(pares) < 6:
        raise ToolError(f"Solo hay {len(pares)} periodos en común entre {codigo_a} y {codigo_b}; se necesitan 6.")
    r = float(pares.a.corr(pares.b))
    return {"codigo_a": codigo_a, "nombre_a": fa["nombre"], "codigo_b": codigo_b, "nombre_b": fb["nombre"],
            "r": round(r, 4), "n": len(pares), "desde": pares.index[0], "hasta": pares.index[-1],
            "descartados": sorted(set(juntos.index) - set(pares.index)),
            "nota": "Asociación lineal descriptiva; no implica causalidad.",
            "fuentes": [url_a, url_b]}


@mcp.tool(annotations={"readOnlyHint": False, "openWorldHint": True})
def graficar_serie(codigo: str, desde: str, hasta: str, titulo: str | None = None) -> dict:
    """Grafica una serie oficial del BCRP y guarda el PNG en figuras/bcrp_{codigo}.png (200 dpi).
    El gráfico lleva título, unidad, periodo y la fuente con el código. Devuelve la ruta del archivo.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ficha, url, datos = _datos(codigo, desde, hasta)
    df = pd.DataFrame(datos)
    FIGURAS.mkdir(exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(range(len(df)), df.valor, color="#1f4e79", lw=2)
    paso = max(1, len(df) // 10)
    ax.set_xticks(range(0, len(df), paso), df.periodo[::paso], rotation=45, ha="right")
    ax.set_title(titulo or f"{ficha['nombre']}\n{df.periodo.iloc[0]} a {df.periodo.iloc[-1]}", fontsize=11)
    ax.grid(axis="y", alpha=.3)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    fig.text(0.01, 0.01, f"Fuente: BCRP, serie {codigo} ({ficha['frecuencia']}). {url}", fontsize=7, color="gray")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    ruta = FIGURAS / f"bcrp_{codigo}.png"
    fig.savefig(ruta, dpi=200)
    plt.close(fig)
    return {"archivo": str(ruta.relative_to(RAIZ)), "codigo": codigo, "n": len(df), "fuente": url}


# ---------------------------------------------------------------- recurso y prompt
@mcp.resource("bcrp://serie/{codigo}", mime_type="application/json")
def ficha_serie(codigo: str) -> dict:
    """Ficha descriptiva de una serie del BCRP: nombre, categoría, frecuencia, inicio y última actualización."""
    return _ficha(codigo)


@mcp.prompt
def informe(tema: str) -> str:
    """Plantilla para redactar un informe breve con series del BCRP, citando código y periodo de cada cifra."""
    return (f"Redacta un informe breve sobre: {tema}.\n"
            "1. Usa buscar_series para encontrar los códigos oficiales pertinentes.\n"
            "2. Usa resumen (y serie si hace falta) para obtener cada cifra; no calcules a mano.\n"
            "3. Si comparas dos series, usa correlacion y aclara que es una asociación, no causalidad.\n"
            "4. Cada cifra va con su código de serie, periodo y la frase 'Fuente: BCRP'.\n"
            "5. Si una herramienta falla o no hay datos, dilo; no inventes valores.")


if __name__ == "__main__":
    mcp.run()
