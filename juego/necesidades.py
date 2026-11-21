"""Vida realista (opcional): hambre, sed, sueño e higiene.

Con la opción activada, el cuerpo cuenta: hay que comer, beber, dormir y lavarse. Con hambre, con sed o con sueño vas
más despacio y apuntas peor, y si los ignoras del todo, la salud empieza a bajar. Comer en cualquier sitio quita el
hambre y algo de sed; beber quita la sed; dormir en casa, en un hotel o donde sea quita el sueño; una ducha te deja
limpio. Viene desactivada.

Desde la 1.7.2, ir sucio tiene consecuencias de verdad: la gente de la calle te coge menos confianza, en una cita se
nota, nadie quiere un beso ni una noche contigo hasta que te duches, el portero del club o del casino no te deja pasar,
y en el trabajo rindes menos. Ir con mucha hambre, mucha sed o oliendo mal te va bajando el ánimo. Para asearse, además
de la ducha de casa y la del hotel: los vestuarios del gimnasio, el mar, que quita algo, y lo de la droguería del
súper y de la gasolinera (desodorante, toallitas...), que ayuda, pero no sustituye a una ducha. En los lugares con
fuente (lo dicen sus datos, con el campo «fuente») se bebe gratis. Los números y las frases están en los datos (vida.json, sección necesidades).
"""
from .i18n import tr
from . import realismo
from .ajustes import Ajustes

AJ = Ajustes("necesidades", {
    "sucio_umbral": 70, "apesta_umbral": 90, "cita_sucio_pct": 50, "vendedor_sucio": 15, "turno_sucio": 15,
    "animo_cada": 120, "animo_baja": 2, "ducha_gimnasio_precio": 3, "mar_limpia": 40, "aseo_minimo": 30, "fuente_sed": 60,
}, {
    "locales_exigentes": ["club", "casino"],
    "frases_portero": [tr("El portero te para con la mano: «Así no entras. Date una ducha y vuelve.»"), tr("En la puerta te miran de arriba abajo y arrugan la nariz. Hoy no pasas.")],
    "frases_cita_sucio": [tr("{n} se aparta un poco cuando te acercas. Se nota que no te has duchado."), tr("A {n} no le hace gracia el olor. La cita se queda en menos de lo que podía ser.")],
    "frases_gesto_sucio": [tr("{n} arruga la nariz: «Mejor después de una ducha, ¿vale?»"), tr("«Uf. Primero, una ducha», te dice {n}, medio en broma, medio en serio.")],
    "frases_charla_sucio": [tr("Se echa un poco hacia atrás mientras habláis: hueles mal."), tr("Te contesta, pero sin acercarse mucho. El olor no ayuda.")],
    "frases_animo": [tr("Así no se puede estar: tienes el cuerpo pidiendo a gritos lo que le falta."), tr("Te sientes fatal. El cuerpo se queja.")],
}, cero=("cita_sucio_pct", "vendedor_sucio", "turno_sucio", "animo_baja", "ducha_gimnasio_precio", "mar_limpia", "aseo_minimo"))

HAMBRE_POR_MINUTO = 100.0 / (14 * 60)      # de recién comido a desfallecido, unas catorce horas de juego
SUENO_POR_MINUTO = 100.0 / (20 * 60)       # veinte horas despierto


