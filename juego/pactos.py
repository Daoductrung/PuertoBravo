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
from .i18n import tr
import random
import zlib

from . import gente as G
from .ajustes import Ajustes

AJ = Ajustes("pactos", {
    "devolver_base": 1800, "tributo_base": 120, "tributo_dias_min": 5, "tributo_dias_max": 10, "comprar_base": 6000, "espera_dias": 3,
    "regateo_extra": 25, "ofensa_ataque": 40, "plante_prob": 8,
    "tregua_base": 900, "tregua_dias_min": 6, "tregua_dias_max": 10, "tregua_rompe_prob": 4,
}, {
    "frases_devolver_si": [tr("{banda}: ¿{barrio}, por las buenas? Te damos {euros} euros y aquí no ha pasado nada."),
                           tr("{banda} lo habla entre ellos y vuelve con una cifra: {euros} euros por {barrio}."),
                           tr("{banda}: Siempre fue nuestro. {euros} euros, y nos lo devuelves hoy.")],
    "frases_devolver_no": [tr("{banda}: Con vosotros no hay tratos. {barrio} lo recuperaremos por las malas."),
                           tr("{banda} te cuelga. Antes de pagarte un euro prefieren quitártelo a tiros."),
                           tr("{banda}: ¿Pagar por lo que es nuestro? Ya iremos a buscarlo.")],
    "frases_devolver_hecho": [tr("Trato cerrado: {barrio} vuelve a ser de {banda} y tú te llevas {euros} euros."),
                              tr("Os dais la mano. {banda} entra en {barrio} sin un tiro, y tú cuentas {euros} euros.")],
    "frases_regateo_si": [tr("{banda} gruñe, pero sube la oferta: {euros} euros."), tr("Aguantas la mirada y funciona: {banda} llega a {euros} euros.")],
    "frases_regateo_no": [tr("{banda} se levanta de la mesa: ya no hay oferta."), tr("Has tensado demasiado la cuerda. {banda} retira lo dicho.")],
    "frases_tributo_si": [tr("{banda}: De acuerdo. {euros} euros al día durante {dias} días, y nos dejas trabajar."),
                          tr("{banda} no quiere guerra contigo: pagará {euros} euros cada medianoche, {dias} días."),
                          tr("{banda} hace cuentas y le sale más barato pagarte: {euros} euros diarios, {dias} días.")],
    "frases_tributo_no": [tr("{banda}: ¿Tributo? ¿A ti? Vuelve cuando seas alguien."), tr("{banda} se ríe en tu cara. No van a pagarte nada."),
                          tr("{banda}: Aquí el que cobra somos nosotros. Lárgate.")],
    "frases_tributo_ofensa": [tr("Y no se queda ahí: {banda} se lo ha tomado como una ofensa. Mandarán a alguien a explicártelo."),
                              tr("Lo de pedirles dinero les ha sentado mal. {banda} no lo va a dejar pasar.")],
    "frases_tributo_cobro": [tr("{banda} cumple: te llegan {euros} euros de tributo."), tr("Sobre de {banda}: {euros} euros, como quedasteis.")],
    "frases_tributo_fin": [tr("Se acaba el trato con {banda}: desde hoy ya no te pagan. Puedes volver a negociarlo."),
                           tr("{banda} ha pagado lo acordado. El tributo termina aquí.")],
    "frases_tributo_plante": [tr("{banda} se planta: dicen que no pagan ni un día más."), tr("Hoy no llega el sobre de {banda}. Han decidido que ya no te tienen miedo.")],
    "frases_comprar_si": [tr("{banda}: Todo tiene un precio. {barrio} es tuyo por {euros} euros."), tr("{banda} pone la cifra sobre la mesa: {euros} euros por {barrio}."),
                          tr("{banda}: Nos viene bien el dinero. {euros} euros y nos vamos de {barrio}.")],
    "frases_comprar_no": [tr("{banda}: {barrio} no está en venta. Y menos para ti."), tr("{banda}: A quien nos mata a los nuestros no le vendemos ni la hora."),
                          tr("{banda} ni te contesta. Con ellos, de momento, no hay negocio.")],
    "frases_comprar_hecho": [tr("Pagas {euros} euros y {banda} recoge sus cosas: {barrio} es tuyo, sin pegar un tiro."),
                             tr("El dinero cambia de manos y las esquinas de {barrio}, de dueño. Ahora mandas tú.")],
    "frases_tregua_si": [tr("{banda}: Una tregua se puede hablar. {euros} euros y en {dias} días no tocamos lo tuyo."),
                         tr("{banda} hace cuentas: por {euros} euros, {dias} días sin acercarse a tus barrios."),
                         tr("{banda}: Nos viene bien un respiro. {euros} euros, {dias} días de paz.")],
    "frases_tregua_no": [tr("{banda}: ¿Tregua? Contigo solo hablamos de una manera."), tr("{banda} no quiere oír hablar de treguas. Van a por lo tuyo."),
                         tr("{banda} te cuelga: no hay nada que pactar.")],
    "frases_tregua_hecho": [tr("Tregua cerrada con {banda}: {dias} días sin asaltos suyos, hasta el día {hasta}."),
                            tr("Pagas {euros} euros y {banda} da su palabra: {dias} días de paz, hasta el día {hasta}.")],
}, cero=("ofensa_ataque", "plante_prob", "regateo_extra", "tregua_rompe_prob"))

