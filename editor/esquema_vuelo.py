"""Esquema del editor para volar de verdad: los números y las frases, cómo vuela cada aparato y dónde está cada localidad."""
from juego.vuelo import AJ


def c(k, e, t="texto", ayuda="", **kw):
    d = {"k": k, "e": e, "t": t, "ayuda": ayuda}
    d.update(kw)
    return d


# clave: (etiqueta, pestaña, ayuda, mínimo, máximo)
_NUMEROS = {
    "alt_despegue": ("Metros a los que queda el aparato al despegar", "General", "", 10, 1000),
    "alt_minima": ("Altura mínima en vuelo, en metros", "General", "Más abajo solo se baja para aterrizar.", 5, 500),
    "alt_alta": ("Metros desde los que se vuela alto", "General", "Por encima, la policía de tierra no te sigue y el radar te ve.", 20, 5000),
    "paso_altura": ("Cada cuántos metros suena el tono de altitud", "General", "Volando sobre una localidad.", 5, 500),
    "descenso": ("Metros por segundo que baja al aterrizar", "General", "", 1, 200),
    "planeo": ("Metros por segundo que cae sin motor", "General", "", 1, 200),
    "pista_radio": ("Metros alrededor de un campo que cuentan como pista", "General", "", 5, 500),
    "forzoso_min": ("Aterrizaje forzoso: daño mínimo, por ciento", "General", "Del estado del aparato.", 0, 100),
    "forzoso_max": ("Y máximo", "General", "", 1, 100),
    "consumo_local": ("Combustible que se gasta por minuto sobre una localidad, por ciento", "Combustible", "A toda velocidad; más despacio, menos.", 0, 100),
    "reserva": ("Tanto por ciento al que avisa de la reserva", "Combustible", "", 1, 99),
    "critico": ("Tanto por ciento al que suena la alarma", "Combustible", "", 1, 99),
    "caida_min": ("Caída sin motor sobre un edificio, o lejos de todo: daño mínimo, por ciento", "Combustible", "", 1, 100),
    "caida_max": ("Y máximo", "Combustible", "", 1, 100),
    "caida_herida_min": ("Salud que pierdes tú, como poco", "Combustible", "", 1, 200),
    "caida_herida_max": ("Y como mucho", "Combustible", "", 1, 200),
    "compresion": ("Segundos de vuelo que pasan en cada segundo de travesía", "Travesía", "Con 12, cuarenta kilómetros en helicóptero son poco más de un minuto.", 1, 200),
    "acelerado": ("Cuántas veces más deprisa va acelerada", "Travesía", "", 1, 50),
    "viento_max": ("Viento máximo, en kilómetros por hora", "Travesía", "Cada travesía tiene el suyo, de una dirección distinta.", 0, 300),
    "viento_lluvia": ("Viento con lluvia, por ciento del normal", "Travesía", "", 1, 1000),
    "giro": ("Grados que vira cada pulsación", "Travesía", "", 1, 90),
    "paso_crucero": ("Metros que sube o baja cada pulsación", "Travesía", "", 10, 1000),
    "ascenso_crucero": ("Metros de altitud que cambia por segundo", "Travesía", "", 1, 500),
    "nivel_km": ("Metros de altitud de crucero por cada kilómetro de trayecto, como mucho", "Travesía", "En un trayecto corto no da tiempo a subir hasta la altitud de crucero del aparato: se queda más abajo.", 1, 1000),
    "bajo_lento": ("Volando bajo: velocidad, por ciento de la de crucero", "Travesía", "", 10, 100),
    "bajo_consumo": ("Volando bajo: consumo, por ciento del normal", "Travesía", "", 100, 1000),
    "aprox_km": ("Kilómetros a los que empieza la aproximación", "Aproximación", "", 1, 100),
    "aprox_alt": ("Altitud a la que hay que llegar, en metros", "Aproximación", "", 30, 5000),
    "alineacion": ("Grados que se puede ir torcido", "Aproximación", "", 1, 90),
    "frustradas": ("Aproximaciones frustradas tras las que la torre te guía", "Aproximación", "", 0, 20),
    "frustrada_km": ("Kilómetros a los que quedas al dar otra vuelta", "Aproximación", "", 1, 50),
    "llegada_km": ("Kilómetros a los que se da por tocado el campo", "Aproximación", "", 0.1, 10),
    "sobrevuelo_km": ("Kilómetros a los que se entra volando bajo", "Aproximación", "", 0.1, 20),
    "duro_dano": ("Daño de un aterrizaje duro, por ciento", "Aproximación", "", 0, 100),
    "suceso_cada": ("Segundos de travesía entre un suceso y el siguiente, más o menos", "Sucesos", "", 5, 3600),
    "peso_turbulencia": ("Cuánto pesan las turbulencias", "Sucesos", "Los sucesos se sortean con estos pesos. Con cero, ese no sale.", 0, 100),
    "peso_trafico": ("Cuánto pesa el tráfico aéreo", "Sucesos", "", 0, 100),
    "peso_tormenta": ("Cuánto pesan las tormentas", "Sucesos", "Con lluvia, el doble. Como mucho, una por travesía.", 0, 100),
    "peso_paisaje": ("Decir las localidades junto a las que se pasa", "Sucesos", "Con cero, no se dicen.", 0, 100),
    "turbulencia_seg": ("Segundos que dura una turbulencia", "Sucesos", "", 1, 120),
    "trafico_seg": ("Segundos para dejar paso al otro aparato", "Sucesos", "", 2, 120),
    "trafico_multa": ("Sanción si no lo haces, en euros", "Sucesos", "", 0, 100000),
    "tormenta_radio": ("Radio de una tormenta, en kilómetros", "Tormentas y obstáculos", "", 1, 100),
    "tormenta_alt": ("Metros por encima de los que no afecta", "Tormentas y obstáculos", "Solo la pasa por encima un aparato cuyo techo sea cien metros mayor.", 100, 20000),
    "tormenta_dano": ("Daño de cada sacudida dentro, por ciento", "Tormentas y obstáculos", "", 0, 100),
    "obstaculo_cada": ("Volando bajo: segundos entre obstáculos, más o menos", "Tormentas y obstáculos", "", 1, 600),
    "obstaculo_seg": ("Segundos para subir", "Tormentas y obstáculos", "", 1, 60),
    "obstaculo_sube": ("Metros que hay que subir", "Tormentas y obstáculos", "", 10, 1000),
    "obstaculo_dano": ("Daño si no subes, por ciento", "Tormentas y obstáculos", "", 0, 100),
    "radar_pierde": ("Segundos volando bajo sobre una localidad para que el radar te pierda", "Radar y secuestro", "", 1, 3600),
    "radar_pierde_crucero": ("Y en una travesía", "Radar y secuestro", "", 1, 3600),
    "secuestro_busqueda": ("Nivel de búsqueda al secuestrar", "Radar y secuestro", "Con el helicóptero de la policía encendido, sube hasta el nivel con el que sale.", 1, 5),
    "secuestro_espera": ("Nivel si aterrizas en un campo con el radar encima", "Radar y secuestro", "", 1, 5),
    "secuestro_reconocen": ("Nivel si aterrizas en un campo sin radar", "Radar y secuestro", "Con cero, no pasa nada.", 0, 5),
    "secuestro_llegada": ("Nivel al entrar volando bajo en una localidad con el radar encima", "Radar y secuestro", "", 1, 5),
    "secuestro_gravedad": ("Gravedad del antecedente, de 1 a 3", "Radar y secuestro", "", 1, 3),
    "encargo_min": ("Lo que paga el encargo, como poco", "Radar y secuestro", "", 1, 10000000),
    "encargo_max": ("Y como mucho", "Radar y secuestro", "", 1, 10000000),
    "encargo_radio": ("Metros alrededor del sitio donde vale posarse", "Radar y secuestro", "", 5, 1000),
    "hangar_plazas": ("Aeronaves que caben en cada plaza de hangar", "Hangares y piloto", "", 1, 50),
    "hangar_tope": ("Aeronaves guardadas como mucho, entre todos los hangares", "Hangares y piloto", "", 1, 500),
    "hangar_impago": ("Días sin pagar tras los que te quitan una plaza vacía", "Hangares y piloto", "Con cero, nunca. Una plaza con aeronaves dentro no se quita.", 0, 365),
    "vuelo_base": ("Vuelo comercial: parte fija de la paga", "Hangares y piloto", "", 0, 1000000),
    "vuelo_km": ("Y lo que se suma por kilómetro", "Hangares y piloto", "", 0, 100000),
    "vuelo_ofertas": ("Vuelos que ofrece cada campo al día", "Hangares y piloto", "", 1, 12),
    "vuelo_propio": ("Suplemento por volar con tu aparato, por ciento", "Hangares y piloto", "", 0, 500),
    "vuelo_confort": ("Gratificación o descuento por cómo ha ido el vuelo, por ciento", "Hangares y piloto", "", 0, 100),
    "vuelo_prestigio": ("Prestigio que da cada vuelo cumplido", "Hangares y piloto", "", 0, 100),
}
_ENTEROS = ("frustradas", "trafico_multa", "secuestro_busqueda", "secuestro_espera", "secuestro_reconocen", "secuestro_llegada", "secuestro_gravedad", "encargo_min", "encargo_max",
            "hangar_plazas", "hangar_tope", "hangar_impago", "vuelo_ofertas")
