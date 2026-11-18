"""Jugar juntos con versiones distintas del juego: lo que el servidor hace para que nadie se quede fuera ni se rompa.

Tres cosas, y ninguna necesita el juego:

- El **catálogo** de un mundo: qué armas y qué vehículos conoce el juego de una versión. Con él, el servidor sabe qué
  no entiende el juego de cada jugador, y en vez de mandarle un arma o un vehículo que no conoce le manda el más
  parecido de los que sí conoce. El daño, el alcance y la cadencia los decide siempre el servidor con las cifras de su
  mundo, sea cual sea la versión de quien dispara o de quien recibe: el equivalente es solo lo que el otro oye y ve.
- El **personaje** que viaja entre versiones: a un juego anterior se le da sin las armas y los vehículos que no
  conoce (se quedan guardados en el servidor), y cuando ese juego guarda, el servidor vuelve a poner lo que ese
  juego no sabía guardar. Así nada de lo nuevo se pierde por pasar por una versión anterior.
- Las **nóminas**: qué paga cada puesto de un contrato fijo según el mundo, para que el servidor pague la suya y no
  la que diga el juego de cada cual.

Funciona con Python 3.8 y solo usa la biblioteca de serie.
"""
import math

# Los mundos de las versiones publicadas, para saber qué conoce el juego de cada una sin tener que pedírselo.
# Al publicar una versión que añada armas o vehículos, se apunta aquí el catálogo de la anterior
# (herramientas/exportar_mundo_servidor.py --catalogo lo escribe).
CATALOGOS = {
    "180125344b7496ff": {
        "version": "1.7.0",
        "armas": ["ametralladora", "ballesta", "bate", "carabina", "cd_arpon", "cd_bengala", "cd_remo", "escopeta", "escopeta_combate", "fusil",
                  "granada", "iv_fusil", "iv_garfio", "katana", "lanzacohetes", "machete", "minigun", "molotov", "navaja", "nn_derringer", "nn_porra",
                  "oc_garrafa", "oc_llave", "oc_remachadora", "pa_carabina", "pa_dinamita", "pa_pico", "pistola", "puno_americano", "punos",
                  "revolver", "rifle", "silenciada", "subfusil", "uzi", "vo_escopeta", "vo_hoz"],
        "modelos": ["ambulancia", "autobus", "avioneta", "bici", "blindado", "bomberos", "buggy", "camion", "caravana", "carreras", "catamaran",
                    "cd_autogiro", "cd_buggy", "cd_reparto", "cd_velero", "cross", "deportivo", "descapotable", "funebre", "furgoneta", "grua",
                    "heladero", "helicoptero", "iv_catamaran", "iv_moto", "lancha", "lancha_rapida", "limusina", "lujo", "ma_cafe", "ma_clasico",
                    "ma_gt", "ma_rally", "monster", "moto", "moto_agua", "nn_limusina", "nn_taxi", "nn_vespa", "oc_cisterna", "oc_lanchon",
                    "oc_ranchera", "oc_rebajado", "oc_vigia", "of_moto", "pa_quad", "pa_trial", "pa_volquete", "patrulla", "pesquero", "pickup",
                    "quad", "remolcador", "scooter", "sedan", "taxi", "todoterreno", "tractor", "utilitario", "velero", "vo_campero", "vo_remolque",
                    "yate"],
    },
}
MAX_IDS = 2000                    # ningún mundo de verdad tiene tantas armas o vehículos: más es un mundo mal hecho
# Lo que va en la raíz de un personaje guardado y depende del momento (lo que conduces, dónde lo dejaste): si un guardado
# no lo trae es que ya no lo hay, no que ese juego no lo conozca.
VOLATILES = ("veh", "veh_fuera", "mis_vehiculos", "momento", "lugar", "version")


def _ids(cosas):
    return [str(k)[:60] for k in list(cosas)[:MAX_IDS] if isinstance(k, str) and k]


