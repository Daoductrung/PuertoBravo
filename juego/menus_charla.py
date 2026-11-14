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
    from .config import OPCIONES
    cfg = app.cfg

    def alternar(d):
        if not cfg["ia_activa"] and not ia.disponible(cfg):
            app.son("error")
            app.decir(ia.por_que_no(cfg), True)
            return
        cfg["ia_activa"] = not cfg["ia_activa"]
        ia.ajustar_local(cfg)                 # el modelo local solo está en marcha mientras se va a usar

    def servicio(d):
        ops = OPCIONES["ia_servicio"]
        cfg["ia_servicio"] = ops[(ops.index(cfg["ia_servicio"]) + (d or 1)) % len(ops)]
        ia.ajustar_local(cfg)

    def pedir_clave(s):
        def abrir():
            def hecho(t):
                ia.guardar_clave(t, s)
                app.decir("Clave guardada, cifrada, en la carpeta de configuración." if t.strip() else "Clave borrada.", True)
            app.abrir(EntradaTexto(app, f"Clave de {ia.NOMBRES[s]}. Déjala vacía para borrarla", hecho, secreto=True, maximo=300,
                                   ayuda=ia.DONDE_CLAVE[s] + " Se guarda cifrada en tu ordenador y solo se usa para hablar con los personajes. Puedes pegarla con Control V."))
        return abrir

    def estado_clave(s):
        def txt():
            if ia.clave_guardada(s):
                return f"Clave de {ia.NOMBRES[s]}: guardada"
            return f"Clave de {ia.NOMBRES[s]}: " + ("tomada de una variable de entorno" if ia.clave(s) else "sin poner")
        return txt

    def texto(clave_cfg, titulo, ayuda):
        def abrir():
            def hecho(t):
                cfg[clave_cfg] = t.strip()
                ia.olvidar_modelos("otro")
                app.decir("Guardado." if t.strip() else "Borrado.", True)
            app.abrir(EntradaTexto(app, titulo, hecho, maximo=200, ayuda=ayuda))
        return abrir

    def estado_local():
        if ia.local_instalado():
            k = ia.modelo_instalado()
            nombre = ia.MODELOS_LOCALES[k]["nombre"].split(",")[0].lower() if k in ia.MODELOS_LOCALES else k
            return f"Modelo local: instalado, el {nombre}. " + ("Está en marcha" if ia.local_en_marcha() else "Ahora está parado")
        if ia._buscar_local():
            return "Modelo local: hay un programa de modelos abierto en este ordenador y el juego lo usará"
        return "Modelo local: sin instalar. Intro para descargarlo"

    def info_local():
        local(app)

    def probar():
        if not ia.disponible(cfg):
            app.son("error")
            app.decir(ia.por_que_no(cfg), True)
            return
        app.decir("Probando. Espera un momento.", True)
        app.decir(ia.probar(cfg), True)

    def cual():
        u = ia.ultimo_uso
        if not u["servicio"]:
            return "Todavía no se ha usado ningún servicio en esta sesión"
        return f"Lo último lo contestó {ia.NOMBRES[u['servicio']]}, con el modelo {u['modelo']}, en {u['segundos']} segundos"

    def ops():
        lista = [
            Opcion(lambda: f"Modo IA al hablar con la gente: {'sí' if cfg['ia_activa'] else 'no'}", ajuste=alternar,
                   ayuda="Con el modo IA, cuando escribes lo que quieres decirle a alguien con la tecla J, contesta una inteligencia artificial interpretando a esa persona, "
                         "y nunca contesta dos veces igual. Sin modo IA, el juego usa su propio motor de conversación, sin conexión."),
            Opcion(lambda: f"Servicio: {ia.NOMBRES[cfg['ia_servicio']]}", ajuste=servicio,
                   ayuda="Izquierda y derecha para cambiar. En automático, el juego prueba primero lo gratuito: el modelo local y luego Google AI Studio. "
                         "Después, los demás servicios que tengan clave. Si uno falla, pasa al siguiente. En cada servicio elige solo el modelo más barato."),
            Opcion(estado_local, info_local, ayuda="Gratis, sin internet y sin clave. Intro para descargar, cambiar o quitar el modelo."),
            Opcion(estado_clave("gemini"), pedir_clave("gemini"), ayuda="Google AI Studio tiene un nivel gratuito. Intro para escribir o borrar la clave."),
            Opcion(estado_clave("openai"), pedir_clave("openai"), ayuda="De pago: unos céntimos por cada mil frases. Intro para escribir o borrar la clave."),
            Opcion(estado_clave("anthropic"), pedir_clave("anthropic"), ayuda="De pago: unos céntimos por cada mil frases. Intro para escribir o borrar la clave."),
            Opcion(estado_clave("otro"), pedir_clave("otro"), ayuda="Para otros servicios compatibles con el formato de OpenAI, como OpenRouter o Groq. Algunos tienen modelos gratuitos."),
            Opcion(lambda: f"Dirección del otro servicio: {cfg['ia_url_otro'] or 'la de OpenRouter'}",
                   texto("ia_url_otro", "Dirección del servicio, empezando por https. Vacía, la de OpenRouter", "Es la dirección base del servicio, la que termina en barra v1."),
                   ayuda="Solo hace falta si usas un servicio que no sea OpenRouter."),
            Opcion(lambda: f"Modelo del otro servicio: {cfg['ia_modelo_otro'] or 'lo elige el juego'}",
                   texto("ia_modelo_otro", "Nombre del modelo. Vacío, lo elige el juego", "Si lo dejas vacío, el juego busca un modelo gratuito y, si no hay, usa el primero de la lista."),
                   ayuda="Solo para el otro servicio. En los demás, el modelo lo elige siempre el juego."),
            Opcion("Probar ahora", probar, ayuda="Hace una pregunta de prueba y te dice qué servicio y qué modelo han contestado y cuánto han tardado."),
            Opcion(cual),
            Opcion("Volver a buscar el modelo más barato", lambda: (ia.olvidar_modelos(), app.decir("Hecho. En la próxima conversación se vuelve a preguntar a cada servicio.", True)),
                   ayuda="El juego lo hace solo cada semana, y cuando un modelo deja de existir. Úsalo si quieres forzarlo."),
            Opcion("Qué se envía", accion=lambda: app.decir("Se envía lo que escribes, la ficha de la persona con la que hablas, la hora, el barrio y si llueve, y cómo te ven los vecinos. "
                                                            "No se envían tu partida, tus archivos ni ningún dato tuyo. Con el modelo local no sale nada de tu ordenador. "
                                                            "En el nivel gratuito de Google, lo enviado puede usarse para mejorar sus productos.", True)),
            Opcion("Volver", lambda: app.cerrar(m)),
        ]
        return lista

    m = Menu(app, "Personas e inteligencia artificial", ops, al_cerrar=cfg.guardar)
    app.abrir(m)


