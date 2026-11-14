"""Modo IA: las personas de la calle contestan con Claude a lo que escribas.

Es opcional y viene apagado. Para que funcione hacen falta tres cosas:

1. El paquete «anthropic» instalado (viene en requirements.txt y en el juego compilado).
2. Una credencial de la API de Anthropic: la variable de entorno ANTHROPIC_API_KEY, un perfil de
   «ant auth login», o una clave escrita en el juego (Opciones, Personas e inteligencia artificial),
   que se guarda cifrada en data/config.
3. Activarlo en Opciones.

Cada frase que escribas a una persona se envía a la API de Anthropic junto con la ficha de esa persona y
un resumen de la situación. El uso de la API tiene coste, que paga el dueño de la clave. Sin modo IA,
el juego usa su motor de conversación propio, sin conexión.

Las respuestas son siempre aptas para leerse en voz alta: sin contenido sexual explícito, y con
personajes adultos.
"""
import json
import os
import threading

from . import cifrado, rutas

MODELO = "claude-opus-5-5"
ESQUEMA = {
    "type": "object",
    "properties": {
        "respuesta": {"type": "string", "description": "Lo que dice el personaje, en español de España, una o dos frases, sin acotaciones."},
        "confianza": {"type": "integer", "description": "Cuánto cambia la confianza del personaje hacia el jugador, de -15 a 15."},
        "accion": {"type": "string", "enum": ["nada", "se_va", "se_enfada"]},
    },
    "required": ["respuesta", "confianza", "accion"],
    "additionalProperties": False,
}
SISTEMA = """Eres un personaje secundario de un audiojuego de mundo abierto ambientado en una ciudad costera española ficticia llamada Puerto Bravo. El juego lo usan personas ciegas y todo lo que escribas se leerá en voz alta con un lector de pantalla.

Interpretas a una única persona de la calle, cuya ficha recibirás. Contesta siempre como esa persona, en español de España, con naturalidad y de forma breve: una o dos frases, sin acotaciones entre asteriscos ni paréntesis, sin emojis y sin listas.

Mantén el carácter de la ficha: «amable» es cordial, «hablador» se enrolla, «seco» responde con pocas palabras, «timido» duda y se corta, «chulo» presume y no se achanta. La confianza va de -100 a 100: con poca confianza eres reservado; con mucha, cercano.

Eres una persona corriente: no sabes nada de misiones ni de mecánicas de juego, no puedes dar dinero ni objetos y no conoces datos que no estén en la ficha o en la situación. Si te preguntan algo que no sabrías, dilo como lo diría cualquiera.

Todos los personajes son adultos. Puedes coquetear o rechazar un coqueteo según la ficha, siempre con buen gusto: nunca escribas contenido sexual explícito. Si el jugador insiste, es grosero o amenaza, reacciona como lo haría esa persona: corta la conversación (accion «se_va») o enfádate (accion «se_enfada»).

Devuelve cuánto cambia tu confianza hacia el jugador con lo que te ha dicho, entre -15 y 15."""

_cliente = None
_lock = threading.Lock()


def _ruta_clave():
    return os.path.join(rutas.carpeta_data("config"), "ia.pbc")


def clave_guardada():
    try:
        return str(cifrado.leer_json(_ruta_clave()).get("clave", ""))
    except (OSError, ValueError):
        return ""


def guardar_clave(clave):
    """Guarda (cifrada) la clave que el jugador escribe en el juego. Con una cadena vacía, la borra."""
    global _cliente
    _cliente = None
    ruta = _ruta_clave()
    if clave.strip():
        cifrado.escribir_json(ruta, {"clave": clave.strip()}, cifrado=True)
    elif os.path.exists(ruta):
        os.remove(ruta)


def instalado():
    try:
        import anthropic  # noqa: F401
        return True
    except Exception:
        return False


def disponible():
    """¿Se puede usar el modo IA? Hace falta el paquete y alguna credencial."""
    if not instalado():
        return False
    return bool(clave_guardada() or os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_PROFILE")
                or os.path.isdir(os.path.join(os.path.expanduser("~"), ".config", "anthropic")))