def catalogo_de(mundo):
    """El catálogo de un mundo, listo para guardar: su versión y los identificadores de sus armas y sus vehículos."""
    return {"version": str(mundo.get("version") or "")[:20], "armas": sorted(_ids(mundo.get("armas") or {})), "modelos": sorted(_ids(mundo.get("modelos") or {}))}


def en_uso(guardado):
    """Un catálogo guardado, puesto para consultarlo deprisa. None si no tiene la forma esperada."""
    try:
        return {"version": str(guardado.get("version") or ""), "armas": frozenset(_ids(guardado["armas"])), "modelos": frozenset(_ids(guardado["modelos"])), "eq": {}}
    except (TypeError, KeyError, AttributeError):
        return None


def _num(d, clave, defecto):
    try:
        v = float(d.get(clave, defecto))
        return v if math.isfinite(v) and v > 0 else float(defecto)
    except (TypeError, ValueError, AttributeError):
        return float(defecto)


def _lejos(a, b, claves):
    """Cuánto se parecen dos cosas por sus cifras: 0 es idénticas. Se comparan en proporción, no en valor."""
    return sum(peso * abs(math.log(_num(a, clave, defecto) / _num(b, clave, defecto))) for clave, defecto, peso in claves)


def _familia(cosa):
    """La primera palabra del nombre, sin tildes y recortada: «Escopeta de corredera» y «Escopeta de combate» son de la misma."""
    nombre = str((cosa or {}).get("nombre") or "").lower()
    for a, b in (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u")):
        nombre = nombre.replace(a, b)
    palabra = next((p for p in nombre.split() if len(p) >= 4), "")
    return palabra[:5]


def _misma_familia(a, b):
    return 0.0 if _familia(a) and _familia(a) == _familia(b) else 0.7


_CIFRAS_ARMA = (("dano", 10, 1.0), ("alcance", 2, 1.0), ("cadencia", 0.5, 0.7))
_CIFRAS_MODELO = (("vel_max", 25, 1.0), ("salud", 100, 0.6), ("acel", 6, 0.4))


def arma_equivalente(ident, armas, conocidas):
    """El arma más parecida a ``ident`` de entre las que conoce un juego. ``armas`` son las del mundo del servidor, con
    sus cifras. Se mira primero que sea de la misma clase (cuerpo a cuerpo, de fuego, explosivo) y después que se parezcan
    en las cifras, en el nombre y en si son automáticas."""
    a = armas.get(ident)
    candidatas = [k for k in conocidas if k in armas and k != ident]
    if not isinstance(a, dict) or not candidatas:
        return "punos" if "punos" in conocidas else (sorted(conocidas)[0] if conocidas else ident)
    misma = [k for k in candidatas if armas[k].get("tipo") == a.get("tipo")] or candidatas
    return min(sorted(misma), key=lambda k: _lejos(a, armas[k], _CIFRAS_ARMA) + _misma_familia(a, armas[k])
               + (0.0 if bool(armas[k].get("automatica")) == bool(a.get("automatica")) else 0.8))


def modelo_equivalente(ident, modelos, conocidos):
    """El vehículo más parecido a ``ident`` de entre los que conoce un juego: que vuele o no como él, y sus cifras."""
    m = modelos.get(ident)
    candidatos = [k for k in conocidos if k in modelos and k != ident]
    if not isinstance(m, dict) or not candidatos:
        return "utilitario" if "utilitario" in conocidos else (sorted(conocidos)[0] if conocidos else ident)
    mismo = [k for k in candidatos if bool(modelos[k].get("vuela")) == bool(m.get("vuela"))] or candidatos
    return min(sorted(mismo), key=lambda k: _lejos(m, modelos[k], _CIFRAS_MODELO) + _misma_familia(m, modelos[k]))


def diferencias(mundo, cat, suyo=None):
    """Qué no coincide entre el mundo del servidor y el del juego de un jugador, en nombres que se puedan decir.
    Devuelve (lo que el servidor tiene y su juego no, lo que su juego tiene y el servidor no): dos diccionarios con
    «armas» y «vehiculos», cada uno una lista de nombres. ``suyo`` es su mundo, si se tiene, para poder nombrarlo."""
    le_falta, sobra = {"armas": [], "vehiculos": []}, {"armas": [], "vehiculos": []}
    if not cat:
        return le_falta, sobra
    for clave, donde in (("armas", "armas"), ("modelos", "vehiculos")):
        mias = mundo.get(clave) or {}
        for k in sorted(mias):
            if k not in cat[clave]:
                le_falta[donde].append(str((mias[k] or {}).get("nombre") or k)[:60])
        suyas = (suyo or {}).get(clave) or {}
        for k in sorted(cat[clave]):
            if k not in mias:
                sobra[donde].append(str((suyas.get(k) or {}).get("nombre") or k)[:60])
    return le_falta, sobra


def _lista(nombres, tope=4):
    nombres = [n for n in nombres if n]
    if len(nombres) <= tope:
        return ", ".join(nombres[:-1]) + (" y " if len(nombres) > 1 else "") + nombres[-1] if nombres else ""
    return ", ".join(nombres[:tope]) + " y %d más" % (len(nombres) - tope)


def texto_diferencias(le_falta, sobra):
    """Lo mismo, dicho para el jugador: qué no coincide y qué va a notar. Vacío si no hay nada que decir."""
    out = []
    partes = []
    if le_falta["armas"]:
        partes.append("%s: %s" % ("un arma" if len(le_falta["armas"]) == 1 else "%d armas" % len(le_falta["armas"]), _lista(le_falta["armas"])))
    if le_falta["vehiculos"]:
        partes.append("%s: %s" % ("un vehículo" if len(le_falta["vehiculos"]) == 1 else "%d vehículos" % len(le_falta["vehiculos"]), _lista(le_falta["vehiculos"])))
    if partes:
        out.append("En este servidor hay cosas que tu versión del juego no tiene. " + ". ".join(p[0].upper() + p[1:] for p in partes) +
                   ". Las oirás y las verás como lo más parecido de lo que tu juego conoce; hacen el daño que marca el servidor, el mismo para todos.")
    partes = []
    if sobra["armas"]:
        partes.append("%s: %s" % ("un arma" if len(sobra["armas"]) == 1 else "%d armas" % len(sobra["armas"]), _lista(sobra["armas"])))
    if sobra["vehiculos"]:
        partes.append("%s: %s" % ("un vehículo" if len(sobra["vehiculos"]) == 1 else "%d vehículos" % len(sobra["vehiculos"]), _lista(sobra["vehiculos"])))
    if partes:
        out.append("Tu juego trae cosas que este servidor no conoce. " + ". ".join(p[0].upper() + p[1:] for p in partes) +
                   ". Puedes usarlas en lo tuyo, pero contra otros jugadores esas armas cuentan como ir con las manos, y esos vehículos los verán como un utilitario.")
    return " ".join(out)


# ---------------------------------------------------------------- el personaje, entre versiones
def adaptar_partida(p, cat):
    """El personaje guardado, tal como hay que dárselo a un juego que no conoce todo lo que lleva: sin las armas ni los
    vehículos que ese juego no tiene (uno anterior puede fallar al encontrárselos). No toca el original: lo apartado
    sigue guardado en el servidor y vuelve cuando ese juego guarde."""
    if not cat or not isinstance(p, dict) or not isinstance(p.get("jugador"), dict):
        return p
    j = p["jugador"]
    armas, garajes, veh = j.get("armas"), j.get("garajes"), p.get("veh")
    fuera_armas = isinstance(armas, dict) and any(a not in cat["armas"] for a in armas)
    fuera_garajes = isinstance(garajes, dict) and any(isinstance(f, dict) and f.get("modelo") not in cat["modelos"]
                                                      for fichas in garajes.values() if isinstance(fichas, list) for f in fichas)
    fuera_veh = isinstance(veh, dict) and veh.get("modelo") not in cat["modelos"]
    if not (fuera_armas or fuera_garajes or fuera_veh or (isinstance(j.get("arma"), str) and j["arma"] not in cat["armas"])):
        return p
    p2, j2 = dict(p), dict(j)
    p2["jugador"] = j2
    if isinstance(armas, dict):
        j2["armas"] = {a: d for a, d in armas.items() if a in cat["armas"]}
        if j2.get("arma") not in j2["armas"]:
            j2["arma"] = "punos" if ("punos" in j2["armas"] or not j2["armas"]) else sorted(j2["armas"])[0]
    elif isinstance(j.get("arma"), str) and j["arma"] not in cat["armas"]:
        j2["arma"] = "punos"
    if fuera_garajes:
        j2["garajes"] = {g: ([f for f in fichas if not (isinstance(f, dict) and f.get("modelo") not in cat["modelos"])] if isinstance(fichas, list) else fichas)
                         for g, fichas in garajes.items()}
    if fuera_veh:
        p2.pop("veh", None)
    return p2


def fundir_partida(nueva, vieja, cat):
    """Un juego anterior guarda el personaje que se guardó con uno más nuevo: lo que ese juego no conoce no viene en su
    guardado, y se vuelve a poner de lo que había. Cambia y devuelve ``nueva``.

    - Los campos del jugador y de la raíz que faltan (los de una versión posterior) vuelven como estaban.
    - Las armas y los vehículos de garaje que ese juego no conoce (se le quitaron al dárselo) vuelven también.
    Lo que ese juego sí conoce manda siempre lo que él diga: si falta, es que el jugador ya no lo tiene."""
    if not isinstance(nueva, dict) or not isinstance(vieja, dict):
        return nueva
    for k, v in vieja.items():
        if k not in nueva and k not in VOLATILES:
            nueva[k] = v
    jn, jv = nueva.get("jugador"), vieja.get("jugador")
    if not isinstance(jn, dict) or not isinstance(jv, dict):
        return nueva
    for k, v in jv.items():
        if k not in jn:
            jn[k] = v
    if cat:
        an, av = jn.get("armas"), jv.get("armas")
        if isinstance(an, dict) and isinstance(av, dict):
            for a, d in av.items():
                if a not in an and a not in cat["armas"]:
                    an[a] = d
        gn, gv = jn.get("garajes"), jv.get("garajes")
        if isinstance(gn, dict) and isinstance(gv, dict):
            for g, fichas in gv.items():
                if isinstance(fichas, list) and isinstance(gn.get(g), list):      # si ya no tiene ese garaje, lo que había dentro se fue con él
                    gn[g] = list(gn[g]) + [f for f in fichas if isinstance(f, dict) and f.get("modelo") not in cat["modelos"]]
    return nueva


# ---------------------------------------------------------------- las nóminas de los contratos fijos
def empleos_validos(mundo):
    """Lo que el mundo dice de los contratos fijos, comprobado: {"periodo": días, "prima": tanto por ciento,
    "puestos": {empleo: [[cupo de turnos, sueldo], ...]}}. None si el mundo no lo trae (el de una versión anterior)."""
    e = mundo.get("empleos") if isinstance(mundo, dict) else None
    try:
        periodo = max(1, min(60, int(e["periodo"])))
        prima = max(0, min(100, int(e.get("prima", 0))))
        puestos = {}
        for ident, lista in list(e["puestos"].items())[:100]:
            limpio = [[max(1, min(50, int(c))), max(0, int(s))] for c, s in lista[:20]]
            if limpio and isinstance(ident, str):
                puestos[ident[:40]] = limpio
        return {"periodo": periodo, "prima": prima, "puestos": puestos} if puestos else None
    except (TypeError, KeyError, ValueError, AttributeError):
        return None
