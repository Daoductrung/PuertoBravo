"""Modo IA con varios servicios, sin red: se sustituye la función que hace las peticiones.

Comprueba el formato de cada servicio, la elección automática del modelo barato, el paso de un servicio a otro
cuando uno falla, el cambio de modelo cuando el elegido deja de existir y el guardado cifrado de las claves.
"""
import json
import os

import pygame
import pytest

from juego import ia, registro, rutas
from test_mundo_vivo import _vecino

MODELOS = {
    "anthropic": {"data": [
        {"id": "claude-opus-5-5", "line": "opus", "lifecycle": "active", "created_at": "2026-09-01T00:00:00Z"},
        {"id": "claude-haiku-4-5", "line": "haiku", "lifecycle": "active", "created_at": "2025-10-01T00:00:00Z"},
        {"id": "claude-haiku-5-5", "line": "haiku", "lifecycle": "active", "created_at": "2026-08-01T00:00:00Z"},
        {"id": "claude-haiku-3", "line": "haiku", "lifecycle": "retired", "created_at": "2024-03-01T00:00:00Z"}]},
    "openai": {"data": [
        {"id": "gpt-6-sol", "created": 900}, {"id": "gpt-6-luna", "created": 900}, {"id": "gpt-5.6-luna", "created": 800},
        {"id": "gpt-6-luna-audio", "created": 950}, {"id": "gpt-5-nano", "created": 500, "shutdown_date": "2026-12-11"},
        {"id": "text-embedding-4-luna", "created": 990}]},
    "gemini": {"models": [
        {"name": "models/gemini-3.5-flash-lite", "supportedGenerationMethods": ["generateContent"]},
        {"name": "models/gemini-2.5-flash-lite", "supportedGenerationMethods": ["generateContent"]},
        {"name": "models/gemini-3.5-flash-lite-preview", "supportedGenerationMethods": ["generateContent"]},
        {"name": "models/gemini-4-hydrogen", "supportedGenerationMethods": ["generateContent"]},
        {"name": "models/gemini-embedding-2", "supportedGenerationMethods": ["embedContent"]}]},
}
BUENA = json.dumps({"respuesta": "Pues  mira, hoy hace bueno.", "confianza": 7, "accion": "nada"})


