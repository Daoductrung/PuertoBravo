"""Las opciones del servidor, descritas una sola vez.

De esta descripción salen cuatro cosas, para que nunca se desajusten entre sí:

- los valores de serie con los que arranca el servidor (``valores_de_serie``);
- el ejemplo de ``servidor.conf`` y el archivo que se guarda desde el panel (``texto_conf``, ``guardar``);
- la comprobación de lo que escribe quien administra, con mensajes claros (``validar``, ``leer``);
- la interfaz del panel y el apartado de opciones de la documentación (``html_opciones``).

Solo usa la biblioteca de serie: el servidor tiene que poder funcionar con Python y nada más.
"""
import html
import os
import textwrap

TEXTO, SECRETO, ENTERO, ELECCION, SINO = "texto", "secreto", "entero", "eleccion", "sino"

SECCIONES = (
    ("general", "General", "Cómo se llama el servidor, qué se le dice a quien entra y cuánta gente cabe."),
    ("red", "Red y cifrado", "Por dónde escucha el servidor y cómo protege la conexión."),
    ("acceso", "Acceso y administración", "Quién puede entrar, quién manda y a quién no se deja pasar."),
    ("versiones", "Versiones del juego", "Qué versiones del juego pueden jugar juntas en este servidor."),
    ("datos", "Datos y copias de seguridad", "Dónde se guarda todo, cada cuánto y cuántas copias se conservan."),
    ("combate", "Combate entre jugadores", "Las reglas de las peleas, los atracos y las recompensas."),
    ("mundo", "Mundo vivo", "El tráfico, la gente de la calle, la policía y los personajes que lleva el servidor."),
    ("economia", "Economía y propiedades", "El dinero que reconoce el servidor, las casas, los negocios y los vehículos."),
    ("bandas", "Bandas y territorios", "Lo que cuesta fundar una banda, reclamar un barrio y declarar una guerra."),
    ("rol", "Rol y convivencia", "Los canales de chat para interpretar a tu personaje y lo que se oye de los demás jugadores."),
)

SI_NO = (("si", "sí"), ("no", "no"))
_VERDADERO = ("si", "sí", "1", "true", "yes", "s", "verdadero")
_FALSO = ("no", "0", "false", "n", "falso")


class Opcion:
    """Una opción: su nombre en servidor.conf, dónde va en el panel, qué es y entre qué valores puede estar."""

    __slots__ = ("clave", "seccion", "etiqueta", "ayuda", "tipo", "defecto", "minimo", "maximo", "valores", "reinicio", "largo")

    def __init__(self, clave, seccion, etiqueta, ayuda, tipo, defecto, minimo=None, maximo=None, valores=(), reinicio=False, largo=200):
        self.clave, self.seccion, self.etiqueta, self.ayuda, self.tipo, self.defecto = clave, seccion, etiqueta, ayuda, tipo, defecto
        self.minimo, self.maximo, self.valores, self.reinicio, self.largo = minimo, maximo, tuple(valores), reinicio, largo

    def permitidos(self):
        """Los valores que se pueden escribir, tal como van en el archivo."""
        if self.tipo == SINO:
            return ("si", "no")
        return tuple(v for v, _ in self.valores)

    def descripcion_valores(self):
        """En una frase, qué se puede poner. Sirve para el archivo, para la ayuda del panel y para la documentación."""
        if self.tipo == SINO:
            return "Valores: si o no."
        if self.tipo == ELECCION:
            return "Valores: " + "; ".join("%s (%s)" % (v, d) for v, d in self.valores) + "."
        if self.tipo == ENTERO:
            return "Un número entero entre %d y %d." % (self.minimo, self.maximo)
        if self.tipo == SECRETO:
            return "Un texto de hasta %d letras. Se guarda tal cual en el archivo: no lo enseñes." % self.largo
        return "Un texto de hasta %d letras." % self.largo


def _o(*a, **k):
    return Opcion(*a, **k)


