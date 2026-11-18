"""Negociar con las bandas (1.7.1): además del pacto de paz que ya te ofrecían ellas, ahora propones tú.

Tres tratos, en el móvil, Territorios, Negociar con las bandas:
  - devolverles un barrio tuyo a cambio de dinero;
  - cobrarles un tributo diario por dejarles estar;
  - comprarles un barrio, sin pegar un tiro.

Lo que contestan depende de tu fuerza (tu banda, tus barrios y tu fama) y de cómo te lleves con ellos, y no es igual
dos veces: los precios bailan y hay quien acepta, quien regatea y quien se lo toma como una ofensa. Los números y las
frases están en los datos (vida.json, sección pactos). Solo en solitario: en un servidor, los barrios son de las bandas
de los jugadores.
"""
import random
import zlib

from . import gente as G
from .ajustes import Ajustes

AJ = Ajustes("pactos", {
    "devolver_base": 1800, "tributo_base": 120, "tributo_dias_min": 5, "tributo_dias_max": 10, "comprar_base": 6000, "espera_dias": 3,
    "regateo_extra": 25, "ofensa_ataque": 40, "plante_prob": 8,
    "tregua_base": 900, "tregua_dias_min": 6, "tregua_dias_max": 10, "tregua_rompe_prob": 4,
}, {
    "frases_devolver_si": ["{banda}: ¿{barrio}, por las buenas? Te damos {euros} euros y aquí no ha pasado nada.",
                           "{banda} lo habla entre ellos y vuelve con una cifra: {euros} euros por {barrio}.",
                           "{banda}: Siempre fue nuestro. {euros} euros, y nos lo devuelves hoy."],
    "frases_devolver_no": ["{banda}: Con vosotros no hay tratos. {barrio} lo recuperaremos por las malas.",
                           "{banda} te cuelga. Antes de pagarte un euro prefieren quitártelo a tiros.",
                           "{banda}: ¿Pagar por lo que es nuestro? Ya iremos a buscarlo."],
    "frases_devolver_hecho": ["Trato cerrado: {barrio} vuelve a ser de {banda} y tú te llevas {euros} euros.",
                              "Os dais la mano. {banda} entra en {barrio} sin un tiro, y tú cuentas {euros} euros."],
    "frases_regateo_si": ["{banda} gruñe, pero sube la oferta: {euros} euros.", "Aguantas la mirada y funciona: {banda} llega a {euros} euros."],
    "frases_regateo_no": ["{banda} se levanta de la mesa: ya no hay oferta.", "Has tensado demasiado la cuerda. {banda} retira lo dicho."],
    "frases_tributo_si": ["{banda}: De acuerdo. {euros} euros al día durante {dias} días, y nos dejas trabajar.",
                          "{banda} no quiere guerra contigo: pagará {euros} euros cada medianoche, {dias} días.",
                          "{banda} hace cuentas y le sale más barato pagarte: {euros} euros diarios, {dias} días."],
    "frases_tributo_no": ["{banda}: ¿Tributo? ¿A ti? Vuelve cuando seas alguien.", "{banda} se ríe en tu cara. No van a pagarte nada.",
                          "{banda}: Aquí el que cobra somos nosotros. Lárgate."],
    "frases_tributo_ofensa": ["Y no se queda ahí: {banda} se lo ha tomado como una ofensa. Mandarán a alguien a explicártelo.",
                              "Lo de pedirles dinero les ha sentado mal. {banda} no lo va a dejar pasar."],
    "frases_tributo_cobro": ["{banda} cumple: te llegan {euros} euros de tributo.", "Sobre de {banda}: {euros} euros, como quedasteis."],
    "frases_tributo_fin": ["Se acaba el trato con {banda}: desde hoy ya no te pagan. Puedes volver a negociarlo.",
                           "{banda} ha pagado lo acordado. El tributo termina aquí."],
    "frases_tributo_plante": ["{banda} se planta: dicen que no pagan ni un día más.", "Hoy no llega el sobre de {banda}. Han decidido que ya no te tienen miedo."],
    "frases_comprar_si": ["{banda}: Todo tiene un precio. {barrio} es tuyo por {euros} euros.", "{banda} pone la cifra sobre la mesa: {euros} euros por {barrio}.",
                          "{banda}: Nos viene bien el dinero. {euros} euros y nos vamos de {barrio}."],
    "frases_comprar_no": ["{banda}: {barrio} no está en venta. Y menos para ti.", "{banda}: A quien nos mata a los nuestros no le vendemos ni la hora.",
                          "{banda} ni te contesta. Con ellos, de momento, no hay negocio."],
    "frases_comprar_hecho": ["Pagas {euros} euros y {banda} recoge sus cosas: {barrio} es tuyo, sin pegar un tiro.",
                             "El dinero cambia de manos y las esquinas de {barrio}, de dueño. Ahora mandas tú."],
    "frases_tregua_si": ["{banda}: Una tregua se puede hablar. {euros} euros y en {dias} días no tocamos lo tuyo.",
                         "{banda} hace cuentas: por {euros} euros, {dias} días sin acercarse a tus barrios.",
                         "{banda}: Nos viene bien un respiro. {euros} euros, {dias} días de paz."],
    "frases_tregua_no": ["{banda}: ¿Tregua? Contigo solo hablamos de una manera.", "{banda} no quiere oír hablar de treguas. Van a por lo tuyo.",
                         "{banda} te cuelga: no hay nada que pactar."],
    "frases_tregua_hecho": ["Tregua cerrada con {banda}: {dias} días sin asaltos suyos, hasta el día {hasta}.",
                            "Pagas {euros} euros y {banda} da su palabra: {dias} días de paz, hasta el día {hasta}."],
}, cero=("ofensa_ataque", "plante_prob", "regateo_extra", "tregua_rompe_prob"))

