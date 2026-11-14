"""Menú de conversación con una persona de la calle, conocidos y opciones del modo IA."""
from .charla import SITIOS, ficha
from .menus import EntradaTexto, Menu, Opcion


def conversar(p, q):
    app = p.app
    f = ficha(q)
    primera = not f["presentado"]
    intro = p.presentacion(q)

    def decir(intencion, dato=None):
        def hacer():
            texto = p.responder(q, intencion, dato)
            app.decir(texto, True)
            if q.estado in ("huye", "ataca") or q.hostil:
                app.cerrar(menu)
        return hacer

    def sitios():
        ops = [Opcion(f"Dónde puedo {c}" if c in ("comer", "curarme", "dormir", "comprar") else f"Dónde hay {c}" if c != "policía" else "Dónde está la policía",
                      (lambda c=c: (app.cerrar(m), app.decir(p.responder(q, "sitio", c), True)))) for c in SITIOS]
        m = Menu(app, "Preguntar por un sitio", ops + [Opcion("Volver", lambda: app.cerrar(m))])
        app.abrir(m)

    def libre():
        def hecho(texto):
            if not texto.strip():
                return
            if p.ia_disponible():
                app.decir("Espera un momento.", True)
            r = p.responder_libre(q, texto)
            app.decir(r, True)
            if q.estado in ("huye", "ataca") or q.hostil or q not in p.personas:
                app.cerrar(menu)
        app.abrir(EntradaTexto(app, f"Qué le dices a {f['nombre']}", hecho, maximo=200,
                               ayuda="Escribe con tus palabras: saludar, preguntar por un sitio, contar algo, hacer un cumplido. " +
                                     ("Con el modo IA, contesta con libertad." if p.ia_disponible() else "El juego entiende la intención de lo que escribes.")))

    def ligar():
        app.decir(p.ligar(q), True)

    def proponer(hotel):
        def hacer():
            if not p.proponer_aventura(q, en_hotel=hotel):
                if q.estado == "huye":
                    app.cerrar(menu)
        return hacer

    def ops():
        lista = [Opcion(lambda: f"{f['nombre']}, {f['edad']} años, {f['oficio']}. {p.confianza_txt(f).capitalize()}"),
                 Opcion("Saludar", decir("saludar")), Opcion("Preguntar por el barrio", decir("barrio")),
                 Opcion("Preguntar qué se cuenta", decir("rumor"), ayuda="Lo que te diga sale de lo que de verdad está pasando en tu partida."),
                 Opcion("Preguntar por un sitio", sitios, ayuda="Te dice dónde está lo más cercano y te lo marca en el GPS."),
                 Opcion("Preguntar a qué se dedica", decir("trabajo_npc")),
                 Opcion("Hacer un cumplido", decir("cumplido")), Opcion("Contar un chiste", decir("chiste")),
                 Opcion("Invitar a un café: 4 euros", decir("invitar"), ayuda="Sube mucho la confianza. Una vez por persona."),
                 Opcion("Darle 10 euros", decir("limosna"), ayuda="Sube la confianza y, la primera vez, tu prestigio entre los vecinos."),
                 Opcion("Pedirle el número y ser amigos", decir("amistad"), ayuda="Hace falta que le caigas bien. Tus conocidos están en el móvil y te cuentan cosas."),
                 Opcion("Escribir lo que quieras decirle", libre, ayuda="Con el modo IA activado en Opciones, la persona contesta con total libertad a lo que escribas.")]
        if p.modo_adulto():
            lista.append(Opcion("Coquetear", ligar, ayuda="Puede salir bien o mal, según la confianza, tu ánimo y lo que busque la otra persona. Un no es un no."))
            if p.puede_proponer(q):
                lista.append(Opcion("Proponerle ir a tu casa", proponer(False), ayuda="Si no tienes casa en esta localidad, vais a un hotel por 70 euros."))
                lista.append(Opcion("Proponerle ir a un hotel: 70 euros", proponer(True)))
        lista += [Opcion("Insultar", decir("insultar"), ayuda="Puede marcharse, o plantarte cara. Baja tu prestigio."),
                  Opcion("Amenazar para que te dé dinero", decir("amenazar"), ayuda="Es un delito. Puede darte lo que lleve, o gritar pidiendo ayuda."),
                  Opcion("Despedirte", lambda: (app.decir(p.responder(q, "despedir"), True), app.cerrar(menu)))]
        return lista
    menu = Menu(app, f"Hablas con {f['nombre']}", ops, intro=intro if primera else None)
    app.abrir(menu)


def conocidos(p):
    app = p.app
    j = p.j

    def ops():
        lista = [Opcion(f"{k['nombre']}, {k['oficio']}, de {p.mapas[k['mapa']].nombre if k['mapa'] in p.mapas else 'por ahí'}. Os conocisteis el día {k['dia']}",
                        (lambda k=k: app.decir(p.llamar_conocido(k), True)), ayuda="Intro para llamar. Cada día te cuenta una cosa.") for k in reversed(j.conocidos)]
        if not lista:
            lista = [Opcion("Aún no tienes conocidos. Habla con la gente de la calle con la tecla J y, cuando le caigas bien a alguien, pídele el número")]
        return lista + [Opcion("Volver", lambda: app.cerrar(m))]
    m = Menu(app, "Tus conocidos", ops)
    app.abrir(m)


def opciones_ia(app):
    from . import ia
    cfg = app.cfg

    def alternar(d):
        if not cfg["ia_activa"] and not ia.disponible():
            app.son("error")
            app.decir(ia.por_que_no(), True)
            return
        cfg["ia_activa"] = not cfg["ia_activa"]

    def clave():
        def hecho(t):
            ia.guardar_clave(t)
            app.decir("Clave guardada, cifrada, en la carpeta de configuración." if t.strip() else "Clave borrada.", True)
        app.abrir(EntradaTexto(app, "Clave de la API de Anthropic. Déjala vacía para borrarla", hecho, secreto=True, maximo=200,
                               ayuda="La clave la consigues en la consola de Anthropic. Se guarda cifrada en tu ordenador y solo se usa para hablar con los personajes. Puedes pegarla con Control V."))

    def estado():
        if not ia.instalado():
            return "Falta el componente de inteligencia artificial: en esta copia del juego el modo IA no se puede usar"
        return "Hay una clave guardada en el juego" if ia.clave_guardada() else "No hay clave guardada en el juego. También vale la variable de entorno ANTHROPIC_API_KEY"

    m = Menu(app, "Personas e inteligencia artificial", [
        Opcion(lambda: f"Modo IA al hablar con la gente: {'sí' if cfg['ia_activa'] else 'no'}", ajuste=alternar,
               ayuda="Con el modo IA, cuando escribes lo que quieres decirle a alguien con la tecla J, contesta una inteligencia artificial, Claude, interpretando a esa persona. "
                     "Cada frase se envía a la API de Anthropic y tiene un coste que paga el dueño de la clave. Sin modo IA, el juego usa su propio motor de conversación, sin conexión."),
        Opcion(estado, clave, ayuda="Intro para escribir o borrar la clave."),
        Opcion("Qué se envía", accion=lambda: app.decir("Se envía lo que escribes, la ficha de la persona con la que hablas, la hora, el barrio y si llueve, y cómo te ven los vecinos. "
                                                        "No se envían tu partida, tus archivos ni ningún dato tuyo.", True)),
        Opcion("Volver", lambda: app.cerrar(m)),
    ], al_cerrar=cfg.guardar)
    app.abrir(m)