OPCIONES = (
    # ------------------------------------------------------------------ general
    _o("nombre", "general", "Nombre del servidor",
       "El nombre con el que los jugadores ven tu servidor en su lista.", TEXTO, "Servidor de Puerto Bravo", largo=60),
    _o("bienvenida", "general", "Bienvenida",
       "Lo que se le dice a cada jugador nada más entrar.", TEXTO, "Bienvenido. Juega limpio.", largo=300),
    _o("mensaje_dia", "general", "Mensaje del día",
       "Un aviso que oye cada jugador al entrar, después de la bienvenida: una quedada, una norma nueva. Vacío, ninguno. "
       "Se puede cambiar con el servidor en marcha.", TEXTO, "", largo=300),
    _o("max_jugadores", "general", "Máximo de jugadores a la vez",
       "Cuántos jugadores pueden estar dentro a la vez. Con 0 no hay límite. Los administradores entran aunque esté lleno. "
       "Los personajes que lleva el servidor no cuentan.", ENTERO, 32, 0, 100000),
    _o("adultos", "general", "Contenido para adultos",
       "Con no, quien entra juega sin el contenido para adultos aunque lo tenga activado en su juego.", SINO, "no"),
    # ---------------------------------------------------------------------- red
    _o("puerto", "red", "Puerto",
       "El puerto en el que escucha el servidor. Es el que hay que abrir en el router para que entren desde fuera de casa. "
       "Con 0, el sistema elige uno libre cada vez, cosa que solo sirve para pruebas.", ENTERO, 47820, 0, 65535, reinicio=True),
    _o("interfaz", "red", "Dirección en la que escucha",
       "Con 0.0.0.0 escucha en todas las conexiones del equipo, que es lo normal. Con 127.0.0.1 solo se puede entrar desde este "
       "mismo ordenador. También vale la dirección de una sola de tus conexiones de red.", TEXTO, "0.0.0.0", reinicio=True, largo=60),
    _o("cifrado", "red", "Cifrado de la conexión",
       "Con auto, el servidor crea su propio certificado la primera vez que arranca y cifra; no hay que instalar nada.",
       ELECCION, "auto", valores=(("auto", "cifra si puede, y casi siempre puede"), ("si", "obligatorio: si no puede cifrar, no arranca"),
                                  ("no", "nunca cifra")), reinicio=True),
    _o("certificado", "red", "Archivo del certificado",
       "Solo si quieres usar un certificado tuyo: la ruta de su archivo PEM. Vacío, el servidor usa el que crea él mismo en la "
       "carpeta de datos.", TEXTO, "", reinicio=True, largo=260),
    _o("llave", "red", "Archivo de la llave del certificado",
       "La ruta del archivo PEM con la llave privada de tu certificado. Vacío si la llave va dentro del propio certificado "
       "o si usas el que crea el servidor.", TEXTO, "", reinicio=True, largo=260),
    _o("conexiones_por_ip", "red", "Conexiones a la vez desde una misma dirección",
       "Cuántas conexiones se admiten a la vez desde una misma dirección de red. Con 0 no hay límite. Ojo: quienes juegan "
       "desde la misma casa comparten dirección, y detrás de Docker o de un intermediario todos pueden parecer la misma.",
       ENTERO, 0, 0, 100000),
    _o("registro_ip", "red", "Anotar la dirección de quien se conecta",
       "Con si, el registro anota la dirección de red de cada conexión y el panel la enseña. De serie, no: el servidor "
       "no guarda ningún dato personal.", SINO, "no"),
    # ------------------------------------------------------------------- acceso
    _o("entrada", "acceso", "Quién puede crear un personaje",
       "Solo afecta a quien entra por primera vez: quien ya tiene personaje vuelve a entrar siempre.",
       ELECCION, "abierta", valores=(("abierta", "cualquiera que tenga la dirección"), ("clave", "hay que saber la contraseña de entrada"),
                                     ("invitacion", "hace falta un código de un solo uso"))),
    _o("clave", "acceso", "Contraseña de entrada",
       "La contraseña que hay que saber para crear un personaje cuando la entrada es con clave.", SECRETO, "", largo=60),
    _o("admins", "acceso", "Administradores",
       "Nombres de jugador que administran el servidor, separados por comas. Se suman a los que se nombran con la orden admin.",
       TEXTO, "", largo=600),
    _o("primer_admin", "acceso", "La primera cuenta es administradora",
       "Con si, la primera cuenta que se crea en el servidor es administradora: lo normal es que seas tú.", SINO, "si"),
    _o("vetados", "acceso", "Nombres vetados",
       "Nombres de jugador que no pueden entrar, separados por comas. Se suman a las cuentas vetadas con la orden vetar.",
       TEXTO, "", largo=600),
    _o("inactividad_minutos", "acceso", "Expulsar por inactividad, en minutos",
       "Minutos sin moverse ni hacer nada tras los que se saca a un jugador, para dejar sitio. Con 0, nunca. "
       "A los administradores no se les saca.", ENTERO, 0, 0, 1440),
    _o("varias_sesiones", "acceso", "Permitir dos sesiones con la misma identidad",
       "Solo para pruebas. De serie, no: si alguien entra con su personaje desde otro sitio, la sesión anterior se cierra.", SINO, "no"),
    # ---------------------------------------------------------------- versiones
    _o("comprobar_datos", "versiones", "Comprobar los datos del juego de quien entra",
       "Con si, el servidor comprueba que el mundo que trae el juego de quien entra es de una versión de verdad y sin mods "
       "que lo cambien. Con no, entra cualquiera con lo que traiga.", SINO, "si"),
    _o("versiones", "versiones", "Versiones que pueden jugar juntas",
       "El servidor trabaja con el mundo de la versión más nueva que ha visto.",
       ELECCION, "compatibles", valores=(("compatibles", "pueden jugar juntos quienes tengan versiones distintas del juego, cada uno "
                                                         "con lo que su versión conoce"),
                                         ("iguales", "solo entra quien tenga exactamente los mismos datos que el servidor"))),
    _o("version_minima", "versiones", "Versión mínima del juego",
       "La versión más antigua del juego con la que se puede entrar, por ejemplo 1.7.0. Vacío, cualquiera.", TEXTO, "", largo=20),
    _o("actualizar_mundo", "versiones", "Quién puede traer un mundo nuevo",
       "El mundo del juego (lugares, armas, misiones) no va atado al servidor: se lo trae el juego de quien entra.",
       ELECCION, "firmado", valores=(("firmado", "el de una versión más nueva se acepta de cualquiera si lo firma quien publica el juego"),
                                     ("admin", "además, sin firma, de un administrador: para servidores con mods"),
                                     ("no", "nunca: el servidor se queda con el mundo que tiene"))),
    # -------------------------------------------------------------------- datos
    _o("datos", "datos", "Carpeta de datos",
       "La carpeta donde se guarda todo: personajes, bandas, territorios, vehículos, el certificado y las copias de seguridad.",
       TEXTO, "datos_servidor", reinicio=True, largo=260),
    _o("guardado_minutos", "datos", "Guardar cada tantos minutos",
       "Cada cuántos minutos se guarda todo en disco. Al parar el servidor se guarda siempre.", ENTERO, 1, 1, 120),
    _o("copia_auto_horas", "datos", "Copia de seguridad automática, cada tantas horas",
       "Cada cuántas horas hace el servidor una copia de seguridad en la carpeta copias, dentro de la de datos. Con 0, no hace ninguna.",
       ENTERO, 24, 0, 720),
    _o("copias_guardar", "datos", "Copias de seguridad que se conservan",
       "Cuántas copias automáticas se conservan: al hacer una nueva se borran las más antiguas. Las que haces tú a mano con "
       "otro nombre no se tocan.", ENTERO, 7, 1, 365),
    _o("registro_archivo", "datos", "Guardar el registro en un archivo",
       "Con si, lo que va diciendo el servidor se escribe también en registro.txt, dentro de la carpeta de datos.", SINO, "no"),
    # ------------------------------------------------------------------ combate
    _o("pvp", "combate", "Combate entre jugadores",
       "Con no, los jugadores no pueden herirse, atracarse ni robarse entre sí.", SINO, "si"),
    _o("zonas_seguras", "combate", "Zonas seguras",
       "Con si, en hospitales, comisarías, casas y dentro de los locales nadie puede herir a nadie.", SINO, "si"),
    _o("modo_pasivo", "combate", "Permitir el modo pasivo",
       "Con si, cada jugador puede ponerse en modo pasivo: ni hiere a otros jugadores ni le hieren.", SINO, "si"),
    _o("proteccion", "combate", "Segundos de protección al llegar",
       "Segundos sin poder herir ni ser herido al entrar y al reaparecer.", ENTERO, 20, 0, 600),
    _o("botin", "combate", "Botín al tumbar a otro jugador, en tanto por ciento",
       "El tanto por ciento del dinero de bolsillo que pierde quien cae ante otro jugador.", ENTERO, 10, 0, 100),
    _o("botin_max", "combate", "Botín máximo",
       "Lo más que se puede perder al caer ante otro jugador, en euros.", ENTERO, 5000, 0, 100000000),
    _o("atraco", "combate", "Atraco a otro jugador, en tanto por ciento",
       "El tanto por ciento del dinero de bolsillo que se lleva quien atraca a otro jugador.", ENTERO, 15, 0, 100),
    _o("atraco_max", "combate", "Atraco máximo",
       "Lo más que se puede quitar en un atraco a otro jugador, en euros.", ENTERO, 1000, 0, 100000000),
    _o("robo_segundos", "combate", "Segundos para atracar un negocio",
       "Los segundos que hay que aguantar en la puerta para vaciar la caja del negocio de otro jugador. Al dueño le salta el aviso.",
       ENTERO, 20, 1, 600),
    _o("recompensa", "combate", "Recompensa por tumbar a un inocente",
       "Lo que sube, en euros, la recompensa por la cabeza de quien tumba a quien no se defendía.", ENTERO, 500, 0, 100000000),
    # -------------------------------------------------------------------- mundo
    _o("trafico", "mundo", "Tráfico común",
       "Con si, los coches que circulan los lleva el servidor y son los mismos para todos. Con no, cada jugador ve su propio tráfico.",
       SINO, "si"),
    _o("trafico_max", "mundo", "Coches por zona con jugadores",
       "Cuántos coches lleva el servidor, como mucho, por cada zona de una localidad en la que hay jugadores. Para unos amigos "
       "que van juntos es el total de coches de la localidad.", ENTERO, 8, 0, 200),
    _o("trafico_total", "mundo", "Coches por localidad, como mucho",
       "El tope de coches en una misma localidad cuando hay jugadores repartidos por muchas zonas. Con 0 no hay tope.",
       ENTERO, 60, 0, 5000),
    _o("patrullas", "mundo", "Coches patrulla por localidad",
       "Coches patrulla del servidor que rondan por cada localidad con jugadores. Con 0, ninguno.", ENTERO, 1, 0, 50),
    _o("policia", "mundo", "Policía común",
       "Con si, la búsqueda, la persecución y la detención las lleva el servidor, y las ve y las oye todo el que esté cerca. "
       "Con no, las lleva el juego de cada jugador.", SINO, "si"),
    _o("peatones", "mundo", "Gente de la calle común",
       "Con si, los peatones los lleva el servidor y son los mismos para todos.", SINO, "si"),
    _o("peatones_max", "mundo", "Peatones por zona con jugadores",
       "Cuántos peatones lleva el servidor, como mucho, por cada zona de una localidad en la que hay jugadores.", ENTERO, 10, 0, 200),
    _o("peatones_total", "mundo", "Peatones por localidad, como mucho",
       "El tope de peatones en una misma localidad cuando hay jugadores repartidos por muchas zonas. Con 0 no hay tope.",
       ENTERO, 80, 0, 5000),
    _o("personajes", "mundo", "Personajes que lleva el servidor",
       "Paseantes, rateros, pistoleros, ladrones de coches y atracadores que lleva el servidor y son los mismos para todos. "
       "Salen solo donde hay jugadores. Con 0, ninguno.", ENTERO, 6, 0, 200),
    _o("radio_detalle", "mundo", "Metros a los que se sigue a los demás al detalle",
       "A cada jugador se le cuenta diez veces por segundo dónde están los que tiene a menos de esta distancia, y una vez por "
       "segundo por dónde andan los demás de su localidad. Es lo que más red y procesador ahorra en servidores con mucha gente. "
       "Con 0, a todos al detalle y siempre, que solo conviene con poca gente.",
       ENTERO, 150, 0, 100000),
    # ----------------------------------------------------------------- economía
    _o("economia", "economia", "El servidor lleva la cuenta del dinero",
       "Con si, el servidor lleva la cuenta del dinero de cada jugador y no da por bueno lo que no puede justificar.", SINO, "si"),
    _o("ganancia_hora", "economia", "Ganancia máxima por hora",
       "Lo más que se puede ganar en una hora de reloj con trabajos, ventas, juego y botín de la calle, en euros. Lo que da el "
       "propio servidor no cuenta.", ENTERO, 30000, 0, 1000000000),
    _o("ganancia_acumula", "economia", "Horas de ganancia que se pueden acumular",
       "La ganancia por hora que un jugador no usa no se pierde: se le guarda hasta este número de horas, también mientras está "
       "fuera, para que una buena racha quepa entera. Con 1, nunca tiene más margen que el de una hora.", ENTERO, 3, 1, 48),
    _o("encargos_hora", "economia", "Encargos repetibles reconocidos por hora, de cada tipo",
       "Los contratos, los combates del gimnasio, los atracos y los encargos de coches que se cumplen de verdad no gastan la "
       "ganancia por hora: el servidor los da por buenos, hasta este número por hora de cada tipo. Con 0 no reconoce ninguno "
       "y todos cuentan contra la ganancia por hora.", ENTERO, 6, 0, 1000),
    _o("encargo_max", "economia", "Paga máxima reconocida por un encargo repetible",
       "Lo más que se da por bueno de la paga de un solo encargo repetible, en euros. Lo que pase de ahí cuenta contra la "
       "ganancia por hora.", ENTERO, 15000, 0, 1000000000),
    _o("saldo_inicial", "economia", "Dinero inicial máximo",
       "Lo más con que puede empezar un personaje nuevo, en euros.", ENTERO, 5000, 0, 1000000000),
    _o("venta_mercado", "economia", "Venta al mercado, en tanto por ciento",
       "El tanto por ciento del precio que recupera quien vende su casa o su negocio al mercado.", ENTERO, 70, 0, 100),
    _o("propiedad_dias", "economia", "Días sin entrar para perder las propiedades",
       "Días de verdad sin entrar tras los que las propiedades de un jugador vuelven al mercado. Se le guarda su parte.",
       ENTERO, 30, 1, 3650),
    _o("vehiculos_horas", "economia", "Horas que dura un vehículo en la calle",
       "Horas de verdad que un vehículo dejado en la calle sigue ahí.", ENTERO, 12, 1, 8760),
    _o("vehiculos_por_jugador", "economia", "Vehículos aparcados por jugador",
       "Cuántos vehículos puede tener aparcados en la calle cada jugador. Al dejar uno más, desaparece el más antiguo.",
       ENTERO, 3, 1, 100),
    # ------------------------------------------------------------------- bandas
    _o("precio_banda", "bandas", "Precio de fundar una banda", "En euros.", ENTERO, 2000, 0, 1000000000),
    _o("precio_barrio", "bandas", "Precio de reclamar un barrio", "En euros, de la caja de la banda.", ENTERO, 3000, 0, 1000000000),
    _o("renta_barrio", "bandas", "Renta diaria de cada barrio",
       "Lo que deja cada barrio en la caja de la banda a medianoche, en euros.", ENTERO, 300, 0, 1000000000),
    _o("precio_guerra", "bandas", "Precio de declarar una guerra", "En euros, de la caja de la banda.", ENTERO, 1000, 0, 1000000000),
    _o("guerra_espera", "bandas", "Minutos hasta que empieza una guerra",
       "Minutos de verdad entre declarar una guerra y que empiece.", ENTERO, 20, 1, 10080),
    _o("guerra_dura", "bandas", "Minutos que dura una guerra", "Minutos de verdad.", ENTERO, 10, 1, 1440),
    # ---------------------------------------------------------------------- rol
    _o("rol", "rol", "Canales de rol",
       "Con si, los jugadores tienen un canal para hablar en personaje, que solo oye quien está cerca, otro para hablar fuera de "
       "personaje, que oye todo el servidor, una orden para describir lo que hace su personaje y una frase de ficha que los demás "
       "pueden leer. Con no, solo queda el chat de siempre.", SINO, "si"),
    _o("rol_metros", "rol", "Metros a los que llega lo dicho en personaje",
       "A qué distancia se oye lo que un jugador dice en personaje y las acciones que describe. Lo dicho fuera de personaje "
       "llega siempre a todo el servidor.", ENTERO, 30, 5, 2000),
    _o("radio_coches", "rol", "Radio de los coches de otros jugadores",
       "Con si, quien está cerca del vehículo de otro jugador oye, floja, la emisora del juego que lleva puesta. Solo se cuenta "
       "qué emisora del juego es: nunca viaja música ni nada personal. Con no, no se oye la radio de nadie.", SINO, "si"),
)

