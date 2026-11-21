"""Esquema del editor para volar de verdad: los números y las frases, cómo vuela cada aparato y dónde está cada localidad."""
from juego.i18n import tr
from juego.vuelo import AJ


def c(k, e, t="texto", ayuda="", **kw):
    d = {"k": k, "e": e, "t": t, "ayuda": ayuda}
    d.update(kw)
    return d


# clave: (etiqueta, pestaña, ayuda, mínimo, máximo)
_NUMEROS = {
    "alt_despegue": (tr("Metros a los que queda el aparato al despegar"), tr("General"), "", 10, 1000),
    "alt_minima": (tr("Altura mínima en vuelo, en metros"), tr("General"), tr("Más abajo solo se baja para aterrizar."), 5, 500),
    "alt_alta": (tr("Metros desde los que se vuela alto"), tr("General"), tr("Por encima, la policía de tierra no te sigue y el radar te ve."), 20, 5000),
    "paso_altura": (tr("Cada cuántos metros suena el tono de altitud"), tr("General"), tr("Volando sobre una localidad."), 5, 500),
    "descenso": (tr("Metros por segundo que baja al aterrizar"), tr("General"), "", 1, 200),
    "planeo": (tr("Metros por segundo que cae sin motor"), tr("General"), "", 1, 200),
    "pista_radio": (tr("Metros alrededor de un campo que cuentan como pista"), tr("General"), "", 5, 500),
    "forzoso_min": (tr("Aterrizaje forzoso: daño mínimo, por ciento"), tr("General"), tr("Del estado del aparato."), 0, 100),
    "forzoso_max": (tr("Y máximo"), tr("General"), "", 1, 100),
    "consumo_local": (tr("Combustible que se gasta por minuto sobre una localidad, por ciento"), tr("Combustible"), tr("A toda velocidad; más despacio, menos."), 0, 100),
    "reserva": (tr("Tanto por ciento al que avisa de la reserva"), tr("Combustible"), "", 1, 99),
    "critico": (tr("Tanto por ciento al que suena la alarma"), tr("Combustible"), "", 1, 99),
    "caida_min": (tr("Caída sin motor sobre un edificio, o lejos de todo: daño mínimo, por ciento"), tr("Combustible"), "", 1, 100),
    "caida_max": (tr("Y máximo"), tr("Combustible"), "", 1, 100),
    "caida_herida_min": (tr("Salud que pierdes tú, como poco"), tr("Combustible"), "", 1, 200),
    "caida_herida_max": (tr("Y como mucho"), tr("Combustible"), "", 1, 200),
    "compresion": (tr("Segundos de vuelo que pasan en cada segundo de travesía"), tr("Travesía"), tr("Con 12, cuarenta kilómetros en helicóptero son poco más de un minuto."), 1, 200),
    "acelerado": (tr("Cuántas veces más deprisa va acelerada"), tr("Travesía"), "", 1, 50),
    "viento_max": (tr("Viento máximo, en kilómetros por hora"), tr("Travesía"), tr("Cada travesía tiene el suyo, de una dirección distinta."), 0, 300),
    "viento_lluvia": (tr("Viento con lluvia, por ciento del normal"), tr("Travesía"), "", 1, 1000),
    "giro": (tr("Grados que vira cada pulsación"), tr("Travesía"), "", 1, 90),
    "paso_crucero": (tr("Metros que sube o baja cada pulsación"), tr("Travesía"), "", 10, 1000),
    "ascenso_crucero": (tr("Metros de altitud que cambia por segundo"), tr("Travesía"), "", 1, 500),
    "nivel_km": (tr("Metros de altitud de crucero por cada kilómetro de trayecto, como mucho"), tr("Travesía"), tr("En un trayecto corto no da tiempo a subir hasta la altitud de crucero del aparato: se queda más abajo."), 1, 1000),
    "bajo_lento": (tr("Volando bajo: velocidad, por ciento de la de crucero"), tr("Travesía"), "", 10, 100),
    "bajo_consumo": (tr("Volando bajo: consumo, por ciento del normal"), tr("Travesía"), "", 100, 1000),
    "aprox_km": (tr("Kilómetros a los que empieza la aproximación"), tr("Aproximación"), "", 1, 100),
    "aprox_alt": (tr("Altitud a la que hay que llegar, en metros"), tr("Aproximación"), "", 30, 5000),
    "alineacion": (tr("Grados que se puede ir torcido"), tr("Aproximación"), "", 1, 90),
    "frustradas": (tr("Aproximaciones frustradas tras las que la torre te guía"), tr("Aproximación"), "", 0, 20),
    "frustrada_km": (tr("Kilómetros a los que quedas al dar otra vuelta"), tr("Aproximación"), "", 1, 50),
    "llegada_km": (tr("Kilómetros a los que se da por tocado el campo"), tr("Aproximación"), "", 0.1, 10),
    "sobrevuelo_km": (tr("Kilómetros a los que se entra volando bajo"), tr("Aproximación"), "", 0.1, 20),
    "duro_dano": (tr("Daño de un aterrizaje duro, por ciento"), tr("Aproximación"), "", 0, 100),
    "suceso_cada": (tr("Segundos de travesía entre un suceso y el siguiente, más o menos"), tr("Sucesos"), "", 5, 3600),
    "peso_turbulencia": (tr("Cuánto pesan las turbulencias"), tr("Sucesos"), tr("Los sucesos se sortean con estos pesos. Con cero, ese no sale."), 0, 100),
    "peso_trafico": (tr("Cuánto pesa el tráfico aéreo"), tr("Sucesos"), "", 0, 100),
    "peso_tormenta": (tr("Cuánto pesan las tormentas"), tr("Sucesos"), tr("Con lluvia, el doble. Como mucho, una por travesía."), 0, 100),
    "peso_paisaje": (tr("Decir las localidades junto a las que se pasa"), tr("Sucesos"), tr("Con cero, no se dicen."), 0, 100),
    "turbulencia_seg": (tr("Segundos que dura una turbulencia"), tr("Sucesos"), "", 1, 120),
    "trafico_seg": (tr("Segundos para dejar paso al otro aparato"), tr("Sucesos"), "", 2, 120),
    "trafico_multa": (tr("Sanción si no lo haces, en euros"), tr("Sucesos"), "", 0, 100000),
    "tormenta_radio": (tr("Radio de una tormenta, en kilómetros"), tr("Tormentas y obstáculos"), "", 1, 100),
    "tormenta_alt": (tr("Metros por encima de los que no afecta"), tr("Tormentas y obstáculos"), tr("Solo la pasa por encima un aparato cuyo techo sea cien metros mayor."), 100, 20000),
    "tormenta_dano": (tr("Daño de cada sacudida dentro, por ciento"), tr("Tormentas y obstáculos"), "", 0, 100),
    "obstaculo_cada": (tr("Volando bajo: segundos entre obstáculos, más o menos"), tr("Tormentas y obstáculos"), "", 1, 600),
    "obstaculo_seg": (tr("Segundos para subir"), tr("Tormentas y obstáculos"), "", 1, 60),
    "obstaculo_sube": (tr("Metros que hay que subir"), tr("Tormentas y obstáculos"), "", 10, 1000),
    "obstaculo_dano": (tr("Daño si no subes, por ciento"), tr("Tormentas y obstáculos"), "", 0, 100),
    "radar_pierde": (tr("Segundos volando bajo sobre una localidad para que el radar te pierda"), tr("Radar y secuestro"), "", 1, 3600),
    "radar_pierde_crucero": (tr("Y en una travesía"), tr("Radar y secuestro"), "", 1, 3600),
    "secuestro_busqueda": (tr("Nivel de búsqueda al secuestrar"), tr("Radar y secuestro"), tr("Con el helicóptero de la policía encendido, sube hasta el nivel con el que sale."), 1, 5),
    "secuestro_espera": (tr("Nivel si aterrizas en un campo con el radar encima"), tr("Radar y secuestro"), "", 1, 5),
    "secuestro_reconocen": (tr("Nivel si aterrizas en un campo sin radar"), tr("Radar y secuestro"), tr("Con cero, no pasa nada."), 0, 5),
    "secuestro_llegada": (tr("Nivel al entrar volando bajo en una localidad con el radar encima"), tr("Radar y secuestro"), "", 1, 5),
    "secuestro_gravedad": (tr("Gravedad del antecedente, de 1 a 3"), tr("Radar y secuestro"), "", 1, 3),
    "encargo_min": (tr("Lo que paga el encargo, como poco"), tr("Radar y secuestro"), "", 1, 10000000),
    "encargo_max": (tr("Y como mucho"), tr("Radar y secuestro"), "", 1, 10000000),
    "encargo_radio": (tr("Metros alrededor del sitio donde vale posarse"), tr("Radar y secuestro"), "", 5, 1000),
    "hangar_plazas": (tr("Aeronaves que caben en cada plaza de hangar"), tr("Hangares y piloto"), "", 1, 50),
    "hangar_tope": (tr("Aeronaves guardadas como mucho, entre todos los hangares"), tr("Hangares y piloto"), "", 1, 500),
    "hangar_impago": (tr("Días sin pagar tras los que te quitan una plaza vacía"), tr("Hangares y piloto"), tr("Con cero, nunca. Una plaza con aeronaves dentro no se quita."), 0, 365),
    "vuelo_base": (tr("Vuelo comercial: parte fija de la paga"), tr("Hangares y piloto"), "", 0, 1000000),
    "vuelo_km": (tr("Y lo que se suma por kilómetro"), tr("Hangares y piloto"), "", 0, 100000),
    "vuelo_ofertas": (tr("Vuelos que ofrece cada campo al día"), tr("Hangares y piloto"), "", 1, 12),
    "vuelo_propio": (tr("Suplemento por volar con tu aparato, por ciento"), tr("Hangares y piloto"), "", 0, 500),
    "vuelo_confort": (tr("Gratificación o descuento por cómo ha ido el vuelo, por ciento"), tr("Hangares y piloto"), "", 0, 100),
    "vuelo_prestigio": (tr("Prestigio que da cada vuelo cumplido"), tr("Hangares y piloto"), "", 0, 100),
}
_ENTEROS = ("frustradas", "trafico_multa", "secuestro_busqueda", "secuestro_espera", "secuestro_reconocen", "secuestro_llegada", "secuestro_gravedad", "encargo_min", "encargo_max",
            "hangar_plazas", "hangar_tope", "hangar_impago", "vuelo_ofertas")
