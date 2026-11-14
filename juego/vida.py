"""Personajes, prestigio ciudadano y vida honrada: empleos con ascensos, jornadas, cursos y voluntariado.

El juego se puede jugar como una persona de bien o como un delincuente. El prestigio entre los
vecinos sube con el trabajo honrado y baja con los delitos; la fama en la calle va por otro lado.
"""
import math
import re

RANGOS = ["aprendiz", "oficial", "veterano", "maestro", "leyenda"]
HAB_NOMBRE = {"conduccion": "conducción", "punteria": "puntería", "resistencia": "resistencia", "pesca": "pesca"}
JORNADAS = [("camarero", "Jornada de camarero", 70, 0), ("reponedor", "Jornada de reponedor en un supermercado", 85, 0),
            ("peon", "Jornada de peón de descarga", 115, -6)]


class Vida:
    # -------------------------------------------------------------- personajes
    def personajes(self):
        return self.datos.get("personajes", [])

    def aplicar_personaje(self, ident):
        j = self.j
        pj = next((x for x in self.personajes() if x["id"] == ident), None) or (self.personajes() or [{"id": "dani", "nombre": "Dani", "apellido": "Roca"}])[0]
        j.personaje = pj["id"]
        j.nombre = pj.get("nombre", "Dani")
        j.apellido = pj.get("apellido", "Roca")
        j.dinero = int(pj.get("dinero", j.dinero))
        j.salud_max = float(pj.get("salud_max", 100))
        j.salud = j.salud_max
        j.animo = float(pj.get("animo", j.animo))
        j.reputacion = float(pj.get("reputacion", 0))
        j.ciudadania = float(pj.get("ciudadania", 20))
        j.objetos["botiquin"] = int(pj.get("botiquines", 1))
        j.objetos["ganzua"] = int(pj.get("ganzuas", 0))
        for h in HAB_NOMBRE:
            j.hab[h] = 60.0 * int(pj.get(h, 0)) ** 2
        if pj.get("arma") in self.armas_d:
            a = self.armas_d[pj["arma"]]
            j.armas[a["id"]] = {"cargador": a.get("cargador", 0), "reserva": a.get("balas", 0)}

    def txt(self, texto):
        """Pone el nombre del personaje elegido en los textos de la historia, escritos para Dani Roca."""
        j = self.j
        if not isinstance(texto, str) or (j.nombre == "Dani" and j.apellido == "Roca") or "Dani" not in texto:
            return texto
        texto = texto.replace("Dani Roca", f"{j.nombre} {j.apellido}")
        return re.sub(r"\bDani\b", j.nombre, texto)

    # ------------------------------------------------------ prestigio ciudadano
    def ciudadania_txt(self):
        c = self.j.ciudadania
        return "los vecinos te evitan" if c < 10 else "eres un vecino más" if c < 40 else "los vecinos te aprecian" if c < 75 else "eres un ciudadano ejemplar"

    def cambiar_ciudadania(self, n):
        antes = self.ciudadania_txt()
        self.j.ciudadania = max(0.0, min(100.0, self.j.ciudadania + n))
        ahora = self.ciudadania_txt()
        if ahora != antes:
            self.son("prestigio" if n > 0 else "animo_baja", cat="interfaz")
            self.decir(f"Cambia cómo te ven en el barrio: {ahora}.")

    # ------------------------------------------------------------------ empleos
    def servicios_de(self, tipo):
        return int(self.j.stats.get("serv_" + tipo, 0))

    def rango(self, tipo):
        return min(len(RANGOS) - 1, self.servicios_de(tipo) // 8)

    def mult_trabajo(self, tipo):
        c = self.j.ciudadania
        return (1.0 + 0.12 * self.rango(tipo)) * (1.2 if c >= 75 else 1.1 if c >= 40 else 1.0)

    def servicio_hecho(self, tipo, nombre):
        antes = self.rango(tipo)
        self.j.stats["serv_" + tipo] = self.servicios_de(tipo) + 1
        self.cambiar_ciudadania(0.5)
        if self.rango(tipo) > antes:
            self.son("ascenso", cat="interfaz")
            self.decir(f"¡Ascenso! Ya eres {nombre} {RANGOS[self.rango(tipo)]}: cobras un {12 * self.rango(tipo)} por ciento más.")

    def jornada(self, clave, nombre, paga, salud):
        j = self.j
        if j.jornada_dia == self.dia:
            self.app.son("error")
            self.decir("Hoy ya has trabajado una jornada. Vuelve mañana.", True)
            return
        if j.estrellas:
            self.app.son("error")
            self.decir("Con la policía buscándote no te contratan.", True)
            return
        j.jornada_dia = self.dia
        cobro = int(paga * self.mult_trabajo("jornada"))
        self.pasar_horas(8)
        j.salud = max(10.0, j.salud + salud)
        self.son("jornada", cat="interfaz")
        self.dar_dinero(cobro)
        self.servicio_hecho("jornada", "trabajador")
        self.cambiar_ciudadania(1.0)
        self.cambiar_animo(-2)
        self.decir(f"{nombre}: ocho horas de trabajo y {cobro} euros. Son las {self.hora_txt()}.", True)

    def curso(self, hab):
        j = self.j
        if j.curso_dia == self.dia:
            self.app.son("error")
            self.decir("Ya has ido a clase hoy. La cabeza no da para más.", True)
            return
        if self.nivel(hab) >= 10:
            self.decir("Ya no pueden enseñarte nada más: tienes el nivel máximo.", True)
            return
        if not self.pagar(250):
            return
        j.curso_dia = self.dia
        self.pasar_horas(4)
        self.son("diploma", cat="interfaz")
        self.decir(f"Cuatro horas de clase de {HAB_NOMBRE[hab]}. Son las {self.hora_txt()}.", True)
        self.ganar_xp(hab, 320)
        self.cambiar_ciudadania(1.0)

    def donar(self, cantidad):
        if not self.pagar(cantidad):
            return
        self.son("donativo", cat="interfaz")
        self.cambiar_ciudadania(cantidad / 40.0)
        self.cambiar_animo(2 + cantidad / 100.0)
        self.j.stats["donado"] = self.j.stats.get("donado", 0) + cantidad
        self.decir(f"Donas {cantidad} euros. Te dan las gracias de corazón.", True)

    def voluntariado(self):
        j = self.j
        if j.voluntario_dia == self.dia:
            self.decir("Hoy ya has echado una mano. Vuelve mañana.", True)
            return
        j.voluntario_dia = self.dia
        self.pasar_horas(4)
        self.son("lugar_ong", cat="interfaz")
        j.stats["voluntariado"] = j.stats.get("voluntariado", 0) + 1
        self.cambiar_ciudadania(3.0)
        self.cambiar_animo(6)
        self.decir(f"Pasas cuatro horas sirviendo comidas. Sales cansado y contento. Son las {self.hora_txt()}.", True)

    def vehiculo_de_trabajo_cercano(self, tipo):
        """Lugar de este mapa que tiene siempre aparcado un vehículo de ese oficio."""
        modelos = {m["id"] for m in self.datos["vehiculos"] if m.get("trabajo") == tipo}
        x, y = self.pos()
        ops = [l for l in self.mundo.lugares.values() if l.get("vehiculo") in modelos]
        return min(ops, key=lambda l: math.hypot(l.x - x, l.y - y)) if ops else None

    # --------------------------------------------------------------- interiores
    def entrar_interior(self, l):
        """Al entrar en un local: la puerta y su ambiente de fondo mientras estés dentro."""
        self.salir_interior(silencio=True)
        self.son("puerta_entrar", cat="interfaz", vol=0.7)
        self.interior = self.mez.sonar(l.sonido, bucle=True, cat="interfaz", vol=0.22)

    def salir_interior(self, silencio=False):
        c = getattr(self, "interior", None)
        if c is not None:
            c.parar()
            self.interior = None
            if not silencio:
                self.son("puerta_salir", cat="interfaz", vol=0.6)
