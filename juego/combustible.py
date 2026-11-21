"""Combustible (opcional): los vehículos de tierra gastan y hay que repostar.

Con la opción activada, cada coche, moto o camión tiene su depósito. Gasta al rodar, más cuanto más deprisa, y un poco
al ralentí. Avisa al entrar en reserva y cuando queda muy poco; con el depósito vacío, el motor se para y el vehículo se
queda donde esté. Se reposta en las gasolineras (tiendas con surtidor), con un bidón comprado en ellas, o llamando a la
asistencia en carretera desde el móvil. Viene desactivada. No cuenta en los barcos, en lo que vuela, en las bicicletas,
en los vehículos de las misiones ni jugando en un servidor.
"""
from .i18n import tr
import random

# Los números salen de los datos del juego (data/datos/vida.json, sección combustible), que un mod puede cambiar.
# Estos son los de serie, por si la sección falta.
PRECIO_LITRO = 1.6
LITROS_BIDON = 10
PRECIO_BIDON = 30
PRECIO_ASISTENCIA = 140
LITROS_ASISTENCIA = 15
AUTONOMIA = 9000.0          # metros que da un depósito lleno a velocidad de crucero
RESERVA = 0.15
DEPOSITOS = {"motor_moto": 14, "motor_camion": 160, "motor_furgoneta": 70, "motor_deportivo": 60, "otros": 45}
SIN_MOTOR = ("bici",)


def configurar(datos):
    """Toma los ajustes del combustible de los datos ya cargados, con los mods encima."""
    global PRECIO_LITRO, LITROS_BIDON, PRECIO_BIDON, PRECIO_ASISTENCIA, LITROS_ASISTENCIA, AUTONOMIA, RESERVA, DEPOSITOS
    c = next((x for x in datos.get("combustible", []) if isinstance(x, dict)), None)
    if not c:
        return
    try:
        PRECIO_LITRO = float(c.get("precio_litro", PRECIO_LITRO))
        LITROS_BIDON = int(c.get("litros_bidon", LITROS_BIDON))
        PRECIO_BIDON = int(c.get("precio_bidon", PRECIO_BIDON))
        PRECIO_ASISTENCIA = int(c.get("precio_asistencia", PRECIO_ASISTENCIA))
        LITROS_ASISTENCIA = int(c.get("litros_asistencia", LITROS_ASISTENCIA))
        AUTONOMIA = max(500.0, float(c.get("autonomia", AUTONOMIA)))
        RESERVA = max(0.02, min(0.5, float(c.get("reserva", RESERVA * 100)) / 100.0))
        dep = {str(k): float(v) for k, v in (c.get("depositos") or {}).items() if float(v) > 0}
        if dep:
            DEPOSITOS = dict(DEPOSITOS, **dep)
    except (TypeError, ValueError):
        pass


def deposito(modelo):
    """Los litros que caben. Cero si el vehículo no gasta combustible."""
    if modelo.get("barco") or modelo.get("vuela") or modelo.get("id") in SIN_MOTOR or modelo.get("sin_motor"):
        return 0.0
    return float(modelo.get("deposito") or DEPOSITOS.get(modelo.get("motor"), DEPOSITOS.get("otros", 45)))


def capacidad(v):
    """Los litros que caben en un vehículo concreto: los de su modelo, y más si lleva el depósito ampliado en el taller."""
    from . import sistemas
    return deposito(v.modelo) * sistemas.factor_deposito(v)


def tiene_surtidor(lugar):
    """¿Se puede repostar aquí? Lo dice el mapa: el lugar lleva la marca de surtidor."""
    return lugar is not None and bool(lugar.get("surtidor"))


def precio_litro(lugar=None):
    """Cada gasolinera puede tener su precio; si no lo pone, el general."""
    try:
        return float(lugar.get("precio_litro") or PRECIO_LITRO) if lugar is not None else PRECIO_LITRO
    except (TypeError, ValueError):
        return PRECIO_LITRO


