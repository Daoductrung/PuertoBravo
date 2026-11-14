"""Menús de «Jugar con amigos»: abrir tu partida, unirte a la de otro, mensajes, GPS y dinero."""
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
    app.decir("Dirección copiada al portapapeles. Pégala en un mensaje a tu amigo." if ok else "No se pudo copiar. Te la leo: " + deletrear(texto), True)


def deletrear(direccion):
    """Lee una dirección de forma que se pueda apuntar: los puntos y los dos puntos, dichos."""
    return direccion.replace("://", ", dos puntos, barra, barra, ").replace(":", ", dos puntos, ").replace(".", " punto ")


def escribir_mensaje(p):
    app = p.app
    if not p.online_activo():
        app.son("error")
        app.decir("No estás jugando con nadie. Abre el móvil con M y entra en Jugar con amigos.", True)
        return
    app.abrir(EntradaTexto(app, "Mensaje para tus amigos", p.enviar_chat, maximo=300))


def amigos(p):
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
            app.decir(f"Tus amigos te verán como {p.nombre_online()}.", True)
        app.abrir(EntradaTexto(app, "Tu nombre para los amigos", hecho, inicial=cfg["red_nombre"], maximo=24))

    def poner_clave():
        def hecho(t):
            estado["clave"] = t
            app.decir("Contraseña puesta: solo entrará quien la sepa." if t else "Sin contraseña: entrará cualquiera que tenga la dirección.", True)
        app.abrir(EntradaTexto(app, "Contraseña para tu partida. Déjala vacía para no poner ninguna", hecho, inicial=estado["clave"], secreto=True, maximo=40))

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
        app.decir(texto + f" En tu casa, la dirección es {deletrear(red.direccion(ips[0], p.servidor.puerto))}. "
                  "Para amigos de fuera, mira en este menú Cómo invitar a un amigo.", True)
        menu.i = 0
        menu.refrescar(False)

    def unirse():
        def con_direccion(d):
            if not d.strip():
                return

            def con_clave(c):
                app.decir("Conectando.", True)
                ok, texto = p.unirse_a_amigo(d, c)
                cfg.guardar()
                app.son("menu_ok" if ok else "error")
                app.decir(texto, True)
                menu.i = 0
            app.abrir(EntradaTexto(app, "Contraseña de la partida. Si no tiene, pulsa Intro", con_clave, secreto=True, maximo=40))
        app.abrir(EntradaTexto(app, "Dirección de la partida de tu amigo", con_direccion, inicial=cfg["red_ultima"], maximo=80,
                               ayuda="Es lo que te ha pasado tu amigo: empieza por puertobravo, dos puntos, barra, barra. Puedes pegarla con Control V."))

    # --------------------------------------------------------------- conectado
    def invitar():
        srv = p.servidor
        ips = red.direcciones_locales()
        local = red.direccion(ips[0], srv.puerto)

        def publica():
            app.decir("Consultando tu dirección de internet.", True)

            def hacer():
                ip = red.direccion_publica()
                if ip:
                    estado["publica"] = red.direccion(ip, srv.puerto)
                    app.decir(f"Tu dirección para amigos de fuera es {deletrear(estado['publica'])}. Está en este menú para copiarla.")
                else:
                    app.decir("No se pudo averiguar. Busca en internet cuál es mi IP y dásela a tu amigo, seguida de dos puntos y el puerto.")
            threading.Thread(target=hacer, daemon=True).start()
        ops = [
            Opcion(f"En la misma casa o la misma red: {deletrear(local)}", lambda: copiar(app, local), ayuda="Intro la copia al portapapeles."),
            Opcion(lambda: "Para amigos de fuera: " + (deletrear(estado["publica"]) if estado.get("publica") else "pulsa Intro para averiguar tu dirección de internet"),
                   lambda: copiar(app, estado["publica"]) if estado.get("publica") else publica(),
                   ayuda="La primera vez pregunta a un servicio de internet cuál es tu dirección. Después, Intro la copia."),
            Opcion(f"Tu router tiene que dejar pasar el puerto {srv.puerto}, protocolo TCP, hacia este ordenador",
                   ayuda="Se hace en la configuración del router, en el apartado de abrir puertos o redirección de puertos. Si el cortafuegos de Windows pregunta, permite el acceso. Sin esto, solo podrán entrar los que estén en tu misma red."),
            Opcion("Tu partida está protegida con contraseña: díselo a tu amigo" if srv.protegido else "Tu partida no tiene contraseña: entra cualquiera que tenga la dirección"),
            Opcion("Si no consigue entrar: AdGuard, antivirus y cortafuegos", ayuda=red.AVISO_FILTROS,
                   accion=lambda: app.decir(red.AVISO_FILTROS + " El cortafuegos de Windows pregunta la primera vez: hay que permitir el acceso.", True)),
            Opcion("Volver", lambda: app.cerrar(m)),
        ]
        m = Menu(app, "Cómo invitar a un amigo", ops)
        app.abrir(m)

    def amigo(r):
        def abrir_amigo():
            ops = [Opcion(lambda: p.donde_esta(r)),
                   Opcion("Marcar en el GPS", lambda: (volver_al_juego(), p.gps_a_amigo(r))),
                   Opcion("Enviarle 50 euros", lambda: p.dar_dinero_a(r, 50)),
                   Opcion("Enviarle 500 euros", lambda: p.dar_dinero_a(r, 500))]
            if p.es_anfitrion():
                def echar():
                    p.servidor.expulsar(r.id)
                    app.decir(f"Has sacado a {r.nombre} de tu partida.", True)
                    app.cerrar(m)
                ops.append(Opcion("Expulsarlo de mi partida", echar, ayuda="Lo desconecta. Si vuelve a entrar y no quieres, cierra la partida y ábrela con contraseña."))
            ops.append(Opcion("Volver", lambda: app.cerrar(m)))
            m = Menu(app, r.nombre, ops)
            app.abrir(m)
        return abrir_amigo

    def mensajes():
        lineas = list(reversed(p.chat)) or ["Todavía no hay mensajes"]
        m = Menu(app, "Últimos mensajes, del más reciente al más antiguo", [Opcion(t) for t in lineas] + [Opcion("Volver", lambda: app.cerrar(m))])
        app.abrir(m)

    def desconectar():
        anfitrion = p.es_anfitrion()
        p.desconectar_online()
        app.son("amigo_sale")
        app.decir("Has cerrado tu partida a los amigos. Sigues jugando tú solo." if anfitrion else "Te has desconectado. Sigues jugando tú solo.", True)
        menu.i = 0
        menu.refrescar(False)

    def ops():
        if not p.online_activo():
            return [
                Opcion("Abrir mi partida a mis amigos", abrir, ayuda="Tu ordenador hace de servidor y tú sigues jugando con normalidad. Después te digo la dirección que tienes que darles."),
                Opcion(lambda: "Contraseña de mi partida: " + ("puesta" if estado["clave"] else "ninguna, entra quien tenga la dirección"), poner_clave,
                       ayuda="Intro para escribirla. Con contraseña solo entra quien la sepa."),
                Opcion(lambda: f"Puerto: {cfg['red_puerto']}", ajuste=puerto, ayuda="Cámbialo con izquierda y derecha solo si el de serie está ocupado. Es el número que hay que abrir en el router."),
                Opcion("Unirme a la partida de un amigo", unirse, ayuda="Te pedirá la dirección que te ha dado tu amigo y la contraseña, si tiene."),
                Opcion(lambda: f"Mi nombre para los amigos: {p.nombre_online()}", poner_nombre),
                Opcion("Qué se comparte", ayuda="",
                       accion=lambda: app.decir("Oyes a tus amigos donde están: el motor de lo que conducen, sus pasos y su claxon. El radar los anuncia y el GPS te lleva hasta ellos. "
                                                "Podéis escribiros mensajes, que se leen en voz alta, con la tecla F10, y enviaros dinero. Cada uno conserva su propia partida, sus misiones y su progreso.", True)),
                Opcion("Volver", cerrar_menu),
            ]
        lista = [Opcion(lambda: ("Tu partida está abierta" + (", con contraseña" if p.servidor.protegido else ", sin contraseña") if p.es_anfitrion() else "Estás en la partida de un amigo")
                        + f". Jugadores: {len(p.remotos) + 1}")]
        lista += [Opcion((lambda r=r: p.donde_esta(r)), amigo(r), ayuda="Intro para marcarlo en el GPS, enviarle dinero" + (" o expulsarlo." if p.es_anfitrion() else ".")) for r in p.remotos.values()]
        lista.append(Opcion("Escribir un mensaje", lambda: escribir_mensaje(p), ayuda="También con la tecla F10, sin abrir el móvil."))
        lista.append(Opcion("Repasar los últimos mensajes", mensajes))
        if p.es_anfitrion():
            lista.append(Opcion("Cómo invitar a un amigo: direcciones y puerto", invitar))
        lista.append(Opcion("Cerrar mi partida a los amigos" if p.es_anfitrion() else "Desconectarme", desconectar))
        lista.append(Opcion("Volver", cerrar_menu))
        return lista
    menu = Menu(app, "Jugar con amigos", ops, al_cerrar=cfg.guardar,
                intro="Tú montas la partida o te unes a la de un amigo. No hace falta ningún servidor de fuera")
    app.abrir(menu)
