"""Vivir en pareja y planes nuevos juntos (1.7.1). Solo con el contenido para adultos activado, que es donde están las
relaciones; lo de mudarse, además, con su propia opción, que viene apagada.

Cada persona decide: a tu pareja le puedes pedir que se venga a vivir contigo, y dice que sí o que no según cómo estéis
y según cómo sea ella (hay quien no deja su casa por nadie). Si acepta, vive en una de tus casas: te la encuentras
allí, cocina para ti o te pide que cocines tú, te pide cosas de vez en cuando y se nota si no apareces. Se le puede
pedir que se vaya.

Los planes nuevos (un paseo, el cine, una cena, una travesía en barco...) son para cualquier pareja, viva o no contigo:
cada uno se cuenta con una escena hablada distinta cada vez. Los planes están en los datos (vida.json, planes_pareja) y
los números y las frases, en la sección convivencia.
"""
import random
import zlib

from .ajustes import Ajustes

AJ = Ajustes("convivencia", {
    "afinidad_minima": 70, "citas_minimas": 3, "nunca_prob": 20, "espera_dias": 5, "ausencia_dias": 2,
    "peticion_prob": 30, "peticion_dias": 2, "peticion_premio": 6, "peticion_castigo": 5, "cocina_salud": 30, "cocina_hambre": 70,
}, {
    "frases_si": ["{n} se queda en silencio un momento, y luego sonríe: Creía que no me lo ibas a pedir nunca. Sí.",
                  "{n}: ¿Vivir juntos? Dame dos días para recoger mis cosas. Claro que sí.", "{n} te abraza antes de contestar. Es que sí."],
    "frases_no_pronto": ["{n}: Me gustas mucho, pero es pronto. Vamos poco a poco.", "{n}: Todavía no. No quiero que lo estropeemos por correr.",
                         "{n} te coge la mano: Aún no estamos ahí. Pregúntamelo más adelante."],
    "frases_no_nunca": ["{n}: Te quiero, pero mi casa es mi casa. No me pidas eso.", "{n}: Yo no valgo para vivir con nadie, y no es por ti. Así estamos bien.",
                        "{n} niega despacio: Cada uno en su casa. Es como mejor me va."],
    "frases_llega": ["{n} llega con dos maletas y una planta. {casa} ya no es solo tuya.", "Ayudas a {n} a subir las cajas a {casa}. Desde hoy vivís bajo el mismo techo.",
                     "{n} deja su cepillo de dientes junto al tuyo, en {casa}. Ya está hecho."],
    "frases_recibe": ["{n} te oye llegar: ¿Qué tal el día?", "{n} está en el sofá, con los pies en alto, y te hace sitio.", "{n} canturrea en la cocina. Te da un beso al pasar.",
                      "{n} levanta la vista del móvil y sonríe al verte.", "Huele a café recién hecho. {n} te sirve una taza sin preguntar."],
    "frases_ausente": ["En casa no hay nadie: {n} está en {lugar}.", "Hay una nota en la nevera: «Estoy en {lugar}. Luego nos vemos».", "{n} no está: a estas horas anda por {lugar}."],
    "frases_charla": ["Os contáis el día sin prisa.", "{n} te cuenta un cotilleo del barrio y acabáis riendo.", "Habláis de lo que haréis el fin de semana.",
                      "{n} te pregunta en qué andas metid[o|a]. Cambias de tema, y lo nota.", "Os quedáis un rato en silencio, a gusto."],
    "frases_cocina": ["{n} ha hecho la cena: arroz con lo que había, y está buenísimo.", "{n} saca del horno algo que huele de maravilla.",
                      "{n} ha preparado tortilla y una ensalada. Coméis en la cocina, de pie, picando del mismo plato.", "Hoy {n} se ha lucido: guiso de los de mojar pan."],
    "frases_cocinas_tu": ["{n}: Hoy te toca a ti. Te pones el delantal y sale algo decente.", "{n} te tiende la sartén: Sorpréndeme. Lo consigues, a medias.",
                          "Cocinas tú. {n} dice que está rico y repite, que es lo que cuenta."],
    "frases_se_va": ["{n} recoge sus cosas en silencio. Dice que lo entiende, pero no te mira al irse.", "{n}: Si es lo que quieres... Mañana no quedará nada mío aquí.",
                     "{n} mete su ropa en una maleta. La planta se la lleva."],
    "frases_se_va_sola": ["{n} ha recogido sus cosas y se ha ido de {casa}.", "Al volver, los armarios de {n} están vacíos."],
    "frases_ausencia": ["{n} te escribe: hace días que no pasas por casa. No le hace gracia.", "{n}: ¿Vives aquí o solo recibes el correo? Hace días que no te veo."],
    "frases_peticion_cena": ["{n}: Hoy no tengo ganas de cocinar. ¿Pides algo a domicilio y cenamos aquí?", "{n}: ¿Y si esta noche cenamos algo de encargo, aquí en casa?"],
    "frases_peticion_plan": ["{n}: Hace mucho que no salimos. Llévame a algún sitio, anda.", "{n}: Necesito que me dé el aire. Hagamos algo juntos estos días."],
    "frases_peticion_dormir": ["{n}: Casi no paras en casa. Quédate a dormir esta noche.", "{n}: Me gustaría despertarme contigo mañana, para variar."],
    "frases_peticion_mueble": ["{n}: Esta casa necesita un arreglo. ¿Por qué no compramos algún mueble?", "{n}: Si vamos a vivir aquí, habrá que amueblarlo un poco mejor."],
    "frases_peticion_regalo": ["{n}: No te pido mucho, pero un detalle de vez en cuando...", "{n} suspira: Antes me traías cosas."],
    "frases_peticion_ok": ["{n} lo agradece de verdad: se le nota.", "{n}: Gracias. Estas cosas son las que cuentan.", "A {n} se le ilumina la cara."],
    "frases_peticion_mal": ["{n} no dice nada, pero lleva la cuenta: no hiciste lo que te pidió.", "{n}: Te lo pedí hace días. Da igual, déjalo."],
    "frases_celos_casa": ["{n} estaba en casa. No hay nada que explicar: coge el abrigo y se va dando un portazo.",
                          "Abres la puerta y {n} está en el salón. Os mira a los dos, recoge el bolso y sale sin decir palabra."],
}, cero=("nunca_prob", "peticion_prob", "peticion_premio", "peticion_castigo", "citas_minimas"))