# clave: (etiqueta, pestaña, huecos)
_FRASES = {
    "torre_despegue": (tr("Al despegar de un campo"), tr("La torre"), tr("{campo}, {destino}, {km}, {rumbo} y {viento}")),
    "torre_salida": (tr("Al salir volando por el borde de la localidad"), tr("La torre"), tr("{origen}, {destino}, {km}, {rumbo} y {viento}")),
    "torre_crucero": (tr("Al llegar a la altitud de crucero"), tr("La torre"), tr("{alt} y {km}")),
    "torre_aprox": (tr("Al empezar la aproximación"), tr("La torre"), tr("{campo}, {km}, {alt} y {rumbo}")),
    "torre_final": (tr("En final, bien encarado"), tr("La torre"), ""),
    "torre_frustrada": (tr("Aproximación frustrada"), tr("La torre"), tr("{motivo}, que es alto o torcido")),
    "torre_guiada": (tr("La torre te guía"), tr("La torre"), ""),
    "torre_trafico": (tr("Tráfico a tu altitud"), tr("La torre"), ""),
    "torre_tormenta": (tr("Tormenta en el rumbo"), tr("La torre"), "{km}"),
    "frases_aterrizaje": (tr("Aterrizaje suave"), tr("Llegar"), "{campo}"),
    "frases_aterrizaje_duro": (tr("Aterrizaje duro"), tr("Llegar"), "{campo}"),
    "frases_sobrevuelo": (tr("Entrar volando bajo"), tr("Llegar"), "{destino}"),
    "frases_forzoso": (tr("Aterrizaje forzoso"), tr("Llegar"), ""),
    "frases_caida": (tr("Caída"), tr("Llegar"), ""),
    "frases_turbulencia": (tr("Empiezan las turbulencias"), tr("En el aire"), ""),
    "frases_turbulencia_fin": (tr("Acaban"), tr("En el aire"), ""),
    "frases_trafico_libre": (tr("Dejas paso al otro aparato"), tr("En el aire"), ""),
    "frases_trafico_susto": (tr("No lo dejas"), tr("En el aire"), ""),
    "frases_tormenta_dentro": (tr("Entras en la tormenta"), tr("En el aire"), ""),
    "frases_tormenta_fuera": (tr("Sales"), tr("En el aire"), ""),
    "frases_tormenta_encima": (tr("La pasas por encima"), tr("En el aire"), ""),
    "frases_paisaje": (tr("Pasas junto a una localidad"), tr("En el aire"), tr("{lugar}, {lado} y {km}")),
    "frases_obstaculo": (tr("Volando bajo: un obstáculo"), tr("Vuelo bajo y combustible"), ""),
    "frases_obstaculo_libre": (tr("Lo libras"), tr("Vuelo bajo y combustible"), ""),
    "frases_obstaculo_roce": (tr("Lo rozas"), tr("Vuelo bajo y combustible"), ""),
    "frases_reserva": (tr("Combustible en reserva"), tr("Vuelo bajo y combustible"), "{pct}"),
    "frases_critico": (tr("Combustible crítico"), tr("Vuelo bajo y combustible"), "{pct}"),
    "frases_sin_motor": (tr("Se para el motor"), tr("Vuelo bajo y combustible"), ""),
    "frases_radar": (tr("El radar te sigue"), tr("Frases del radar"), "{alt}"),
    "frases_radar_perdido": (tr("Te pierde"), tr("Frases del radar"), ""),
    "frases_radar_otra_vez": (tr("Te vuelve a ver"), tr("Frases del radar"), ""),
    "frases_te_esperan": (tr("Te esperan en el campo"), tr("Frases del radar"), "{campo}"),
    "frases_reconocen": (tr("Reconocen el aparato"), tr("Frases del radar"), "{campo}"),
    "frases_secuestro": (tr("Al secuestrar"), tr("Frases del radar"), ""),
    "frases_encargo_hecho": (tr("Entregas el encargo"), tr("Frases del radar"), "{paga}"),
    "frases_encargo_radar": (tr("Llegas con el radar encima"), tr("Frases del radar"), ""),
    "sitios_discretos": (tr("Tipos de lugar donde se entrega el encargo"), tr("Frases del radar"), tr("Uno por línea, con el nombre interno del tipo de lugar. Se elige uno que quede lejos de los campos.")),
    "frases_piloto_oferta": (tr("Cómo se anuncia un vuelo"), tr("Frases del piloto"), tr("{que}, {destino}, {km} y {paga}")),
    "frases_piloto_sale": (tr("Al aceptarlo"), tr("Frases del piloto"), "{destino}"),
    "frases_piloto_llega": (tr("Al cobrar"), tr("Frases del piloto"), tr("{paga} y {destino}")),
    "frases_piloto_propina": (tr("Vuelo tranquilo"), tr("Frases del piloto"), "{extra}"),
    "frases_piloto_queja": (tr("Vuelo movido"), tr("Frases del piloto"), "{extra}"),
    "pasajes": (tr("A quién se lleva"), tr("Frases del piloto"), tr("Uno por línea.")),
    "cargas": (tr("Qué se lleva"), tr("Frases del piloto"), tr("Uno por línea.")),
}


