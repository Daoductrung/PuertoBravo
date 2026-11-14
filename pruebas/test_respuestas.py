"""La base de respuestas de la gente de la calle, que se usa cuando no hay modo IA."""
import random
import re

from juego import charla, respuestas as R
from test_mundo_vivo import _vecino

CTX = {"barrio": "Barrio Viejo", "ciudad": "Puerto Bravo", "hora": "las once", "tu": "Dani"}


def _ficha(caracter="amable", **k):
    f = {"nombre": "Maite", "genero": "m", "oficio": "panadera", "caracter": caracter, "confianza": 10}
    f.update(k)
    return f


def test_la_base_es_grande_y_esta_bien_escrita():
    temas, frases = R.cuantas()
    assert temas >= 60 and frases >= 1100
    ids = [t["id"] for t in R.TEMAS]
    assert len(ids) == len(set(ids))
    vistas = set()
    for t in R.TEMAS:
        assert t["claves"] and len(t["r"]) >= 5, t["id"]
        for c in t["claves"]:
            assert c.strip("* ") == R.normal(c.strip("* ")).strip(), f"{t['id']}: clave mal preparada «{c}»"
        for grupo in ("r",) + R.CARACTERES + ("poca", "mucha"):
            for frase in t[grupo]:
                assert frase[0].isupper() or frase[0] in "¿¡{", (t["id"], frase)
                assert frase.rstrip()[-1] in ".?!", (t["id"], frase)
                assert set(re.findall(r"\{(\w+)\}", frase)) <= {"yo", "oficio", "barrio", "ciudad", "hora", "tu", "o"}, (t["id"], frase)
                assert "  " not in frase and (t["id"], frase) not in vistas, (t["id"], frase)
                vistas.add((t["id"], frase))
    for c in R.CARACTERES:                              # todos los caracteres tienen frases propias en casi todos los temas
        assert sum(1 for t in R.TEMAS if t[c]) >= len(R.TEMAS) * 0.85, c


def test_reconoce_de_que_se_habla():
    casos = {"¿Qué tiempo hace hoy?": "tiempo", "Oye, ¿qué tal el trabajo?": "trabajo_duro", "¿De qué equipo eres? ¿Te gusta el fútbol?": "futbol",
             "¿Cómo te llamas?": "nombre", "¿Tienes hijos?": "hijos", "¿Qué opinas del alcalde?": "politica", "¿Me prestas diez euros?": "pedir_dinero",
             "¿Qué sabes de Belmonte?": "belmonte", "MUCHAS GRACIAS": "gracias", "¿Cuántos años tienes?": "edad", "Estoy muy triste hoy": "tristeza",
             "¿Hay trabajo para mí?": "trabajo_para_mi", "¿Qué me recomiendas hacer aquí?": "recomienda", "¿Has oído lo de los robos?": "delincuencia",
             "La policía me busca": "policia", "¿Tienes perro?": "animales", "¿De dónde eres?": "de_donde", "¿Cómo estás?": "como_estas"}
    for texto, esperado in casos.items():
        t = R.tema_de(texto)
        assert t is not None and t["id"] == esperado, (texto, t and t["id"])
    for texto in ("El cielo es azul", "asdf qwer", "Tres por cuatro son doce"):
        assert R.tema_de(texto) is None, texto


def test_cada_caracter_contesta_a_su_manera_y_sin_repetirse():
    largos = {}
    for c in R.CARACTERES:
        rng = random.Random(7)
        f = _ficha(c)
        dichas = [R.responder("¿Qué tal el trabajo?", f, CTX, rng)[0] for _ in range(12)]
        assert len(set(dichas)) >= 10, (c, dichas)                 # una misma persona no repite
        largos[c] = sum(len(d) for d in dichas) / len(dichas)
        for d in dichas:
            assert "{" not in d and d[0].isupper() or d[0] in "¿¡", d
    assert largos["seco"] < largos["amable"] < largos["hablador"]      # el seco habla poco y el hablador, mucho
    # el género de quien habla se respeta
    assert "panadera" in " ".join(R.responder("¿Qué tal el trabajo?", _ficha("chulo"), CTX, random.Random(i))[0] for i in range(40))
    juntas = " ".join(R.responder("¿Cómo estás?", _ficha("amable", genero="h", nombre="Paco"), CTX, random.Random(i))[0] for i in range(80))
    assert "cansado" in juntas.lower() and "cansada" not in juntas.lower()
    # con el mismo tema hay cientos de respuestas distintas entre unas personas y otras
    distintas = {R.responder("que tiempo hace", _ficha("hablador"), CTX, random.Random(i))[0] for i in range(300)}
    assert len(distintas) > 120


def test_confianza_y_temas_delicados():
    rng = random.Random(3)
    frio = [R.responder("¿Cómo te llamas?", _ficha("amable", confianza=-40), CTX, rng)[0] for _ in range(30)]
    assert any(x in " ".join(frio) for x in ("para qué quieres", "no te hace falta"))           # quien no se fía, no se presenta
    amigo = [R.responder("¿Me conoces?", _ficha("amable", confianza=60), CTX, random.Random(i))[0] for i in range(40)]
    assert any("Dani" in a for a in amigo)                                                        # y quien te aprecia te llama por tu nombre
    assert R.responder("¿Me prestas dinero?", _ficha(), CTX, rng)[1] < 0 and R.responder("Muchas gracias", _ficha(), CTX, rng)[1] > 0
    f = _ficha("seco")
    R.responder("¿Te gusta el fútbol?", f, CTX, random.Random(1))
    repes = [R.responder("¿Te gusta el fútbol?", dict(f), CTX, random.Random(i))[0] for i in range(40)]
    assert any(r.startswith(tuple(x.strip() for x in R.REPETIDO)) for r in repes)                 # si insistes en lo mismo, te lo hace notar
    # lo que no se entiende: una pregunta y un comentario no se contestan igual
    assert R.responder("¿Por qué brillan las estrellas?", _ficha("seco"), CTX, random.Random(2))[2] is None
    preguntas = {R.responder("¿Por qué brillan las estrellas?", _ficha("seco"), CTX, random.Random(i))[0] for i in range(60)}
    comentarios = {R.responder("Tres por cuatro son doce", _ficha("seco"), CTX, random.Random(i))[0] for i in range(60)}
    assert not preguntas & comentarios and len(preguntas) > 10 and len(comentarios) > 10


def test_en_el_juego_sin_modo_ia(robot):
    p = robot.nueva_partida()
    q, f = _vecino(p)
    p.cfg["ia_activa"] = False
    assert charla.interpretar("¿qué tal el trabajo?")[0] == "saludar"            # antes esto se quedaba en un saludo
    r = p.responder_libre(q, "¿Qué tal el trabajo?")
    assert r.startswith("Maite: ") and f["ultimo_tema"] == "trabajo_duro"
    r2 = p.responder_libre(q, "¿Por qué brillan las estrellas?")
    assert r2.startswith("Maite: ") and f["ultimo_tema"] is None and r2 != r
    c0 = f["confianza"]
    p.responder_libre(q, "Muchas gracias, eres muy amable")
    assert f["confianza"] > c0
    assert p.responder_libre(q, "hola").startswith("Maite: ")                    # lo de siempre sigue igual: saludar, despedirse...
    assert "Lo más cerca es" in p.responder_libre(q, "¿Dónde hay una farmacia?")
    varias = {p.responder_libre(q, "¿Qué tiempo hace?") for _ in range(8)}
    assert len(varias) >= 7
