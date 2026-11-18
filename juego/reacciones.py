"""La gente actúa, no solo habla (1.7.1).

Sin ningún modelo de inteligencia artificial: el propio juego decide, según el carácter de cada persona y la confianza
que te tenga, si después de hablar contigo te sigue un rato, te da un puñetazo tras una discusión, te denuncia o te
hace un favor. Y en la conversación hay dos opciones nuevas: pedirle un favor y proponerle que se una a tu banda, que
tiene sus condiciones (tu fama, su carácter, su confianza y una prima).

Con el modo IA, y solo si se activa aparte, el modelo puede además PROPONER una acción de una lista cerrada (seguirte,
irse, enfadarse, unirse a tu banda). Nunca la ejecuta él: la decide el juego con estas mismas reglas. En esa lista no
hay dinero ni objetos, así que nada de lo que escriba el jugador puede sacarle algo a un personaje.

Los números y las frases están en los datos (vida.json, sección reacciones).
"""
import random

from . import gente as G
from . import sistemas
from .ajustes import Ajustes

AJ = Ajustes("reacciones", {
    "seguir_confianza": 45, "seguir_prob": 35, "seguir_min": 40, "seguir_max": 100,
    "pegar_prob": 55, "pegar_dano": 9, "denuncia_prob": 35, "denuncia_puntos": 1,
    "favor_confianza": 50, "recluta_confianza": 40, "recluta_fama": 15, "recluta_valor": 25, "recluta_prima": 60, "recluta_edad_max": 62,
}, {
    "frases_sigue": ["{nombre}: Oye, voy para allá también. Te acompaño un rato.", "{nombre}: No tengo prisa. ¿Te importa si voy contigo un trecho?",
                     "{nombre}: Venga, te acompaño, que así estiro las piernas.", "{nombre} echa a andar a tu lado sin preguntar."],
    "frases_sigue_fin": ["{nombre}: Bueno, yo me quedo aquí. Ya nos veremos.", "{nombre}: Hasta aquí llego. Cuídate.", "{nombre} se despide con la mano y sigue su camino."],
    "frases_sigue_susto": ["{nombre} da media vuelta: contigo así no quiere ir.", "{nombre}: Yo de esto no quiero saber nada. Me voy."],
    "frases_comentario": ["{nombre}: Pues se está bien hoy.", "{nombre} silba algo por lo bajo mientras camina.", "{nombre}: Este barrio ya no es lo que era.",
                          "{nombre}: Hacía tiempo que no paseaba con nadie.", "{nombre}: ¿Tú vienes mucho por aquí?"],
    "frases_pega": ["{nombre} no aguanta más: te suelta un puñetazo.", "{nombre}: ¡Que me dejes en paz! Te da un empujón y un golpe.",
                    "A {nombre} se le acaba la paciencia y te cruza la cara."],
    "frases_pelea": ["{nombre} se arremanga: quiere pelea.", "{nombre}: ¡Ven aquí, que te lo explico de otra manera!"],
    "frases_denuncia": ["{nombre} se aleja con el móvil en la oreja: está dando tu descripción a la policía.",
                        "Oyes a {nombre} decir «sí, agente, aquí mismo». Te ha denunciado.", "{nombre} para a un vecino y te señala. Alguien ha llamado ya a la policía."],
    "frases_favor_tapa": ["{nombre}: Métete en mi portal, corre. Yo no he visto a nadie.", "{nombre}: Ven, por aquí. Cuando pregunten, pasaste hace una hora y hacia el otro lado."],
    "frases_favor_cura": ["{nombre}: Tienes mala cara. Toma, come algo, y siéntate un momento.", "{nombre} saca agua y una gasa del bolso y te apaña lo peor."],
    "frases_favor_pista": ["{nombre}: Ya que preguntas, he visto algo raro tirado cerca de aquí. Te digo dónde.", "{nombre}: Por ahí hay una cosa que no es de nadie. Igual te interesa."],
    "frases_favor_barrio": ["{nombre}: Descuida, que en el barrio voy a hablar bien de ti.", "{nombre}: Si alguien pregunta por ti, sabrá que eres de fiar."],
    "frases_favor_no": ["{nombre}: ¿Un favor? Si casi no te conozco.", "{nombre}: Otro día, cuando haya más confianza.", "{nombre}: No me pidas cosas, anda."],
    "frases_favor_hoy": ["{nombre}: Hoy ya te he echado una mano. No abuses."],
    "frases_recluta_si": ["{nombre}: ¿Con {banda}? Llevaba tiempo esperando algo así. Cuenta conmigo.", "{nombre} te estrecha la mano: desde hoy es de {banda}.",
                          "{nombre}: Total, peor que mi trabajo no va a ser. Me apunto."],
    "frases_recluta_no_confianza": ["{nombre}: ¿Meterme en una banda con alguien a quien acabo de conocer? Ni loc[o|a].", "{nombre}: Primero tendré que saber quién eres."],
    "frases_recluta_no_caracter": ["{nombre}: Yo no valgo para eso. Me tiemblan las piernas solo de pensarlo.", "{nombre}: No, no. Yo quiero una vida tranquila."],
    "frases_recluta_no_fama": ["{nombre}: ¿Y tú quién eres para tener banda? No te conoce nadie.", "{nombre}: Cuando tu nombre suene en la calle, hablamos."],
    "frases_recluta_no_edad": ["{nombre}: A mi edad, lo único que persigo es el autobús.", "{nombre} se ríe: ya no está para esos trotes."],
}, cero=("seguir_prob", "pegar_prob", "denuncia_prob", "denuncia_puntos", "recluta_fama", "recluta_valor", "recluta_prima"))

