"""Esquema del editor para los golpes preparados con la banda: los papeles, los números y las frases de la radio."""
from juego.golpes import AJ, ATRIBUTOS, EFECTOS


def c(k, e, t="texto", ayuda="", **kw):
    d = {"k": k, "e": e, "t": t, "ayuda": ayuda}
    d.update(kw)
    return d


# clave: (etiqueta, pestaña, ayuda, mínimo, máximo)
_NUMEROS = {
    "radio_presentes": ("Metros a los que cuenta que uno de los tuyos está contigo", "General", "Solo se puede dar papel a quien esté a esa distancia o menos.", 5, 500),
    "radio_vehiculo": ("Metros a los que vale un vehículo tuyo para la huida", "General", "", 5, 1000),
    "atributo_min": ("Lo menos que vale alguien recién reclutado, de 0 a 100", "General", "Puntería, conducción y nervios se sortean entre el mínimo y el máximo.", 1, 100),
    "atributo_max": ("Y lo más", "General", "", 1, 100),
    "exp_bono": ("Puntos que gana en todo con cada golpe que sale bien", "General", "", 0, 50),
    "exp_max": ("Hasta cuántos golpes sigue aprendiendo", "General", "", 0, 100),
    "reparto_tope": ("Lo más que se lleva tu gente entre todos, por ciento del botín", "General", "Si las partes de los papeles suman más, se encogen en proporción.", 0, 100),
    "lealtad_exito": ("Lealtad que ganan cuando el golpe sale bien", "General", "", 0, 100),
    "lealtad_fracaso": ("Lealtad que pierden cuando fracasa", "General", "Quien se queda sin ninguna, deja la banda.", 0, 100),
    "caja_min": ("Segundos que tarda una caja, como poco", "La caja", "Para los locales que no estén en la lista de tiempos.", 1, 600),
    "caja_max": ("Y como mucho", "La caja", "", 1, 600),
    "caja_radio": ("Metros a los que tienes que estar si la abres tú", "La caja", "", 1, 50),
    "cubrir_radio": ("Metros a los que tienes que estar si cubres a quien la abre", "La caja", "", 1, 200),
    "caja_ayuda": ("Lo que acorta el de la caja, por ciento, si valiera cien", "La caja", "Con 50 y un 60 de nervios, la caja tarda un 30 por ciento menos.", 0, 75),
    "caja_nervios": ("Lo que la alarga si le fallan los nervios, por ciento", "La caja", "", 0, 500),
    "vigilante_retraso": ("Segundos que entretiene el vigilante a la policía", "Policía y huida", "Con alguien que valga 100 es un cuarto más; con alguien que valga 0, la mitad.", 0, 600),
    "vigilante_aviso": ("Segundos antes de que lleguen a los que avisa otra vez", "Policía y huida", "", 0, 120),
    "conductor_ventaja": ("Segundos de más que gana el conductor si aún no han llegado", "Policía y huida", "", 0, 600),
    "conductor_nivel": ("Si ya te buscan: probabilidad de que te quite un nivel, por ciento", "Policía y huida", "Para un conductor que valga 100; con menos, menos.", 0, 100),
    "tirador_cada": ("Segundos entre disparo y disparo del tirador", "Policía y huida", "", 0.3, 60),
    "tirador_alcance": ("Metros a los que alcanza", "Policía y huida", "", 5, 300),
    "tirador_dano": ("Daño de cada acierto", "Policía y huida", "", 0, 500),
    "heroe_prob": ("Probabilidad de que alguien se haga el héroe, por ciento", "Lo que sale mal", "", 0, 100),
    "heroe_escolta": ("Cuánto lo evita un escolta que valga 100, por ciento", "Lo que sale mal", "", 0, 100),
    "alarma_prob": ("Probabilidad de que den la alarma antes de tiempo, por ciento", "Lo que sale mal", "", 0, 100),
    "alarma_escolta": ("Cuánto lo evita un escolta que valga 100, por ciento", "Lo que sale mal", "", 0, 100),
    "fallo_base": ("Probabilidad de que a alguien sin nervios le fallen, por ciento", "Lo que sale mal", "Baja con sus nervios: con 100 no falla nunca.", 0, 100),
    "herido_prob": ("Probabilidad de que hieran al escolta si hay guardia, por ciento", "Lo que sale mal", "", 0, 100),
    "herido_dias_min": ("Días de baja del herido, como poco", "Lo que sale mal", "", 1, 365),
    "herido_dias_max": ("Y como mucho", "Lo que sale mal", "", 1, 365),
    "detenido_prob": ("Probabilidad de que detengan al vigilante, por ciento", "Detenidos", "", 0, 100),
    "delata_lealtad": ("Lealtad por debajo de la cual un detenido da tu nombre", "Detenidos", "", 0, 101),
    "delata_busqueda": ("Niveles de búsqueda que sube entonces", "Detenidos", "Además deja un antecedente, si los antecedentes están activados.", 0, 4),
    "tarde_min": ("Segundos que se retrasa el conductor que llega tarde, como poco", "Detenidos", "Cuentan desde que acabas con la caja.", 1, 600),
    "tarde_max": ("Y como mucho", "Detenidos", "", 1, 600),
}
_ENTEROS = ("radio_presentes", "radio_vehiculo", "atributo_min", "atributo_max", "exp_max", "herido_dias_min", "herido_dias_max", "delata_busqueda")
# clave: (etiqueta, pestaña, huecos)
_FRASES = {
    "tiempos_caja": ("Segundos de la caja según el tipo de local", "La caja", "Uno por línea: el nombre interno del tipo, un signo igual y los segundos. Por ejemplo, banco=26."),
    "vehiculos": ("Vehículos de la banda para la huida", "General", ""),
    "frases_entrada": ("Fase uno, entrada", "Fases", ""),
    "frases_control": ("Fase dos, control, con guardia", "Fases", "Va delante de la frase del atraco."),
    "frases_control_sin_guardia": ("Fase dos, control, sin guardia", "Fases", ""),
    "frases_caja": ("Fase tres, la caja", "Fases", ""),
    "frases_salida": ("Fase cuatro, salida", "Fases", ""),
    "frases_huida": ("Fase cinco, huida", "Fases", ""),
    "radio_conductor_listo": ("Está en la puerta", "Radio del conductor", ""),
    "radio_conductor_tarde": ("Avisa de que llega tarde", "Radio del conductor", ""),
    "radio_conductor_llega": ("Llega por fin", "Radio del conductor", ""),
    "radio_conductor_ventaja": ("Te da ventaja", "Radio del conductor", ""),
    "radio_conductor_sin_ventaja": ("Le fallan los nervios: sin ventaja", "Radio del conductor", ""),
    "radio_conductor_tu": ("Conduces tú", "Radio del conductor", ""),
    "radio_vigilante_listo": ("Está en su sitio", "Radio del vigilante", ""),
    "radio_vigilante_alarma": ("Salta la alarma", "Radio del vigilante", "{segundos}"),
    "radio_vigilante_cerca": ("Ya vienen", "Radio del vigilante", "{segundos}"),
    "radio_vigilante_llegan": ("Ya están aquí", "Radio del vigilante", ""),
    "radio_vigilante_falla": ("No los ha visto venir", "Radio del vigilante", ""),
    "frases_vigilante_detenido": ("Lo detienen", "Detenidos", "{nombre}"),
    "frases_delata": ("Da tu nombre", "Detenidos", "{nombre}"),
    "frases_no_delata": ("No dice nada", "Detenidos", "{nombre}"),
    "radio_escolta_control": ("Se ocupa de la gente", "Radio del escolta", ""),
    "radio_escolta_heroe": ("Ha parado a uno que iba a por ti", "Radio del escolta", ""),
    "radio_escolta_alarma": ("Ha evitado la alarma", "Radio del escolta", ""),
    "frases_escolta_herido": ("Lo hieren", "Radio del escolta", "{nombre}"),
    "frases_heroe": ("Alguien se hace el héroe", "Radio del escolta", ""),
    "frases_alarma": ("Dan la alarma antes de tiempo", "Radio del escolta", ""),
    "radio_caja_empieza": ("Empieza con la caja, él solo", "Radio de la caja", "{segundos}"),
    "radio_caja_ayuda": ("Te ayuda con la caja", "Radio de la caja", ""),
    "radio_caja_mitad": ("Va por la mitad", "Radio de la caja", ""),
    "radio_caja_hecho": ("Abierta", "Radio de la caja", ""),
    "radio_caja_nervios": ("Le fallan los nervios", "Radio de la caja", ""),
    "radio_caja_solo": ("Te has alejado y no sigue", "Radio de la caja", ""),
    "radio_tirador_dispara": ("El tirador empieza a disparar", "Final", ""),
    "radio_tirador_acierta": ("Acierta", "Final", ""),
    "frases_reparto": ("El reparto", "Final", "{partes}, {neto} y {botin}"),
    "frases_se_va": ("Alguien deja la banda tras un fracaso", "Final", "{nombre}"),
}