POR_CLAVE = {o.clave: o for o in OPCIONES}
assert len(POR_CLAVE) == len(OPCIONES), "hay una opción repetida"


def valores_de_serie():
    return {o.clave: o.defecto for o in OPCIONES}


def de_seccion(seccion):
    return [o for o in OPCIONES if o.seccion == seccion]


def _version_valida(t):
    partes = t.split(".")
    return 1 <= len(partes) <= 4 and all(p.isdigit() and len(p) <= 5 for p in partes)


def validar_valor(clave, valor):
    """Comprueba un valor. Devuelve (valor ya en su forma, None) o (None, por qué no vale)."""
    o = POR_CLAVE.get(clave)
    if o is None:
        return None, "no existe ninguna opción con ese nombre"
    if o.tipo == ENTERO:
        try:
            n = int(str(valor).strip()) if not isinstance(valor, bool) else int(valor)
        except (TypeError, ValueError):
            return None, "tiene que ser un número entero entre %d y %d" % (o.minimo, o.maximo)
        if not o.minimo <= n <= o.maximo:
            return None, "tiene que estar entre %d y %d" % (o.minimo, o.maximo)
        return n, None
    if isinstance(valor, bool):
        valor = "si" if valor else "no"
    texto = str(valor if valor is not None else "").strip()
    if o.tipo == SINO:
        bajo = texto.lower()
        if bajo in _VERDADERO:
            return "si", None
        if bajo in _FALSO:
            return "no", None
        return None, "tiene que ser si o no"
    if o.tipo == ELECCION:
        bajo = texto.lower().replace("ó", "o").replace("í", "i")
        if bajo in o.permitidos():
            return bajo, None
        return None, "tiene que ser uno de estos valores: " + ", ".join(o.permitidos())
    if "\n" in texto or "\r" in texto:
        return None, "no puede tener saltos de línea"
    if len(texto) > o.largo:
        return None, "no puede tener más de %d letras" % o.largo
    if clave == "nombre" and len(texto) < 2:
        return None, "tiene que tener al menos dos letras"
    if clave == "datos" and not texto:
        return None, "no puede quedar vacía"
    if clave == "version_minima" and texto and not _version_valida(texto):
        return None, "tiene que ser un número de versión, como 1.7.0, o quedar vacía"
    return texto, None


