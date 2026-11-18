"""Reconquista (1.7.1): conquistar no es el final. Las bandas vencidas se rehacen e intentan recuperar tus barrios.

Solo jugando sin conexión, y con la opción «Las bandas intentan reconquistar tus barrios» (Opciones, La calle) en
tranquilo, normal o duro. Cómo va:

- Empieza cuando tienes todos los barrios de una ciudad (fase plena; con todas las ciudades, algo más deprisa) o, más
  despacio, cuando tienes muchos sin tenerlos todos (fase suave). Antes hay unos días de calma, y un aviso, una vez.
- Cada banda tiene una fuerza que crece cada medianoche. Cuando llega a su umbral, prepara un asalto: elige barrio
  (su antiguo barrio, el peor defendido, el más abandonado, el más rentable) y, a veces, se alía con otra.
- Avisos: según tus informantes y la lealtad del barrio, te enteras con días de antelación, con uno, o no te enteras.
  Al empezar el asalto te enteras siempre.
- El asalto: unas horas para ir y defender en persona (oleadas, con lo de guerra.py), o para enviar a tu gente (cuenta
  de fuerza contra defensa, más la suerte, dicha con sus números). Si no haces nada, defiende la guardia fija si la hay;
  si no, el barrio se pierde. El plazo no corre en mitad de una misión, y dormir no lo agota de golpe.
- Defensa preventiva: guardia fija, refuerzos, informantes, tregua (pactos.py) y golpe al escondite de una banda.
- Lealtad de cada barrio: baja si no lo pisas, sube al visitarlo, defenderlo o invertir.
- Nunca dos asaltos a la vez, y siempre un descanso entre uno y otro.

Todo el estado va en Jugador.reconquista y se guarda con la partida. Los números y las frases salen de los datos
(data/datos/vida.json, sección reconquista).
"""
import random

from . import gente as G
from .ajustes import Ajustes

NIVELES = ("apagado", "tranquilo", "normal", "duro")
FASES = ("", "suave", "plena", "mundo")

AJ = Ajustes("reconquista", {
    "calma_min": 3, "calma_max": 5, "calma_carga": 3, "suave_barrios": 4, "suave_ritmo": 50, "mundo_ritmo": 125,
    "fuerza_inicial_min": 10, "fuerza_inicial_max": 35, "crece_min": 4, "crece_max": 8, "ritmo_tranquilo": 60, "ritmo_normal": 100, "ritmo_duro": 150,
    "fuerza_tranquilo": 85, "fuerza_normal": 100, "fuerza_duro": 115,
    "umbral_min": 45, "umbral_max": 65, "prepara_min": 2, "prepara_max": 3,
    "plazo_tranquilo": 18, "plazo_normal": 12, "plazo_duro": 8, "gracia_horas": 4, "hora_min": 9, "hora_max": 19,
    "descanso_tranquilo": 7, "descanso_normal": 4, "descanso_duro": 2, "descanso_azar": 2,
    "alianza_prob": 15, "alianza_fuerza": 30, "alianza_suma": 70,
    "peso_antiguo": 40, "peso_defensa": 35, "peso_abandono": 30, "peso_rentable": 20, "peso_azar": 15,
    "lealtad_inicial": 70, "lealtad_dias": 3, "lealtad_baja": 3, "lealtad_visita": 5, "lealtad_defensa": 15, "lealtad_inversion": 12,
    "lealtad_impago": 6, "lealtad_aviso": 45, "lealtad_grave": 25, "inversion_precio": 500,
    "guardia_max": 3, "guardia_coste": 60, "defensa_guardia": 14, "refuerzo_max": 3, "refuerzo_precio": 1500, "defensa_refuerzo": 12,
    "defensa_banda": 4, "defensa_lealtad": 20, "informante_max": 3, "informante_coste": 45, "rumor_prob": 40,
    "envio_banda": 8, "envio_azar": 15, "guardia_sola": 80, "baja_prob": 35,
    "oleadas": 2, "oleada_base": 3, "defensa_resta": 40, "fuerza_oleada_extra": 60, "fuerza_oleada_menos": 35,
    "premio_defensa": 800, "fama_defensa": 3, "fama_perdida": 5,
    "moral_gana": 25, "moral_pierde": 20, "fuerza_tras_ganar": 50, "fuerza_tras_perder": 35,
    "derrotas_desmantela": 3, "desmantela_min": 20, "desmantela_max": 30,
    "forastera_dias": 30, "forastera_fuerza": 30, "forastera_quedan": 2, "forastera_prob": 30,
    "golpe_fuerza_min": 20, "golpe_quita": 60, "golpe_espera": 4, "golpe_paga": 600,
}, {
    "forasteras": ["La Marea Negra", "Los del Norte", "Los Chacales del Estrecho", "La Hermandad del Faro", "Los Sin Santo"],
    "frases_inicio_todo": ["Has conquistado todos los barrios de {ciudad}, pero conquistar no es el final."],
    "frases_inicio_muchos": ["Tienes ya {n} barrios, y eso no pasa desapercibido."],
    "frases_inicio_carga": ["Aviso importante sobre tus barrios: desde esta versión, tenerlos no basta."],
    "frases_explicacion": ["Las bandas que has vencido se están rehaciendo y van a intentar recuperar lo suyo. Tienes {dias} de calma. "
                           "Después, cuando una banda asalte un barrio, tendrás unas horas para ir a defenderlo en persona o para enviar a tu gente desde el móvil; "
                           "si no haces nada, lo pierdes. Prepárate en el móvil, en Territorios, Defensa de tus barrios: allí pones guardias, refuerzas un barrio, "
                           "pagas informantes que te avisan con tiempo, pactas treguas y das golpes a los escondites. Y pisa tus barrios de vez en cuando: "
                           "uno abandonado cae antes. Si prefieres que no ocurra, se apaga en Opciones, La calle."],
    "frases_calma": ["Has conquistado todos los barrios de {ciudad}. Las bandas tardarán en levantar cabeza: tienes {dias} de calma."],
    "frases_rumor_vago": ["Se rumorea en la calle que alguna banda prepara algo contra uno de tus barrios, hoy mismo. Nadie sabe decirte más.",
                          "Hoy hay caras raras por la calle. Alguien trama algo contra tus barrios, pero no sabes dónde."],
    "frases_rumor": ["Rumor en la calle: alguien prepara un asalto a {barrio}, {cuando}. No se sabe quién.",
                     "Los vecinos de {barrio} han visto movimiento raro: algo se prepara allí para {cuando}."],
    "frases_chivatazo": ["Chivatazo: {banda} prepara un asalto a {barrio} para {cuando}.",
                         "Un informante te lo sopla: {banda} irá a por {barrio}, {cuando}."],
    "frases_mensaje": ["Mensaje al móvil de tu mejor informante: {banda} asaltará {barrio}, {cuando}, hacia las {hora}. Fuerza, unos {fuerza} de 100. {motivo}",
                       "Tu gente lo sabe todo: {banda} va a por {barrio}, {cuando}, sobre las {hora}, con una fuerza de {fuerza} de 100. {motivo}"],
    "frases_alianza": ["Y no van solos: {banda} y {aliada} se han aliado para un golpe grande.", "Es una alianza: {banda} y {aliada} juntan a su gente."],
    "frases_asalto": ["¡{banda} asalta {barrio}!", "¡Asalto! {banda} ha entrado en {barrio}.", "¡{banda} ha venido a por {barrio}!"],
    "frases_defendido": ["{banda} se retira de {barrio} con las manos vacías.", "{barrio} aguanta: {banda} sale por piernas.", "Nadie de {banda} se queda en {barrio}."],
    "frases_perdido": ["{banda} se ha quedado con {barrio}.", "Has perdido {barrio}: ahora manda {banda}.", "{barrio} cae: las esquinas vuelven a ser de {banda}."],
    "frases_desmantelada": ["{banda} no levanta cabeza: queda desmantelada una buena temporada.", "Después de tantos palos, {banda} se deshace. Tardará mucho en volver."],
    "frases_forastera": ["Llega gente nueva a la comarca: se hacen llamar {banda}, y vienen a por lo que es tuyo.",
                         "Se corre la voz: una banda de fuera, {banda}, se ha instalado en la comarca."],
    "frases_forastera_fin": ["{banda} recoge y se marcha de la comarca para siempre.", "De {banda} no queda nadie: se han ido por donde vinieron."],
    "frases_lealtad_aviso": ["En {barrio} empiezan a decir que no se te ve el pelo. Pásate por allí, o invierte en el barrio, antes de que vaya a más.",
                             "La gente de {barrio} se siente abandonada. Una visita, o algo de dinero para el barrio, lo arreglaría."],
    "frases_lealtad_grave": ["{barrio} está muy descuidado: allí ya casi nadie daría la cara por ti. Así caerá al primer asalto.",
                             "En {barrio} ya no te deben nada, dicen. Si no vas pronto, quien venga a quitártelo lo tendrá fácil."],
    "frases_golpe": ["El escondite de {banda} queda arrasado: pierden gente, armas y ganas.", "{banda} tardará en rehacerse de esta: les has dejado sin escondite."],
    "frases_golpe_suspende": ["Y el asalto que preparaban a {barrio} queda suspendido.", "Con esto, lo de {barrio} se les ha acabado antes de empezar."],
    "frases_tregua_rota": ["{banda} ha roto la tregua: vuelven a ir a por lo tuyo.", "Se acabó la tregua con {banda}: dicen que ya no les compensa."],
    "frases_tregua_fin": ["La tregua con {banda} termina hoy.", "Hoy vence lo pactado con {banda}: desde mañana, cada uno a lo suyo."],
}, cero=("alianza_prob", "rumor_prob", "baja_prob", "peso_antiguo", "peso_defensa", "peso_abandono", "peso_rentable", "peso_azar", "descanso_azar",
         "premio_defensa", "fama_defensa", "fama_perdida", "forastera_prob", "golpe_paga", "lealtad_baja", "lealtad_visita", "calma_carga",
         "defensa_banda", "defensa_lealtad", "defensa_resta", "lealtad_impago", "fuerza_inicial_min", "fuerza_inicial_max"))

