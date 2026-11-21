"""Alquilar tus casas (1.7.2): una vivienda tuya que no usas puede dar dinero cada día.

Una casa tuya se pone en alquiler desde su propio menú, con el garaje vacío y sin nadie viviendo en ella contigo. Desde ese
momento vive allí un inquilino, que paga cada medianoche una renta que depende del precio de la casa y que nunca es igual
dos días seguidos. A veces hay algún desperfecto que pagas tú, y alguna vez el inquilino se retrasa un día. Mientras
está alquilada no puedes dormir, guardar la partida ni usar el garaje en ella. Se recupera cuando quieras, desde la
puerta: el inquilino se va y le devuelves la fianza, que es la renta de unos días.

En un servidor en línea no se alquila: el dinero lo arbitra el servidor. Los números y las frases están en los datos
(vida.json, sección alquiler).
"""
from .i18n import tr
import random

from .ajustes import Ajustes

AJ = Ajustes("alquiler", {
    "renta_milesimas": 4, "renta_minima": 25, "variacion": 15, "desperfecto_prob": 6, "desperfecto_dias": 2, "retraso_prob": 5, "fianza_dias": 2,
}, {
    "inquilinos": [tr("una pareja joven con un bebé"), tr("un matrimonio jubilado"), tr("una enfermera del hospital"), tr("dos estudiantes"), tr("un músico que ensaya poco, por suerte"),
                   tr("un profesor recién llegado a la comarca"), tr("una familia con dos niños"), tr("un camionero que pasa media semana fuera"), tr("una pescadora del puerto"),
                   tr("un programador que trabaja desde casa")],
    "frases_alquila": [tr("Firmas el contrato en la inmobiliaria: desde hoy en {casa} vive {inquilino}. Pagan unos {renta} euros cada medianoche."),
                       tr("Le das las llaves de {casa} a {inquilino}. La renta, unos {renta} euros al día, te llega sola cada medianoche.")],
    "frases_renta": [tr("Alquileres: {euros} euros de {n}."), tr("Te llega el alquiler de {n}: {euros} euros.")],
    "frases_desperfecto": [tr("En {casa} se ha roto el calentador. El arreglo, {euros} euros, corre de tu cuenta."), tr("Una gotera en {casa}: {euros} euros de fontanero que pagas tú."),
                           tr("{inquilino} te avisa de que la persiana de {casa} no sube. La reparación te cuesta {euros} euros.")],
    "frases_retraso": [tr("{inquilino}, en {casa}, se retrasa un día con el alquiler. Dice que mañana paga sin falta."),
                       tr("Hoy no llega el alquiler de {casa}: {inquilino} pide un día más.")],
    "frases_recupera": [tr("{inquilino} deja {casa} limpia y te devuelve las llaves. Le devuelves la fianza: {fianza} euros. La casa vuelve a ser para ti."),
                        tr("Recoges las llaves de {casa}. {inquilino} se va sin problemas y tú le devuelves {fianza} euros de fianza.")],
}, cero=("desperfecto_prob", "retraso_prob", "fianza_dias", "variacion"))


def _may(t):
    return t[:1].upper() + t[1:]


