"""Menús del contenido para adultos: activación, vida social, sustancias, clubes y proveedores."""
import random

from .menus import Dialogo, Menu, Opcion


def _volver_al_juego(p):
    while len(p.app.pila) > 1 and p.app.pila[-1] is not p:
        p.app.pila.pop()
    p.app.teclas.clear()


# ================================================================== activación
def alternar_modo(app):
    cfg = app.cfg
    if cfg["adultos"]:
        cfg["adultos"] = False
        app.aplicar_adultos()
        app.decir("Contenido para adultos desactivado. Esos lugares y opciones desaparecen del juego.", True)
        return

    def si():
        cfg["adultos"] = True
        cfg.guardar()
        app.aplicar_adultos()
        app.cerrar(m)
        app.decir("Contenido para adultos activado. En el móvil aparecen Vida social y Sustancias, y en las ciudades hay clubes nocturnos y proveedores. "
                  "Con Mayúsculas Z abres tus sustancias.", True)

    m = Menu(app, "El contenido para adultos incluye relaciones sentimentales y sexuales, compañía de pago, drogas y venta de drogas, siempre sin escenas explícitas. ¿Eres mayor de 18 años y quieres activarlo?",
             [Opcion("No, dejarlo desactivado", lambda: app.cerrar(m)), Opcion("Sí, soy mayor de 18 años: activarlo", si)])
    app.abrir(m)


