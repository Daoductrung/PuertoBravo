"""Jugar como policía (1.7.1): un oficio más, y un modo opcional que viene apagado.

Con el modo encendido, en cualquier comisaría puedes ingresar en la policía (un curso, y hace falta que los vecinos te
aprecien algo). Ya de agente, empiezas el turno en una comisaría: te dan un coche patrulla y la emisora te va pasando
avisos: un robo en un local, una pelea, un conductor temerario, una persecución. Acudes, y los resuelves como es
debido: dando el alto, reduciendo a quien se resiste, deteniendo, multando o dejándolo en un aviso. Cada aviso resuelto
se paga, y con los avisos llegan los ascensos.

Mientras estás de servicio, usar la fuerza contra los sospechosos de un aviso no es delito. Lo demás, sí: una falta
pequeña es un apercibimiento, y con tres, o con un delito serio, te quitan la placa y la policía va a por ti como a
cualquiera. Abatir a quien podías detener se paga peor y también cuenta.

Todo es original de este juego. Los avisos están en los datos (vida.json, avisos_policia) y los números, los rangos y
las frases, en la sección policia_oficio. Solo en solitario.
"""
from .i18n import tr
import math
import random

from . import gente as G
from .ajustes import Ajustes
from .entidades import Persona

AJ = Ajustes("policia_oficio", {
    "ciudadania_minima": 30, "curso_horas": 8, "ascenso_cada": 6, "rango_extra": 15, "espera_min": 12, "espera_max": 35,
    "llegada_base": 70, "llegada_por_metro": 0.25, "rendicion_salud": 45, "alto_prob": 45, "alto_arma": 20, "pelea_alto_prob": 60,
    "temerario_obedece": 70, "temerario_segundos": 3, "persecucion_salud": 55, "multa_importe": 120, "multa_comision": 25,
    "apercibimientos": 3, "expulsion_dias": 7, "bono_rapidez": 40, "radio_fuerza": 120, "radio_fuerza_vehiculo": 300, "abandono_metros": 170,
}, {
    "rangos": [tr("agente en prácticas"), tr("agente de policía"), tr("oficial de policía"), tr("subinspector[|a]"), tr("inspector[|a]"), tr("comisari[o|a]")],
    "frases_ingreso": [tr("Firmas, juras y te dan una placa que pesa más de lo que parece. Ya eres agente en prácticas."),
                       tr("Ocho horas de teoría, tiro y normas. Al salir llevas placa y un número de agente.")],
    "frases_turno": [tr("Central a todas las unidades: {nombre} entra de servicio. Buen turno."), tr("Fichas, coges las llaves y la emisora cruje: estás de servicio."),
                     tr("El sargento te tira las llaves: «El de la puerta es el tuyo. Y devuélvelo entero».")],
    "frases_fin": [tr("Central: recibido. Fin del turno."), tr("Dejas las llaves en el mostrador de guardia. Turno terminado.")],
    "frases_tarde": [tr("Central: otra unidad se ha hecho cargo. Vuelva a la ronda."), tr("Central: ya no hace falta que vaya. Ha llegado tarde.")],
    "frases_abandono": [tr("Central: ha abandonado el aviso. Otra unidad se hace cargo."), tr("Central: le hemos perdido en el aviso. Mandamos a otra unidad.")],
    "frases_alto": [tr("¡Alto, policía!"), tr("¡Policía! ¡Quieto ahí!"), tr("¡Alto! ¡Las manos donde yo las vea!")],
    "frases_se_rinde": [tr("{nombre} levanta las manos: ¡Vale, vale! ¡No dispares!"), tr("{nombre} tira lo que lleva y se queda inmóvil: se rinde."),
                        tr("{nombre} se deja caer de rodillas con las manos en la nuca.")],
    "frases_no_obedece": [tr("{nombre} no obedece."), tr("{nombre} hace como que no te ha oído."), tr("{nombre} te mira y echa a correr más deprisa.")],
    "frases_detenido": [tr("Le pones las esposas. Una unidad se lo lleva a comisaría."), tr("Esposado y leído. Llega un furgón y se hace cargo."), tr("Detenido. La central manda a alguien a recogerlo.")],
    "frases_abatido": [tr("Central: sospechoso abatido. Tendrá que hacer el informe."), tr("Lo comunicas por la emisora: ha caído. No era lo que se esperaba de usted.")],
    "frases_excesivo": [tr("Asuntos internos abre expediente: has usado más fuerza de la debida."), tr("Te llaman al despacho: eso no era necesario, y queda apuntado.")],
    "frases_escapa": [tr("Central: el sospechoso se ha perdido. Vuelva a la ronda."), tr("Se te ha escapado. La central anota la descripción y sigue.")],
    "frases_pelea_calma": [tr("Se separan refunfuñando y cada uno se va por su lado."), tr("Uno pide perdón, el otro se sacude la ropa. Aquí no ha pasado nada."),
                           tr("Bajan los puños. Les tomas el nombre y los mandas a casa.")],
    "frases_pelea_bronca": [tr("Uno de ellos se revuelve contra ti: «¡Tú no te metas!»."), tr("El más grande decide que ahora la pelea es contigo.")],
    "frases_para": [tr("El conductor ve las luces, pone el intermitente y se arrima a la acera. Acércate y pulsa Intro."),
                    tr("Frena y para a la derecha. Te espera con las manos en el volante: acércate y pulsa Intro.")],
    "frases_no_para": [tr("¡No para! Acelera y se salta el cruce: ahora es una persecución. Embístele hasta que se detenga."),
                       tr("Mira por el retrovisor y pisa a fondo. Persecución: hay que pararle a golpes.")],
    "frases_vehiculo_rinde": [tr("El vehículo echa humo y se queda cruzado en la calzada. Acércate y pulsa Intro."), tr("Se acabó: se le cala y no arranca. Acércate y pulsa Intro.")],
    "frases_conductor_corre": [tr("¡El conductor abre la puerta y sale corriendo! Dale el alto con la H o alcánzale."), tr("Salta del coche y echa a correr. ¡A por él!")],
    "frases_multa": [tr("Firma la multa de mala gana: {euros} euros."), tr("Le entregas el boletín: {euros} euros y puntos. Protesta, pero firma.")],
    "frases_aviso": [tr("Le dejas ir con un aviso. Te da las gracias tres veces."), tr("Por esta vez, un aviso. Arranca despacio, como si llevara huevos.")],
    "frases_apercibimiento": [tr("Apercibimiento: {motivo}, estando de servicio. Llevas {n} de {tope}."), tr("La central toma nota: {motivo}. Apercibimiento {n} de {tope}.")],
    "frases_expulsion": [tr("Asuntos internos te quita la placa: {motivo}. Estás fuera del cuerpo."), tr("Se acabó: {motivo}. Entregas la placa y vacías la taquilla.")],
    "frases_ascenso": [tr("¡Ascenso! Desde hoy eres {rango}: cobras un {extra} por ciento más por aviso."), tr("El comisario te llama al despacho: te ascienden a {rango}.")],
}, cero=("bono_rapidez", "alto_arma", "multa_comision", "rango_extra", "llegada_por_metro"))

