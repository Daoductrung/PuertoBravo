"""Golpes preparados: cada uno de tu banda con su papel (1.7.1).

Un atraco de los de siempre (un banco, un local con caja, un proveedor) se puede preparar antes si tienes a gente de tu
banda al lado: uno espera fuera con el motor en marcha, otro vigila y avisa de la policía, otro entra contigo y tiene a
raya a la gente, otro abre la caja y otro dispara desde el coche en la huida. Tú eliges también lo tuyo: abrir la caja
o cubrir a quien la abre, y conducir o ir de pasajero.

Preparado, el golpe tiene cinco fases que se dicen en voz alta (entrada, control, caja, salida y huida), la caja tarda
en abrirse y tu gente habla por la radio. Cada uno rinde según lo que vale (puntería, conducción, nervios y lealtad,
que se guardan con la partida), puede fallar y se lleva su parte del botín.

Nada de esto es obligatorio: sin banda, o sin prepararlo, el atraco es el de siempre.

Los papeles, los números y las frases están en los datos (vida.json, secciones «golpes» y «papeles_golpe»).
"""
import math
import random

from . import gente as G
from .ajustes import Ajustes
from .entidades import Persona

AJ = Ajustes("golpes", {
    "radio_presentes": 80, "radio_vehiculo": 200,
    "atributo_min": 30, "atributo_max": 85, "exp_bono": 3, "exp_max": 5,
    "caja_min": 8, "caja_max": 16, "caja_radio": 5, "cubrir_radio": 25, "caja_ayuda": 50, "caja_nervios": 40,
    "vigilante_retraso": 22, "vigilante_aviso": 8,
    "conductor_ventaja": 12, "conductor_nivel": 70,
    "tirador_cada": 2.6, "tirador_alcance": 48, "tirador_dano": 20,
    "heroe_prob": 30, "heroe_escolta": 85, "alarma_prob": 30, "alarma_escolta": 80,
    "fallo_base": 30, "herido_prob": 18, "herido_dias_min": 2, "herido_dias_max": 5, "detenido_prob": 25,
    "delata_lealtad": 40, "delata_busqueda": 1, "tarde_min": 10, "tarde_max": 25,
    "reparto_tope": 60, "lealtad_exito": 3, "lealtad_fracaso": 6,
}, {
    "tiempos_caja": ["banco=26", "proveedor=14", "casino=20", "empenos=14", "armeria=14", "concesionario=16", "hotel=14"],
    "frases_entrada": ["Fase uno, entrada. Cada uno a su sitio.", "Fase uno, entrada. Relojes en hora: empezamos."],
    "frases_control": ["Fase dos, control. Que nadie se mueva hasta que no quede guardia en pie.", "Fase dos, control. Primero, los que van armados."],
    "frases_control_sin_guardia": ["Fase dos, control. Aquí no hay guardia: todo el mundo al suelo y nadie se hace el valiente.",
                                   "Fase dos, control. Sin guardia a la vista: la gente, quieta y callada."],
    "frases_caja": ["Fase tres, la caja.", "Fase tres: a por la caja."],
    "frases_salida": ["Fase cuatro, salida. Fuera de aquí con lo que llevas.", "Fase cuatro, salida. Ya lo tienes: a la calle."],
    "frases_huida": ["Fase cinco, huida. Despista a la policía y el botín es vuestro.", "Fase cinco, huida. Ahora toca desaparecer."],
    "radio_conductor_listo": ["En la puerta, con el motor en marcha.", "Aparcado delante y sin apagar el motor. Cuando salgáis, arranco."],
    "radio_conductor_tarde": ["Voy con retraso, hay un atasco. Aguantad un poco.", "Me he tenido que dar una vuelta: había una patrulla. Llego enseguida."],
    "radio_conductor_llega": ["Ya estoy en la puerta. ¡Vamos, vamos!", "Aquí estoy. Subid ya."],
    "radio_conductor_ventaja": ["Agárrate: me sé un callejón por el que no nos sigue nadie.", "Salgo por detrás del mercado. Ahí nos pierden."],
    "radio_conductor_sin_ventaja": ["Se me ha calado. Ya está, ya arranca. Hemos perdido la ventaja.", "Me tiemblan las manos. Salimos, pero nos han visto salir."],
    "radio_conductor_tu": ["El motor está en marcha. Conduces tú: yo voy mirando atrás.", "Todo tuyo, ya está arrancado. Yo te canto por dónde vienen."],
    "radio_vigilante_listo": ["En mi sitio. Desde aquí veo las dos esquinas.", "Colocado. Si viene alguien, os enteráis antes que ellos."],
    "radio_vigilante_alarma": ["Ha saltado la alarma. Calculo {segundos} segundos hasta que lleguen.", "Los han avisado. Tenéis unos {segundos} segundos, ni uno más."],
    "radio_vigilante_cerca": ["¡Ya se oyen las sirenas! Os quedan {segundos} segundos.", "Vienen por la avenida. {segundos} segundos y los tenéis encima."],
    "radio_vigilante_llegan": ["¡Ya están aquí! Me quito de en medio.", "¡Policía en la puerta! Salid como podáis."],
    "radio_vigilante_falla": ["No... no he visto venir nada. ¡Los tenéis encima!", "Se me ha pasado. ¡Están ahí mismo!"],
    "frases_vigilante_detenido": ["A {nombre} lo han cogido en la esquina: se lo llevan esposado.", "{nombre} no ha corrido lo bastante: la policía lo tiene."],
    "frases_delata": ["{nombre} no ha aguantado ni el primer interrogatorio: ha dado tu nombre.", "{nombre} ha cantado para salvarse. La policía sabe quién ha sido."],
    "frases_no_delata": ["{nombre} no ha dicho ni una palabra. De esos quedan pocos.", "{nombre} se come el marrón sin dar un solo nombre."],
    "radio_escolta_control": ["Yo me ocupo de la gente. Tú a lo tuyo.", "Los tengo a todos contra la pared. Nadie se mueve."],
    "radio_escolta_heroe": ["Uno quería hacerse el héroe. Ya no quiere.", "Quieto ahí. Le he quitado las ganas a uno que iba a por ti."],
    "radio_escolta_alarma": ["Una mano iba hacia el botón de la alarma. No ha llegado.", "Casi pulsan la alarma. Casi."],
    "frases_escolta_herido": ["¡A {nombre} le han dado! Se arrastra hacia la puerta: está fuera del golpe.", "{nombre} cae herido y sale como puede. No cuentes con él para lo que queda."],
    "frases_heroe": ["¡Uno de los que estaban en el suelo se levanta y va a por ti!", "¡Cuidado! Alguien ha sacado un arma de debajo del mostrador."],
    "frases_alarma": ["¡Alguien ha pulsado la alarma antes de tiempo!", "Se oye un timbre al fondo: han dado la alarma mientras abrías."],
    "radio_caja_empieza": ["Me pongo con ella. Dame {segundos} segundos.", "Esta la conozco. {segundos} segundos y es nuestra."],
    "radio_caja_ayuda": ["Yo sujeto, tú gira. Así va más deprisa.", "Déjame la cerradura a mí, tú vigila la puerta de la cámara."],
    "radio_caja_mitad": ["Va por la mitad.", "Ya cede. Un poco más."],
    "radio_caja_hecho": ["¡Abierta!", "¡Ya está! Todo dentro de la bolsa."],
    "radio_caja_nervios": ["No... no atino. Me sudan las manos. Va a tardar más.", "Se me ha partido la ganzúa. Empiezo otra vez."],
    "radio_caja_solo": ["Si no me cubres, no sigo. Vuelve aquí.", "No abro con la espalda al aire. Acércate."],
    "radio_tirador_dispara": ["¡Los tengo detrás! Disparo.", "Baja la ventanilla, que les voy a dar."],
    "radio_tirador_acierta": ["¡Le he dado!", "¡Ese ya no nos sigue igual!", "¡Tocado!"],
    "frases_reparto": ["Reparto: {partes}. Para ti quedan {neto} euros de {botin}.", "Cada uno lo suyo: {partes}. A ti te quedan {neto} de los {botin} euros."],
    "frases_se_va": ["{nombre} se harta de golpes que salen mal y deja la banda.", "{nombre} dice que contigo solo se gana cárcel, y se va."],
    "vehiculos": [],
}, cero=("caja_ayuda", "caja_nervios", "vigilante_retraso", "vigilante_aviso", "conductor_ventaja", "conductor_nivel", "heroe_prob", "heroe_escolta", "alarma_prob",
         "alarma_escolta", "fallo_base", "herido_prob", "detenido_prob", "delata_lealtad", "delata_busqueda", "reparto_tope", "lealtad_exito", "lealtad_fracaso",
         "exp_bono", "exp_max", "tirador_dano"))