PLANES = [
    {"id": "paseo_barrio", "nombre": "Dar una vuelta por el barrio, sin rumbo", "precio": 0, "horas": 2, "afinidad": 6, "animo": 5,
     "escenas": ["Salís sin rumbo. {n} se para en todos los escaparates y tú finges que te interesan.", "Camináis despacio, del brazo. {n} saluda a medio barrio.",
                 "Acabáis en un banco, viendo pasar a la gente e inventándole una vida a cada cual.", "{n} te enseña el portal donde se crió. No se lo había contado a nadie."]},
    {"id": "cine_juntos", "nombre": "Ir al cine", "precio": 30, "horas": 3, "afinidad": 7, "animo": 6, "requiere": "cine",
     "escenas": ["Elegís la película a suertes. Pierdes tú, pero acaba gustándote.", "{n} se come sus palomitas y la mitad de las tuyas.",
                 "A media película {n} te coge la mano y ya no la suelta.", "Salís discutiendo el final. {n} tiene razón, pero no se la das."]},
    {"id": "cena_fuera", "nombre": "Cenar fuera", "precio": 60, "horas": 3, "afinidad": 9, "animo": 7, "requiere": "comida",
     "escenas": ["El camarero os da la mesa del rincón. {n} pide por los dos y acierta.", "Compartís el postre. {n} se queda con la última cucharada.",
                 "La cena se alarga. Cierran el restaurante con vosotros dentro, y ni os dais cuenta.", "{n} brinda por vosotros. Tú brindas por que no se acabe."]},
    {"id": "barco", "nombre": "Una travesía en barco al atardecer", "precio": 90, "horas": 4, "afinidad": 12, "animo": 9, "requiere": "embarcadero",
     "escenas": ["Alquiláis una lancha y salís despacio. {n} quiere llevar el timón, y le dejas.", "Paráis el motor mar adentro. Solo se oye el agua contra el casco.",
                 "El sol se mete en el mar y {n} apoya la cabeza en tu hombro.", "Volvéis a puerto con las luces ya encendidas, con sal en la piel y sin decir nada."]},
    {"id": "playa", "nombre": "Una tarde de playa", "precio": 10, "horas": 4, "afinidad": 8, "animo": 8,
     "escenas": ["Extendéis las toallas donde rompe la brisa. {n} se duerme al sol.", "{n} te mete en el agua a traición. Está helada.",
                 "Coméis pipas mirando a los que pescan desde el espigón.", "Os quedáis hasta que refresca, con arena hasta en los bolsillos."]},
    {"id": "compras", "nombre": "Ir de compras", "precio": 80, "horas": 3, "afinidad": 7, "animo": 4, "requiere": "ropa",
     "escenas": ["{n} se prueba media tienda. Tú sujetas las perchas.", "Te convence para llevarte una camisa que no te habrías puesto nunca.",
                 "Salís con dos bolsas y la sensación de haber gastado de más.", "{n} te pregunta cuál le queda mejor. Aciertas de milagro."]},
    {"id": "feria_juntos", "nombre": "Una noche de feria", "precio": 25, "horas": 3, "afinidad": 8, "animo": 8, "requiere": "feria",
     "escenas": ["{n} te gana en la caseta de tiro y no deja de recordártelo.", "Compartís un algodón de azúcar que se os pega a todo.",
                 "Subís a la noria. Arriba del todo, {n} te besa.", "Os reís hasta que os duele la tripa en los coches de choque."]},
    {"id": "baile_juntos", "nombre": "Salir a bailar", "precio": 40, "horas": 4, "afinidad": 9, "animo": 8, "requiere": "club", "adultos": True,
     "escenas": ["La pista está llena, pero {n} baila como si no hubiera nadie más.", "Bailáis muy cerca hasta que cierran.",
                 "{n} te arrastra a la pista con la canción que le gusta.", "Volvéis a casa andando, con los zapatos en la mano."]},
    {"id": "noche_casa", "nombre": "Una noche de sofá, película y manta", "precio": 0, "horas": 3, "afinidad": 6, "animo": 6, "en_casa": True,
     "escenas": ["Empezáis tres películas y no acabáis ninguna.", "{n} se duerme en tu hombro a los diez minutos.",
                 "Pedís perdón al vecino por las risas.", "La manta es pequeña para dos. Mejor."]},
]