AVISOS = [
    {"id": "robo_local", "tipo": "robo", "nombre": tr("Robo en un local"), "peso": 3, "paga": 160, "sospechoso": "atracador", "n_min": 1, "n_max": 2,
     "frases": [tr("Central a patrulla: alarma de robo en {lugar}. Acuda."), tr("Central: nos avisan de un atraco en curso en {lugar}. Unidad más cercana, acuda.")]},
    {"id": "pelea_calle", "tipo": "pelea", "nombre": tr("Pelea en la calle"), "peso": 3, "paga": 110, "sospechoso": "maton",
     "frases": [tr("Central a patrulla: pelea en la vía pública junto a {lugar}."), tr("Central: dos individuos a golpes delante de {lugar}. Vaya a poner orden.")]},
    {"id": "temerario", "tipo": "temerario", "nombre": tr("Conductor temerario"), "peso": 3, "paga": 130, "modelos": ["sedan", "utilitario", "deportivo", "furgoneta", "pickup"],
     "frases": [tr("Central a patrulla: un {modelo} circulando de forma temeraria cerca de {lugar}. Dele el alto: póngase detrás con la sirena."),
                tr("Central: varios avisos de un {modelo} saltándose semáforos por {lugar}. Párelo.")]},
    {"id": "persecucion", "tipo": "persecucion", "nombre": tr("Persecución"), "peso": 2, "paga": 240, "sospechoso": "atracador", "modelos": ["deportivo", "sedan", "todoterreno"],
     "frases": [tr("Central a todas las unidades: {modelo} a la fuga tras un atraco, visto junto a {lugar}. Intercéptelo."),
                tr("Central: vehículo robado, un {modelo}, huyendo desde {lugar}. No lo pierda.")]},
]
TIPOS = ("robo", "pelea", "temerario", "persecucion")


def avisos(p):
    lista = [a for a in p.datos.get("avisos_policia", []) if isinstance(a, dict) and a.get("tipo") in TIPOS]
    return lista or AVISOS