EFECTOS = ("conductor", "vigilante", "escolta", "caja", "tirador")
ATRIBUTOS = {"punteria": "puntería", "conduccion": "conducción", "nervios": "nervios", "lealtad": "lealtad"}
# Los papeles de serie; los datos (vida.json, papeles_golpe) pueden cambiarlos, quitarlos o añadir otros con los mismos efectos.
PAPELES_SERIE = [
    {"id": "conductor", "nombre": "Conductor", "efecto": "conductor", "atributo": "conduccion", "parte": 10,
     "desc": "Espera fuera, con el motor en marcha, en el vehículo que elijas. Al salir subes de pasajero, o al volante con el coche ya arrancado, y la huida empieza con ventaja."},
    {"id": "vigilante", "nombre": "Vigilante", "efecto": "vigilante", "atributo": "nervios", "parte": 8,
     "desc": "Se queda fuera. Cuando salta la alarma, entretiene a la policía un rato y te va diciendo por la radio cuánto falta para que llegue."},
    {"id": "escolta", "nombre": "Escolta dentro", "efecto": "escolta", "atributo": "punteria", "parte": 8,
     "desc": "Entra contigo y tiene a raya a la gente y a los guardias: es mucho más difícil que alguien se haga el héroe o pulse la alarma antes de tiempo."},
    {"id": "caja", "nombre": "El de la caja", "efecto": "caja", "atributo": "nervios", "parte": 10,
     "desc": "Sabe de cerraduras: contigo, la caja se abre bastante antes; y si eliges cubrirle, la abre él mientras tú vigilas."},
    {"id": "tirador", "nombre": "Tirador", "efecto": "tirador", "atributo": "punteria", "parte": 8,
     "desc": "Va en el vehículo de la huida y dispara por la ventanilla a los que os persiguen."},
]
PAPELES = [dict(x) for x in PAPELES_SERIE]


def configurar(datos):
    """Los papeles de los datos. Uno sin efecto conocido no vale; sin ninguno válido, los de serie."""
    lista = []
    for x in datos.get("papeles_golpe", []) or []:
        if not isinstance(x, dict) or x.get("efecto") not in EFECTOS or not str(x.get("id") or "").strip():
            continue
        try:
            lista.append({"id": str(x["id"]), "nombre": str(x.get("nombre") or x["id"]), "efecto": x["efecto"],
                          "atributo": x.get("atributo") if x.get("atributo") in ATRIBUTOS else "nervios",
                          "parte": max(0.0, min(100.0, float(x.get("parte", 0) or 0))), "desc": str(x.get("desc") or "")})
        except (TypeError, ValueError):
            continue
    PAPELES[:] = lista or [dict(x) for x in PAPELES_SERIE]


def papel(ident):
    return next((x for x in PAPELES if x["id"] == ident), None)


def _tiempo_caja(tipo):
    for linea in AJ.lista("tiempos_caja"):
        k, _, v = linea.partition("=")
        if k.strip() == tipo:
            try:
                return max(1.0, float(v))
            except ValueError:
                break
    return AJ.entre("caja_min", "caja_max")


def _lista_txt(cosas):
    cosas = list(cosas)
    return cosas[0] if len(cosas) == 1 else ", ".join(cosas[:-1]) + " y " + cosas[-1] if cosas else ""