class Combustible:
    """Mixin de Partida."""

    def combustible_activo(self):
        return bool(self.cfg["combustible"]) and not getattr(self, "en_servidor", False)

    def litros(self, v):
        """Los litros que lleva. Un vehículo que no se había mirado aún aparece con el depósito a medias, como en la vida."""
        cap = capacidad(v)
        if getattr(v, "litros", None) is None:
            v.litros = cap * (1.0 if getattr(v, "propio", False) else random.uniform(0.4, 1.0))
        v.litros = max(0.0, min(cap, float(v.litros)))
        return v.litros

    def gasta(self, v):
        return self.combustible_activo() and v is not None and not v.tag and deposito(v.modelo) > 0

    def gastar_combustible(self, v, dt):
        """Se llama mientras conduces. Devuelve False si el motor está parado por falta de combustible."""
        if not self.gasta(v):
            v.seco = False
            return True
        cap = capacidad(v)
        antes = self.litros(v)
        if antes <= 0:
            v.seco = True
            return False
        ritmo = abs(v.vel) / max(1.0, v.modelo["vel_max"])
        metros = abs(v.vel) * dt
        v.litros = max(0.0, antes - cap / AUTONOMIA * metros * (0.75 + 0.9 * ritmo * ritmo) - cap / 5400.0 * dt * 0.15)
        a, b = antes / cap, v.litros / cap
        if b <= 0:
            v.seco = True
            self.son("motor_seco", cat="interfaz")
            self.decir(tr("Te has quedado sin combustible. El motor se para. Con el móvil, en Servicios, puedes llamar a la asistencia en carretera, "
                       "o echarle un bidón si llevas uno."))
            return False
        if a > 0.05 >= b:
            self.son("reserva", cat="interfaz")
            self.decir(tr("Casi no queda combustible. Reposta ya."))
        elif a > RESERVA >= b:
            self.son("reserva", cat="interfaz")
            g = self.surtidor_cercano()
            self.decir(tr("Entras en reserva: queda poco combustible.") + (tr(' La gasolinera más cercana: {situar}.').format(situar=(self.situar(g.x, g.y, g.nombre))) if g else ""))
        v.seco = False
        return True

    def surtidor_cercano(self):
        x, y = self.pos()
        ops = [l for l in self.mundo.lugares.values() if tiene_surtidor(l)]
        return min(ops, key=lambda l: (l.x - x) ** 2 + (l.y - y) ** 2) if ops else None

    def combustible_txt(self, v):
        if not self.gasta(v):
            return ""
        cap = capacidad(v)
        l = self.litros(v)
        return tr(' Depósito al {int} por ciento, {int2} litros').format(int=(int(round(100 * l / cap))), int2=(int(round(l)))) + (tr(", en reserva.") if l / cap <= RESERVA else ".")

    def repostar(self, v, litros=None, gratis=False, precio=None):
        """Echa combustible. Con litros=None, llena. Devuelve los litros echados, o 0 si no se pudo pagar o ya estaba lleno."""
        cap = capacidad(v)
        if cap <= 0:
            return 0
        hueco = cap - self.litros(v)
        n = hueco if litros is None else min(hueco, float(litros))
        if n < 0.5:
            return 0
        if not gratis and not self.pagar(max(1, int(round(n * (precio or PRECIO_LITRO))))):
            return 0
        v.litros = min(cap, v.litros + n)
        v.seco = False
        self.son("repostar", cat="interfaz")
        return n

    def vehiculo_para_repostar(self, radio=45):
        """El que llevas, o el que has dejado cerca."""
        return self.j.veh or self.tu_vehiculo(radio)

    def usar_bidon(self):
        j = self.j
        v = self.vehiculo_para_repostar(12)
        if not j.objetos.get("bidon"):
            self.app.son("error")
            self.decir(tr("No llevas ningún bidón de gasolina. Se compran en las gasolineras."), True)
        elif v is None or deposito(v.modelo) <= 0:
            self.app.son("error")
            self.decir(tr("Tienes que estar en tu vehículo o al lado de él."), True)
        elif self.repostar(v, LITROS_BIDON, gratis=True):
            j.objetos["bidon"] -= 1
            self.decir(tr('Vacías el bidón en el depósito de {nombre}.{combustible_txt}').format(nombre=(v.nombre), combustible_txt=(self.combustible_txt(v))), True)
        else:
            self.decir(tr("El depósito está lleno."), True)

    def asistencia_carretera(self):
        v = self.vehiculo_para_repostar(30)
        if v is None or deposito(v.modelo) <= 0 or self.mundo.tipo == "mar":
            self.app.son("error")
            self.decir(tr("La asistencia viene a donde esté tu vehículo: tienes que estar en él o al lado."), True)
            return False
        if self.j.estrellas:
            self.app.son("error")
            self.decir(tr("Con la policía buscándote, la grúa no se acerca."), True)
            return False
        if capacidad(v) - self.litros(v) < 1:
            self.decir(tr("El depósito está lleno."), True)
            return False
        if not self.pagar(PRECIO_ASISTENCIA):
            return False
        self.pasar_horas(0.5)
        self.repostar(v, LITROS_ASISTENCIA, gratis=True)
        self.decir(tr('En media hora llega la asistencia y te echa {LITROS_ASISTENCIA} litros.{combustible_txt}').format(LITROS_ASISTENCIA=(LITROS_ASISTENCIA), combustible_txt=(self.combustible_txt(v))), True)
        return True