class Red:
    """Internet de pega: anota cada petición y contesta como lo haría cada servicio."""

    def __init__(self):
        self.pedidos = []
        self.falla = {}             # trozo de dirección -> código de error
        self.sin_modelo = set()     # modelos que ya no existen
        self.texto = BUENA
        self.locales = False

    def __call__(self, metodo, url, cabeceras, cuerpo=None, espera=0):
        self.pedidos.append((metodo, url, cabeceras, cuerpo))
        for trozo, codigo in self.falla.items():
            if trozo in url and metodo == "POST":
                raise ia.ErrorIA(codigo, "fallo de pega")
        if "127.0.0.1" in url:
            if not self.locales:
                raise ia.ErrorIA(0, "ConnectionRefusedError")
            if metodo == "GET":
                return {"data": [{"id": "qwen-pequeno"}]}
            return {"choices": [{"message": {"content": "Aquí andamos, tirando."}}]}
        servicio = "anthropic" if "anthropic" in url else "openai" if "openai.com" in url else "gemini" if "googleapis" in url else "otro"
        if metodo == "GET":
            return MODELOS.get(servicio, {"data": [{"id": "caro/grande"}, {"id": "pequeno/chat:free"}]})
        mod = cuerpo.get("model") or url.split("/models/")[1].split(":")[0]
        if mod in self.sin_modelo:
            raise ia.ErrorIA(404, "model not found")
        if servicio == "anthropic":
            return {"stop_reason": "end_turn", "content": [{"type": "thinking", "thinking": "..."}, {"type": "text", "text": self.texto}]}
        if servicio == "gemini":
            return {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": self.texto}]}}]}
        return {"choices": [{"message": {"content": self.texto}}]}


@pytest.fixture
def red(monkeypatch, tmp_path):
    r = Red()
    monkeypatch.setattr(ia, "_pedir", r)
    monkeypatch.setattr(ia, "_ruta_clave", lambda: str(tmp_path / "ia.pbc"))
    monkeypatch.setattr(ia, "_ruta_modelos", lambda: str(tmp_path / "ia_modelos.json"))
    monkeypatch.setattr(ia, "carpeta_local", lambda: str(tmp_path / "ia_local"))
    monkeypatch.setattr(ia, "_modelos", None)
    for v in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY"):
        monkeypatch.delenv(v, raising=False)
    ia._pausa.clear()
    ia._local.update(base="", t=0.0)
    yield r
    ia._pausa.clear()
    ia._local.update(base="", t=0.0)


def test_elige_el_modelo_barato_de_cada_servicio():
    assert ia.candidatos("anthropic", MODELOS["anthropic"]["data"]) == ["claude-haiku-5-5", "claude-haiku-4-5"]
    assert ia.candidatos("openai", MODELOS["openai"]["data"]) == ["gpt-6-luna", "gpt-5.6-luna"]          # ni audio, ni incrustaciones, ni los que cierran
    assert ia.candidatos("gemini", MODELOS["gemini"]["models"]) == ["gemini-2.5-flash-lite", "gemini-3.5-flash-lite"]
    assert ia.candidatos("openai", [{"id": "gpt-9-nano", "created": 1}, {"id": "gpt-9-mini", "created": 2}]) == ["gpt-9-nano"]
    assert ia.candidatos("otro", [{"id": "caro/grande"}, {"id": "pequeno/chat:free"}])[0] == "pequeno/chat:free"


def test_claves_cifradas_y_compatibles_con_la_version_anterior(red):
    from juego import cifrado
    cifrado.escribir_json(ia._ruta_clave(), {"clave": "clave-antigua-123"}, cifrado=True)       # así se guardaba antes: una sola, de Anthropic
    assert ia.clave("anthropic") == "clave-antigua-123" and ia.clave("gemini") == ""
    ia.guardar_clave("clave-gemini-456", "gemini")
    assert ia.clave_guardada("gemini") == "clave-gemini-456" and ia.clave_guardada("anthropic") == "clave-antigua-123"
    bruto = open(ia._ruta_clave(), "rb").read()
    assert b"clave-gemini" not in bruto and b"clave-antigua" not in bruto
    ia.guardar_clave("", "gemini")
    ia.guardar_clave("", "anthropic")
    assert not os.path.exists(ia._ruta_clave())


def test_cada_servicio_recibe_su_formato(robot, red):
    p = robot.nueva_partida()
    q, f = _vecino(p)
    cfg = p.cfg
    for servicio, cabecera, trozo in (("anthropic", "x-api-key", "/messages"), ("openai", "Authorization", "/chat/completions"),
                                      ("gemini", "x-goog-api-key", ":generateContent"), ("otro", "Authorization", "/chat/completions")):
        ia.guardar_clave(f"clave-{servicio}-secreta", servicio)
        cfg["ia_servicio"] = servicio
        red.pedidos.clear()
        r = ia.responder(p, q, "¿Qué tal el día?")
        assert r == {"respuesta": "Pues mira, hoy hace bueno.", "confianza": 7, "accion": "nada"}, servicio
        metodo, url, cab, cuerpo = red.pedidos[-1]
        assert metodo == "POST" and trozo in url and url.startswith("https://") and "clave" not in url
        assert f"clave-{servicio}-secreta" in cab[cabecera]
        texto = json.dumps(cuerpo, ensure_ascii=False)
        assert "¿Qué tal el día?" in texto and "panadera" in texto and "explícito" in texto and "humor_de_ahora" in texto
        assert ia.ultimo_uso["servicio"] == servicio
    assert red.pedidos[-1][1].startswith(ia.OTRO_POR_DEFECTO) and red.pedidos[-1][3]["model"] == "pequeno/chat:free"
    # los modelos elegidos se recuerdan: la segunda vez no se vuelve a pedir la lista
    cfg["ia_servicio"] = "anthropic"
    red.pedidos.clear()
    ia.responder(p, q, "otra cosa")
    assert [m for m, *_ in red.pedidos] == ["POST"] and red.pedidos[0][3]["model"] == "claude-haiku-5-5"
    assert "temperature" not in red.pedidos[0][3] and red.pedidos[0][3]["messages"][-1]["role"] == "user"


def test_automatico_prueba_lo_gratuito_y_salta_al_siguiente(robot, red):
    p = robot.nueva_partida()
    q, f = _vecino(p)
    cfg = p.cfg
    cfg["ia_servicio"] = "auto"
    assert not ia.disponible(cfg) and "clave" in ia.por_que_no(cfg)
    ia.guardar_clave("k-anthropic", "anthropic")
    ia.guardar_clave("k-openai", "openai")
    ia.guardar_clave("k-gemini", "gemini")
    assert ia.orden(cfg) == ["gemini", "openai", "anthropic"]                     # primero el que tiene nivel gratuito
    assert ia.responder(p, q, "hola")["confianza"] == 7 and ia.ultimo_uso["servicio"] == "gemini"
    assert ia.ultimo_uso["modelo"] == "gemini-2.5-flash-lite"
    # Gemini llega a su límite: contesta OpenAI, y a Gemini se le deja descansar
    red.falla["googleapis"] = 429
    assert ia.responder(p, q, "hola otra vez") and ia.ultimo_uso["servicio"] == "openai" and ia.ultimo_uso["modelo"] == "gpt-6-luna"
    red.pedidos.clear()
    ia.responder(p, q, "y otra")
    assert not any("googleapis" in u for _, u, *_ in red.pedidos)
    # con un modelo local en marcha, va el primero, y sin formato JSON
    ia._pausa.clear()
    red.locales = True
    ia._local["t"] = 0.0
    assert ia.orden(cfg)[0] == "local"
    r = ia.responder(p, q, "buenas")
    assert r == {"respuesta": "Aquí andamos, tirando.", "confianza": 1, "accion": "nada"} and ia.ultimo_uso["modelo"] == "qwen-pequeno"
    assert red.pedidos[-1][3]["max_tokens"] <= 100 and "seed" in red.pedidos[-1][3]
    # todo caído: no hay respuesta y queda explicado el motivo
    red.locales = False
    ia._local["t"] = 0.0
    red.falla.update({"openai.com": 401, "anthropic": 0})
    ia._pausa.clear()
    assert ia.responder(p, q, "nada") is None and ia.ultimo_error[0]


def test_si_el_modelo_deja_de_existir_busca_otro(robot, red):
    p = robot.nueva_partida()
    q, f = _vecino(p)
    p.cfg["ia_servicio"] = "anthropic"
    ia.guardar_clave("k", "anthropic")
    assert ia.responder(p, q, "hola") and ia.ultimo_uso["modelo"] == "claude-haiku-5-5"
    red.sin_modelo.add("claude-haiku-5-5")                                           # un día lo retiran
    assert ia.responder(p, q, "hola") and ia.ultimo_uso["modelo"] == "claude-haiku-4-5"
    assert ia.modelo("anthropic", p.cfg) == "claude-haiku-4-5"                       # y queda recordado el nuevo
    # un servicio que no admite algún parámetro: se repite la petición con lo mínimo
    p.cfg["ia_servicio"] = "openai"
    ia.guardar_clave("k2", "openai")
    original = red.__call__

    def quisquilloso(metodo, url, cabeceras, cuerpo=None, espera=0):
        if metodo == "POST" and "reasoning_effort" in (cuerpo or {}):
            red.pedidos.append((metodo, url, cabeceras, cuerpo))
            raise ia.ErrorIA(400, "unsupported parameter")
        return original(metodo, url, cabeceras, cuerpo, espera)
    ia._pedir = quisquilloso
    assert ia.responder(p, q, "hola")["respuesta"].startswith("Pues mira")
    assert "reasoning_effort" not in red.pedidos[-1][3]


def test_respuestas_raras_no_rompen_nada(robot, red):
    assert ia._leer('Claro: {"respuesta": "Hola *guapo*", "confianza": 99, "accion": "volar"} y ya') == {"respuesta": "Hola guapo", "confianza": 15, "accion": "nada"}
    assert ia._leer("<think>a ver</think> Buenas tardes.", con_json=False)["respuesta"] == "Buenas tardes."
    assert ia._leer('{"respuesta": "roto', con_json=True) is None and ia._leer("", con_json=False) is None
    p = robot.nueva_partida()
    q, f = _vecino(p)
    p.cfg["ia_servicio"] = "gemini"
    p.cfg["ia_activa"] = True
    ia.guardar_clave("k", "gemini")
    c0 = f["confianza"]
    assert p.responder_libre(q, "¿Qué tal el día?") == "Maite: Pues mira, hoy hace bueno."
    assert f["confianza"] == c0 + 7 and f["memoria"][-1][0] == "¿Qué tal el día?"
    p.responder_libre(q, "¿Y mañana?")
    assert len(red.pedidos[-1][3]["contents"]) == 3 and red.pedidos[-1][3]["contents"][1]["role"] == "model"      # recuerda lo hablado
    red.texto = '{"respuesta": "roto'
    assert p.responder_libre(q, "hola").startswith("Maite:")                          # contesta el motor propio
    red.falla["googleapis"] = 0
    assert p.responder_libre(q, "hola").startswith("Maite:")
    p.cfg["ia_activa"] = False


def test_menu_de_opciones_y_prueba(robot, red):
    from juego import menus_charla
    from juego.menus import Menu
    app = robot.app
    app.cfg["ia_servicio"] = "auto"
    app.cfg["ia_activa"] = False
    menus_charla.opciones_ia(app)
    m = app.pila[-1]
    assert isinstance(m, Menu) and len(m.opciones) == 14
    textos = [o.texto for o in m.opciones]
    assert "Automático" in textos[1] and "Modelo local: sin instalar" in textos[2] and "sin poner" in textos[3]
    m.opciones[0].ajuste(1)                                   # sin nada preparado, no se activa
    assert not app.cfg["ia_activa"] and "No hay ningún servicio" in robot.dicho()
    ia.guardar_clave("k-gemini", "gemini")
    m.opciones[0].ajuste(1)
    assert app.cfg["ia_activa"]
    frase = ia.probar(app.cfg)
    assert "Funciona" in frase and "Gemini" in frase and "gemini-2.5-flash-lite" in frase
    m.opciones[1].ajuste(1)
    assert app.cfg["ia_servicio"] == "local"
    app.cfg["ia_servicio"] = "auto"
    app.cfg["ia_activa"] = False


def test_las_claves_no_llegan_al_registro(red, tmp_path):
    registro.iniciar("juego", str(tmp_path), "0.0", graves=False)
    try:
        ia.guardar_clave("sk-SECRETISIMA-0123456789", "openai")
        registro.info("ia", "prueba sk-SECRETISIMA-0123456789")
        carpeta = registro.carpeta_sesion()
    finally:
        registro.cerrar()
    for base, _, archivos in os.walk(carpeta):
        for a in archivos:
            assert "SECRETISIMA" not in open(os.path.join(base, a), encoding="utf-8", errors="replace").read()


def test_solo_https_o_este_ordenador():
    for mala in ("http://ejemplo.com/v1/models", "ftp://x", "http://192.168.1.5:1234/v1/models"):
        with pytest.raises(ia.ErrorIA):
            ia.__dict__["_pedir"]("GET", mala, {})
    assert rutas.DATA in ia.carpeta_local()


# ====================================================================== modelo local: descarga, arranque y cierre
def _catalogo_de_pega(monkeypatch):
    """Un programa y un modelo diminutos, con sus huellas, y una internet que los sirve."""
    import hashlib
    import io
    import zipfile
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w") as z:
        z.writestr("llama-server.exe", b"programa de pega")
        z.writestr("llama.dll", b"biblioteca de pega")
    zip_ = mem.getvalue()
    modelo = b"pesos de pega " * 5000
    monkeypatch.setattr(ia, "PROGRAMA", {"url": "https://ejemplo.test/programa.zip", "tamano": len(zip_), "sha256": hashlib.sha256(zip_).hexdigest()})
    cat = {"ligero": {"nombre": "Ligero", "archivo": "ligero.gguf", "tamano": len(modelo), "url": "https://ejemplo.test/ligero.gguf",
                      "sha256": hashlib.sha256(modelo).hexdigest(), "desc": "De pega."},
           "mediano": {"nombre": "Mediano", "archivo": "mediano.gguf", "tamano": len(modelo), "url": "https://ejemplo.test/mediano.gguf",
                       "sha256": hashlib.sha256(modelo).hexdigest(), "desc": "De pega."}}
    monkeypatch.setattr(ia, "MODELOS_LOCALES", cat)
    pedidas = []

    def abrir(url):
        pedidas.append(url)
        return io.BytesIO(zip_ if url.endswith(".zip") else modelo)
    return abrir, pedidas, modelo


def test_descarga_del_modelo_local_comprobada(red, monkeypatch):
    abrir, pedidas, modelo = _catalogo_de_pega(monkeypatch)
    carpeta = ia.carpeta_local()
    assert not ia.local_instalado() and ia.modelo_instalado() == ""
    avances = []
    assert ia.instalar_local("ligero", progreso=lambda h, t: avances.append(h / t), abrir=abrir)
    assert ia.local_instalado() and ia.modelo_instalado() == "ligero" and avances[-1] == 1.0
    assert os.path.exists(os.path.join(carpeta, "programa", "llama-server.exe")) and not os.path.exists(os.path.join(carpeta, "programa.zip"))
    # cambiar de modelo: no vuelve a bajar el programa y quita el modelo anterior
    pedidas.clear()
    ia.instalar_local("mediano", abrir=abrir)
    assert pedidas == ["https://ejemplo.test/mediano.gguf"] and ia.modelo_instalado() == "mediano"
    assert [f for f in os.listdir(carpeta) if f.endswith(".gguf")] == ["mediano.gguf"]
    # un archivo que no es el publicado no se instala y no deja restos
    import io
    with pytest.raises(ia.ErrorIA):
        ia.instalar_local("ligero", abrir=lambda url: io.BytesIO(b"otra cosa " * 7000))
    with pytest.raises(ia.ErrorIA):
        ia.instalar_local("ligero", abrir=lambda url: io.BytesIO(modelo + b"de mas"))
    with pytest.raises(ia.Cancelado):
        ia.instalar_local("ligero", abrir=abrir, cancelado=lambda: True)
    assert sorted(os.listdir(carpeta)) == ["mediano.gguf", "programa"] and ia.modelo_instalado() == "mediano"
    with pytest.raises(ia.ErrorIA):                                   # y nunca por una dirección sin cifrar
        ia._bajar("http://ejemplo.test/x.gguf", os.path.join(carpeta, "x.gguf"), 1, "0")
    ia.quitar_local()
    assert not os.path.exists(carpeta) and not ia.local_instalado()


def test_menu_del_modelo_local(robot, red, monkeypatch):
    from juego import menus_charla
    from juego.menus import Menu
    abrir, pedidas, _ = _catalogo_de_pega(monkeypatch)
    arranques = []
    monkeypatch.setattr(ia, "arrancar_local", lambda calentar=True: arranques.append("arranca") or True)
    monkeypatch.setattr(ia, "parar_local", lambda: arranques.append("para"))
    app = robot.app
    app.ia_abrir = abrir
    app.cfg["ia_activa"] = False
    app.cfg["ia_servicio"] = "auto"
    menus_charla.local(app)
    m = app.pila[-1]
    assert isinstance(m, Menu) and [o.texto.split(":")[0] for o in m.opciones] == ["Qué es", "Descargar el modelo ligero", "Descargar el modelo mediano", "Volver"]
    m.i = 1
    robot.tecla(pygame.K_RETURN)
    robot.frames(3)
    assert ia.local_instalado() and app.cfg["ia_activa"] and arranques[-1] == "arranca" and "Modelo instalado" in robot.dicho()
    m.refrescar() if hasattr(m, "refrescar") else None
    menus_charla.local(app)
    m = app.pila[-1]
    assert "instalado" in m.opciones[1].texto and m.opciones[3].texto == "Quitar el modelo local"
    # el modelo solo está en marcha mientras se va a usar
    arranques.clear()
    app.cfg["ia_servicio"] = "openai"
    ia.ajustar_local(app.cfg)
    app.cfg["ia_servicio"] = "local"
    ia.ajustar_local(app.cfg)
    app.cfg["ia_activa"] = False
    ia.ajustar_local(app.cfg)
    assert arranques == ["para", "arranca", "para"]
    m.i = 3
    robot.tecla(pygame.K_RETURN)
    c = app.pila[-1]
    c.i = 1
    robot.tecla(pygame.K_RETURN)
    assert not ia.local_instalado() and "quitado" in robot.dicho()
    app.cfg["ia_servicio"] = "auto"


def test_el_modelo_local_muere_con_el_juego(tmp_path):
    """Aunque al juego lo maten de golpe, el programa del modelo no queda abierto: Windows lo cierra con él."""
    import subprocess
    import sys
    import time
    guion = tmp_path / "padre.py"
    guion.write_text(
        "import subprocess, sys, time\n"
        f"sys.path.insert(0, {rutas.base()!r})\n"
        "from juego import ia\n"
        "hijo = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(120)'])\n"
        "print(hijo.pid, ia._atar_al_juego(hijo), flush=True)\n"
        "time.sleep(120)\n", encoding="utf-8")
    padre = subprocess.Popen([sys.executable, str(guion)], stdout=subprocess.PIPE, text=True)
    pid, atado = padre.stdout.readline().split()
    assert atado == "True"

    def vivo(pid):
        salida = subprocess.run(["tasklist", "/fi", f"PID eq {pid}", "/fo", "csv", "/nh"], capture_output=True, text=True, encoding="mbcs", errors="replace").stdout
        return f'"{pid}"' in salida
    assert vivo(pid)
    padre.kill()                                      # como cerrarlo desde el administrador de tareas
    padre.wait(10)
    for _ in range(50):
        if not vivo(pid):
            break
        time.sleep(0.1)
    assert not vivo(pid)
