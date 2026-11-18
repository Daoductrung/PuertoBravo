"""Menús de la vida honrada y sus consecuencias: la consulta del móvil, los contratos fijos, los estudios con título,
la dirección de un negocio, los créditos y las obligaciones, los antecedentes y los asuntos pendientes."""
from .honrado import AJ, GRAVEDAD, NIVELES, _n
from .menus import Menu, Opcion

NIVEL_TXT = {"apagado": "apagado, como en versiones anteriores", "suave": "suave", "normal": "normal", "exigente": "exigente"}


def _abrir(p, titulo, ops, intro=None):
    m = Menu(p.app, titulo, ops, intro=intro)
    p.app.abrir(m)
    return m


def _en_servidor_txt(p):
    """Qué de todo esto existe en el servidor en el que estás: lo decide él, igual para todos."""
    if not p.en_servidor:
        return ""
    hay = [t for clave, t in (("nominas", "los contratos fijos, con la nómina que paga el servidor, y los antecedentes"),
                              ("trato_prestigio", "el trato de las tiendas según tu prestigio")) if p.sv_honrado(clave)]
    if not hay:
        return ". En un servidor en línea no cuentan"
    return ". En este servidor no cuenta tu nivel: lo decide el servidor, igual para todos. Aquí hay " + " y ".join(hay)


def _bloqueado(p, que=""):
    """En un servidor en línea no hay casi nada de lo que mueve dinero: lo dice y devuelve verdadero. Los contratos fijos
    («contrato») sí, donde el servidor paga las nóminas."""
    if p.hon_bloqueo(que):
        p.app.son("error")
        p.app.decir(p.hon_bloqueo(que), True)
        return True
    return False


# ====================================================================== el móvil: cómo te ven
def menu_vida(p):
    """Un solo sitio para saber cómo te ve la ciudad, cómo te ve la calle y qué ganas o pierdes por ello."""
    app, j = p.app, p.j
    h = p.hon()

    def ops():
        lista = [Opcion(p.hon_ciudad_txt, ayuda="El prestigio entre los vecinos sube con el trabajo honrado, los estudios, los donativos, el voluntariado y las buenas acciones. Baja con los delitos que te ven cometer y con las detenciones."),
                 Opcion(p.hon_calle_txt, ayuda="La fama en la calle sube con las misiones, los contratos y los barrios que conquistas. Es independiente del prestigio: puedes tener las dos cosas, una o ninguna."),
                 Opcion(lambda: "Antecedentes penales. " + p.hon_antecedentes_txt(), lambda: menu_antecedentes(p),
                        ayuda="Las condenas que constan en tu ficha, cuándo caducan y cómo atenuarlas. Cierran empleos de confianza, créditos y el ingreso en la policía."),
                 Opcion(lambda: "Trabajo. " + p.hon_contrato_txt(), lambda: menu_contrato(p),
                        ayuda="Tu contrato fijo, si lo tienes: jefe, turnos del periodo, nómina y avisos. Los contratos se firman en las oficinas de empleo."),
                 Opcion(lambda: "Estudios. " + estudios_txt(p), lambda: menu_estudios(p, None),
                        ayuda="Los títulos que tienes y los que estás sacando. Se estudian en las academias, una sesión al día, y abren puestos mejores y mejoras para tus negocios."),
                 Opcion(lambda: "Negocios. " + negocios_txt(p), lambda: menu_negocios(p), ayuda="Tus negocios: nivel, empleados, nombre entre la clientela y lo que dan. Se dirigen yendo a cada uno."),
                 Opcion(lambda: "Banco y obligaciones. " + banco_txt(p), lambda: menu_banco(p, None),
                        ayuda="Tus créditos e hipotecas, lo que te van a cobrar de facturas e impuestos y cuándo. Todo se cobra solo, con aviso dos días antes."),
                 Opcion(p.hon_doble_txt, ayuda="Si llevas las dos vidas a la vez, lo que se va sabiendo de ti. Sube cuando te ven delinquir, te detienen o una inspección te encuentra algo; baja con los días tranquilos."),
                 Opcion(lambda: f"Asuntos pendientes: {len(h['asuntos'])}" + (". " + p.hon_asunto_txt(h["asuntos"][0]) if h["asuntos"] else ""), lambda: menu_asuntos(p),
                        ayuda="Lo que espera una decisión tuya: una inspección con problemas, un periodista o una banda que pide dinero. Si se acaba el plazo, se resuelve solo."),
                 Opcion(p.hon_trama_txt, lambda: _marcar_trama(p), ayuda="La historia de prosperar honradamente en Puerto Bravo. Intro marca en el GPS dónde sigue, si ya cumples lo que pide.")]
        if h["fiado"]:
            lista.append(Opcion(lambda: f"Pagar lo que debes de fiado en las tiendas: {h['fiado']} euros", p.hon_pagar_fiado, ayuda="Si no lo pagas tú, se cobra solo con las facturas del periodo."))
        if h["embargo"]:
            lista.append(Opcion(lambda: f"Estás embargad[o|a]: debes {int(h['embargo'])} euros. Se quedan la mitad de tus nóminas y de lo que dan tus negocios", lambda: _saldar_embargo(p)))
        if p.hon_nivel():
            lista.append(Opcion(lambda: ("Tu abogado: lo tienes contratado" if p.hon_abogado() else f"Contratar a un abogado: {AJ.entero('abogado_semana')} euros a la semana"), p.hon_contratar_abogado,
                                ayuda="Mientras le pagues, lo que se sepa de tu otra vida hace la mitad de daño, frena a la prensa y puede recurrir las sanciones de una inspección. Se renueva solo cada semana; Intro otra vez lo despide."))
        lista.append(Opcion(lambda: f"Nivel de consecuencias: {NIVEL_TXT.get(p.cfg['consecuencias'], 'suave')}" + _en_servidor_txt(p),
                            ayuda="Se cambia en Opciones, en Vida, reputación y consecuencias. Apagado deja el juego como en versiones anteriores; suave es lo de serie."))
        return lista
    _abrir(p, "Vida, reputación y consecuencias", ops, "Cómo te ve la ciudad, cómo te ve la calle y qué estás ganando o perdiendo por ello")


