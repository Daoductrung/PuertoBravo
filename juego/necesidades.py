"""Vida realista (opcional): hambre, sed, sueño e higiene.

Con la opción activada, el cuerpo cuenta: hay que comer, beber, dormir y lavarse. Con hambre, con sed o con sueño vas
más despacio y apuntas peor, y si los ignoras del todo, la salud empieza a bajar. Comer en cualquier sitio quita el
hambre y algo de sed; beber quita la sed; dormir en casa, en un hotel o donde sea quita el sueño; una ducha te deja
limpio. Ir sucio baja el ánimo y la gente lo nota. Viene desactivada.
"""
from . import realismo

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
        self._aviso_necesidad(d0, j.sed, ((60, "Tienes sed."), (85, "Tienes mucha sed. Te cuesta correr."), (100, "Llevas demasiado sin beber. Estás perdiendo salud.")))
        self._aviso_necesidad(c0, j.suciedad, ((70, "Te vendría bien una ducha."), (90, "Hueles mal. La gente se aparta, y a ti tampoco te hace gracia.")))
        if j.suciedad >= 90 and c0 < 90:
            self.cambiar_animo(-4)
        j.hambre = min(100.0, j.hambre + minutos * HAMBRE_POR_MINUTO * (0.5 if durmiendo else 1.0))
        if durmiendo:
            j.sueno = max(0.0, j.sueno - minutos * 100.0 / (7 * 60))       # siete horas de sueño reparan del todo
        else:
            j.sueno = min(100.0, j.sueno + minutos * SUENO_POR_MINUTO)
        self._aviso_necesidad(h0, j.hambre, ((60, "Empiezas a tener hambre."), (82, "Tienes mucha hambre. Te cuesta moverte."), (100, "Llevas demasiado sin comer. Estás perdiendo salud.")))
        if not durmiendo:
            self._aviso_necesidad(s0, j.sueno, ((65, "Empiezas a tener sueño."), (85, "Se te cierran los ojos. Apuntas peor y vas más despacio."), (100, "No te tienes en pie. Necesitas dormir ya.")))
        if j.hambre >= 100.0 or j.sueno >= 100.0:
            j.salud = max(10.0, j.salud - minutos * 0.05)
        if j.sed >= 100.0:
            j.salud = max(10.0, j.salud - minutos * 0.08)

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
        return not self.vida_realista() or self.j.suciedad < 90

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
        h = "sin hambre" if j.hambre < 40 else "con algo de hambre" if j.hambre < 60 else "con hambre" if j.hambre < 82 else "con mucha hambre"
        s = "sin sueño" if j.sueno < 40 else "con algo de cansancio" if j.sueno < 65 else "con sueño" if j.sueno < 85 else "con muchísimo sueño"
        d = "sin sed" if j.sed < 40 else "con algo de sed" if j.sed < 60 else "con sed" if j.sed < 85 else "con muchísima sed"
        c = "" if j.suciedad < 70 else " Te hace falta una ducha." if j.suciedad < 90 else " Hueles mal: dúchate."
        return f" Estás {h}, {d} y {s}.{c}"