def local(app):
    """Descargar, cambiar o quitar el modelo de inteligencia artificial que funciona en el propio ordenador."""
    from . import ia
    from .menus_actualizar import Tarea
    cfg = app.cfg

    def instalar(clave):
        def empezar():
            estado = {"decimo": 0}

            def trabajo(tarea):
                def progreso(hecho, total):
                    decimo = int(10 * hecho / max(1, total))
                    if decimo > estado["decimo"] and decimo < 10:
                        estado["decimo"] = decimo
                        tarea.decir(f"{decimo * 10} por ciento.")
                return ia.instalar_local(clave, progreso=progreso, cancelado=lambda: tarea.cancelada, decir=tarea.decir, abrir=getattr(app, "ia_abrir", None))

            def fin(ok, error):
                if error is not None:
                    if isinstance(error, ia.Cancelado):
                        app.decir("Descarga cancelada. No se ha instalado nada nuevo.", True)
                    else:
                        app.son("error")
                        app.decir("No se ha podido descargar. Comprueba la conexión y el espacio en el disco, y vuelve a intentarlo.", True)
                    ia.ajustar_local(cfg)
                    return
                app.son("guardado")
                if not cfg["ia_activa"]:
                    cfg["ia_activa"] = True
                ia.ajustar_local(cfg)
                app.decir("Modelo instalado y modo IA activado. El modelo se está cargando: en unos segundos puedes usar Probar ahora, en el menú anterior.", True)
            app.abrir(Tarea(app, f"Descargando el modelo {ia.MODELOS_LOCALES[clave]['nombre'].split(',')[0].lower()}", trabajo, fin))
        return empezar

    def quitar():
        def si():
            ia.quitar_local()
            app.cerrar(c)
            app.decir("Modelo local quitado. Se ha borrado la carpeta data, ia local.", True)
        c = Menu(app, "Vas a borrar el programa y el modelo local de tu disco. Podrás volver a descargarlos cuando quieras",
                 [Opcion("No, dejarlo como está", lambda: app.cerrar(c)), Opcion("Sí, quitarlo", si)])
        app.abrir(c)

    def ops():
        puesto = ia.modelo_instalado()
        lista = [Opcion("Qué es", accion=lambda: app.decir(
            "Un modelo local es una inteligencia artificial pequeña que funciona en tu propio ordenador: es gratis, no necesita internet ni clave, y nada de lo que escribes sale de tu equipo. "
            "Contesta más despacio y con menos gracia que los servicios de internet, y cuanto más antiguo es el ordenador, más tarda. "
            "El juego descarga dos cosas a la carpeta data, ia local: el programa llama punto c p p, de código abierto, y el modelo que elijas. "
            "Mientras el modo IA lo use, el juego lo arranca al abrirse y lo cierra siempre al salir: nunca queda nada abierto.", True))]
        for clave, m in ia.MODELOS_LOCALES.items():
            marca = ", instalado" if clave == puesto else ""
            lista.append(Opcion(f"{'Volver a comprobar' if marca else 'Descargar'} el modelo {m['nombre'].lower()}: {m['tamano'] // 2 ** 20} megas{marca}",
                                instalar(clave), ayuda=m["desc"] + (" Sustituye al que tengas instalado." if puesto and not marca else "")))
        if ia.local_instalado():
            lista.append(Opcion("Quitar el modelo local", quitar, ayuda="Borra el programa y el modelo de tu disco."))
        lista.append(Opcion("Volver", lambda: app.cerrar(m_)))
        return lista

    m_ = Menu(app, "Modelo local", ops, al_cerrar=cfg.guardar)
    app.abrir(m_)