ASUNTOS = {"devolver": tr("devolverles un barrio"), "tributo": tr("cobrarles un tributo"), "comprar": tr("comprarles un barrio"), "tregua": tr("pactar una tregua")}


def _dias(n):
    return tr("un día") if int(n) == 1 else tr('{int} días').format(int=(int(n)))


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
            return tr("En un servidor en línea no se negocia con estas bandas: allí los barrios son de las bandas de los jugadores.")
        if self.mundo.tipo != "ciudad":
            return tr("Las bandas están en las ciudades: Puerto Bravo, San Lucero y Monteferro.")
        if self.j.estrellas:
            return tr("Con la policía detrás, nadie se sienta contigo a hablar.")
        if self.mision or self.guerra:
            return tr("Termina antes lo que tienes entre manos.")
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
            return tr("Sin un solo barrio tuyo no eres nadie para cobrar a una banda. Conquista uno primero.")
        if banda in j.tributos:
            t = j.tributos[banda]
            return tr('{banda} ya te paga {euros} euros cada medianoche, hasta el día {hasta}.').format(banda=(banda), euros=(t['euros']), hasta=(t['hasta']))
        falta = self.trato_espera(banda, "tributo")
        if falta:
            return tr('{banda} ya te contestó hace poco. Vuelve a intentarlo dentro de {_dias}.').format(banda=(banda), _dias=(_dias(falta)))
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
        self.decir(AJ.frase("frases_comprar_hecho", banda=banda, barrio=b["nombre"], euros=euros) + tr(' Te pagará {precio} euros cada medianoche.').format(precio=(self.precio('tributo_territorio', 300))), True)
        return True

    # ------------------------------------------------------------------ tregua (la reconquista)
    def tregua_rompe_prob(self):
        """De cada cien medianoches, cuántas rompe una banda su tregua contigo: el doble si pesas poco."""
        return AJ("tregua_rompe_prob") * (2.0 if self.fuerza_propia() < 30 else 1.0)

    def tregua_motivo(self, banda):
        if not self.rec_nivel():
            return tr("Las treguas son cosa de la reconquista de barrios, que aquí no está en marcha.")
        b = self.rec_banda(banda)
        if self.dia <= b["fuera"]:
            return tr('{banda} está desmantelada: no queda nadie con quien pactar.').format(banda=(banda))
        if self.dia <= b["tregua"]:
            return tr('Ya tienes una tregua con {banda}, hasta el día {tregua}.').format(banda=(banda), tregua=(b['tregua']))
        if self.j.estrellas:
            return tr("Con la policía detrás, nadie se sienta contigo a hablar.")
        falta = self.trato_espera(banda, "tregua")
        if falta:
            return tr('{banda} ya te contestó hace poco. Vuelve a intentarlo dentro de {_dias}.').format(banda=(banda), _dias=(_dias(falta)))
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
                texto += tr(" Y lo que estuvieran preparando contra ti, lo dejan.")
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
            return app.decir(tr("Ya has apretado una vez. Ahora, o lo tomas o lo dejas."), True)
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
        Opcion(tr('Aceptar: {euros} euros').format(euros=(estado['euros'])), aceptar, ayuda=tr("Cierras el trato por esa cifra, la de ahora, también si ha cambiado al regatear.")),
        Opcion(pedir_mas, regatear, ayuda=tr("Una sola vez. Cuanto más pesas en la calle y mejor te llevas con ellos, más fácil es que cedan. Si no cuela, se levantan de la mesa y no hay trato en unos días.")),
        Opcion(tr("Dejarlo"), lambda: app.cerrar(mm))])
    app.abrir(mm)