ASUNTOS = {"devolver": "devolverles un barrio", "tributo": "cobrarles un tributo", "comprar": "comprarles un barrio", "tregua": "pactar una tregua"}


def _dias(n):
    return "un día" if int(n) == 1 else f"{int(n)} días"


class Pactos:
    """Mixin de Partida."""

    def fuerza_propia(self):
        """Lo que pesas en la calle, de 0 a 100: tu banda, tus barrios y tu fama."""
        j = self.j
        return max(0.0, min(100.0, j.banda * 10 + len(j.territorios) * 7 + j.reputacion * 0.4))

    def banda_interesada(self, b, mapa=None):
        """La banda con la que se trata un barrio: la que manda en él o, si no es de nadie (o es tuyo), la que siempre le
        ha tenido ganas, que es la misma en toda la partida."""
        banda = self.j.barrios_banda.get(b["id"]) or b.get("banda")
        if b["id"] not in self.j.territorios:
            banda = banda or self.banda_de_barrio(b)
        bandas = G.nombres_bandas()
        if banda or not bandas:
            return banda or ""
        mapa = mapa or self.mundo
        return bandas[zlib.crc32(f"trato:{self.j.semilla}:{mapa.id}:{b['id']}".encode("utf-8")) % len(bandas)]

    def _azar_trato(self, banda, asunto, extra=""):
        return random.Random(f"trato:{self.j.semilla}:{self.dia}:{banda}:{asunto}:{extra}")

    def trato_espera(self, banda, asunto, extra=""):
        """Días que faltan para poder volver a tratar esto con esa banda, o 0."""
        ultimo = self.j.tratos.get(f"{banda}:{asunto}:{extra}")
        return max(0, int(ultimo) + AJ.entero("espera_dias") - self.dia) if ultimo is not None else 0

    def _apuntar_trato(self, banda, asunto, extra=""):
        self.j.tratos[f"{banda}:{asunto}:{extra}"] = self.dia
        for k in [k for k, d in self.j.tratos.items() if self.dia - int(d) > 30]:      # lo viejo se olvida
            del self.j.tratos[k]

    def pactos_motivo(self):
        if self.en_servidor:
            return "En un servidor en línea no se negocia con estas bandas: allí los barrios son de las bandas de los jugadores."
        if self.mundo.tipo != "ciudad":
            return "Las bandas están en las ciudades: Puerto Bravo, San Lucero y Monteferro."
        if self.j.estrellas:
            return "Con la policía detrás, nadie se sienta contigo a hablar."
        if self.mision or self.guerra:
            return "Termina antes lo que tienes entre manos."
        return ""

    # ------------------------------------------------------------------ devolver un barrio
    def oferta_devolver(self, b):
        """Lo que contesta la banda a la que le ofreces un barrio tuyo: (acepta, euros, frase)."""
        banda = self.banda_interesada(b)
        rng = self._azar_trato(banda, "devolver", b["id"])
        rep = self.rep_banda(banda)
        if rep <= -50:
            return False, 0, AJ.frase("frases_devolver_no", rng, banda=banda, barrio=b["nombre"])
        euros = int(AJ("devolver_base") * (0.7 + self.fuerza_propia() / 150.0) * (1.0 + rep / 250.0) * rng.uniform(0.8, 1.3) / 10) * 10
        return True, max(50, euros), AJ.frase("frases_devolver_si", rng, banda=banda, barrio=b["nombre"], euros=max(50, euros))

    def devolver_barrio(self, b, euros):
        j = self.j
        banda = self.banda_interesada(b)
        if b["id"] not in j.territorios:
            return False
        j.territorios.remove(b["id"])
        j.barrios_banda[b["id"]] = banda
        if j.amenaza and j.amenaza.get("territorio") == b["id"]:
            j.amenaza = None
        self._apuntar_trato(banda, "devolver", b["id"])
        self.cambiar_rep_banda(banda, 12, hablar=False)
        self.cambiar_reputacion(-3)
        self.son("trato", cat="interfaz")
        self.dar_dinero(euros)
        j.stats["tratos_bandas"] = j.stats.get("tratos_bandas", 0) + 1
        self.decir(AJ.frase("frases_devolver_hecho", banda=banda, barrio=b["nombre"], euros=euros), True)
        return True

    def regatear(self, banda, euros, asunto, extra=""):
        """Pides más (o menos, si compras). Devuelve la cifra nueva, o None si se levantan de la mesa."""
        rng = self._azar_trato(banda, "regateo:" + asunto, extra)
        if rng.random() < 0.25 + self.fuerza_propia() / 160.0 + self.rep_banda(banda) / 400.0:
            cambio = 1.0 + AJ("regateo_extra") / 100.0
            return int(euros * cambio / 10) * 10 if asunto not in ("comprar", "tregua") else int(euros / cambio / 10) * 10
        self._apuntar_trato(banda, asunto, extra)
        self.cambiar_rep_banda(banda, -3, hablar=False)
        return None

    # ------------------------------------------------------------------ tributo
    def barrios_de_banda(self, banda):
        return [b for m in self.mapas.values() if m.tipo == "ciudad" for b in m.barrios if b["id"] not in self.j.territorios and self.banda_de_barrio(b) == banda]

    def pedir_tributo(self, banda):
        """Le exiges a una banda que te pague por dejarla estar. Devuelve la frase con lo que pasa."""
        j = self.j
        if not j.territorios:
            return "Sin un solo barrio tuyo no eres nadie para cobrar a una banda. Conquista uno primero."
        if banda in j.tributos:
            t = j.tributos[banda]
            return f"{banda} ya te paga {t['euros']} euros cada medianoche, hasta el día {t['hasta']}."
        falta = self.trato_espera(banda, "tributo")
        if falta:
            return f"{banda} ya te contestó hace poco. Vuelve a intentarlo dentro de {_dias(falta)}."
        rng = self._azar_trato(banda, "tributo")
        rep, fuerza = self.rep_banda(banda), self.fuerza_propia()
        self._apuntar_trato(banda, "tributo")
        if rng.random() < max(0.05, min(0.92, 0.10 + fuerza / 110.0 + rep / 300.0)):
            dias = rng.randint(*sorted((AJ.entero("tributo_dias_min"), AJ.entero("tributo_dias_max"))))
            euros = max(10, int(AJ("tributo_base") * (1.0 + 0.5 * len(self.barrios_de_banda(banda))) * rng.uniform(0.8, 1.25) * (0.8 if rep >= 30 else 1.0) / 10) * 10)
            j.tributos[banda] = {"euros": euros, "hasta": self.dia + dias}
            self.cambiar_rep_banda(banda, -6, hablar=False)
            self.cambiar_reputacion(2)
            self.son("trato", cat="interfaz")
            j.stats["tratos_bandas"] = j.stats.get("tratos_bandas", 0) + 1
            return AJ.frase("frases_tributo_si", rng, banda=banda, euros=euros, dias=dias)
        self.cambiar_rep_banda(banda, -10, hablar=False)
        self.son("rechazo", cat="interfaz")
        texto = AJ.frase("frases_tributo_no", rng, banda=banda)
        if fuerza < 45 and rng.random() * 100 < AJ("ofensa_ataque"):
            j.represalias.append({"cuando": self.dia * 1440.0 + self.reloj + rng.uniform(40, 200), "lugar": banda, "n": rng.randint(2, 3)})
            texto += " " + AJ.frase("frases_tributo_ofensa", rng, banda=banda)
        return texto

    def dia_pactos(self, azar=random):
        """Cada medianoche: las bandas que te pagan tributo, pagan; el trato que vence, se acaba; y alguna se planta."""
        j = self.j
        if self.en_servidor:
            return
        for banda, t in list(j.tributos.items()):
            if not j.territorios or azar.random() * 100 < AJ("plante_prob") * (2.0 if self.fuerza_propia() < 30 else 1.0):
                del j.tributos[banda]
                self.cambiar_rep_banda(banda, -5, hablar=False)
                self.decir(AJ.frase("frases_tributo_plante", banda=banda))
                continue
            j.dinero += int(t["euros"])
            j.stats["dinero_ganado"] += int(t["euros"])
            j.stats["tributos_cobrados"] = j.stats.get("tributos_cobrados", 0) + int(t["euros"])
            self.decir(AJ.frase("frases_tributo_cobro", banda=banda, euros=t["euros"]))
            if self.dia >= int(t["hasta"]):
                del j.tributos[banda]
                self.decir(AJ.frase("frases_tributo_fin", banda=banda))

    # ------------------------------------------------------------------ comprar un barrio
    def oferta_comprar(self, b):
        """Lo que pide la banda por un barrio que no es tuyo: (vende, euros, frase)."""
        banda = self.banda_interesada(b)
        rng = self._azar_trato(banda, "comprar", b["id"])
        rep, fuerza = self.rep_banda(banda), self.fuerza_propia()
        if rep <= -40 and fuerza < 60:
            return False, 0, AJ.frase("frases_comprar_no", rng, banda=banda, barrio=b["nombre"])
        euros = AJ("comprar_base") * rng.uniform(0.85, 1.3) * (1.25 if rep < 0 else 0.85 if rep >= 30 else 1.0) * (1.0 - min(0.25, fuerza / 400.0))
        euros = max(100, int(euros / 50) * 50)
        return True, euros, AJ.frase("frases_comprar_si", rng, banda=banda, barrio=b["nombre"], euros=euros)

    def comprar_barrio(self, b, euros):
        j = self.j
        banda = self.banda_interesada(b)
        if b["id"] in j.territorios or not self.pagar(euros):
            return False
        j.territorios.append(b["id"])
        j.barrios_banda.pop(b["id"], None)
        self._apuntar_trato(banda, "comprar", b["id"])
        self.cambiar_rep_banda(banda, 5, hablar=False)
        self.cambiar_reputacion(4)
        self.son("territorio", cat="interfaz")
        j.stats["tratos_bandas"] = j.stats.get("tratos_bandas", 0) + 1
        self.decir(AJ.frase("frases_comprar_hecho", banda=banda, barrio=b["nombre"], euros=euros) + f" Te pagará {self.precio('tributo_territorio', 300)} euros cada medianoche.", True)
        return True

    # ------------------------------------------------------------------ tregua (la reconquista)
    def tregua_rompe_prob(self):
        """De cada cien medianoches, cuántas rompe una banda su tregua contigo: el doble si pesas poco."""
        return AJ("tregua_rompe_prob") * (2.0 if self.fuerza_propia() < 30 else 1.0)

    def tregua_motivo(self, banda):
        if not self.rec_nivel():
            return "Las treguas son cosa de la reconquista de barrios, que aquí no está en marcha."
        b = self.rec_banda(banda)
        if self.dia <= b["fuera"]:
            return f"{banda} está desmantelada: no queda nadie con quien pactar."
        if self.dia <= b["tregua"]:
            return f"Ya tienes una tregua con {banda}, hasta el día {b['tregua']}."
        if self.j.estrellas:
            return "Con la policía detrás, nadie se sienta contigo a hablar."
        falta = self.trato_espera(banda, "tregua")
        if falta:
            return f"{banda} ya te contestó hace poco. Vuelve a intentarlo dentro de {_dias(falta)}."
        return ""

    def oferta_tregua(self, banda):
        """Lo que pide una banda por dejar tus barrios en paz unos días: (acepta, euros, días, frase)."""
        rng = self._azar_trato(banda, "tregua")
        rep, b = self.rep_banda(banda), self.rec_banda(banda)
        a = self.rec()["asalto"]
        if rep <= -50 or (a and a["estado"] == "en_curso" and banda in a["bandas"]):
            return False, 0, 0, AJ.frase("frases_tregua_no", rng, banda=banda)
        dias = rng.randint(*sorted((AJ.entero("tregua_dias_min"), AJ.entero("tregua_dias_max"))))
        euros = AJ("tregua_base") * (0.6 + b["fuerza"] / 80.0) * (1.3 if rep < 0 else 0.8 if rep >= 30 else 1.0) * (1.0 - min(0.25, self.fuerza_propia() / 400.0)) * rng.uniform(0.85, 1.25)
        euros = max(50, int(euros / 10) * 10)
        return True, euros, dias, AJ.frase("frases_tregua_si", rng, banda=banda, euros=euros, dias=dias)

    def pactar_tregua(self, banda, euros, dias):
        if not self.pagar(euros):
            return False
        r, b = self.rec(), self.rec_banda(banda)
        b["tregua"] = self.dia + int(dias)
        self._apuntar_trato(banda, "tregua")
        self.cambiar_rep_banda(banda, 4, hablar=False)
        self.son("trato", cat="interfaz")
        self.j.stats["tratos_bandas"] = self.j.stats.get("tratos_bandas", 0) + 1
        texto = AJ.frase("frases_tregua_hecho", banda=banda, euros=euros, dias=int(dias), hasta=b["tregua"])
        a = r["asalto"]
        if a and a["estado"] == "prepara" and banda in a["bandas"]:      # lo que estuvieran tramando, se queda en nada
            if a["bandas"][0] == banda:
                r["asalto"] = None
                texto += " Y lo que estuvieran preparando contra ti, lo dejan."
            else:
                a["bandas"].remove(banda)
                a["fuerza"] = round(a["fuerza"] * 0.6, 1)
        self.decir(texto, True)
        self._rec_parte(texto)
        return True