def validar(cfg, completar=True):
    """Comprueba un juego de opciones. Devuelve (opciones ya en su forma, lista de problemas).

    Lo que no vale se sustituye por su valor de serie y se cuenta en la lista. Lo que no se conoce se deja fuera."""
    limpio = valores_de_serie() if completar else {}
    problemas = []
    for clave, valor in (cfg or {}).items():
        o = POR_CLAVE.get(clave)
        if o is None:
            problemas.append("%s: no existe ninguna opción con ese nombre; no se le hace caso." % clave)
            continue
        v, error = validar_valor(clave, valor)
        if error:
            problemas.append("%s (%s): %s. Se usa el valor de serie, %s." % (o.etiqueta, clave, error, o.defecto if o.defecto != "" else "vacío"))
            limpio[clave] = o.defecto
        else:
            limpio[clave] = v
    final = dict(valores_de_serie(), **limpio)
    if final.get("entrada") == "clave" and not final.get("clave"):
        problemas.append("La entrada es con clave pero la contraseña de entrada está vacía: no podrá crear personaje nadie nuevo.")
    if final.get("cifrado") == "si" and bool(final.get("llave")) and not final.get("certificado"):
        problemas.append("Has puesto la llave de un certificado pero no el certificado.")
    return limpio, problemas


