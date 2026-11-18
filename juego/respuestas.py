"""Base de respuestas de la gente de la calle, para cuando no se usa el modo IA.

El jugador escribe lo que quiera. El juego busca de qué está hablando (el tiempo, el fútbol, la familia, la
policía, el trabajo, el barrio...) y la persona contesta con una frase de la base, según su carácter, la
confianza que le tenga y la situación. Las frases se montan con piezas (una entrada, el cuerpo y una coletilla)
y cada persona recuerda lo que ya ha dicho, así que es muy difícil oír dos veces lo mismo.

Los temas están en respuestas_datos1.py y respuestas_datos2.py. Para añadir uno basta con una línea T(...).
En las frases se pueden usar: {yo} nombre de quien habla, {oficio}, {barrio}, {ciudad}, {tu} nombre del jugador,
{o} terminación de género de quien habla (cansad{o}) y {hora}.
"""
import random
import unicodedata

CARACTERES = ("amable", "hablador", "seco", "timido", "chulo")
TEMAS = []
_POR_ID = {}


def T(ident, claves, generales, amable=(), hablador=(), seco=(), timido=(), chulo=(), poca=(), mucha=(), confianza=1, flojo=False):
    """Da de alta un tema. claves: palabras o trozos separados por |, sin tildes. poca/mucha: frases para poca o mucha confianza."""
    tema = {"id": ident, "claves": tuple(("*" if c.startswith("*") else "") + normal(c.lstrip("*")).strip() + (" " if c.endswith(" ") else "") for c in claves.split("|") if c.strip()), "r": tuple(generales), "amable": tuple(amable),
            "hablador": tuple(hablador), "seco": tuple(seco), "timido": tuple(timido), "chulo": tuple(chulo), "poca": tuple(poca), "mucha": tuple(mucha),
            "confianza": confianza, "flojo": flojo}      # flojo: tema comodín, que cede ante cualquier otro
    TEMAS.append(tema)
    _POR_ID[ident] = tema
    return tema


# Piezas que dan a cada frase el aire del carácter de quien habla. La cadena vacía cuenta: muchas veces no se pone nada.
ENTRADAS = {
    "amable": ("", "", "", "Pues mira, ", "Ay, ", "Mira, ", "Pues la verdad, ", "Hombre, ", "Te digo una cosa: ", "Si te soy sincer{o}, ", "Qué quieres que te diga, ", "Pues verás, "),
    "hablador": ("", "", "Uy, ", "Calla, calla, ", "Pues mira, te cuento: ", "No me tires de la lengua. ", "¿Tú sabes lo que te digo? ", "Mira que te diga, ", "Anda que no. ",
                 "Fíjate lo que te voy a decir: ", "Pues eso mismo decía yo ayer. ", "Ahora que lo dices, "),
    "seco": ("", "", "", "", "", "Mira, ", "A ver, ", "Pues ", "Bah. ", "En fin. "),
    "timido": ("", "", "Eh... ", "Pues... ", "Bueno... ", "No sé... ", "Yo... ", "A ver... ", "Esto... ", "Perdona, es que... "),
    "chulo": ("", "", "Mira, chaval[|a], ", "Te lo digo yo: ", "A mí me lo vas a contar. ", "Escucha, ", "Venga ya. ", "Eso lo sé yo de sobra. ", "Tú apunta: ", "Mira lo que te digo, "),
}
COLETILLAS = {
    "amable": ("", "", "", " ¿Y tú qué tal?", " Así es la vida.", " Pero bien, ¿eh?", " Gracias por preguntar.", " No nos podemos quejar.", " Ya ves tú.", " Qué le vamos a hacer.",
               " Poquito a poco.", " Y que no falte."),
    "hablador": ("", " Y no te cuento más porque no acabamos.", " Que luego dicen que hablo mucho.", " ¿A que sí?", " Y eso que no sabes ni la mitad.", " Ya te contaré otro día con calma.",
                 " Bueno, ya sabes cómo es esto.", " Y así todo.", " Pero vamos, que es lo que hay.", " Que yo de esto podría escribir un libro.", " ¿Tú qué opinas?", " Lo que yo te diga."),
    "seco": ("", "", "", "", "", " Y ya.", " Punto.", " Nada más.", " Es lo que hay.", " Pues eso."),
    "timido": ("", "", "", " Creo.", " O eso me parece.", " No sé si me explico.", " Perdona.", " Bueno, tú sabrás más.", " Digo yo.", " Si no te importa."),
    "chulo": ("", "", " Y el que diga otra cosa, miente.", " Como te lo cuento.", " Para que te enteres.", " Y a mucha honra.", " Que aquí me conoce todo el mundo.", " Apréndetelo.",
              " Yo no hablo por hablar.", " Tú hazme caso."),
}
# Cuando el jugador vuelve sobre lo mismo
REPETIDO = ("Ya te lo he dicho antes, pero bueno. ", "¿Otra vez con eso? ", "Como te decía, ", "Sigues con lo mismo, ¿eh? ", "Te lo repito: ", "Lo mismo que antes: ", "Y dale. ")
# Lo que dice quien no se fía de ti, a cualquier pregunta
DESCONFIANZA = ("No sé por qué te lo iba a contar a ti.", "Eso no es asunto tuyo.", "Prefiero no hablar de eso contigo.", "Mira, mejor lo dejamos.", "¿Y a ti qué más te da?",
                "No te conozco tanto como para eso.", "Pregúntale a otro.", "Tengo prisa.", "Yo no sé nada.", "Déjame en paz, anda.")