def _campos_ajuste():
    campos = [c("id", tr("Identificador"), req=True, defecto="general", ayuda=tr("Déjalo en general: solo se usa el primero."))]
    for k, serie in AJ._n.items():
        e, grupo, ayuda, minimo, maximo = _NUMEROS[k]
        campos.append(c(k, e, "entero" if k in _ENTEROS else "decimal", ayuda, minimo=minimo, maximo=maximo,
                        defecto=int(serie) if float(serie).is_integer() else serie, **({} if grupo == "General" else {"grupo": grupo})))
    for k in AJ._l:
        e, grupo, huecos = _FRASES[k]
        ayuda = huecos if not huecos.startswith("{") and huecos else (tr("Una por línea; se dice una al azar. ") + (tr("Huecos: ") + huecos + "." if huecos else "")).strip()
        campos.append(c(k, e, "textos", ayuda, grupo=grupo))
    return campos


ESQUEMAS = {
    "ajuste_vuelo": {"titulo": tr("Volar: números y frases"),
                     "resumen": lambda d: tr('Se vuela alto desde {get} metros; la travesía va {get2} veces más deprisa que el reloj').format(get=(d.get('alt_alta', 150)), get2=(d.get('compresion', 12))),
                     "campos": _campos_ajuste()},
    "aeronave": {"titulo": tr("Aeronave: cómo vuela"), "resumen": lambda d: tr('{get}: {get2} kilómetros por hora, {get3} de autonomía').format(get=(d.get('id', '?')), get2=(d.get('crucero', '?')), get3=(d.get('autonomia', '?'))), "campos": [
        c("id", tr("Vehículo"), "ref", tr("El vehículo, que tiene que tener marcada la casilla de que vuela. Con el identificador de uno del juego, tu mod cambia cómo vuela ese."), ref="modelo", req=True),
        c("crucero", tr("Velocidad de crucero, en kilómetros por hora"), "decimal", tr("En las travesías entre localidades."), minimo=40, maximo=2000, defecto=170),
        c("alt_crucero", tr("Altitud de crucero, en metros"), "decimal", tr("A la que sube el piloto automático."), minimo=100, maximo=20000, defecto=500),
        c("techo", tr("Techo, en metros"), "decimal", tr("Lo más alto que sube. Para pasar una tormenta por encima tiene que ser mayor que la altura de las tormentas."), minimo=200, maximo=30000, defecto=900),
        c("autonomia", tr("Autonomía, en kilómetros"), "decimal", tr("Lo que hace con el depósito lleno."), minimo=20, maximo=100000, defecto=260),
        c("ascenso", tr("Metros que sube por segundo"), "decimal", tr("Volando sobre una localidad."), minimo=2, maximo=200, defecto=10),
        c("pista", tr("Necesita pista para aterrizar"), "si_no", tr("Con sí, solo aterriza bien en un aeropuerto o un aeródromo; en otro sitio es un aterrizaje forzoso. Con no, se posa en cualquier espacio abierto, como un helicóptero.")),
    ]},
    "punto_aire": {"titulo": tr("Mapa del aire: dónde está una localidad"), "resumen": lambda d: tr('{get}: {get2} al este, {get3} al norte').format(get=(d.get('id', '?')), get2=(d.get('x', 0)), get3=(d.get('y', 0))), "campos": [
        c("id", tr("Localidad"), "ref", tr("Para volar entre localidades hace falta saber dónde está cada una. Si no pones la tuya, el juego la coloca él, según por dónde se llegue a ella."), ref="mapa", req=True),
        c("x", tr("Kilómetros hacia el este"), "decimal", tr("Desde Puerto Bravo, que está en cero. Negativo, hacia el oeste."), minimo=-5000, maximo=5000, defecto=0),
        c("y", tr("Kilómetros hacia el norte"), "decimal", tr("Negativo, hacia el sur, que es donde está el mar."), minimo=-5000, maximo=5000, defecto=0),
    ]},
}
SECCIONES = [("vuelo", tr("Volar: números y frases"), "ajuste_vuelo"), ("aeronaves", tr("Aeronaves: cómo vuela cada una"), "aeronave"), ("mapa_aire", tr("Mapa del aire: dónde está cada localidad"), "punto_aire")]
CAMPO_LUGAR = c("hangar_precio", tr("Precio de la plaza de hangar"), "entero", tr("Lo que cuesta comprar una plaza de hangar en este campo. Con cero o sin valor, el de las tarifas."),
                si=lambda d: d.get("tipo") in ("helipuerto", "aeropuerto"), minimo=0, maximo=100000000)


def aplicar(esquemas, secciones):
    esquemas.update(ESQUEMAS)
    esquemas["lugar"]["campos"].append(dict(CAMPO_LUGAR))
    pos = next(k for k, x in enumerate(secciones) if x[0] == "vehiculos_propios") + 1
    secciones[pos:pos] = SECCIONES