# ================================================================== vida social
def vida_social(p, directo=None):
    app = p.app
    j = p.j
    aqui = p.lugar_cercano(16)

    def ficha(pers):
        pid = pers["id"]
        nuevo = pid not in j.relaciones

        def en_mi_mapa():
            l = p.lug(pers["lugar"])
            return l is not None and l.mapa == p.mundo.id

        def lejos():
            l = p.lug(pers["lugar"])
            app.son("error")
            app.decir(f"{pers['nombre']} está en {p.nombre_lugar(l) if l else 'otra localidad'}. Para quedar tenéis que estar en la misma localidad.", True)

        def charlar():
            r = p.relacion(pid)
            if not en_mi_mapa():
                return lejos()
            if p._hecho_hoy(r, "charla"):
                app.decir(f"Ya habéis charlado hoy. {pers['nombre']} tiene cosas que hacer.", True)
                return
            p.sumar_afinidad(pid, 3)
            p.cambiar_animo(2)
            app.decir(f"Charláis un rato. {random.choice(['Te cuenta cómo le ha ido el día.', 'Os reís de una tontería.', 'Te pregunta por tu vida.', 'Te habla de sus planes.'])} Ahora {p.afinidad_txt(r)}.", True)

        def cita(act):
            def f():
                r = p.relacion(pid)
                if not en_mi_mapa():
                    return lejos()
                if j.estrellas:
                    app.son("error")
                    app.decir("Con la policía detrás no es momento de citas.", True)
                    return
                if r["afinidad"] < 10:
                    app.decir(f"{pers['nombre']} apenas te conoce. Charlad primero algún día.", True)
                    return
                if p._hecho_hoy(r, "cita"):
                    app.decir("Ya habéis quedado hoy. Mejor otro día.", True)
                    return
                if not p.pagar(act["precio"]):
                    r["hoy"].pop("cita", None)
                    return
                gusta = act["id"] in pers.get("gustos", [])
                p.sumar_afinidad(pid, 13 if gusta else 5)
                r["citas"] = r.get("citas", 0) + 1
                p.pasar_horas(act["horas"])
                p.cambiar_animo(8 if gusta else 3)
                p.son("cita", cat="interfaz")
                como = "Lo pasáis en grande: es justo lo que le gusta." if gusta else "Pasáis un rato agradable, aunque no es su plan favorito."
                app.decir(f"{act['nombre']} con {pers['nombre']}. {como} Ahora {p.afinidad_txt(r)}. Son las {p.hora_txt()}.", True)
                p.celos(pid)
            return f

        def menu_cita():
            app.abrir(Menu(app, f"Cita con {pers['nombre']}. Tienes {j.dinero} euros",
                           [Opcion(f"{a['nombre']}: {a['precio']} euros", cita(a)) for a in p.dato_adulto("actividades")] + [Opcion("Volver", lambda: app.cerrar())],
                           intro="Cada persona tiene sus planes favoritos. Descúbrelos"))

        def regalo(g):
            def f():
                r = p.relacion(pid)
                if not en_mi_mapa():
                    return lejos()
                if p._hecho_hoy(r, "regalo"):
                    app.decir("Ya le has hecho un regalo hoy. No hay que agobiar.", True)
                    return
                if not p.pagar(g["precio"]):
                    r["hoy"].pop("regalo", None)
                    return
                favorito = pers.get("regalo") == g["id"]
                p.son("regalo", cat="interfaz")
                p.sumar_afinidad(pid, g["afinidad"] * (2 if favorito else 1))
                app.decir(f"Le regalas {g['nombre'].lower()}. {'¡Le encanta! Has acertado de lleno.' if favorito else 'Lo agradece con una sonrisa.'} Ahora {p.afinidad_txt(r)}.", True)
            return f

        def menu_regalo():
            app.abrir(Menu(app, f"Regalo para {pers['nombre']}. Tienes {j.dinero} euros",
                           [Opcion(f"{g['nombre']}: {g['precio']} euros", regalo(g)) for g in p.dato_adulto("regalos")] + [Opcion("Volver", lambda: app.cerrar())]))

        def pedir():
            r = p.relacion(pid)
            if j.pareja == pid:
                app.decir("Ya sois pareja.", True)
            elif j.pareja:
                otra = p.persona_social(j.pareja)
                app.decir(f"Ya tienes pareja: {otra['nombre']}. Tendrías que romper antes.", True)
            elif r["afinidad"] < 60:
                app.decir(f"{pers['nombre']} sonríe, pero te dice que aún es pronto. Necesitáis más tiempo juntos.", True)
            else:
                r["estado"] = "pareja"
                j.pareja = pid
                r["ultimo"] = p.dia
                p.son("pareja", cat="interfaz")
                p.cambiar_animo(20)
                app.decir(f"{pers['nombre']} dice que sí. Desde hoy sois pareja. Cuida la relación: si pasas días sin dar señales, o si se entera de que hay alguien más, lo vuestro se resentirá.", True)

        def noche():
            r = p.relacion(pid)
            if not en_mi_mapa():
                return lejos()
            if r["afinidad"] < 55 and j.pareja != pid:
                app.decir(f"{pers['nombre']} te dice que prefiere ir despacio.", True)
                return
            if j.estrellas:
                app.son("error")
                app.decir("Con la policía detrás, mejor otro día.", True)
                return
            casa = next((l for l in p.mundo.lugares.values() if l.tipo == "casa" and l.id in j.propiedades), None)
            if casa is None:
                if not p.pagar(70):
                    return
                donde = "un hotel"
            else:
                donde = casa.nombre
            if p._hecho_hoy(r, "noche"):
                app.decir("Hoy ya habéis estado juntos.", True)
                return
            from .intimidad import ENCUENTROS

            def elegir(tipo):
                def f():
                    gusta = tipo == pers.get("noche", "romantico")
                    p.sumar_afinidad(pid, 9 if gusta else 5)
                    p.encuentro(pers["nombre"], tipo, donde, pid=pid)
                    if gusta:
                        p.decir(f"Era justo lo que le apetecía a {pers['nombre']}.")
                    p.celos(pid)
                return f
            mm = Menu(app, f"La noche con {pers['nombre']}", [Opcion(ENCUENTROS[t][0], elegir(t)) for t in ENCUENTROS] + [Opcion("Mejor otro día", lambda: (r["hoy"].pop("noche", None), app.cerrar(mm)))],
                      intro="Cada persona tiene su manera preferida. Lo que hayas comprado para la ocasión se nota")
            app.abrir(mm)

        def romper():
            r = p.relacion(pid)
            r["estado"] = "ex"
            r["afinidad"] = max(0, r["afinidad"] - 40)
            if j.pareja == pid:
                j.pareja = ""
            p.son("ruptura", cat="interfaz")
            p.cambiar_animo(-10)
            app.cerrar()
            app.decir(f"Lo dejas con {pers['nombre']}. No ha sido agradable.", True)

        def ops():
            r = j.relaciones.get(pid)
            l = p.lug(pers["lugar"])
            lista = [Opcion(f"{pers['nombre']}, {pers['edad']} años. {pers['desc']} Suele estar en {p.nombre_lugar(l) if l else 'paradero desconocido'}")]
            if r is None:
                return lista + [Opcion("Aún no os conocéis. Ve a ese lugar y preséntate desde este mismo menú"), Opcion("Volver", lambda: app.cerrar())]
            estado = {"pareja": "Sois pareja", "ex": "Lo dejasteis"}.get(r["estado"], "Os estáis conociendo")
            lista.append(Opcion(lambda: f"{estado}. {p.afinidad_txt(p.relacion(pid)).capitalize()}. Habéis tenido {p.relacion(pid).get('citas', 0)} citas"))
            from .intimidad import GESTOS
            lista += [Opcion("Charlar un rato", charlar), Opcion("Proponer una cita", menu_cita), Opcion("Hacerle un regalo", menu_regalo)]
            from . import sistemas
            if p.acompanante and p.acompanante["pid"] == pid:
                lista.append(Opcion("Despedirte: el paseo termina aquí", lambda: (app.cerrar(), sistemas.terminar_paseo(p))))
            elif aqui is not None and aqui.id == pers["lugar"]:
                lista.append(Opcion("Proponerle salir contigo a dar una vuelta", lambda: sistemas.empezar_paseo(p, pers) and [app.cerrar(x) for x in list(app.pila) if x is not p],
                                    ayuda="Se viene contigo de verdad: te sigue a pie y sube al vehículo que lleves. Pasear, llevarle a comer, a un bar, al cine o a la feria le gusta y os acerca. "
                                          "Si te metes en líos con la policía, no. Una vez al día; dura como mucho tres horas del juego."))
            lista += [Opcion(GESTOS[g][0], (lambda g=g: p.gesto(pid, pers, g)) if True else None, ayuda="Un gesto de cariño. Hace falta cierta confianza, y cada uno se puede repetir una vez al día.") for g in GESTOS]
            lista += [
                      Opcion("Pasar la noche juntos", noche, ayuda="Necesitáis mucha confianza. Vais a una de tus casas en esta localidad o, si no tienes, a un hotel por 70 euros.")]
            if j.pareja == pid:
                lista.append(Opcion("Romper la relación", romper))
            else:
                lista.append(Opcion("Pedirle que sea tu pareja", pedir, ayuda="Hace falta mucha química. Tener pareja sube tu ánimo cada día, pero hay que cuidarla."))
            lista.append(Opcion("Volver", lambda: app.cerrar()))
            return lista
        if nuevo and aqui is not None and aqui.id == pers["lugar"]:
            p.relacion(pid)
            j.stats["conocidos"] = j.stats.get("conocidos", 0) + 1
            app.decir(f"Te presentas a {pers['nombre']}. {pers['desc']}", True)
        app.abrir(Menu(app, pers["nombre"], ops))

    def ops():
        lista = []
        for pers in p.dato_adulto("personas"):
            l = p.lug(pers["lugar"])
            if l is None:
                continue
            r = j.relaciones.get(pers["id"])
            if r is None:
                if aqui is not None and aqui.id == pers["lugar"]:
                    lista.append(Opcion(f"Presentarte a {pers['nombre']}, que está aquí mismo", (lambda pers=pers: ficha(pers))))
                else:
                    lista.append(Opcion(f"Alguien a quien no conoces suele estar en {p.nombre_lugar(l)}", (lambda pers=pers: ficha(pers))))
            else:
                marca = ", tu pareja" if j.pareja == pers["id"] else ", ex" if r["estado"] == "ex" else ""
                lista.append(Opcion(f"{pers['nombre']}{marca}: {p.afinidad_txt(r)}", (lambda pers=pers: ficha(pers))))
        lista.append(Opcion(lambda: f"Tu ánimo es {p.animo_txt()}. En la calle, {p.reputacion_txt()}"))
        lista.append(Opcion("Volver", lambda: app.cerrar()))
        return lista
    if directo:                                              # desde el propio local, vas derecho a la persona
        pers = next((x for x in p.dato_adulto("personas") if x["id"] == directo), None)
        if pers is not None:
            ficha(pers)
        return
    app.abrir(Menu(app, "Vida social", ops, intro="Aquí están las personas con las que puedes tener una relación"))