class Necesidades:
    """Mixin de Partida."""

    def vida_realista(self):
        return bool(self.cfg["vida_realista"])

    def _aviso_necesidad(self, antes, ahora, textos):
        for umbral, texto in textos:
            if antes < umbral <= ahora:
                self.son("animo_baja", cat="interfaz", vol=0.6)
                self.decir(texto)

    def pasar_necesidades(self, minutos, durmiendo=False):
        if not self.vida_realista() or minutos <= 0:
            return
        j = self.j
        h0, s0 = j.hambre, j.sueno
        d0, c0 = j.sed, j.suciedad
        j.sed = min(100.0, j.sed + minutos * 100.0 / (realismo.aj("sed_horas") * 60) * (0.4 if durmiendo else 1.0))
        j.suciedad = min(100.0, j.suciedad + minutos * 100.0 / (realismo.aj("higiene_horas") * 60))
        self._aviso_necesidad(d0, j.sed, ((60, tr("Tienes sed.")), (85, tr("Tienes mucha sed. Te cuesta correr.")), (100, tr("Llevas demasiado sin beber. Estás perdiendo salud."))))
        self._aviso_necesidad(c0, j.suciedad, ((70, tr("Te vendría bien una ducha.")), (90, tr("Hueles mal. La gente se aparta, y a ti tampoco te hace gracia."))))
        if j.suciedad >= 90 and c0 < 90:
            self.cambiar_animo(-4)
        j.hambre = min(100.0, j.hambre + minutos * HAMBRE_POR_MINUTO * (0.5 if durmiendo else 1.0))
        if durmiendo:
            j.sueno = max(0.0, j.sueno - minutos * 100.0 / (7 * 60))       # siete horas de sueño reparan del todo
        else:
            j.sueno = min(100.0, j.sueno + minutos * SUENO_POR_MINUTO)
        self._aviso_necesidad(h0, j.hambre, ((60, tr("Empiezas a tener hambre.")), (82, tr("Tienes mucha hambre. Te cuesta moverte.")), (100, tr("Llevas demasiado sin comer. Estás perdiendo salud."))))
        if h0 < 60 <= j.hambre and "comer_en_casa" not in j.recordado:      # la primera vez que aprieta el hambre, una sola vez por partida
            j.recordado.append("comer_en_casa")
            self.decir(tr("Puedes comer en un bar, pedir comida a domicilio desde una casa tuya, o hacer la compra en una tienda de comida y cocinar en casa, que es lo que más alimenta."))
        if not durmiendo:
            self._aviso_necesidad(s0, j.sueno, ((65, tr("Empiezas a tener sueño.")), (85, tr("Se te cierran los ojos. Apuntas peor y vas más despacio.")), (100, tr("No te tienes en pie. Necesitas dormir ya."))))
        if j.hambre >= 100.0 or j.sueno >= 100.0:
            j.salud = max(10.0, j.salud - minutos * 0.05)
        if j.sed >= 100.0:
            j.salud = max(10.0, j.salud - minutos * 0.08)
        # con mucha hambre, mucha sed u oliendo mal, el ánimo se resiente poco a poco
        if j.hambre >= 82 or j.sed >= 85 or j.suciedad >= AJ("apesta_umbral"):
            self._t_animo_cuerpo = getattr(self, "_t_animo_cuerpo", 0.0) + minutos
            cada = max(1.0, AJ("animo_cada"))
            if self._t_animo_cuerpo >= cada:
                veces = int(self._t_animo_cuerpo // cada)
                self._t_animo_cuerpo -= veces * cada
                if AJ.entero("animo_baja"):
                    self.cambiar_animo(-AJ.entero("animo_baja") * veces)
                    if not durmiendo:
                        self.decir(AJ.frase("frases_animo"))
        else:
            self._t_animo_cuerpo = 0.0

    def ha_comido(self, cuanto=45.0):
        j = self.j
        if self.vida_realista() and j.hambre > 0:
            j.hambre = max(0.0, j.hambre - cuanto)
        if self.vida_realista():
            j.sed = max(0.0, j.sed - cuanto * 0.4)             # con la comida también se bebe algo

    def ha_bebido(self, cuanto=70.0):
        if self.vida_realista():
            self.j.sed = max(0.0, self.j.sed - cuanto)

    def ha_duchado(self):
        if self.vida_realista():
            self.j.suciedad = 0.0

    def limpio(self):
        """¿Vas presentable? Sin vida realista, siempre."""
        return not self.vida_realista() or self.j.suciedad < AJ("apesta_umbral")

    def sucio(self):
        """Te hace falta una ducha (sin vida realista, nunca)."""
        return self.vida_realista() and self.j.suciedad >= AJ("sucio_umbral")

    def apesta(self):
        """Hueles mal: la gente lo nota."""
        return self.vida_realista() and self.j.suciedad >= AJ("apesta_umbral")

    def asearse(self, cuanto):
        """Desodorante, toallitas, el mar: ayuda, pero sin ducha no se queda del todo limpio."""
        if self.vida_realista() and cuanto > 0:
            j = self.j
            if j.suciedad > AJ("aseo_minimo"):
                j.suciedad = max(AJ("aseo_minimo"), j.suciedad - cuanto)
            return True
        return False

    def bano_en_el_mar(self):
        if self.vida_realista() and self.j.suciedad > AJ("mar_limpia"):
            self.j.suciedad = AJ("mar_limpia")

    def tiene_fuente(self, l):
        """¿Hay una fuente para beber? Lo dicen los datos de cada lugar (campo «fuente»), que el editor de mods marca."""
        return bool(l.get("fuente"))

    def beber_en_fuente(self):
        self.mez.sonar("beber", cat="interfaz")                  # el sonido solo: «son» con «beber» ya cuenta un trago entero
        self.ha_bebido(AJ("fuente_sed"))
        return tr("Bebes agua fresca de la fuente.") + self.necesidades_txt()

    def portero_no_deja(self, l):
        """En un sitio exigente, oliendo mal no se entra. Devuelve la frase, o cadena vacía."""
        if self.apesta() and l.tipo in AJ.lista("locales_exigentes") and l.id not in self.j.propiedades and not self.mision:
            return AJ.frase("frases_portero")
        return ""

    def mod_necesidades(self):
        """Factor de velocidad a pie por hambre y sueño."""
        if not self.vida_realista():
            return 1.0
        j = self.j
        return (0.88 if j.hambre >= 82 else 1.0) * (0.85 if j.sueno >= 85 else 1.0) * (0.88 if j.sed >= 85 else 1.0)

    def mod_punteria_necesidades(self):
        if not self.vida_realista():
            return 0.0
        return -0.12 if self.j.sueno >= 85 else 0.0

    def necesidades_txt(self):
        if not self.vida_realista():
            return ""
        j = self.j
        h = tr("sin hambre") if j.hambre < 40 else tr("con algo de hambre") if j.hambre < 60 else tr("con hambre") if j.hambre < 82 else tr("con mucha hambre")
        s = tr("sin sueño") if j.sueno < 40 else tr("con algo de cansancio") if j.sueno < 65 else tr("con sueño") if j.sueno < 85 else tr("con muchísimo sueño")
        d = tr("sin sed") if j.sed < 40 else tr("con algo de sed") if j.sed < 60 else tr("con sed") if j.sed < 85 else tr("con muchísima sed")
        c = "" if j.suciedad < AJ("sucio_umbral") else tr(" Te hace falta una ducha.") if j.suciedad < AJ("apesta_umbral") else tr(" Hueles mal: dúchate. La gente lo nota.")
        return tr(' Estás {h}, {d} y {s}.{c}').format(h=(h), d=(d), s=(s), c=(c))
