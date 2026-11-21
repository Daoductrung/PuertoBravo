"""Esquema del editor para los golpes preparados con la banda: los papeles, los números y las frases de la radio."""
from juego.i18n import tr
from juego.golpes import AJ, ATRIBUTOS, EFECTOS


def c(k, e, t="texto", ayuda="", **kw):
    d = {"k": k, "e": e, "t": t, "ayuda": ayuda}
    d.update(kw)
    return d


# clave: (etiqueta, pestaña, ayuda, mínimo, máximo)
_NUMEROS = {
    "radio_presentes": (tr("Metros a los que cuenta que uno de los tuyos está contigo"), tr("General"), tr("Solo se puede dar papel a quien esté a esa distancia o menos."), 5, 500),
    "radio_vehiculo": (tr("Metros a los que vale un vehículo tuyo para la huida"), tr("General"), "", 5, 1000),
    "atributo_min": (tr("Lo menos que vale alguien recién reclutado, de 0 a 100"), tr("General"), tr("Puntería, conducción y nervios se sortean entre el mínimo y el máximo."), 1, 100),
    "atributo_max": (tr("Y lo más"), tr("General"), "", 1, 100),
    "exp_bono": (tr("Puntos que gana en todo con cada golpe que sale bien"), tr("General"), "", 0, 50),
    "exp_max": (tr("Hasta cuántos golpes sigue aprendiendo"), tr("General"), "", 0, 100),
    "reparto_tope": (tr("Lo más que se lleva tu gente entre todos, por ciento del botín"), tr("General"), tr("Si las partes de los papeles suman más, se encogen en proporción."), 0, 100),
    "lealtad_exito": (tr("Lealtad que ganan cuando el golpe sale bien"), tr("General"), "", 0, 100),
    "lealtad_fracaso": (tr("Lealtad que pierden cuando fracasa"), tr("General"), tr("Quien se queda sin ninguna, deja la banda."), 0, 100),
    "charla_lealtad": (tr("Lealtad que gana uno de los tuyos al hablar con él"), tr("Tu gente"), tr("Desde Tu gente, uno por uno. Una vez al día."), 0, 100),
    "invitar_precio": (tr("Lo que cuesta invitarle a algo, en euros"), tr("Tu gente"), "", 0, 100000),
    "invitar_lealtad": (tr("Lealtad que gana al invitarle"), tr("Tu gente"), "", 0, 100),
    "paga_precio": (tr("La paga extra, en euros"), tr("Tu gente"), "", 0, 1000000),
    "paga_lealtad": (tr("Lealtad que gana con la paga"), tr("Tu gente"), "", 0, 100),
    "caja_min": (tr("Segundos que tarda una caja, como poco"), tr("La caja"), tr("Para los locales que no estén en la lista de tiempos."), 1, 600),
    "caja_max": (tr("Y como mucho"), tr("La caja"), "", 1, 600),
    "caja_radio": (tr("Metros a los que tienes que estar si la abres tú"), tr("La caja"), "", 1, 50),
    "cubrir_radio": (tr("Metros a los que tienes que estar si cubres a quien la abre"), tr("La caja"), "", 1, 200),
    "caja_ayuda": (tr("Lo que acorta el de la caja, por ciento, si valiera cien"), tr("La caja"), tr("Con 50 y un 60 de nervios, la caja tarda un 30 por ciento menos."), 0, 75),
    "caja_nervios": (tr("Lo que la alarga si le fallan los nervios, por ciento"), tr("La caja"), "", 0, 500),
    "vigilante_retraso": (tr("Segundos que entretiene el vigilante a la policía"), tr("Policía y huida"), tr("Con alguien que valga 100 es un cuarto más; con alguien que valga 0, la mitad."), 0, 600),
    "vigilante_aviso": (tr("Segundos antes de que lleguen a los que avisa otra vez"), tr("Policía y huida"), "", 0, 120),
    "conductor_ventaja": (tr("Segundos de más que gana el conductor si aún no han llegado"), tr("Policía y huida"), "", 0, 600),
    "conductor_nivel": (tr("Si ya te buscan: probabilidad de que te quite un nivel, por ciento"), tr("Policía y huida"), tr("Para un conductor que valga 100; con menos, menos."), 0, 100),
    "tirador_cada": (tr("Segundos entre disparo y disparo del tirador"), tr("Policía y huida"), "", 0.3, 60),
    "tirador_alcance": (tr("Metros a los que alcanza"), tr("Policía y huida"), "", 5, 300),
    "tirador_dano": (tr("Daño de cada acierto"), tr("Policía y huida"), "", 0, 500),
    "heroe_prob": (tr("Probabilidad de que alguien se haga el héroe, por ciento"), tr("Lo que sale mal"), "", 0, 100),
    "heroe_escolta": (tr("Cuánto lo evita un escolta que valga 100, por ciento"), tr("Lo que sale mal"), "", 0, 100),
    "alarma_prob": (tr("Probabilidad de que den la alarma antes de tiempo, por ciento"), tr("Lo que sale mal"), "", 0, 100),
    "alarma_escolta": (tr("Cuánto lo evita un escolta que valga 100, por ciento"), tr("Lo que sale mal"), "", 0, 100),
    "fallo_base": (tr("Probabilidad de que a alguien sin nervios le fallen, por ciento"), tr("Lo que sale mal"), tr("Baja con sus nervios: con 100 no falla nunca."), 0, 100),
    "herido_prob": (tr("Probabilidad de que hieran al escolta si hay guardia, por ciento"), tr("Lo que sale mal"), "", 0, 100),
    "herido_dias_min": (tr("Días de baja del herido, como poco"), tr("Lo que sale mal"), "", 1, 365),
    "herido_dias_max": (tr("Y como mucho"), tr("Lo que sale mal"), "", 1, 365),
    "detenido_prob": (tr("Probabilidad de que detengan al vigilante, por ciento"), tr("Detenidos"), "", 0, 100),
    "delata_lealtad": (tr("Lealtad por debajo de la cual un detenido da tu nombre"), tr("Detenidos"), "", 0, 101),
    "delata_busqueda": (tr("Niveles de búsqueda que sube entonces"), tr("Detenidos"), tr("Además deja un antecedente, si los antecedentes están activados."), 0, 4),
    "tarde_min": (tr("Segundos que se retrasa el conductor que llega tarde, como poco"), tr("Detenidos"), tr("Cuentan desde que acabas con la caja."), 1, 600),
    "tarde_max": (tr("Y como mucho"), tr("Detenidos"), "", 1, 600),
}
_ENTEROS = ("invitar_precio", "paga_precio", "radio_presentes", "radio_vehiculo", "atributo_min", "atributo_max", "exp_max", "herido_dias_min", "herido_dias_max", "delata_busqueda")
# clave: (etiqueta, pestaña, huecos)
_FRASES = {
    "frases_charla_banda": (tr("Hablas con uno de los tuyos"), tr("Tu gente"), "{nombre}"),
    "frases_invitar_banda": (tr("Le invitas a algo"), tr("Tu gente"), "{nombre}"),
    "frases_paga_banda": (tr("Le das la paga extra"), tr("Tu gente"), tr("{nombre} y {euros}")),
    "frases_echar_banda": (tr("Le echas de la banda"), tr("Tu gente"), "{nombre}"),
    "tiempos_caja": (tr("Segundos de la caja según el tipo de local"), tr("La caja"), tr("Uno por línea: el nombre interno del tipo, un signo igual y los segundos. Por ejemplo, banco=26.")),
    "vehiculos": (tr("Vehículos de la banda para la huida"), tr("General"), ""),
    "frases_entrada": (tr("Fase uno, entrada"), tr("Fases"), ""),
    "frases_control": (tr("Fase dos, control, con guardia"), tr("Fases"), tr("Va delante de la frase del atraco.")),
    "frases_control_sin_guardia": (tr("Fase dos, control, sin guardia"), tr("Fases"), ""),
    "frases_caja": (tr("Fase tres, la caja"), tr("Fases"), ""),
    "frases_salida": (tr("Fase cuatro, salida"), tr("Fases"), ""),
    "frases_huida": (tr("Fase cinco, huida"), tr("Fases"), ""),
    "radio_conductor_listo": (tr("Está en la puerta"), tr("Radio del conductor"), ""),
    "radio_conductor_tarde": (tr("Avisa de que llega tarde"), tr("Radio del conductor"), ""),
    "radio_conductor_llega": (tr("Llega por fin"), tr("Radio del conductor"), ""),
    "radio_conductor_ventaja": (tr("Te da ventaja"), tr("Radio del conductor"), ""),
    "radio_conductor_sin_ventaja": (tr("Le fallan los nervios: sin ventaja"), tr("Radio del conductor"), ""),
    "radio_conductor_tu": (tr("Conduces tú"), tr("Radio del conductor"), ""),
    "radio_vigilante_listo": (tr("Está en su sitio"), tr("Radio del vigilante"), ""),
    "radio_vigilante_alarma": (tr("Salta la alarma"), tr("Radio del vigilante"), "{segundos}"),
    "radio_vigilante_cerca": (tr("Ya vienen"), tr("Radio del vigilante"), "{segundos}"),
    "radio_vigilante_llegan": (tr("Ya están aquí"), tr("Radio del vigilante"), ""),
    "radio_vigilante_falla": (tr("No los ha visto venir"), tr("Radio del vigilante"), ""),
    "frases_vigilante_detenido": (tr("Lo detienen"), tr("Detenidos"), "{nombre}"),
    "frases_delata": (tr("Da tu nombre"), tr("Detenidos"), "{nombre}"),
    "frases_no_delata": (tr("No dice nada"), tr("Detenidos"), "{nombre}"),
    "radio_escolta_control": (tr("Se ocupa de la gente"), tr("Radio del escolta"), ""),
    "radio_escolta_heroe": (tr("Ha parado a uno que iba a por ti"), tr("Radio del escolta"), ""),
    "radio_escolta_alarma": (tr("Ha evitado la alarma"), tr("Radio del escolta"), ""),
    "frases_escolta_herido": (tr("Lo hieren"), tr("Radio del escolta"), "{nombre}"),
    "frases_heroe": (tr("Alguien se hace el héroe"), tr("Radio del escolta"), ""),
    "frases_alarma": (tr("Dan la alarma antes de tiempo"), tr("Radio del escolta"), ""),
    "radio_caja_empieza": (tr("Empieza con la caja, él solo"), tr("Radio de la caja"), "{segundos}"),
    "radio_caja_ayuda": (tr("Te ayuda con la caja"), tr("Radio de la caja"), ""),
    "radio_caja_mitad": (tr("Va por la mitad"), tr("Radio de la caja"), ""),
    "radio_caja_hecho": (tr("Abierta"), tr("Radio de la caja"), ""),
    "radio_caja_nervios": (tr("Le fallan los nervios"), tr("Radio de la caja"), ""),
    "radio_caja_solo": (tr("Te has alejado y no sigue"), tr("Radio de la caja"), ""),
    "radio_tirador_dispara": (tr("El tirador empieza a disparar"), tr("Final"), ""),
    "radio_tirador_acierta": (tr("Acierta"), tr("Final"), ""),
    "frases_reparto": (tr("El reparto"), tr("Final"), tr("{partes}, {neto} y {botin}")),
    "frases_se_va": (tr("Alguien deja la banda tras un fracaso"), tr("Final"), "{nombre}"),
}