# =================================================================== sustancias
def menu_sustancias(p):
    app = p.app
    j = p.j
    if not p.modo_adulto():
        return

    def tomar(ident):
        def f():
            p.consumir(ident)
            if app.pila and app.pila[-1] is m:
                m.refrescar(False)
        return f

    def ops():
        lista = []
        for s in p.dato_adulto("sustancias"):
            n = j.sustancias.get(s["id"], 0)
            if n > 0:
                lista.append(Opcion(f"Tomar {s['nombre'].lower()}: tienes {n}", tomar(s["id"]), ayuda=s["desc"]))
        if not lista:
            lista.append(Opcion("No llevas nada encima"))
        activos = [p.sustancia(e["id"])["nombre"] + (", bajón" if e.get("bajon") else "") + f", {int(e['t'])} segundos" for e in j.efectos if p.sustancia(e["id"])]
        lista.append(Opcion("Efectos ahora mismo: " + ("; ".join(activos) if activos else "ninguno")))
        enganches = [f"{p.sustancia(s)['nombre']} {int(n)} de 100" for s, n in j.adiccion.items() if p.sustancia(s)]
        lista.append(Opcion("Dependencia: " + (", ".join(enganches) if enganches else "ninguna") + (". Tienes síndrome de abstinencia" if p._abstinencia() else ""),
                            ayuda="A partir de 40 necesitas tomar cada día o sufres abstinencia. Baja sola poco a poco, y en un hospital te desintoxican."))
        lista.append(Opcion(f"Llevas {p.carga()} de {100} unidades de mercancía. Para vender, ponte junto a un peatón sin arma en la mano y pulsa E"))
        lista.append(Opcion("Volver", lambda: app.cerrar()))
        return lista
    m = Menu(app, "Sustancias", ops, intro="F1 explica el efecto de cada una")
    app.abrir(m)