def leer(ruta):
    """Lee un servidor.conf. Devuelve (opciones, avisos). Si el archivo no existe, las de serie y ningún aviso.

    Una opción por línea: nombre = valor. Las líneas que empiezan por almohadilla son comentarios."""
    crudo, avisos = {}, []
    if ruta and os.path.exists(ruta):
        with open(ruta, encoding="utf-8-sig") as f:
            for n, linea in enumerate(f, 1):
                linea = linea.strip()
                if not linea or linea.startswith("#"):
                    continue
                if "=" not in linea:
                    avisos.append("Línea %d: no la entiendo, le falta el signo igual. No se le hace caso." % n)
                    continue
                k, v = linea.split("=", 1)
                k = k.strip().lower()
                if k not in POR_CLAVE:
                    avisos.append("Línea %d: no existe la opción %s. No se le hace caso; puede ser de otra versión del servidor." % (n, k))
                    continue
                crudo[k] = v.strip()
    limpio, problemas = validar(crudo)
    return limpio, avisos + problemas


def _comentario(texto, ancho=110):
    return "\n".join("# " + l for l in textwrap.wrap(texto, ancho - 2)) if texto else ""


def texto_conf(cfg=None):
    """El texto de un servidor.conf completo y comentado, con estos valores o con los de serie."""
    valores = dict(valores_de_serie(), **(cfg or {}))
    out = ["# Servidor en línea de Puerto Bravo: Ley del Asfalto",
           "# Una opción por línea: nombre = valor. Las líneas que empiezan por almohadilla no cuentan.",
           "# Este archivo se puede cambiar con un editor de texto o desde el panel del servidor, en Configuración.",
           "# Las opciones marcadas con «necesita reiniciar» solo se aplican al parar y volver a arrancar el servidor.", ""]
    for ident, titulo, que in SECCIONES:
        out += ["# " + "=" * 76, "# " + titulo.upper(), _comentario(que), "# " + "=" * 76, ""]
        for o in de_seccion(ident):
            out.append(_comentario("%s. %s" % (o.etiqueta, o.ayuda)))
            if o.tipo == ELECCION:
                out += ["\n".join(textwrap.wrap("%s: %s." % (v, d), 108, initial_indent="#   ", subsequent_indent="#     ")) for v, d in o.valores]
            else:
                out.append(_comentario(o.descripcion_valores()))
            serie = "De serie: %s." % (o.defecto if o.defecto != "" else "vacío")
            out.append("# " + serie + (" Necesita reiniciar." if o.reinicio else ""))
            out += [("%s = %s" % (o.clave, valores.get(o.clave, o.defecto))).rstrip(), ""]
    return "\n".join(out)