MOTIVOS = {"antiguo": "Quieren recuperar el que fue su barrio.", "defensa": "Saben que es el peor defendido.",
           "abandono": "Saben que allí la gente está descontenta contigo.", "rentable": "Van a por el que más dinero te da.", "": ""}
EXPLICACION = ("Las bandas que has vencido se rehacen con los días e intentan recuperar tus barrios. Cuando una asalta un barrio, se te avisa siempre y tienes unas horas: "
               "ve allí y defiéndelo en persona, por oleadas y con tu banda a tu lado, o envía a tu gente desde este menú, y el resultado se calcula con su fuerza contra tu defensa, más la suerte. "
               "Si no haces nada, defiende sola la guardia fija, si la hay; si no, el barrio se pierde, con su dinero diario y algo de fama, y habrá que reconquistarlo. "
               "El plazo no corre mientras haces una misión, y si duermes o pasas por el hospital o el calabozo, tu gente aguanta: al volver te quedan siempre unas horas. "
               "La defensa de un barrio sube con guardias fijos, que cobran cada día, con refuerzos, que se pagan una vez, con su lealtad y con la gente de tu banda. "
               "La lealtad baja si pasan días sin que pises el barrio y sube al visitarlo, al defenderlo o al invertir en él. "
               "Los informantes cobran cada día y te avisan antes: sin ellos, te enteras tarde o cuando ya han llegado. "
               "Con una banda puedes pactar una tregua de unos días, o dar un golpe a su escondite para hundir su fuerza. "
               "Una banda vencida varias veces queda desmantelada una temporada larga, pero siempre acaba llegando alguien nuevo. "
               "Nunca hay dos asaltos a la vez y siempre hay unos días de descanso entre uno y otro. La intensidad se elige en Opciones, La calle: apagado, tranquilo, normal o duro.")


def _dias(n):
    return "un día" if int(n) == 1 else f"{int(n)} días"


def _cuando(faltan):
    return "hoy" if faltan <= 0 else "mañana" if faltan == 1 else f"dentro de {int(faltan)} días"


def _rato(minutos):
    m = max(0.0, float(minutos))
    if m >= 90:
        return f"{int(round(m / 60.0))} horas"
    return "una hora" if m >= 45 else f"{max(1, int(m))} minutos"


def _suerte(n):
    n = int(round(n))
    return f"{n} a favor" if n > 0 else f"{-n} en contra" if n < 0 else "ni a favor ni en contra"


def _y(nombres):
    nombres = list(nombres)
    return nombres[0] if len(nombres) == 1 else ", ".join(nombres[:-1]) + " y " + nombres[-1]


def probabilidad(diferencia, azar_max):
    """De 0 a 1: lo probable que es ganar con esa diferencia a favor, cuando cada bando suma una suerte de hasta azar_max."""
    if azar_max <= 0:
        return 1.0 if diferencia >= 0 else 0.0
    x = max(-1.0, min(1.0, diferencia / (2.0 * azar_max)))
    return max(0.0, min(1.0, 0.5 + x - x * abs(x) / 2.0))