class Agente:
    """Mixin de Partida."""

    def agente_iniciar(self):
        self.t_alto = -99.0

    # ------------------------------------------------------------------ el modo y el puesto
    def policia_activa(self):
        """¿Se puede jugar de policía? Con el modo encendido y fuera de un servidor."""
        return bool(self.cfg["oficio_policia"]) and not self.en_servidor

    def es_agente(self):
        return self.policia_activa() and bool(self.j.policia.get("alta"))

    def de_servicio(self):
        t = self.trabajo
        return bool(t and t.get("tipo") == "policia")

    def rango_policia(self):
        return min(len(AJ.lista("rangos")) - 1, int(self.j.stats.get("serv_policia", 0)) // max(1, AJ.entero("ascenso_cada")))

    def rango_policia_txt(self):
        return AJ.lista("rangos")[self.rango_policia()]

    def ingreso_motivo(self):
        j = self.j
        pol = j.policia
        if not self.policia_activa():
            return tr("El oficio de policía está desactivado. Se activa en Opciones, La calle.")
        if pol.get("alta"):
            return tr("Ya eres agente.")
        if int(pol.get("expulsado", 0)) >= self.dia:
            return tr('Te quitaron la placa. No puedes volver a presentarte hasta el día {v}.').format(v=(int(pol['expulsado']) + 1))
        if j.estrellas:
            return tr("Con la policía buscándote, lo de ingresar en el cuerpo va a ser que no.")
        if j.ciudadania < AJ("ciudadania_minima"):
            return tr("No te admiten: los vecinos no hablan lo bastante bien de ti. Sube tu prestigio con trabajo honrado, cursos, donativos o ayudando en los sucesos.")
        if self.hon_antecedentes():
            return tr("No te admiten: tienes antecedentes penales en vigor. Espera a que caduquen, o atenúalos con servicios a la comunidad o con un abogado; lo tienes en el móvil, en Vida, reputación y consecuencias.")
        return ""

    def ingresar_policia(self):
        motivo = self.ingreso_motivo()
        if motivo:
            self.app.son("error")
            self.decir(motivo, True)
            return False
        if not self.pagar(self.precio("academia_policia", 400)):
            return False
        j = self.j
        j.policia = {"alta": self.dia, "apercibimientos": 0, "detenciones": 0, "multas": 0, "bajas": 0, "avisos": 0}
        self.pasar_horas(AJ("curso_horas"))
        self.son("diploma", cat="interfaz")
        self.cambiar_ciudadania(3.0)
        self.decir(AJ.frase("frases_ingreso") + tr(' Son las {hora_txt}. Para trabajar, empieza el turno en una comisaría.').format(hora_txt=(self.hora_txt())), True)
        return True

    def dejar_policia(self):
        """Cuelgas la placa por tu cuenta: sin castigo, y puedes volver a ingresar pagando el curso."""
        if self.de_servicio():
            self.terminar_trabajo(None)
        self.j.policia = {}
        self.decir(tr("Entregas la placa. Ya no eres agente. Si cambias de idea, puedes volver a presentarte."), True)

    # ------------------------------------------------------------------ el turno
    def turno_motivo(self):
        j = self.j
        if not self.es_agente():
            return tr("No eres agente de policía.")
        if self.mision or self.guerra:
            return tr("Termina antes lo que tienes entre manos.")
        if j.estrellas:
            return tr("Con la policía buscándote no puedes entrar de servicio.")
        if self.mundo.tipo in ("mar", "isla") or not self.mundo.policia:
            return tr("Aquí no hay servicio de patrulla.")
        return ""

    def empezar_turno(self, comisaria=None, veh=None):
        """Entras de servicio. En una comisaría te dan un coche patrulla; si ya vas en uno, con ese."""
        motivo = self.turno_motivo()
        if motivo:
            self.app.son("error")
            self.decir(motivo, True)
            return False
        if self.trabajo:
            self.terminar_trabajo(None)
        while len(self.app.pila) > 1 and self.app.pila[-1] is not self:
            self.app.pila.pop()
        self.app.teclas.clear()
        self.salir_interior(silencio=True)
        j = self.j
        patrulla = veh
        if patrulla is None and comisaria is not None and "patrulla" in self.modelos and not j.veh:
            x, y, d = self.mundo.plaza_junto_a(comisaria)
            self._despejar_plaza(x, y)
            patrulla = self.crear_vehiculo("patrulla", x, y, d, "aparcado", tr("Tu coche patrulla"), "servicio")
            patrulla.sirena = self.son("loc_vehiculo", bucle=True, xy=(x, y), ref=5, maxd=70)
            patrulla.propio = True                               # te lo han dado: subirte no es robarlo
        self.trabajo = {"tipo": "policia", "patrulla": patrulla, "prestada": veh is None and patrulla is not None, "hechas": 0, "ganado": 0, "limite": None,
                        "aviso": None, "espera": AJ.entre("espera_min", "espera_max") * 0.5, "texto": tr("Estás de servicio: a la espera de un aviso de la emisora.")}
        self.son("emisora", cat="interfaz")
        donde = tr(' Tu coche patrulla está aparcado ahí mismo: {situar}. Sube con F.').format(situar=(self.situar(patrulla.x, patrulla.y, 'está'))) if patrulla is not None and veh is None else ""
        self.decir(AJ.frase("frases_turno", nombre=j.nombre) + donde + tr(" La emisora te pasará los avisos. La P enciende la sirena; la H, a pie, da el alto. "
                   "Para terminar el turno, pulsa J en el coche patrulla o vuelve a una comisaría."))
        return True

    def fin_turno_limpieza(self, t):
        """Al acabar el turno, por lo que sea: se retira lo del aviso en curso y se devuelve el coche patrulla prestado."""
        self._aviso_limpiar(t.get("aviso"))
        t["aviso"] = None
        v = t.get("patrulla")
        if v is not None and t.get("prestada") and not v.muerto and v in self.vehiculos:
            if self.j.veh is v:
                self.salir_vehiculo(forzado=True)
            self.quitar_vehiculo(v)

    def terminar_turno(self):
        if not self.de_servicio():
            return
        self.son("emisora", cat="interfaz", vol=0.6)
        self.terminar_trabajo(AJ.frase("frases_fin"))

    # ------------------------------------------------------------------ faltas y delitos estando de servicio
    def _sospechoso_cerca(self, radio=None):
        t = self.trabajo or {}
        a = t.get("aviso")
        if not a:
            return False
        x, y = self.pos()
        radio = AJ("radio_fuerza") if radio is None else radio
        if any(not s.muerto and s.dist(x, y) < radio for s in a.get("sospechosos", [])):
            return True
        v = a.get("veh")
        if v is not None and a.get("fase") == "seguir" and (a.get("tipo") == "persecucion" or a.get("huyo")):
            radio = max(radio, AJ("radio_fuerza_vehiculo"))      # huye en coche: se aleja deprisa, y pararlo a tiros o a golpes es lo que toca
        return v is not None and not v.muerto and v.dist(x, y) < radio

    def delito_de_servicio(self, puntos, texto):
        """Has hecho algo que sería delito, estando de servicio. Devuelve True si no cuenta como tal: la fuerza contra los
        sospechosos de un aviso está justificada, y una falta pequeña se queda en un apercibimiento. Con un delito serio,
        o al tercer apercibimiento, te quitan la placa y entonces sí cuenta."""
        if not self.de_servicio():
            return False
        if texto in (None, "disparos en la vía pública") and self._sospechoso_cerca():
            return True
        motivo = texto or tr("uso indebido de la fuerza")
        if puntos >= 2:
            self.expulsar_policia(motivo)
            return False
        return not self.apercibir(motivo)

    def apercibir(self, motivo):
        """Un apercibimiento. Devuelve True si con este te expulsan."""
        pol = self.j.policia
        pol["apercibimientos"] = int(pol.get("apercibimientos", 0)) + 1
        tope = AJ.entero("apercibimientos")
        if pol["apercibimientos"] >= tope:
            self.expulsar_policia(motivo)
            return True
        self.son("multa", cat="interfaz")
        self.decir(AJ.frase("frases_apercibimiento", motivo=motivo, n=pol["apercibimientos"], tope=tope))
        return False

    def expulsar_policia(self, motivo):
        j = self.j
        if not j.policia.get("alta"):
            return
        j.policia = {"expulsado": self.dia + AJ.entero("expulsion_dias")}
        j.stats["expulsiones_policia"] = j.stats.get("expulsiones_policia", 0) + 1
        if self.de_servicio():
            self.terminar_trabajo(None)
        self.son("mision_fallo", cat="interfaz")
        self.cambiar_ciudadania(-6.0)
        self.decir(AJ.frase("frases_expulsion", motivo=motivo))

    # ------------------------------------------------------------------ rendirse: sospechosos y morosos
    def se_rinde_con(self, p, dano):
        """Un golpe a alguien a quien hay que detener o solo asustar: si con él queda bastante tocado, se rinde en vez de
        caer. Devuelve True si se ha rendido (y entonces el golpe no le hace más)."""
        if getattr(p, "rendido", False) or not (getattr(p, "sospechoso", False) or getattr(p, "intimidar", False)):
            return False
        entera = float(getattr(p, "salud_entera", p.salud) or p.salud)
        if p.salud - dano > entera * AJ("rendicion_salud") / 100.0 or dano >= entera * 2.5:      # o aguanta, o era una barbaridad: eso no hay quien lo sobreviva
            return False
        p.salud = max(1.0, min(p.salud, entera * 0.25))
        self.rendir_persona(p)
        return True

    def rendir_persona(self, p, frase=True):
        p.rendido = True
        p.hostil, p.estado, p.t_estado, p.arma = False, "quieto", 0.0, None
        p.ha_resistido = bool(getattr(p, "ha_resistido", False) or getattr(p, "agresor_real", False))
        if self.objetivo is p:
            self.objetivo = None
        self.voz_persona(p, "dolor")
        if frase:
            if getattr(p, "intimidar", False):
                self.decir(tr('{nombre} suelta lo que lleva y se encoge: ').format(nombre=(p.nombre)) + random.choice([tr("¡Ya, ya! ¡Mañana tiene su dinero!"), tr("¡Basta! ¡Pago, pago!"), tr("¡Vale! ¡Lo he entendido!")]) + tr(" Ya está: no le toques más."))
            else:
                self.decir(AJ.frase("frases_se_rinde", nombre=p.nombre) + tr(" Acércate y pulsa Intro para detenerle."))

    # ------------------------------------------------------------------ dar el alto
    def dar_alto(self):
        """La H, a pie y de servicio: das el alto. A veces basta."""
        t = self.trabajo or {}
        a = t.get("aviso")
        if not self.de_servicio() or not a:
            return False
        j = self.j
        cerca = [s for s in a.get("sospechosos", []) if not s.muerto and not getattr(s, "rendido", False) and s.dist(j.x, j.y) < 18]
        if not cerca and not (a["tipo"] == "pelea" and a.get("fase") == "pelea" and a["lugar_xy"] and math.hypot(a["lugar_xy"][0] - j.x, a["lugar_xy"][1] - j.y) < 20):
            return False
        self.decir(AJ.frase("frases_alto"), True)
        if self.t - self.t_alto < 4.0:
            return True                                          # no por gritar más seguido obedecen antes
        self.t_alto = self.t
        if a["tipo"] == "pelea" and a.get("fase") == "pelea":
            self._pelea_alto(a)
            return True
        armado = self.arma()["tipo"] == "fuego"
        for s in cerca:
            if getattr(s, "alto_dado", 0) >= 2:
                continue
            s.alto_dado = getattr(s, "alto_dado", 0) + 1
            prob = AJ("alto_prob") + (AJ("alto_arma") if armado else 0) + (20 if s.estado == "huye" and not s.hostil else 0) - 25 * (s.alto_dado - 1)
            if random.random() * 100 < prob:
                self.rendir_persona(s)
            else:
                self.decir(AJ.frase("frases_no_obedece", nombre=s.nombre))
        return True

    # ------------------------------------------------------------------ los avisos
    def _sospechoso(self, clase, x, y, nombre):
        f = G.enemigo(G.grupo(clase, tipo=nombre, arma="navaja", salud=70))
        e = G.vestir(Persona("enemigo", *self.mundo.punto_libre(x + random.uniform(-4, 4), y + random.uniform(-4, 4)), nombre or f["nombre"]), f)
        e.nombre = nombre or f["nombre"]
        e.salud_entera = e.salud
        e.sospechoso, e.tag, e.agresor, e.activo = True, "aviso", True, True
        e.hostil, e.estado = False, "quieto"
        e.t_disparo = random.uniform(1.5, 2.5)
        self.personas.append(e)
        return e

    def _aviso_nuevo(self):
        t = self.trabajo
        x, y = self.pos()
        m = self.mundo
        con_calles = m.tipo != "mar" and m.NX >= 2 and m.NY >= 2
        ops = [a for a in avisos(self) if a["tipo"] in ("robo", "pelea") or (con_calles and any(mo in self.modelos for mo in (a.get("modelos") or ["sedan"])))]
        if not ops:
            return
        d = random.choices(ops, weights=[max(0.01, float(a.get("peso", 1) or 1)) for a in ops])[0]
        lugares = [l for l in m.lugares.values() if l.tipo not in ("salida", "muelle", "embarcadero", "comisaria") and "xy" not in l.d]
        if d["tipo"] == "robo":
            con_caja = [l for l in lugares if G.caja_local(l.tipo) is not None]
            lugares = con_caja or lugares
        lejos = 380 if d["tipo"] in ("temerario", "persecucion") else 650      # a un vehículo que huye hay que poder alcanzarlo
        cerca = [l for l in lugares if 120 <= math.hypot(l.x - x, l.y - y) <= lejos] or sorted(lugares, key=lambda l: math.hypot(l.x - x, l.y - y))[:3]
        if not cerca:
            return
        l = random.choice(cerca)
        dist = math.hypot(l.x - x, l.y - y)
        modelos = [mo for mo in (d.get("modelos") or ["sedan"]) if mo in self.modelos] or ["sedan"]
        modelo = random.choice(modelos)
        a = {"def": d, "tipo": d["tipo"], "lugar": l, "lugar_xy": (l.x, l.y), "fase": "ir", "sospechosos": [], "veh": None, "modelo": modelo,
             "limite": AJ("llegada_base") + dist * AJ("llegada_por_metro"), "plazo": AJ("llegada_base") + dist * AJ("llegada_por_metro"), "t0": self.t, "detenidos": 0, "abatidos": 0, "escapados": 0, "excesos": 0, "extra": 0, "pacifico": False}
        t["aviso"] = a
        frases = [str(f) for f in (d.get("frases") or []) if str(f).strip()] or [tr("Central a patrulla: aviso en {lugar}.")]
        texto = random.choice(frases).replace("{lugar}", l.nombre).replace("{modelo}", self.modelos[modelo]["nombre"])
        t["texto"] = f"{d.get('nombre', tr('Aviso'))}: {l.nombre}."
        self.son("emisora", cat="interfaz")
        if d["tipo"] in ("temerario", "persecucion"):
            self._aviso_vehiculo(a)
        else:
            self.gps_a_lugar(l, auto=True, callar=True)
        self.decir(texto + tr(' {situar}. Tienes {int} segundos para llegar.').format(situar=(self.situar(l.x, l.y, tr('Está'))), int=(int(a['limite']))))
        if self.gps:
            self.repetir_gps_suave()

    def _aviso_vehiculo(self, a):
        l, m = a["lugar"], self.mundo
        x, y, d = m.plaza_junto_a(l)
        x, y = (x, m.carril("H", m._idx(y, m.NY), d)) if d in (1, 3) else (m.carril("V", m._idx(x, m.NX), d), y)
        mo = self.modelos[a["modelo"]]
        v = self.crear_vehiculo(mo["id"], x, y, d, "huida", f"{mo['nombre']} {tr('a la fuga') if a['tipo'] == 'persecucion' else tr('del conductor temerario')}", "objetivo")
        v.ocupado = True
        v.hostil = a["tipo"] == "persecucion"
        v.vel_obj = min(mo["vel_max"] * (0.6 if a["tipo"] == "persecucion" else 0.45), 20.0 if a["tipo"] == "persecucion" else 15.0)
        a["veh"], a["fase"], a["t_detras"] = v, "seguir", 0.0
        a["limite"] = a["plazo"] = max(a["limite"], 150.0)
        self.objetivo = v
        self.fijar_gps(v.x, v.y, v.nombre, sigue=v, auto=True, callar=True)
        if a["tipo"] == "persecucion":
            self.agente_como_parar()

    def _aviso_limpiar(self, a):
        if not a:
            return
        for s in a.get("sospechosos", []):
            if s in self.personas and not s.muerto:
                self.personas.remove(s)
        v = a.get("veh")
        if v is not None and not v.muerto and v in self.vehiculos and v is not self.j.veh:
            self.quitar_vehiculo(v)
        if self.gps:
            self.quitar_gps_auto()
        if self.objetivo is v or self.objetivo in a.get("sospechosos", []):
            self.objetivo = None

    def _aviso_fin(self, texto, pagar=True):
        """Se cierra el aviso en curso: se paga según cómo haya acabado y la emisora queda a la espera del siguiente."""
        t = self.trabajo
        a = t.get("aviso")
        if not a:
            return
        j, pol = self.j, self.j.policia
        d = a["def"]
        total = max(1, a["detenidos"] + a["abatidos"] + a["escapados"]) if a["tipo"] != "pelea" or not a["pacifico"] else 1
        bien = a["detenidos"] + (1 if a["pacifico"] else 0)
        parte = min(1.0, (bien + 0.5 * a["abatidos"]) / total) if pagar else 0.0
        self._aviso_limpiar(a)
        t["aviso"] = None
        t["espera"] = AJ.entre("espera_min", "espera_max")
        t["texto"] = tr("Estás de servicio: a la espera de un aviso de la emisora.")
        if texto:
            self.decir(texto)
        if a["excesos"]:
            self.son("multa", cat="interfaz")
            self.decir(AJ.frase("frases_excesivo"))
            if self.apercibir(tr("uso excesivo de la fuerza")):
                return
        if parte <= 0:
            return
        antes = self.rango_policia()
        rapido = AJ("bono_rapidez") if (self.t - a["t0"]) < a["plazo"] * 0.6 else 0          # resuelto en poco más de la mitad del plazo que se dio para llegar
        paga = int((float(d.get("paga", 120)) * parte + rapido + a["extra"]) * (1.0 + AJ("rango_extra") / 100.0 * antes) * (1.1 if j.ciudadania >= 40 else 1.0))
        t["hechas"] += 1
        t["ganado"] += paga
        pol["avisos"] = int(pol.get("avisos", 0)) + 1
        j.stats["serv_policia"] = int(j.stats.get("serv_policia", 0)) + 1
        j.stats["servicios"] = j.stats.get("servicios", 0) + 1
        self.dar_dinero(paga, tr("Aviso resuelto"))
        self.cambiar_ciudadania(0.8)
        if self.rango_policia() > antes:
            self.son("ascenso", cat="interfaz")
            self.decir(AJ.frase("frases_ascenso", rango=self.rango_policia_txt(), extra=AJ.entero("rango_extra") * self.rango_policia()))

    def _apuntar_baja(self, a, s):
        """Un sospechoso ha caído. Si no te había atacado, es un exceso."""
        a["abatidos"] += 1
        self.j.policia["bajas"] = int(self.j.policia.get("bajas", 0)) + 1
        if not getattr(s, "ha_resistido", False) or getattr(s, "rendido", False):
            a["excesos"] += 1

    def detener_sospechoso(self, s):
        """Intro junto a un sospechoso rendido: esposas."""
        t = self.trabajo or {}
        a = t.get("aviso")
        if not a or s not in a.get("sospechosos", []):
            return False
        a["sospechosos"].remove(s)
        if s in self.personas:
            self.personas.remove(s)
        a["detenidos"] += 1
        self.j.policia["detenciones"] = int(self.j.policia.get("detenciones", 0)) + 1
        self.j.stats["detenidos"] = self.j.stats.get("detenidos", 0) + 1
        self.son("esposas", cat="interfaz")
        self.decir(f"{s.nombre}: " + AJ.frase("frases_detenido"), True)
        return True

    def agente_intro(self):
        """Intro estando de servicio: detener a quien se ha rendido o tratar con el conductor que ha parado. Devuelve True si había algo."""
        t = self.trabajo or {}
        a = t.get("aviso") if self.de_servicio() else None
        if not a:
            return False
        j = self.j
        x, y = self.pos()
        if not j.veh:
            rendidos = [s for s in a["sospechosos"] if not s.muerto and getattr(s, "rendido", False) and s.dist(x, y) < 6.0]
            if rendidos:
                self.detener_sospechoso(min(rendidos, key=lambda s: s.dist(x, y)))
                return True
        v = a.get("veh")
        if v is not None and a.get("fase") == "parado" and not v.muerto and v.dist(x, y) < (14 if j.veh else 8) and (not j.veh or abs(j.veh.vel) < 3):
            self._menu_conductor(a)
            return True
        return False

    def _menu_conductor(self, a):
        from .menus import Menu, Opcion
        app = self.app
        huyo = a["tipo"] == "persecucion" or a.get("huyo")
        euros = AJ.entero("multa_importe") * (2 if huyo else 1)

        def cerrar(texto, **cambios):
            app.cerrar(m)
            for k, n in cambios.items():
                a[k] = a.get(k, 0) + n
            v = a.get("veh")
            if v is not None:                                    # el coche se queda ahí, como uno más: no desaparece delante de ti
                v.tag, v.ocupado, v.hostil = None, False, False
                a["veh"] = None
            self._aviso_fin(texto)

        def multar():
            self.j.policia["multas"] = int(self.j.policia.get("multas", 0)) + 1
            self.son("multa", cat="interfaz")
            cerrar(AJ.frase("frases_multa", euros=euros), detenidos=1, extra=int(euros * AJ("multa_comision") / 100.0))

        def avisar():
            self.cambiar_ciudadania(1.0)
            cerrar(AJ.frase("frases_aviso"), detenidos=1)

        def detener():
            self.son("esposas", cat="interfaz")
            self.j.policia["detenciones"] = int(self.j.policia.get("detenciones", 0)) + 1
            self.j.stats["detenidos"] = self.j.stats.get("detenidos", 0) + 1
            cerrar(tr("El conductor: ") + AJ.frase("frases_detenido"), detenidos=1, excesos=0 if huyo else 1, extra=40 if huyo else 0)
        ops = [Opcion(tr('Ponerle una multa de {euros} euros').format(euros=(euros)), multar, ayuda=tr("Lo que toca por conducir así. Te llevas una parte como gratificación.")),
               Opcion(tr("Dejarlo en un aviso"), avisar, ayuda=tr("Sin multa. A los vecinos les gusta un agente con mano izquierda: sube tu prestigio."))]
        ops.insert(0, Opcion(tr("Detener al conductor"), detener, ayuda=tr("Ha huido de la policía: procede la detención.") if huyo
                             else tr("Solo conducía mal y ha parado cuando se lo has pedido: detenerle es pasarse, y te lo apuntarán.")))
        if not huyo:
            ops.append(ops.pop(0))
        m = Menu(app, tr("El conductor baja la ventanilla") + (tr(": «Vale, me ha pillado»") if huyo else tr(": «¿He hecho algo, agente?»")), ops, escapable=False)
        app.abrir(m)

    # ------------------------------------------------------------------ cada fotograma
    def actualizar_agente(self, dt):
        if not self.de_servicio():
            return
        t = self.trabajo
        j = self.j
        if j.estrellas or self.mundo.tipo in ("mar", "isla") or not self.mundo.policia:
            if j.estrellas and j.policia.get("alta"):
                self.expulsar_policia(tr("te busca la policía"))
            else:
                self.terminar_trabajo(tr("Aquí no hay servicio de patrulla. Fin del turno."))
            return
        a = t.get("aviso")
        if a is None:
            t["espera"] -= dt
            if t["espera"] <= 0:
                t["espera"] = 6.0
                self._aviso_nuevo()
            return
        if a["lugar"].mapa != self.mundo.id:                     # te has ido a otra localidad con un aviso pendiente
            a["sospechosos"], a["veh"] = [], None
            self._aviso_fin(AJ.frase("frases_tarde"), pagar=False)
            return
        x, y = self.pos()
        tipo = a["tipo"]
        if a["fase"] in ("ir", "seguir"):
            antes = a["limite"]
            a["limite"] -= dt
            if antes > 30 >= a["limite"]:
                self.decir(tr("Central: le quedan treinta segundos."))
            if a["limite"] <= 0:
                self._aviso_fin(AJ.frase("frases_tarde" if a["fase"] == "ir" else "frases_escapa"), pagar=False)
                return
        else:                                                    # ya estabas en ello: si te marchas, el aviso se da por perdido
            foco = [(s.x, s.y) for s in a["sospechosos"] if not s.muerto] or ([(a["veh"].x, a["veh"].y)] if a.get("veh") is not None else [a["lugar_xy"]])
            if min(math.hypot(fx - x, fy - y) for fx, fy in foco) > AJ("abandono_metros"):
                self._aviso_fin(AJ.frase("frases_abandono"), pagar=False)
                return
        if tipo in ("robo", "pelea"):
            self._aviso_a_pie(a, x, y, dt)
        else:
            self._aviso_rodado(a, x, y, dt)

    def _aviso_a_pie(self, a, x, y, dt):
        l = a["lugar"]
        d = a["def"]
        if a["fase"] == "ir":
            if math.hypot(l.x - x, l.y - y) > 42:
                return
            if self.gps:
                self.quitar_gps_auto()
            clase = d.get("sospechoso") or "atracador"
            if a["tipo"] == "pelea":
                a["sospechosos"] = [self._sospechoso(clase, l.x, l.y, n) for n in random.sample([tr("El de la camisa rota"), tr("El grandullón"), tr("El del chándal"), tr("El de la gorra"), tr("El borracho")], 2)]
                for s in a["sospechosos"]:
                    s.arma = None
                a["fase"], a["t_golpe"] = "pelea", 0.0
                self.decir(tr('Ahí están: dos tipos pegándose delante de {nombre}. Bájate, acércate y da el alto con la H, o sepáralos como puedas.').format(nombre=(l.nombre)))
                return
            n = random.randint(*sorted((int(d.get("n_min", 1) or 1), int(d.get("n_max", 1) or 1))))
            for k in range(n):
                s = self._sospechoso(clase, l.x, l.y, tr("Atracador") if n == 1 else tr('Atracador {v}').format(v=(k + 1)))
                r = random.random()
                if r < 0.25:
                    s.plan = "entrega"
                elif r < 0.55:
                    s.plan, s.estado, s.t_estado = "huye", "huye", 60.0
                else:
                    s.plan, s.hostil, s.estado, s.ha_resistido = "pelea", True, "ataca", True
                a["sospechosos"].append(s)
            a["fase"] = "actuar"
            self.son("alarma", xy=(l.x, l.y), ref=10, maxd=120, vol=0.5)
            self.decir((tr("Sale un tipo") if n == 1 else tr('Salen {n} tipos').format(n=(n))) + tr(' de {nombre} con la caja. Bájate del coche: da el alto con la H, y si no obedecen, redúcelos. Q para fijar.').format(nombre=(l.nombre)))
            return
        if a["tipo"] == "pelea" and a["fase"] == "pelea":
            a["t_golpe"] -= dt
            if a["t_golpe"] <= 0:
                a["t_golpe"] = random.uniform(0.7, 1.4)
                s = random.choice(a["sospechosos"])
                self.son("golpe", xy=(s.x, s.y), ref=5, maxd=60, vol=0.8)
                if random.random() < 0.3:
                    self.voz_persona(s, "dolor")
            if any(s.salud < s.salud_entera or s.muerto or getattr(s, "rendido", False) for s in a["sospechosos"]):      # te has metido a golpes: ahora van a por ti
                for s in a["sospechosos"]:
                    if not s.muerto and not getattr(s, "rendido", False):
                        s.hostil, s.estado, s.arma = True, "ataca", None
                a["fase"] = "actuar"
            return
        # fase «actuar»: hasta que no quede nadie por resolver
        for s in list(a["sospechosos"]):
            if s.muerto:
                a["sospechosos"].remove(s)
                self._apuntar_baja(a, s)
            elif getattr(s, "plan", "") == "entrega" and not getattr(s, "rendido", False) and s.dist(x, y) < 14:
                self.rendir_persona(s)
            elif not getattr(s, "rendido", False) and s.dist(x, y) > 130:
                a["sospechosos"].remove(s)
                if s in self.personas:
                    self.personas.remove(s)
                a["escapados"] += 1
                self.decir(tr('{nombre} se ha perdido de vista.').format(nombre=(s.nombre)))
        if not a["sospechosos"]:
            if a["abatidos"] and not a["detenidos"]:
                self._aviso_fin(AJ.frase("frases_abatido"))
            elif a["escapados"] and not a["detenidos"] and not a["abatidos"]:
                self._aviso_fin(AJ.frase("frases_escapa"), pagar=False)
            else:
                self._aviso_fin(tr("Central: recibido. Aviso resuelto."))

    def _pelea_alto(self, a):
        if random.random() * 100 < AJ("pelea_alto_prob"):
            for s in a["sospechosos"]:
                s.estado, s.t_estado, s.tag = "huye", 10.0, None
                s.sospechoso = False
            a["sospechosos"] = []
            a["pacifico"] = True
            self._aviso_fin(AJ.frase("frases_pelea_calma"))
            return
        bronca, otro = random.sample(a["sospechosos"], 2)
        otro.estado, otro.t_estado, otro.tag, otro.sospechoso = "huye", 10.0, None, False
        a["sospechosos"] = [bronca]
        bronca.hostil, bronca.estado, bronca.ha_resistido, bronca.arma = True, "ataca", True, None
        a["fase"] = "actuar"
        self.decir(AJ.frase("frases_pelea_bronca") + tr(" Redúcele: Q para fijarle. Cuando se rinda, Intro."))

    def _aviso_rodado(self, a, x, y, dt):
        v = a.get("veh")
        j = self.j
        if a["fase"] in ("seguir", "parado"):
            if v is None or v.muerto or v not in self.vehiculos:
                a["veh"] = None
                a["abatidos"] += 1
                j.policia["bajas"] = int(j.policia.get("bajas", 0)) + 1
                if a["fase"] == "parado" or (a["tipo"] != "persecucion" and not a.get("huyo")):
                    a["excesos"] += 1                            # ya había parado, o solo conducía mal: no era para tanto
                self._aviso_fin(tr("El vehículo ha quedado destrozado, con el conductor dentro. ") + AJ.frase("frases_abatido"))
                return
            if v.ardiendo >= 0:                                  # está ardiendo: ya no hay nada que hacer hasta que reviente
                return
        if a["fase"] == "seguir":
            d = v.dist(x, y)
            if d > 520:
                self._aviso_fin(AJ.frase("frases_escapa"), pagar=False)
                return
            if j.veh and self.gps is None:
                self.fijar_gps(v.x, v.y, v.nombre, sigue=v, auto=True, callar=True)
            if a["tipo"] == "temerario" and not a.get("huyo"):
                detras = d < 30 and j.veh is not None and self.sirena_propia is not None
                a["t_detras"] = a["t_detras"] + dt if detras else max(0.0, a["t_detras"] - dt)
                if d < 30 and j.veh is not None and self.sirena_propia is None and not a.get("dicho_sirena"):
                    a["dicho_sirena"] = True
                    self.decir(tr("Lo tienes delante. Enciende la sirena con la P y mantente detrás."))
                if a["t_detras"] >= AJ("temerario_segundos"):
                    if random.random() * 100 < AJ("temerario_obedece") and v.salud > v.salud_max * 0.5:
                        self._parar_vehiculo(a, AJ.frase("frases_para"))
                    else:
                        a["huyo"] = True
                        v.hostil = True
                        v.vel_obj = min(v.modelo["vel_max"] * 0.62, 21.0)
                        a["limite"] = max(a["limite"], 160.0)
                        self.decir(AJ.frase("frases_no_para"))
                        self.agente_como_parar()
                    return
            if v.salud <= v.salud_max * AJ("persecucion_salud") / 100.0 and (a["tipo"] == "persecucion" or a.get("huyo") or v.salud <= v.salud_max * 0.5):
                if a["tipo"] == "temerario" and not a.get("huyo"):
                    a["excesos"] += 1                            # no le has dado el alto: le has parado a golpes
                if random.random() < 0.5:
                    self._parar_vehiculo(a, AJ.frase("frases_vehiculo_rinde"))
                else:
                    v.ia, v.vel, v.ocupado, v.hostil, v.tag = "aparcado", 0.0, False, False, None
                    if v.canal:
                        v.canal.parar()
                        v.canal = None
                    s = self._sospechoso(a["def"].get("sospechoso") or "atracador", v.x, v.y, tr("Conductor fugado"))
                    s.estado, s.t_estado, s.arma, s.ha_resistido = "huye", 60.0, None, True
                    a["sospechosos"], a["veh"], a["fase"] = [s], None, "actuar"
                    if self.gps:
                        self.quitar_gps_auto()
                    self.son("puerta_coche", xy=(v.x, v.y))
                    self.decir(AJ.frase("frases_conductor_corre"))
            return
        if a["fase"] == "actuar":
            self._aviso_a_pie(a, x, y, dt)

    def agente_como_parar(self):
        """La primera persecución en coche de servicio: cómo se para a quien huye sin que el delito sea tuyo."""
        if "agente_persecucion" in self.j.recordado:
            return
        self.j.recordado.append("agente_persecucion")
        self.decir(tr('Cómo parar a quien huye en coche: síguele con el GPS, que ya lo lleva marcado, y embístele, o dispárale al vehículo con la Q para fijarlo. Mientras huye, y a menos de {entero} metros, no es delito. Cuando el vehículo está muy tocado, se para o el conductor sale corriendo. Lo que sí cuenta es darle a la gente o a otros coches: cada falta es un apercibimiento, y al tercero te quitan la placa.').format(entero=(AJ.entero('radio_fuerza_vehiculo'))))

    def _parar_vehiculo(self, a, frase):
        v = a["veh"]
        v.ia, v.vel, v.hostil = "aparcado", 0.0, False
        if v.canal:
            v.canal.parar()
            v.canal = None
        a["fase"] = "parado"
        if self.objetivo is v:
            self.objetivo = None
        self.son("frenazo", xy=(v.x, v.y), ref=12, maxd=120, vol=0.5)
        self.decir(frase)


def opciones_comisaria(p, l, Menu, Opcion, refrescar=None):
    """Lo que añade el oficio de policía al menú de una comisaría, con el modo encendido."""
    if not p.policia_activa():
        return []
    app = p.app
    j = p.j
    pol = j.policia
    if not pol.get("alta"):
        return [Opcion(lambda: tr('Ingresar en la policía: curso de {precio} euros y {entero} horas').format(precio=(p.precio('academia_policia', 400)), entero=(AJ.entero('curso_horas'))), lambda: (p.ingresar_policia(), refrescar and refrescar()),
                       ayuda=tr("Te haces agente. Hace falta que los vecinos te aprecien algo y que no te busque nadie. Después, en cualquier comisaría empiezas el turno: "
                             "te dan un coche patrulla y la emisora te pasa avisos. Cada aviso resuelto se paga, y con ellos asciendes. Si delinques, te quitan la placa."))]

    def estado():
        return (tr('Eres {rango_policia_txt}: {get} avisos resueltos, {get2} detenciones, {get3} multas. Apercibimientos: {get4} de {entero}').format(rango_policia_txt=(p.rango_policia_txt()), get=(j.stats.get('serv_policia', 0)), get2=(pol.get('detenciones', 0)), get3=(pol.get('multas', 0)), get4=(pol.get('apercibimientos', 0)), entero=(AJ.entero('apercibimientos'))))

    def dejar():
        mm = Menu(app, tr("¿Entregas la placa? Podrás volver a ingresar pagando el curso"),
                  [Opcion(tr("No"), lambda: app.cerrar(mm)), Opcion(tr("Sí, dejar la policía"), lambda: (app.cerrar(mm), p.dejar_policia(), refrescar and refrescar()),
                                                     ayuda=tr("Entregas la placa sin castigo y dejas de recibir avisos. Si estás de servicio, el turno se acaba."))])
        app.abrir(mm)
    ops = [Opcion(estado, ayuda=tr('Cada {entero} avisos resueltos asciendes y cobras un {entero2} por ciento más. Los apercibimientos llegan por faltas pequeñas estando de servicio o por usar más fuerza de la debida; con el último, pierdes la placa.').format(entero=(AJ.entero('ascenso_cada')), entero2=(AJ.entero('rango_extra'))))]
    if p.de_servicio():
        ops.append(Opcion(tr("Terminar el turno"), lambda: ([app.cerrar(x) for x in list(app.pila) if x is not p], p.terminar_turno()),
                          ayuda=tr("Devuelves el coche patrulla y dejas el aviso que tuvieras a medias. Sigues siendo agente: el próximo turno lo empiezas en cualquier comisaría.")))
    else:
        ops.append(Opcion(tr("Empezar el turno"), lambda: p.empezar_turno(l),
                          ayuda=tr("Te dan un coche patrulla, que te espera en la puerta. La emisora te pasa avisos: acude antes de que se acabe el tiempo. A pie, la H da el alto; "
                                "a quien se resista, redúcele sin matarle, y cuando se rinda, Intro para detenerle. Al conductor temerario se le para poniéndose detrás con la sirena, que es la P.")))
    ops.append(Opcion(tr("Dejar la policía"), dejar, ayuda=tr("Cuelgas la placa por tu cuenta, sin castigo. Antes te pide que lo confirmes. Para volver, hay que pagar otra vez el curso.")))
    return ops