class Golpes:
    """Mixin de Partida."""

    def golpes_iniciar(self):
        self.golpe = None

    # ------------------------------------------------------------------ la gente de tu banda, uno por uno
    def _ficha_banda(self, nombre=None, genero=None, nervios=None, lealtad=None):
        a, b = sorted((AJ.entero("atributo_min"), AJ.entero("atributo_max")))
        j = self.j
        genero = genero or random.choice("hm")
        usados = {f.get("n") for f in j.banda_gente if isinstance(f, dict)}
        if not nombre:
            libres = [n for n in G.nombres(genero) if n not in usados] or list(G.nombres(genero))
            nombre = random.choice(libres)
        return {"id": max([int(f.get("id", 0)) for f in j.banda_gente if isinstance(f, dict)] or [0]) + 1, "n": nombre, "g": genero,
                "punteria": random.randint(a, b), "conduccion": random.randint(a, b),
                "nervios": int(nervios) if nervios is not None else random.randint(a, b),
                "lealtad": int(lealtad) if lealtad is not None else random.randint(max(a, 40), max(b, 60)), "exp": 0, "baja": 0}

    def banda_fichas(self):
        """La gente de tu banda, uno por uno, con su nombre y lo que vale. Siempre tantos como diga la banda: una partida
        anterior, que solo sabía cuántos erais, les da nombre y aptitudes la primera vez."""
        j = self.j
        if not isinstance(j.banda_gente, list):
            j.banda_gente = []
        j.banda_gente[:] = [f for f in j.banda_gente if isinstance(f, dict) and f.get("n")]
        for f in j.banda_gente:
            for k in ("punteria", "conduccion", "nervios", "lealtad"):
                try:
                    f[k] = max(0, min(100, int(f.get(k, 50))))
                except (TypeError, ValueError):
                    f[k] = 50
            f.setdefault("exp", 0)
            f.setdefault("baja", 0)
            f.setdefault("g", "h")
            f.setdefault("id", 0)
        n = max(0, int(j.banda))
        while len(j.banda_gente) < n:
            j.banda_gente.append(self._ficha_banda())
        del j.banda_gente[n:]
        return j.banda_gente

    def banda_ficha(self, bid):
        return next((f for f in self.banda_fichas() if f["id"] == bid), None)

    def banda_alta(self, nombre=None, genero=None, nervios=None, lealtad=None):
        """Alguien acaba de entrar en la banda (la cuenta ya está subida): se le apunta con su nombre."""
        j = self.j
        if not isinstance(j.banda_gente, list):
            j.banda_gente = []
        if len(j.banda_gente) < j.banda:
            del j.banda_gente[max(0, j.banda - 1):]
            j.banda_gente.append(self._ficha_banda(nombre, genero, nervios, lealtad))
        self.banda_fichas()
        return j.banda_gente[-1] if j.banda_gente else None

    def banda_quitar_ficha(self, bid=None):
        """Uno deja la banda (la cuenta ya está bajada): si se sabe quién, se borra a ese; si no, al último en llegar."""
        j = self.j
        if not isinstance(j.banda_gente, list):
            j.banda_gente = []
        f = next((x for x in j.banda_gente if isinstance(x, dict) and x.get("id") == bid), None) if bid is not None else None
        if f is not None:
            j.banda_gente.remove(f)
        self.banda_fichas()

    def banda_echar(self, bid, callar=False):
        """Uno de la banda se va o se lo llevan: baja la cuenta, se borra su ficha y desaparece de tu lado."""
        j = self.j
        if self.banda_ficha(bid) is None:
            return
        for e in [e for e in self.personas if getattr(e, "bid", None) == bid]:
            self.personas.remove(e)
        j.banda = max(0, j.banda - 1)
        self.banda_quitar_ficha(bid)

    def banda_ligar(self):
        """Cada uno de los tuyos que tienes al lado es alguien de la lista: se le da su nombre. Devuelve [(persona, ficha)]."""
        from . import sistemas
        fichas = self.banda_fichas()
        presentes = sistemas.miembros_presentes(self)
        usados = set()
        pares = []
        for e in presentes:
            f = self.banda_ficha(getattr(e, "bid", None))
            if f is not None and f["id"] not in usados:
                usados.add(f["id"])
                pares.append((e, f))
            else:
                e.bid = None
        for e in presentes:
            if getattr(e, "bid", None) is not None:
                continue
            nombre = e.nombre.split(",")[0]
            libres = [f for f in fichas if f["id"] not in usados and f.get("baja", 0) < self.dia] or [f for f in fichas if f["id"] not in usados]
            f = next((x for x in libres if x["n"] == nombre), None) or (libres[0] if libres else None)
            if f is None:
                continue
            e.bid = f["id"]
            usados.add(f["id"])
            e.nombre = f"{f['n']}, de {self.j.banda_nombre or 'tu banda'}"
            pares.append((e, f))
        return pares

    def aptitud(self, f, atributo):
        """Lo que vale alguien para algo, de 0 a 1: su atributo, más lo que ha aprendido en los golpes que lleva."""
        if not f:
            return 0.5
        v = float(f.get(atributo, 50)) + AJ("exp_bono") * min(float(f.get("exp", 0)), AJ("exp_max"))
        return max(0.05, min(1.0, v / 100.0))

    def ficha_banda_txt(self, f):
        t = f"{f['n']}: puntería {f['punteria']}, conducción {f['conduccion']}, nervios {f['nervios']} y lealtad {f['lealtad']}, de 100. "
        t += "Aún no ha dado ningún golpe contigo" if not f.get("exp") else "Lleva un golpe contigo" if f["exp"] == 1 else f"Lleva {f['exp']} golpes contigo"
        if f.get("baja", 0) >= self.dia:
            dias = f["baja"] - self.dia + 1
            t += f". Está de baja, herido: le queda{'n' if dias != 1 else ''} {dias} día{'s' if dias != 1 else ''}"
        return t

    # ------------------------------------------------------------------ ¿se puede preparar?
    def golpe_bloqueo(self):
        """Por qué no se puede preparar un golpe ahora, o una cadena vacía."""
        if self.en_servidor:
            return "En un servidor en línea los golpes no se preparan con la banda: allí tu gente son los demás jugadores, y el botín y la policía los lleva el servidor. El atraco de siempre sigue funcionando."
        if self.online_activo():
            return "Jugando con amigos los golpes no se preparan con la banda. El atraco de siempre sigue funcionando."
        if not self.j.banda:
            return "Para preparar un golpe necesitas gente en tu banda. Se recluta en el móvil, en Territorios, Tu banda, o hablando con la gente de la calle."
        return ""

    def golpe_presentes(self):
        """Los de tu banda que tienes cerca y pueden trabajar: [(persona, ficha)]."""
        x, y = self.pos()
        return [(e, f) for e, f in self.banda_ligar() if e.dist(x, y) <= AJ("radio_presentes") and f.get("baja", 0) < self.dia]

    def golpe_vehiculos(self):
        """Con qué puede esperar el conductor: tus vehículos de tierra que estén cerca, y los de la banda."""
        x, y = self.pos()
        u = self.tu_vehiculo()
        ops = []
        for v in self.vehiculos:
            if v.muerto or v.tag or v.ardiendo >= 0 or v.ia not in (None, "aparcado") or v.modelo.get("barco") or v.modelo.get("vuela") or getattr(v, "con_chofer", False):
                continue
            if (self.es_mio(v) or v is u or v is self.j.veh) and v.dist(x, y) <= AJ("radio_vehiculo"):
                ops.append(("veh", v, f"{v.nombre}, que está a {int(v.dist(x, y))} metros"))
        modelos = [m for m in AJ.lista("vehiculos") if m in self.modelos and not self.modelos[m].get("barco") and not self.modelos[m].get("vuela")] or self.chofer_modelos()
        for m in modelos:
            ops.append(("modelo", m, f"{self.modelos[m]['nombre']} de {self.j.banda_nombre or 'tu banda'}"))
        return ops

    # ------------------------------------------------------------------ empezar
    def golpe_adaptar(self, m, l, plan):
        """Convierte la misión de un atraco en un golpe preparado: la caja tarda, y el plan va con la misión (así un
        reintento lo repite igual)."""
        tipo = "banco" if m.get("id") == "atraco_banco" else "proveedor" if m.get("id") == "asalto_proveedor" else l.tipo
        segundos = round(_tiempo_caja(tipo), 1)
        for p in m["pasos"]:
            if p["tipo"] == "recoger":
                p["tarda"] = segundos
            elif p["tipo"] == "eliminar":
                p["texto"] = AJ.frase("frases_control") + " " + p["texto"]
        m["golpe"] = dict(plan, lugar=l.id, segundos=segundos)
        m["botin_bruto"] = int((m.get("recompensa") or {}).get("dinero", 0))
        antes = m.get("al_completar")

        def hecho():
            if callable(antes):
                antes()
            self.golpe_fin(True)
        m["al_completar"] = hecho
        return m

    def golpe_al_iniciar(self, m):
        """Empieza (o se reintenta) la misión de un golpe preparado: cada uno a su puesto."""
        plan = m.get("golpe")
        if not plan:
            return
        l = self.lug(plan.get("lugar"))
        pares = {f["id"]: (e, f) for e, f in self.banda_ligar()}
        g = {"lugar": l, "plan": plan, "mision": m, "fase": None, "papeles": {}, "alarma": None, "llegan": None, "avisado_cerca": False, "llegado": False,
             "veh": None, "veh_tuyo": False, "subido": False, "t_tirador": 0.0, "t0": self.t, "detenidos": [], "heridos": [], "fallos": {},
             "caja_dicho": set(), "heroe": None, "alarma_antes": None, "tarde": None, "nivel": 1, "botin": int(m.get("botin_bruto", 0))}
        g["nivel"] = next((int(p.get("nivel", 1)) for p in m["pasos"] if p["tipo"] == "policia"), 0)
        g["guardias"] = any(p["tipo"] == "eliminar" for p in m["pasos"])
        for bid, pid in (plan.get("papeles") or {}).items():
            par = pares.get(int(bid))
            pp = papel(pid)
            if par is None or pp is None:
                continue
            e, f = par
            g["papeles"][f["id"]] = {"papel": pp, "persona": e, "ficha": f, "efecto": pp["efecto"], "fuera": False}
            e.papel = pp["efecto"]
        self.golpe = g
        yo = plan.get("yo") or {}
        g["cubrir"] = yo.get("dentro") == "cubrir" and self._golpe_de("caja") is not None
        g["pasajero"] = yo.get("huida") == "pasajero" and self._golpe_de("conductor") is not None
        self._golpe_sortear(g)
        self._golpe_fase("entrada")
        self._golpe_puestos(g, plan)

    def _golpe_de(self, efecto):
        """Quien tiene ese papel y sigue en el golpe: su entrada, o None."""
        g = self.golpe
        if not g:
            return None
        return next((r for r in g["papeles"].values() if r["efecto"] == efecto and not r["fuera"]), None)

    def _golpe_radio(self, r, cual, **kw):
        """Uno de los tuyos habla por la radio."""
        self.son("emisora", cat="interfaz", vol=0.5)
        self.decir(f"{r['ficha']['n']}, por la radio: {AJ.frase(cual, **kw)}")

    def _golpe_fallo(self, r, base=None):
        """¿Le pueden los nervios? Cuanto más temple y más golpes a la espalda, menos."""
        p = (AJ("fallo_base") if base is None else base) / 100.0 * (1.0 - self.aptitud(r["ficha"], "nervios"))
        return random.random() < p

    def _golpe_sortear(self, g):
        """Lo que va a salir mal se decide al empezar, cada vez distinto, según lo que vale cada uno."""
        esc = self._golpe_de("escolta")
        cubre = self.aptitud(esc["ficha"], esc["papel"]["atributo"]) if esc else 0.0
        heroe, alarma = random.random() * 100 < AJ("heroe_prob"), random.random() * 100 < AJ("alarma_prob")
        para_heroe = heroe and esc is not None and random.random() * 100 < AJ("heroe_escolta") * cubre
        para_alarma = alarma and esc is not None and random.random() * 100 < AJ("alarma_escolta") * cubre
        # en qué momento de la caja ocurre, de 0 a 1
        g["heroe"] = random.uniform(0.2, 0.7) if heroe and not para_heroe else None
        g["alarma_antes"] = random.uniform(0.3, 0.8) if alarma and not para_alarma and g["nivel"] else None
        g["evitado"] = {"heroe": para_heroe, "alarma": para_alarma}
        for r in g["papeles"].values():
            ef = r["efecto"]
            if ef == "conductor":
                if self._golpe_fallo(r):
                    g["fallos"]["conductor"] = random.choice(("tarde", "calado"))
            elif ef == "vigilante":
                if self._golpe_fallo(r):
                    g["fallos"]["vigilante"] = "dormido"
                if g["nivel"] and random.random() < AJ("detenido_prob") / 100.0 * (1.2 - self.aptitud(r["ficha"], "nervios")):
                    g["fallos"]["vigilante_detenido"] = True
            elif ef == "caja":
                if self._golpe_fallo(r):
                    g["fallos"]["caja"] = "nervios"
            elif ef == "escolta":
                if g["guardias"] and random.random() < AJ("herido_prob") / 100.0 * (1.3 - self.aptitud(r["ficha"], "punteria")):
                    g["fallos"]["escolta"] = random.uniform(4.0, 12.0)

    def _golpe_puestos(self, g, plan):
        """Cada uno a su sitio: el vigilante a la esquina, el conductor al vehículo, y los demás contigo."""
        l = g["lugar"]
        x, y = (l.x, l.y) if l is not None else self.pos()
        vig = self._golpe_de("vigilante")
        if vig:
            vig["persona"].puesto = self._golpe_esquina(x, y)
            vig["persona"].x, vig["persona"].y = vig["persona"].puesto
            self._golpe_radio(vig, "radio_vigilante_listo")
        con = self._golpe_de("conductor")
        if con:
            if g["fallos"].get("conductor") == "tarde":
                g["tarde"] = AJ.entre("tarde_min", "tarde_max")
                self._golpe_radio(con, "radio_conductor_tarde")
                con["persona"].puesto = self._golpe_esquina(x, y)
            else:
                self._golpe_poner_vehiculo(g, con)
        esc = self._golpe_de("escolta")
        if esc:
            self._golpe_radio(esc, "radio_escolta_control")

    def _golpe_esquina(self, x, y):
        """Un sitio en la acera, a unos metros de la puerta, desde donde vigilar."""
        for _ in range(40):
            a = random.uniform(0, 2 * math.pi)
            d = random.uniform(14, 24)
            px, py = x + math.sin(a) * d, y + math.cos(a) * d
            if self.mundo.superficie(px, py) == "acera":
                return px, py
        return self.mundo.punto_libre(x, y)

    def _golpe_poner_vehiculo(self, g, con, llega=False):
        """El conductor arrima el vehículo de la huida a la puerta, con el motor en marcha."""
        l = g["lugar"]
        plan = g["plan"]
        px, py, d = self.mundo.plaza_junto_a(l) if l is not None else self.plaza_cercana()
        v = next((x for x in self.vehiculos if getattr(x, "id_golpe", None) == plan.get("veh_id") and not x.muerto), None) if plan.get("veh_id") else None
        if v is not None and (self.j.veh is v or v.ia not in (None, "aparcado")):
            v = None
        if v is not None:
            v.x, v.y, v.dir, v.rumbo, v.vel = px, py, d, d * 90.0, 0.0
            g["veh_tuyo"] = True
        else:
            modelo = plan.get("modelo") if plan.get("modelo") in self.modelos else random.choice(self.chofer_modelos())
            v = self.crear_vehiculo(modelo, px, py, d, None, f"{self.modelos[modelo]['nombre']} de {self.j.banda_nombre or 'tu banda'}", "banda")
            v.propio = True
        v.cerrado = False
        v.en_marcha = True
        if v.canal is None:
            v.canal = self.son(v.modelo["motor"], bucle=True, xy=(v.x, v.y), ref=7, maxd=95, vol=0.7, tono=v.modelo["tono"] * 0.6)
        if v.sirena is None:
            v.sirena = self.son("loc_vehiculo", bucle=True, xy=(v.x, v.y), ref=5, maxd=70)
        g["veh"] = v
        con["persona"].puesto = (v.x, v.y)
        con["persona"].x, con["persona"].y = self.mundo.punto_libre(v.x, v.y)
        if self.chofer:                                          # si ya tenías chófer, se retira: hoy conduce el del golpe
            self.despedir_chofer(callar=True)
        if g["pasajero"]:
            self.chofer = {"estado": "aqui", "t": 0.0, "garaje": None, "ficha": None, "modelo": v.modelo["id"], "veh": v, "propio": g["veh_tuyo"],
                           "nombre": f"{con['ficha']['n']}, de {self.j.banda_nombre or 'tu banda'}", "intentos": 0, "sin_destino": 0.0, "golpe": True}
            v.con_chofer = True
        self._golpe_radio(con, "radio_conductor_llega" if llega else "radio_conductor_listo")
        self.decir(f"{self.situar(v.x, v.y, v.nombre)}." + (" Irás de pasajero." if g["pasajero"] else " Conducirás tú."))

    # ------------------------------------------------------------------ las fases
    def _golpe_fase(self, fase):
        g = self.golpe
        if not g or g["fase"] == fase:
            return
        g["fase"] = fase
        if fase == "control" and g["guardias"]:
            return                                               # la frase va con el texto del paso, que ya la lleva delante
        clave = "frases_control_sin_guardia" if fase == "control" else "frases_" + fase
        self.son("emisora", cat="interfaz", vol=0.4)
        self.decir(AJ.frase(clave))

    def golpe_fase_txt(self):
        g = self.golpe
        nombres = {"entrada": "entrada", "control": "control", "caja": "la caja", "salida": "salida", "huida": "huida"}
        orden = ["entrada", "control", "caja", "salida", "huida"]
        if not g or g["fase"] not in nombres:
            return ""
        return f"Golpe preparado, fase {orden.index(g['fase']) + 1} de 5: {nombres[g['fase']]}."

    def golpe_caja(self):
        """Cómo se abre la caja en este golpe: cuánto se alarga o se acorta, a qué distancia vale estar, y si la abre uno de
        los tuyos sin que tú la toques. None si no hay golpe preparado."""
        g = self.golpe
        if not g:
            return None
        r = self._golpe_de("caja")
        factor = 1.0
        if r:
            if g["fallos"].get("caja") == "nervios":
                factor = 1.0 + AJ("caja_nervios") / 100.0
            else:
                factor = max(0.25, 1.0 - AJ("caja_ayuda") / 100.0 * self.aptitud(r["ficha"], r["papel"]["atributo"]))
        solo = bool(g["cubrir"] and r)
        return {"factor": factor, "radio": AJ("cubrir_radio") if solo else AJ("caja_radio"), "solo": solo, "quien": r}

    def golpe_caja_evento(self, cual, segundos=0):
        """La caja empieza a abrirse, va por la mitad, se para o se abre: lo dice quien la abre."""
        g = self.golpe
        if not g:
            return False
        r = self._golpe_de("caja")
        if cual == "empieza":
            self._golpe_fase("caja")
            if r:
                self._golpe_radio(r, "radio_caja_nervios" if g["fallos"].get("caja") == "nervios" else "radio_caja_empieza" if g["cubrir"] else "radio_caja_ayuda", segundos=int(round(segundos)))
                return bool(g["cubrir"])
            return False
        if r is None:
            return False
        if cual == "mitad":
            self._golpe_radio(r, "radio_caja_mitad")
        elif cual == "hecho":
            self._golpe_radio(r, "radio_caja_hecho")
        elif cual == "pausa":
            self._golpe_radio(r, "radio_caja_solo")
        return True

    def golpe_retraso_policia(self, nivel):
        """Al acabar la caja: cuánto tarda aún la policía en llegar. Con un golpe preparado la alarma salta y el vigilante,
        si lo hay, la entretiene; devuelve los segundos que faltan (0, ya)."""
        g = self.golpe
        if not g:
            return 0.0
        g["nivel"] = max(g["nivel"], int(nivel or 1))
        self._golpe_fase("salida")
        if g["alarma"] is None:
            self._golpe_alarma(g)
        return max(0.0, (g["llegan"] or self.t) - self.t)

    def _golpe_alarma(self, g, antes=False):
        """Salta la alarma. Desde aquí, la policía llega cuando el vigilante deje de poder entretenerla."""
        g["alarma"] = self.t
        r = self._golpe_de("vigilante")
        retraso = 0.0
        if r:
            if g["fallos"].get("vigilante") == "dormido":
                self._golpe_radio(r, "radio_vigilante_falla")
            else:
                retraso = AJ("vigilante_retraso") * (0.5 + 0.75 * self.aptitud(r["ficha"], r["papel"]["atributo"]))
                self._golpe_radio(r, "radio_vigilante_alarma", segundos=int(round(retraso)))
        g["llegan"] = self.t + retraso
        if antes:
            self.son("alarma", vol=0.4)

    def _golpe_llegan(self, g):
        """La policía ya está aquí: cae la búsqueda, y al vigilante lo pueden coger."""
        if g["llegado"]:
            return
        g["llegado"] = True
        r = self._golpe_de("vigilante")
        if r and g["fallos"].get("vigilante") != "dormido":
            self._golpe_radio(r, "radio_vigilante_llegan")
        if g["nivel"]:
            self.poner_busqueda(g["nivel"])
        if r and g["fallos"].get("vigilante_detenido"):
            f = r["ficha"]
            r["fuera"] = True
            g["detenidos"].append(f["n"])
            self.son("esposas", cat="interfaz", vol=0.6)
            self.decir(AJ.frase("frases_vigilante_detenido", nombre=f["n"]))
            delata = f["lealtad"] < AJ("delata_lealtad")
            self.banda_echar(f["id"])
            self.j.stats["banda_detenidos"] = self.j.stats.get("banda_detenidos", 0) + 1
            if delata:
                self.decir(AJ.frase("frases_delata", nombre=f["n"]) + f" Quedáis {self.j.banda} en la banda.")
                if AJ("delata_busqueda") >= 1 and g["nivel"]:
                    self.poner_busqueda(min(5, g["nivel"] + AJ.entero("delata_busqueda")))
                self.hon_antecedente(2, f"señalado por un detenido tras el atraco a {g['lugar'].nombre if g['lugar'] else 'un local'}")
                self.j.stats["banda_delaciones"] = self.j.stats.get("banda_delaciones", 0) + 1
            else:
                self.decir(AJ.frase("frases_no_delata", nombre=f["n"]) + f" Quedáis {self.j.banda} en la banda.")

    def actualizar_golpe(self, dt):
        g = self.golpe
        if not g:
            return
        ms = self.mision
        if not ms or not ms["def"].get("golpe"):
            self.golpe_fin(False, callar=True)
            return
        pasos = ms["def"]["pasos"]
        if not (0 <= ms["paso"] < len(pasos)):
            return
        tipo = pasos[ms["paso"]]["tipo"]
        j = self.j
        if tipo == "eliminar":
            self._golpe_fase("control")
            t_herido = g["fallos"].get("escolta")
            esc = self._golpe_de("escolta")
            if esc and t_herido is not None and ms.get("generado") and self.t - g.setdefault("t_control", self.t) >= t_herido:
                g["fallos"].pop("escolta")
                self._golpe_herido(g, esc)
        elif tipo == "recoger":
            if g["fase"] in ("entrada", None):
                self._golpe_fase("control")
                g["fase_t"] = self.t
            ab = ms.get("abriendo")
            hecho = float(ab["t"]) / max(0.1, float(ab["total"])) if ab else 0.0      # cuánto va de caja, de 0 a 1
            esc = self._golpe_de("escolta")
            if g["heroe"] is not None and hecho >= g["heroe"]:
                g["heroe"] = None
                self._golpe_heroe(g)
            elif g["evitado"].get("heroe") and esc and hecho >= 0.4:
                g["evitado"]["heroe"] = False
                self._golpe_radio(esc, "radio_escolta_heroe")
            if g["alarma_antes"] is not None and hecho >= g["alarma_antes"] and g["alarma"] is None:
                g["alarma_antes"] = None
                self.decir(AJ.frase("frases_alarma"))
                self._golpe_alarma(g, antes=True)
            elif g["evitado"].get("alarma") and esc and hecho >= 0.7:
                g["evitado"]["alarma"] = False
                self._golpe_radio(esc, "radio_escolta_alarma")
        elif tipo == "policia":
            if g["llegado"] and (j.veh is not None or (g["lugar"] is not None and math.hypot(g["lugar"].x - self.pos()[0], g["lugar"].y - self.pos()[1]) > 45)):
                self._golpe_fase("huida")
        # la policía viene de camino: el vigilante lo va cantando
        if g["alarma"] is not None and not g["llegado"]:
            falta = g["llegan"] - self.t
            vig = self._golpe_de("vigilante")
            if falta <= 0:
                self._golpe_llegan(g)
            elif vig and not g["avisado_cerca"] and falta <= AJ("vigilante_aviso") and g["fallos"].get("vigilante") != "dormido":
                g["avisado_cerca"] = True
                self._golpe_radio(vig, "radio_vigilante_cerca", segundos=max(1, int(round(falta))))
        # el conductor que llegaba tarde
        if g["tarde"] is not None and tipo == "policia":
            g["tarde"] -= dt
            con = self._golpe_de("conductor")
            if con is None:
                g["tarde"] = None
            elif g["tarde"] <= 0:
                g["tarde"] = None
                self._golpe_poner_vehiculo(g, con, llega=True)
        v = g["veh"]
        if v is not None and (v.muerto or v not in self.vehiculos):
            g["veh"] = v = None
        if v is not None and j.veh is v and not g["subido"]:
            g["subido"] = True
            self._golpe_subes(g)
        self._golpe_tirador(g, dt)

    def _golpe_herido(self, g, r):
        f = r["ficha"]
        r["fuera"] = True
        g["heridos"].append(f["n"])
        dias = random.randint(*sorted((AJ.entero("herido_dias_min"), AJ.entero("herido_dias_max"))))
        f["baja"] = self.dia + dias
        e = r["persona"]
        self.son("dolor_npc", xy=(e.x, e.y), ref=6, tono=e.tono)
        if e in self.personas:
            self.personas.remove(e)
        self.decir(AJ.frase("frases_escolta_herido", nombre=f["n"]) + f" Estará de baja {dias} días.")
        # sin él, lo que tenía a raya puede volver a pasar
        if g["evitado"].get("heroe"):
            g["evitado"]["heroe"], g["heroe"] = False, random.uniform(0.2, 0.7)
        if g["evitado"].get("alarma"):
            g["evitado"]["alarma"], g["alarma_antes"] = False, random.uniform(0.3, 0.8)

    def _golpe_heroe(self, g):
        x, y = self.pos()
        pos = self._punto_cercano(7, 14, acera=False) or self.mundo.punto_libre(x + random.uniform(-10, 10), y + random.uniform(-10, 10))
        e = Persona("enemigo", pos[0], pos[1], "El que se hace el héroe")
        e.salud, e.arma = 55.0, "pistola"
        e.hostil, e.estado, e.activo, e.tag = True, "ataca", True, "golpe"
        e.t_disparo = random.uniform(1.5, 2.5)
        self.personas.append(e)
        g["heroe_persona"] = e
        self.son("grito", xy=pos, vol=0.6)
        self.decir(AJ.frase("frases_heroe") + " Pulsa Q para fijarlo.")

    def _golpe_subes(self, g):
        """Subes al vehículo de la huida: el motor ya estaba en marcha, y el conductor te da ventaja."""
        con = self._golpe_de("conductor")
        if con is None:
            return
        j = self.j
        apt = self.aptitud(con["ficha"], con["papel"]["atributo"])
        if g["fallos"].get("conductor") == "calado":
            self._golpe_radio(con, "radio_conductor_sin_ventaja")
        elif not g["llegado"] and g["alarma"] is not None:
            extra = AJ("conductor_ventaja") * (0.5 + 0.75 * apt)
            g["llegan"] += extra
            g["avisado_cerca"] = False
            self._golpe_radio(con, "radio_conductor_ventaja")
            self.decir(f"Ventaja: la policía tardará unos {int(round(extra))} segundos más en dar contigo.")
        elif j.estrellas > 1 and random.random() * 100 < AJ("conductor_nivel") * (0.4 + 0.6 * apt):
            from .combate import UMBRAL
            j.puntos_busqueda = float(UMBRAL[j.estrellas - 2])
            j.estrellas -= 1
            self.sv_busqueda(j.estrellas)
            self._golpe_radio(con, "radio_conductor_ventaja")
            self.son("estrella_baja", cat="interfaz")
            self.decir(f"Ventaja: sale por donde no os esperan. Nivel de búsqueda {j.estrellas}.")
        elif not g["pasajero"]:
            self._golpe_radio(con, "radio_conductor_tu")
        if g["pasajero"] and self.chofer_conduce() and not self.gps:
            dest = self._destino_azar(280, 700, g["lugar"])
            self.gps_a_lugar(dest, callar=True)
            self.decir(f"{con['ficha']['n']} pone rumbo a {dest.nombre}, lejos de aquí. Con la L eliges tú otro destino.")

    def _golpe_tirador(self, g, dt):
        r = self._golpe_de("tirador")
        j = self.j
        if r is None or j.veh is None or j.estrellas <= 0:
            return
        g["t_tirador"] -= dt
        if g["t_tirador"] > 0:
            return
        g["t_tirador"] = AJ("tirador_cada") * random.uniform(0.8, 1.3)
        x, y = self.pos()
        alcance = AJ("tirador_alcance")
        blancos = [v for v in self.vehiculos if v.ia == "policia" and not v.muerto and getattr(v, "hostil", True) and v.dist(x, y) <= alcance]
        gente = [p for p in self.personas if p.tipo == "policia" and p.hostil and not p.muerto and p.dist(x, y) <= alcance]
        if not blancos and not gente:
            return
        if not g.get("tirador_dicho"):
            g["tirador_dicho"] = True
            self._golpe_radio(r, "radio_tirador_dispara")
        self.son("disparo_pistola", vol=0.6)
        apt = self.aptitud(r["ficha"], r["papel"]["atributo"])
        if random.random() > 0.25 + 0.6 * apt:
            return
        dano = AJ("tirador_dano") * (0.7 + 0.6 * apt)
        if blancos:
            v = min(blancos, key=lambda v: v.dist(x, y))
            self.danar_vehiculo(v, dano)
        else:
            self.danar_persona(min(gente, key=lambda p: p.dist(x, y)), dano)
        g["tirador_aciertos"] = g.get("tirador_aciertos", 0) + 1
        if g["tirador_aciertos"] % 3 == 1:
            self.decir(f"{r['ficha']['n']}: {AJ.frase('radio_tirador_acierta')}")

    # ------------------------------------------------------------------ el final
    def golpe_reparto(self, botin, g=None):
        """Cuánto se lleva cada uno de los que han cumplido: [(nombre, papel, euros)] y lo que te queda."""
        g = g or self.golpe
        if not g:
            return [], botin
        partes = [(r["ficha"]["n"], r["papel"]["nombre"], float(r["papel"]["parte"])) for r in g["papeles"].values()
                  if r["ficha"]["n"] not in g["detenidos"] and self.banda_ficha(r["ficha"]["id"]) is not None]
        total = sum(p for _, _, p in partes)
        tope = AJ("reparto_tope")
        escala = tope / total if total > tope > 0 else 1.0 if tope > 0 else 0.0
        lista = [(n, papel_n, int(botin * p * escala / 100.0)) for n, papel_n, p in partes]
        return lista, max(0, botin - sum(e for _, _, e in lista))

    def golpe_fin(self, exito, callar=False):
        """Se acaba el golpe: bien (reparto, experiencia y lealtad) o mal (cada uno por su lado, y la confianza baja)."""
        g = self.golpe
        if not g:
            return
        self.golpe = None
        m = g.get("mision")
        for e in self.personas:
            if getattr(e, "puesto", None) is not None:
                e.puesto = None
            if getattr(e, "papel", None):
                e.papel = None
        h = g.get("heroe_persona")
        if h is not None and h in self.personas and not exito:
            self.personas.remove(h)
        v = g["veh"]
        if v is not None and not v.muerto:
            v.en_marcha = False
            if self.j.veh is not v:
                if v.canal is not None:
                    v.canal.parar()
                    v.canal = None
                if not (self.chofer and self.chofer.get("veh") is v):
                    if v.sirena is not None:
                        v.sirena.parar()
                        v.sirena = None
                    if v.tag == "banda":                         # el coche de la banda se va con quien lo trajo
                        self.quitar_vehiculo(v)
        fichas = [r["ficha"] for r in g["papeles"].values() if self.banda_ficha(r["ficha"]["id"]) is not None]
        if exito:
            botin = int(g["botin"])
            lista, neto = self.golpe_reparto(botin, g) if m is not None else ([], botin)
            if m is not None and botin:
                m.setdefault("recompensa", {})["dinero"] = neto
            for f in fichas:
                f["exp"] = int(f.get("exp", 0)) + 1
                f["lealtad"] = min(100, f["lealtad"] + AJ.entero("lealtad_exito"))
            self.j.stats["golpes_preparados"] = self.j.stats.get("golpes_preparados", 0) + 1
            if lista and botin and not callar:
                self.son("dinero", cat="interfaz", vol=0.5)
                self.decir(AJ.frase("frases_reparto", partes=_lista_txt(f"{n}, {e} euros" for n, _, e in lista), neto=neto, botin=botin))
            if g["heridos"] and not callar:
                self.decir(f"{_lista_txt(g['heridos'])} cobra igual, pero no podrá trabajar hasta que se cure.")
            return
        if m is not None and g["botin"]:
            m.setdefault("recompensa", {})["dinero"] = int(g["botin"])       # un reintento empieza con el botín entero
        se_van = []
        for f in fichas:
            f["lealtad"] = max(0, f["lealtad"] - AJ.entero("lealtad_fracaso"))
            if f["lealtad"] <= 0:
                se_van.append(f)
        for f in se_van:
            self.banda_echar(f["id"])
            if not callar:
                self.decir(AJ.frase("frases_se_va", nombre=f["n"]) + f" Quedáis {self.j.banda}.")
        self.j.stats["golpes_fallidos"] = self.j.stats.get("golpes_fallidos", 0) + 1

    def golpe_estado_txt(self):
        """Para la tecla del objetivo: en qué fase va el golpe y quién hace qué."""
        g = self.golpe
        if not g:
            return ""
        t = self.golpe_fase_txt()
        quien = [f"{r['ficha']['n']}, {r['papel']['nombre'].lower()}" for r in g["papeles"].values() if not r["fuera"]]
        if quien:
            t += " " + _lista_txt(quien) + "."
        if g["alarma"] is not None and not g["llegado"]:
            t += f" La policía llega en unos {max(1, int(g['llegan'] - self.t))} segundos."
        return t


