"""Vida íntima, solo con el contenido para adultos activado: ligar con cualquiera, aventuras, encuentros
con la pareja, protección y salud sexual.

Todo se cuenta de forma sensual pero sin escenas explícitas: el juego describe el ambiente, el deseo y
lo que cambia después, y deja el resto a la imaginación. Todas las personas son adultas y siempre
pueden decir que no; un no se respeta y no hay ninguna opción para forzar a nadie.
"""
import random

from .charla import CARACTERES, ficha

# tipo de encuentro: (nombre, lo que se cuenta, ánimo que da, horas)
ENCUENTROS = {
    "romantico": ("Una noche romántica", ["Cenáis despacio, con velas, y os quedáis hablando hasta que sobran las palabras.",
                                          "Suena música bajita. Bailáis en el salón, muy cerca, y lo demás llega solo.",
                                          "Os miráis un rato largo antes del primer beso. La noche se hace corta."], 24, 8),
    "apasionado": ("Una noche apasionada", ["No llegáis ni a encender la luz. La ropa va quedando por el pasillo.",
                                            "Os buscáis con prisa, como si llevarais semanas esperándolo. Nadie duerme mucho.",
                                            "La puerta se cierra de un golpe y ya no hay nada más en el mundo que vosotros dos."], 26, 8),
    "jugueton": ("Una noche de risas y juegos", ["Empezáis de broma, con cosquillas y almohadas, y acabáis sin aliento por otros motivos.",
                                                  "Os retáis, os provocáis, os reís. Es de esas noches en las que todo vale si lo queréis los dos.",
                                                  "Entre risas y susurros descubrís un par de cosas nuevas el uno del otro."], 22, 7),
    "tranquilo": ("Una noche tranquila", ["Un masaje lento, una ducha larga, y os dormís abrazados.",
                                          "Hoy no hay prisa. Caricias, la ventana abierta y el mar de fondo.",
                                          "Os quedáis piel con piel, hablando bajito, hasta que os vence el sueño."], 20, 9),
}
GESTOS = {
    "beso": ("Darle un beso", 4, 4, 35, "Le das un beso. {n} sonríe y te lo devuelve."),
    "baile": ("Bailar juntos", 5, 5, 20, "Bailáis pegados un par de canciones. {n} se deja llevar."),
    "masaje": ("Darle un masaje", 6, 5, 45, "Le das un masaje en los hombros. {n} cierra los ojos y suspira."),
    "susurro": ("Decirle algo al oído", 3, 3, 30, "Le dices algo al oído. {n} se ríe y te mira de otra manera."),
}
ARTICULOS = [
    {"id": "preservativos", "nombre": "Caja de preservativos", "precio": 9, "unidades": 6, "desc": "Seis unidades. Evitan sustos: sin ellos, cada encuentro con alguien a quien no conoces bien tiene su riesgo."},
    {"id": "lenceria", "nombre": "Lencería fina", "precio": 60, "afinidad": 9, "desc": "Un regalo para tu pareja, o para estrenarlo en vuestra próxima noche: la hace más especial."},
    {"id": "aceite", "nombre": "Aceite de masaje", "precio": 22, "afinidad": 5, "desc": "Con olor a naranja. Mejora las noches tranquilas y los masajes."},
    {"id": "velas", "nombre": "Velas aromáticas", "precio": 14, "afinidad": 4, "desc": "Para las noches románticas."},
    {"id": "juguete", "nombre": "Un juguete para dos", "precio": 45, "afinidad": 7, "desc": "Para parejas con confianza. Mejora las noches de risas y juegos."},
]
MEJORA = {"romantico": "velas", "tranquilo": "aceite", "jugueton": "juguete", "apasionado": "lenceria"}