class Reconquista:
    """Mixin de Partida."""

    def reconquista_iniciar(self):
        self._t_rec = 1.0
        self._rec_cargada = False

    # ------------------------------------------------------------------ estado
    def rec(self):
        r = self.j.reconquista
        if r.get("v") != 1:
            r.update({"v": 1, "visto": False, "calma": 0, "fase": "", "bandas": {}, "barrios": {}, "informantes": 0, "asalto": None, "descanso": 0,
                      "forastera_dia": self.dia, "ultima_forastera": "", "partes": []})
        return r

    def rec_nivel(self):
        """La intensidad en vigor: tranquilo, normal o duro. Vacío si está apagado, o si se juega en un servidor o con amigos."""
        n = self.cfg["reconquista"]
        if n not in NIVELES[1:] or getattr(self, "en_servidor", False) or self.online_activo():
            return ""
        return n

    def rec_barrios(self):
        """Tus barrios de ciudad, que son los que pueden asaltarte: [(mapa, barrio)]."""
        mios = set(self.j.territorios)
        return [(m, b) for m in self.mapas.values() if m.tipo == "ciudad" for b in m.barrios if b["id"] in mios]

    def rec_fase(self):
        """Cuánto tienes: vacío, suave (muchos barrios), plena (una ciudad entera) o mundo (todas)."""
        mios = set(self.j.territorios)
        ciudades = [m for m in self.mapas.values() if m.tipo == "ciudad" and m.barrios]
        total = sum(1 for m in ciudades for b in m.barrios if b["id"] in mios)
        if not total:
            return ""
        completas = [m for m in ciudades if all(b["id"] in mios for b in m.barrios)]
        if completas:
            return "mundo" if len(completas) == len(ciudades) else "plena"
        return "suave" if total >= AJ.entero("suave_barrios") else ""

    def rec_activa(self):
        """Hay reconquista en marcha: la opción está encendida y tienes barrios bastantes. Entonces los ataques de siempre no salen."""
        return bool(self.rec_nivel() and self.rec_fase())

    def rec_barrio(self, bid):
        r = self.rec()
        st = r["barrios"].get(bid)
        if st is None:
            st = r["barrios"][bid] = {"lealtad": float(AJ("lealtad_inicial")), "guardia": 0, "refuerzo": 0, "pisado": self.dia, "visita": 0, "inversion": 0, "de": ""}
        return st

    def rec_banda(self, nombre):
        r = self.rec()
        b = r["bandas"].get(nombre)
        if b is None:
            b = r["bandas"][nombre] = {"fuerza": round(AJ.entre("fuerza_inicial_min", "fuerza_inicial_max"), 1), "moral": 0.0, "derrotas": 0, "fuera": 0, "tregua": 0, "golpe": -99,
                                       "umbral": round(AJ.entre("umbral_min", "umbral_max"), 1)}
        return b

    def rec_nombres(self):
        """Las bandas que cuentan: las de la comarca y, si ha llegado alguna, las forasteras."""
        nativas = G.nombres_bandas()
        return nativas + [n for n, b in self.rec()["bandas"].items() if b.get("forastera") and n not in nativas]

    def rec_buscar(self, bid):
        """(mapa, barrio) de un barrio por su identificador, o (None, None)."""
        for m in self.mapas.values():
            for b in m.barrios:
                if b["id"] == bid:
                    return m, b
        return None, None

    def rec_origen(self, b, mapa=None):
        """La banda que tenía ese barrio antes que tú, o la que siempre le ha tenido ganas."""
        return self.rec_barrio(b["id"]).get("de") or b.get("banda") or self.banda_interesada(b, mapa)

    def rec_defensa(self, bid):
        """La defensa de un barrio tuyo, de 0 a 100: guardias, refuerzos, lealtad y la gente de tu banda."""
        st = self.rec_barrio(bid)
        return max(0.0, min(100.0, st["guardia"] * AJ("defensa_guardia") + st["refuerzo"] * AJ("defensa_refuerzo")
                            + st["lealtad"] / 100.0 * AJ("defensa_lealtad") + self.j.banda * AJ("defensa_banda")))

    def rec_renta(self, b, mapa):
        """Lo que te da un barrio al día: su tributo y lo que ingresan los negocios que tengas en él."""
        negocios = sum(int(l.get("ingresos", 0)) for l in mapa.lugares.values()
                       if l.tipo == "negocio" and l.id in self.j.propiedades and mapa.barrio(l.x, l.y)["id"] == b["id"])
        return self.precio("tributo_territorio", 300) + negocios

    def _rec_parte(self, texto):
        r = self.rec()
        r["partes"].append(f"Día {self.dia}: {texto}")
        del r["partes"][:-8]

    def _rec_decir(self, texto, sonido=None, interrumpir=False):
        if sonido:
            self.son(sonido, cat="interfaz")
        self.decir(texto, interrumpir)
        self._rec_parte(texto)

    # ------------------------------------------------------------------ cuándo empieza
    def reconquista_revisar(self):
        """Mira si ha cambiado lo que tienes: al conquistarlo todo (o mucho) empieza la cuenta, con sus días de calma y su aviso."""
        if not self.rec_nivel():
            return
        fase = self.rec_fase()
        r = self.j.reconquista
        if not fase and not r.get("v"):
            return
        r = self.rec()
        antes = r["fase"]
        if fase == antes:
            return
        r["fase"] = fase
        if FASES.index(fase) <= FASES.index(antes):
            return                                               # has perdido terreno: nada que anunciar
        mios = set(self.j.territorios)
        ciudad = next((m.nombre for m in self.mapas.values() if m.tipo == "ciudad" and m.barrios and all(b["id"] in mios for b in m.barrios)), "")
        if fase == "mundo":
            ciudad = "todas las ciudades"
        if not antes:
            r["forastera_dia"] = self.dia
        cargada, self._rec_cargada = self._rec_cargada, False
        dias = AJ.entero("calma_carga") if cargada else random.randint(*sorted((AJ.entero("calma_min"), AJ.entero("calma_max"))))
        if fase == "suave" and r["visto"]:
            return
        r["calma"] = max(r["calma"], self.dia + dias)
        a = r["asalto"]
        if a and a["estado"] == "prepara":                       # lo que estuvieran tramando espera a que pase la calma
            a["dia"] = max(a["dia"], r["calma"] + 1)
        for m, b in self.rec_barrios():
            self.rec_barrio(b["id"])["pisado"] = max(self.rec_barrio(b["id"])["pisado"], self.dia)
        if not r["visto"]:
            r["visto"] = True
            cabeza = AJ.frase("frases_inicio_carga") if cargada else AJ.frase("frases_inicio_muchos", n=len(mios)) if fase == "suave" else AJ.frase("frases_inicio_todo", ciudad=ciudad)
            self._rec_decir(f"{cabeza} {AJ.frase('frases_explicacion', dias=_dias(dias))}", "amenaza_barrio")
        else:
            self._rec_decir(AJ.frase("frases_calma", ciudad=ciudad, dias=_dias(dias)), "notificacion")

    # ------------------------------------------------------------------ cada medianoche
    def dia_reconquista(self, azar=random):
        nivel = self.rec_nivel()
        if not nivel:
            return
        self.reconquista_revisar()
        if not self.j.reconquista.get("v"):
            return
        r = self.rec()
        mios = set(self.j.territorios)
        for bid, st in r["barrios"].items():                     # en un barrio que ya no es tuyo no queda guardia
            if bid not in mios:
                st["guardia"] = 0
        self._rec_cobros()
        if not r["fase"]:
            return
        self._rec_lealtad()
        self._rec_treguas(azar)
        if self.dia <= r["calma"]:
            return
        self._rec_crecer(azar, nivel)
        self._rec_forastera(azar)
        if r["asalto"]:
            self._rec_avisar(azar)
        elif self.dia > r["descanso"] and not self.j.amenaza and self.dia > self.j.pacto_hasta:
            self._rec_planear(azar, nivel)

    def _rec_cobros(self):
        """Los guardias fijos y los informantes cobran cada medianoche. Si no llega, se van."""
        r, j = self.rec(), self.j
        guardias = sum(st["guardia"] for bid, st in r["barrios"].items() if bid in j.territorios)
        total_g = guardias * AJ.entero("guardia_coste")
        total_i = r["informantes"] * AJ.entero("informante_coste")
        if not total_g + total_i:
            return
        if j.dinero >= total_g + total_i:
            j.dinero -= total_g + total_i
            partes = ([f"{total_g} euros a los {guardias} guardias de tus barrios" if guardias > 1 else f"{total_g} euros al guardia de tu barrio"] if total_g else []) \
                + ([f"{total_i} euros a tus informantes"] if total_i else [])
            self.decir("Pagas " + " y ".join(partes) + ".")
            return
        if total_i:
            r["informantes"] = 0
        if j.dinero >= total_g:
            j.dinero -= total_g
            self._rec_decir("No te llega para pagar a tus informantes, y dejan de trabajar para ti." + (f" A los guardias sí: {total_g} euros." if total_g else ""), "error")
            return
        for bid, st in r["barrios"].items():
            if st["guardia"]:
                st["guardia"] = 0
                st["lealtad"] = max(0.0, st["lealtad"] - AJ("lealtad_impago"))
        self._rec_decir("No te llega para pagar a los guardias de tus barrios" + (" ni a tus informantes" if total_i else "") + ": se marchan todos, y en esos barrios sienta mal.", "error")

    def rec_impago(self):
        """No has podido pagar a tu banda: en tus barrios se sabe."""
        if not self.rec_activa():
            return
        for m, b in self.rec_barrios():
            st = self.rec_barrio(b["id"])
            st["lealtad"] = max(0.0, st["lealtad"] - AJ("lealtad_impago"))

    def _rec_lealtad(self):
        aviso, grave = [], []
        for m, b in self.rec_barrios():
            st = self.rec_barrio(b["id"])
            if self.dia - st["pisado"] <= AJ("lealtad_dias"):
                continue
            antes = st["lealtad"]
            st["lealtad"] = max(0.0, antes - AJ("lealtad_baja") * (0.5 if st["guardia"] else 1.0))
            if antes >= AJ("lealtad_grave") > st["lealtad"]:
                grave.append(b["nombre"])
            elif antes >= AJ("lealtad_aviso") > st["lealtad"]:
                aviso.append(b["nombre"])
        if grave:
            self._rec_decir(AJ.frase("frases_lealtad_grave", barrio=_y(grave)), "amenaza_barrio")
        if aviso:
            self._rec_decir(AJ.frase("frases_lealtad_aviso", barrio=_y(aviso)), "notificacion")

    def _rec_treguas(self, azar):
        r = self.rec()
        for nombre in self.rec_nombres():
            b = r["bandas"].get(nombre)
            if not b or not b["tregua"]:
                continue
            if self.dia > b["tregua"]:
                b["tregua"] = 0
                self._rec_decir(AJ.frase("frases_tregua_fin", banda=nombre), "notificacion")
            elif azar.random() * 100 < self.tregua_rompe_prob():
                b["tregua"] = 0
                r["descanso"] = max(r["descanso"], self.dia + 2)   # romperla no les da derecho a golpear al día siguiente
                self.cambiar_rep_banda(nombre, -5, hablar=False)
                self._rec_decir(AJ.frase("frases_tregua_rota", banda=nombre), "amenaza_barrio")

    def _rec_crecer(self, azar, nivel):
        r = self.rec()
        ritmo = AJ(f"ritmo_{nivel}") / 100.0 * {"suave": AJ("suave_ritmo") / 100.0, "mundo": AJ("mundo_ritmo") / 100.0}.get(r["fase"], 1.0)
        for nombre in self.rec_nombres():
            b = self.rec_banda(nombre)
            b["moral"] = round(b["moral"] * 0.9, 2)
            if self.dia <= b["fuera"] or nombre in self.j.tributos:
                continue                                         # desmantelada, o te paga por estar tranquila
            g = AJ.entre("crece_min", "crece_max", azar) * ritmo * (1.0 + b["moral"] / 100.0)
            if self.dia <= b["tregua"] or self.rep_banda(nombre) >= 30:
                g *= 0.5
            b["fuerza"] = round(max(0.0, min(100.0, b["fuerza"] + max(0.0, g))), 1)

    def _rec_forastera(self, azar):
        r = self.rec()
        if r["fase"] not in ("plena", "mundo") or any(b.get("forastera") for b in r["bandas"].values()):
            return
        nativas = G.nombres_bandas()
        vivas = sum(1 for n in nativas if self.dia > self.rec_banda(n)["fuera"])
        if vivas > AJ("forastera_quedan") and self.dia - r["forastera_dia"] < AJ("forastera_dias"):
            return
        if azar.random() * 100 >= AJ("forastera_prob"):
            return
        nombres = [n for n in AJ.lista("forasteras") if n not in nativas and n != r["ultima_forastera"]] or [n for n in AJ.lista("forasteras") if n not in nativas]
        if not nombres:
            return
        nombre = azar.choice(nombres)
        r["bandas"][nombre] = {"fuerza": float(AJ("forastera_fuerza")), "moral": 0.0, "derrotas": 0, "fuera": 0, "tregua": 0, "golpe": -99,
                               "umbral": round(AJ.entre("umbral_min", "umbral_max", azar), 1), "forastera": True}
        r["ultima_forastera"], r["forastera_dia"] = nombre, self.dia
        self._rec_decir(AJ.frase("frases_forastera", banda=nombre), "amenaza_barrio")

    # ------------------------------------------------------------------ el plan de un asalto
    def rec_elegir_objetivo(self, banda, azar=random):
        """El barrio al que irá una banda y por qué: (mapa, barrio, motivo). El motivo es lo que más ha pesado."""
        barrios = self.rec_barrios()
        if not barrios:
            return None, None, ""
        rentas = {b["id"]: self.rec_renta(b, m) for m, b in barrios}
        tope, suelo = max(rentas.values()), min(rentas.values())
        fichas = []
        for m, b in barrios:
            st = self.rec_barrio(b["id"])
            partes = {"antiguo": AJ("peso_antiguo") if self.rec_origen(b, m) == banda else 0.0,
                      "defensa": AJ("peso_defensa") * (100.0 - self.rec_defensa(b["id"])) / 100.0,
                      "abandono": AJ("peso_abandono") * (100.0 - st["lealtad"]) / 100.0,
                      "rentable": AJ("peso_rentable") * ((rentas[b["id"]] - suelo) / (tope - suelo) if tope > suelo else 0.0)}
            fichas.append((sum(partes.values()) + azar.uniform(0, AJ("peso_azar")), m, b, partes))
        total, m, b, partes = max(fichas, key=lambda f: f[0])
        # el motivo que se cuenta es aquello en lo que ese barrio destaca sobre los demás
        medias = {k: sum(f[3][k] for f in fichas) / len(fichas) for k in partes} if len(fichas) > 1 else dict.fromkeys(partes, 0.0)
        motivo = max(partes, key=lambda k: partes[k] - medias[k])
        return m, b, motivo if partes[motivo] - medias[motivo] > 0 else ""

    def _rec_listas(self):
        """Las bandas que pueden lanzar un asalto ahora: ni desmanteladas, ni en tregua, ni pagándote tributo."""
        return [n for n in self.rec_nombres() if self.dia > self.rec_banda(n)["fuera"] and self.dia > self.rec_banda(n)["tregua"] and n not in self.j.tributos]

    def _rec_planear(self, azar, nivel):
        r = self.rec()
        listas = self._rec_listas()
        cand = [n for n in listas if self.rec_banda(n)["fuerza"] >= self.rec_banda(n)["umbral"]]
        if not cand:
            return
        banda = max(cand, key=lambda n: self.rec_banda(n)["fuerza"] + azar.uniform(0, 10))
        b = self.rec_banda(banda)
        mapa, barrio, motivo = self.rec_elegir_objetivo(banda, azar)
        if barrio is None:
            return
        bandas, fuerza = [banda], b["fuerza"]
        otras = [n for n in listas if n != banda and self.rec_banda(n)["fuerza"] >= AJ("alianza_fuerza")]
        if otras and azar.random() * 100 < AJ("alianza_prob"):
            aliada = azar.choice(otras)
            bandas.append(aliada)
            fuerza += self.rec_banda(aliada)["fuerza"] * AJ("alianza_suma") / 100.0
        b["umbral"] = round(AJ.entre("umbral_min", "umbral_max", azar), 1)
        prepara = azar.randint(*sorted((AJ.entero("prepara_min"), AJ.entero("prepara_max"))))
        r["asalto"] = {"barrio": barrio["id"], "nombre": barrio["nombre"], "mapa": mapa.id, "ciudad": mapa.nombre, "bandas": bandas,
                       "fuerza": round(fuerza * AJ(f"fuerza_{nivel}") / 100.0, 1), "dia": self.dia + prepara,
                       "hora": azar.randint(*sorted((AJ.entero("hora_min"), AJ.entero("hora_max")))), "motivo": motivo,
                       "estado": "prepara", "sabido": 0, "quedan": 0.0, "plazo": float(AJ(f"plazo_{nivel}")) * 60.0, "gracia": False, "avisos": []}
        self._rec_avisar(azar)

    def rec_calidad_aviso(self, bid):
        """Lo bien informado que estás sobre un barrio, de 0 a 3: tus informantes, o lo que te cuente su gente si te es leal."""
        st = self.rec_barrio(bid)
        vecinos = 2 if st["lealtad"] >= 75 else 1 if st["lealtad"] >= 50 else 0
        return max(int(self.rec()["informantes"]), vecinos)

    def _rec_avisar(self, azar=random):
        """Lo que llegas a saber de un asalto que se prepara: depende de tus informantes y de la lealtad del barrio."""
        a = self.rec()["asalto"]
        if not a or a["estado"] != "prepara":
            return
        faltan = a["dia"] - self.dia
        q = self.rec_calidad_aviso(a["barrio"])
        sabe = 3 if q >= 3 else 2 if q == 2 and faltan <= 2 else 1 if q >= 1 and faltan <= 1 else 0
        donde = a["nombre"] + (f", en {a['ciudad']}" if a["mapa"] != self.mundo.id else "")
        if sabe > a["sabido"]:
            a["sabido"] = sabe
            if sabe == 3:
                texto = AJ.frase("frases_mensaje", azar, banda=a["bandas"][0], barrio=donde, cuando=_cuando(faltan), hora=a["hora"], fuerza=int(a["fuerza"]), motivo=MOTIVOS.get(a["motivo"], ""))
            elif sabe == 2:
                texto = AJ.frase("frases_chivatazo", azar, banda=a["bandas"][0], barrio=donde, cuando=_cuando(faltan))
            else:
                texto = AJ.frase("frases_rumor", azar, barrio=donde, cuando=_cuando(faltan))
            if sabe >= 2 and len(a["bandas"]) > 1:
                texto += " " + AJ.frase("frases_alianza", azar, banda=a["bandas"][0], aliada=a["bandas"][1])
            self._rec_decir(texto.strip() + " Mira qué puedes hacer en el móvil, en Territorios, Defensa de tus barrios.", "amenaza_barrio")
        elif not a["sabido"] and faltan <= 0 and "vago" not in a["avisos"]:
            a["avisos"].append("vago")
            if azar.random() * 100 < AJ("rumor_prob"):
                self._rec_decir(AJ.frase("frases_rumor_vago", azar), "amenaza_barrio")

    # ------------------------------------------------------------------ el asalto
    def actualizar_reconquista(self, dt):
        self._t_rec -= dt
        if self._t_rec <= 0:
            self._t_rec = 2.0
            if self.rec_nivel():
                self.reconquista_revisar()
                self._rec_pisar()
        r = self.j.reconquista
        a = r.get("asalto")
        if not a or not self.rec_nivel():
            return
        atraso = (self.dia - a["dia"]) * 1440.0 + self.reloj - a["hora"] * 60.0
        if self.mision:                                          # en mitad de una misión, ni empieza el asalto ni corre el plazo
            if a["estado"] == "prepara" and atraso >= 0:
                a["espera"] = True                               # tocaba empezar: esperan a que acabes, y ese rato no cuenta
            return
        if a["estado"] == "prepara":
            if atraso >= 0:
                self._rec_empezar_asalto(0.0 if a.pop("espera", False) else atraso)
            return
        g = self.guerra
        if g and g.get("rec"):
            return                                               # estás allí peleando: el plazo espera
        a["quedan"] -= dt / 2.0
        if a["quedan"] <= 0:
            self._rec_vence()
            return
        for marca, minutos in (("2h", 120.0), ("30m", 30.0)):
            if a["quedan"] <= minutos and marca not in a["avisos"] and a["plazo"] > minutos:
                a["avisos"].append(marca)
                self.son("amenaza_barrio", cat="interfaz")
                self.decir(f"Quedan {_rato(a['quedan'])} para que {a['nombre']} caiga. Ve allí, o envía a tu gente desde el móvil, en Territorios.")
        if not g and self.t > self.t_guerra_enfria and self.mundo.id == a["mapa"] and self.puede_guerra(True) and self.mundo.barrio(*self.pos())["id"] == a["barrio"]:
            self.rec_defender_en_persona()

    def _rec_pisar(self):
        """Estás en un barrio tuyo: cuenta como visita, y la primera del día sube su lealtad."""
        r = self.j.reconquista
        if not r.get("v") or self.mundo.tipo != "ciudad":
            return
        bid = self.mundo.barrio(*self.pos())["id"]
        if bid not in self.j.territorios:
            return
        st = self.rec_barrio(bid)
        st["pisado"] = self.dia
        if st["visita"] != self.dia:
            st["visita"] = self.dia
            st["lealtad"] = min(100.0, st["lealtad"] + AJ("lealtad_visita"))

    def _rec_empezar_asalto(self, atraso=0.0):
        r = self.rec()
        a = r["asalto"]
        if a["barrio"] not in self.j.territorios:                # ya no es tuyo (lo devolviste, lo perdiste de otra forma): no hay nada que asaltar
            r["asalto"] = None
            return
        a["estado"], a["sabido"] = "en_curso", 3
        gracia = AJ("gracia_horas") * 60.0
        a["gracia"] = a["plazo"] - atraso < gracia                # empezó mientras dormías o estabas fuera, y ya se ha gastado el margen
        a["quedan"] = max(gracia, a["plazo"] - max(0.0, atraso))
        donde = a["nombre"] + (f", en {a['ciudad']}" if a["mapa"] != self.mundo.id else "")
        texto = AJ.frase("frases_asalto", banda=_y(a["bandas"]), barrio=donde)
        if len(a["bandas"]) > 1:
            texto += " " + AJ.frase("frases_alianza", banda=a["bandas"][0], aliada=a["bandas"][1])
        if atraso > 30:
            texto += " Empezó mientras no estabas, y tu gente ha aguantado como ha podido."
        texto += (f" Tienes {_rato(a['quedan'])}: ve allí y defiéndelo en persona, la pelea empieza al entrar en el barrio, o abre el móvil, Territorios, y envía a tu gente. "
                  + ("Si no haces nada, defenderá sola la guardia del barrio." if self.rec_barrio(a["barrio"])["guardia"] else "Si no haces nada, lo pierdes."))
        self._rec_decir(texto, "amenaza_barrio")

    def rec_pasar_horas(self, horas):
        """Pasan horas de golpe (dormir, hospital, calabozo, un viaje): el plazo corre, pero la primera vez tu gente aguanta
        y al volver te quedan siempre unas horas. Nadie pierde un barrio por dormir una noche."""
        a = self.j.reconquista.get("asalto")
        if not a or a["estado"] != "en_curso" or not self.rec_nivel() or self.mision or (self.guerra and self.guerra.get("rec")):
            return                                               # en una misión, o peleando allí mismo, el plazo no corre
        nuevo = a["quedan"] - horas * 60.0
        gracia = AJ("gracia_horas") * 60.0
        if horas >= 3 and nuevo < gracia and not a["gracia"]:     # un rato corto (un trayecto, una comida) pasa sin más
            a["gracia"] = True
            nuevo = min(a["quedan"], gracia)
            self.son("amenaza_barrio", cat="interfaz")
            self.decir(f"Mientras no estabas, tu gente ha aguantado en {a['nombre']}, pero no puede más: te quedan {_rato(nuevo)} para defenderlo o enviar refuerzos.")
        a["quedan"] = nuevo

    def rec_plan_persona(self):
        """Cómo será la defensa en persona del asalto en curso: (oleadas, enemigos de la primera)."""
        a = self.rec()["asalto"]
        efectiva = max(0.0, a["fuerza"] - self.rec_defensa(a["barrio"]) * AJ("defensa_resta") / 100.0)
        oleadas = AJ.entero("oleadas") + (1 if efectiva >= AJ("fuerza_oleada_extra") else 0) + (1 if len(a["bandas"]) > 1 else 0)
        base = AJ.entero("oleada_base") - (1 if efectiva < AJ("fuerza_oleada_menos") else 0) + (1 if self.rec_nivel() == "duro" else 0)
        return max(1, min(5, oleadas)), max(2, base)

    def rec_defender_en_persona(self):
        a = self.rec()["asalto"]
        if not a or a["estado"] != "en_curso" or self.mundo.id != a["mapa"]:
            return False
        b = next((x for x in self.mundo.barrios if x["id"] == a["barrio"]), None)
        if b is None:
            return False
        oleadas, base = self.rec_plan_persona()
        return self.empezar_guerra(b, True, a["bandas"][0], rec={"oleadas": oleadas, "base": base, "bandas": list(a["bandas"])})

    def rec_posibilidades(self, modo="gente"):
        """De 0 a 1: lo probable que es que tu gente (o la guardia sola) aguante el asalto en curso."""
        a = self.rec()["asalto"]
        if not a:
            return 0.0
        return probabilidad(self._rec_poder(modo) - a["fuerza"], AJ("envio_azar"))

    def _rec_poder(self, modo):
        a = self.rec()["asalto"]
        base = self.rec_defensa(a["barrio"])
        return base + self.j.banda * AJ("envio_banda") if modo == "gente" else base * AJ("guardia_sola") / 100.0

    def rec_enviar_gente(self, azar=random):
        """Mandas a tu banda a defender el barrio asaltado. Devuelve (hecho, frase)."""
        a = self.j.reconquista.get("asalto")
        if not a or a["estado"] != "en_curso":
            return False, "Ahora mismo nadie está asaltando un barrio tuyo."
        if self.j.banda < 1:
            return False, "No tienes a nadie en tu banda a quien enviar. Recluta gente en Territorios, Tu banda, o ve tú en persona."
        if self.guerra and self.guerra.get("rec"):
            return False, "Ya estás tú allí, peleando."
        return True, self._rec_calculo("gente", azar)

    def _rec_calculo(self, modo, azar=random):
        """La defensa sin ti: fuerza contra defensa, más la suerte de cada bando. Lo cuenta con sus números."""
        j = self.j
        a = self.rec()["asalto"]
        base = self.rec_defensa(a["barrio"])
        poder = self._rec_poder(modo)
        az = AJ("envio_azar")
        sd, sa = azar.uniform(-az, az), azar.uniform(-az, az)
        td, ta = poder + sd, a["fuerza"] + sa
        texto = f"{_y(a['bandas'])} ataca {a['nombre']} con una fuerza de {int(round(a['fuerza']))}. "
        if modo == "gente":
            texto += (f"Tu defensa suma {int(round(poder))}: {int(round(base))} del barrio y {int(round(poder - base))} de "
                      + ("el único que envías" if j.banda == 1 else f"los {j.banda} que envías") + ". ")
        else:
            texto += f"No has ido ni has enviado a nadie: defiende sola la guardia del barrio, con {int(round(poder))}. "
        texto += f"La suerte: {_suerte(sd)} para los tuyos, y {_suerte(sa)} para ellos. Resultado: {int(round(td))} contra {int(round(ta))}. "
        gana = td >= ta
        if modo == "gente" and j.banda > 0 and (not gana or td - ta < 10) and azar.random() * 100 < AJ("baja_prob"):
            j.banda -= 1
            texto += f"En la pelea cae uno de los tuyos: te quedan {j.banda}. "
        if gana:
            self.rec_defendido(modo, texto)
        else:
            self._rec_perdido(texto)
        return texto

    def _rec_vence(self):
        """Se acabó el plazo sin que hicieras nada: defiende la guardia fija, si la hay; si no, el barrio cae."""
        a = self.rec()["asalto"]
        if a["barrio"] not in self.j.territorios:
            self.rec()["asalto"] = None
            return
        if self.rec_barrio(a["barrio"])["guardia"]:
            self._rec_calculo("guardia")
        else:
            self._rec_perdido(f"Nadie ha defendido {a['nombre']}. ")

    def _rec_cerrar_asalto(self):
        r = self.rec()
        nivel = self.rec_nivel() or "normal"
        r["asalto"] = None
        r["descanso"] = self.dia + AJ.entero(f"descanso_{nivel}") + random.randint(0, AJ.entero("descanso_azar"))

    def rec_defendido(self, modo, texto="", g=None):
        """El asalto ha fracasado: en persona, con tu gente o con la guardia sola."""
        j = self.j
        a = self.rec()["asalto"]
        if not a:
            return
        st = self.rec_barrio(a["barrio"])
        st["lealtad"] = min(100.0, st["lealtad"] + AJ("lealtad_defensa"))
        st["pisado"] = self.dia
        frase = AJ.frase("frases_defendido", banda=_y(a["bandas"]), barrio=a["nombre"])
        self.son("barrio_defendido", cat="interfaz")
        j.stats["asaltos_rechazados"] = j.stats.get("asaltos_rechazados", 0) + 1
        self._rec_cerrar_asalto()
        extra = []
        for nombre in a["bandas"]:
            b = self.rec_banda(nombre)
            b["fuerza"] = round(b["fuerza"] * AJ("fuerza_tras_perder") / 100.0, 1)
            b["moral"] = max(-50.0, b["moral"] - AJ("moral_pierde"))
            b["derrotas"] += 1
            self.cambiar_rep_banda(nombre, -2, hablar=False)
            fin = self._rec_desmantelar(nombre)
            if fin:
                extra.append(fin)
        self._rec_decir(" ".join([texto.strip(), frase, f"{a['nombre']} sigue siendo tuyo."] + extra).strip(), None, modo != "persona")
        self.cambiar_reputacion(AJ("fama_defensa"))
        if modo == "persona":
            j.stats["defensas"] = j.stats.get("defensas", 0) + 1
            premio = int(AJ("premio_defensa") * (0.5 if self.cfg["mod_dinero"] else 1.0))
            if premio:
                self.dar_dinero(premio, "Lo que se han dejado en la huida")
            self.cambiar_animo(4)
            from . import menus_juego
            menus_juego.autoguardar(self)

    def _rec_desmantelar(self, nombre):
        """Si la banda ya ha encajado bastantes derrotas, queda fuera de juego una temporada (y la forastera se va). Devuelve la frase, o vacío."""
        r = self.rec()
        b = self.rec_banda(nombre)
        if b["derrotas"] < AJ("derrotas_desmantela"):
            return ""
        if b.get("forastera"):
            del r["bandas"][nombre]
            r["forastera_dia"] = self.dia
            return AJ.frase("frases_forastera_fin", banda=nombre)
        dias = random.randint(*sorted((AJ.entero("desmantela_min"), AJ.entero("desmantela_max"))))
        b.update(fuerza=0.0, moral=0.0, derrotas=0, fuera=self.dia + dias, tregua=0)
        return AJ.frase("frases_desmantelada", banda=nombre) + f" No sabrás de ellos en unos {dias} días."

    def _rec_perdido(self, texto=""):
        j = self.j
        a = self.rec()["asalto"]
        if not a:
            return
        bid, banda = a["barrio"], a["bandas"][0]
        if self.guerra and self.guerra.get("rec"):
            self.guerra_retirada(callar=True)
        self._rec_cerrar_asalto()
        if bid in j.territorios:
            j.territorios.remove(bid)
        j.barrios_banda[bid] = banda
        st = self.rec_barrio(bid)
        st.update(guardia=0, refuerzo=max(0, st["refuerzo"] - 1), de=banda)
        for nombre in a["bandas"]:
            b = self.rec_banda(nombre)
            b["fuerza"] = round(b["fuerza"] * AJ("fuerza_tras_ganar") / 100.0, 1)
            b["moral"] = min(100.0, b["moral"] + AJ("moral_gana"))
            b["derrotas"] = max(0, b["derrotas"] - 1)
        j.stats["barrios_perdidos"] = j.stats.get("barrios_perdidos", 0) + 1
        self.son("barrio_perdido", cat="interfaz")
        self._rec_decir(f"{texto.strip()} {AJ.frase('frases_perdido', banda=banda, barrio=a['nombre'])} Pierdes los {self.precio('tributo_territorio', 300)} euros que te daba cada medianoche, "
                        "y algo de fama. Puedes reconquistarlo como cualquier otro barrio, en el móvil, en Territorios.".strip(), None, True)
        self.cambiar_reputacion(-AJ("fama_perdida"))
        self.reconquista_revisar()

    # ------------------------------------------------------------------ defensa preventiva
    def rec_guardia(self, bid, d):
        """Contrata (d=1) o despide (d=-1) a un guardia fijo de un barrio. Devuelve la frase."""
        st = self.rec_barrio(bid)
        coste = AJ.entero("guardia_coste")
        if d > 0:
            if st["guardia"] >= AJ.entero("guardia_max"):
                self.app.son("error")
                return f"Ese barrio ya tiene los {AJ.entero('guardia_max')} guardias que admite."
            if not self.pagar(coste):
                return ""
            st["guardia"] += 1
            return f"Contratado. Ahora hay {st['guardia']} de guardia fija, a {coste} euros cada uno cada medianoche. Defensa del barrio: {int(self.rec_defensa(bid))} de 100."
        if st["guardia"] <= 0:
            self.app.son("error")
            return "En ese barrio no hay guardia fija."
        st["guardia"] -= 1
        return f"Despides a uno. Quedan {st['guardia']} de guardia fija. Defensa del barrio: {int(self.rec_defensa(bid))} de 100."

    def rec_precio_refuerzo(self, bid):
        st = self.rec_barrio(bid)
        return AJ.entero("refuerzo_precio") * (st["refuerzo"] + 1) if st["refuerzo"] < AJ.entero("refuerzo_max") else 0

    def rec_reforzar(self, bid):
        st = self.rec_barrio(bid)
        precio = self.rec_precio_refuerzo(bid)
        if not precio:
            self.app.son("error")
            return "Ese barrio ya está reforzado al máximo."
        if not self.pagar(precio):
            return ""
        st["refuerzo"] += 1
        st["lealtad"] = min(100.0, st["lealtad"] + 5)
        return f"Hecho: refuerzo de nivel {st['refuerzo']} de {AJ.entero('refuerzo_max')}. Puertas, vigías y gente del barrio pagada para avisar. Defensa: {int(self.rec_defensa(bid))} de 100."

    def rec_invertir(self, bid):
        st = self.rec_barrio(bid)
        if st["inversion"] == self.dia:
            self.app.son("error")
            return "Hoy ya has puesto dinero en este barrio. Mañana, más."
        if st["lealtad"] >= 100:
            self.app.son("error")
            return "La gente de este barrio ya está contigo a muerte: no hace falta."
        if not self.pagar(AJ.entero("inversion_precio")):
            return ""
        st["inversion"] = self.dia
        st["lealtad"] = min(100.0, st["lealtad"] + AJ("lealtad_inversion"))
        self.son("prestigio", cat="interfaz")
        return f"Arreglas lo que hace falta y se nota. Lealtad del barrio: {int(st['lealtad'])} de 100."

    def rec_informantes(self, d):
        """Sube o baja el nivel de tus informantes. Subir cuesta ya el primer día."""
        r = self.rec()
        nuevo = max(0, min(AJ.entero("informante_max"), r["informantes"] + d))
        if nuevo == r["informantes"]:
            self.app.son("error")
            return "No hay más niveles." if d > 0 else "Ya no tienes informantes."
        if nuevo > r["informantes"] and not self.pagar(AJ.entero("informante_coste")):
            return ""
        r["informantes"] = nuevo
        self._rec_avisar()
        return (f"Informantes de nivel {nuevo}: {AJ.entero('informante_coste') * nuevo} euros cada medianoche. " + self.rec_informantes_txt(nuevo)) if nuevo else "Despides a tus informantes."

    @staticmethod
    def rec_informantes_txt(nivel):
        return ("Sin informantes: te enteras el mismo día, si acaso por un rumor, o cuando ya han llegado.", "Te llega el rumor un día antes, con el barrio.",
                "Chivatazo dos días antes, con la banda y el barrio.", "Lo sabes en cuanto lo deciden: banda, barrio, día, hora y fuerza.")[max(0, min(3, int(nivel)))]

    def golpe_motivo(self, banda):
        """Por qué no puedes dar ahora un golpe al escondite de esa banda, o vacío."""
        b = self.rec_banda(banda)
        if self.mundo.tipo != "ciudad":
            return "Los escondites están en las ciudades. Ve a una."
        if self.mision or self.trabajo or self.guerra:
            return "Termina antes lo que tienes entre manos."
        if self.j.estrellas:
            return "Con la policía detrás no es momento."
        if self.dia <= b["fuera"]:
            return f"{banda} está desmantelada: no hay a quién golpear."
        falta = int(b["golpe"]) + AJ.entero("golpe_espera") - self.dia
        if falta > 0:
            return f"Después del último golpe, {banda} se ha escondido bien. Tus fuentes tardarán {_dias(falta)} en dar con ellos."
        if b["fuerza"] < AJ("golpe_fuerza_min"):
            return f"{banda} está tan deshecha que no tiene ni escondite que asaltar."
        return ""

    def empezar_golpe(self, banda):
        """Golpe preventivo: una misión corta contra el escondite de una banda que se está rehaciendo. Cada vez, de una manera."""
        if self.golpe_motivo(banda):
            return False
        b = self.rec_banda(banda)
        r = self.rec()
        ls = [l for l in self.mundo.lugares.values() if l.tipo not in ("salida", "embarcadero")]
        fuera = [l for l in ls if self.mundo.barrio(l.x, l.y)["id"] not in self.j.territorios]
        ls = fuera if len(fuera) >= 2 else ls
        if len(ls) < 2:
            return False
        l1, l2 = random.sample(ls, 2)
        tipos, refuerzo = G.tipos_de_banda(banda)
        if refuerzo and G.tipo_enemigo(refuerzo).get("vehiculo") not in self.modelos:
            refuerzo = None
        n = max(3, min(6, 3 + int(b["fuerza"] // 30)))

        def grupo(clase, cuantos, mas=0):
            t = G.tipo_enemigo(clase)
            if not t:
                return {"n": cuantos, "tipo": f"Pandillero de {banda}", "arma": random.choice(["pistola", "pistola", "subfusil", "bate"]), "salud": 70 + mas}
            return {"n": cuantos, "clase": clase, "tipo": f"{t.get('nombre', 'Pandillero')} de {banda}", "salud": float(t.get("salud", 70)) + mas}
        base, duro = (tipos[0], tipos[-1]) if tipos else ("", "")
        variante = random.choice(["directo", "vigias", "arsenal"] + (["refuerzos"] if refuerzo else []))
        if variante == "directo":
            pasos = [{"tipo": "eliminar", "lugar": l1.id, "texto": f"{banda} se esconde junto a {l1.nombre}: son {n}. Entra y no dejes a nadie.",
                      "enemigos": [grupo(base, n - 1), grupo(duro, 1, 15)]}]
        elif variante == "vigias":
            pasos = [{"tipo": "eliminar", "lugar": l1.id, "texto": f"Primero, los vigías de {banda}: 2, junto a {l1.nombre}. Que no den la voz.", "enemigos": [grupo(base, 2)]},
                     {"tipo": "eliminar", "lugar": l2.id, "texto": f"Ya no hay quien avise. El escondite está junto a {l2.nombre}: quedan {n - 1}.", "enemigos": [grupo(base, max(1, n - 2)), grupo(duro, 1, 15)]}]
        elif variante == "arsenal":
            pasos = [{"tipo": "eliminar", "lugar": l1.id, "texto": f"{banda} guarda sus armas junto a {l1.nombre}, con {n - 1} de guardia. Acaba con ellos.", "enemigos": [grupo(base, max(1, n - 2)), grupo(duro, 1, 10)]},
                     {"tipo": "recoger", "lugar": l1.id, "objeto": "La caja de armas", "texto": "Despejado. Busca la caja de armas y llévatela: sin ella no son nadie."}]
        else:
            llegan = min(max(1, n - 2), int(G.tipo_enemigo(refuerzo).get("ocupantes", 3) or 3))
            pasos = [{"tipo": "eliminar", "lugar": l1.id, "texto": f"El escondite de {banda} está junto a {l1.nombre}: {n} en total, y {llegan} de ellos llegarán en un vehículo en cuanto empiece. Escucha el motor.",
                      "enemigos": [g for g in (grupo(base, n - llegan - 1), grupo(duro, 1, 10), grupo(refuerzo, llegan, 5)) if g["n"] > 0]}]
        b["golpe"] = self.dia
        if self.dia <= b["tregua"]:                              # golpear a una banda con la que tienes tregua la rompe
            b["tregua"] = 0
            b["moral"] = min(100.0, b["moral"] + 15)
            self.cambiar_rep_banda(banda, -15, hablar=False)
            self._rec_decir(f"Con este golpe rompes la tregua con {banda}. No lo olvidarán.", "amenaza_barrio")

        def hecho():
            r, b = self.rec(), self.rec_banda(banda)             # tras reintentar la misión, el estado guardado es otro: se pide otra vez
            b["golpe"] = self.dia
            quita = AJ("golpe_quita") / 100.0
            b["fuerza"] = round(b["fuerza"] * (1.0 - quita), 1)
            b["moral"] = max(-50.0, b["moral"] - 10)
            b["derrotas"] += 1
            self.cambiar_rep_banda(banda, -8, hablar=False)
            texto = AJ.frase("frases_golpe", banda=banda)
            a = r["asalto"]
            if a and a["estado"] == "prepara" and banda in a["bandas"]:
                if a["bandas"][0] == banda:
                    r["asalto"] = None
                    r["descanso"] = max(r["descanso"], self.dia + 2)
                    texto += " " + AJ.frase("frases_golpe_suspende", barrio=a["nombre"])
                else:
                    a["bandas"].remove(banda)
                    a["fuerza"] = round(a["fuerza"] * 0.6, 1)
                    texto += f" {a['bandas'][0]} se queda sin su aliada."
            fin = self._rec_desmantelar(banda)
            self._rec_decir((texto + " " + fin).strip(), "barrio_defendido")
        self._empezar_repetible({"id": "golpe_preventivo", "titulo": f"Golpe al escondite de {banda}", "lugar": l1.id, "contador": "golpes_preventivos", "banda": banda,
                                 "variante": variante, "pasos": pasos, "recompensa": {"dinero": AJ.entero("golpe_paga")}, "al_completar": hecho})
        return True

    # ------------------------------------------------------------------ lo que se sabe, dicho con palabras
    def rec_asalto_de(self, bid):
        a = self.j.reconquista.get("asalto")
        return a if a and a["barrio"] == bid else None

    def rec_asalto_txt(self):
        """Lo que dice la tecla O mientras asaltan un barrio tuyo. Vacío si no hay asalto en curso."""
        a = self.j.reconquista.get("asalto")
        if not a or a["estado"] != "en_curso" or not self.rec_nivel():
            return ""
        return (f"{_y(a['bandas'])} está asaltando {a['nombre']}" + (f", en {a['ciudad']}" if a["mapa"] != self.mundo.id else "")
                + f". Te quedan {_rato(a['quedan'])}: ve allí y defiéndelo, o envía a tu gente desde el móvil, en Territorios.")

    def rec_amenaza_txt(self, bid):
        """El estado de amenaza de un barrio tuyo, que siempre se puede consultar. Los detalles dependen de lo que sepas."""
        r = self.rec()
        a = self.rec_asalto_de(bid)
        if a and a["estado"] == "en_curso":
            return f"¡asalto en curso de {_y(a['bandas'])}! Quedan {_rato(a['quedan'])}"
        if a:
            cuando = _cuando(a["dia"] - self.dia)
            if a["sabido"] >= 3:
                return f"{_y(a['bandas'])} lo asaltará {cuando}, hacia las {a['hora']}, con una fuerza de {int(a['fuerza'])} de 100"
            if a["sabido"] == 2:
                return f"{a['bandas'][0]} prepara un asalto para {cuando}"
            if a["sabido"] == 1:
                return f"se rumorea un asalto para {cuando}"
            return "alta: se nota movimiento raro por sus calles"
        if not r["fase"]:
            return "ninguna, de momento"
        if self.dia <= r["calma"]:
            return f"baja: las bandas siguen lamiéndose las heridas, hasta el día {r['calma']}"
        listas = self._rec_listas()
        fuerte = max((self.rec_banda(n)["fuerza"] for n in listas), default=0.0)
        riesgo = fuerte / max(1.0, AJ("umbral_max")) * (0.5 + 0.5 * (100.0 - self.rec_defensa(bid)) / 100.0)
        return "baja" if riesgo < 0.35 else "media" if riesgo < 0.7 else "alta"

    @staticmethod
    def rec_fuerza_txt(f):
        return "deshecha" if f < 15 else "rehaciéndose" if f < 35 else "con gente otra vez" if f < 55 else "fuerte" if f < 75 else "muy fuerte, lista para golpear"

    def rec_banda_txt(self, nombre):
        b = self.rec_banda(nombre)
        if self.dia <= b["fuera"]:
            return f"{nombre}: desmantelada hasta el día {b['fuera']}"
        partes = [self.rec_fuerza_txt(b["fuerza"]) + (f", fuerza {int(b['fuerza'])} de 100" if self.rec()["informantes"] >= 2 else "")]
        if b.get("forastera"):
            partes.append("banda forastera")
        if self.dia <= b["tregua"]:
            partes.append(f"en tregua contigo hasta el día {b['tregua']}")
        if nombre in self.j.tributos:
            partes.append("te paga tributo y no ataca")
        if b["derrotas"]:
            partes.append(f"lleva {b['derrotas']} de {AJ.entero('derrotas_desmantela')} derrotas para quedar desmantelada")
        return f"{nombre}: " + ", ".join(partes)

    def rec_estado_txt(self):
        r = self.rec()
        nivel = self.rec_nivel()
        if not nivel:
            return "Reconquista: apagada o no disponible aquí"
        if not r["fase"]:
            return f"Reconquista, nivel {nivel}: todavía no. Empieza al tener todos los barrios de una ciudad, o {AJ.entero('suave_barrios')} barrios en total"
        fase = {"suave": "tienes muchos barrios: las bandas se mueven despacio", "plena": "tienes una ciudad entera: las bandas quieren recuperarla",
                "mundo": "tienes todas las ciudades: todas las bandas van a por ti"}[r["fase"]]
        if r["asalto"] and r["asalto"]["estado"] == "en_curso":
            cola = "hay un asalto en curso"
        elif self.dia <= r["calma"]:
            cola = f"calma hasta el día {r['calma']}. Hoy es el día {self.dia}"
        elif self.dia <= r["descanso"]:
            cola = f"las bandas descansan tras el último asalto, al menos hasta el día {r['descanso']}"
        else:
            cola = "las bandas se están rehaciendo"
        return f"Reconquista, nivel {nivel}: {fase}; {cola}"


# ====================================================================== menús
def menu_reconquista(p):
    """Móvil, Territorios, Defensa de tus barrios: todo lo de la reconquista, por menú."""
    from .menus import Menu, Opcion
    app, j = p.app, p.j
    r = p.rec()

    def decir(f, *a):
        def g():
            t = f(*a)
            t = t[1] if isinstance(t, tuple) else t
            if t:
                app.decir(t, True)
            for mm in app.pila:
                if isinstance(mm, Menu) and mm is not app.pila[0]:
                    mm.refrescar(False)
        return g

    def ir(a):
        def f():
            mapa, b = p.rec_buscar(a["barrio"])
            l = p.lugar_de_barrio(b, mapa) if b else None
            while app.pila and app.pila[-1] is not p:
                app.cerrar(app.pila[-1])
            if l is not None:
                p.gps_a_lugar(l)
            app.decir(f"{_y(a['bandas'])} está en {a['nombre']}" + (f", en {a['ciudad']}" if a["mapa"] != p.mundo.id else "") + f". Ve allí: la defensa empieza en cuanto entres en el barrio. Te quedan {_rato(a['quedan'])}.", True)
        return f

    def enviar():
        hecho, texto = p.rec_enviar_gente()
        if not hecho:
            app.son("error")
        app.decir(texto, True)
        m.refrescar(False)

    def barrio(mapa, b):
        def f():
            bid = b["id"]
            st = p.rec_barrio(bid)

            def gps():
                l = p.lugar_de_barrio(b, mapa)
                while app.pila and app.pila[-1] is not p:
                    app.cerrar(app.pila[-1])
                if l is not None:
                    p.gps_a_lugar(l)
                app.decir(f"Marcado: {l.nombre if l else b['nombre']}, en {b['nombre']}. Con pasar por allí ya cuenta como visita.", True)
            mb = Menu(app, lambda: f"{b['nombre']}, en {mapa.nombre}. Lealtad {int(st['lealtad'])} de 100, defensa {int(p.rec_defensa(bid))} de 100. Amenaza: {p.rec_amenaza_txt(bid)}", lambda: [
                Opcion(lambda: f"Guardia fija: {st['guardia']} de {AJ.entero('guardia_max')}. Contratar a uno más, {AJ.entero('guardia_coste')} euros al día", decir(p.rec_guardia, bid, 1),
                       ayuda="Gente que se queda en el barrio. Cada guardia sube la defensa, cobra cada medianoche y hace que la lealtad baje la mitad de deprisa. "
                             "Si te asaltan y no haces nada, la guardia defiende sola; sin guardia, el barrio se pierde. Si una medianoche no puedes pagarles, se van. Pagas el primer día al contratar."),
                Opcion("Despedir a un guardia", decir(p.rec_guardia, bid, -1), ayuda="Uno menos que pagar cada medianoche, y menos defensa."),
                Opcion(lambda: (f"Reforzar el barrio: nivel {st['refuerzo']} de {AJ.entero('refuerzo_max')}. Subir cuesta {p.rec_precio_refuerzo(bid)} euros, una sola vez"
                                if p.rec_precio_refuerzo(bid) else f"Reforzar el barrio: ya está al máximo, nivel {st['refuerzo']}"), decir(p.rec_reforzar, bid),
                       ayuda="Una mejora que se paga una vez y se queda: vigías, puertas y gente avisada. Cada nivel sube la defensa, y cada nivel cuesta más que el anterior. "
                             "Con más defensa, quien te asalte lo tiene peor contra tu gente, y si vas tú, vienen menos en cada oleada. Si pierdes el barrio, pierde un nivel."),
                Opcion(lambda: f"Invertir en el barrio: {AJ.entero('inversion_precio')} euros. Tienes {j.dinero}", decir(p.rec_invertir, bid),
                       ayuda="Dinero para la gente del barrio: sube su lealtad. Una vez al día por barrio. Un barrio leal se defiende mejor, es menos tentador para las bandas, "
                             "y sus vecinos te avisan de lo que se prepara aunque no pagues informantes."),
                Opcion("Marcarlo en el GPS para visitarlo", gps, ayuda="La lealtad baja si pasan días sin que pises el barrio, y sube la primera vez que entras en él cada día."),
            ])
            app.abrir(mb)
        return f

    def banda(nombre):
        def f():
            def golpe():
                motivo = p.golpe_motivo(nombre)
                if motivo:
                    app.son("error")
                    return app.decir(motivo, True)

                def ya():
                    if not p.empezar_golpe(nombre):
                        app.son("error")
                        app.decir("Aquí no hay dónde dar el golpe.", True)
                if p.dia <= p.rec_banda(nombre)["tregua"]:
                    return app.abrir(Menu(app, f"Tienes una tregua con {nombre}. Si das el golpe, la rompes", [Opcion("Dar el golpe de todas formas", ya), Opcion("Dejarlo", lambda: app.cerrar())]))
                ya()

            def tregua():
                from . import pactos
                pactos.menu_tregua(p, nombre, lambda: [mm.refrescar(False) for mm in app.pila if isinstance(mm, Menu) and mm is not app.pila[0]])
            mb = Menu(app, lambda: p.rec_banda_txt(nombre), [
                Opcion(lambda: f"Dar un golpe a su escondite. Paga {AJ.entero('golpe_paga')} euros", golpe,
                       ayuda=f"Una misión corta, cada vez distinta, en la ciudad en la que estés: asaltas el escondite donde se están rehaciendo. Si la cumples, pierden el {AJ.entero('golpe_quita')} por ciento de su fuerza, "
                             "cuenta como una derrota y, si eran ellos quienes preparaban un asalto, se suspende. Hace falta que tengan fuerza bastante para tener escondite, "
                             f"y no se puede repetir contra la misma banda hasta pasados {_dias(AJ.entero('golpe_espera'))}. Si tienes una tregua con ellos, la rompes."),
                Opcion(lambda: f"Pactar una tregua con {nombre}" if p.dia > p.rec_banda(nombre)["tregua"] else f"Tregua en vigor hasta el día {p.rec_banda(nombre)['tregua']}", tregua,
                       ayuda="Les pagas y durante unos días no asaltan tus barrios, y se rehacen la mitad de deprisa. Si estaban preparando un asalto, lo dejan. "
                             "Piden más cuanto más fuertes están y peor os lleváis; se puede regatear una vez. La tregua se puede romper: ellos, algún día, sin avisar antes, o tú, si das un golpe a su escondite."),
            ])
            app.abrir(mb)
        return f

    def informantes(d=1):
        t = p.rec_informantes(d)
        if t:
            app.decir(t, True)

    def partes():
        app.decir("Últimos partes. " + " ".join(reversed(r["partes"])) if r["partes"] else "Todavía no ha pasado nada que contar.", True)

    def ops():
        lista = [Opcion(lambda: p.rec_estado_txt(), lambda: app.decir(EXPLICACION, True),
                        ayuda="Pulsa Intro para oír cómo funciona todo. " + EXPLICACION)]
        a = r["asalto"]
        if a and a["estado"] == "en_curso":
            lista.append(Opcion(lambda: f"Asalto a {a['nombre']}: ir en persona. Quedan {_rato(a['quedan'])}", ir(a),
                                ayuda="Marca el barrio en el GPS. La defensa empieza al entrar en él: vienen por oleadas, cada una más dura, y tu banda acude a tu lado. "
                                      "Mientras peleas, el plazo no corre. Si sales del barrio o caes, el asalto sigue y puedes volver a intentarlo o enviar a tu gente."))
            lista.append(Opcion(lambda: (f"Enviar a tu gente a defender {a['nombre']}: unas {int(round(p.rec_posibilidades() * 10))} de cada 10 posibilidades" if j.banda
                                         else f"Enviar a tu gente a defender {a['nombre']}: no tienes a nadie en la banda"), enviar,
                                ayuda="Tu banda va sin ti y el resultado se calcula al momento: la fuerza de ellos contra la defensa del barrio más lo que suma cada uno de los tuyos, y la suerte de cada bando. "
                                      "Se te dice con sus números. Puede caer alguno de los tuyos. Si sale mal, pierdes el barrio."))
        elif a and a["sabido"] >= 1:
            lista.append(Opcion(lambda: f"Lo que sabes: {a['nombre']}, {p.rec_amenaza_txt(a['barrio'])}",
                                ayuda="Aún no ha empezado. Puedes reforzar ese barrio, ponerle guardia, pactar una tregua con esa banda o dar un golpe a su escondite antes de que llegue el día."))
        for mapa, b in p.rec_barrios():
            lista.append(Opcion(lambda b=b, mapa=mapa: f"{b['nombre']}, en {mapa.nombre}: lealtad {int(p.rec_barrio(b['id'])['lealtad'])}, defensa {int(p.rec_defensa(b['id']))}, "
                                f"guardias {p.rec_barrio(b['id'])['guardia']}. Amenaza: {p.rec_amenaza_txt(b['id'])}", barrio(mapa, b),
                                ayuda="Intro abre el barrio: guardia fija, refuerzos, invertir y marcarlo en el GPS. La lealtad y la defensa van de 0 a 100. "
                                      "La amenaza se puede consultar siempre; con informantes, o con el barrio de tu parte, sabrás además quién viene y cuándo."))
        lista.append(Opcion(lambda: f"Informantes: nivel {r['informantes']} de {AJ.entero('informante_max')}, {AJ.entero('informante_coste') * r['informantes']} euros al día. {p.rec_informantes_txt(r['informantes'])}",
                            lambda: informantes(1), ajuste=None,
                            ayuda="Intro sube un nivel; la opción siguiente lo baja. Cada nivel cuesta lo mismo cada medianoche, y el primer día se paga al contratar. "
                                  "Nivel 1: el rumor, un día antes. Nivel 2: chivatazo dos días antes, con la banda, y ves la fuerza exacta de cada banda. Nivel 3: mensaje al móvil en cuanto lo deciden, con día, hora y fuerza. "
                                  "Sin informantes, un barrio con mucha lealtad también te avisa: con 50, como el nivel 1; con 75, como el 2. Si una medianoche no puedes pagarles, se van."))
        lista.append(Opcion("Bajar un nivel de informantes", lambda: informantes(-1), ayuda="Pagas menos cada medianoche y te enteras más tarde."))
        for nombre in p.rec_nombres():
            lista.append(Opcion(lambda nombre=nombre: p.rec_banda_txt(nombre), banda(nombre),
                                ayuda="Intro abre lo que puedes hacer con esta banda: darle un golpe a su escondite o pactar una tregua. "
                                      "Su fuerza crece cada día; cuando es bastante, prepara un asalto. Con informantes de nivel 2 ves la cifra exacta."))
        lista.append(Opcion("Últimos partes: lo que ha ido pasando", partes, ayuda="Los últimos avisos, asaltos y resultados, por si se te pasó alguno."))
        return lista
    m = Menu(app, "Defensa de tus barrios", ops, intro="F1 explica cada opción. La primera, con Intro, cuenta cómo funciona todo")
    app.abrir(m)


def opciones_territorios(p, Opcion):
    """Lo que la reconquista pone en el menú de Territorios: el asalto en curso, arriba del todo, y la entrada a la defensa."""
    if not p.rec_nivel():
        return [], []
    r = p.rec()
    a = r["asalto"]
    arriba = []
    if a and a["estado"] == "en_curso":
        arriba.append(Opcion(lambda: f"¡Asalto a {a['nombre']}! {_y(a['bandas'])}. Quedan {_rato(a['quedan'])}: defenderlo", lambda: menu_reconquista(p),
                             ayuda="Abre Defensa de tus barrios: desde allí marcas el barrio en el GPS para ir en persona, o envías a tu gente. Si no haces nada antes de que se acabe el plazo, "
                                   "defiende sola la guardia fija, si la hay; si no, lo pierdes."))
    abajo = [Opcion(lambda: "Defensa de tus barrios. " + p.rec_estado_txt(), lambda: menu_reconquista(p),
                    ayuda="Las bandas que has vencido intentan recuperar tus barrios. Aquí ves la amenaza, la lealtad y la defensa de cada uno, pones guardias y refuerzos, pagas informantes, "
                          "pactas treguas, das golpes a los escondites y, cuando te asaltan, envías a tu gente. Dentro, la primera opción lo explica todo.")]
    return arriba, abajo
