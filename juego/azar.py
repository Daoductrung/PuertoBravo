"""El azar de cada día: ninguna partida es igual a otra, y ningún día igual al anterior.

- Cada partida nace con su propia semilla: con ella varían los precios de cada comercio.
- Cada medianoche se sortea cómo viene el día: normal, rebajas, mercado, escasez, fiesta, huelga de
  transportes, operación salida... Eso cambia los precios, cuánta gente hay por la calle y cuánto tráfico.
- Además, cada comercio tiene cada día su pequeño vaivén de precios, distinto del de la tienda de al lado.

Lo que ya era aleatorio sigue siéndolo: qué coches circulan, quiénes son los peatones (cada uno con su
nombre, su oficio y su carácter), el tiempo, los sucesos callejeros, la bolsa y los precios de la calle.
"""
import random

# id, peso, lo que se anuncia, efectos
DIAS = [
    ("normal", 46, "", {}),
    ("rebajas", 8, "Hoy hay rebajas en las armerías.", {"armas": 0.8}),
    ("mercado", 9, "Hoy hay mercado: comer sale más barato.", {"comida": 0.75}),
    ("escasez", 6, "Han cortado la carretera de la costa y no llega género: hoy todo está más caro.", {"armas": 1.2, "comida": 1.25}),
    ("fiesta", 8, "Hoy es fiesta: las calles están llenas de gente y hay menos coches.", {"peatones": 1.6, "trafico": 0.7}),
    ("huelga", 5, "Hay huelga de transportes: apenas circulan vehículos.", {"trafico": 0.4}),
    ("operacion", 7, "Operación salida: hoy hay mucho más tráfico.", {"trafico": 1.6}),
    ("desierto", 5, "Hoy no hay un alma por la calle.", {"peatones": 0.4, "trafico": 0.6}),
    ("turistas", 6, "Ha llegado un crucero: hay turistas por todas partes y los bares suben los precios.", {"peatones": 1.5, "comida": 1.2}),
]


class Azar:
    """Mixin de Partida."""

    def azar_iniciar(self):
        j = self.j
        if not getattr(j, "semilla", 0):
            j.semilla = random.randrange(1, 10 ** 9)
        self.dia_azar = {"id": "normal", "texto": "", "efectos": {}, "dia": 0}
        self.sortear_dia(anunciar=False)

    def azar_activo(self):
        """En las pruebas automáticas el azar de precios se apaga, salvo que la prueba lo pida, para que las cuentas salgan exactas."""
        return not getattr(self.app, "pruebas", False) or getattr(self, "azar_forzado", False)

    def sortear_dia(self, anunciar=True):
        rng = random.Random(f"{self.j.semilla}-dia-{self.dia}")
        total = sum(peso for _, peso, _, _ in DIAS)
        tirada = rng.uniform(0, total)
        for ident, peso, texto, efectos in DIAS:
            tirada -= peso
            if tirada <= 0:
                break
        self.dia_azar = {"id": ident, "texto": texto, "efectos": dict(efectos), "dia": self.dia}
        if anunciar and texto and self.azar_activo():
            self.son("evento", cat="interfaz", vol=0.5)
            self.decir(texto)

    def azar_factor(self, que):
        """Multiplicador del día para tráfico o peatones."""
        if not self.azar_activo():
            return 1.0
        return float(self.dia_azar["efectos"].get(que, 1.0))

    def mercado(self, categoria, lugar_id=""):
        """Multiplicador de precio de hoy en un comercio: el del día por el vaivén propio de esa tienda."""
        if not self.azar_activo():
            return 1.0
        propio = random.Random(f"{self.j.semilla}-{self.dia}-{categoria}-{lugar_id}").uniform(0.92, 1.1)
        return round(float(self.dia_azar["efectos"].get(categoria, 1.0)) * propio, 3)

    def dia_txt(self):
        return self.dia_azar["texto"] if self.azar_activo() else ""
