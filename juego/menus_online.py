"""Menús de «Jugar con amigos»: abrir tu partida, unirte a la de otro, mensajes, GPS y dinero."""
from .i18n import tr
import threading

from . import red
from .menus import EntradaTexto, Menu, Opcion


def copiar(app, texto):
    """Copia un texto al portapapeles, para pegarlo en un mensaje a un amigo."""
    try:
        import pygame
        pygame.scrap.put_text(texto)
        ok = True
    except Exception:
        ok = False
    if not ok:
        try:
            import subprocess
            subprocess.run("clip", input=texto.encode("utf-16-le"), shell=True, timeout=5, check=True)
            ok = True
        except Exception:
            ok = False
    app.son("menu_ok" if ok else "error")
    app.decir(tr("Dirección copiada al portapapeles. Pégala en un mensaje a tu amigo.") if ok else tr("No se pudo copiar. Te la leo: ") + deletrear(texto), True)


def deletrear(direccion):
    """Lee una dirección de forma que se pueda apuntar: los puntos y los dos puntos, dichos."""
    return direccion.replace("://", ", dos puntos, barra, barra, ").replace(":", ", dos puntos, ").replace(".", " punto ")


def escribir_mensaje(p, canal=None):
    """F10: un mensaje para los demás. En un servidor, con «canal» va por un canal de rol: «ic», en personaje, o «yo», una acción."""
    app = p.app
    if not p.online_activo():
        app.son("error")
        app.decir(tr("No estás jugando con nadie. Abre el móvil con M y entra en Jugar con amigos."), True)
        return
    if getattr(p, "en_servidor", False):
        from . import menus_enlinea
        return menus_enlinea.chat(p, canal) if canal else menus_enlinea.chat(p)
    if canal:
        app.son("error")
        app.decir(tr("Los canales de rol son de los servidores en línea. Jugando con amigos, el mensaje es para todos: pulsa F10."), True)
        return
    from . import gente
    app.abrir(EntradaTexto(app, tr("Mensaje para tus amigos"), p.enviar_chat, maximo=300, propuestas=gente.lista("frases_chat")))