def planes(p):
    lista = [x for x in p.datos.get("planes_pareja", []) if isinstance(x, dict) and x.get("nombre")]
    return lista or PLANES


class Convivencia:
    """Mixin de Partida."""

    def convivencia_activa(self):
        if self.en_servidor or not self.vida_sentimental():
            return False
        return (self.modo_adulto() and bool(self.cfg["pareja_convive"])) or bool(self.hon_estado_pareja())      # prometidos o casados, siempre

    def conviviente(self):
        """Los datos de quien vive contigo, o None."""
        j = self.j
        return self.persona_social(j.convive) if j.convive and self.vida_sentimental() else None

    def casa_comun(self):
        return self.lug(self.j.convive_casa) if self.j.convive else None

    def _disposicion(self, pers):
        """Cómo es cada persona con lo de vivir juntos: «nunca», o el nivel de afinidad con el que se anima. Es fija en cada partida."""
        quiere = str(pers.get("convivir") or "").strip()
        rng = random.Random(zlib.crc32(f"convivir:{self.j.semilla}:{pers['id']}".encode("utf-8")))
        if quiere == "nunca" or (quiere not in ("si", "facil") and rng.random() * 100 < AJ("nunca_prob")):
            return None
        return AJ("afinidad_minima") + (-8 if quiere == "facil" else rng.uniform(-6, 12))

    def pedir_convivir(self, pers, casa):
        """Le pides a tu pareja que se venga a vivir a una casa tuya. Devuelve (acepta, frase)."""
        j = self.j
        pid, n = pers["id"], pers["nombre"]
        r = self.relacion(pid)
        if not self.convivencia_activa():
            return False, ("Vivir en pareja está desactivado. Se activa en Opciones, Contenido para adultos." if self.modo_adulto()
                           else "Para vivir juntos, primero tenéis que estar prometidos.")
        if j.pareja != pid:
            return False, f"{n} y tú no sois pareja."
        if j.convive == pid:
            return False, f"{n} ya vive contigo."
        if casa is None:
            return False, "Necesitas una casa tuya en la que vivir los dos."
        falta = int(r.get("pidio_convivir", -99)) + AJ.entero("espera_dias") - self.dia
        if falta > 0:
            return False, f"{n} ya te contestó hace poco. Dale tiempo: vuelve a preguntárselo dentro de {falta} {'día' if falta == 1 else 'días'}."
        r["pidio_convivir"] = self.dia
        umbral = self._disposicion(pers)
        if umbral is None:
            self.son("afinidad_baja", cat="interfaz", vol=0.5)
            return False, AJ.frase("frases_no_nunca", n=n)
        if r["afinidad"] < umbral or r.get("citas", 0) < AJ("citas_minimas"):
            return False, AJ.frase("frases_no_pronto", n=n)
        j.convive, j.convive_casa, j.convive_desde = pid, casa.id, self.dia
        j.convive_hoy = {"visto": self.dia}
        j.peticion_pareja = None
        r["ultimo"] = self.dia
        self.son("pareja", cat="interfaz")
        self.cambiar_animo(12)
        j.stats["convivencias"] = j.stats.get("convivencias", 0) + 1
        return True, AJ.frase("frases_si", n=n) + " " + AJ.frase("frases_llega", n=n, casa=casa.nombre)

    def fin_convivencia(self, motivo="pedido", callar=False):
        """Deja de vivir contigo: porque se lo pides, porque lo habéis dejado o porque se ha ido ella."""
        j = self.j
        pers = self.persona_social(j.convive) if j.convive else None
        casa = self.lug(j.convive_casa)
        pid = j.convive
        j.convive, j.convive_casa, j.peticion_pareja, j.convive_hoy = "", "", None, {}
        if pers is None:
            return ""
        n = pers["nombre"]
        if motivo == "pedido":
            r = self.relacion(pid)
            r["afinidad"] = max(0, r["afinidad"] - 15)
            r["pidio_convivir"] = self.dia
            self.son("afinidad_baja", cat="interfaz")
            self.cambiar_animo(-6)
            texto = AJ.frase("frases_se_va", n=n)
        else:
            texto = AJ.frase("frases_se_va_sola", n=n, casa=casa.nombre if casa else "tu casa")
        if not callar:
            self.decir(texto)
        return texto

    def pareja_en_casa(self):
        """¿Está ahora en casa quien vive contigo? De noche, siempre; de día, a ratos: tiene su vida."""
        if not self.conviviente():
            return False
        h = int(self.reloj // 60) % 24
        if h >= 19 or h < 9:
            return True
        return random.Random(f"encasa:{self.j.semilla}:{self.dia}:{h // 3}").random() < 0.35

    def saludo_de_casa(self, casa):
        """Al entrar en la casa donde vivís: lo que te encuentras. Cadena vacía si allí no vive nadie contigo."""
        j = self.j
        pers = self.conviviente()
        if pers is None or casa.id != j.convive_casa:
            return ""
        n = pers["nombre"]
        if not self.pareja_en_casa():
            l = self.lug(pers.get("lugar"))
            return AJ.frase("frases_ausente", n=n, lugar=self.nombre_lugar(l) if l else "sus cosas")
        primera = j.convive_hoy.get("visto") != self.dia
        j.convive_hoy["visto"] = self.dia
        self.relacion(j.convive)["ultimo"] = self.dia
        texto = AJ.frase("frases_recibe", n=n)
        pet = self._peticion_nueva(pers) if primera else ""
        return texto + (" " + pet if pet else "")

    # ------------------------------------------------------------------ lo que te pide
    def _peticion_nueva(self, pers):
        j = self.j
        if j.peticion_pareja or random.random() * 100 >= AJ("peticion_prob"):
            return ""
        from . import sistemas
        casa = self.casa_comun()
        ops = ["cena", "plan", "dormir", "regalo"]
        if casa is not None and len(sistemas.muebles_de(j, casa)) < len(sistemas.MUEBLES) - 1:
            ops.append("mueble")
        que = random.choice(ops)
        j.peticion_pareja = {"que": que, "dia": self.dia, "hasta": self.dia + AJ.entero("peticion_dias"),
                             "muebles": len(sistemas.muebles_de(j, casa)) if casa is not None else 0}
        return AJ.frase("frases_peticion_" + que, n=pers["nombre"])

    def peticion_txt(self):
        pet, pers = self.j.peticion_pareja, self.conviviente()
        if not pet or not pers:
            return ""
        que = {"cena": "que pidas cena a domicilio para los dos, en casa", "plan": "que hagáis algún plan juntos", "dormir": "que te quedes a dormir en casa",
               "mueble": "que compres algún mueble para la casa", "regalo": "un detalle: un regalo"}.get(pet["que"], "algo")
        return f"{pers['nombre']} te ha pedido {que}. Tienes hasta el día {pet['hasta']}."

    def peticion_cumplida(self, que):
        """Has hecho algo de lo que te pide quien vive contigo (cena, plan, dormir, mueble o regalo)."""
        j = self.j
        pet, pers = j.peticion_pareja, self.conviviente()
        if not pet or not pers or pet.get("que") != que:
            return False
        j.peticion_pareja = None
        self.sumar_afinidad(j.convive, AJ.entero("peticion_premio"))
        self.cambiar_animo(3)
        self.decir(AJ.frase("frases_peticion_ok", n=pers["nombre"]))
        return True

    # ------------------------------------------------------------------ en casa
    def charla_en_casa(self):
        j = self.j
        pers = self.conviviente()
        r = self.relacion(j.convive)
        if j.convive_hoy.get("charla") == self.dia:
            return f"Ya habéis hablado un buen rato hoy. {pers['nombre']} está a lo suyo."
        j.convive_hoy["charla"] = self.dia
        self.sumar_afinidad(j.convive, 2)
        self.cambiar_animo(3)
        return AJ.frase("frases_charla", n=pers["nombre"]) + f" Ahora {self.afinidad_txt(r)}."

    def comer_en_casa(self):
        """Quien vive contigo cocina para los dos o, a veces, te pide que cocines tú. Una vez al día."""
        j = self.j
        pers = self.conviviente()
        if j.convive_hoy.get("comida") == self.dia:
            return "Hoy ya habéis comido juntos. Queda algo en la nevera para mañana."
        j.convive_hoy["comida"] = self.dia
        tu = random.random() < 0.3
        j.salud = min(j.salud_max, j.salud + AJ("cocina_salud"))
        self.ha_comido(AJ("cocina_hambre"))
        self.ha_bebido(60)
        self.mez.sonar("comer", cat="interfaz")
        self.pasar_horas(1)
        self.sumar_afinidad(j.convive, 4 if tu else 2)
        self.cambiar_animo(4)
        return AJ.frase("frases_cocinas_tu" if tu else "frases_cocina", n=pers["nombre"]) + f" Salud {int(j.salud)}.{self.necesidades_txt()}"

    def aventura_en_casa(self, casa):
        """Traes a otra persona a la casa donde vive tu pareja. Si está, se acabó. Devuelve True si os ha visto."""
        j = self.j
        pers = self.conviviente()
        if pers is None or casa is None or casa.id != j.convive_casa or not self.pareja_en_casa():
            return False
        pid = j.convive
        r = self.relacion(pid)
        r["afinidad"] = max(0, r["afinidad"] - 45)
        r["estado"] = "ex"
        j.pareja = ""
        self.fin_convivencia("sola", callar=True)
        self.son("ruptura", cat="interfaz")
        self.cambiar_animo(-20)
        self.decir(AJ.frase("frases_celos_casa", n=pers["nombre"]))
        return True

    # ------------------------------------------------------------------ planes juntos
    def planes_para(self, pers):
        """Los planes que se pueden hacer ahora con esa persona: (plan, por qué no se puede o cadena vacía)."""
        out = []
        for pl in planes(self):
            motivo = ""
            req = pl.get("requiere")
            if pl.get("en_casa") and not (self.j.convive == pers["id"] and self.casa_aqui() is not None and self.casa_aqui().id == self.j.convive_casa):
                continue                                         # los planes de casa, solo en la casa en la que vivís
            if req and not any(l.tipo == req or (req == "comida" and l.tipo in ("comida", "pizzeria")) for l in self.mundo.lugares.values()):
                motivo = "en esta localidad no hay dónde"
            out.append((pl, motivo))
        return out

    def hacer_plan(self, pers, pl):
        """Un plan con tu pareja: se cuenta con una escena hablada, distinta cada vez. Devuelve True si se ha hecho."""
        from .menus import Dialogo
        j = self.j
        pid, n = pers["id"], pers["nombre"]
        r = self.relacion(pid)
        l = self.lug(pers.get("lugar"))
        junto = j.convive == pid or (l is not None and l.mapa == self.mundo.id)
        if not junto:
            self.app.son("error")
            self.decir(f"{n} está en {self.nombre_lugar(l) if l else 'otra localidad'}. Para hacer planes tenéis que estar en la misma localidad.", True)
            return False
        if j.estrellas:
            self.app.son("error")
            self.decir("Con la policía detrás no es momento de planes.", True)
            return False
        if r.get("hoy", {}).get("plan") == self.dia:
            self.decir(f"Hoy ya habéis hecho un plan. {n} quiere dejar algo para mañana.", True)
            return False
        if not self.pagar(int(pl.get("precio", 0))):
            return False
        r.setdefault("hoy", {})["plan"] = self.dia
        r["planes"] = r.get("planes", 0) + 1
        r["citas"] = r.get("citas", 0) + 1
        escenas = [str(e) for e in pl.get("escenas", []) if str(e).strip()] or ["Pasáis un buen rato juntos."]
        vistas = list(r.setdefault("escenas", {}).get(pl["id"], []))
        frescas = [e for e in escenas if e not in vistas]                     # no se repite una escena hasta haberlas oído todas
        if len(frescas) < min(2, len(escenas)):
            vistas, frescas = [], list(escenas)
        elegidas = random.sample(frescas, min(2, len(frescas)))
        r["escenas"][pl["id"]] = vistas + elegidas
        self.pasar_horas(float(pl.get("horas", 2)))
        self.sumar_afinidad(pid, int(pl.get("afinidad", 6)))
        self.cambiar_animo(int(pl.get("animo", 5)))
        j.stats["planes_pareja"] = j.stats.get("planes_pareja", 0) + 1
        self.son("cita", cat="interfaz")
        while len(self.app.pila) > 1 and self.app.pila[-1] is not self:
            self.app.pila.pop()
        self.app.teclas.clear()
        lineas = [("Narrador", f"{pl['nombre']}, con {n}.")] + [("Narrador", e.replace("{n}", n)) for e in elegidas]
        lineas.append(("Narrador", f"Son las {self.hora_txt()}. Ahora {self.afinidad_txt(r)}."))
        self.app.abrir(Dialogo(self.app, lineas, lambda: (self.peticion_cumplida("plan"), self.celos(pid))))
        return True

    # ------------------------------------------------------------------ cada día
    def dia_convivencia(self):
        """Cada medianoche, si alguien vive contigo: se nota si has pasado por casa y si has hecho lo que te pidió."""
        j = self.j
        if not j.convive:
            return
        pers = self.persona_social(j.convive)
        if pers is None or not self.vida_sentimental():
            return
        n = pers["nombre"]
        if j.pareja != j.convive:                                # lo habéis dejado: no se queda
            self.fin_convivencia("sola")
            return
        if j.convive_casa not in j.propiedades or self.lug(j.convive_casa) is None:
            otra = next((l for l in (self.lug(i) for i in j.propiedades) if l is not None and l.tipo == "casa"), None)
            if otra is None:
                self.fin_convivencia("sola")
                return
            j.convive_casa = otra.id
            self.decir(f"{n} se muda contigo a {self.nombre_lugar(otra)}.")
        r = self.relacion(j.convive)
        visto = j.convive_hoy.get("visto", j.convive_desde)
        if self.dia - 1 - int(visto) >= AJ("ausencia_dias"):
            r["afinidad"] = max(0, r["afinidad"] - 2)
            if (self.dia - 1 - int(visto)) % max(1, AJ.entero("ausencia_dias")) == 0:
                self.decir(AJ.frase("frases_ausencia", n=n))
        else:
            r["ultimo"] = self.dia                               # vivís juntos: os veis sin tener que quedar
            j.animo = min(100.0, j.animo + 2)
        pet = j.peticion_pareja
        if pet and pet.get("que") == "mueble":
            from . import sistemas
            casa = self.casa_comun()
            if casa is not None and len(sistemas.muebles_de(j, casa)) > int(pet.get("muebles", 0)):
                self.peticion_cumplida("mueble")
                pet = None
        if pet and self.dia > int(pet.get("hasta", self.dia)):
            j.peticion_pareja = None
            r["afinidad"] = max(0, r["afinidad"] - AJ.entero("peticion_castigo"))
            self.son("afinidad_baja", cat="interfaz", vol=0.5)
            self.decir(AJ.frase("frases_peticion_mal", n=n))

    def actualizar_convivencia(self, dt):
        pass


def opciones_casa(p, casa, Menu, Opcion):
    """Lo que añade al menú de una casa quien vive en ella contigo."""
    pers = p.conviviente()
    j = p.j
    if pers is None or casa.id != j.convive_casa:
        return []
    app = p.app
    n = pers["nombre"]
    if not p.pareja_en_casa():
        l = p.lug(pers.get("lugar"))
        return [Opcion(f"{n} no está en casa ahora: anda por {p.nombre_lugar(l) if l else 'sus cosas'}" + (". " + p.peticion_txt() if p.peticion_txt() else ""),
                       ayuda="Vive aquí contigo, pero tiene su vida. De noche está siempre; de día, a ratos.")]

    def abrir():
        def decir(f):
            return lambda: (app.decir(f(), True), m.refrescar(False))

        def planear():
            menu_planes(p, pers)

        def social():
            from . import menus_adultos
            menus_adultos.vida_social(p, directo=pers["id"])

        def irse():
            def si():
                app.cerrar(mm)
                app.cerrar(m)
                app.decir(p.fin_convivencia("pedido", callar=True), True)
            mm = Menu(app, f"¿Le pides a {n} que se vaya de casa? Le va a doler, y tardará en querer volver",
                      [Opcion("No, dejarlo como está", lambda: app.cerrar(mm)), Opcion("Sí, pedirle que se vaya", si)])
            app.abrir(mm)
        ops = [Opcion("Hablar un rato", decir(p.charla_en_casa), ayuda="Os acerca un poco. Una vez al día."),
               Opcion("Comer juntos", decir(p.comer_en_casa), ayuda="Cocina para los dos o, a veces, te toca a ti. Da salud y quita el hambre y la sed de la vida realista. Una vez al día."),
               Opcion("Hacer un plan juntos", planear, ayuda="Un paseo, el cine, una cena, una travesía en barco... Cada plan se cuenta con una escena distinta. Uno al día."),
               Opcion(f"Todo lo demás con {n}: regalos, gestos, pasar la noche", social, ayuda="Abre su ficha, la misma que tienes en el móvil, en Vida social."),
               Opcion(lambda: p.peticion_txt() or f"{n} no te ha pedido nada estos días",
                      ayuda="De vez en cuando te pide algo: una cena a domicilio, un plan, que duermas en casa, un mueble o un detalle. Si lo haces, os acerca; si lo dejas pasar, se resiente."),
               Opcion("Pedirle que se vaya de casa", irse, ayuda="Deja de vivir contigo. No rompe la relación, pero la enfría mucho."),
               Opcion("Volver", lambda: app.cerrar(m))]
        m = Menu(app, lambda: f"{n}, en casa. {p.afinidad_txt(p.relacion(pers['id'])).capitalize()}", ops)
        app.abrir(m)
    return [Opcion(f"{n} está en casa: estar con {n}", abrir, ayuda="Vive aquí contigo. Hablar, comer juntos, hacer planes o pedirle que se vaya.")]


def menu_planes(p, pers):
    from .menus import Menu, Opcion
    app = p.app
    ops = []
    for pl, motivo in p.planes_para(pers):
        if pl.get("adultos") and not p.modo_adulto():
            continue
        if motivo:
            ops.append(Opcion(f"{pl['nombre']}: {motivo}"))
        else:
            ops.append(Opcion(f"{pl['nombre']}: {int(pl.get('precio', 0))} euros, {pl.get('horas', 2)} horas", (lambda pl=pl: p.hacer_plan(pers, pl)),
                              ayuda="Se cuenta con una escena, distinta cada vez. Os acerca y te sube el ánimo. Un plan al día."))
    ops.append(Opcion("Volver", lambda: app.cerrar(m)))
    m = Menu(app, lambda: f"Planes con {pers['nombre']}. Tienes {p.j.dinero} euros", ops, intro="Cada plan se cuenta de una manera, y no siempre igual")
    app.abrir(m)
