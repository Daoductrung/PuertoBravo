"""Ajustes de una parte del juego leídos de los datos: números y listas de frases, con su valor de serie.

Cada módulo que los usa crea los suyos (`AJ = Ajustes("seccion", {...}, {...})`) y `mundo.cargar_datos()` los pone al
día con lo que digan los datos y los mods. Lo que falte o venga mal vale lo de serie, así que unos datos antiguos, sin
la sección, funcionan igual.
"""
import random

from . import genero

_TODOS = []


class Ajustes:
    def __init__(self, seccion, numeros, listas=None, cero=()):
        self.seccion = seccion
        self._n = dict(numeros)
        self._l = {k: list(v) for k, v in (listas or {}).items()}
        self._cero = set(cero)                 # los que pueden valer cero (una probabilidad a cero apaga esa parte)
        self.n = dict(self._n)
        self.l = {k: list(v) for k, v in self._l.items()}
        _TODOS.append(self)

    def configurar(self, datos):
        c = next((x for x in datos.get(self.seccion, []) if isinstance(x, dict)), {})
        for k, serie in self._n.items():
            try:
                n = float(c.get(k, serie))
                self.n[k] = n if n > 0 or (n == 0 and k in self._cero) else serie
            except (TypeError, ValueError):
                self.n[k] = serie
        for k, serie in self._l.items():
            v = c.get(k)
            self.l[k] = [str(x) for x in v if str(x).strip()] if isinstance(v, list) and any(str(x).strip() for x in v) else list(serie)

    def __call__(self, k):
        return self.n[k]

    def entero(self, k):
        return int(round(self.n[k]))

    def lista(self, k):
        return self.l[k]

    def frase(self, k, rng=random, **kw):
        """Una frase al azar de una lista, con sus huecos rellenos. Un hueco que la frase no conozca se deja como está."""
        t = rng.choice(self.l[k]) if self.l.get(k) else ""
        for clave, valor in kw.items():
            t = t.replace("{" + clave + "}", str(valor))
        return t

    def entre(self, minimo, maximo, rng=random):
        a, b = sorted((self.n[minimo], self.n[maximo]))
        return rng.uniform(a, b)


def configurar_todos(datos):
    for a in _TODOS:
        a.configurar(datos)


def hueco(texto, **kw):
    for clave, valor in kw.items():
        texto = texto.replace("{" + clave + "}", str(valor))
    return texto


def quien_es(texto):
    """Resuelve las marcas de género del protagonista ([o|a]) de una frase de los datos."""
    return genero.resolver(texto)