def _marcar_trama(p):
    m, faltas, n, total = p.hon_trama()
    if m is None or faltas:
        return p.app.decir(p.hon_trama_txt(), True)
    while p.app.pila and p.app.pila[-1] is not p:
        p.app.cerrar(p.app.pila[-1])
    p.gps_a_lugar(p.lugares[m["lugar"]])


def _saldar_embargo(p):
    h = p.hon()
    total = int(h["embargo"])
    if total > p.j.dinero + p.j.banco:
        p.app.son("error")
        return p.app.decir(f"Para saldar la deuda de una vez hacen falta {total} euros entre la cuenta y el bolsillo.", True)
    p.hon_cobrar_de_cuentas(total)
    h["embargo"] = 0
    p.hon_decir(AJ.frase("frases_embargo_fin"), "prestigio")


# ====================================================================== antecedentes
def menu_antecedentes(p, lugar=None):
    """La ficha: qué consta, cuándo caduca y cómo atenuarlo. En comisaría o desde el móvil."""
    app = p.app

    def ops():
        vivos = p.hon_antecedentes()
        lista = [Opcion(p.hon_antecedentes_txt, ayuda="Cada detención y cada multa que pagas a un agente queda apuntada, más grave cuanto más te buscaban. Caducan solas con el tiempo.")]
        for a in vivos:
            lista.append(Opcion(p.hon_antecedente_txt(a) + f". Recurrirla con un abogado cuesta {p.hon_abogado_precio(a)} euros", (lambda a=a: (p.hon_rebajar(a), m.refrescar(False))),
                                ayuda="Intro paga a un abogado para que la recurra: baja un grado, o desaparece si era leve. Solo una vez por antecedente."))
        if vivos:
            lista.append(Opcion(f"Hacer servicios a la comunidad: {AJ.entero('servicio_horas')} horas", lambda: (p.hon_servicio_comunidad(), m.refrescar(False)),
                                ayuda=f"Sin cobrar. Le quita {AJ.entero('servicio_quita')} días al antecedente más grave y los vecinos lo ven con buenos ojos. Una vez al día."))
            lista.append(Opcion("Qué te cierran: " + cierres_txt(p)))
        elif p.hon_con_antecedentes():
            lista.append(Opcion(f"Plazos: una falta leve caduca a los {AJ.entero('caduca_leve')} días, una media a los {AJ.entero('caduca_media')} y una grave a los {AJ.entero('caduca_grave')}"))
        return lista
    m = _abrir(p, "Antecedentes penales", ops)


