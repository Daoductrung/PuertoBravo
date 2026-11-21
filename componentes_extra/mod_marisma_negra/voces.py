"""Genera con Phonon las voces de las escenas de Marisma Negra, en español y en inglés, para su componente.

    ..\\..\\.venv\\Scripts\\python.exe voces.py es        las españolas, en voces\\marisma_negra_es
    ..\\..\\.venv\\Scripts\\python.exe voces.py en        las inglesas, en voces\\marisma_negra_en (necesita la traducción del mod)

Usa lo mismo que las voces del juego (adjuntos\\voces_phonon): el protagonista y el narrador suenan como en el resto de la
historia; los vecinos de la marisma tienen voces que nadie más lleva en su idioma, o una mezcla de dos. Cada frase se
genera hasta veinte veces y se queda la que mejor entiende el reconocedor. Lo ya hecho no se repite.
"""
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
COD = sys.argv[1] if len(sys.argv) > 1 else "es"
FONO = os.path.join(RAIZ, "adjuntos", "voces_phonon")
sys.path.insert(0, FONO)
sys.argv = [sys.argv[0], COD]                                 # producir_idioma lee el idioma de aquí al importarse

import soundfile as sf                                        # noqa: E402

import producir as P                                          # noqa: E402

HISTORIA = "marisma_negra"
SALIDA = os.path.join(AQUI, "voces", f"{HISTORIA}_{COD}")
INFORME = os.path.join(AQUI, f"voces_{COD}.json")
SEXO = {"Amador": "hombre", "Celia": "mujer", "Toñi": "mujer", "Ruano": "hombre"}
SEMILLAS = tuple(range(1, 21))


def lineas_del_mod():
    mod = json.load(open(os.path.join(AQUI, f"{HISTORIA}.json"), encoding="utf-8"))
    for m in mod.get("misiones", []):
        for k, paso in enumerate(m.get("pasos", [])):
            if paso.get("tipo") != "dialogo":
                continue
            for n, linea in enumerate(paso.get("lineas", [])):
                quien, texto = (linea.get("quien"), linea.get("texto")) if isinstance(linea, dict) else (linea[0], linea[1])
                yield m["id"], k, n, quien, texto


def guion():
    if COD == "es":
        for mid, k, n, quien, texto in lineas_del_mod():
            for sufijo, pj, g in P.formas(quien, texto):
                yield {"archivo": f"{mid}_{k + 1}_{n + 1}{sufijo}", "quien": quien, "texto": P.texto_para(texto, pj, g), "pj": pj, "g": g}
        return
    import producir_idioma as PI
    cat = json.load(open(os.path.join(RAIZ, "traduccion", COD, "mods", f"{HISTORIA}.json"), encoding="utf-8"))["textos"]
    for mid, k, n, quien, texto in lineas_del_mod():
        t = cat.get(texto)
        if not t:
            raise SystemExit(f"Falta la traducción de: {texto}")
        for sufijo, pj, g in P.formas(quien, t):
            yield {"archivo": f"{mid}_{k + 1}_{n + 1}{sufijo}", "quien": quien, "texto": PI.texto_para(t, pj, g), "pj": pj, "g": g}


def reparto():
    """La voz de cada uno: las del juego para el protagonista y el narrador; para los vecinos, voces libres del idioma."""
    if COD == "es":
        base = json.load(open(os.path.join(FONO, "reparto_final.json"), encoding="utf-8"))
    else:
        base = json.load(open(os.path.join(FONO, f"reparto_{COD}.json"), encoding="utf-8"))
    cat = [json.loads(l) for l in open(P.CATALOGO, encoding="utf-8")]
    cat = [v for v in cat if (v.get("language") == COD or str(v.get("language", "")).startswith(COD)) and v.get("gender") in ("female", "male")]
    usadas = {e.get("id") for e in base["personajes"].values()} | {e.get("id") for e in base["protagonista"].values()}
    libres = {s: [v for v in cat if (v["gender"] == "female") == (s == "mujer") and v["voice_id"] not in usadas] for s in ("mujer", "hombre")}
    todas = {s: [v for v in cat if (v["gender"] == "female") == (s == "mujer")] for s in ("mujer", "hombre")}
    r = {"protagonista": base["protagonista"], "personajes": {"Narrador": base["personajes"]["Narrador"]}}
    turno = {"mujer": 3, "hombre": 3}
    for quien, sexo in SEXO.items():
        if libres[sexo]:
            v = libres[sexo].pop(0)
            r["personajes"][quien] = {"tipo": "pura", "id": v["voice_id"], "voz": v["name"]}
        else:                                                      # dos del idioma, a medias: un timbre que no tiene nadie
            vs = todas[sexo]
            a, b = vs[turno[sexo] % len(vs)], vs[(turno[sexo] + 5) % len(vs)]
            turno[sexo] += 2
            r["personajes"][quien] = {"tipo": "mezcla", "id": a["voice_id"], "con_id": b["voice_id"], "parte": 0.5, "voz": f"{a['name']} con {b['name']}"}
    return r


def main():
    import ptts
    rep = reparto()
    json.dump(rep, open(os.path.join(AQUI, f"reparto_{COD}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    informe = json.load(open(INFORME, encoding="utf-8")) if os.path.exists(INFORME) else {}
    tts = ptts.TTS(P.MODELO, lang=COD)
    puestas = set()
    por_id = {}
    lineas = list(guion())
    os.makedirs(SALIDA, exist_ok=True)
    for i, l in enumerate(lineas, 1):
        salida = os.path.join(SALIDA, l["archivo"] + ".ogg")
        ya = informe.get(l["archivo"])
        if ya and ya.get("texto") == l["texto"] and ya.get("guardada") and os.path.exists(salida):
            continue
        if l["quien"] == P.PROTA:
            clave, esp = f"prota_{l['pj']}_{l['g']}", rep["protagonista"][f"{l['pj']}_{l['g']}"]
        else:
            clave, esp = "mn_" + l["quien"], rep["personajes"][l["quien"]]
        if clave not in puestas:
            if esp["tipo"] == "pura":
                tts.add_voice(clave, os.path.join(P.MODELO, "voces", esp["id"] + ".safetensors"))
            else:
                P.poner_voz(tts, clave, esp, por_id)
            puestas.add(clave)
        if COD == "es":
            r = P.probar(tts, clave, l["texto"], semillas=SEMILLAS, basta=0.95)
        else:
            import producir_idioma as PI
            r = PI.probar(tts, clave, l["texto"], semillas=SEMILLAS, basta=0.95)
        guardada = r["nota"] >= 0.8
        if guardada:
            sf.write(salida, r["pcm"], tts.sample_rate, format="OGG", subtype="VORBIS")
        informe[l["archivo"]] = {"texto": l["texto"], "quien": l["quien"], "nota": r["nota"], "oido": r["oido"], "guardada": guardada}
        json.dump(informe, open(INFORME, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        print(f"{i}/{len(lineas)} {l['archivo']} {r['nota']}", flush=True)
    malas = [k for k, v in informe.items() if not v.get("guardada")]
    print("FIN", COD, len(lineas), "frases;", len(lineas) - len(malas), "guardadas; sin guardar:", malas)


if __name__ == "__main__":
    main()