class Alquiler:
    """Mixin de Partida."""

    def alquiler_motivo(self, l=None):
        """Por qué no se puede alquilar (esa casa, o ninguna). Cadena vacía si se puede."""
        if self.en_servidor:
            return tr("En un servidor en línea no se alquilan casas: el dinero lo arbitra el servidor.")
        if l is None:
            return ""
        j = self.j
        if l.tipo != "casa" or l.id not in j.propiedades:
            return tr("Solo se alquilan las viviendas tuyas.")
        if self.alquilada(l.id):
            return tr("Ya está alquilada.")
        if j.convive and j.convive_casa == l.id:
            return tr("Vives allí con tu pareja. Para alquilarla, mudaos antes a otra casa.")
        if j.garajes.get(l.id):
            return tr("Saca antes tus vehículos del garaje: el inquilino lo usa también.")
        if sum(1 for i in j.propiedades if self.lug(i) is not None and self.lug(i).tipo == "casa" and not self.alquilada(i)) <= 1:
            return tr("Es la única casa que te queda para vivir: necesitas al menos otra libre.")
        return ""

    def alquilada(self, lid):
        return lid in (getattr(self.j, "alquiladas", None) or {})

    def renta_de(self, l):
        precio = int(l.get("precio", 0) or 0)
        return max(AJ.entero("renta_minima"), int(round(precio * AJ("renta_milesimas") / 1000.0)))

    def alquilar_casa(self, l):
        """Pone una casa tuya en alquiler. Devuelve la frase (de éxito o de por qué no)."""
        motivo = self.alquiler_motivo(l)
        if motivo:
            self.app.son("error")
            return motivo
        renta = self.renta_de(l)
        inquilino = random.choice(AJ.lista("inquilinos") or [tr("un inquilino")])
        self.j.alquiladas[l.id] = {"desde": self.dia, "renta": renta, "inquilino": inquilino, "cobrado": 0}
        self.son("dinero", cat="interfaz")
        return AJ.frase("frases_alquila", casa=self.nombre_lugar(l), inquilino=inquilino, renta=renta)

    def recuperar_casa(self, l):
        """El inquilino se va: le devuelves la fianza y la casa vuelve a ser para ti."""
        a = self.j.alquiladas.pop(l.id, None)
        if a is None:
            return tr("Esa casa no está alquilada.")
        fianza = int(a.get("renta", 0)) * AJ.entero("fianza_dias")
        if fianza:
            self.j.dinero = max(0, self.j.dinero - fianza)       # la fianza se devuelve aunque no llegue: queda a cero
        self.son("puerta_entrar", cat="interfaz")
        return AJ.frase("frases_recupera", casa=self.nombre_lugar(l), inquilino=_may(a.get("inquilino", "el inquilino")), fianza=fianza)

    def alquiler_txt(self, l):
        a = (getattr(self.j, "alquiladas", None) or {}).get(l.id)
        if not a:
            return ""
        return (tr('Alquilada a {get} desde el día {get2}, por unos {get3} euros al día. Llevas cobrados {get4} euros.').format(get=(a.get('inquilino', tr('un inquilino'))), get2=(a.get('desde', self.dia)), get3=(a.get('renta', 0)), get4=(a.get('cobrado', 0))))

    def dia_alquiler(self):
        """Cada medianoche: cobras los alquileres, con algún desperfecto o retraso de vez en cuando."""
        alq = getattr(self.j, "alquiladas", None) or {}
        if not alq or self.en_servidor:
            return
        total, n = 0, 0
        for lid, a in list(alq.items()):
            l = self.lug(lid)
            if l is None or lid not in self.j.propiedades:       # la has vendido o ya no existe: se acaba el contrato
                alq.pop(lid, None)
                continue
            casa, quien = self.nombre_lugar(l), a.get("inquilino", tr("El inquilino"))
            renta = int(a.get("renta", 0))
            if random.random() * 100 < AJ("retraso_prob") and not a.get("debe"):
                a["debe"] = renta
                self.decir(AJ.frase("frases_retraso", casa=casa, inquilino=_may(quien)))
                continue
            var = AJ("variacion") / 100.0
            euros = int(round(renta * random.uniform(1 - var, 1 + var))) + int(a.pop("debe", 0) or 0)
            if random.random() * 100 < AJ("desperfecto_prob"):
                coste = renta * AJ.entero("desperfecto_dias")
                euros -= coste
                self.decir(AJ.frase("frases_desperfecto", casa=casa, inquilino=_may(quien), euros=coste))
            a["cobrado"] = int(a.get("cobrado", 0)) + euros
            total += euros
            n += 1
        if not n:
            return
        if total > 0:
            self.hon()["caja"] = self.hon().get("caja", 0) + total       # cuenta para los impuestos del periodo, como un negocio
            total -= self._hon_embargar(total)                         # y si hay embargo, se queda su parte
            self.j.dinero += total
            self.j.stats["dinero_ganado"] += total
            self.son("dinero", cat="interfaz", vol=0.6)
        else:
            self.j.dinero = max(0, self.j.dinero + total)
        self.decir(AJ.frase("frases_renta", euros=total, n="tu casa alquilada" if n == 1 else f"tus {n} casas alquiladas"))