def cierres_txt(p):
    cosas = ["los empleos de confianza"]
    if p.hon_graves():
        cosas += ["los créditos y las hipotecas"]
    cosas.append("el ingreso en la policía")
    return ", ".join(cosas[:-1]) + " y " + cosas[-1] + ". Además, la policía te tiene fichad[o|a] y cada delito cuenta algo más."


# ====================================================================== trabajo: contratos fijos
def menu_contrato(p):
    j = p.j

    def dimitir():
        def si():
            p.app.cerrar(c)
            p.hon_dimitir()
            m.refrescar(False)
        c = Menu(p.app, "¿Dejas tu puesto?", [Opcion("Sí, presentar la dimisión", si, ayuda=f"Si llevas {AJ.entero('carta_periodos')} periodos o más y ningún aviso, te llevas una carta de recomendación."),
                                              Opcion("No, me quedo", lambda: p.app.cerrar(c))])
        p.app.abrir(c)

    def ops():
        ct = j.contrato
        lista = [Opcion(p.hon_contrato_txt)]
        if not ct:
            return lista + [Opcion("Los contratos fijos se firman en las oficinas de empleo. Sin contrato, trabajas cuando quieres, como siempre")]
        c = p.hon_empleo()
        k = int(ct["puesto"])
        if c:
            lista.append(Opcion("Cuentan como turno: " + cuenta_txt(p, c), ayuda="Una jornada es un turno. Con vehículo, tres servicios hacen un turno."))
            lista.append(Opcion(f"Tu jef[e|a], {ct['jefe']}, es {ct['caracter']}. Evaluaciones buenas que llevas para el ascenso: {ct['meritos']} de {AJ.entero('meritos_ascenso')}"
                                + (f". Última nota: {ct['nota']} de 100" if "nota" in ct else "")))
            if k + 1 < len(c["puestos"]):
                sig = c["puestos"][k + 1]
                falta = p.hon_puesto_falta(sig)
                lista.append(Opcion(f"Siguiente puesto: {sig['nombre']}, {int(_n(sig, 'sueldo'))} euros de nómina" + (f". Te falta {falta}" if falta else ". Cumples lo que pide")))
        lista.append(Opcion("Presentar la dimisión", dimitir))
        return lista
    m = _abrir(p, "Tu trabajo", ops)


def cuenta_txt(p, c):
    from .trabajos import NOMBRE_TRABAJO
    jornadas = {x["id"]: x["nombre"].lower() for x in p.datos.get("jornadas", [])}
    partes = []
    for clave in c.get("cuenta") or []:
        tipo, _, ident = clave.partition(":")
        partes.append(jornadas.get(ident, ident) if tipo == "jornada" else f"servicios de {NOMBRE_TRABAJO.get(ident, ident)}")
    return ", ".join(partes) or "nada"