AYUDA_TREGUA = (tr("Les pagas y durante unos días esa banda no asalta tus barrios, y se rehace la mitad de deprisa. Si estaba preparando un asalto, lo deja. "
                "Piden más cuanto más fuertes están y peor os lleváis, y la cifra no es la misma cada día. Puedes pedir una rebaja, una vez. "
                "La tregua se puede romper: ellos, algún día, o tú, si das un golpe a su escondite."))


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
    _mesa(p, frase + tr(' Tienes {dinero} euros').format(dinero=(p.j.dinero)), banda, "tregua", "", euros, hecho, tr("Pedir una rebaja"))


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
                return app.decir(tr('{banda} ya te contestó sobre {nombre}. Vuelve dentro de {_dias}.').format(banda=(banda), nombre=(b['nombre']), _dias=(_dias(falta))), True)
            si, euros, frase = p.oferta_devolver(b)
            if not si:
                p._apuntar_trato(banda, "devolver", b["id"])
                p.son("rechazo", cat="interfaz")
                return app.decir(frase, True)
            mesa(frase, banda, "devolver", b["id"], euros, lambda e: (p.devolver_barrio(b, e), m.refrescar(False)), tr("Pedir más dinero"))
        return f

    def comprar(b):
        def f():
            banda = p.banda_interesada(b)
            falta = p.trato_espera(banda, "comprar", b["id"])
            if falta:
                return app.decir(tr('{banda} ya te contestó sobre {nombre}. Vuelve dentro de {_dias}.').format(banda=(banda), nombre=(b['nombre']), _dias=(_dias(falta))), True)
            si, euros, frase = p.oferta_comprar(b)
            if not si:
                p._apuntar_trato(banda, "comprar", b["id"])
                p.son("rechazo", cat="interfaz")
                return app.decir(frase, True)
            mesa(frase + tr(' Tienes {dinero} euros').format(dinero=(j.dinero)), banda, "comprar", b["id"], euros, lambda e: (p.comprar_barrio(b, e), m.refrescar(False)), tr("Pedir una rebaja"))
        return f

    def tributo(banda):
        def f():
            app.decir(p.pedir_tributo(banda), True)
            m.refrescar(False)
        return f

    def ops():
        lista = [Opcion(lambda: tr('Tu fuerza en la calle: {int} de 100. Tu banda, {banda}; tus barrios, {len}').format(int=(int(p.fuerza_propia())), banda=(j.banda), len=(len(j.territorios))),
                        ayuda=tr("De tu fuerza y de cómo te lleves con cada banda depende lo que te contesten: si aceptan, cuánto pagan y cuánto piden. "
                              "Sube con más gente en tu banda, más barrios y más fama."))]
        barrios = p.mundo.barrios if p.mundo.tipo == "ciudad" else []
        for b in barrios:
            if b["id"] in j.territorios:
                lista.append(Opcion(lambda b=b: tr('Devolver {nombre} a {banda_interesada} a cambio de dinero').format(nombre=(b['nombre']), banda_interesada=(p.banda_interesada(b))), devolver(b),
                                    ayuda=tr("Les ofreces el barrio por las buenas. Si les interesa, dicen una cifra: la aceptas, pides más o lo dejas. "
                                          "Pierdes el barrio y lo que te paga cada medianoche, pero cobras de golpe y mejora tu relación con esa banda.")))
        for b in barrios:
            if b["id"] not in j.territorios:
                lista.append(Opcion(lambda b=b: tr('Comprar {nombre} a {banda_interesada}').format(nombre=(b['nombre']), banda_interesada=(p.banda_interesada(b))), comprar(b),
                                    ayuda=tr("Quedarte con el barrio pagando, sin pelear. Piden más o menos según cómo os llevéis y lo que peses en la calle, y la cifra no es la misma cada día. "
                                          "Puedes pedir una rebaja, una vez.")))
        for banda in G.nombres_bandas():
            def texto(banda=banda):
                t = j.tributos.get(banda)
                if t:
                    return tr('{banda} te paga {euros} euros cada medianoche, hasta el día {hasta}').format(banda=(banda), euros=(t['euros']), hasta=(t['hasta']))
                return tr('Cobrar un tributo a {banda}: {rep_banda_txt}').format(banda=(banda), rep_banda_txt=(p.rep_banda_txt(p.rep_banda(banda))))
            lista.append(Opcion(texto, tributo(banda),
                                ayuda=tr("Les exiges que te paguen cada día por dejarles estar. Hace falta tener algún barrio. Si te temen, pagan unos días; si no, se niegan, "
                                      "y si pesas poco pueden mandar a alguien a por ti. Mientras pagan, esa banda no ataca tus barrios.")))
        if p.rec_nivel():                                        # con la reconquista: treguas, también con las bandas forasteras
            for banda in p.rec_nombres():
                lista.append(Opcion(lambda banda=banda: (tr('Tregua con {banda} en vigor hasta el día {tregua}').format(banda=(banda), tregua=(p.rec_banda(banda)['tregua'])) if p.dia <= p.rec_banda(banda)["tregua"]
                                                         else tr('Pactar una tregua con {banda}: {v}').format(banda=(banda), v=(p.rec_banda_txt(banda).split(': ', 1)[1]))),
                                    lambda banda=banda: menu_tregua(p, banda, lambda: m.refrescar(False)), ayuda=AYUDA_TREGUA))
        return lista
    m = Menu(app, tr('Negociar con las bandas de {nombre}').format(nombre=(p.mundo.nombre)), ops, intro=tr("Devolver un barrio por dinero, comprar uno o cobrar un tributo. F1 explica cada trato"))
    app.abrir(m)
