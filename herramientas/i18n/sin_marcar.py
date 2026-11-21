"""Busca en el código textos en español que no van en tr(): lo que el marcador no envolvió.

    python herramientas\\i18n\\sin_marcar.py [carpeta...]       de serie: juego, editor y panel_servidor

Mira las cadenas y los f-strings que no están dentro de tr() ni van al registro, y dice los que parecen españoles: con
palabras que solo son españolas, con letras del español, o palabras sueltas de la lista de abajo (puntos cardinales,
grados...). Es un aviso: algunos son identificadores o comparaciones que no se tocan.
"""
import ast
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fugas  # noqa: E402

SALTAR = {"registro", "logging", "log", "print", "tr", "es", "depurar", "anotar_fallo", "_volcar"}
SALTAR_ATTR = {"info", "aviso", "error", "debug", "warning", "exception", "critical", "una_vez", "anotar", "evento", "son", "sonar",
               "get", "setdefault", "pop", "startswith", "endswith", "split", "replace", "strip", "index", "count", "find", "join_path", "data",
               "carpeta_data", "archivo_config", "lug", "precio", "seccion", "entero", "lista", "frase", "dato_adulto"}


def _texto(n):
    if isinstance(n, ast.Constant) and isinstance(n.value, str):
        return n.value
    if isinstance(n, ast.JoinedStr):
        return "".join(v.value if isinstance(v, ast.Constant) else " X " for v in n.values)
    return None


def revisar(ruta):
    src = open(ruta, encoding="utf-8").read()
    arbol = ast.parse(src)
    padres = {}
    for n in ast.walk(arbol):
        for h in ast.iter_child_nodes(n):
            padres[h] = n
    salida = []
    for n in ast.walk(arbol):
        t = _texto(n)
        if t is None or isinstance(padres.get(n), ast.JoinedStr):
            continue
        p, dentro, hijo = padres.get(n), False, n
        while p is not None:
            if isinstance(p, ast.Call) and hijo is not p.func:      # «f"...".strip()»: el texto es de quien llama, no se salta
                f = p.func
                nombre = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else ""
                base = f.value.id if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) else ""
                if nombre in SALTAR or base in SALTAR or (nombre in SALTAR_ATTR and isinstance(f, ast.Attribute)):
                    dentro = True
                    break
            if isinstance(p, (ast.Compare, ast.Subscript)) or (isinstance(p, ast.Expr) and isinstance(p.value, ast.Constant)):
                dentro = True
                break
            if isinstance(p, ast.Dict) and n in p.keys:
                dentro = True
                break
            if isinstance(p, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                break
            hijo, p = p, padres.get(p)
        if dentro:
            continue
        limpio = re.sub(r"\{[^}]*\}", " ", t)
        if not re.search(r"[A-Za-zÁÉÍÓÚáéíóúñÑ]{3}", limpio) or "\\" in limpio or re.fullmatch(r"[a-z0-9_.]+", limpio.strip()) and not fugas.RARAS.search(limpio):
            continue
        if fugas.sospechosa(limpio) or (isinstance(n, ast.JoinedStr) and re.search(r"[a-záéíóúñ]{3,} [a-záéíóúñ]{3,}", limpio)):
            salida.append((n.lineno, t[:140]))
    return salida


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    total = 0
    for carpeta in sys.argv[1:] or ("juego", "editor", "panel_servidor"):
        for raiz, _d, archivos in os.walk(os.path.join(RAIZ, carpeta)):
            for a in sorted(archivos):
                if a.endswith(".py") and a != "i18n.py":
                    r = os.path.join(raiz, a)
                    for linea, t in revisar(r):
                        total += 1
                        print(f"{os.path.relpath(r, RAIZ)}:{linea}: {t!r}")
    print("Total:", total)