def menu_empleos(p, l):
    """En la oficina de empleo: los contratos fijos."""
    if _bloqueado(p, "contrato"):
        return
    j = p.j

    def ficha(c):
        def ops():
            lista = [Opcion(f"{c['nombre']}, en {c['empresa']}. {c.get('desc', '')}"), Opcion("Cuentan como turno: " + cuenta_txt(p, c))]
            for k, pu in enumerate(c["puestos"]):
                pide = " y ".join(x for x in ((f"título de {p.hon_titulo_nombre(pu['titulo'])}" if pu.get("titulo") else ""), (f"prestigio {int(_n(pu, 'prestigio'))}" if _n(pu, "prestigio") else "")) if x)
                lista.append(Opcion(f"Puesto {k + 1}: {pu['nombre']}. {int(_n(pu, 'cupo', 3))} turnos por periodo, {int(_n(pu, 'sueldo'))} euros de nómina" + (f". Pide {pide}" if pide else "")
                                    + (". Con decisiones de responsabilidad" if pu.get("mando") else "")))
            motivo = p.hon_firma_motivo(c)
            lista.append(Opcion("Firmar el contrato" + (f". Ahora no puedes: {motivo}" if motivo else ""), lambda: p.hon_firmar(c) and (p.app.cerrar(mf), m.refrescar(False)),
                                ayuda=f"Te comprometes a un número de turnos cada {AJ.entero('periodo_dias')} días. Cobras cada turno como siempre y, al acabar el periodo, la nómina según tu evaluación. "
                                      f"Faltar o hacerlo mal trae avisos, y con {AJ.entero('avisos_despido')} avisos te despiden."))
            return lista
        mf = _abrir(p, c["nombre"], ops)

    def ops():
        lista = [Opcion(lambda: "Tu situación: " + p.hon_contrato_txt(), lambda: menu_contrato(p))]
        for c in p.hon_empleos():
            pu = c["puestos"][0]
            lista.append(Opcion(f"{c['nombre']}, en {c['empresa']}: empiezas de {pu['nombre']}, con {int(_n(pu, 'sueldo'))} euros de nómina por periodo" + (". Empleo de confianza" if c.get("confianza") else ""),
                                (lambda c=c: ficha(c)), ayuda=c.get("desc")))
        return lista
    m = _abrir(p, "Contratos fijos", ops, "Con un contrato tienes jefe, turnos que cumplir, nómina, evaluaciones y ascensos. Sin contrato, todo sigue como siempre"
               + (". En este servidor los turnos los cuenta el servidor y la nómina la paga él, con su calendario" if p.en_servidor else ""))


# ====================================================================== estudios
def estudios_txt(p):
    tengo = [p.hon_titulo_nombre(k) for k in p.hon_titulos()]
    cursando = [f"{p.hon_titulo_nombre(k)}, {v.get('s', 0)} sesiones" for k, v in p.j.titulos.items() if isinstance(v, dict) and not v.get("ok") and p.hon_titulo(k)]
    t = ("Tienes: " + ", ".join(tengo)) if tengo else "No tienes ningún título"
    return t + (". Estás sacando: " + "; ".join(cursando) if cursando else "")


def menu_estudios(p, l):
    """En una academia (o desde el móvil, solo para consultar): los títulos."""
    j = p.j

    def ops():
        lista = [Opcion(lambda: estudios_txt(p))]
        for t in p.datos.get("titulos", []):
            e = j.titulos.get(t["id"], {})
            total = int(_n(t, "sesiones", 4))
            if e.get("ok"):
                estado = "ya lo tienes"
            else:
                estado = f"llevas {int(e.get('s', 0))} de {total} sesiones; cada una, {int(_n(t, 'precio'))} euros y {int(_n(t, 'horas', 3))} horas"
            pide = " y ".join(x for x in ((f"el título de {p.hon_titulo_nombre(t['requiere'])}" if t.get("requiere") else ""), (f"prestigio {int(_n(t, 'prestigio'))}" if _n(t, "prestigio") else "")) if x)
            texto = f"{t['nombre']}: {estado}" + (f". Pide {pide}" if pide and not e.get("ok") else "")
            accion = (lambda t=t: (p.hon_estudiar(t), m.refrescar(False))) if l is not None else (lambda: p.app.decir("Las clases se dan en las academias: ve a una.", True))
            lista.append(Opcion(texto, accion, ayuda=f"{t.get('desc', '')} {t.get('abre', '')} Una sesión al día; se puede estudiar y trabajar el mismo día.".strip()))
        return lista
    m = _abrir(p, "Estudios con título" if l is not None else "Tus estudios", ops, "Cada título lleva varias sesiones, una al día. Al completarlas, es tuyo para siempre" if l is not None else None)


# ====================================================================== la empresa
def negocios_txt(p):
    negocios = p.negocios_tuyos()
    if not negocios:
        return "No tienes ninguno. Se compran yendo a ellos, al contado o con hipoteca"
    return f"Tienes {len(negocios)}, que dan {sum(p.ingreso_negocio(l) for l in negocios)} euros al día"