# ========================================================================= club
def club(p, l):
    app = p.app
    j = p.j

    def copa():
        if p.pagar(15):
            p.consumir("alcohol", de_inventario=False)

    def espectaculo():
        if p.pagar(20):
            p.pasar_horas(1)
            p.cambiar_animo(5)
            app.decir(f"Ves el espectáculo desde la barra. Sales una hora después, a las {p.hora_txt()}.", True)

    def compania():
        if j.estrellas:
            app.son("error")
            app.decir("El portero te ha reconocido de las noticias y no te deja pasar al reservado.", True)
            return
        if not p.pagar(150):
            return
        p.pasar_horas(1)
        j.stats["pagos"] = j.stats.get("pagos", 0) + 1
        p.son("pasan_horas", cat="interfaz")
        _volver_al_juego(p)
        app.abrir(Dialogo(app, [("Narrador", f"Pagas, subís a una habitación y la puerta se cierra. Una hora después estás otra vez en la calle. Son las {p.hora_txt()}.")]))
        p.cambiar_animo(14)
        if j.intimos.get("preservativos", 0) > 0:
            j.intimos["preservativos"] -= 1
        elif not j.its and random.random() < 0.15:
            j.its = p.dia
        azar = random.random()
        if azar < 0.08 and p.mundo.policia:
            multa = min(j.dinero, 300)
            j.dinero -= multa
            p.decir(f"¡Redada! La policía entra en el club y te cae una multa de {multa} euros.")
            p.poner_busqueda(1)
        elif azar < 0.14:
            robo = int(j.dinero * 0.1)
            j.dinero -= robo
            p.decir(f"Al salir notas la cartera más ligera: te faltan {robo} euros.")
        p.celos()
    def bailar():
        if not p.pagar(5):
            return
        p.pasar_horas(1)
        p.cambiar_animo(6)
        p.son("cita", cat="interfaz")
        if random.random() < 0.45:
            from .charla import ficha
            from .entidades import Persona
            x, y = p.mundo.punto_libre(j.x + random.uniform(-3, 3), j.y + random.uniform(-3, 3))
            q = Persona("civil", x, y)
            q.estado = "quieto"
            f = ficha(q)
            f["confianza"], f["disponible"] = 25, True
            if p.cfg["mi_genero"] != "x" and p.cfg["mi_genero"] not in f["le_atraen"]:
                f["le_atraen"] += p.cfg["mi_genero"]
            p.personas.append(q)
            app.decir(f"Bailas una hora en la pista. Alguien no deja de mirarte: al salir está a tu lado. Háblale con la tecla J. Son las {p.hora_txt()}.", True)
        else:
            app.decir(f"Bailas una hora en la pista y sales con otra cara. Son las {p.hora_txt()}.", True)

    def privado():
        if p.pagar(60):
            p.pasar_horas(0.5)
            p.cambiar_animo(9)
            p.son("cita", cat="interfaz")
            app.decir("Pase privado. Luces bajas, música lenta y un baile solo para ti, a un palmo y sin tocar. Sales con el pulso acelerado.", True)

    def tienda():
        mt = Menu(app, lambda: f"Tienda discreta del club. Tienes {j.dinero} euros",
                  [Opcion((lambda a=a: f"{a['nombre']}: {a['precio']} euros. Tienes {j.intimos.get(a['id'], 0)}"), (lambda a=a: p.comprar_articulo(a)), ayuda=a["desc"]) for a in p.articulos_intimos()]
                  + [Opcion("Volver", lambda: app.cerrar(mt))])
        app.abrir(mt)
    m = Menu(app, lambda: f"{l.nombre}. Tienes {j.dinero} euros", [
        Opcion("Tomar una copa: 15 euros", copa, ayuda="Es alcohol: sube el ánimo, pero cada copa te hace caminar más torcido y apuntar peor."),
        Opcion("Bailar en la pista: 5 euros", bailar, ayuda="Sube el ánimo, y es buen sitio para conocer a alguien."),
        Opcion("Ver el espectáculo: 20 euros", espectaculo),
        Opcion("Pase privado: 60 euros", privado, ayuda="Un baile sensual solo para ti. Sube el ánimo."),
        Opcion("Tienda discreta: preservativos, lencería y más", tienda, ayuda="Lo que compres aquí mejora tus noches y sirve de regalo."),
        Opcion("Pagar por compañía: 150 euros", compania, ayuda="Sube el ánimo. Puede haber redada, pueden robarte y, si tienes pareja, puede enterarse. Sin preservativos hay riesgo para tu salud."),
        Opcion("Volver", lambda: app.cerrar())])
    app.abrir(m)