def opciones_casa(p, l, Menu, Opcion, cerrar):
    """Lo que añade el alquiler al menú de una casa tuya que no está alquilada."""
    if p.en_servidor or l.tipo != "casa":
        return []
    app = p.app

    def alquilar():
        motivo = p.alquiler_motivo(l)
        if motivo:
            app.son("error")
            app.decir(motivo, True)
            return

        def si():
            app.cerrar(mm)
            frase = p.alquilar_casa(l)
            cerrar()
            app.decir(frase, True)
        mm = Menu(app, tr('¿Alquilas {nombre_lugar} por unos {renta_de} euros al día? Mientras dure no podrás dormir, guardar la partida ni usar el garaje aquí').format(nombre_lugar=(p.nombre_lugar(l)), renta_de=(p.renta_de(l))),
                  [Opcion(tr("No, dejarla como está"), lambda: app.cerrar(mm)),
                   Opcion(tr("Sí, alquilarla"), si, ayuda=tr("Entra el inquilino y desde esta medianoche cobras la renta. La recuperas cuando quieras, devolviendo la fianza."))])
        app.abrir(mm)
    return [Opcion(tr('Alquilar la casa: unos {renta_de} euros al día').format(renta_de=(p.renta_de(l))), alquilar,
                   ayuda=tr('Vive en ella un inquilino que paga cada medianoche, un poco distinto cada día. A veces hay desperfectos que pagas tú, y alguna vez se retrasa un día. Hace falta el garaje vacío, que no viva aquí tu pareja y tener otra casa libre. Se recupera cuando quieras, devolviendo la fianza: {entero} días de renta.').format(entero=(AJ.entero('fianza_dias'))))]


def menu_alquilada(p, l, Menu, Opcion, menu_lugar):
    """El menú de la puerta de una casa tuya que está alquilada."""
    app = p.app

    def recuperar():
        def si():
            app.cerrar(mm)
            app.cerrar(m)
            app.decir(p.recuperar_casa(l), True)
        a = p.j.alquiladas.get(l.id) or {}
        fianza = int(a.get("renta", 0)) * AJ.entero("fianza_dias")
        mm = Menu(app, tr('¿Recuperas {nombre_lugar}? El inquilino se va y le devuelves {fianza} euros de fianza').format(nombre_lugar=(p.nombre_lugar(l)), fianza=(fianza)),
                  [Opcion(tr("No, que siga alquilada"), lambda: app.cerrar(mm)),
                   Opcion(tr("Sí, recuperarla"), si, ayuda=tr("Pagas la fianza aunque no te llegue el dinero: te quedas a cero. Dejas de cobrar la renta y la casa vuelve a ser para ti."))])
        app.abrir(mm)
    m = menu_lugar(p, l, [Opcion(lambda: p.alquiler_txt(l), ayuda=tr("La renta llega sola cada medianoche. Mientras esté alquilada no puedes dormir, guardar la partida ni usar el garaje aquí.")),
                          Opcion(tr("Recuperar la casa: el inquilino se va"), recuperar,
                                 ayuda=tr('Le devuelves la fianza, {entero} días de renta, y vuelves a poder dormir, guardar la partida y usar el garaje aquí. Antes te pide que lo confirmes.').format(entero=(AJ.entero('fianza_dias')))),
                          Opcion(tr("Descripción"), lambda: app.decir(l.desc, True), ayuda=tr("Cómo es la casa."))], tr("Esta casa está alquilada"))
    return m