def guardar(ruta, cfg):
    """Escribe servidor.conf, comentado, sin dejarlo a medias si algo falla. Devuelve los problemas que tenía lo pedido."""
    limpio, problemas = validar(cfg)
    carpeta = os.path.dirname(os.path.abspath(ruta))
    os.makedirs(carpeta, exist_ok=True)
    temporal = ruta + ".nuevo"
    with open(temporal, "w", encoding="utf-8", newline="\n") as f:
        f.write(texto_conf(limpio))
    os.replace(temporal, ruta)
    return problemas


def cambios(antes, despues):
    """Las opciones que cambian entre dos juegos de valores: (las que se aplican al momento, las que piden reiniciar)."""
    al_momento, con_reinicio = [], []
    for o in OPCIONES:
        if str(antes.get(o.clave, o.defecto)) != str(despues.get(o.clave, o.defecto)):
            (con_reinicio if o.reinicio else al_momento).append(o.clave)
    return al_momento, con_reinicio


def html_opciones(nivel=3):
    """El apartado de opciones de la guía, en HTML limpio: un encabezado por grupo y otro por opción."""
    e = html.escape
    out = []
    for ident, titulo, que in SECCIONES:
        out.append("<h%d>%s</h%d>" % (nivel, e(titulo), nivel))
        out.append("<p>%s</p>" % e(que))
        for o in de_seccion(ident):
            out.append("<h%d>%s: <code>%s</code></h%d>" % (nivel + 1, e(o.etiqueta), e(o.clave), nivel + 1))
            out.append("<p>%s</p>" % e(o.ayuda))
            out.append("<ul>")
            if o.tipo == ELECCION:
                out.append("<li>Valores:<ul>")
                out += ["<li><code>%s</code>: %s.</li>" % (e(v), e(d)) for v, d in o.valores]
                out.append("</ul></li>")
            else:
                out.append("<li>%s</li>" % e(o.descripcion_valores()))
            out.append("<li>De serie: %s.</li>" % (("<code>%s</code>" % e(str(o.defecto))) if o.defecto != "" else "vacío"))
            out.append("<li>%s</li>" % ("Necesita reiniciar el servidor." if o.reinicio else "Se aplica sin reiniciar el servidor."))
            out.append("</ul>")
    return "\n".join(out)
