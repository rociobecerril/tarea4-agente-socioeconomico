"""Experimento Modo A (sin MCP ni Skills) vs. Modo B (con MCP y Skills): mismas 10 preguntas, mismo modelo.

    uv run evaluacion/evaluar.py                    # ambos modos, Haiku
    uv run evaluacion/evaluar.py --modelo sonnet

Cada pregunta se lanza en una sesión independiente de Claude Code (claude -p --no-session-persistence).
Modo A: sin herramientas (--tools ""), sin MCP (--strict-mcp-config) y sin Skills: no puede leer archivos con
respuestas. Modo B: servidor MCP bcrp + Skill + Bash/Read/Glob para ejecutar los scripts de las skills.
Las respuestas esperadas (preguntas.csv) se fijaron antes de correr y no se modifican.
Escribe evaluacion/resultados.csv, evaluacion/respuestas_crudas.jsonl y evaluacion/comparacion.md.
"""
import argparse
import json
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

AQUI = Path(__file__).parent
RAIZ = AQUI.parent
ESQUEMA = {"type": "object", "required": ["valor", "fuente"],
           "properties": {"valor": {"type": ["number", "null"]}, "unidad": {"type": "string"},
                          "fuente": {"type": "string"}, "herramientas": {"type": "string"}}}
INSTRUCCION = ("Responde con un solo número en «valor», en la unidad que pide la pregunta. Si no puedes saberlo "
               "con certeza, pon valor null: no estimes. En «fuente» di de dónde sale la cifra y en "
               "«herramientas» qué herramientas o skills usaste (o 'ninguna').\n\n")
MODOS = {
    "A_sin": {"args": ["--tools", "", "--strict-mcp-config", "--disallowedTools", "Skill"],
              "habilitado": "ninguna herramienta, sin MCP, sin Skills"},
    "B_con": {"args": ["--strict-mcp-config", "--mcp-config", str(RAIZ / ".mcp.json"),
                       "--tools", "Skill,Bash,Read,Glob",
                       "--allowedTools", "mcp__bcrp,Skill,Bash,Read,Glob"],
              "habilitado": "MCP bcrp + Skills del proyecto + Bash/Read/Glob (sin web)"},
}


def preguntar(pregunta, modo, modelo):
    cmd = ["claude", "-p", INSTRUCCION + pregunta, "--output-format", "json", "--json-schema", json.dumps(ESQUEMA),
           "--no-session-persistence", "--model", modelo, *MODOS[modo]["args"]]
    t = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=900, cwd=RAIZ)
        salida = json.loads(proc.stdout)
    except (json.JSONDecodeError, subprocess.TimeoutExpired) as e:
        salida = {"result": f"ERROR: {e}"[-300:]}
    r = salida.get("structured_output") or {}
    return {"valor": r.get("valor"), "fuente": r.get("fuente", ""), "herramientas": r.get("herramientas", ""),
            "segundos": round(time.time() - t, 1), "turnos": salida.get("num_turns"),
            "error": "" if r else str(salida.get("result", ""))[:300], "_crudo": salida}


def calificar(valor, verdad, tol):
    if valor is None:
        return "no responde"
    return "correcta" if abs(float(valor) - verdad) <= tol else "incorrecta"


def comparacion(res, modelo):
    t = res.groupby("modo").resultado.value_counts().unstack(fill_value=0)
    for c in ["correcta", "incorrecta", "no responde"]:
        if c not in t:
            t[c] = 0
    t["segundos_promedio"] = res.groupby("modo").segundos.mean().round(1)
    piv = res.pivot(index="id", columns="modo", values="resultado")
    mejoran = piv[(piv.get("A_sin") != "correcta") & (piv.get("B_con") == "correcta")].index.tolist()
    empeoran = piv[(piv.get("A_sin") == "correcta") & (piv.get("B_con") != "correcta")].index.tolist()
    por_tipo = res.assign(ok=res.resultado == "correcta").pivot_table(index="tipo", columns="modo", values="ok",
                                                                      aggfunc="sum")
    errores = res[res.resultado != "correcta"][["modo", "id", "verdad", "valor", "resultado", "error"]]
    lineas = [
        "# Comparación Modo A (sin MCP/Skills) vs. Modo B (con MCP/Skills)", "",
        f"Modelo: `{modelo}`. Cada pregunta en una sesión independiente de `claude -p`.", "",
        "| Modo | Herramientas habilitadas |", "|---|---|",
        *[f"| {m} | {v['habilitado']} |" for m, v in MODOS.items()], "",
        "## Resultados", "", t[["correcta", "incorrecta", "no responde", "segundos_promedio"]].to_markdown(), "",
        "## Aciertos por tipo de pregunta", "", por_tipo.to_markdown(), "",
        f"**Mejoran con MCP/Skills:** {', '.join(mejoran) or 'ninguna'}  ",
        f"**Empeoran con MCP/Skills:** {', '.join(empeoran) or 'ninguna'}", "",
        "## Respuestas no correctas", "", errores.to_markdown(index=False) if len(errores) else "Ninguna.", "",
        "## Conclusión", "", "_(Redactar a partir de las tablas anteriores: utilidad de MCP y Skills, errores "
        "típicos del Modo A —cifras inventadas vs. reconocer que no sabe—, costo en tiempo del Modo B.)_", ""]
    (AQUI / "comparacion.md").write_text("\n".join(lineas), encoding="utf-8")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--modos", nargs="+", default=list(MODOS), choices=list(MODOS))
    p.add_argument("--modelo", default="haiku")
    p.add_argument("--paralelo", type=int, default=4)
    a = p.parse_args()
    preguntas = pd.read_csv(AQUI / "preguntas.csv")
    casos = [(q, m) for q in preguntas.itertuples() for m in a.modos]
    print(f"{len(casos)} llamadas a claude -p con {a.modelo}...")
    with ThreadPoolExecutor(a.paralelo) as ex:
        resp = list(ex.map(lambda c: preguntar(c[0].pregunta, c[1], a.modelo), casos))

    with open(AQUI / "respuestas_crudas.jsonl", "w", encoding="utf-8") as f:
        for (q, m), r in zip(casos, resp):
            f.write(json.dumps({"id": q.id, "modo": m, "salida": r["_crudo"]}, ensure_ascii=False) + "\n")
    filas = [{"id": q.id, "tipo": q.tipo, "modo": m, "pregunta": q.pregunta, "verdad": q.verdad,
              "tolerancia": q.tolerancia, **{k: v for k, v in r.items() if k != "_crudo"},
              "resultado": calificar(r["valor"], q.verdad, q.tolerancia)} for (q, m), r in zip(casos, resp)]
    res = pd.DataFrame(filas)
    res.to_csv(AQUI / "resultados.csv", index=False)
    comparacion(res, a.modelo)
    print(res.pivot(index="id", columns="modo", values="valor").to_string())
    print(res.groupby("modo").resultado.value_counts().unstack(fill_value=0).to_string())
