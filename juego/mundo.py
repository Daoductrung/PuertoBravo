"""La ciudad: calles, manzanas, barrios, lugares, rutas y carga de datos.

Coordenadas en metros: x crece hacia el este, y hacia el norte. Las avenidas
van de sur a norte y las calles de oeste a este, separadas B metros.
Los rumbos son grados en sentido horario desde el norte.
"""
import heapq
import json
import math
import os
import random

from . import rutas

B = 90.0          # separación entre vías
CALZADA = 6.0     # media anchura de la calzada
ACERA = 9.0       # distancia del eje de la vía al final de la acera
CARRIL = 3.0
APARCA = 6.7       # distancia del eje a la que se aparca (pegado al bordillo, fuera del carril)
DIRS = [(0, 1), (1, 0), (0, -1), (-1, 0)]       # norte, este, sur, oeste
NOMBRE_DIR = ["norte", "este", "sur", "oeste"]
CARDINAL8 = ["norte", "noreste", "este", "sureste", "sur", "suroeste", "oeste", "noroeste"]
SUPERFICIE_TXT = {"via": "vías del tranvía", "via_tren": "vías del tren", "calzada": "calzada", "acera": "acera", "hierba": "césped", "arena": "arena",
                  "plaza": "plaza", "muelle": "muelle", "pared": "pared", "fuera": "límite de la ciudad"}


def norm180(a):
    return (a + 180.0) % 360.0 - 180.0


def rumbo_a(dx, dy):
    return math.degrees(math.atan2(dx, dy)) % 360.0