# clave: (etiqueta, pestaña, huecos)
_FRASES = {
    "torre_despegue": ("Al despegar de un campo", "La torre", "{campo}, {destino}, {km}, {rumbo} y {viento}"),
    "torre_salida": ("Al salir volando por el borde de la localidad", "La torre", "{origen}, {destino}, {km}, {rumbo} y {viento}"),
    "torre_crucero": ("Al llegar a la altitud de crucero", "La torre", "{alt} y {km}"),
    "torre_aprox": ("Al empezar la aproximación", "La torre", "{campo}, {km}, {alt} y {rumbo}"),
    "torre_final": ("En final, bien encarado", "La torre", ""),
    "torre_frustrada": ("Aproximación frustrada", "La torre", "{motivo}, que es alto o torcido"),
    "torre_guiada": ("La torre te guía", "La torre", ""),
    "torre_trafico": ("Tráfico a tu altitud", "La torre", ""),
    "torre_tormenta": ("Tormenta en el rumbo", "La torre", "{km}"),
    "frases_aterrizaje": ("Aterrizaje suave", "Llegar", "{campo}"),
    "frases_aterrizaje_duro": ("Aterrizaje duro", "Llegar", "{campo}"),
    "frases_sobrevuelo": ("Entrar volando bajo", "Llegar", "{destino}"),
    "frases_forzoso": ("Aterrizaje forzoso", "Llegar", ""),
    "frases_caida": ("Caída", "Llegar", ""),
    "frases_turbulencia": ("Empiezan las turbulencias", "En el aire", ""),
    "frases_turbulencia_fin": ("Acaban", "En el aire", ""),
    "frases_trafico_libre": ("Dejas paso al otro aparato", "En el aire", ""),
    "frases_trafico_susto": ("No lo dejas", "En el aire", ""),
    "frases_tormenta_dentro": ("Entras en la tormenta", "En el aire", ""),
    "frases_tormenta_fuera": ("Sales", "En el aire", ""),
    "frases_tormenta_encima": ("La pasas por encima", "En el aire", ""),
    "frases_paisaje": ("Pasas junto a una localidad", "En el aire", "{lugar}, {lado} y {km}"),
    "frases_obstaculo": ("Volando bajo: un obstáculo", "Vuelo bajo y combustible", ""),
    "frases_obstaculo_libre": ("Lo libras", "Vuelo bajo y combustible", ""),
    "frases_obstaculo_roce": ("Lo rozas", "Vuelo bajo y combustible", ""),
    "frases_reserva": ("Combustible en reserva", "Vuelo bajo y combustible", "{pct}"),
    "frases_critico": ("Combustible crítico", "Vuelo bajo y combustible", "{pct}"),
    "frases_sin_motor": ("Se para el motor", "Vuelo bajo y combustible", ""),
    "frases_radar": ("El radar te sigue", "Frases del radar", "{alt}"),
    "frases_radar_perdido": ("Te pierde", "Frases del radar", ""),
    "frases_radar_otra_vez": ("Te vuelve a ver", "Frases del radar", ""),
    "frases_te_esperan": ("Te esperan en el campo", "Frases del radar", "{campo}"),
    "frases_reconocen": ("Reconocen el aparato", "Frases del radar", "{campo}"),
    "frases_secuestro": ("Al secuestrar", "Frases del radar", ""),
    "frases_encargo_hecho": ("Entregas el encargo", "Frases del radar", "{paga}"),
    "frases_encargo_radar": ("Llegas con el radar encima", "Frases del radar", ""),
    "sitios_discretos": ("Tipos de lugar donde se entrega el encargo", "Frases del radar", "Uno por línea, con el nombre interno del tipo de lugar. Se elige uno que quede lejos de los campos."),
    "frases_piloto_oferta": ("Cómo se anuncia un vuelo", "Frases del piloto", "{que}, {destino}, {km} y {paga}"),
    "frases_piloto_sale": ("Al aceptarlo", "Frases del piloto", "{destino}"),
    "frases_piloto_llega": ("Al cobrar", "Frases del piloto", "{paga} y {destino}"),
    "frases_piloto_propina": ("Vuelo tranquilo", "Frases del piloto", "{extra}"),
    "frases_piloto_queja": ("Vuelo movido", "Frases del piloto", "{extra}"),
    "pasajes": ("A quién se lleva", "Frases del piloto", "Uno por línea."),
    "cargas": ("Qué se lleva", "Frases del piloto", "Uno por línea."),
}