# Cuando no se reconoce de qué habla: una pregunta
NO_SE_PREGUNTA = {
    "": ("Pues no sabría decirte.", "Ni idea, la verdad.", "Eso habría que preguntárselo a otro.", "No lo sé. De eso no entiendo.", "Buena pregunta. No tengo ni idea.", "A saber.",
         "Eso depende de a quién le preguntes.", "No me lo había planteado nunca.", "Pues ahora que lo dices, no lo sé.", "Vete tú a saber.", "No te lo sé decir seguro.",
         "Eso pregúntalo en {barrio}, que allí lo saben todo.", "Yo de eso sé lo justo.", "No me hagas mucho caso, pero creo que no.", "Yo diría que sí, pero no pongo la mano en el fuego.",
         "Quién sabe.", "Eso mismo me pregunto yo.", "Uf, me pillas fuera de juego.", "No sabría ni por dónde empezar.", "Pregunta en el bar, que allí se enteran de todo."),
    "amable": ("Ojalá pudiera ayudarte, pero no lo sé.", "Lo siento, de eso no sé nada. Pregunta a ver si alguien te dice.", "Ay, pues no te sé decir. Perdona.", "No lo sé, pero si me entero te lo digo."),
    "hablador": ("No lo sé, pero conozco a uno que seguro que sí. Bueno, lo conocía.", "De eso no sé, y mira que yo sé de casi todo.", "Pues no, y eso que le he dado vueltas. A otras cosas, pero vueltas.",
                 "Ni idea, pero te puedo contar otra cosa si quieres."),
    "seco": ("No sé.", "Ni idea.", "No.", "A mí no me preguntes.", "Sabe Dios."),
    "timido": ("No... no lo sé. Perdona.", "Yo de eso no sé nada, lo siento.", "Creo que no lo sé.", "Mejor pregúntale a otra persona."),
    "chulo": ("Si lo supiera no te lo iba a decir gratis.", "Eso no lo sabe ni el alcalde.", "Yo sé muchas cosas, pero esa no.", "¿Me has visto cara de oficina de información?"),
}
# Cuando no se reconoce de qué habla: un comentario
NO_SE_COMENTARIO = {
    "": ("Ya, ya.", "Puede ser.", "Si tú lo dices.", "Mira qué bien.", "Eso dicen.", "Pues vaya.", "No te digo que no.", "Cada uno lo ve a su manera.", "Qué cosas.", "Ajá.",
         "Vaya por Dios.", "Pues mira, no lo había pensado así.", "Tú sabrás.", "Eso es verdad.", "Ya ves.", "Hombre, visto así.", "Algo de eso he oído.", "No me extraña nada.",
         "Pues qué bien, ¿no?", "Así están las cosas.", "Será eso.", "Lo que tú digas.", "Me lo creo.", "Pues anda que no.", "Menuda historia."),
    "amable": ("Qué interesante lo que cuentas.", "Me alegro por ti, de verdad.", "Pues mira, eso está muy bien.", "Qué bien que me lo cuentes."),
    "hablador": ("Eso mismo le decía yo a mi vecina el otro día, que no me dejó ni terminar.", "Uy, de eso tengo yo una historia, pero es larga.", "Pues igualito que lo que me pasó a mí. Bueno, parecido.",
                 "¡No me digas! Sigue, sigue."),
    "seco": ("Ya.", "Bueno.", "Vale.", "Ah.", "Si tú lo dices."),
    "timido": ("Ah... vale.", "Sí, supongo.", "Claro, claro.", "No sabía."),
    "chulo": ("Eso ya lo sabía yo.", "Me lo vas a contar a mí.", "Bah, eso no es nada.", "Qué me vas a contar."),
}


