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
from .i18n import tr
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
    "forasteras": [tr("La Marea Negra"), tr("Los del Norte"), tr("Los Chacales del Estrecho"), tr("La Hermandad del Faro"), tr("Los Sin Santo")],
    "frases_inicio_todo": [tr("Has conquistado todos los barrios de {ciudad}, pero conquistar no es el final.")],
    "frases_inicio_muchos": [tr("Tienes ya {n} barrios, y eso no pasa desapercibido.")],
    "frases_inicio_carga": [tr("Aviso importante sobre tus barrios: desde esta versión, tenerlos no basta.")],
    "frases_explicacion": [tr("Las bandas que has vencido se están rehaciendo y van a intentar recuperar lo suyo. Tienes {dias} de calma. "
                           "Después, cuando una banda asalte un barrio, tendrás unas horas para ir a defenderlo en persona o para enviar a tu gente desde el móvil; "
                           "si no haces nada, lo pierdes. Prepárate en el móvil, en Territorios, Defensa de tus barrios: allí pones guardias, refuerzas un barrio, "
                           "pagas informantes que te avisan con tiempo, pactas treguas y das golpes a los escondites. Y pisa tus barrios de vez en cuando: "
                           "uno abandonado cae antes. Si prefieres que no ocurra, se apaga en Opciones, La calle.")],
    "frases_calma": [tr("Has conquistado todos los barrios de {ciudad}. Las bandas tardarán en levantar cabeza: tienes {dias} de calma.")],
    "frases_rumor_vago": [tr("Se rumorea en la calle que alguna banda prepara algo contra uno de tus barrios, hoy mismo. Nadie sabe decirte más."),
                          tr("Hoy hay caras raras por la calle. Alguien trama algo contra tus barrios, pero no sabes dónde.")],
    "frases_rumor": [tr("Rumor en la calle: alguien prepara un asalto a {barrio}, {cuando}. No se sabe quién."),
                     tr("Los vecinos de {barrio} han visto movimiento raro: algo se prepara allí para {cuando}.")],
    "frases_chivatazo": [tr("Chivatazo: {banda} prepara un asalto a {barrio} para {cuando}."),
                         tr("Un informante te lo sopla: {banda} irá a por {barrio}, {cuando}.")],
    "frases_mensaje": [tr("Mensaje al móvil de tu mejor informante: {banda} asaltará {barrio}, {cuando}, hacia las {hora}. Fuerza, unos {fuerza} de 100. {motivo}"),
                       tr("Tu gente lo sabe todo: {banda} va a por {barrio}, {cuando}, sobre las {hora}, con una fuerza de {fuerza} de 100. {motivo}")],
    "frases_alianza": [tr("Y no van solos: {banda} y {aliada} se han aliado para un golpe grande."), tr("Es una alianza: {banda} y {aliada} juntan a su gente.")],
    "frases_asalto": [tr("¡{banda} asalta {barrio}!"), tr("¡Asalto! {banda} ha entrado en {barrio}."), tr("¡{banda} ha venido a por {barrio}!")],
    "frases_defendido": [tr("{banda} se retira de {barrio} con las manos vacías."), tr("{barrio} aguanta: {banda} sale por piernas."), tr("Nadie de {banda} se queda en {barrio}.")],
    "frases_perdido": [tr("{banda} se ha quedado con {barrio}."), tr("Has perdido {barrio}: ahora manda {banda}."), tr("{barrio} cae: las esquinas vuelven a ser de {banda}.")],
    "frases_desmantelada": [tr("{banda} no levanta cabeza: queda desmantelada una buena temporada."), tr("Después de tantos palos, {banda} se deshace. Tardará mucho en volver.")],
    "frases_forastera": [tr("Llega gente nueva a la comarca: se hacen llamar {banda}, y vienen a por lo que es tuyo."),
                         tr("Se corre la voz: una banda de fuera, {banda}, se ha instalado en la comarca.")],
    "frases_forastera_fin": [tr("{banda} recoge y se marcha de la comarca para siempre."), tr("De {banda} no queda nadie: se han ido por donde vinieron.")],
    "frases_lealtad_aviso": [tr("En {barrio} empiezan a decir que no se te ve el pelo. Pásate por allí, o invierte en el barrio, antes de que vaya a más."),
                             tr("La gente de {barrio} se siente abandonada. Una visita, o algo de dinero para el barrio, lo arreglaría.")],
    "frases_lealtad_grave": [tr("{barrio} está muy descuidado: allí ya casi nadie daría la cara por ti. Así caerá al primer asalto."),
                             tr("En {barrio} ya no te deben nada, dicen. Si no vas pronto, quien venga a quitártelo lo tendrá fácil.")],
    "frases_golpe": [tr("El escondite de {banda} queda arrasado: pierden gente, armas y ganas."), tr("{banda} tardará en rehacerse de esta: les has dejado sin escondite.")],
    "frases_golpe_suspende": [tr("Y el asalto que preparaban a {barrio} queda suspendido."), tr("Con esto, lo de {barrio} se les ha acabado antes de empezar.")],
    "frases_tregua_rota": [tr("{banda} ha roto la tregua: vuelven a ir a por lo tuyo."), tr("Se acabó la tregua con {banda}: dicen que ya no les compensa.")],
    "frases_tregua_fin": [tr("La tregua con {banda} termina hoy."), tr("Hoy vence lo pactado con {banda}: desde mañana, cada uno a lo suyo.")],
}, cero=("alianza_prob", "rumor_prob", "baja_prob", "peso_antiguo", "peso_defensa", "peso_abandono", "peso_rentable", "peso_azar", "descanso_azar",
         "premio_defensa", "fama_defensa", "fama_perdida", "forastera_prob", "golpe_paga", "lealtad_baja", "lealtad_visita", "calma_carga",
         "defensa_banda", "defensa_lealtad", "defensa_resta", "lealtad_impago", "fuerza_inicial_min", "fuerza_inicial_max"))

