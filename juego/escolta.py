"""Las misiones se ajustan a tu escolta (1.7.1). Opciones, Combate y dificultad: no, moderado (de serie) o fuerte.

Con toda la banda y dos guardaespaldas, los enemigos de una misión caían antes de que el jugador hiciera nada. Con esta
opción, al aparecer los enemigos de una misión se cuenta a los tuyos que tienes cerca y la oposición sube con ellos:
vienen algunos más, aguantan más y apuntan mejor, siempre dentro de los topes que digan los datos, para que ninguna
misión se vuelva imposible. No cuenta en los tutoriales, ni con muñecos de prácticas, rivales del gimnasio o gente a la
que solo hay que asustar, ni en un servidor en línea (allí los enemigos son de todo el grupo).

Los números y las frases salen de los datos (data/datos/vida.json, sección escolta_misiones).
"""
import random

from .ajustes import Ajustes

NIVELES = ("no", "moderado", "fuerte")

AJ = Ajustes("escolta_misiones", {
    "radio": 120, "aliados_gratis": 1,
    "moderado_extra": 0.5, "moderado_extra_max": 50, "moderado_salud": 6, "moderado_salud_max": 40, "moderado_punteria": 3, "moderado_punteria_max": 15,
    "fuerte_extra": 1.0, "fuerte_extra_max": 100, "fuerte_salud": 10, "fuerte_salud_max": 80, "fuerte_punteria": 5, "fuerte_punteria_max": 30,
}, {
    "frases": ["Saben que vienes con {n} de escolta: te esperan más, y mejor preparados.", "Con {n} a tu lado se ha corrido la voz: han reforzado el sitio.",
               "No te esperaban sol[o|a]: al ver llegar a {n} contigo, han llamado a más gente."],
}, cero=("aliados_gratis", "moderado_extra", "moderado_salud", "moderado_punteria", "fuerte_extra", "fuerte_salud", "fuerte_punteria"))


def _especial(grupo):
    return bool(grupo.get("inofensivo") or grupo.get("deportivo") or grupo.get("intimidar"))


class Escolta:
    """Mixin de Partida."""

    def escolta_presente(self):
        """Cuántos de los tuyos van contigo ahora mismo: banda y guardaespaldas vivos y cerca. El perro no cuenta."""
        x, y = self.pos()
        return sum(1 for e in self.personas if e.tipo == "aliado" and not e.muerto and e.dist(x, y) <= AJ("radio"))

    def escolta_ajuste(self, mision=None):
        """Lo que sube la oposición de esta misión por la escolta que llevas, o None si no sube nada:
        {"n": los tuyos, "extra": enemigos de más por cada uno de los que hay, como mucho, "salud": por cuánto se
        multiplica su salud, "punteria": y su puntería}."""
        nivel = self.cfg["escolta_misiones"]
        m = mision if mision is not None else ((self.mision or {}).get("def") or {})
        if nivel not in NIVELES[1:] or getattr(self, "en_servidor", False) or self.online_activo() or m.get("tutorial"):
            return None
        n = self.escolta_presente()
        cuentan = n - AJ.entero("aliados_gratis")
        if cuentan <= 0:
            return None
        return {"n": n, "cuentan": cuentan, "extra": AJ(nivel + "_extra") * cuentan, "extra_max": AJ(nivel + "_extra_max") / 100.0,
                "salud": 1.0 + min(AJ(nivel + "_salud_max"), AJ(nivel + "_salud") * cuentan) / 100.0,
                "punteria": 1.0 + min(AJ(nivel + "_punteria_max"), AJ(nivel + "_punteria") * cuentan) / 100.0}

    def escolta_grupos(self, grupos, aj):
        """Los grupos de enemigos de un paso con cuántos salen de cada uno: [(grupo, n)]. Con escolta, algunos más,
        repartidos entre los grupos según su tamaño y sin pasar del tope."""
        base = [(g, max(0, int(g.get("n", 1)))) for g in grupos]
        if not aj:
            return base
        total = sum(n for g, n in base if not _especial(g))
        tope = total * aj["extra_max"]
        de_mas = min(tope, aj["extra"])
        de_mas = int(de_mas) + (1 if random.random() < de_mas - int(de_mas) else 0)       # la fracción, a suertes: no siempre sale lo mismo
        de_mas = min(de_mas, int(tope + 1e-9)) if tope >= 1 else 0
        if de_mas <= 0 or total <= 0:
            return base
        out, resto, quedan = [], 0.0, de_mas
        for g, n in base:
            mas = 0
            if not _especial(g) and n > 0:
                exacto = de_mas * n / total + resto
                mas = min(quedan, int(exacto + 1e-9))
                resto = exacto - mas
                quedan -= mas
            out.append((g, n + mas))
        if quedan > 0:                                           # lo que haya quedado por los redondeos, al grupo más numeroso
            k = max((i for i, (g, n) in enumerate(out) if not _especial(g)), key=lambda i: out[i][1])
            out[k] = (out[k][0], out[k][1] + quedan)
        return out

    def escolta_endurecer(self, enemigos, aj, de_mas=0):
        """Sube la salud y la puntería de los enemigos recién aparecidos, y lo dice una vez por misión."""
        if not aj:
            return
        for e in enemigos:
            if getattr(e, "inofensivo", False) or getattr(e, "deportivo", False) or getattr(e, "intimidar", False) or getattr(e, "escolta_hecha", False):
                continue
            e.escolta_hecha = True
            e.salud *= aj["salud"] * random.uniform(0.95, 1.05)
            e.salud_entera = e.salud
            e.punteria = min(0.95, float(getattr(e, "punteria", 0.5)) * aj["punteria"])
        ms = self.mision
        if ms is not None and "escolta" not in ms.setdefault("avisos", set()):
            ms["avisos"].add("escolta")
            self.decir(AJ.frase("frases", n=aj["n"]) + " Si prefieres que no cambie, está en Opciones, Combate y dificultad: Las misiones se ajustan a tu escolta.")