def _campos_ajuste():
    campos = [c("id", "Identificador", req=True, defecto="general", ayuda="Déjalo en general: solo se usa el primero.")]
    for k, serie in AJ._n.items():
        e, grupo, ayuda, minimo, maximo = _NUMEROS[k]
        campos.append(c(k, e, "entero" if k in _ENTEROS else "decimal", ayuda, minimo=minimo, maximo=maximo,
                        defecto=int(serie) if float(serie).is_integer() else serie, **({} if grupo == "General" else {"grupo": grupo})))
    for k in AJ._l:
        e, grupo, huecos = _FRASES[k]
        if k == "vehiculos":
            campos.append(c(k, e, "refs", "Si lo dejas vacío, valen los del chófer de la banda.", ref="modelo"))
        elif k == "tiempos_caja":
            campos.append(c(k, e, "textos", huecos, grupo=grupo))
        else:
            campos.append(c(k, e, "textos", ("Una por línea; se dice una al azar. " + ("Huecos: " + huecos + "." if huecos.startswith("{") else huecos)).strip(), grupo=grupo))
    return campos


ESQUEMAS = {
    "ajuste_golpes": {"titulo": "Golpes preparados: números y frases",
                      "resumen": lambda d: f"La caja tarda de {d.get('caja_min', 8)} a {d.get('caja_max', 16)} segundos; el vigilante entretiene {d.get('vigilante_retraso', 22)}",
                      "campos": _campos_ajuste()},
    "papel_golpe": {"titulo": "Papel de un golpe", "resumen": lambda d: f"{d.get('nombre', '?')}: {d.get('parte', 0)} por ciento del botín", "campos": [
        c("id", "Identificador", req=True, ayuda="Una palabra sin espacios. Los de serie son conductor, vigilante, escolta, caja y tirador: con el mismo identificador, tu mod cambia ese papel."),
        c("nombre", "Nombre", req=True, ayuda="Como sale en el menú de preparar el golpe."),
        c("efecto", "Lo que hace", "opcion", "Lo que hace en el golpe. Puedes tener varios papeles con el mismo efecto, pero en cada golpe solo uno de ellos lo hace.", req=True, defecto="vigilante",
          ops=[("conductor", "Espera fuera con el vehículo en marcha y da ventaja en la huida"), ("vigilante", "Entretiene a la policía y avisa de cuánto falta"),
               ("escolta", "Tiene a raya a la gente: menos héroes y menos alarmas"), ("caja", "Abre la caja más deprisa, o él solo"), ("tirador", "Dispara desde el vehículo en la huida")]),
        c("atributo", "De qué depende lo bien que lo hace", "opcion", req=True, defecto="nervios", ops=[(k, v.capitalize()) for k, v in ATRIBUTOS.items()]),
        c("parte", "Parte del botín que se lleva, por ciento", "decimal", minimo=0, maximo=100, defecto=8),
        c("desc", "Explicación", "largo", "Se lee en el menú y en «Cómo funciona esto»."),
    ]},
}
SECCIONES = [("golpes", "Golpes preparados: números y frases", "ajuste_golpes"), ("papeles_golpe", "Papeles de un golpe", "papel_golpe")]
CAMPOS_PASO = [
    c("tarda", "Segundos que tarda en abrirse o cogerse", "decimal", "Con cero, se coge al momento. Con más, al pulsar Intro empieza a abrirse, se oye cómo avanza y el jugador tiene que quedarse al lado hasta que ceda. "
      "Sirve para cajas fuertes, cámaras y cerraduras.", si=lambda d: d.get("tipo") == "recoger", minimo=0, maximo=600),
    c("retraso", "Segundos que tarda en llegar la policía", "decimal", "Con cero, el nivel de búsqueda cae al momento. Con más, el jugador tiene ese tiempo para alejarse antes de que empiecen a buscarle.",
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