MOTIVOS = {"antiguo": tr("Quieren recuperar el que fue su barrio."), "defensa": tr("Saben que es el peor defendido."),
           "abandono": tr("Saben que allí la gente está descontenta contigo."), "rentable": tr("Van a por el que más dinero te da."), "": ""}
EXPLICACION = (tr("Las bandas que has vencido se rehacen con los días e intentan recuperar tus barrios. Cuando una asalta un barrio, se te avisa siempre y tienes unas horas: "
               "ve allí y defiéndelo en persona, por oleadas y con tu banda a tu lado, o envía a tu gente desde este menú, y el resultado se calcula con su fuerza contra tu defensa, más la suerte. "
               "Si no haces nada, defiende sola la guardia fija, si la hay; si no, el barrio se pierde, con su dinero diario y algo de fama, y habrá que reconquistarlo. "
               "El plazo no corre mientras haces una misión, y si duermes o pasas por el hospital o el calabozo, tu gente aguanta: al volver te quedan siempre unas horas. "
               "La defensa de un barrio sube con guardias fijos, que cobran cada día, con refuerzos, que se pagan una vez, con su lealtad y con la gente de tu banda. "
               "La lealtad baja si pasan días sin que pises el barrio y sube al visitarlo, al defenderlo o al invertir en él. "
               "Los informantes cobran cada día y te avisan antes: sin ellos, te enteras tarde o cuando ya han llegado. "
               "Con una banda puedes pactar una tregua de unos días, o dar un golpe a su escondite para hundir su fuerza. "
               "Una banda vencida varias veces queda desmantelada una temporada larga, pero siempre acaba llegando alguien nuevo. "
               "Nunca hay dos asaltos a la vez y siempre hay unos días de descanso entre uno y otro. La intensidad se elige en Opciones, La calle: apagado, tranquilo, normal o duro."))


def _dias(n):
    return tr("un día") if int(n) == 1 else tr('{int} días').format(int=(int(n)))


def _cuando(faltan):
    return tr("hoy") if faltan <= 0 else tr("mañana") if faltan == 1 else tr('dentro de {int} días').format(int=(int(faltan)))


def _rato(minutos):
    m = max(0.0, float(minutos))
    if m >= 90:
        return tr('{int} horas').format(int=(int(round(m / 60.0))))
    return tr("una hora") if m >= 45 else tr('{max} minutos').format(max=(max(1, int(m))))


def _suerte(n):
    n = int(round(n))
    return tr('{n} a favor').format(n=(n)) if n > 0 else tr('{v} en contra').format(v=(-n)) if n < 0 else tr("ni a favor ni en contra")