class Intimidad:
    """Mixin de Partida."""

    def me_atrae(self, genero):
        pref = self.cfg["atraccion"]
        return pref == "todos" or (pref == "mujeres" and genero == "m") or (pref == "hombres" and genero == "h")

    def articulos_intimos(self):
        return ARTICULOS

    def comprar_articulo(self, art):
        j = self.j
        if not self.pagar(art["precio"]):
            return False
        j.intimos[art["id"]] = j.intimos.get(art["id"], 0) + art.get("unidades", 1)
        self.decir(f"Compras {art['nombre'].lower()}. Tienes {j.intimos[art['id']]}. Te quedan {j.dinero} euros.", True)
        return True

    # ------------------------------------------------------------- ligar
    def ligar(self, q):
        """Coquetear con una persona de la calle. Puede salir bien, regular o mal; un no es un no."""
        j = self.j
        f = ficha(q)
        n = f["nombre"]
        if not self.me_atrae(f["genero"]):
            return f"{n} no es tu tipo. Lo puedes cambiar en Opciones, Contenido para adultos."
        if f.get("calabazas"):
            return f"{n} ya te dijo que no. Déjalo estar."
        mi_genero = self.cfg["mi_genero"]
        compatible = f["disponible"] and (mi_genero == "x" or mi_genero in f["le_atraen"])
        encanto = f["confianza"] + (j.animo - 50) * 0.3 + min(20, j.reputacion * 0.15) + j.ciudadania * 0.1 + random.uniform(-15, 15)
        self.son("murmullo", xy=(q.x, q.y), vol=0.5)
        f["coqueteos"] = f.get("coqueteos", 0) + 1
        if not compatible or (f["coqueteos"] > 4 and f["confianza"] < 30):
            f["calabazas"] = True
            self._trato(f, -3)
            self.cambiar_animo(-2)
            return f"{n}: " + random.choice(["Eres muy amable, pero no estoy por la labor.", "Gracias, pero tengo pareja.", "No eres mi tipo, lo siento. Sin malos rollos."])
        if encanto < 12:
            self._trato(f, 2)
            return f"{n}: " + random.choice(["Uy, qué directo. Primero invítame a algo, ¿no?", "Ja. Tú no pierdes el tiempo. Ya veremos.", "No vayas tan deprisa, que acabamos de conocernos."])
        self._trato(f, 9 if CARACTERES[f["caracter"]]["cumplido"] > 5 else 6)
        self.cambiar_animo(3)
        f["interes"] = True
        return f"{n}: " + random.choice(["Pues tú tampoco estás nada mal.", "Me gusta cómo me miras. Sigue hablando.", "¿Siempre eres así, o es que hoy te has levantado con suerte?"]) + " Le gustas."

    def puede_proponer(self, q):
        f = ficha(q)
        return bool(f.get("interes")) and f["confianza"] >= 35 and not f.get("calabazas")

    def proponer_aventura(self, q, en_hotel=False):
        """Proponerle a alguien que acaba de conocer pasar la noche juntos. Devuelve True si acepta."""
        j = self.j
        f = ficha(q)
        n = f["nombre"]
        if j.estrellas:
            self.app.son("error")
            self.decir("Con la policía detrás no es momento.", True)
            return False
        if not self.puede_proponer(q):
            self.decir(f"{n}: " + random.choice(["Para, para. Todavía no.", "No tan rápido. Conóceme un poco más.", "Me caes bien, pero no."]), True)
            self._trato(f, -4)
            return False
        if f["confianza"] + random.uniform(-10, 20) < 45:
            self.decir(f"{n}: Hoy no. Pero quédate con mi número.", True)
            return False
        casa = next((l for l in self.mundo.lugares.values() if l.tipo == "casa" and l.id in j.propiedades), None)
        if casa is None or en_hotel:
            if not self.pagar(self.precio("hotel_cita", 70)):
                return False
            donde = "un hotel"
        else:
            donde = casa.nombre
        j.stats["aventuras"] = j.stats.get("aventuras", 0) + 1
        self.personas = [x for x in self.personas if x is not q]
        self.encuentro(n, random.choice(["apasionado", "jugueton", "romantico"]), donde, desconocido=True)
        self.cambiar_reputacion(1)
        if j.pareja:
            self.celos()
        return True

    # --------------------------------------------------------- encuentros
    def _proteccion(self, desconocido):
        """Usa un preservativo si lo llevas. Sin él, con alguien a quien no conoces hay riesgo."""
        j = self.j
        if j.intimos.get("preservativos", 0) > 0:
            j.intimos["preservativos"] -= 1
            return " Habéis tenido cuidado."
        if desconocido and not j.its and random.random() < 0.12:
            j.its = self.dia
            return " No habéis usado protección."
        return " No lleváis protección." if desconocido else ""

    def encuentro(self, nombre, tipo, donde, desconocido=False, pid=None, sintonia=None):
        """Una noche con alguien. Se cuenta sin detalles explícitos y tiene efectos en el ánimo, la salud y la relación.

        Con la opción «la noche, paso a paso», antes se juega: decides tú qué haces y la otra persona responde. Lo bien
        que os entendáis (sintonía, de 0 a 1) cambia el ánimo que te deja y lo que os acerca.
        """
        from .menus import Dialogo
        j = self.j
        if self.cfg["noche_por_pasos"] and sintonia is None:
            from .laboratorio import Noche
            while len(self.app.pila) > 1 and self.app.pila[-1] is not self:
                self.app.pila.pop()
            self.app.teclas.clear()
            self.son("puerta_entrar", cat="interfaz", vol=0.6)
            Noche(self, nombre, donde, lambda s: self.encuentro(nombre, tipo, donde, desconocido, pid, sintonia=s)).empezar()
            return
        titulo, frases, animo, horas = ENCUENTROS[tipo]
        if sintonia is not None:
            animo = int(animo * (0.6 + 0.6 * sintonia))
            if pid:
                self.sumar_afinidad(pid, int(round(6 * sintonia)))
        extra = ""
        mejora = MEJORA.get(tipo)
        if mejora and j.intimos.get(mejora, 0) > 0:
            j.intimos[mejora] -= 1
            animo += 6
            extra = " " + {"velas": "Las velas hacen su parte.", "aceite": "El aceite de naranja lo cambia todo.", "juguete": "Estrenáis lo que compraste, entre risas.",
                           "lenceria": "La lencería dura puesta muy poco."}[mejora]
            if pid:
                self.sumar_afinidad(pid, 4)
        proteccion = self._proteccion(desconocido)
        self.pasar_horas(horas, dormir=True)
        j.salud = j.salud_max
        self.cambiar_animo(animo)
        j.stats["noches"] = j.stats.get("noches", 0) + 1
        self.son("puerta_entrar", cat="interfaz", vol=0.6)
        self.son("noche_juntos", cat="interfaz")
        while len(self.app.pila) > 1 and self.app.pila[-1] is not self:
            self.app.pila.pop()
        self.app.teclas.clear()
        self.app.abrir(Dialogo(self.app, [
            ("Narrador", f"{titulo} con {nombre}, en {donde}. {random.choice(frases)}{extra}"),
            ("Narrador", f"Lo que pasa después es solo vuestro.{proteccion} Por la mañana, son las {self.hora_txt()} y te sientes {self.animo_txt()}.")]))

    def gesto(self, pid, pers, clave):
        """Un gesto de cariño con alguien con quien tienes una relación: beso, baile, masaje o un susurro."""
        nombre, afin, animo, minimo, frase = GESTOS[clave]
        r = self.relacion(pid)
        if r["afinidad"] < minimo and self.j.pareja != pid:
            self.decir(f"{pers['nombre']} se aparta con una sonrisa. Todavía es pronto para eso.", True)
            return False
        if self._hecho_hoy(r, "gesto_" + clave):
            self.decir("Eso ya lo habéis hecho hoy. No hay que gastarlo.", True)
            return False
        if clave == "masaje" and self.j.intimos.get("aceite", 0) > 0:
            self.j.intimos["aceite"] -= 1
            afin += 3
        self.sumar_afinidad(pid, afin)
        self.cambiar_animo(animo)
        self.son("cita" if clave != "beso" else "afinidad_sube", cat="interfaz", vol=0.7)
        self.decir(frase.format(n=pers["nombre"]) + f" Ahora {self.afinidad_txt(r)}.", True)
        return True

    # ------------------------------------------------------------- salud
    def dia_intimidad(self):
        """Cada medianoche: una infección sin tratar baja el ánimo y, si tienes pareja, acaba sabiéndose."""
        j = self.j
        if not j.its:
            return
        dias = self.dia - j.its
        if dias >= 2:
            self.cambiar_animo(-4)
            if dias == 2:
                self.decir("Notas molestias desde hace un par de días. Deberías pasar por una farmacia o un hospital a hacerte una prueba.")
            if dias >= 5 and j.pareja:
                pers = self.persona_social(j.pareja)
                if pers:
                    self.sumar_afinidad(j.pareja, -20)
                    self.decir(f"{pers['nombre']} se ha enterado de lo tuyo y no le ha hecho ninguna gracia.")

    def prueba_y_tratamiento(self):
        """En farmacias y hospitales: prueba gratuita y, si hace falta, tratamiento."""
        j = self.j
        if not j.its:
            self.decir("Te haces la prueba. Todo está bien.", True)
            return True
        coste = self.precio("tratamiento_its", 120)
        if not self.pagar(coste):
            return False
        j.its = 0
        self.son("curar", cat="interfaz")
        self.cambiar_animo(5)
        self.decir(f"La prueba da positivo. Te ponen tratamiento por {coste} euros y en unos días estarás bien. La próxima vez, con protección.", True)
        return True

    def estado_intimo_txt(self):
        j = self.j
        partes = []
        if j.intimos.get("preservativos", 0):
            partes.append(f"llevas {j.intimos['preservativos']} preservativos")
        if j.its and self.dia - j.its >= 2:
            partes.append("tienes molestias que deberías mirarte")
        return ". ".join(partes).capitalize() + "." if partes else ""