def menu_negocios(p):
    negocios = p.negocios_tuyos()
    ops = [Opcion(lambda l=l: f"{p.nombre_lugar(l)}. {p.hon_negocio_txt(l)}", (lambda l=l: (p.app.cerrar(m), p.gps_a_lugar(l)) if l.mapa == p.mundo.id else p.app.decir("Está en otra localidad.", True)),
                  ayuda="Intro lo marca en el GPS. Un negocio se dirige yendo a él.") for l in negocios]
    m = _abrir(p, "Tus negocios", ops or [Opcion("No tienes negocios")])


def opciones_negocio(p, l, refrescar):
    """Las opciones de dirección de un negocio tuyo, para su menú."""
    if p.en_servidor:
        return []
    e = p.hon_emp(l)
    p.hon_visitar(l)

    def mejora_txt():
        mj = p.hon_mejora(int(e["nivel"]) + 1)
        if not mj:
            return "Mejoras: el negocio ya está en su nivel más alto"
        motivo = p.hon_mejora_motivo(l)
        return f"Mejorar: {mj['nombre']}, por {p.hon_mejora_coste(l, mj)} euros. Sube lo que da un {int(_n(mj, 'ingresos'))} por ciento sobre la base y admite un empleado más" + (f". {motivo}" if motivo else "")

    def hacer(f, *a):
        return lambda: (f(l, *a), refrescar())
    ops = [Opcion(lambda: "Dirección. " + p.hon_negocio_txt(l), ayuda="Un negocio atendido rinde más y uno abandonado, menos. Su nombre entre la clientela sube si pasas por aquí, si echas horas y con precios bajos."),
           Opcion(f"Echar {AJ.entero('atender_horas')} horas en el negocio", hacer(p.hon_atender), ayuda="Atiendes tú: sube el nombre del negocio. Una vez al día en cada negocio."),
           Opcion(mejora_txt, hacer(p.hon_mejorar), ayuda="Cada nivel hace que el negocio dé más y admita más gente. Los niveles altos piden un título de gestión y buen prestigio."),
           Opcion(lambda: f"Contratar a un empleado. Tienes {e['emp']} de {p.hon_max_empleados(e)}", hacer(p.hon_empleado, 1),
                  ayuda=f"Cada empleado cobra al día un {AJ.entero('empleado_sueldo')} por ciento de lo que da el negocio de base y hace que dé un {AJ.entero('empleado_rinde')} por ciento más. "
                        "Con gente contratada, el negocio aguanta aunque tú no pases."),
           Opcion("Despedir a un empleado", hacer(p.hon_empleado, -1)),
           Opcion(lambda: f"Precios: {e['precios']}", hacer(p.hon_precios), ayuda="Intro cambia entre bajos, normales y altos. Bajos: ganas menos y sube el nombre. Altos: ganas más y baja."),
           Opcion(lambda: f"Horario: {e['horario']}", hacer(p.hon_horario), ayuda=f"Con horario ampliado da un {AJ.entero('horario_ingreso')} por ciento más, pero necesitas al menos un empleado.")]
    if p.hon_nivel():
        ops.append(Opcion(lambda: "Tapadera: " + ("sí, blanquea tu dinero sin justificar" if e["tapadera"] else "no, es un negocio limpio"), hacer(p.hon_tapadera),
                          ayuda="Para quien lleva doble vida. Cada medianoche pasa por la caja parte del dinero que no podrías justificar, a cambio de una comisión. "
                                "Si una inspección lo encuentra: sanción, y si intentas sobornar y sale mal, antecedentes y portada en el periódico."))
    return ops


def opcion_hipoteca(p, l, al_comprar):
    """La opción de comprar una casa o un negocio con hipoteca, para su menú de compra."""
    if p.en_servidor or int(l.get("precio", 0)) <= 0:
        return []

    def comprar():
        if p.hon_hipoteca(l):
            if l.tipo == "negocio":
                p.hon_emp(l)
            al_comprar()

    def texto():
        entrada, cuota, n = p.hon_hipoteca_datos(l)
        motivo = p.hon_credito_motivo("hipoteca")
        return f"Comprar con hipoteca: {entrada} euros de entrada y {n} cuotas de {cuota}" + (". Ahora no te la dan" if motivo else "")
    return [Opcion(texto, comprar, ayuda=f"El banco pone el resto y lo devuelves en cuotas, una cada {AJ.entero('cuota_dias')} días, con aviso antes de cada una. "
                                         "Hace falta buena solvencia: prestigio, una nómina o un negocio, y nada de antecedentes graves.")]