# ====================================================================== menús
def como_funciona(p):
    """«Cómo funciona esto»: los golpes preparados, con los números de verdad de los datos."""
    from .menus import Menu, Opcion
    app = p.app
    lineas = [
        "Qué es. Un atraco de los de siempre, a un banco, a un local con caja o a un proveedor, lo puedes preparar antes si tienes a gente de tu banda al lado. No es obligatorio: sin prepararlo, el atraco es el de siempre.",
        "Antes de empezar repartes los papeles: eliges a cada uno de los tuyos y le das uno. A quien no le des ninguno, viene contigo y pelea a tu lado, como siempre. Quien tiene un papel está en lo suyo.",
    ]
    for x in PAPELES:
        lineas.append(f"{x['nombre']}. {x['desc']} Rinde según su {ATRIBUTOS[x['atributo']]}. Se lleva el {int(x['parte'])} por ciento del botín.")
    lineas += [
        "Tu papel. Dentro, o abres tú la caja, o cubres a quien la abre y te ocupas de lo que venga. En la huida, o conduces tú, o vas de pasajero y disparas con la Q y Control.",
        f"Las fases. Un golpe preparado tiene cinco, y el juego las dice: entrada, control, caja, salida y huida. La tecla O te dice en cuál vas. La caja ya no se coge al momento: tarda entre {AJ.entero('caja_min')} y "
        f"{AJ.entero('caja_max')} segundos según el local, y más en un banco. Se oye cómo avanza. Si te apartas, se para.",
        "Lo que vale cada uno. Cada persona de tu banda tiene puntería, conducción, nervios y lealtad, de 0 a 100, distintas en cada partida. Las ves en el móvil, en Territorios, Tu banda, Tu gente. Con cada golpe que sale bien aprenden y te son más leales.",
        "Lo que puede salir mal. A quien le fallan los nervios llega tarde, no avisa o tarda más con la caja. Al de dentro le pueden herir y está de baja unos días. Al vigilante lo pueden detener, y si su lealtad es baja, da tu nombre: "
        "sube la búsqueda y te queda un antecedente. Si el golpe fracasa, todos pierden confianza en ti, y quien se queda sin ninguna se va.",
        f"El reparto. Cada uno cobra su parte del botín al acabar; entre todos, como mucho el {AJ.entero('reparto_tope')} por ciento. Lo demás es tuyo. Antes de empezar, el menú te dice cuánto te va a quedar.",
        "En un servidor en línea y jugando con amigos los golpes no se preparan con la banda: el atraco de siempre sigue funcionando.",
    ]
    ops = [Opcion(t.rstrip(".")) for t in lineas]
    ops.append(Opcion("Volver", lambda: app.cerrar(m)))
    m = Menu(app, "Golpes preparados: cómo funciona. Recorre la explicación con las flechas", ops)
    app.abrir(m)


