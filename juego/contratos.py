"""Contratos del tablón con más variedad (1.7.1).

El tablón de las tabernas ya no ofrece siempre lo mismo. Cada día, y cada vez que cumples uno, cuelga tres encargos
distintos, y eliges: el objetivo de siempre con sus guardaespaldas, uno con escolta que llega en vehículo, uno que huye
en coche, uno metido en un local, uno al que hay que seguir antes hasta su guarida, uno al que solo hay que asustar,
algo que recuperar, o alguien a quien proteger y poner a salvo.

Los tipos de contrato están en los datos (vida.json, contratos) y el editor los edita: un mod puede cambiar los que
hay o añadir otros con cualquiera de las situaciones que el juego sabe montar.
"""
import random

from . import gente as G

SITUACIONES = ("eliminar", "escolta_vehiculo", "huye", "local", "seguir", "intimidar", "recuperar", "proteger")

CONTRATOS = [
    {"id": "clasico", "nombre": "Quitar de en medio", "situacion": "eliminar", "peso": 3, "paga": 600, "paga_escolta": 380, "objetivo": "objetivo_contrato", "escolta": "guardaespaldas",
     "resumen": "{quien} anda por {lugar} con {n} guardaespaldas. Alguien paga por que no vuelva a casa."},
    {"id": "motorizada", "nombre": "Objetivo con escolta motorizada", "situacion": "escolta_vehiculo", "peso": 2, "desde": 2, "paga": 800, "paga_escolta": 420,
     "objetivo": "objetivo_contrato", "escolta": "guardaespaldas", "refuerzo": "escolta_motorizada",
     "resumen": "{quien} está en {lugar}. Lleva {n} de escolta, y parte ronda la zona en un vehículo: llegarán cuando empiece el jaleo."},
    {"id": "fuga", "nombre": "Objetivo a la fuga", "situacion": "huye", "peso": 2, "desde": 1, "paga": 900, "paga_escolta": 150, "salud_vehiculo": 130,
     "modelos": ["sedan", "deportivo", "todoterreno", "utilitario"],
     "resumen": "{quien} se ha enterado de que le buscan y sale de {lugar} en un {modelo}. Hay que alcanzarle y dejarle sin vehículo: ve con algo que corra."},
    {"id": "madriguera", "nombre": "En su madriguera", "situacion": "local", "peso": 2, "paga": 700, "paga_escolta": 380, "objetivo": "objetivo_contrato", "escolta": "maton",
     "locales": ["bar", "taberna", "comida", "gimnasio", "casino", "hotel", "club"],
     "resumen": "{quien} no sale de {lugar}, y dentro tiene a {n} de los suyos. Hay que entrar a buscarle."},
    {"id": "sombra", "nombre": "Tras el recadero", "situacion": "seguir", "peso": 2, "desde": 2, "paga": 950, "paga_escolta": 300, "objetivo": "objetivo_contrato", "escolta": "guardaespaldas",
     "resumen": "Nadie sabe dónde se esconde {quien}. Su recadero sale de {lugar}: síguele a pie sin que te vea y te llevará hasta él."},
    {"id": "aviso", "nombre": "Un aviso", "situacion": "intimidar", "peso": 2, "paga": 550, "paga_escolta": 250, "objetivo": "maton", "escolta": "maton",
     "resumen": "{quien} debe dinero a quien no debe. Está en {lugar} con {n} más. A él no hay que matarle: dale un escarmiento hasta que se rinda. Mejor con los puños o un arma de mano."},
    {"id": "recobro", "nombre": "Recuperar lo robado", "situacion": "recuperar", "peso": 2, "desde": 1, "paga": 750, "paga_escolta": 350, "objetivo": "atracador", "escolta": "maton",
     "objetos": ["un maletín con documentos", "una bolsa con joyas", "una caja con relojes", "un sobre con fotografías", "un disco duro"],
     "resumen": "{quien} se llevó {objeto} que no era suyo. Lo guarda en {lugar}, con {n} hombres. Quítaselo y tráelo."},
    {"id": "custodia", "nombre": "Proteger a un testigo", "situacion": "proteger", "peso": 2, "desde": 3, "paga": 1000, "paga_escolta": 300, "escolta": "pandillero", "refuerzo": "pandillero_motorizado",
     "personas": ["la testigo", "el contable", "el periodista", "la abogada", "el chivato"],
     "resumen": "Van a por {persona}, que te espera en {lugar}. Llegan {n} en un vehículo: acaba con ellos y llévale a pie o en coche hasta {destino}."},
]