# ====================================================================== banco y obligaciones
def banco_txt(p):
    j, h = p.j, p.hon()
    partes = []
    if j.creditos:
        partes.append(f"{len(j.creditos)} {'crédito' if len(j.creditos) == 1 else 'créditos'} en marcha")
    partes.append(p.hon_cobro_txt().rstrip("."))
    if h["embargo"]:
        partes.append(f"embargo de {int(h['embargo'])} euros")
    return ". ".join(partes)


def menu_banco(p, l):
    """Créditos, hipotecas y lo que hay que pagar. En un banco se piden; desde el móvil, solo se consulta y se liquida."""
    j = p.j

    def pedir(n):
        return lambda: (p.hon_pedir_credito(n), m.refrescar(False))

    def ops():
        lista = [Opcion(lambda: f"Tu solvencia para el banco es {p.hon_solvencia_txt()}. Ingresos estables: {p.hon_ingresos_semana()} euros por semana",
                        ayuda="Sube con el prestigio entre los vecinos, con una nómina, con negocios y con créditos devueltos. Baja con antecedentes, impagos y embargos."),
                 Opcion(p.hon_cobro_txt, ayuda=f"Cada {AJ.entero('cobro_dias')} días se cobran la luz y el agua de tus casas, su contribución y el impuesto de lo que han dado tus negocios. "
                                               "Se cobra solo, primero del banco. Si no llega, queda a deber con recargo; a los tres impagos, embargo.")]
        for c in j.creditos:
            lista.append(Opcion((lambda c=c: p.hon_credito_txt(c) + f". Liquidarlo ahora cuesta {int(c['cuota'] * c['quedan'] * 0.95 + c.get('atraso', 0))} euros"),
                                (lambda c=c: (p.hon_liquidar(c), m.refrescar(False))), ayuda="Intro paga de una vez lo que queda, con un cinco por ciento de rebaja."))
        if l is not None and not p.hon_bloqueo():
            motivo = p.hon_credito_motivo()
            if motivo:
                lista.append(Opcion("Crédito personal: " + motivo))
            else:
                maximo = p.hon_credito_maximo()
                interes, n = int(p.hon_interes()), AJ.entero("credito_cuotas")
                for importe in sorted({maximo // 4 // 100 * 100, maximo // 2 // 100 * 100, maximo}):
                    if importe >= 300:
                        cuota = int(importe * (1.0 + interes / 100.0) / n) + 1
                        lista.append(Opcion(f"Pedir un crédito de {importe} euros: {n} cuotas de {cuota}", pedir(importe),
                                            ayuda=f"Interés del {interes} por ciento, según tu solvencia. Una cuota cada {AJ.entero('cuota_dias')} días, que se cobra sola."))
            lista.append(Opcion("Las hipotecas se piden al comprar: ve a la casa o al negocio que quieras y elige comprar con hipoteca"))
        elif l is None:
            lista.append(Opcion("Los créditos se piden en un banco"))
        return lista
    m = _abrir(p, "Créditos, hipotecas y obligaciones", ops)


# ====================================================================== asuntos pendientes
def menu_asuntos(p):
    h = p.hon()

    def abrir(a):
        def hacer(clave):
            def f():
                p.app.cerrar(ma)
                p.hon_resolver(a, clave)
                m.refrescar(False)
            return f
        ma = _abrir(p, p.hon_asunto_txt(a), [Opcion(texto, hacer(clave), ayuda=ayuda) for clave, texto, ayuda in p.hon_asunto_opciones(a)], "F1 explica cada salida")

    def ops():
        return [Opcion(p.hon_asunto_txt(a), (lambda a=a: abrir(a)), ayuda="Intro para decidir qué haces.") for a in h["asuntos"]] or [Opcion("No tienes ningún asunto pendiente")]
    m = _abrir(p, "Asuntos pendientes", ops)


__all__ = ["menu_vida", "menu_antecedentes", "menu_contrato", "menu_empleos", "menu_estudios", "menu_negocios", "opciones_negocio", "opcion_hipoteca", "menu_banco", "menu_asuntos",
           "GRAVEDAD", "NIVELES"]