def amigos(p):
    if getattr(p, "en_servidor", False):
        from . import menus_enlinea
        return menus_enlinea.menu(p)
    app = p.app
    cfg = p.cfg
    estado = {"clave": ""}

    def cerrar_menu():
        app.cerrar(menu)

    def volver_al_juego():
        while len(app.pila) > 1 and app.pila[-1] is not p:
            app.pila.pop()
        app.teclas.clear()

    # ------------------------------------------------------------ sin conectar
    def poner_nombre():
        def hecho(t):
            cfg["red_nombre"] = t.strip()[:24]
            cfg.guardar()
            app.decir(tr('Tus amigos te verán como {nombre_online}.').format(nombre_online=(p.nombre_online())), True)
        app.abrir(EntradaTexto(app, tr("Tu nombre para los amigos"), hecho, inicial=cfg["red_nombre"], maximo=24))

    def poner_clave():
        def hecho(t):
            estado["clave"] = t
            app.decir(tr("Contraseña puesta: solo entrará quien la sepa.") if t else tr("Sin contraseña: entrará cualquiera que tenga la dirección."), True)
        app.abrir(EntradaTexto(app, tr("Contraseña para tu partida. Déjala vacía para no poner ninguna"), hecho, inicial=estado["clave"], secreto=True, maximo=40))

    def puerto(d):
        cfg["red_puerto"] = max(1024, min(65535, cfg["red_puerto"] + d))

    def abrir():
        ok, texto = p.abrir_a_amigos(cfg["red_puerto"], estado["clave"])
        cfg.guardar()
        if not ok:
            app.son("error")
            app.decir(texto, True)
            return
        ips = red.direcciones_locales()
        app.decir(texto + tr(' En tu casa, la dirección es {deletrear}. Para amigos de fuera, mira en este menú Cómo invitar a un amigo.').format(deletrear=(deletrear(red.direccion(ips[0], p.servidor.puerto)))), True)
        menu.i = 0
        menu.refrescar(False)

    def unirse():
        def con_direccion(d):
            if not d.strip():
                return

            def con_clave(c):
                app.decir(tr("Conectando."), True)
                ok, texto = p.unirse_a_amigo(d, c)
                cfg.guardar()
                app.son("menu_ok" if ok else "error")
                app.decir(texto, True)
                menu.i = 0
            app.abrir(EntradaTexto(app, tr("Contraseña de la partida. Si no tiene, pulsa Intro"), con_clave, secreto=True, maximo=40))
        app.abrir(EntradaTexto(app, tr("Dirección de la partida de tu amigo"), con_direccion, inicial=cfg["red_ultima"], maximo=80,
                               ayuda=tr("Es lo que te ha pasado tu amigo: empieza por puertobravo, dos puntos, barra, barra. Puedes pegarla con Control V.")))

    # --------------------------------------------------------------- conectado
    def invitar():
        srv = p.servidor
        ips = red.direcciones_locales()
        local = red.direccion(ips[0], srv.puerto)

        def publica():
            app.decir(tr("Consultando tu dirección de internet."), True)

            def hacer():
                ip = red.direccion_publica()
                if ip:
                    estado["publica"] = red.direccion(ip, srv.puerto)
                    app.decir(tr('Tu dirección para amigos de fuera es {deletrear}. Está en este menú para copiarla.').format(deletrear=(deletrear(estado['publica']))))
                else:
                    app.decir(tr("No se pudo averiguar. Busca en internet cuál es mi IP y dásela a tu amigo, seguida de dos puntos y el puerto."))
            threading.Thread(target=hacer, daemon=True).start()
        ops = [
            Opcion(tr('En la misma casa o la misma red: {deletrear}').format(deletrear=(deletrear(local))), lambda: copiar(app, local), ayuda=tr("Intro la copia al portapapeles.")),
            Opcion(lambda: tr("Para amigos de fuera: ") + (deletrear(estado["publica"]) if estado.get("publica") else tr("pulsa Intro para averiguar tu dirección de internet")),
                   lambda: copiar(app, estado["publica"]) if estado.get("publica") else publica(),
                   ayuda=tr("La primera vez pregunta a un servicio de internet cuál es tu dirección. Después, Intro la copia.")),
            Opcion(tr('Tu router tiene que dejar pasar el puerto {puerto}, protocolo TCP, hacia este ordenador').format(puerto=(srv.puerto)),
                   ayuda=tr("Se hace en la configuración del router, en el apartado de abrir puertos o redirección de puertos. Si el cortafuegos de Windows pregunta, permite el acceso. Sin esto, solo podrán entrar los que estén en tu misma red.")),
            Opcion(tr("Tu partida está protegida con contraseña: díselo a tu amigo") if srv.protegido else tr("Tu partida no tiene contraseña: entra cualquiera que tenga la dirección"),
                   ayuda=tr("La contraseña se pone antes de abrir la partida. Para cambiarla, cierra la partida a los amigos y vuelve a abrirla.")),
            Opcion(tr("Si no consigue entrar: AdGuard, antivirus y cortafuegos"), ayuda=red.AVISO_FILTROS,
                   accion=lambda: app.decir(red.AVISO_FILTROS + tr(" El cortafuegos de Windows pregunta la primera vez: hay que permitir el acceso."), True)),
            Opcion(tr("Volver"), lambda: app.cerrar(m)),
        ]
        m = Menu(app, tr("Cómo invitar a un amigo"), ops)
        app.abrir(m)

    def amigo(r):
        def abrir_amigo():
            dinero_ayuda = tr("Sale de lo que llevas encima y le llega al momento, esté donde esté. Si no lo llevas, no se envía.")
            ops = [Opcion(lambda: p.donde_esta(r), ayuda=tr("Dónde está y si va a pie o al volante. Cambia a medida que se mueve.")),
                   Opcion(tr("Marcar en el GPS"), lambda: (volver_al_juego(), p.gps_a_amigo(r)),
                          ayuda=tr("Vuelves al juego con el GPS hacia tu amigo. Si está en otra localidad, te lleva al sitio más cercano a donde está. Si se mueve, vuelve a marcarlo.")),
                   Opcion(tr("Enviarle 50 euros"), lambda: p.dar_dinero_a(r, 50), ayuda=dinero_ayuda),
                   Opcion(tr("Enviarle 500 euros"), lambda: p.dar_dinero_a(r, 500), ayuda=dinero_ayuda),
                   Opcion(tr("Darle un botiquín"), lambda: p.dar_botiquin_a(r), ayuda=tr("Le das uno de tus botiquines, esté donde esté. Si no te queda ninguno, no se puede."))]
            if p.es_anfitrion():
                def echar():
                    p.servidor.expulsar(r.id)
                    app.decir(tr('Has sacado a {nombre} de tu partida.').format(nombre=(r.nombre)), True)
                    app.cerrar(m)
                ops.append(Opcion(tr("Expulsarlo de mi partida"), echar, ayuda=tr("Lo desconecta. Si vuelve a entrar y no quieres, cierra la partida y ábrela con contraseña.")))
            ops.append(Opcion(tr("Volver"), lambda: app.cerrar(m)))
            m = Menu(app, r.nombre, ops)
            app.abrir(m)
        return abrir_amigo

    def mensajes():
        lineas = list(reversed(p.chat)) or [tr("Todavía no hay mensajes")]
        ayuda = tr("Un mensaje de la partida. Para escribir uno, pulsa F10 durante el juego.")
        m = Menu(app, tr("Últimos mensajes, del más reciente al más antiguo"), [Opcion(t, ayuda=ayuda) for t in lineas] + [Opcion(tr("Volver"), lambda: app.cerrar(m))])
        app.abrir(m)

    def hecho(resultado, salir=False):
        ok, texto = resultado
        if texto:
            app.son("menu_ok" if ok else "error")
            app.decir(texto, True)
        menu.refrescar(False)
        if ok and salir:
            volver_al_juego()

    def carrera():
        from . import menus_juego
        menus_juego.lista_lugares(p, al_elegir=lambda l: hecho(p.proponer_carrera(l)), titulo=tr("Destino de la carrera"), otras=False)

    def reparto():
        hecho(p.proponer_reparto())

    def desconectar():
        anfitrion = p.es_anfitrion()
        p.desconectar_online()
        app.son("amigo_sale")
        app.decir(tr("Has cerrado tu partida a los amigos. Sigues jugando por tu cuenta.") if anfitrion else tr("Te has desconectado. Sigues jugando por tu cuenta."), True)
        menu.i = 0
        menu.refrescar(False)

    def ops():
        if not p.online_activo():
            return [
                Opcion(tr("Abrir mi partida a mis amigos"), abrir, ayuda=tr("Tu ordenador hace de servidor y tú sigues jugando con normalidad. Después te digo la dirección que tienes que darles.")),
                Opcion(lambda: tr("Contraseña de mi partida: ") + ("puesta" if estado["clave"] else tr("ninguna, entra quien tenga la dirección")), poner_clave,
                       ayuda=tr("Intro para escribirla. Con contraseña solo entra quien la sepa.")),
                Opcion(lambda: tr('Abrir el puerto del router automáticamente: {v}').format(v=(tr('sí') if cfg['red_upnp'] else tr('no'))), ajuste=lambda d: cfg.__setitem__("red_upnp", not cfg["red_upnp"]),
                       ayuda=tr("Al abrir tu partida, el juego le pide a tu router que abra el puerto, para que entren amigos de fuera de casa sin que tengas que configurar nada. "
                             "Al cerrar la partida, le pide que lo cierre. Si tu router no lo permite, el juego te lo dice y queda la manera manual, que explica el manual.")),
                Opcion(lambda: tr('Puerto: {red_puerto}').format(red_puerto=(cfg['red_puerto'])), ajuste=puerto, ayuda=tr("Cámbialo con izquierda y derecha solo si el de serie está ocupado. Es el número que hay que abrir en el router.")),
                Opcion(tr("Unirme a la partida de un amigo"), unirse, ayuda=tr("Te pedirá la dirección que te ha dado tu amigo y la contraseña, si tiene.")),
                Opcion(lambda: tr('Mi nombre para los amigos: {nombre_online}').format(nombre_online=(p.nombre_online())), poner_nombre,
                       ayuda=tr("Intro para cambiarlo, hasta veinticuatro letras. Es el nombre con el que te ven tus amigos.")),
                Opcion(tr("Qué se comparte"), ayuda=tr("Intro te cuenta qué oyes de tus amigos y qué podéis hacer juntos."),
                       accion=lambda: app.decir(tr("Oyes a tus amigos donde están: el motor de lo que conducen, sus pasos y su claxon. El radar los anuncia y el GPS te lleva hasta ellos. "
                                                "Podéis escribiros mensajes, que se leen en voz alta, con la tecla F10, y enviaros dinero. Cada uno conserva su propia partida, sus misiones y su progreso."), True)),
                Opcion(tr("Cómo se juega con amigos: explicación paso a paso"), lambda: p.explicacion("tut05") or app.decir(tr("La explicación no está en estos datos. El manual lo cuenta en Jugar con amigos."), True),
                       ayuda=tr("Cómo abrir tu partida, cómo unirte a la de otro y qué se puede hacer juntos. Se lee aquí mismo: no es una misión.")),
                Opcion(tr("Volver"), cerrar_menu),
            ]
        lista = [Opcion(lambda: (tr("Tu partida está abierta") + (tr(", con contraseña") if p.servidor.protegido else tr(", sin contraseña")) if p.es_anfitrion() else tr("Estás en la partida de un amigo"))
                        + tr('. Jugadores: {v}').format(v=(len(p.remotos) + 1)),
                        ayuda=tr("Cuántos estáis en la partida, contándote a ti. Debajo está cada uno de tus amigos."))]
        lista += [Opcion((lambda r=r: p.donde_esta(r)), amigo(r), ayuda=tr("Intro para marcarlo en el GPS, enviarle dinero") + (tr(" o expulsarlo.") if p.es_anfitrion() else ".")) for r in p.remotos.values()]
        lista.append(Opcion(tr("Escribir un mensaje"), lambda: escribir_mensaje(p), ayuda=tr("También con la tecla F10, sin abrir el móvil.")))
        lista.append(Opcion(lambda: p.coop_txt(), ayuda=tr("Las actividades conjuntas son carreras con apuesta y repartos en equipo. Además, a pie junto al vehículo parado de un amigo, la tecla F te sube de pasajero.")))
        c = p.coop
        if c is None:
            lista.append(Opcion(tr("Proponer una carrera hasta un lugar: 100 euros de apuesta"), carrera, ayuda=tr("Eliges el destino. Quien llega primero se lleva las apuestas de todos.")))
            lista.append(Opcion(tr("Proponer un reparto en equipo"), reparto, ayuda=tr("Cuatro entregas por esta localidad en seis minutos. Si las hacéis entre todos, cobráis todos.")))
        elif c["estado"] == "propuesta":
            if c["de"] == p.red.id:
                lista.append(Opcion(tr("Empezar ya"), lambda: hecho(p.empezar_coop(), True),
                                    ayuda=tr("Arranca la actividad con los que han aceptado y vuelves al juego. Hace falta que haya aceptado al menos uno.")))
            elif p.red.id not in c["participantes"]:
                lista.append(Opcion(tr("Aceptar y participar"), lambda: hecho(p.aceptar_coop()),
                                    ayuda=tr("Te apuntas. Si es una carrera, tienes que llevar encima el dinero de la apuesta. Empieza cuando lo diga quien la ha propuesto.")))
            if c["de"] == p.red.id:
                lista.append(Opcion(tr("Cancelar la actividad"), lambda: (p.cancelar_coop(), menu.refrescar(False)), ayuda=tr("La anulas para todos y se quita el GPS.")))
        elif c["de"] == p.red.id:
            lista.append(Opcion(tr("Cancelar la actividad"), lambda: (p.cancelar_coop(), menu.refrescar(False)), ayuda=tr("La anulas para todos y se quita el GPS.")))
        lista.append(Opcion(tr("Repasar los últimos mensajes"), mensajes, ayuda=tr("Los mensajes de la partida, del más reciente al más antiguo.")))
        if p.es_anfitrion():
            lista.append(Opcion(tr("Cómo invitar a un amigo: direcciones y puerto"), invitar,
                                ayuda=tr("La dirección que tienes que dar a tus amigos, para copiarla, y lo que hay que abrir en el router para que entren los de fuera de casa.")))
        lista.append(Opcion(tr("Cerrar mi partida a los amigos") if p.es_anfitrion() else tr("Desconectarme"), desconectar,
                            ayuda=tr("Se desconectan todos tus amigos y sigues jugando tu partida por tu cuenta.") if p.es_anfitrion()
                            else tr("Sales de la partida de tu amigo y sigues jugando la tuya por tu cuenta.")))
        lista.append(Opcion(tr("Volver"), cerrar_menu))
        return lista
    menu = Menu(app, tr("Jugar con amigos"), ops, al_cerrar=cfg.guardar,
                intro=tr("Tú montas la partida o te unes a la de un amigo. No hace falta ningún servidor de fuera"))
    app.abrir(menu)