def menu_gente(p):
    """Tu gente, uno por uno: lo que vale cada cual."""
    from .menus import Menu, Opcion
    app = p.app
    p.banda_ligar()

    def ops():
        lista = [Opcion(p.ficha_banda_txt(f), ayuda="Puntería, para disparar y tener a raya a la gente; conducción, para la huida; nervios, para no fallar cuando aprieta; lealtad, para no delatarte si lo detienen. "
                        "Suben con cada golpe preparado que sale bien.") for f in p.banda_fichas()]
        return lista or [Opcion("Todavía no hay nadie en tu banda")]
    app.abrir(Menu(app, lambda: f"Tu gente: {p.j.banda} en {p.j.banda_nombre or 'tu banda'}", ops))


def preparar(p, l, empezar, que="el golpe"):
    """El menú «Preparar el golpe»: quién hace qué, tu papel, el vehículo y empezar. `empezar(plan)` lanza el atraco de
    ese sitio con el plan; devuelve True si ha empezado."""
    from .menus import Menu, Opcion
    from . import sistemas
    app = p.app
    motivo = p.golpe_bloqueo()
    if motivo:
        app.son("error")
        app.decir(motivo, True)
        return
    plan = {"papeles": {}, "yo": {"dentro": "caja", "huida": "conducir"}, "veh_id": None, "modelo": None}
    caja = p.caja_de_local(l) or {}
    botin = int(caja.get("dinero", 0) or 0)

    def presentes():
        return p.golpe_presentes()

    def limpiar():
        vivos = {f["id"] for _, f in presentes()}
        for bid in [b for b in plan["papeles"] if b not in vivos]:
            del plan["papeles"][bid]
        efectos = {papel(pid)["efecto"] for pid in plan["papeles"].values() if papel(pid)}
        if "caja" not in efectos:
            plan["yo"]["dentro"] = "caja"
        if "conductor" not in efectos:
            plan["yo"]["huida"] = "conducir"

    def partes_txt():
        total = sum(papel(pid)["parte"] for pid in plan["papeles"].values() if papel(pid))
        tope = AJ("reparto_tope")
        total = min(total, tope)
        if not plan["papeles"]:
            return "Reparto: nadie tiene papel todavía, así que todo el botín sería para ti"
        return f"Reparto: tu gente se lleva el {int(total)} por ciento y tú el {int(100 - total)}" + (f". Hoy, de unos {botin} euros, te quedarían {int(botin * (100 - total) / 100)}" if botin else "")

    def elegir_papel(f):
        def abrir():
            def poner(pid):
                def h():
                    if pid is None:
                        plan["papeles"].pop(f["id"], None)
                    else:
                        ef = papel(pid)["efecto"]
                        for b in [b for b, x in plan["papeles"].items() if papel(x) and papel(x)["efecto"] == ef and b != f["id"]]:
                            del plan["papeles"][b]              # cada papel lo hace uno solo: el anterior se queda sin él
                        plan["papeles"][f["id"]] = pid
                    limpiar()
                    app.cerrar(sub)
                    app.decir(f"{f['n']}: {papel(pid)['nombre'].lower() if pid else 'sin papel, viene contigo'}.", True)
                return h
            ops = [Opcion(f"{x['nombre']}. {f['n']} tiene {f[x['atributo']]} de 100 en {ATRIBUTOS[x['atributo']]}", poner(x["id"]),
                          ayuda=f"{x['desc']} Se lleva el {int(x['parte'])} por ciento del botín.") for x in PAPELES]
            ops.append(Opcion("Sin papel: viene contigo y pelea a tu lado, como siempre", poner(None), ayuda="No cobra parte del botín."))
            sub = Menu(app, f"Papel de {f['n']}. {p.ficha_banda_txt(f)}", ops)
            app.abrir(sub)
        return abrir

    def texto_miembro(f):
        return lambda: f"{f['n']}: " + (papel(plan["papeles"][f["id"]])["nombre"].lower() if papel(plan["papeles"].get(f["id"])) else "sin papel, viene contigo")

    def cambiar_dentro():
        if not any(papel(x) and papel(x)["efecto"] == "caja" for x in plan["papeles"].values()):
            app.son("error")
            app.decir("Para cubrir tiene que haber alguien que abra la caja: dale ese papel a uno de los tuyos.", True)
            return
        plan["yo"]["dentro"] = "cubrir" if plan["yo"]["dentro"] == "caja" else "caja"
        m.refrescar()

    def cambiar_huida():
        if not any(papel(x) and papel(x)["efecto"] == "conductor" for x in plan["papeles"].values()):
            app.son("error")
            app.decir("Para ir de pasajero tiene que haber conductor: dale ese papel a uno de los tuyos.", True)
            return
        plan["yo"]["huida"] = "pasajero" if plan["yo"]["huida"] == "conducir" else "conducir"
        m.refrescar()

    def veh_txt():
        if plan["veh_id"] is not None:
            v = next((x for x in p.vehiculos if getattr(x, "id_golpe", None) == plan["veh_id"] and not x.muerto), None)
            if v is not None:
                return f"Vehículo de la huida: {v.nombre}"
            plan["veh_id"] = None
        return f"Vehículo de la huida: {p.modelos[plan['modelo']]['nombre']} de la banda" if plan["modelo"] in p.modelos else "Vehículo de la huida: el que tenga la banda a mano"

    def elegir_veh():
        def poner(tipo, cosa):
            def h():
                if tipo == "veh":
                    cosa.id_golpe = cosa.id
                    plan["veh_id"], plan["modelo"] = cosa.id, None
                else:
                    plan["veh_id"], plan["modelo"] = None, cosa
                app.cerrar(sub)
                app.decir(veh_txt() + ".", True)
            return h
        ops = [Opcion(t, poner(tipo, cosa)) for tipo, cosa, t in p.golpe_vehiculos()]
        sub = Menu(app, "Con qué vehículo espera el conductor", ops, intro="Los tuyos que estén cerca y los de la banda")
        app.abrir(sub)

    def llamar():
        n, frase = sistemas.llamar(p)
        p.banda_ligar()
        if not n:
            app.son("error")
        m.refrescar(False)
        app.decir(frase, True)

    def lanzar():
        limpiar()
        if not plan["papeles"]:
            app.son("error")
            app.decir("Nadie tiene papel todavía. Da al menos uno, o vuelve atrás y empieza el atraco de siempre.", True)
            return
        copia = {"papeles": {str(b): pid for b, pid in plan["papeles"].items()}, "yo": dict(plan["yo"]), "veh_id": plan["veh_id"], "modelo": plan["modelo"]}
        empezar(copia)

    def ops():
        limpiar()
        pres = presentes()
        lista = [Opcion("Cómo funciona esto: los papeles, las fases y el reparto", lambda: como_funciona(p),
                        ayuda="La explicación entera de los golpes preparados, con sus números.")]
        for _, f in pres:
            lista.append(Opcion(texto_miembro(f), elegir_papel(f), ayuda=p.ficha_banda_txt(f) + ". Intro para darle un papel o quitárselo."))
        if len(pres) < len([f for f in p.banda_fichas() if f.get("baja", 0) < p.dia]):
            lista.append(Opcion("Llamar a los de tu banda que faltan", llamar, ayuda="Acuden a donde estés. Los que están de baja, heridos, no vienen."))
        if not pres:
            lista.append(Opcion("No tienes a nadie de tu banda al lado: llámalos"))
        lista.append(Opcion(lambda: "Tú, dentro: " + ("cubres a quien abre la caja" if plan["yo"]["dentro"] == "cubrir" else "abres tú la caja"), cambiar_dentro,
                            ayuda="Intro cambia. Si abres tú, tienes que estar junto a la caja hasta que ceda. Si cubres, la abre el de la caja y tú te quedas cerca, libre para pelear."))
        lista.append(Opcion(lambda: "Tú, en la huida: " + ("vas de pasajero" if plan["yo"]["huida"] == "pasajero" else "conduces tú"), cambiar_huida,
                            ayuda="Intro cambia. De pasajero conduce el conductor y tú disparas con la Q y Control. Si conduces tú, te encuentras el motor en marcha."))
        if any(papel(x) and papel(x)["efecto"] == "conductor" for x in plan["papeles"].values()):
            lista.append(Opcion(veh_txt, elegir_veh, ayuda="El conductor lo arrima a la puerta y te espera con el motor en marcha. Vale un vehículo tuyo que esté cerca, o uno de la banda."))
        lista.append(Opcion(partes_txt, ayuda="Cada uno cobra su parte al acabar, si el golpe sale bien. A quien detienen no cobra."))
        lista.append(Opcion(f"Empezar {que}", lanzar, ayuda="Con el plan como está. Hace falta que al menos uno de los tuyos tenga papel."))
        return lista
    m = Menu(app, lambda: f"Preparar {que}: {l.nombre}. Tienes al lado a {len(presentes())} de {p.j.banda_nombre or 'tu banda'}", ops,
             intro="Da un papel a cada uno. A quien no le des ninguno, viene contigo")
    app.abrir(m)