def por_que_no():
    if not instalado():
        return "Esta copia del juego no incluye el componente de inteligencia artificial, así que el modo IA no se puede activar. Todo lo demás funciona igual."
    return "Falta una clave de la API de Anthropic. Escríbela en esta misma sección, o define la variable de entorno ANTHROPIC_API_KEY."


def cliente():
    global _cliente
    with _lock:
        if _cliente is None:
            import anthropic
            clave = clave_guardada()
            _cliente = anthropic.Anthropic(api_key=clave, timeout=25.0, max_retries=1) if clave else anthropic.Anthropic(timeout=25.0, max_retries=1)
        return _cliente


def _situacion(p, q, f):
    x, y = p.pos()
    barrio = p.mundo.barrio(x, y)
    j = p.j
    return {"lugar": f"{barrio['nombre']}, {p.mundo.nombre}", "hora": p.hora_txt(), "llueve": bool(p.lluvia),
            "jugador": {"nombre": j.nombre, "fama_en_la_calle": p.reputacion_txt(), "entre_los_vecinos": p.ciudadania_txt(), "le_busca_la_policia": bool(j.estrellas),
                        "lleva_un_arma_en_la_mano": p.arma()["id"] != "punos"},
            "personaje": {k: f[k] for k in ("nombre", "genero", "edad", "oficio", "caracter", "confianza")}}


def responder(p, q, texto, cliente_=None):
    """Pide a Claude la respuesta del personaje. Devuelve un dict con respuesta, confianza y accion, o None si falla."""
    from .charla import ficha
    f = ficha(q)
    mensajes = []
    for dicho, contestado in f.get("memoria", []):
        mensajes.append({"role": "user", "content": dicho})
        mensajes.append({"role": "assistant", "content": json.dumps({"respuesta": contestado, "confianza": 0, "accion": "nada"}, ensure_ascii=False)})
    mensajes.append({"role": "user", "content": f"Situación: {json.dumps(_situacion(p, q, f), ensure_ascii=False)}\n\nEl jugador te dice: {texto[:400]}"})
    try:
        c = cliente_ or cliente()
        r = c.beta.messages.create(
            model=MODELO,
            max_tokens=2000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            system=[{"type": "text", "text": SISTEMA, "cache_control": {"type": "ephemeral"}}],
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": ESQUEMA}},
            messages=mensajes,
        )
        if r.stop_reason == "refusal":
            return {"respuesta": "De eso prefiero no hablar.", "confianza": -3, "accion": "nada"}
        bruto = next((b.text for b in r.content if b.type == "text"), "")
        datos = json.loads(bruto)
        respuesta = " ".join(str(datos.get("respuesta", "")).split())[:400]
        if not respuesta:
            return None
        accion = datos.get("accion") if datos.get("accion") in ("nada", "se_va", "se_enfada") else "nada"
        return {"respuesta": respuesta, "confianza": int(datos.get("confianza", 0)), "accion": accion}
    except Exception as e:
        ultimo_error[0] = _explicar(e)
        return None


ultimo_error = [""]


def _explicar(e):
    """Mensaje para el jugador a partir del error de la API, del más concreto al más general."""
    try:
        import anthropic
    except Exception:
        return "No se pudo usar el modo IA."
    if isinstance(e, anthropic.AuthenticationError):
        return "La clave de la API no es válida."
    if isinstance(e, anthropic.PermissionDeniedError):
        return "La clave de la API no tiene permiso para este modelo."
    if isinstance(e, anthropic.RateLimitError):
        return "La API está saturada o has llegado a tu límite. Prueba dentro de un momento."
    if isinstance(e, anthropic.APIStatusError):
        return f"La API ha devuelto un error {e.status_code}."
    if isinstance(e, anthropic.APIConnectionError):
        return "No hay conexión con la API. Comprueba internet y que ningún filtro de red la bloquee."
    return "La respuesta de la IA no se pudo leer."