def tipos(p):
    lista = [c for c in p.datos.get("contratos", []) if isinstance(c, dict) and c.get("situacion") in SITUACIONES]
    return lista or CONTRATOS


def _lista(c, clave, serie):
    v = c.get(clave)
    return [str(x) for x in v if str(x).strip()] if isinstance(v, list) and any(str(x).strip() for x in v) else list(serie)


class Contratos:
    """Mixin de Partida."""

    def ofertas_contrato(self, l, n=3):
        """Los encargos que cuelgan hoy del tablón de ese sitio. Son los mismos todo el día, hasta que cumplas uno."""
        j = self.j
        hechos = j.stats.get("contratos", 0)
        rng = random.Random(f"contratos:{j.semilla}:{self.dia}:{l.id}:{hechos}")
        disponibles = [c for c in tipos(self) if hechos >= int(c.get("desde", 0) or 0)]
        if not disponibles:
            disponibles = tipos(self)[:1]
        elegidos = []
        bolsa = list(disponibles)
        while bolsa and len(elegidos) < n:
            c = rng.choices(bolsa, weights=[max(0.01, float(x.get("peso", 1) or 1)) for x in bolsa])[0]
            bolsa.remove(c)
            o = self._oferta(c, l, rng)
            if o:
                elegidos.append(o)
        return elegidos

    def _oferta(self, c, l, rng):
        """Un encargo concreto de un tipo: quién, dónde, con cuántos y lo que paga."""
        hechos = self.j.stats.get("contratos", 0)
        n = min(5, 1 + hechos // 2)
        sit = c["situacion"]
        lugares = [x for x in self.mundo.lugares.values() if x.tipo not in ("salida", "muelle", "embarcadero") and "xy" not in x.d and x is not l]
        if sit == "local":
            de_tipo = [x for x in lugares if x.tipo in _lista(c, "locales", ["bar", "taberna", "comida"])]
            lugares = de_tipo or lugares
        cerca = [x for x in lugares if 150 <= self._dist(x) <= 900] or lugares
        if not cerca:
            return None
        dest = rng.choice(cerca)
        o = {"tipo": c, "quien": rng.choice(G.lista("apodos")), "lugar": dest, "n": n,
             "paga": int(c.get("paga", 600)) + int(c.get("paga_escolta", 380)) * n}
        if sit == "huye":
            modelos = [m for m in _lista(c, "modelos", ["sedan"]) if m in self.modelos] or ["sedan"]
            o["modelo"] = rng.choice(modelos)
        if sit == "recuperar":
            o["objeto"] = rng.choice(_lista(c, "objetos", ["un maletín"]))
        if sit in ("proteger", "seguir"):
            otros = [x for x in lugares if x is not dest and 120 <= ((x.x - dest.x) ** 2 + (x.y - dest.y) ** 2) ** 0.5 <= 450] or [x for x in lugares if x is not dest]
            if not otros:
                return None
            o["destino"] = rng.choice(otros)
            o["persona"] = rng.choice(_lista(c, "personas", ["la testigo"])) if sit == "proteger" else "el recadero de " + o["quien"]
        o["resumen"] = self._contrato_txt(c.get("resumen") or "{quien}, en {lugar}.", o)
        return o

    def _contrato_txt(self, texto, o):
        cambios = {"quien": o["quien"], "lugar": o["lugar"].nombre, "n": o["n"], "paga": o["paga"], "objeto": o.get("objeto", "algo"), "persona": o.get("persona", "alguien"),
                   "destino": o["destino"].nombre if o.get("destino") else "", "modelo": self.modelos[o["modelo"]]["nombre"] if o.get("modelo") else ""}
        for k, v in cambios.items():
            texto = texto.replace("{" + k + "}", str(v))
        return texto[:1].upper() + texto[1:]

    def empezar_contrato_de(self, l, o):
        """Empieza un encargo del tablón. Cada situación se monta con los pasos de misión que ya sabe jugar el juego."""
        c, sit, quien, dest, n = o["tipo"], o["tipo"]["situacion"], o["quien"], o["lugar"], o["n"]
        clase_obj = c.get("objetivo") or "objetivo_contrato"
        clase_esc = c.get("escolta") or "guardaespaldas"
        armas = ["pistola", "pistola", "subfusil", "escopeta", "navaja"]

        def objetivo(**extra):
            return dict(G.grupo(clase_obj, arma="pistola", salud=95), tipo=f"Objetivo, {quien}", **extra)

        def escolta(cuantos, nombre="Guardaespaldas"):
            return [G.grupo(clase_esc, tipo=nombre, arma=random.choice(armas), salud=70) for _ in range(max(0, cuantos))]

        def en_vehiculo(cuantos):
            """Parte de la escolta, en el vehículo del tipo de refuerzo, si lo hay y aquí puede venir."""
            t = G.tipo_enemigo(c.get("refuerzo"))
            if not t or t.get("vehiculo") not in self.modelos or cuantos <= 0:
                return []
            return [{"n": cuantos, "clase": c["refuerzo"]}]
        cobrar = {"tipo": "ir", "lugar": l.id, "texto": f"Hecho. Vuelve a {l.nombre} a cobrar."}
        if sit == "eliminar":
            pasos = [{"tipo": "eliminar", "lugar": dest.id, "texto": f"El objetivo, {quien}, está en {dest.nombre} con {n} guardaespaldas. Ve allí y cumple el contrato.",
                      "enemigos": [objetivo()] + escolta(n)}]
        elif sit == "escolta_vehiculo":
            coche = en_vehiculo(max(1, min(n, 3)))
            llegan = sum(g["n"] for g in coche)
            pasos = [{"tipo": "eliminar", "lugar": dest.id,
                      "texto": f"El objetivo, {quien}, está en {dest.nombre} con {n} de escolta." + (f" {llegan} de ellos rondan la zona en un vehículo y llegarán en cuanto empiece." if llegan else ""),
                      "enemigos": [objetivo()] + escolta(n - llegan) + coche}]
        elif sit == "huye":
            mo = self.modelos[o["modelo"]]
            pasos = [{"tipo": "perseguir", "lugar": dest.id, "modelo": mo["id"], "nombre": f"{mo['nombre']} de {quien}", "salud": int(c.get("salud_vehiculo", 130)),
                      "texto": f"{quien} huye en un {mo['nombre']} desde {dest.nombre}. Alcánzale con un vehículo y destrózaselo: embístele, o fíjalo con la Q y dispara con Control."}]
        elif sit == "local":
            pasos = [{"tipo": "ir", "lugar": dest.id, "radio": 9, "texto": f"{quien} está dentro de {dest.nombre}, con {n} de los suyos. Llega hasta la puerta, a pie."},
                     {"tipo": "eliminar", "lugar": dest.id, "ya": True, "texto": f"Empujas la puerta de {dest.nombre} y se acaba la música. {quien} te ha reconocido.",
                      "enemigos": [objetivo()] + escolta(n, "Hombre de " + quien)}]
        elif sit == "seguir":
            guarida = o["destino"]
            pasos = [{"tipo": "seguir", "lugar": dest.id, "destino": guarida.id, "persona": o["persona"],
                      "texto": f"El recadero de {quien} sale de {dest.nombre}. Ve allí y síguele a pie, de oído, sin pegarte a él y sin perderle: te llevará a la guarida."},
                     {"tipo": "eliminar", "lugar": guarida.id, "ya": True, "texto": f"El recadero entra en {guarida.nombre}: ahí se esconde {quien}, con {n} guardaespaldas. Ahora, a por él.",
                      "enemigos": [objetivo()] + escolta(n)}]
        elif sit == "intimidar":
            pasos = [{"tipo": "eliminar", "lugar": dest.id,
                      "texto": f"{quien} está en {dest.nombre} con {n} más. A él no le mates: pégale hasta que se rinda. A los demás, como veas.",
                      "enemigos": [dict(G.grupo(clase_obj, arma="bate", salud=120), tipo=f"Moroso, {quien}", intimidar=True, salud=120, arma="bate")] + escolta(n, "Amigo de " + quien)}]
        elif sit == "recuperar":
            pasos = [{"tipo": "eliminar", "lugar": dest.id, "texto": f"{quien} guarda {o['objeto']} en {dest.nombre}, con {n} hombres. Acaba con ellos.",
                      "enemigos": [dict(G.grupo(clase_obj, arma="pistola", salud=85), tipo=f"Ladrón, {quien}")] + escolta(n, "Hombre de " + quien)},
                     {"tipo": "recoger", "lugar": dest.id, "objeto": o["objeto"][:1].upper() + o["objeto"][1:], "texto": f"Ya no lo guarda nadie. Busca {o['objeto']} y cógelo."}]
            cobrar = {"tipo": "ir", "lugar": l.id, "texto": f"Lo tienes. Llévalo a {l.nombre} y cobra."}
        else:                                                    # proteger
            refugio = o["destino"]
            atacan = en_vehiculo(max(1, min(n + 1, 4))) or escolta(n + 1, "Sicario")
            pasos = [{"tipo": "ir", "lugar": dest.id, "texto": f"{o['persona'].capitalize()} te espera en {dest.nombre}. Llega antes que quienes van a por {o['persona'].split()[0]}."},
                     {"tipo": "eliminar", "lugar": dest.id, "ya": True, "texto": f"Ya están aquí: vienen a por {o['persona']}. Que no pasen.", "enemigos": atacan},
                     {"tipo": "escoltar", "lugar": dest.id, "destino": refugio.id, "persona": o["persona"],
                      "texto": f"Despejado. Acércate a {o['persona']}, que sigue en {dest.nombre}, y llévale hasta {refugio.nombre}: te sigue a pie y sube al vehículo que cojas."}]
        self._empezar_repetible({"id": "contrato", "titulo": f"{c.get('nombre', 'Contrato')}: {quien}", "lugar": l.id, "contador": "contratos", "clase_contrato": c.get("id"),
                                 "pasos": pasos + [cobrar], "recompensa": {"dinero": int(o["paga"])}})
        return True


def menu_contratos(p, l):
    """El tablón de encargos de una taberna: tres contratos para elegir."""
    from .menus import Menu, Opcion
    app = p.app

    def aceptar(o):
        def f():
            if p.mision or p.trabajo or p.guerra:
                app.son("error")
                return app.decir("Termina antes lo que tienes entre manos.", True)
            if p.de_servicio():
                app.son("error")
                return app.decir("Estás de servicio. Estos encargos no son para quien lleva placa.", True)
            p.empezar_contrato_de(l, o)
        return f

    def ops():
        lista = [Opcion(f"{o['tipo'].get('nombre', 'Contrato')}, {o['paga']} euros. {o['resumen']}", aceptar(o),
                        ayuda="Intro acepta este encargo. Al cumplirlo se cobra aquí mismo, y el tablón cambia. Cada contrato cumplido hace los siguientes más difíciles y mejor pagados.")
                 for o in p.ofertas_contrato(l)]
        return (lista or [Opcion("Hoy el tablón está vacío")]) + [Opcion("Volver", lambda: app.cerrar(m))]
    m = Menu(app, f"Tablón de encargos de {l.nombre}. Llevas {p.j.stats.get('contratos', 0)} contratos cumplidos", ops,
             intro="Hay varios encargos, cada uno de una manera. Elige uno con Intro")
    app.abrir(m)