def _mesa(p, titulo, banda, asunto, extra, euros, hecho, pedir_mas):
    """La mesa de un trato con cifra: aceptar, regatear una vez o dejarlo."""
    from .menus import Menu, Opcion
    app = p.app
    estado = {"euros": euros, "regateado": False}

    def aceptar():
        app.cerrar(mm)
        hecho(estado["euros"])

    def regatear():
        if estado["regateado"]:
            app.son("error")
            return app.decir("Ya has apretado una vez. Ahora, o lo tomas o lo dejas.", True)
        estado["regateado"] = True
        nuevo = p.regatear(banda, estado["euros"], asunto, extra)
        if nuevo is None:
            app.cerrar(mm)
            p.son("rechazo", cat="interfaz")
            app.decir(AJ.frase("frases_regateo_no", banda=banda), True)
            return
        estado["euros"] = nuevo
        app.decir(AJ.frase("frases_regateo_si", banda=banda, euros=nuevo), True)
        mm.refrescar(False)
    mm = Menu(app, titulo, lambda: [
        Opcion(f"Aceptar: {estado['euros']} euros", aceptar),
        Opcion(pedir_mas, regatear, ayuda="Una sola vez. Cuanto más pesas en la calle y mejor te llevas con ellos, más fácil es que cedan. Si no cuela, se levantan de la mesa y no hay trato en unos días."),
        Opcion("Dejarlo", lambda: app.cerrar(mm))])
    app.abrir(mm)