# ==================================================================== proveedor
def proveedor(p, l):
    app = p.app
    j = p.j
    ilegales = [s for s in p.dato_adulto("sustancias") if not s.get("legal")]

    def comprar(s, n):
        def f():
            precio, _ = p.precio_sustancia(s["id"], l)
            if p.carga() + n > 100:
                app.son("error")
                app.decir(f"No te cabe: llevas {p.carga()} de 100 unidades.", True)
                return
            if p.pagar(precio * n):
                j.sustancias[s["id"]] = j.sustancias.get(s["id"], 0) + n
                p.son("trato", cat="interfaz")
                app.decir(f"Compras {n} de {s['nombre'].lower()} por {precio * n} euros. Llevas {j.sustancias[s['id']]}.", True)
        return f

    def vender(s, n):
        def f():
            tengo = j.sustancias.get(s["id"], 0)
            k = tengo if n is None else min(n, tengo)
            if k <= 0:
                app.son("error")
                app.decir("No llevas de eso.", True)
                return
            precio, _ = p.precio_sustancia(s["id"], l)
            cobro = int(precio * 0.85) * k
            j.sustancias[s["id"]] = tengo - k
            j.stats["vendido"] = j.stats.get("vendido", 0) + cobro
            p.son("trato", cat="interfaz")
            p.dar_dinero(cobro)
            p.cambiar_reputacion(0.02 * k)
            app.decir(f"Vendes {k} de {s['nombre'].lower()} por {cobro} euros. Te quedan {j.sustancias[s['id']]}.", True)
        return f

    def tratar(s):
        def titulo():
            precio, nota = p.precio_sustancia(s["id"], l)
            extra = {"ganga": " Hoy está tirado de precio.", "escasez": " Hoy hay escasez: está carísimo."}.get(nota, "")
            if nota:
                p.son("precio_" + nota, cat="interfaz")
            return f"{s['nombre']}: {precio} euros la unidad.{extra} Llevas {j.sustancias.get(s['id'], 0)}. Tienes {j.dinero} euros"
        app.abrir(Menu(app, titulo, [Opcion("Comprar 1", comprar(s, 1)), Opcion("Comprar 10", comprar(s, 10)),
                                     Opcion("Vender 10 al 85 por ciento del precio", vender(s, 10)), Opcion("Vender todo", vender(s, None)),
                                     Opcion(s["desc"]), Opcion("Volver", lambda: app.cerrar())]))

    def ops():
        lista = []
        for s in ilegales:
            precio, nota = p.precio_sustancia(s["id"], l)
            marca = {"ganga": ", ganga", "escasez": ", escasez"}.get(nota, "")
            lista.append(Opcion(f"{s['nombre']}: {precio} euros{marca}. Llevas {j.sustancias.get(s['id'], 0)}", (lambda s=s: tratar(s)), ayuda=s["desc"]))
        from . import laboratorio
        lista.append(laboratorio.opcion_proveedor(p, Opcion))
        lista.append(Opcion(f"Mochila: {p.carga()} de 100 unidades. En la calle, {p.reputacion_txt()}",
                            ayuda="Los precios cambian cada día y en cada localidad: compra donde esté barato y vende donde esté caro, o al menudeo en la calle, que se paga mejor pero es más arriesgado."))
        lista.append(Opcion("Volver", lambda: app.cerrar()))
        return lista
    app.abrir(Menu(app, lambda: f"{l.nombre}. Tienes {j.dinero} euros", ops, intro="Los precios cambian cada día y son distintos en cada localidad"))


def desintoxicar(p):
    j = p.j
    if not j.adiccion:
        p.app.decir("No tienes ninguna dependencia.", True)
    elif p.pagar(800):
        j.adiccion = {}
        j.efectos = []
        p.pasar_horas(48)
        p.cambiar_animo(10)
        p.son("curar", cat="interfaz")
        p.app.decir(f"Dos días ingresado. Sales limpio y con la cabeza despejada. Es el día {p.dia}, las {p.hora_txt()}.", True)