def _campos_ajuste():
    campos = [c("id", tr("Identificador"), req=True, defecto="general", ayuda=tr("Déjalo en general: solo se usa el primero."))]
    for k, serie in AJ._n.items():
        e, grupo, ayuda, minimo, maximo = _NUMEROS[k]
        campos.append(c(k, e, "entero" if k in _ENTEROS else "decimal", ayuda, minimo=minimo, maximo=maximo,
                        defecto=int(serie) if float(serie).is_integer() else serie, **({} if grupo == "General" else {"grupo": grupo})))
    for k in AJ._l:
        e, grupo, huecos = _FRASES[k]
        if k == "vehiculos":
            campos.append(c(k, e, "refs", tr("Si lo dejas vacío, valen los del chófer de la banda."), ref="modelo"))
        elif k == "tiempos_caja":
            campos.append(c(k, e, "textos", huecos, grupo=grupo))
        else:
            campos.append(c(k, e, "textos", (tr("Una por línea; se dice una al azar. ") + (tr("Huecos: ") + huecos + "." if huecos.startswith("{") else huecos)).strip(), grupo=grupo))
    return campos


ESQUEMAS = {
    "ajuste_golpes": {"titulo": tr("Golpes preparados: números y frases"),
                      "resumen": lambda d: tr('La caja tarda de {get} a {get2} segundos; el vigilante entretiene {get3}').format(get=(d.get('caja_min', 8)), get2=(d.get('caja_max', 16)), get3=(d.get('vigilante_retraso', 22))),
                      "campos": _campos_ajuste()},
    "papel_golpe": {"titulo": tr("Papel de un golpe"), "resumen": lambda d: tr('{get}: {get2} por ciento del botín').format(get=(d.get('nombre', '?')), get2=(d.get('parte', 0))), "campos": [
        c("id", tr("Identificador"), req=True, ayuda=tr("Una palabra sin espacios. Los de serie son conductor, vigilante, escolta, caja y tirador: con el mismo identificador, tu mod cambia ese papel.")),
        c("nombre", tr("Nombre"), req=True, ayuda=tr("Como sale en el menú de preparar el golpe.")),
        c("efecto", tr("Lo que hace"), "opcion", tr("Lo que hace en el golpe. Puedes tener varios papeles con el mismo efecto, pero en cada golpe solo uno de ellos lo hace."), req=True, defecto="vigilante",
          ops=[("conductor", tr("Espera fuera con el vehículo en marcha y da ventaja en la huida")), ("vigilante", tr("Entretiene a la policía y avisa de cuánto falta")),
               ("escolta", tr("Tiene a raya a la gente: menos héroes y menos alarmas")), ("caja", tr("Abre la caja más deprisa, o él solo")), ("tirador", tr("Dispara desde el vehículo en la huida"))]),
        c("atributo", tr("De qué depende lo bien que lo hace"), "opcion", req=True, defecto="nervios", ops=[(k, v.capitalize()) for k, v in ATRIBUTOS.items()]),
        c("parte", tr("Parte del botín que se lleva, por ciento"), "decimal", minimo=0, maximo=100, defecto=8),
        c("desc", tr("Explicación"), "largo", tr("Se lee en el menú y en «Cómo funciona esto».")),
    ]},
}
SECCIONES = [("golpes", tr("Golpes preparados: números y frases"), "ajuste_golpes"), ("papeles_golpe", tr("Papeles de un golpe"), "papel_golpe")]
CAMPOS_PASO = [
    c("tarda", tr("Segundos que tarda en abrirse o cogerse"), "decimal", tr("Con cero, se coge al momento. Con más, al pulsar Intro empieza a abrirse, se oye cómo avanza y el jugador tiene que quedarse al lado hasta que ceda. "
      "Sirve para cajas fuertes, cámaras y cerraduras."), si=lambda d: d.get("tipo") == "recoger", minimo=0, maximo=600),
    c("retraso", tr("Segundos que tarda en llegar la policía"), "decimal", tr("Con cero, el nivel de búsqueda cae al momento. Con más, el jugador tiene ese tiempo para alejarse antes de que empiecen a buscarle."),
      si=lambda d: d.get("tipo") == "policia", minimo=0, maximo=600),
]
assert set(EFECTOS) == {"conductor", "vigilante", "escolta", "caja", "tirador"}


def aplicar(esquemas, secciones):
    esquemas.update(ESQUEMAS)
    paso = esquemas["paso"]["campos"]
    paso.insert(next(k for k, x in enumerate(paso) if x["k"] == "aqui") + 1, CAMPOS_PASO[0])
    paso.insert(next(k for k, x in enumerate(paso) if x["k"] == "nivel") + 1, CAMPOS_PASO[1])
    pos = next(k for k, x in enumerate(secciones) if x[0] == "atracos") + 1
    secciones[pos:pos] = SECCIONES