def _y(nombres):
    nombres = list(nombres)
    return nombres[0] if len(nombres) == 1 else ", ".join(nombres[:-1]) + tr(" y ") + nombres[-1]


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
        r["partes"].append(tr('Día {dia}: {texto}').format(dia=(self.dia), texto=(texto)))
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
            ciudad = tr("todas las ciudades")
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
            partes = ([tr('{total_g} euros a los {guardias} guardias de tus barrios').format(total_g=(total_g), guardias=(guardias)) if guardias > 1 else tr('{total_g} euros al guardia de tu barrio').format(total_g=(total_g))] if total_g else []) \
                + ([tr('{total_i} euros a tus informantes').format(total_i=(total_i))] if total_i else [])
            self.decir(tr("Pagas ") + tr(" y ").join(partes) + ".")
            return
        if total_i:
            r["informantes"] = 0
        if j.dinero >= total_g:
            j.dinero -= total_g
            self._rec_decir(tr("No te llega para pagar a tus informantes, y dejan de trabajar para ti.") + (tr(' A los guardias sí: {total_g} euros.').format(total_g=(total_g)) if total_g else ""), "error")
            return
        for bid, st in r["barrios"].items():
            if st["guardia"]:
                st["guardia"] = 0
                st["lealtad"] = max(0.0, st["lealtad"] - AJ("lealtad_impago"))
        self._rec_decir(tr("No te llega para pagar a los guardias de tus barrios") + (tr(" ni a tus informantes") if total_i else "") + tr(": se marchan todos, y en esos barrios sienta mal."), "error")

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
        donde = a["nombre"] + (tr(', en {ciudad}').format(ciudad=(a['ciudad'])) if a["mapa"] != self.mundo.id else "")
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
            self._rec_decir(texto.strip() + tr(" Mira qué puedes hacer en el móvil, en Territorios, Defensa de tus barrios."), "amenaza_barrio")
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
                self.decir(tr('Quedan {_rato} para que {nombre} caiga. Ve allí, o envía a tu gente desde el móvil, en Territorios.').format(_rato=(_rato(a['quedan'])), nombre=(a['nombre'])))
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
        donde = a["nombre"] + (tr(', en {ciudad}').format(ciudad=(a['ciudad'])) if a["mapa"] != self.mundo.id else "")
        texto = AJ.frase("frases_asalto", banda=_y(a["bandas"]), barrio=donde)
        if len(a["bandas"]) > 1:
            texto += " " + AJ.frase("frases_alianza", banda=a["bandas"][0], aliada=a["bandas"][1])
        if atraso > 30:
            texto += tr(" Empezó mientras no estabas, y tu gente ha aguantado como ha podido.")
        texto += (tr(' Tienes {_rato}: ve allí y defiéndelo en persona, la pelea empieza al entrar en el barrio, o abre el móvil, Territorios, y envía a tu gente. ').format(_rato=(_rato(a['quedan'])))
                  + (tr("Si no haces nada, defenderá sola la guardia del barrio.") if self.rec_barrio(a["barrio"])["guardia"] else tr("Si no haces nada, lo pierdes.")))
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
            self.decir(tr('Mientras no estabas, tu gente ha aguantado en {nombre}, pero no puede más: te quedan {_rato} para defenderlo o enviar refuerzos.').format(nombre=(a['nombre']), _rato=(_rato(nuevo))))
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
            return False, tr("Ahora mismo nadie está asaltando un barrio tuyo.")
        if self.j.banda < 1:
            return False, tr("No tienes a nadie en tu banda a quien enviar. Recluta gente en Territorios, Tu banda, o ve tú en persona.")
        if self.guerra and self.guerra.get("rec"):
            return False, tr("Ya estás tú allí, peleando.")
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
        texto = tr('{_y} ataca {nombre} con una fuerza de {int}. ').format(_y=(_y(a['bandas'])), nombre=(a['nombre']), int=(int(round(a['fuerza']))))
        if modo == "gente":
            texto += (tr('Tu defensa suma {int}: {int2} del barrio y {int3} de ').format(int=(int(round(poder))), int2=(int(round(base))), int3=(int(round(poder - base))))
                      + (tr("el único que envías") if j.banda == 1 else tr('los {banda} que envías').format(banda=(j.banda))) + ". ")
        else:
            texto += tr('No has ido ni has enviado a nadie: defiende sola la guardia del barrio, con {int}. ').format(int=(int(round(poder))))
        texto += tr('La suerte: {_suerte} para los tuyos, y {_suerte2} para ellos. Resultado: {int} contra {int2}. ').format(_suerte=(_suerte(sd)), _suerte2=(_suerte(sa)), int=(int(round(td))), int2=(int(round(ta))))
        gana = td >= ta
        if modo == "gente" and j.banda > 0 and (not gana or td - ta < 10) and azar.random() * 100 < AJ("baja_prob"):
            j.banda -= 1
            texto += tr('En la pelea cae uno de los tuyos: te quedan {banda}. ').format(banda=(j.banda))
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
            self._rec_perdido(tr('Nadie ha defendido {nombre}. ').format(nombre=(a['nombre'])))

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
        self._rec_decir(" ".join([texto.strip(), frase, tr("{nombre} sigue siendo tuyo.").format(nombre=a['nombre'])] + extra).strip(), None, modo != "persona")
        self.cambiar_reputacion(AJ("fama_defensa"))
        if modo == "persona":
            j.stats["defensas"] = j.stats.get("defensas", 0) + 1
            premio = int(AJ("premio_defensa") * (0.5 if self.cfg["mod_dinero"] else 1.0))
            if premio:
                self.dar_dinero(premio, tr("Lo que se han dejado en la huida"))
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
        return AJ.frase("frases_desmantelada", banda=nombre) + tr(' No sabrás de ellos en unos {dias} días.').format(dias=(dias))

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
        self._rec_decir(tr('{strip} {frase} Pierdes los {precio} euros que te daba cada medianoche, y algo de fama. Puedes reconquistarlo como cualquier otro barrio, en el móvil, en Territorios.').format(strip=(texto.strip()), frase=(AJ.frase('frases_perdido', banda=banda, barrio=a['nombre'])), precio=(self.precio('tributo_territorio', 300))).strip(), None, True)
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
                return tr('Ese barrio ya tiene los {entero} guardias que admite.').format(entero=(AJ.entero('guardia_max')))
            if not self.pagar(coste):
                return ""
            st["guardia"] += 1
            return tr('Contratado. Ahora hay {guardia} de guardia fija, a {coste} euros cada uno cada medianoche. Defensa del barrio: {int} de 100.').format(guardia=(st['guardia']), coste=(coste), int=(int(self.rec_defensa(bid))))
        if st["guardia"] <= 0:
            self.app.son("error")
            return tr("En ese barrio no hay guardia fija.")
        st["guardia"] -= 1
        return tr('Despides a uno. Quedan {guardia} de guardia fija. Defensa del barrio: {int} de 100.').format(guardia=(st['guardia']), int=(int(self.rec_defensa(bid))))

    def rec_precio_refuerzo(self, bid):
        st = self.rec_barrio(bid)
        return AJ.entero("refuerzo_precio") * (st["refuerzo"] + 1) if st["refuerzo"] < AJ.entero("refuerzo_max") else 0

    def rec_reforzar(self, bid):
        st = self.rec_barrio(bid)
        precio = self.rec_precio_refuerzo(bid)
        if not precio:
            self.app.son("error")
            return tr("Ese barrio ya está reforzado al máximo.")
        if not self.pagar(precio):
            return ""
        st["refuerzo"] += 1
        st["lealtad"] = min(100.0, st["lealtad"] + 5)
        return tr('Hecho: refuerzo de nivel {refuerzo} de {entero}. Puertas, vigías y gente del barrio pagada para avisar. Defensa: {int} de 100.').format(refuerzo=(st['refuerzo']), entero=(AJ.entero('refuerzo_max')), int=(int(self.rec_defensa(bid))))

    def rec_invertir(self, bid):
        st = self.rec_barrio(bid)
        if st["inversion"] == self.dia:
            self.app.son("error")
            return tr("Hoy ya has puesto dinero en este barrio. Mañana, más.")
        if st["lealtad"] >= 100:
            self.app.son("error")
            return tr("La gente de este barrio ya está contigo a muerte: no hace falta.")
        if not self.pagar(AJ.entero("inversion_precio")):
            return ""
        st["inversion"] = self.dia
        st["lealtad"] = min(100.0, st["lealtad"] + AJ("lealtad_inversion"))
        self.son("prestigio", cat="interfaz")
        return tr('Arreglas lo que hace falta y se nota. Lealtad del barrio: {int} de 100.').format(int=(int(st['lealtad'])))

    def rec_informantes(self, d):
        """Sube o baja el nivel de tus informantes. Subir cuesta ya el primer día."""
        r = self.rec()
        nuevo = max(0, min(AJ.entero("informante_max"), r["informantes"] + d))
        if nuevo == r["informantes"]:
            self.app.son("error")
            return tr("No hay más niveles.") if d > 0 else tr("Ya no tienes informantes.")
        if nuevo > r["informantes"] and not self.pagar(AJ.entero("informante_coste")):
            return ""
        r["informantes"] = nuevo
        self._rec_avisar()
        return (tr('Informantes de nivel {nuevo}: {v} euros cada medianoche. ').format(nuevo=(nuevo), v=(AJ.entero('informante_coste') * nuevo)) + self.rec_informantes_txt(nuevo)) if nuevo else tr("Despides a tus informantes.")

    @staticmethod
    def rec_informantes_txt(nivel):
        return (tr("Sin informantes: te enteras el mismo día, si acaso por un rumor, o cuando ya han llegado."), tr("Te llega el rumor un día antes, con el barrio."),
                tr("Chivatazo dos días antes, con la banda y el barrio."), tr("Lo sabes en cuanto lo deciden: banda, barrio, día, hora y fuerza."))[max(0, min(3, int(nivel)))]

    def golpe_motivo(self, banda):
        """Por qué no puedes dar ahora un golpe al escondite de esa banda, o vacío."""
        b = self.rec_banda(banda)
        if self.mundo.tipo != "ciudad":
            return tr("Los escondites están en las ciudades. Ve a una.")
        if self.mision or self.trabajo or self.guerra:
            return tr("Termina antes lo que tienes entre manos.")
        if self.j.estrellas:
            return tr("Con la policía detrás no es momento.")
        if self.dia <= b["fuera"]:
            return tr('{banda} está desmantelada: no hay a quién golpear.').format(banda=(banda))
        falta = int(b["golpe"]) + AJ.entero("golpe_espera") - self.dia
        if falta > 0:
            return tr('Después del último golpe, {banda} se ha escondido bien. Tus fuentes tardarán {_dias} en dar con ellos.').format(banda=(banda), _dias=(_dias(falta)))
        if b["fuerza"] < AJ("golpe_fuerza_min"):
            return tr('{banda} está tan deshecha que no tiene ni escondite que asaltar.').format(banda=(banda))
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
                return {"n": cuantos, "tipo": tr('Pandillero de {banda}').format(banda=(banda)), "arma": random.choice(["pistola", "pistola", "subfusil", "bate"]), "salud": 70 + mas}
            return {"n": cuantos, "clase": clase, "tipo": tr('{get} de {banda}').format(get=(t.get('nombre', tr('Pandillero'))), banda=(banda)), "salud": float(t.get("salud", 70)) + mas}
        base, duro = (tipos[0], tipos[-1]) if tipos else ("", "")
        variante = random.choice(["directo", "vigias", "arsenal"] + (["refuerzos"] if refuerzo else []))
        if variante == "directo":
            pasos = [{"tipo": "eliminar", "lugar": l1.id, "texto": tr('{banda} se esconde junto a {nombre}: son {n}. Entra y no dejes a nadie.').format(banda=(banda), nombre=(l1.nombre), n=(n)),
                      "enemigos": [grupo(base, n - 1), grupo(duro, 1, 15)]}]
        elif variante == "vigias":
            pasos = [{"tipo": "eliminar", "lugar": l1.id, "texto": tr('Primero, los vigías de {banda}: 2, junto a {nombre}. Que no den la voz.').format(banda=(banda), nombre=(l1.nombre)), "enemigos": [grupo(base, 2)]},
                     {"tipo": "eliminar", "lugar": l2.id, "texto": tr('Ya no hay quien avise. El escondite está junto a {nombre}: quedan {v}.').format(nombre=(l2.nombre), v=(n - 1)), "enemigos": [grupo(base, max(1, n - 2)), grupo(duro, 1, 15)]}]
        elif variante == "arsenal":
            pasos = [{"tipo": "eliminar", "lugar": l1.id, "texto": tr('{banda} guarda sus armas junto a {nombre}, con {v} de guardia. Acaba con ellos.').format(banda=(banda), nombre=(l1.nombre), v=(n - 1)), "enemigos": [grupo(base, max(1, n - 2)), grupo(duro, 1, 10)]},
                     {"tipo": "recoger", "lugar": l1.id, "objeto": tr("La caja de armas"), "texto": tr("Despejado. Busca la caja de armas y llévatela: sin ella no son nadie.")}]
        else:
            llegan = min(max(1, n - 2), int(G.tipo_enemigo(refuerzo).get("ocupantes", 3) or 3))
            pasos = [{"tipo": "eliminar", "lugar": l1.id, "texto": tr('El escondite de {banda} está junto a {nombre}: {n} en total, y {llegan} de ellos llegarán en un vehículo en cuanto empiece. Escucha el motor.').format(banda=(banda), nombre=(l1.nombre), n=(n), llegan=(llegan)),
                      "enemigos": [g for g in (grupo(base, n - llegan - 1), grupo(duro, 1, 10), grupo(refuerzo, llegan, 5)) if g["n"] > 0]}]
        b["golpe"] = self.dia
        if self.dia <= b["tregua"]:                              # golpear a una banda con la que tienes tregua la rompe
            b["tregua"] = 0
            b["moral"] = min(100.0, b["moral"] + 15)
            self.cambiar_rep_banda(banda, -15, hablar=False)
            self._rec_decir(tr('Con este golpe rompes la tregua con {banda}. No lo olvidarán.').format(banda=(banda)), "amenaza_barrio")

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
                    texto += tr(' {v} se queda sin su aliada.').format(v=(a['bandas'][0]))
            fin = self._rec_desmantelar(banda)
            self._rec_decir((texto + " " + fin).strip(), "barrio_defendido")
        self._empezar_repetible({"id": "golpe_preventivo", "titulo": tr('Golpe al escondite de {banda}').format(banda=(banda)), "lugar": l1.id, "contador": "golpes_preventivos", "banda": banda,
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
        return (tr('{_y} está asaltando {nombre}').format(_y=(_y(a['bandas'])), nombre=(a['nombre'])) + (tr(', en {ciudad}').format(ciudad=(a['ciudad'])) if a["mapa"] != self.mundo.id else "")
                + tr('. Te quedan {_rato}: ve allí y defiéndelo, o envía a tu gente desde el móvil, en Territorios.').format(_rato=(_rato(a['quedan']))))

    def rec_amenaza_txt(self, bid):
        """El estado de amenaza de un barrio tuyo, que siempre se puede consultar. Los detalles dependen de lo que sepas."""
        r = self.rec()
        a = self.rec_asalto_de(bid)
        if a and a["estado"] == "en_curso":
            return tr('¡asalto en curso de {_y}! Quedan {_rato}').format(_y=(_y(a['bandas'])), _rato=(_rato(a['quedan'])))
        if a:
            cuando = _cuando(a["dia"] - self.dia)
            if a["sabido"] >= 3:
                return tr('{_y} lo asaltará {cuando}, hacia las {hora}, con una fuerza de {int} de 100').format(_y=(_y(a['bandas'])), cuando=(cuando), hora=(a['hora']), int=(int(a['fuerza'])))
            if a["sabido"] == 2:
                return tr('{v} prepara un asalto para {cuando}').format(v=(a['bandas'][0]), cuando=(cuando))
            if a["sabido"] == 1:
                return tr('se rumorea un asalto para {cuando}').format(cuando=(cuando))
            return tr("alta: se nota movimiento raro por sus calles")
        if not r["fase"]:
            return tr("ninguna, de momento")
        if self.dia <= r["calma"]:
            return tr('baja: las bandas siguen lamiéndose las heridas, hasta el día {calma}').format(calma=(r['calma']))
        listas = self._rec_listas()
        fuerte = max((self.rec_banda(n)["fuerza"] for n in listas), default=0.0)
        riesgo = fuerte / max(1.0, AJ("umbral_max")) * (0.5 + 0.5 * (100.0 - self.rec_defensa(bid)) / 100.0)
        return "baja" if riesgo < 0.35 else "media" if riesgo < 0.7 else "alta"

    @staticmethod
    def rec_fuerza_txt(f):
        return tr("deshecha") if f < 15 else tr("rehaciéndose") if f < 35 else tr("con gente otra vez") if f < 55 else tr("fuerte") if f < 75 else tr("muy fuerte, lista para golpear")

    def rec_banda_txt(self, nombre):
        b = self.rec_banda(nombre)
        if self.dia <= b["fuera"]:
            return tr('{nombre}: desmantelada hasta el día {fuera}').format(nombre=(nombre), fuera=(b['fuera']))
        partes = [self.rec_fuerza_txt(b["fuerza"]) + (tr(', fuerza {int} de 100').format(int=(int(b['fuerza']))) if self.rec()["informantes"] >= 2 else "")]
        if b.get("forastera"):
            partes.append(tr("banda forastera"))
        if self.dia <= b["tregua"]:
            partes.append(tr('en tregua contigo hasta el día {tregua}').format(tregua=(b['tregua'])))
        if nombre in self.j.tributos:
            partes.append(tr("te paga tributo y no ataca"))
        if b["derrotas"]:
            partes.append(tr('lleva {derrotas} de {entero} derrotas para quedar desmantelada').format(derrotas=(b['derrotas']), entero=(AJ.entero('derrotas_desmantela'))))
        return f"{nombre}: " + ", ".join(partes)

    def rec_estado_txt(self):
        r = self.rec()
        nivel = self.rec_nivel()
        if not nivel:
            return tr("Reconquista: apagada o no disponible aquí")
        if not r["fase"]:
            return tr('Reconquista, nivel {nivel}: todavía no. Empieza al tener todos los barrios de una ciudad, o {entero} barrios en total').format(nivel=(nivel), entero=(AJ.entero('suave_barrios')))
        fase = {"suave": tr("tienes muchos barrios: las bandas se mueven despacio"), "plena": tr("tienes una ciudad entera: las bandas quieren recuperarla"),
                "mundo": tr("tienes todas las ciudades: todas las bandas van a por ti")}[r["fase"]]
        if r["asalto"] and r["asalto"]["estado"] == "en_curso":
            cola = tr("hay un asalto en curso")
        elif self.dia <= r["calma"]:
            cola = tr('calma hasta el día {calma}. Hoy es el día {dia}').format(calma=(r['calma']), dia=(self.dia))
        elif self.dia <= r["descanso"]:
            cola = tr('las bandas descansan tras el último asalto, al menos hasta el día {descanso}').format(descanso=(r['descanso']))
        else:
            cola = tr("las bandas se están rehaciendo")
        return tr('Reconquista, nivel {nivel}: {fase}; {cola}').format(nivel=(nivel), fase=(fase), cola=(cola))


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
            app.decir(tr('{_y} está en {nombre}').format(_y=(_y(a['bandas'])), nombre=(a['nombre'])) + (tr(', en {ciudad}').format(ciudad=(a['ciudad'])) if a["mapa"] != p.mundo.id else "") + tr('. Ve allí: la defensa empieza en cuanto entres en el barrio. Te quedan {_rato}.').format(_rato=(_rato(a['quedan']))), True)
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
                app.decir(tr('Marcado: {v}, en {nombre}. Con pasar por allí ya cuenta como visita.').format(v=(l.nombre if l else b['nombre']), nombre=(b['nombre'])), True)
            mb = Menu(app, lambda: tr('{nombre}, en {nombre2}. Lealtad {int} de 100, defensa {int2} de 100. Amenaza: {rec_amenaza_txt}').format(nombre=(b['nombre']), nombre2=(mapa.nombre), int=(int(st['lealtad'])), int2=(int(p.rec_defensa(bid))), rec_amenaza_txt=(p.rec_amenaza_txt(bid))), lambda: [
                Opcion(lambda: tr('Guardia fija: {guardia} de {entero}. Contratar a uno más, {entero2} euros al día').format(guardia=(st['guardia']), entero=(AJ.entero('guardia_max')), entero2=(AJ.entero('guardia_coste'))), decir(p.rec_guardia, bid, 1),
                       ayuda=tr("Gente que se queda en el barrio. Cada guardia sube la defensa, cobra cada medianoche y hace que la lealtad baje la mitad de deprisa. "
                             "Si te asaltan y no haces nada, la guardia defiende sola; sin guardia, el barrio se pierde. Si una medianoche no puedes pagarles, se van. Pagas el primer día al contratar.")),
                Opcion(tr("Despedir a un guardia"), decir(p.rec_guardia, bid, -1), ayuda=tr("Uno menos que pagar cada medianoche, y menos defensa.")),
                Opcion(lambda: (tr('Reforzar el barrio: nivel {refuerzo} de {entero}. Subir cuesta {rec_precio_refuerzo} euros, una sola vez').format(refuerzo=(st['refuerzo']), entero=(AJ.entero('refuerzo_max')), rec_precio_refuerzo=(p.rec_precio_refuerzo(bid)))
                                if p.rec_precio_refuerzo(bid) else tr('Reforzar el barrio: ya está al máximo, nivel {refuerzo}').format(refuerzo=(st['refuerzo']))), decir(p.rec_reforzar, bid),
                       ayuda=tr("Una mejora que se paga una vez y se queda: vigías, puertas y gente avisada. Cada nivel sube la defensa, y cada nivel cuesta más que el anterior. "
                             "Con más defensa, quien te asalte lo tiene peor contra tu gente, y si vas tú, vienen menos en cada oleada. Si pierdes el barrio, pierde un nivel.")),
                Opcion(lambda: tr('Invertir en el barrio: {entero} euros. Tienes {dinero}').format(entero=(AJ.entero('inversion_precio')), dinero=(j.dinero)), decir(p.rec_invertir, bid),
                       ayuda=tr("Dinero para la gente del barrio: sube su lealtad. Una vez al día por barrio. Un barrio leal se defiende mejor, es menos tentador para las bandas, "
                             "y sus vecinos te avisan de lo que se prepara aunque no pagues informantes.")),
                Opcion(tr("Marcarlo en el GPS para visitarlo"), gps, ayuda=tr("La lealtad baja si pasan días sin que pises el barrio, y sube la primera vez que entras en él cada día.")),
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
                        app.decir(tr("Aquí no hay dónde dar el golpe."), True)
                if p.dia <= p.rec_banda(nombre)["tregua"]:
                    return app.abrir(Menu(app, tr('Tienes una tregua con {nombre}. Si das el golpe, la rompes').format(nombre=(nombre)), [
                        Opcion(tr("Dar el golpe de todas formas"), ya, ayuda=tr("Rompes la tregua: esa banda te coge manía, se crece y puede volver a asaltar tus barrios.")),
                        Opcion(tr("Dejarlo"), lambda: app.cerrar())]))
                ya()

            def tregua():
                from . import pactos
                pactos.menu_tregua(p, nombre, lambda: [mm.refrescar(False) for mm in app.pila if isinstance(mm, Menu) and mm is not app.pila[0]])
            mb = Menu(app, lambda: p.rec_banda_txt(nombre), [
                Opcion(lambda: tr('Dar un golpe a su escondite. Paga {entero} euros').format(entero=(AJ.entero('golpe_paga'))), golpe,
                       ayuda=tr('Una misión corta, cada vez distinta, en la ciudad en la que estés: asaltas el escondite donde se están rehaciendo. Si la cumples, pierden el {entero} por ciento de su fuerza, cuenta como una derrota y, si eran ellos quienes preparaban un asalto, se suspende. Hace falta que tengan fuerza bastante para tener escondite, y no se puede repetir contra la misma banda hasta pasados {_dias}. Si tienes una tregua con ellos, la rompes.').format(entero=(AJ.entero('golpe_quita')), _dias=(_dias(AJ.entero('golpe_espera'))))),
                Opcion(lambda: tr('Pactar una tregua con {nombre}').format(nombre=(nombre)) if p.dia > p.rec_banda(nombre)["tregua"] else tr('Tregua en vigor hasta el día {tregua}').format(tregua=(p.rec_banda(nombre)['tregua'])), tregua,
                       ayuda=tr("Les pagas y durante unos días no asaltan tus barrios, y se rehacen la mitad de deprisa. Si estaban preparando un asalto, lo dejan. "
                             "Piden más cuanto más fuertes están y peor os lleváis; se puede regatear una vez. La tregua se puede romper: ellos, algún día, sin avisar antes, o tú, si das un golpe a su escondite.")),
            ])
            app.abrir(mb)
        return f

    def informantes(d=1):
        t = p.rec_informantes(d)
        if t:
            app.decir(t, True)

    def partes():
        app.decir(tr("Últimos partes. ") + " ".join(reversed(r["partes"])) if r["partes"] else tr("Todavía no ha pasado nada que contar."), True)

    def ops():
        lista = [Opcion(lambda: p.rec_estado_txt(), lambda: app.decir(EXPLICACION, True),
                        ayuda=tr("Pulsa Intro para oír cómo funciona todo. ") + EXPLICACION)]
        a = r["asalto"]
        if a and a["estado"] == "en_curso":
            lista.append(Opcion(lambda: tr('Asalto a {nombre}: ir en persona. Quedan {_rato}').format(nombre=(a['nombre']), _rato=(_rato(a['quedan']))), ir(a),
                                ayuda=tr("Marca el barrio en el GPS. La defensa empieza al entrar en él: vienen por oleadas, cada una más dura, y tu banda acude a tu lado. "
                                      "Mientras peleas, el plazo no corre. Si sales del barrio o caes, el asalto sigue y puedes volver a intentarlo o enviar a tu gente.")))
            lista.append(Opcion(lambda: (tr('Enviar a tu gente a defender {nombre}: unas {int} de cada 10 posibilidades').format(nombre=(a['nombre']), int=(int(round(p.rec_posibilidades() * 10)))) if j.banda
                                         else tr('Enviar a tu gente a defender {nombre}: no tienes a nadie en la banda').format(nombre=(a['nombre']))), enviar,
                                ayuda=tr("Tu banda va sin ti y el resultado se calcula al momento: la fuerza de ellos contra la defensa del barrio más lo que suma cada uno de los tuyos, y la suerte de cada bando. "
                                      "Se te dice con sus números. Puede caer alguno de los tuyos. Si sale mal, pierdes el barrio.")))
        elif a and a["sabido"] >= 1:
            lista.append(Opcion(lambda: tr('Lo que sabes: {nombre}, {rec_amenaza_txt}').format(nombre=(a['nombre']), rec_amenaza_txt=(p.rec_amenaza_txt(a['barrio']))),
                                ayuda=tr("Aún no ha empezado. Puedes reforzar ese barrio, ponerle guardia, pactar una tregua con esa banda o dar un golpe a su escondite antes de que llegue el día.")))
        for mapa, b in p.rec_barrios():
            lista.append(Opcion(lambda b=b, mapa=mapa: tr('{nombre}, en {nombre2}: lealtad {int}, defensa {int2}, guardias {guardia}. Amenaza: {rec_amenaza_txt}').format(nombre=(b['nombre']), nombre2=(mapa.nombre), int=(int(p.rec_barrio(b['id'])['lealtad'])), int2=(int(p.rec_defensa(b['id']))), guardia=(p.rec_barrio(b['id'])['guardia']), rec_amenaza_txt=(p.rec_amenaza_txt(b['id']))), barrio(mapa, b),
                                ayuda=tr("Intro abre el barrio: guardia fija, refuerzos, invertir y marcarlo en el GPS. La lealtad y la defensa van de 0 a 100. "
                                      "La amenaza se puede consultar siempre; con informantes, o con el barrio de tu parte, sabrás además quién viene y cuándo.")))
        lista.append(Opcion(lambda: tr('Informantes: nivel {informantes} de {entero}, {v} euros al día. {rec_informantes_txt}').format(informantes=(r['informantes']), entero=(AJ.entero('informante_max')), v=(AJ.entero('informante_coste') * r['informantes']), rec_informantes_txt=(p.rec_informantes_txt(r['informantes']))),
                            lambda: informantes(1), ajuste=None,
                            ayuda=tr("Intro sube un nivel; la opción siguiente lo baja. Cada nivel cuesta lo mismo cada medianoche, y el primer día se paga al contratar. "
                                  "Nivel 1: el rumor, un día antes. Nivel 2: chivatazo dos días antes, con la banda, y ves la fuerza exacta de cada banda. Nivel 3: mensaje al móvil en cuanto lo deciden, con día, hora y fuerza. "
                                  "Sin informantes, un barrio con mucha lealtad también te avisa: con 50, como el nivel 1; con 75, como el 2. Si una medianoche no puedes pagarles, se van.")))
        lista.append(Opcion(tr("Bajar un nivel de informantes"), lambda: informantes(-1), ayuda=tr("Pagas menos cada medianoche y te enteras más tarde.")))
        for nombre in p.rec_nombres():
            lista.append(Opcion(lambda nombre=nombre: p.rec_banda_txt(nombre), banda(nombre),
                                ayuda=tr("Intro abre lo que puedes hacer con esta banda: darle un golpe a su escondite o pactar una tregua. "
                                      "Su fuerza crece cada día; cuando es bastante, prepara un asalto. Con informantes de nivel 2 ves la cifra exacta.")))
        lista.append(Opcion(tr("Últimos partes: lo que ha ido pasando"), partes, ayuda=tr("Los últimos avisos, asaltos y resultados, por si se te pasó alguno.")))
        return lista
    m = Menu(app, tr("Defensa de tus barrios"), ops, intro=tr("F1 explica cada opción. La primera, con Intro, cuenta cómo funciona todo"))
    app.abrir(m)


def opciones_territorios(p, Opcion):
    """Lo que la reconquista pone en el menú de Territorios: el asalto en curso, arriba del todo, y la entrada a la defensa."""
    if not p.rec_nivel():
        return [], []
    r = p.rec()
    a = r["asalto"]
    arriba = []
    if a and a["estado"] == "en_curso":
        arriba.append(Opcion(lambda: tr('¡Asalto a {nombre}! {_y}. Quedan {_rato}: defenderlo').format(nombre=(a['nombre']), _y=(_y(a['bandas'])), _rato=(_rato(a['quedan']))), lambda: menu_reconquista(p),
                             ayuda=tr("Abre Defensa de tus barrios: desde allí marcas el barrio en el GPS para ir en persona, o envías a tu gente. Si no haces nada antes de que se acabe el plazo, "
                                   "defiende sola la guardia fija, si la hay; si no, lo pierdes.")))
    abajo = [Opcion(lambda: tr("Defensa de tus barrios. ") + p.rec_estado_txt(), lambda: menu_reconquista(p),
                    ayuda=tr("Las bandas que has vencido intentan recuperar tus barrios. Aquí ves la amenaza, la lealtad y la defensa de cada uno, pones guardias y refuerzos, pagas informantes, "
                          "pactas treguas, das golpes a los escondites y, cuando te asaltan, envías a tu gente. Dentro, la primera opción lo explica todo."))]
    return arriba, abajo