AYUDA_TREGUA = ("Les pagas y durante unos días esa banda no asalta tus barrios, y se rehace la mitad de deprisa. Si estaba preparando un asalto, lo deja. "
                "Piden más cuanto más fuertes están y peor os lleváis, y la cifra no es la misma cada día. Puedes pedir una rebaja, una vez. "
                "La tregua se puede romper: ellos, algún día, o tú, si das un golpe a su escondite.")


def menu_tregua(p, banda, al_volver=None):
    """Pactar una tregua con una banda (la reconquista): dicen una cifra y unos días; se acepta, se regatea o se deja."""
    app = p.app
    motivo = p.tregua_motivo(banda)
    if motivo:
        app.son("error")
        return app.decir(motivo, True)
    si, euros, dias, frase = p.oferta_tregua(banda)
    if not si:
        p._apuntar_trato(banda, "tregua")
        p.son("rechazo", cat="interfaz")
        return app.decir(frase, True)

    def hecho(e):
        p.pactar_tregua(banda, e, dias)
        if al_volver:
            al_volver()
    _mesa(p, frase + f" Tienes {p.j.dinero} euros", banda, "tregua", "", euros, hecho, "Pedir una rebaja")


def menu_pactos(p):
    from .menus import Menu, Opcion
    app, j = p.app, p.j
    motivo = p.pactos_motivo()
    if motivo:
        app.son("error")
        app.decir(motivo, True)
        return

    def mesa(titulo, banda, asunto, extra, euros, hecho, pedir_mas):
        _mesa(p, titulo, banda, asunto, extra, euros, hecho, pedir_mas)

    def devolver(b):
        def f():
            banda = p.banda_interesada(b)
            falta = p.trato_espera(banda, "devolver", b["id"])
            if falta:
                return app.decir(f"{banda} ya te contestó sobre {b['nombre']}. Vuelve dentro de {_dias(falta)}.", True)
            si, euros, frase = p.oferta_devolver(b)
            if not si:
                p._apuntar_trato(banda, "devolver", b["id"])
                p.son("rechazo", cat="interfaz")
                return app.decir(frase, True)
            mesa(frase, banda, "devolver", b["id"], euros, lambda e: (p.devolver_barrio(b, e), m.refrescar(False)), "Pedir más dinero")
        return f

    def comprar(b):
        def f():
            banda = p.banda_interesada(b)
            falta = p.trato_espera(banda, "comprar", b["id"])
            if falta:
                return app.decir(f"{banda} ya te contestó sobre {b['nombre']}. Vuelve dentro de {_dias(falta)}.", True)
            si, euros, frase = p.oferta_comprar(b)
            if not si:
                p._apuntar_trato(banda, "comprar", b["id"])
                p.son("rechazo", cat="interfaz")
                return app.decir(frase, True)
            mesa(frase + f" Tienes {j.dinero} euros", banda, "comprar", b["id"], euros, lambda e: (p.comprar_barrio(b, e), m.refrescar(False)), "Pedir una rebaja")
        return f

    def tributo(banda):
        def f():
            app.decir(p.pedir_tributo(banda), True)
            m.refrescar(False)
        return f

    def ops():
        lista = [Opcion(lambda: f"Tu fuerza en la calle: {int(p.fuerza_propia())} de 100. Tu banda, {j.banda}; tus barrios, {len(j.territorios)}",
                        ayuda="De tu fuerza y de cómo te lleves con cada banda depende lo que te contesten: si aceptan, cuánto pagan y cuánto piden. "
                              "Sube con más gente en tu banda, más barrios y más fama.")]
        barrios = p.mundo.barrios if p.mundo.tipo == "ciudad" else []
        for b in barrios:
            if b["id"] in j.territorios:
                lista.append(Opcion(lambda b=b: f"Devolver {b['nombre']} a {p.banda_interesada(b)} a cambio de dinero", devolver(b),
                                    ayuda="Les ofreces el barrio por las buenas. Si les interesa, dicen una cifra: la aceptas, pides más o lo dejas. "
                                          "Pierdes el barrio y lo que te paga cada medianoche, pero cobras de golpe y mejora tu relación con esa banda."))
        for b in barrios:
            if b["id"] not in j.territorios:
                lista.append(Opcion(lambda b=b: f"Comprar {b['nombre']} a {p.banda_interesada(b)}", comprar(b),
                                    ayuda="Quedarte con el barrio pagando, sin pelear. Piden más o menos según cómo os llevéis y lo que peses en la calle, y la cifra no es la misma cada día. "
                                          "Puedes pedir una rebaja, una vez."))
        for banda in G.nombres_bandas():
            def texto(banda=banda):
                t = j.tributos.get(banda)
                if t:
                    return f"{banda} te paga {t['euros']} euros cada medianoche, hasta el día {t['hasta']}"
                return f"Cobrar un tributo a {banda}: {p.rep_banda_txt(p.rep_banda(banda))}"
            lista.append(Opcion(texto, tributo(banda),
                                ayuda="Les exiges que te paguen cada día por dejarles estar. Hace falta tener algún barrio. Si te temen, pagan unos días; si no, se niegan, "
                                      "y si pesas poco pueden mandar a alguien a por ti. Mientras pagan, esa banda no ataca tus barrios."))
        if p.rec_nivel():                                        # con la reconquista: treguas, también con las bandas forasteras
            for banda in p.rec_nombres():
                lista.append(Opcion(lambda banda=banda: (f"Tregua con {banda} en vigor hasta el día {p.rec_banda(banda)['tregua']}" if p.dia <= p.rec_banda(banda)["tregua"]
                                                         else f"Pactar una tregua con {banda}: {p.rec_banda_txt(banda).split(': ', 1)[1]}"),
                                    lambda banda=banda: menu_tregua(p, banda, lambda: m.refrescar(False)), ayuda=AYUDA_TREGUA))
        return lista
    m = Menu(app, f"Negociar con las bandas de {p.mundo.nombre}", ops, intro="Devolver un barrio por dinero, comprar uno o cobrar un tributo. F1 explica cada trato")
    app.abrir(m)