def _campos_ajuste():
    campos = [c("id", "Identificador", req=True, defecto="general", ayuda="Déjalo en general: solo se usa el primero.")]
    for k, serie in AJ._n.items():
        e, grupo, ayuda, minimo, maximo = _NUMEROS[k]
        campos.append(c(k, e, "entero" if k in _ENTEROS else "decimal", ayuda, minimo=minimo, maximo=maximo,
                        defecto=int(serie) if float(serie).is_integer() else serie, **({} if grupo == "General" else {"grupo": grupo})))
    for k in AJ._l:
        e, grupo, huecos = _FRASES[k]
        ayuda = huecos if not huecos.startswith("{") and huecos else ("Una por línea; se dice una al azar. " + ("Huecos: " + huecos + "." if huecos else "")).strip()
        campos.append(c(k, e, "textos", ayuda, grupo=grupo))
    return campos


ESQUEMAS = {
    "ajuste_vuelo": {"titulo": "Volar: números y frases",
                     "resumen": lambda d: f"Se vuela alto desde {d.get('alt_alta', 150)} metros; la travesía va {d.get('compresion', 12)} veces más deprisa que el reloj",
                     "campos": _campos_ajuste()},
    "aeronave": {"titulo": "Aeronave: cómo vuela", "resumen": lambda d: f"{d.get('id', '?')}: {d.get('crucero', '?')} kilómetros por hora, {d.get('autonomia', '?')} de autonomía", "campos": [
        c("id", "Vehículo", "ref", "El vehículo, que tiene que tener marcada la casilla de que vuela. Con el identificador de uno del juego, tu mod cambia cómo vuela ese.", ref="modelo", req=True),
        c("crucero", "Velocidad de crucero, en kilómetros por hora", "decimal", "En las travesías entre localidades.", minimo=40, maximo=2000, defecto=170),
        c("alt_crucero", "Altitud de crucero, en metros", "decimal", "A la que sube el piloto automático.", minimo=100, maximo=20000, defecto=500),
        c("techo", "Techo, en metros", "decimal", "Lo más alto que sube. Para pasar una tormenta por encima tiene que ser mayor que la altura de las tormentas.", minimo=200, maximo=30000, defecto=900),
        c("autonomia", "Autonomía, en kilómetros", "decimal", "Lo que hace con el depósito lleno.", minimo=20, maximo=100000, defecto=260),
        c("ascenso", "Metros que sube por segundo", "decimal", "Volando sobre una localidad.", minimo=2, maximo=200, defecto=10),
        c("pista", "Necesita pista para aterrizar", "si_no", "Con sí, solo aterriza bien en un aeropuerto o un aeródromo; en otro sitio es un aterrizaje forzoso. Con no, se posa en cualquier espacio abierto, como un helicóptero."),
    ]},
    "punto_aire": {"titulo": "Mapa del aire: dónde está una localidad", "resumen": lambda d: f"{d.get('id', '?')}: {d.get('x', 0)} al este, {d.get('y', 0)} al norte", "campos": [
        c("id", "Localidad", "ref", "Para volar entre localidades hace falta saber dónde está cada una. Si no pones la tuya, el juego la coloca él, según por dónde se llegue a ella.", ref="mapa", req=True),
        c("x", "Kilómetros hacia el este", "decimal", "Desde Puerto Bravo, que está en cero. Negativo, hacia el oeste.", minimo=-5000, maximo=5000, defecto=0),
        c("y", "Kilómetros hacia el norte", "decimal", "Negativo, hacia el sur, que es donde está el mar.", minimo=-5000, maximo=5000, defecto=0),
    ]},
}
SECCIONES = [("vuelo", "Volar: números y frases", "ajuste_vuelo"), ("aeronaves", "Aeronaves: cómo vuela cada una", "aeronave"), ("mapa_aire", "Mapa del aire: dónde está cada localidad", "punto_aire")]
CAMPO_LUGAR = c("hangar_precio", "Precio de la plaza de hangar", "entero", "Lo que cuesta comprar una plaza de hangar en este campo. Con cero o sin valor, el de las tarifas.",
                si=lambda d: d.get("tipo") in ("helipuerto", "aeropuerto"), minimo=0, maximo=100000000)


def aplicar(esquemas, secciones):
    esquemas.update(ESQUEMAS)
    esquemas["lugar"]["campos"].append(dict(CAMPO_LUGAR))
    pos = next(k for k, x in enumerate(secciones) if x[0] == "vehiculos_propios") + 1
    secciones[pos:pos] = SECCIONES