def normal(texto):
    """Minúsculas y sin tildes, con un espacio delante y detrás, para buscar palabras."""
    t = unicodedata.normalize("NFD", (texto or "").lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")          # sin tildes; la ñ queda como n
    t = " " + " ".join("".join(c if c.isalnum() else " " for c in t).split()) + " "
    return t.replace(" del ", " de el ").replace(" al ", " a el ")          # así «del alcalde» casa con «el alcalde»


def tema_de(texto):
    """El tema del que habla el jugador, o None. Gana el que más y más largas palabras clave acierte."""
    _cargar()
    t = normal(texto)
    for relleno in (" muy ", " tan ", " bastante ", " un poco ", " super ", " realmente ", " de verdad ", " oye ", " pues "):
        t = t.replace(relleno, " ")                 # «estoy muy triste» es «estoy triste»
    mejor, nota = None, 0
    for tema in TEMAS:
        n = 0
        for clave in tema["claves"]:
            if (" " + clave if not clave.startswith("*") else clave[1:]) in t:
                n += len(clave)
        if tema["flojo"]:
            n *= 0.4
        if n > nota:
            mejor, nota = tema, n
    return mejor


def _cargar():
    if not TEMAS:
        from . import respuestas_datos1, respuestas_datos2      # noqa: F401  (al importarse dan de alta sus temas)


def cuantas():
    """Cuántos temas y cuántas frases distintas hay en la base, sin contar las combinaciones."""
    _cargar()
    frases = sum(len(t["r"]) + sum(len(t[c]) for c in CARACTERES) + len(t["poca"]) + len(t["mucha"]) for t in TEMAS)
    frases += sum(len(v) for v in NO_SE_PREGUNTA.values()) + sum(len(v) for v in NO_SE_COMENTARIO.values()) + len(DESCONFIANZA)
    return len(TEMAS), frases


PROPIOS = ("Belmonte", "Bravo", "Dios", "Capitán", "{yo}", "{barrio}", "{ciudad}", "{hora}")


def _unir(entrada, frase):
    """Pone una entrada delante de una frase, con la mayúscula donde toca."""
    if not entrada:
        return frase
    if entrada.rstrip().endswith((".", "?", "!")) or frase.startswith(("¿", "¡") + PROPIOS):
        return entrada + frase
    return entrada + frase[0].lower() + frase[1:]


def _elegir(opciones, dichas, rng):
    """Una frase que esta persona no haya dicho hace poco."""
    nuevas = [o for o in opciones if o not in dichas]
    return rng.choice(nuevas or list(opciones))


def _poner_datos(frase, ficha, ctx):
    datos = {"yo": ficha.get("nombre", ""), "oficio": ficha.get("oficio", ""), "o": "a" if ficha.get("genero") == "m" else "o",
             "barrio": ctx.get("barrio", "el barrio"), "ciudad": ctx.get("ciudad", "la ciudad"), "hora": ctx.get("hora", ""), "tu": ctx.get("tu", "")}
    for k, v in datos.items():
        frase = frase.replace("{" + k + "}", v)
    return frase[0].upper() + frase[1:]


def suelta(ficha, ctx, temas=None, rng=random):
    """Una frase suelta de una persona sin que nadie le pregunte: lo que se le oye a alguien que pasa hablando con otro.
    «temas» son los temas que valen para eso; vacío, cualquiera de los que no piden confianza."""
    _cargar()
    from . import gente
    caracter = gente.habla_de(ficha.get("caracter", "amable"))
    cand = [t for t in TEMAS if t["id"] in temas] if temas else []
    tema = rng.choice(cand or [t for t in TEMAS if t["confianza"] == 1 and not t["flojo"]] or TEMAS)
    ops = [f for f in list(tema["r"]) + list(tema[caracter]) * 2 if "{tu}" not in f and "{yo}" not in f and "[" not in f]      # nada que vaya dirigido a ti
    cuerpo = rng.choice(ops or list(tema["r"]))
    if len(cuerpo) < 110:
        cuerpo = _unir(rng.choice([e for e in ENTRADAS[caracter] if "[" not in e]), cuerpo)
    return _poner_datos(cuerpo, ficha, ctx)


def comentario(ficha, rng=random):
    """Lo que contesta quien va al lado: un comentario corto, con el aire de su carácter."""
    from . import gente
    caracter = gente.habla_de(ficha.get("caracter", "amable"))
    return _poner_datos(rng.choice(NO_SE_COMENTARIO[""] + NO_SE_COMENTARIO[caracter] * 2), ficha, {})


def responder(texto, ficha, ctx, rng=random):
    """Lo que contesta la persona a un texto libre. Devuelve (frase, cambio de confianza, id del tema o None).

    ctx: diccionario con barrio, ciudad, hora y tu (nombre del jugador).
    """
    _cargar()
    from . import gente
    caracter = gente.habla_de(ficha.get("caracter", "amable"))       # un carácter de un mod habla con las frases de uno de los de serie
    conf = ficha.get("confianza", 0)
    dichas = ficha.setdefault("dichas", [])
    tema = tema_de(texto)
    repetido = ""
    if tema is None:
        tabla = NO_SE_PREGUNTA if "?" in (texto or "") or normal(texto).split()[:1] in (["que"], ["como"], ["cuando"], ["donde"], ["quien"], ["por"], ["cual"], ["cuanto"]) else NO_SE_COMENTARIO
        cuerpo = _elegir(tabla[""] + tabla[caracter] * 3, dichas, rng)
        cambio, ident = 0, None
    else:
        ident = tema["id"]
        if ficha.get("ultimo_tema") == ident and rng.random() < 0.5:
            repetido = rng.choice(REPETIDO)
        if conf < -10 and tema["confianza"] >= 0 and rng.random() < 0.6:
            cuerpo = _elegir(tema["poca"] or DESCONFIANZA, dichas, rng)
        else:
            opciones = list(tema["r"]) + list(tema[caracter]) * 3            # las de su carácter salen más
            if conf >= 30:
                opciones += list(tema["mucha"]) * 3
            cuerpo = _elegir(opciones, dichas, rng)
        cambio = tema["confianza"]
    ficha["ultimo_tema"] = ident
    dichas.append(cuerpo)
    del dichas[:-40]
    frase = cuerpo
    if len(cuerpo) < 120 and not repetido:
        frase = _unir(rng.choice(ENTRADAS[caracter]), frase)
    if tema is not None and len(frase) < 140 and not cuerpo.endswith("?") and rng.random() < 0.45:
        frase += rng.choice(COLETILLAS[caracter])
    frase = _unir(repetido, frase)
    datos = {"yo": ficha.get("nombre", ""), "oficio": ficha.get("oficio", ""), "o": "a" if ficha.get("genero") == "m" else "o",
             "barrio": ctx.get("barrio", "el barrio"), "ciudad": ctx.get("ciudad", "la ciudad"), "hora": ctx.get("hora", ""), "tu": ctx.get("tu", "")}
    for k, v in datos.items():
        frase = frase.replace("{" + k + "}", v)
    return frase[0].upper() + frase[1:], cambio, ident