def cardinal(grados):
    return CARDINAL8[int(((grados % 360) + 22.5) // 45) % 8]


def dir_de_rumbo(grados):
    return int(((grados % 360) + 45) // 90) % 4


def texto_relativo(rel):
    """Describe un ángulo relativo (-180..180) en palabras."""
    a = abs(rel)
    lado = "derecha" if rel > 0 else "izquierda"
    if a <= 22:
        return "delante"
    if a <= 67:
        return "delante a la " + lado
    if a <= 112:
        return "a la " + lado
    if a <= 157:
        return "detrás a la " + lado
    return "detrás"


def texto_reloj(rel):
    h = int(round((rel % 360) / 30.0)) % 12
    return "a las " + ("12" if h == 0 else str(h))


def metros(d):
    d = int(round(d))
    return "1 metro" if d == 1 else f"{d} metros"


def _leer_json(ruta_archivo):
    """Lee un archivo de datos. En el código fuente es nombre.json; en el juego compilado, nombre.pbd, protegido."""
    from . import cifrado
    if not os.path.exists(ruta_archivo) and ruta_archivo.lower().endswith(".json"):
        protegido = ruta_archivo[:-5] + rutas.EXT_DATOS
        if os.path.exists(protegido):
            ruta_archivo = protegido
    return cifrado.leer_json(ruta_archivo)


def _es_dato(nombre):
    return nombre.lower().endswith((".json", rutas.EXT_DATOS))


def cargar_datos(con_mods=True):
    """Lee datos/*.json y fusiona encima cualquier JSON de la carpeta mods."""
    d = {}
    d["ciudad"] = _leer_json(os.path.join(rutas.DATOS, "ciudad.json"))
    arm = _leer_json(os.path.join(rutas.DATOS, "armas.json"))
    veh = _leer_json(os.path.join(rutas.DATOS, "vehiculos.json"))
    mis = _leer_json(os.path.join(rutas.DATOS, "misiones.json"))
    d["armas"] = arm["armas"]
    d["objetos"] = arm["objetos"]
    d["comidas"] = arm["comidas"]
    d["vehiculos"] = veh["vehiculos"]
    d["carreras"] = veh["carreras"]
    d["misiones"] = mis["misiones"]
    d["capitulos"] = mis["capitulos"]
    d["errores_mods"] = []
    d["ciudad"].setdefault("id", "puerto_bravo")
    d["mapas"] = [d["ciudad"]]
    d["peces"] = arm.get("peces", [])
    try:
        d["personajes"] = _leer_json(os.path.join(rutas.DATOS, "personajes.json")).get("personajes", [])
    except (OSError, ValueError):
        d["personajes"] = []
    try:
        d["adultos"] = _leer_json(os.path.join(rutas.DATOS, "adultos.json"))
    except (OSError, ValueError):
        d["adultos"] = {"personas": [], "actividades": [], "regalos": [], "sustancias": []}
    carpeta_mapas = os.path.join(rutas.DATOS, "mapas")
    if os.path.isdir(carpeta_mapas):
        for nombre in sorted(os.listdir(carpeta_mapas)):
            if _es_dato(nombre):
                try:
                    d["mapas"].append(_leer_json(os.path.join(carpeta_mapas, nombre)))
                except (OSError, ValueError) as e:
                    d["errores_mods"].append(f"{nombre}: {e}")
    for extra in sorted(f for f in os.listdir(rutas.DATOS) if f.startswith("misiones_") and _es_dato(f)):
        ruta_extra = os.path.join(rutas.DATOS, extra)
        if os.path.exists(ruta_extra):
            ex = _leer_json(ruta_extra)
            d["misiones"] += ex.get("misiones", [])
            d["capitulos"].update(ex.get("capitulos", {}))
    if con_mods and os.path.isdir(rutas.MODS):
        from . import cifrado
        for nombre in sorted(os.listdir(rutas.MODS)):
            if not nombre.lower().endswith((".json", rutas.EXT_MOD)):
                continue
            ruta_mod = os.path.join(rutas.MODS, nombre)
            if cifrado.COMPILADO and not cifrado.esta_cifrado(ruta_mod):
                # en el juego que se reparte solo valen los mods guardados con el editor
                d["errores_mods"].append(f"{nombre} está escrito a mano y no se ha cargado. Ábrelo con el editor de mods y guárdalo: el editor lo deja protegido y listo para usar")
                continue
            try:
                mod = _leer_json(ruta_mod)
            except (OSError, ValueError) as e:
                d["errores_mods"].append(f"{nombre}: {e}")
                continue
            for clave in ("armas", "objetos", "vehiculos", "carreras", "misiones", "comidas", "personajes"):
                for nuevo in mod.get(clave, []):
                    lista = d[clave]
                    ident = nuevo.get("id")
                    pos = next((k for k, x in enumerate(lista) if ident and x.get("id") == ident), None)
                    if pos is None:
                        lista.append(nuevo)
                    else:
                        lista[pos] = nuevo
            for clave in ("personas", "actividades", "regalos", "sustancias"):
                for nuevo in mod.get(clave, []):
                    lista = d["adultos"].setdefault(clave, [])
                    pos = next((k for k, x in enumerate(lista) if x.get("id") == nuevo.get("id")), None)
                    if pos is None:
                        lista.append(nuevo)
                    else:
                        lista[pos] = nuevo
            for nuevo in mod.get("peces", []):
                d["peces"].append(nuevo)
            for nuevo in mod.get("mapas", []):
                nuevo.setdefault("lugares", [])
                pos = next((k for k, x in enumerate(d["mapas"]) if x.get("id") == nuevo.get("id")), None)
                if pos is None:
                    d["mapas"].append(nuevo)
                else:
                    d["mapas"][pos] = nuevo
            for nuevo in mod.get("lugares", []):
                destino = next((x for x in d["mapas"] if x.get("id") == nuevo.get("mapa")), d["ciudad"])
                lista = destino["lugares"]
                pos = next((k for k, x in enumerate(lista) if x["id"] == nuevo["id"]), None)
                if pos is None:
                    lista.append(nuevo)
                else:
                    lista[pos] = nuevo
            d["capitulos"].update(mod.get("capitulos", {}))
    return d


class Lugar:
    def __init__(self, d, mundo):
        self.d = d
        self.id = d["id"]
        self.nombre = d["nombre"]
        self.tipo = d["tipo"]
        self.desc = d.get("desc", "")
        self.mapa = mundo.id
        bi, bj = d.get("bloque", (0, 0))
        if "bloque" not in d:
            self.x, self.y = float(d["xy"][0]), float(d["xy"][1])
        elif "xy" in d:
            self.x = bi * B + ACERA + d["xy"][0]
            self.y = bj * B + ACERA + d["xy"][1]
        else:
            pos = d.get("pos", 36)
            lado = d.get("lado", "S")
            if lado == "S":
                self.x, self.y = bi * B + ACERA + pos, bj * B + 7.5
            elif lado == "N":
                self.x, self.y = bi * B + ACERA + pos, (bj + 1) * B - 7.5
            elif lado == "O":
                self.x, self.y = bi * B + 7.5, bj * B + ACERA + pos
            else:
                self.x, self.y = (bi + 1) * B - 7.5, bj * B + ACERA + pos
        self.sonido = d.get("sonido") or {
            "casa": "lugar_casa", "bar": "lugar_bar", "tienda": "lugar_tienda", "farmacia": "lugar_hospital",
            "comisaria": "lugar_comisaria", "hospital": "lugar_hospital", "armeria": "lugar_armeria",
            "periodico": "lugar_periodico", "pizzeria": "lugar_comida", "comida": "lugar_comida",
            "taxi": "lugar_taxi", "casino": "lugar_casino", "taller": "lugar_taller",
            "desguace": "lugar_taller", "negocio": "lugar_bar", "carrera": "lugar_taxi",
            "banco": "lugar_banco", "gimnasio": "lugar_gimnasio", "ropa": "lugar_tienda", "cine": "lugar_cine",
            "hotel": "lugar_casa", "concesionario": "lugar_taller", "nautica": "lugar_embarcadero",
            "estacion": "lugar_estacion", "embarcadero": "lugar_embarcadero", "muelle": "lugar_boya",
            "salida": "lugar_salida", "loteria": "lugar_tienda", "empenos": "lugar_banco", "pescaderia": "lugar_comida",
            "taberna": "lugar_bar", "pesca": "lugar_boya", "helipuerto": "lugar_helipuerto",
            "protectora": "lugar_protectora", "feria": "lugar_casino", "tesoro": "lugar_boya", "club": "lugar_club", "proveedor": "lugar_proveedor",
            "empleo": "lugar_empleo", "academia": "lugar_academia", "ong": "lugar_ong",
            "tranvia": "lugar_tranvia", "tren": "lugar_tren", "aeropuerto": "lugar_aeropuerto",
        }.get(self.tipo, "lugar_generico")

    def get(self, k, defecto=None):
        return self.d.get(k, defecto)


def _hueco(lugares, bloque, lado, pos):
    """Una posición de fachada libre en esa manzana: si la pedida está ocupada, se prueba con otras."""
    ocupadas = [int(l.get("pos", 36)) for l in lugares if tuple(l.get("bloque", (-1, -1))) == tuple(bloque) and l.get("lado", "S") == lado and "xy" not in l]
    for p in (pos, 62, 18, 76, 48, 30, 8):
        if all(abs(p - o) >= 13 for o in ocupadas):
            return p
    return pos


def completar_transporte(c):
    """Añade a una localidad el transporte público que le corresponde, si el mapa no trae el suyo:

    - en las ciudades, paradas de tranvía repartidas por todos los barrios, para moverse dentro de la ciudad;
    - en las localidades a las que se llega por carretera, una estación de tren, para ir a otras localidades;
    - en las ciudades, un aeropuerto en las afueras, para los trayectos largos;
    - en los pueblos a los que se llega por carretera, un aeródromo: una pista corta a la que llegan avionetas.

    Un mod puede poner sus propias paradas, su estación o su aeropuerto con esos tipos de lugar: entonces no se añade nada
    de ese tipo. Y puede quitarlo todo con "transporte": false en el mapa.
    """
    if c.get("tipo") == "mar" or c.get("transporte") is False or "avenidas" not in c:
        return
    lugares = c.setdefault("lugares", [])
    tipos = {l.get("tipo") for l in lugares}
    mid = c.get("id", "puerto_bravo")
    nx, ny = len(c["avenidas"]) - 1, len(c["calles"]) - 1            # manzanas a lo ancho y a lo alto
    ciudad = c.get("tipo", "ciudad") == "ciudad"
    por_tierra = "salida" in tipos
    if ciudad and "tranvia" not in tipos:
        n = 0
        for b in c.get("barrios", []):
            i0, i1, j0, j1 = b["i"][0], min(b["i"][1], nx - 1), b["j"][0], min(b["j"][1], ny - 1)
            esquinas = [((i0, j0), "S")] + ([((i1, j1), "N")] if (i1, j1) != (i0, j0) else [])
            for (bi, bj), lado in esquinas:
                n += 1
                calle = c["calles"][bj if lado == "S" else bj + 1]
                lugares.append({"id": f"{mid}_tranvia_{n}", "nombre": f"Parada de tranvía de {calle}, en {b['nombre']}", "tipo": "tranvia", "bloque": [bi, bj], "lado": lado,
                                "pos": _hueco(lugares, (bi, bj), lado, 62),
                                "desc": f"Una marquesina con un banco y el cartel de la línea. El tranvía recorre {c['nombre']} parando en todos los barrios."})
        # el orden de la línea: dando la vuelta a la ciudad. Queda escrito en cada parada, para poder cambiarlo a mano
        nuevas = [l for l in lugares if l.get("tipo") == "tranvia"]
        pos = {l["id"]: (l["bloque"][0] * B + ACERA + l["pos"], l["bloque"][1] * B + (7.5 if l["lado"] == "S" else B - 7.5)) for l in nuevas}
        cx = sum(x for x, _ in pos.values()) / len(pos)
        cy = sum(y for _, y in pos.values()) / len(pos)
        for k, l in enumerate(sorted(nuevas, key=lambda l: (math.atan2(pos[l["id"]][1] - cy, pos[l["id"]][0] - cx), l["id"])), 1):
            l["orden"] = k
    if por_tierra and "tren" not in tipos:
        bus = next((l for l in lugares if l.get("tipo") == "estacion" and "bloque" in l), None)
        bloque = tuple(bus["bloque"]) if bus else (0, 0)
        lado = {"S": "N", "N": "S", "E": "O", "O": "E"}.get(bus.get("lado", "S"), "N") if bus else "S"
        lugares.append({"id": f"{mid}_tren", "nombre": f"Estación de tren de {c['nombre']}", "tipo": "tren", "bloque": list(bloque), "lado": lado,
                        "pos": _hueco(lugares, bloque, lado, 45),
                        "desc": "Un andén, una taquilla y el panel de salidas. De aquí salen los trenes a las demás localidades a las que se llega por tierra."})
    if ciudad and "aeropuerto" not in tipos:
        esquinas = [(0, 0), (nx - 1, 0), (0, ny - 1), (nx - 1, ny - 1)]
        bloque = min(esquinas, key=lambda e: sum(1 for l in lugares if tuple(l.get("bloque", (-1, -1))) == e))      # la esquina más despejada de las afueras
        lado = "S" if bloque[1] == 0 else "N"
        lugares.append({"id": f"{mid}_aeropuerto", "nombre": f"Aeropuerto de {c['nombre']}", "tipo": "aeropuerto", "bloque": list(bloque), "lado": lado,
                        "pos": _hueco(lugares, bloque, lado, 45), "precio": 180,
                        "desc": "En las afueras: una terminal pequeña, una pista y un hangar. Salen aviones de pasajeros a las otras ciudades, y se alquilan avionetas y helicópteros."})
    if not ciudad and por_tierra and "aeropuerto" not in tipos:
        esquinas = [(0, 0), (nx - 1, 0), (0, ny - 1), (nx - 1, ny - 1)]
        bloque = min(esquinas, key=lambda e: sum(1 for l in lugares if tuple(l.get("bloque", (-1, -1))) == e))
        lado = "S" if bloque[1] == 0 else "N"
        lugares.append({"id": f"{mid}_aerodromo", "nombre": f"Aeródromo de {c['nombre']}", "tipo": "aeropuerto", "aerodromo": True, "bloque": list(bloque), "lado": lado,
                        "pos": _hueco(lugares, bloque, lado, 45), "precio": 120,
                        "desc": "A las afueras: una pista corta de tierra, una manga de viento y una caseta. Llegan y salen avionetas de línea, y se alquilan avionetas."})


def crear_mapas(datos):
    """Construye todos los mapas del juego: {id: Mundo}."""
    mapas = {}
    for c in datos["mapas"]:
        try:
            m = Mar(c) if c.get("tipo") == "mar" else Mundo(c)
            mapas[m.id] = m
        except (KeyError, ValueError, TypeError, IndexError) as e:
            datos["errores_mods"].append(f"mapa {c.get('id', '?')}: {e}")
    return mapas


class Mundo:
    def __init__(self, c):
        if "ciudad" in c and "avenidas" not in c:
            c = c["ciudad"]
        self.id = c.get("id", "puerto_bravo")
        self.tipo = c.get("tipo", "ciudad")
        self.trafico = int(c.get("trafico", 7))
        self.peatones = int(c.get("peatones", 7))
        self.policia = bool(c.get("policia", True))
        self.nombre_objeto = c.get("nombre_objeto", "Cinta de casete")
        self.nombre = c["nombre"]
        self.avenidas = c["avenidas"]
        self.calles = c["calles"]
        self.NX = len(self.avenidas)
        self.NY = len(self.calles)
        self.ancho = (self.NX - 1) * B
        self.alto = (self.NY - 1) * B
        self.barrios = c["barrios"]
        for b in self.barrios:                     # una isla sin coches puede venir sin la lista
            b.setdefault("vehiculos", [])
        self.bloques = {}
        for k, v in c.get("bloques", {}).items():
            i, j = k.split(",")
            self.bloques[(int(i), int(j))] = v
        self._barrio_de = {}
        for b in self.barrios:
            for i in range(b["i"][0], b["i"][1] + 1):
                for j in range(b["j"][0], b["j"][1] + 1):
                    self._barrio_de[(i, j)] = b
        completar_transporte(c)
        self._vias_datos = c.get("vias")
        self.lugares = {}
        for d in c["lugares"]:
            try:
                l = Lugar(d, self)
                self.lugares[l.id] = l
            except (KeyError, ValueError, TypeError):
                pass
        self.lugares_todos = dict(self.lugares)
        self._tender_vias()
        self._tender_tren(c)
        self.casetes = [self.punto_libre(x, y) for x, y in c.get("casetes", [])]
        self.aparcados = self._generar_aparcados() if c.get("aparcados", True) else []

    # ------------------------------------------------------------------ vías del tranvía
    def linea_tranvia(self):
        """Las paradas de tranvía, en el orden en que las recorre la línea: dando la vuelta a la ciudad."""
        paradas = [l for l in self.lugares_todos.values() if l.tipo == "tranvia"]
        if not paradas:
            return []
        if all(isinstance(l.get("orden"), (int, float)) for l in paradas):
            return sorted(paradas, key=lambda l: (l.get("orden"), l.id))        # el orden que diga cada parada
        cx = sum(l.x for l in paradas) / len(paradas)
        cy = sum(l.y for l in paradas) / len(paradas)
        return sorted(paradas, key=lambda l: (math.atan2(l.y - cy, l.x - cx), l.id))

    def _tender_vias(self):
        """Tiende las vías: un circuito que pasa por el cruce más cercano a cada parada, siguiendo calles y avenidas.

        Las vías van por el centro de la calzada. `vias` guarda cada tramo de calle que las lleva, para saber si un punto
        está sobre ellas; `via_ruta` es el circuito, punto a punto, y `via_marcas` a cuántos metros del principio para en
        cada parada.
        """
        self.vias = set()             # ("H", calle, avenida): tramo de esa calle desde esa avenida a la siguiente; ("V", avenida, calle)
        self.via_ruta, self.via_cum, self.via_marcas, self._via_de_parada = [], [], [], {}
        self.via_nodos = []           # los cruces del circuito, uno a uno
        self.via_largo = 0.0
        linea = self.linea_tranvia()
        if len(linea) < 2:
            return
        escritas = []
        for n in self._vias_datos or []:                         # el recorrido escrito en el mapa: los cruces por los que pasa
            try:
                i, j = (n["a"], n["b"]) if isinstance(n, dict) else (n[0], n[1])
                escritas.append((max(0, min(self.NX - 1, int(i))), max(0, min(self.NY - 1, int(j)))))
            except (KeyError, IndexError, TypeError, ValueError):
                continue
        # Si el mapa no trae el recorrido, se tiende por el cruce más cercano a cada parada, en el orden de la línea.
        nodos = escritas if len(escritas) >= 2 else [(max(0, min(self.NX - 1, int(round(l.x / B)))), max(0, min(self.NY - 1, int(round(l.y / B))))) for l in linea]
        ruta = [nodos[0]]
        for k in range(1, len(nodos) + 1):
            (ia, ja), (ib, jb) = ruta[-1], nodos[k % len(nodos)]
            paso = 1 if ib > ia else -1
            for i in range(ia + paso, ib + paso, paso) if ib != ia else []:      # primero por la calle
                ruta.append((i, ja))
            paso = 1 if jb > ja else -1
            for j in range(ja + paso, jb + paso, paso) if jb != ja else []:      # luego por la avenida
                ruta.append((ib, j))
        if ruta[-1] == ruta[0] and len(ruta) > 1:
            ruta.pop()                                           # el circuito se cierra solo: el último punto es el primero
        # cada parada para en el punto del circuito que le queda más cerca
        indice = {l.id: min(range(len(ruta)), key=lambda n: math.hypot(ruta[n][0] * B - l.x, ruta[n][1] * B - l.y)) for l in linea}
        self.via_nodos = list(ruta)
        for n in range(len(ruta)):
            (ia, ja), (ib, jb) = ruta[n], ruta[(n + 1) % len(ruta)]
            if ja == jb and ia != ib:
                self.vias.add(("H", ja, min(ia, ib)))
            elif ia == ib and ja != jb:
                self.vias.add(("V", ia, min(ja, jb)))
        self.via_ruta = [(i * B, j * B) for i, j in ruta]
        cum = [0.0]
        for n in range(len(self.via_ruta)):
            a, b = self.via_ruta[n], self.via_ruta[(n + 1) % len(self.via_ruta)]
            cum.append(cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
        self.via_cum = cum
        self.via_largo = cum[-1]
        for l in linea:
            self._via_de_parada[l.id] = cum[min(indice.get(l.id, 0), len(self.via_ruta) - 1)]
        self.via_marcas = sorted(set(self._via_de_parada.values()))

    # ------------------------------------------------------------------ vía del tren
    def _tender_tren(self, c):
        """La vía del tren cruza la localidad de lado a lado, en línea recta, por la calle o la avenida de la estación.

        El mapa puede decir por dónde va con `tren_eje` ("H", por una calle, de oeste a este; "V", por una avenida, de sur
        a norte) y `tren_n` (el número de esa calle o avenida, empezando en cero). Si no lo dice, va por la que pasa por
        delante de la estación. Sin estación de tren no hay vía.
        """
        self.tren_eje, self.tren_n, self.tren_largo, self.tren_parada = None, 0, 0.0, 0.0
        est = next((l for l in self.lugares_todos.values() if l.tipo == "tren"), None)
        if est is None:
            return
        eje, n = c.get("tren_eje"), c.get("tren_n")
        if eje not in ("H", "V") or not isinstance(n, int) or isinstance(n, bool) or not (0 <= n < (self.NY if eje == "H" else self.NX)):
            j, i = self._idx(est.y, self.NY), self._idx(est.x, self.NX)
            eje, n = ("H", j) if abs(est.y - j * B) <= abs(est.x - i * B) else ("V", i)      # la que pasa por delante de la estación
        self.tren_eje, self.tren_n = eje, n
        self.tren_largo = float(self.ancho if eje == "H" else self.alto)
        self.tren_parada = max(0.0, min(self.tren_largo, est.x if eje == "H" else est.y))

    def tren_punto(self, s):
        """El punto de la vía del tren que está a s metros de su principio (el oeste o el sur). Vale fuera del mapa: el tren viene de lejos."""
        return (s, self.tren_n * B) if self.tren_eje == "H" else (self.tren_n * B, s)

    def en_via_tren(self, x, y):
        """¿Está el punto sobre la vía del tren? Como la del tranvía, va por el centro de la calzada."""
        if self.tren_eje == "H":
            return abs(y - self.tren_n * B) <= 1.6 and -1.0 <= x <= self.ancho + 1.0
        if self.tren_eje == "V":
            return abs(x - self.tren_n * B) <= 1.6 and -1.0 <= y <= self.alto + 1.0
        return False

    def tren_donde(self):
        """Por dónde va la vía del tren, dicho con palabras."""
        if self.tren_eje is None:
            return ""
        return f"{self.calles[self.tren_n]}, de oeste a este" if self.tren_eje == "H" else f"{self.avenidas[self.tren_n]}, de sur a norte"

    def sobre_vias(self, x, y):
        """Qué vías pisa ese punto: "via" (tranvía), "via_tren" o None."""
        if self.en_via(x, y):
            return "via"
        return "via_tren" if self.en_via_tren(x, y) else None

    def esquinas_de_las_vias(self):
        """El circuito resumido en los cruces donde gira: es lo que se guarda en el mapa y lo que se edita."""
        n = len(self.via_nodos)
        if n < 3:
            return [list(x) for x in self.via_nodos]
        out = []
        for k in range(n):
            a, b, c = self.via_nodos[k - 1], self.via_nodos[k], self.via_nodos[(k + 1) % n]
            if (b[0] - a[0], b[1] - a[1]) != (c[0] - b[0], c[1] - b[1]):       # cambia de dirección, o da la vuelta
                out.append([b[0], b[1]])
        return out

    def via_marca(self, parada):
        """A cuántos metros del principio del circuito para el tranvía en esa parada. None si no es de la línea."""
        return self._via_de_parada.get(getattr(parada, "id", parada))

    def via_punto(self, s):
        """El punto del circuito que está a s metros de su principio."""
        if not self.via_ruta:
            return (0.0, 0.0)
        s %= self.via_largo
        n = len(self.via_ruta)
        for k in range(n):
            if s <= self.via_cum[k + 1]:
                a, b = self.via_ruta[k], self.via_ruta[(k + 1) % n]
                tramo = self.via_cum[k + 1] - self.via_cum[k]
                f = (s - self.via_cum[k]) / tramo if tramo > 0 else 0.0
                return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
        return self.via_ruta[0]

    def en_via(self, x, y):
        """¿Está el punto sobre las vías del tranvía? Van por el centro de la calzada, un metro y medio a cada lado del eje."""
        if not self.vias:
            return False
        j = int(round(y / B))
        if abs(y - j * B) <= 1.6 and (("H", j, int(math.floor((x - 1.6) / B))) in self.vias or ("H", j, int(math.floor((x + 1.6) / B))) in self.vias):
            return True                                          # en un cruce cuentan los dos tramos que llegan a él
        i = int(round(x / B))
        return abs(x - i * B) <= 1.6 and (("V", i, int(math.floor((y - 1.6) / B))) in self.vias or ("V", i, int(math.floor((y + 1.6) / B))) in self.vias)

    def fuera_de_la_via(self, x, y):
        """El punto de la acera más cercano a un punto de la vía: adonde va a parar quien es apartado de ella."""
        j, i = int(round(y / B)), int(round(x / B))
        if abs(y - j * B) <= abs(x - i * B):
            return (x, j * B + (ACERA - 1.0) * (1 if y >= j * B else -1))
        return (i * B + (ACERA - 1.0) * (1 if x >= i * B else -1), y)

    def filtrar(self, adultos):
        """Oculta o muestra los lugares marcados como contenido para adultos."""
        self.lugares = {k: l for k, l in self.lugares_todos.items() if adultos or not l.get("adultos")}

    # --------------------------------------------------------------- geometría
    def _idx(self, v, n):
        return max(0, min(n - 1, int(round(v / B))))

    def bloque(self, x, y):
        return (max(0, min(self.NX - 2, int(x // B))), max(0, min(self.NY - 2, int(y // B))))

    def superficie(self, x, y):
        if x < -ACERA or y < -ACERA or x > self.ancho + ACERA or y > self.alto + ACERA:
            return "fuera"
        dx = abs(x - self._idx(x, self.NX) * B)
        dy = abs(y - self._idx(y, self.NY) * B)
        if dx <= CALZADA or dy <= CALZADA:
            return "calzada"
        if dx <= ACERA or dy <= ACERA:
            return "acera"
        return self.bloques.get(self.bloque(x, y), "pared")

    def transitable(self, x, y):
        return self.superficie(x, y) not in ("pared", "fuera")

    def punto_libre(self, x, y):
        """Devuelve el punto transitable más cercano a (x, y)."""
        if self.transitable(x, y):
            return (float(x), float(y))
        (px, py), _ = self.ancla(x, y)
        return (px + 7.5 if px + 7.5 <= self.ancho + 8 else px - 7.5, py + 7.5 if py + 7.5 <= self.alto + 8 else py - 7.5)

    def cruce(self, x, y, margen=ACERA):
        i = self._idx(x, self.NX)
        j = self._idx(y, self.NY)
        if abs(x - i * B) <= margen and abs(y - j * B) <= margen:
            return (i, j)
        return None

    def via_cercana(self, x, y):
        """('H', j, dist) o ('V', i, dist): la vía cuyo eje está más cerca."""
        i = self._idx(x, self.NX)
        j = self._idx(y, self.NY)
        dv = abs(x - i * B)
        dh = abs(y - j * B)
        if dh <= dv:
            return ("H", j, dh)
        return ("V", i, dv)

    def nombre_via(self, tipo, idx):
        return self.calles[idx] if tipo == "H" else self.avenidas[idx]

    def nombre_tramo(self, p, q):
        if abs(p[1] - q[1]) < abs(p[0] - q[0]):
            return self.calles[self._idx((p[1] + q[1]) / 2, self.NY)]
        return self.avenidas[self._idx((p[0] + q[0]) / 2, self.NX)]

    def barrio(self, x, y):
        return self._barrio_de.get(self.bloque(x, y), self.barrios[0])

    def describir(self, x, y):
        c = self.cruce(x, y)
        if c:
            return f"Cruce de {self.calles[c[1]]} con {self.avenidas[c[0]]}"
        i = self._idx(x, self.NX)
        j = self._idx(y, self.NY)
        dx = abs(x - i * B)
        dy = abs(y - j * B)
        bi, bj = self.bloque(x, y)
        if dy <= ACERA and dy <= dx:
            lado = "" if dy <= CALZADA else (", acera norte" if y > j * B else ", acera sur")
            return f"{self.calles[j]}{lado}, entre {self.avenidas[bi]} y {self.avenidas[bi + 1]}"
        if dx <= ACERA:
            lado = "" if dx <= CALZADA else (", acera este" if x > i * B else ", acera oeste")
            return f"{self.avenidas[i]}{lado}, entre {self.calles[bj]} y {self.calles[bj + 1]}"
        tipo = self.bloques.get((bi, bj), "pared")
        que = {"hierba": "Zona verde", "arena": "Playa", "plaza": "Plaza", "muelle": "Muelle"}.get(tipo, "Interior de manzana")
        t, idx, _ = self.via_cercana(x, y)
        return f"{que}, junto a {self.nombre_via(t, idx)}"

    # -------------------------------------------------------------------- rutas
    def ancla(self, x, y):
        """Punto más cercano sobre el eje de una vía y los cruces de sus extremos."""
        x = max(0.0, min(self.ancho, x))
        y = max(0.0, min(self.alto, y))
        t, idx, _ = self.via_cercana(x, y)
        if t == "H":
            i0 = min(int(x // B), self.NX - 2)
            return (x, idx * B), [(i0, idx), (i0 + 1, idx)]
        j0 = min(int(y // B), self.NY - 2)
        return (idx * B, y), [(idx, j0), (idx, j0 + 1)]

    def ruta(self, x0, y0, x1, y1):
        """Lista de puntos que llevan por las calles de (x0, y0) a (x1, y1)."""
        a, ea = self.ancla(x0, y0)
        b, eb = self.ancla(x1, y1)
        fin = [b, (x1, y1)] if math.hypot(b[0] - x1, b[1] - y1) > 1.0 else [b]
        ini = [a] if math.hypot(a[0] - x0, a[1] - y0) > 12.0 else []
        if set(ea) == set(eb) or math.hypot(a[0] - b[0], a[1] - b[1]) < 1.0:
            return self._limpiar(ini + fin, x0, y0)
        dist = {}
        prev = {}
        cola = []
        for n in ea:
            d = math.hypot(n[0] * B - a[0], n[1] * B - a[1])
            if d < dist.get(n, 1e18):
                dist[n] = d
                prev[n] = None
                heapq.heappush(cola, (d, n))
        metas = {n: math.hypot(n[0] * B - b[0], n[1] * B - b[1]) for n in eb}
        mejor = (1e18, None)
        hechos = set()
        while cola:
            d, n = heapq.heappop(cola)
            if n in hechos:
                continue
            hechos.add(n)
            if n in metas and d + metas[n] < mejor[0]:
                mejor = (d + metas[n], n)
            if d > mejor[0]:
                break
            for dx, dy in DIRS:
                m = (n[0] + dx, n[1] + dy)
                if 0 <= m[0] < self.NX and 0 <= m[1] < self.NY:
                    nd = d + B
                    if nd < dist.get(m, 1e18):
                        dist[m] = nd
                        prev[m] = n
                        heapq.heappush(cola, (nd, m))
        nodos = []
        n = mejor[1]
        while n is not None:
            nodos.append((n[0] * B, n[1] * B))
            n = prev[n]
        nodos.reverse()
        return self._limpiar(ini + nodos + fin, x0, y0)

    @staticmethod
    def _limpiar(pts, x0, y0):
        out = []
        ant = (x0, y0)
        for p in pts:
            if math.hypot(p[0] - ant[0], p[1] - ant[1]) > 2.0 or p is pts[-1]:
                out.append((float(p[0]), float(p[1])))
                ant = p
        # quita puntos intermedios alineados para que «sigue recto» sea un solo tramo
        k = 1
        while k < len(out) - 1:
            a, b, c = out[k - 1], out[k], out[k + 1]
            if (abs(a[0] - b[0]) < 0.5 and abs(b[0] - c[0]) < 0.5 and (b[1] - a[1]) * (c[1] - b[1]) > 0) or \
               (abs(a[1] - b[1]) < 0.5 and abs(b[1] - c[1]) < 0.5 and (b[0] - a[0]) * (c[0] - b[0]) > 0):
                del out[k]
            else:
                k += 1
        return out

    def dir_valida(self, i, j, d):
        ni, nj = i + DIRS[d][0], j + DIRS[d][1]
        return 0 <= ni < self.NX and 0 <= nj < self.NY

    def carril(self, tipo, idx, d, lat=0.0):
        """Coordenada perpendicular del centro del carril para el sentido d."""
        if tipo == "V":
            return idx * B + (CARRIL + lat) * (1 if d == 0 else -1)
        return idx * B + (CARRIL + lat) * (-1 if d == 1 else 1)

    def verde_vertical(self, i, j, t):
        """True si el semáforo del cruce deja pasar el tráfico norte-sur."""
        return (int(t // 14) + i + j) % 2 == 0

    # --------------------------------------------------------------- aparcados
    def _generar_aparcados(self):
        rng = random.Random(1234)
        plazas = []
        n = 0
        for j in range(self.NY):
            for i in range(self.NX - 1):
                for _ in range(rng.choice([0, 1, 1, 2])):
                    d = rng.choice([1, 3])
                    x = i * B + rng.uniform(18, 72)
                    y = j * B + (-APARCA if d == 1 else APARCA)
                    plazas.append({"id": n, "x": x, "y": y, "dir": d, "azar": rng.random()})
                    n += 1
        for i in range(self.NX):
            for j in range(self.NY - 1):
                for _ in range(rng.choice([0, 1, 1, 2])):
                    d = rng.choice([0, 2])
                    y = j * B + rng.uniform(18, 72)
                    x = i * B + (APARCA if d == 0 else -APARCA)
                    plazas.append({"id": n, "x": x, "y": y, "dir": d, "azar": rng.random()})
                    n += 1
        return plazas

    def plaza_junto_a(self, lugar):
        """Posición y sentido para dejar un vehículo en la calzada frente a un lugar."""
        return self.plaza_en(lugar.x, lugar.y)

    def plaza_en(self, x, y):
        """Hueco de aparcamiento junto al bordillo más cercano al punto (x, y)."""
        class _P:
            pass
        lugar = _P()
        lugar.x, lugar.y = x, y
        (ax, ay), _ = self.ancla(lugar.x, lugar.y)
        t, idx, _ = self.via_cercana(ax, ay)
        if t == "H":
            d = 3 if lugar.y > ay else 1
            return ax, ay + (APARCA if d == 3 else -APARCA), d
        d = 0 if lugar.x > ax else 2
        return ax + (APARCA if d == 0 else -APARCA), ay, d


class Mar(Mundo):
    """Mapa de mar abierto: todo es agua navegable salvo las islas."""

    def __init__(self, c):
        self.id = c["id"]
        self.tipo = "mar"
        self.trafico = int(c.get("trafico", 4))
        self.peatones = 0
        self.policia = False
        self.nombre_objeto = c.get("nombre_objeto", "Botella con mensaje")
        self.nombre = c["nombre"]
        self.avenidas = ["mar"]
        self.calles = ["mar"]
        self.NX = self.NY = 1
        self.ancho = float(c["ancho"])
        self.alto = float(c["alto"])
        self.islas = c.get("islas", [])
        self.barrios = [{"id": self.id, "nombre": self.nombre, "ambiente": "amb_mar", "vehiculos": c.get("barcos", ["lancha"]),
                         "descripcion": c.get("descripcion", "Mar abierto.")}]
        self.bloques = {}
        self.lugares = {}
        for d in c["lugares"]:
            l = Lugar(d, self)
            self.lugares[l.id] = l
        self.lugares_todos = dict(self.lugares)
        self.casetes = [(float(x), float(y)) for x, y in c.get("casetes", [])]
        self.aparcados = []

    def superficie(self, x, y):
        if x < 0 or y < 0 or x > self.ancho or y > self.alto:
            return "fuera"
        for i in self.islas:
            if math.hypot(x - i["x"], y - i["y"]) <= i["r"]:
                return "arena"
        return "agua"

    def transitable(self, x, y):
        return self.superficie(x, y) == "agua"

    def punto_libre(self, x, y):
        x = max(5.0, min(self.ancho - 5, x))
        y = max(5.0, min(self.alto - 5, y))
        for i in self.islas:
            d = math.hypot(x - i["x"], y - i["y"])
            if d <= i["r"] + 3:
                f = (i["r"] + 6) / max(d, 0.1)
                x, y = i["x"] + (x - i["x"]) * f, i["y"] + (y - i["y"]) * f
        return (x, y)

    def cruce(self, x, y, margen=ACERA):
        return None

    def via_cercana(self, x, y):
        return ("H", 0, 1e9)

    def barrio(self, x, y):
        return self.barrios[0]

    def bloque(self, x, y):
        return (0, 0)

    def describir(self, x, y):
        if not self.lugares:
            return self.nombre
        l = min(self.lugares.values(), key=lambda l: math.hypot(l.x - x, l.y - y))
        d = math.hypot(l.x - x, l.y - y)
        if d < 25:
            return f"{self.nombre}, junto a {l.nombre}"
        return f"{self.nombre}, a {metros(d)} al {cardinal(rumbo_a(x - l.x, y - l.y))} de {l.nombre}"

    def ancla(self, x, y):
        return (x, y), []

    def ruta(self, x0, y0, x1, y1):
        return [(float(x1), float(y1))]

    def nombre_tramo(self, p, q):
        return self.nombre

    def plaza_en(self, x, y):
        return x, y, 0

    def plaza_junto_a(self, lugar):
        dx, dy = self.ancho / 2 - lugar.x, self.alto / 2 - lugar.y
        d = math.hypot(dx, dy) or 1.0
        x, y = self.punto_libre(lugar.x + dx / d * 12, lugar.y + dy / d * 12)
        return x, y, dir_de_rumbo(rumbo_a(dx, dy))
