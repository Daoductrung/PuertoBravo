"""Genera con Phonon las voces de las escenas de El Diablo, en español y en inglés.

    .venv\\Scripts\\python.exe componentes_extra\\mod_el_diablo\\voces.py es     las españolas, en data\\voces\\el_diablo_es
    .venv\\Scripts\\python.exe componentes_extra\\mod_el_diablo\\voces.py en     las inglesas, en data\\voces\\el_diablo_en
                                                                              (necesita traduccion\\en\\mods\\el_diablo.json)

Usa lo mismo que las voces del juego (adjuntos\\voces_phonon): el protagonista suena como en el resto de la historia.
El Diablo lleva una voz que no tiene nadie más: la mezcla, a partes iguales, de dos voces graves del idioma. Cada
frase se genera hasta veinte veces y se queda la que mejor entiende el reconocedor. Lo ya hecho no se repite.
Desde la 1.7.4 las voces vienen con el juego; el componente para la 1.7.3 las coge de la misma carpeta.
"""
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
COD = sys.argv[1] if len(sys.argv) > 1 else "es"
FONO = os.path.join(RAIZ, "adjuntos", "voces_phonon")
sys.path.insert(0, FONO)
MAS = "mas" in sys.argv[2:]
sys.argv = [sys.argv[0], COD]                                 # producir_idioma lee el idioma de aquí al importarse

import soundfile as sf                                        # noqa: E402

import producir as P                                          # noqa: E402

HISTORIA = "el_diablo"
MOD = os.path.join(RAIZ, "data", "mods", f"{HISTORIA}.json")
SALIDA = os.path.join(RAIZ, "data", "voces", f"{HISTORIA}_{COD}")
INFORME = os.path.join(AQUI, f"voces_{COD}.json")
SEMILLAS = tuple(range(1, 21))
# Si alguna frase no sale con esas, se repite solo esa con más semillas: voces.py en mas
if MAS:
    SEMILLAS = tuple(range(21, 101))
    if COD != "es":
        # Una frase inglesa que empieza por un nombre español (Rubén Saldaña, El Diablo) hace que el reconocedor la tome
        # por española y la descarte aunque se oiga en inglés. En este repaso cuenta solo que lo oído se parezca al
        # texto inglés: si la voz hablara en español, lo oído saldría en español y no se parecería.
        _entender = P.entender
        P.entender = lambda pcm, sr: (_entender(pcm, sr)[0], COD)
# Cómo se le escribe al modelo un nombre que pronuncia mal; el texto del juego no cambia, solo lo que se graba.
PRONUNCIA = {"en": {"Saldaña": "Saldanya"}}
# Dos voces graves que ningún personaje lleva juntas: Lalo y Ulises en español, Trevor y Edwin en inglés.
DIABLO = {"es": ("F05gqkzX7WhKVpSL", "G5HLUsQd659UtRe7", "Lalo con Ulises"),
          "en": ("0zLApsZfVLLNaEGl", "zUCxzrOrugTSis03", "Trevor con Edwin")}


def lineas_del_mod():
    mod = json.load(open(MOD, encoding="utf-8"))
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
        for a, b in PRONUNCIA.get(COD, {}).items():
            t = t.replace(a, b)
        for sufijo, pj, g in P.formas(quien, t):
            yield {"archivo": f"{mid}_{k + 1}_{n + 1}{sufijo}", "quien": quien, "texto": PI.texto_para(t, pj, g), "pj": pj, "g": g}


def reparto():
    base = json.load(open(os.path.join(FONO, "reparto_final.json" if COD == "es" else f"reparto_{COD}.json"), encoding="utf-8"))
    a, b, nombre = DIABLO[COD]
    return {"protagonista": base["protagonista"],
            "personajes": {"El Diablo": {"tipo": "mezcla", "id": a, "con_id": b, "parte": 0.5, "voz": nombre}}}


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
            clave, esp = "di_" + l["quien"], rep["personajes"][l["quien"]]
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