# Lo que el modelo de IA puede proponer, y nada más. Lo decide el juego.
ACCIONES_IA = ("nada", "se_va", "se_enfada", "te_sigue", "se_une")
BUENAS = ("cumplido", "chiste", "invitar", "limosna", "amistad", "saludar", "rumor", "barrio", "trabajo_npc")


class Reacciones:
    """Mixin de Partida."""

    def reacciones_iniciar(self):
        self.t_seguidor = 0.0

    def gente_actua(self):
        return bool(self.cfg["gente_actua"])

    # ------------------------------------------------------------------ lo que decide el juego tras cada frase
    def reaccion_tras(self, q, intencion, antes):
        """Después de contestarte, la persona puede hacer algo. Devuelve la frase que lo cuenta, o cadena vacía.
        `antes` es la confianza que te tenía antes de lo que le has dicho."""
        if not self.gente_actua() or q.muerto or q.hostil or q not in self.personas:
            return ""
        from .charla import ficha
        f = ficha(q)
        c = G.caracter(f["caracter"])
        if intencion == "insultar" and q.estado == "huye" and self.mundo.policia and random.random() * 100 < AJ("denuncia_prob") * (1.2 - c["valor"]):
            return self.denunciar(q)
        if intencion in BUENAS and f["confianza"] > antes and f["confianza"] >= AJ("seguir_confianza") and not f.get("ha_seguido") and q.estado != "sigue":
            ganas = AJ("seguir_prob") * {"hablador": 1.5, "amable": 1.2, "chulo": 0.9, "timido": 0.5, "seco": 0.4}.get(G.habla_de(f["caracter"]), 1.0)
            if random.random() * 100 < ganas:
                return self.seguirte(q)
        return ""

    def insistir(self, q):
        """Le hablas a alguien que ya no quiere saber nada de ti. Según su carácter, se aguanta, te pega o quiere pelea.
        Devuelve la frase, o cadena vacía si se limita a ignorarte."""
        if not self.gente_actua() or q.muerto or q.hostil:
            return ""
        from .charla import ficha
        f = ficha(q)
        valor = G.caracter(f["caracter"])["valor"]
        f["insistencias"] = f.get("insistencias", 0) + 1
        if f.get("ha_pegado") or random.random() * 100 >= AJ("pegar_prob") * (0.3 + valor) * min(2, f["insistencias"]):
            return ""
        return self.pegarte(q)

    # ------------------------------------------------------------------ las acciones
    def seguirte(self, q):
        from .charla import ficha
        f = ficha(q)
        if self.j.veh or q.estado == "huye" or q.hostil:
            return ""
        f["ha_seguido"] = True
        q.estado = "sigue"
        q.sigue_hasta = self.t + AJ.entre("seguir_min", "seguir_max")
        q.t_comenta = self.t + random.uniform(12, 25)
        self.j.stats["acompanantes"] = self.j.stats.get("acompanantes", 0) + 1
        self.son("afinidad_sube", cat="interfaz", vol=0.5)
        return AJ.frase("frases_sigue", nombre=f["nombre"])

    def dejar_de_seguir(self, q, frase="frases_sigue_fin", callar=False):
        from .charla import ficha
        if q.estado == "sigue":
            q.estado = "pasea" if q.bloque is not None else "quieto"
        q.sigue_hasta = None
        if not callar and not q.muerto:
            self.decir(AJ.frase(frase, nombre=ficha(q)["nombre"]))

    def paso_seguidor(self, q, dt):
        """Cada fotograma, quien te acompaña: camina a tu lado, comenta algo de vez en cuando y al rato se despide."""
        j = self.j
        x, y = self.pos()
        d = q.dist(x, y)
        if j.veh or j.estrellas or d > 45 or self.t > (getattr(q, "sigue_hasta", None) or 0) or self.mundo.tipo == "mar":
            self.dejar_de_seguir(q, "frases_sigue_susto" if j.estrellas else "frases_sigue_fin", callar=d > 45)
            return
        if d > 3.0:
            self._andar_hacia(q, x, y, 4.6 if d > 9 else 2.6, dt)
            q.t_paso -= dt
            if q.t_paso <= 0:
                q.t_paso = 0.45
                self.son("paso_npc", xy=(q.x, q.y), ref=3, maxd=28, vol=0.7)
        if self.t > getattr(q, "t_comenta", 1e18):
            from .charla import ficha
            q.t_comenta = self.t + random.uniform(18, 35)
            self.son("murmullo", xy=(q.x, q.y), vol=0.4)
            self.decir(AJ.frase("frases_comentario", nombre=ficha(q)["nombre"]))
            self.cambiar_animo(1)

    def pegarte(self, q):
        from .charla import ficha
        f = ficha(q)
        valor = G.caracter(f["caracter"])["valor"]
        f["ha_pegado"] = True
        self.son("golpe", xy=(q.x, q.y), ref=4)
        self.danar_jugador(AJ("pegar_dano") * random.uniform(0.7, 1.3), (q.x, q.y))
        self.j.stats["bofetadas"] = self.j.stats.get("bofetadas", 0) + 1
        q.agresor = True                                         # ha empezado esa persona: si respondes, es defensa propia
        if valor >= 0.6:                                         # con carácter: se queda a pelear, a puñetazos
            q.hostil, q.estado, q.tipo, q.arma = True, "ataca", "enemigo", None
            return AJ.frase("frases_pega", nombre=f["nombre"]) + " " + AJ.frase("frases_pelea", nombre=f["nombre"])
        q.estado, q.t_estado = "huye", 8
        return AJ.frase("frases_pega", nombre=f["nombre"]) + " Y se marcha."

    def denunciar(self, q):
        from .charla import ficha
        f = ficha(q)
        self.j.stats["denuncias"] = self.j.stats.get("denuncias", 0) + 1
        if AJ("denuncia_puntos") > 0:
            self.delito(AJ("denuncia_puntos"), "insultos y amenazas", siempre=True)
        return AJ.frase("frases_denuncia", nombre=f["nombre"])

    def pedir_favor(self, q):
        """Le pides un favor. Lo que hace depende de cómo estés tú: te tapa de la policía, te apaña una herida, te da una
        pista o habla bien de ti. Una vez al día por persona, y con confianza."""
        from .charla import ficha
        f = ficha(q)
        n = f["nombre"]
        j = self.j
        self.son("murmullo", xy=(q.x, q.y), vol=0.5)
        if f["confianza"] < AJ("favor_confianza"):
            self._trato(f, -2)
            return AJ.frase("frases_favor_no", nombre=n)
        if f.get("favor_dia") == self.dia:
            return AJ.frase("frases_favor_hoy", nombre=n)
        f["favor_dia"] = self.dia
        j.stats["favores"] = j.stats.get("favores", 0) + 1
        x, y = self.pos()
        cerca_poli = any(p.tipo == "policia" and not p.muerto and p.dist(x, y) < 40 for p in self.personas)
        if 1 <= j.estrellas <= 2 and not cerca_poli and not self.sv_policia_comun():
            self.pasar_horas(0.5)
            self._fin_persecucion()
            return AJ.frase("frases_favor_tapa", nombre=n) + " Media hora después, la policía ha dejado de buscarte."
        if j.salud < j.salud_max * 0.6:
            j.salud = min(j.salud_max, j.salud + 25)
            self.ha_comido(20)
            self.mez.sonar("curar", cat="interfaz")
            return AJ.frase("frases_favor_cura", nombre=n) + f" Salud {int(j.salud)}."
        cosas = [o for o in self.objetos if o.tipo == "casete"]
        if cosas:
            o = min(cosas, key=lambda o: o.dist(x, y))
            self.fijar_gps(o.x, o.y, o.nombre, radio=3, callar=True)
            return AJ.frase("frases_favor_pista", nombre=n) + f" {self.situar(o.x, o.y, 'Está')}. Te lo marco en el GPS."
        self.cambiar_ciudadania(2.0)
        self.cambiar_animo(2)
        return AJ.frase("frases_favor_barrio", nombre=n)

    # ------------------------------------------------------------------ reclutar
    def prima_recluta(self):
        return int(self.precio("recluta", sistemas.PRECIO_RECLUTA) * AJ("recluta_prima") / 100.0)

    def recluta_motivo(self, q):
        """Por qué esta persona no se une a tu banda: ("", "") si se uniría, o (clave de la frase, explicación para ti)."""
        from .charla import ficha
        j = self.j
        f = ficha(q)
        if self.en_servidor:
            return "x", "En un servidor en línea la banda es de jugadores: no se recluta a la gente de la calle."
        if not j.territorios:
            return "frases_recluta_no_fama", "Para tener banda necesitas un territorio. Conquista o compra un barrio primero."
        if j.banda >= sistemas.cupo(j):
            return "x", f"Con {len(j.territorios)} territorios no puedes mantener a más de {sistemas.cupo(j)}."
        if f["edad"] > AJ("recluta_edad_max"):
            return "frases_recluta_no_edad", ""
        if G.caracter(f["caracter"])["valor"] * 100 < AJ("recluta_valor"):
            return "frases_recluta_no_caracter", ""
        if f["confianza"] < AJ("recluta_confianza"):
            return "frases_recluta_no_confianza", ""
        if j.reputacion < AJ("recluta_fama"):
            return "frases_recluta_no_fama", ""
        return "", ""

    def reclutar_persona(self, q, cobrar=True):
        """Le propones a alguien de la calle que se una a tu banda. Devuelve (se ha unido, frase)."""
        from .charla import ficha
        j = self.j
        f = ficha(q)
        n = f["nombre"]
        clave, explicacion = self.recluta_motivo(q)
        if clave:
            if clave == "x":
                return False, explicacion
            f["recluta_no"] = self.dia
            self._trato(f, -1)
            return False, AJ.frase(clave, nombre=n) + (" " + explicacion if explicacion else "")
        prima = self.prima_recluta() if cobrar else 0
        if j.dinero < prima:
            return False, f"{n} se uniría, pero quiere una prima de {prima} euros para dejar lo que tiene, y no te llega."
        j.dinero -= prima
        j.banda += 1
        if not j.banda_nombre:
            j.banda_nombre = random.choice(G.lista("bandas_propias"))
        j.stats["reclutados_calle"] = j.stats.get("reclutados_calle", 0) + 1
        # deja de ser un peatón: desde ahora es de los tuyos, con su nombre
        q.tipo, q.estado, q.hostil, q.de_banda = "aliado", "sigue", False, True
        q.nombre = f"{n}, de {j.banda_nombre}"
        q.salud = max(q.salud, 95.0)
        q.arma = random.choice(["pistola", "pistola", "bate", "navaja"])
        q.sigue_hasta = None
        self.son("pareja", cat="interfaz", vol=0.5)
        return True, (AJ.frase("frases_recluta_si", nombre=n, banda=j.banda_nombre)
                      + (f" Le das {prima} euros de prima." if prima else "") + f" Ya sois {j.banda} además de ti. Cobra {self.precio('sueldo_banda', sistemas.SUELDO)} euros cada medianoche, como los demás.")

    # ------------------------------------------------------------------ lo que propone la IA, decidido por el juego
    def ia_acciones(self):
        return bool(self.cfg["ia_acciones"]) and bool(self.cfg["ia_activa"])

    def decidir_accion_ia(self, q, accion):
        """El modelo ha propuesto una acción de la lista cerrada. El juego decide si pasa, con sus reglas de siempre.
        Devuelve la frase que cuenta lo que ha pasado, o cadena vacía si no pasa nada."""
        from .charla import ficha
        f = ficha(q)
        if accion not in ACCIONES_IA or accion == "nada":
            return ""
        if accion == "se_va":
            q.estado, q.t_estado = "huye", 6
            return ""
        if accion == "se_enfada":
            f["ofendido"] = True
            return self.insistir(q) if self.ia_acciones() else ""
        if not self.ia_acciones():                               # sin la opción, la IA solo puede irse o enfadarse, como siempre
            return ""
        if accion == "te_sigue":
            if f["confianza"] >= AJ("seguir_confianza") * 0.6 and not f["ofendido"] and not f.get("ha_seguido"):
                return self.seguirte(q)
            return ""
        if accion == "se_une":
            if self.recluta_motivo(q)[0]:
                return ""                                        # no cumple las condiciones: se queda en palabras
            return self.reclutar_persona(q)[1]
        return ""

    def actualizar_reacciones(self, dt):
        pass                                                     # quien te acompaña se mueve desde actualizar_personas (paso_seguidor)
