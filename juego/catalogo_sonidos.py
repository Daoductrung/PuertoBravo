"""Catálogo de sonidos: qué es cada archivo de data/sonidos. Se usa para generar la documentación."""

GRUPOS = [
    ("Menús y avisos generales", "Sonidos cortos de la interfaz. Conviene que sean breves y discretos.",
     ("menu_",), {"error", "notificacion", "mision_ok", "mision_fallo", "dinero", "guardado", "movil", "dialogo", "pasan_horas", "logro",
                  "nivel", "evento", "caja", "reloj", "llegada", "recoger", "curar", "comer"}),
    ("Orientación y GPS", "Son la base de la accesibilidad del juego. Si los cambias, que sigan siendo cortos, claros y fáciles de localizar en el espacio.",
     ("tono_", "semaforo_", "baliza"), {"sonar", "bordillo", "cruce", "radar", "cursor_mapa"}),
    ("Pasos", "Hay dos variantes de cada suelo, que se alternan pie izquierdo y pie derecho. Deben durar menos de un cuarto de segundo.",
     ("paso_",), {"choque_pared"}),
    ("Personas", "Voces sin palabras, golpes y animales.", (), {"dolor", "dolor_npc", "dolor_mujer", "muerte_npc", "grito", "grito_hombre", "grito_mujer", "murmullo", "golpe", "golpe_aire", "latido", "ladrido"}),
    ("Armas", "Disparos, recargas, impactos y explosiones.", ("disparo_", "bala_"), {"sin_balas", "recarga", "amartillar", "explosion", "navaja", "lanzar", "cohete", "hacha", "lanzagranadas", "recoger_municion"}),
    ("Motores", "Se reproducen en bucle y el juego les sube el tono con la velocidad. Graba el motor al ralentí, a régimen constante.",
     ("motor_",), {"rodadura"}),
    ("Tren, tranvía, avión y agua", "Los viajes en tren, en tranvía y en avión, y nadar y bucear en el mar. El tren, el tranvía, la cabina del avión y el fondo de debajo del agua suenan en bucle.",
     ("tren", "tranvia", "avion"), {"bajo_agua", "brazada"}),
    ("Vehículos", "Cláxones, frenazos, choques, sirenas y demás ruidos de los vehículos.",
     ("claxon", "sirena", "choque"), {"frenazo", "puerta_coche", "alarma", "arranque", "cristal", "ganzua", "intermitente", "radio_cambio", "reparar", "pintura", "fuego", "repostar", "reserva", "motor_seco", "pinchazo", "multa"}),
    ("Policía y búsqueda", "Avisos del nivel de búsqueda, y el helicóptero de la policía.", ("estrella_",), {"policia_perdida", "buscando", "esposas", "helicoptero_policia", "megafono", "emisora"}),
    ("Localizadores", "Suenan en bucle desde la posición de un objeto o de una misión para que puedas encontrarlo.", ("loc_",), set()),
    ("Firmas de los lugares", "Cada tipo de lugar emite su sonido en bucle para reconocerlo al pasar. Deben ser distintos entre sí y no cansar: piensa que se oyen muchas veces.",
     ("lugar_",), set()),
    ("Ambientes de fondo", "Bucles largos que suenan de fondo en cada barrio, con la lluvia y de noche.", ("amb_",), {"lluvia", "multitud", "viento_playa"}),
    ("Sonidos sueltos de ambiente", "Aparecen de vez en cuando alrededor del jugador.", (), {"trueno", "gaviota", "pajaro", "martillo", "claxon_lejano", "sirena_lejana"}),
    ("Mar y pesca", "", (), {"salpicadura", "pesca_lanzar", "pez_pica", "carrete"}),
    ("Minijuegos", "", ("simon_", "diana"), {"ruleta", "dados", "campana_ring"}),
    ("Ánimo, fama, perro, bolsa y territorios", "Avisos de los sistemas que cambian con lo que haces.",
     ("animo_",), {"fama", "perro_olfatea", "bolsa", "territorio"}),
    ("Puertas, horas del día y vida honrada", "Lo que se oye al entrar en un local, al cambiar la hora y en los trabajos.",
     ("puerta_",), {"campanadas", "gallo", "buho", "agacharse", "levantarse", "hospital_despertar", "celda", "ascenso", "diploma", "donativo", "prestigio", "jornada", "timbre"}),
    ("Jugar con amigos", "Avisos de la partida compartida.", ("amigo_",), {"chat"}),
    ("Vida social, solo con el contenido para adultos", "Relaciones sentimentales.",
     ("afinidad_",), {"pareja", "ruptura", "noche_juntos", "cita", "regalo"}),
    ("Sustancias y trapicheo, solo con el contenido para adultos", "Cada sustancia tiene su sonido al tomarla, para reconocerla sin mirar.",
     ("tomar_", "precio_"), {"bajon", "abstinencia", "sobredosis", "trato", "rechazo", "paisano"}),
]

SUELOS = {"via": "las vías del tranvía y las del tren", "acera": "la acera", "calzada": "el asfalto de la calzada", "hierba": "el césped", "arena": "la arena", "plaza": "las losas de una plaza", "muelle": "los tablones de un muelle"}
LUGARES = {"armeria": "armería", "comida": "bar, restaurante o chiringuito", "hospital": "hospital o farmacia", "comisaria": "comisaría", "taller": "taller o desguace",
           "casa": "vivienda", "bar": "bar, taberna o discoteca", "casino": "casino o feria", "tienda": "tienda", "banco": "banco o casa de empeños",
           "iglesia": "iglesia", "fuente": "fuente", "contacto": "lugar con una misión", "generico": "lugar sin sonido propio", "taxi": "parada de taxis o salida de carreras",
           "periodico": "periódico o librería", "boya": "muelle, boya o punto de pesca en el mar", "embarcadero": "embarcadero", "gimnasio": "gimnasio", "cine": "cine",
           "estacion": "estación de autobuses", "salida": "salida por carretera", "helipuerto": "helipuerto", "prision": "prisión", "mina": "mina", "rio": "río",
           "protectora": "protectora de animales", "club": "club nocturno, con música amortiguada y copas", "empleo": "oficina de empleo, con teclados y el aviso de turno",
           "academia": "academia o autoescuela, con el timbre de clase", "ong": "comedor social u organización benéfica, con platos y cubiertos",
           "proveedor": "proveedor de sustancias: dos siseos y una persiana metálica"}
AMBIENTES = {"playa": "playa, con olas", "puerto": "puerto, con olas y una sirena de barco lejana", "ciudad": "centro de ciudad, con tráfico lejano",
             "industrial": "polígono industrial, con maquinaria", "parque": "parque, con pájaros", "residencial": "barrio tranquilo", "noche": "noche, con grillos",
             "mar": "mar abierto", "campo": "campo, con pájaros y cencerros", "montana": "montaña, con viento"}
MOTORES = {"avioneta": "avioneta", "coche": "coche", "deportivo": "deportivo", "moto": "moto", "camion": "camión o autobús", "furgoneta": "furgoneta o todoterreno", "lancha": "lancha",
           "barco": "barco grande", "tractor": "tractor", "helicoptero": "helicóptero", "bici": "bicicleta, el clic de la cadena"}
ARMAS = {"pistola": "pistola", "revolver": "revólver", "subfusil": "subfusil", "escopeta": "escopeta", "rifle": "rifle", "fusil": "fusil de asalto", "silenciado": "pistola con silenciador",
         "rafaga": "pistola de ráfagas: seco y muy corto", "corredera": "escopeta de corredera: un estampido grave y, detrás, la corredera",
         "palanca": "rifle de palanca: el disparo y, detrás, la palanca", "semiautomatico": "fusil semiautomático"}

DESCRIPCIONES = {
    "avion": "La cabina del avión de pasajeros en vuelo. En bucle.", "avion_despegue": "El avión acelerando por la pista y despegando.",
    "lugar_tranvia": "Firma sonora de: parada de tranvía. Dos toques de campana. En bucle.", "lugar_tren": "Firma sonora de: estación de tren. Resoplidos de locomotora. En bucle.",
    "lugar_aeropuerto": "Firma sonora de: aeropuerto. El aviso de megafonía, tres notas que bajan. En bucle.",
    "tren": "El vagón del tren en marcha, con el traqueteo de los raíles. En bucle.", "tren_silbato": "El silbato del tren al salir de la estación.",
    "tranvia": "El tranvía en marcha: el zumbido del motor eléctrico y los raíles. En bucle.", "tranvia_campana": "La campana del tranvía al arrancar: dos toques.",
    "bajo_agua": "Lo que se oye buceando: un rumor sordo y burbujas. En bucle.", "brazada": "Una brazada al nadar.",
    "menu_mover": "Al pasar de una opción a otra en un menú.", "menu_ok": "Al elegir una opción.", "menu_atras": "Al volver atrás.",
    "menu_borde": "Al llegar al principio o al final de un menú, o al borde del mapa.", "menu_ajuste": "Al cambiar el valor de una opción.",
    "error": "Algo no se puede hacer.", "notificacion": "Aviso general: misión nueva, destino marcado.", "mision_ok": "Misión completada.",
    "mision_fallo": "Misión fallida, o has caído.", "dinero": "Ganas dinero.", "guardado": "Partida guardada.", "movil": "Abres el móvil.",
    "dialogo": "Empieza cada frase de un diálogo.", "pasan_horas": "Pasan las horas: dormir, esconderse.", "logro": "Logro conseguido.",
    "nivel": "Sube una habilidad.", "evento": "Suceso callejero cerca.", "caja": "Caja registradora: compras y banco.", "reloj": "Cuenta atrás, cada segundo de los diez últimos.",
    "amigo_entra": "Un amigo se une a la partida, o te conectas tú. Tres notas que suben.",
    "amigo_sale": "Un amigo se va, o te desconectas. Tres notas que bajan.", "chat": "Llega o se envía un mensaje de un amigo. Dos notas agudas y rápidas.",
    "llegada": "Has llegado al destino o has cumplido un paso.", "recoger": "Recoges un objeto.", "curar": "Recuperas salud.", "comer": "Comes o bebes.",
    "baliza": "Baliza del GPS hacia el siguiente punto de la ruta.", "baliza_destino": "Baliza del GPS cuando lo siguiente ya es el destino. También es el tono del norte.",
    "sonar": "Sensor de proximidad al volante, y el pitido de frío o caliente al buscar tesoros.", "tono_objetivo": "Enemigo fijado y a tiro.",
    "tono_apuntado": "Enemigo fijado pero fuera de alcance.", "tono_pared": "El escáner direccional encuentra una pared.", "tono_libre": "El escáner direccional no encuentra pared.",
    "bordillo": "En conducción libre, te sales de la calzada.", "cruce": "Entras en un cruce.", "radar": "Suena desde lo que anuncia el radar.",
    "cursor_mapa": "El cursor del explorador de mapa avanza. También, al leer un tablón dentro de un local.", "semaforo_tic": "Semáforo: puedes cruzar la calle. Se repite muy rápido, así que debe ser un clic muy corto.",
    "semaforo_pio": "Semáforo: puedes cruzar la avenida. Se repite una vez por segundo.", "choque_pared": "Chocas contra una pared caminando.",
    "paso_npc": "Pasos de otras personas.", "dolor": "Te hieren.", "dolor_npc": "Hieres a alguien: la queja de un hombre.", "dolor_mujer": "Hieres a alguien: la queja de una mujer.", "muerte_npc": "Alguien cae abatido.", "grito": "Un grito: el tuyo para espantar a la gente, y el de aviso de un enemigo que te ha visto.",
    "grito_hombre": "Un hombre grita de susto al salir corriendo.", "grito_mujer": "Una mujer grita de susto al salir corriendo.",
    "recoger_municion": "Recoges munición o un arma que ha soltado un enemigo caído: un cargador que entra y el cerrojo.",
    "helicoptero_policia": "El helicóptero de la policía, con el nivel de búsqueda más alto: se le oye llegar y dar vueltas por encima. En bucle.",
    "megafono": "El altavoz del helicóptero de la policía: un acople y una voz metálica. Lo que dice lo lee el lector a continuación.",
    "timbre": "Llaman al timbre de tu casa: llega la comida que has pedido a domicilio. Dos notas, din, don.",
    "emisora": "La emisora de la policía, cuando trabajas de agente: el chasquido del canal y dos pitidos. Entras de servicio, llega un aviso o termina el turno; lo que dice lo lee el lector.",
    "murmullo": "Un peatón murmura al hablarte, o dos que pasan hablando entre ellos.", "golpe": "Un puñetazo o un golpe que acierta.", "golpe_aire": "Un golpe al aire.",
    "latido": "Tu corazón cuando te queda poca salud. En bucle.", "ladrido": "Ladrido de perro.", "sin_balas": "Aprietas el gatillo sin balas.", "recarga": "Recargas el arma.",
    "amartillar": "Un enemigo va a dispararte, y también al cambiar de arma.", "bala_impacto": "Una bala da en algo.", "bala_silbido": "Una bala te pasa rozando.",
    "explosion": "Explosión.", "navaja": "Tajo de navaja, machete o katana.", "lanzar": "Lanzas una granada o disparas la ballesta.", "cohete": "Disparo del lanzacohetes.",
    "hacha": "Golpe de hacha: el silbido y el golpe sordo del filo.", "lanzagranadas": "Disparo del lanzagranadas: un golpe hueco, de tubo.",
    "rodadura": "Ruido de neumáticos de tu vehículo. En bucle; el volumen sube con la velocidad.", "claxon": "Claxon de coche. También lo toca dos veces tu chófer al llegar, y tu mecánico cuando te deja un vehículo.", "claxon_camion": "Bocina de camión.",
    "claxon_bici": "Timbre de bicicleta.", "claxon_helados": "Musiquilla de la furgoneta de helados.", "claxon_lejano": "Un claxon a lo lejos, de ambiente.",
    "frenazo": "Frenazo o derrape.", "choque": "Choque fuerte.", "choque_leve": "Choque leve.", "puerta_coche": "Puerta de un vehículo.",
    "alarma": "Alarma de coche. En bucle.", "arranque": "Arrancas el motor.", "sirena": "Sirena de policía y de bomberos. En bucle.",
    "sirena_ambulancia": "Sirena de ambulancia: la tuya, o la de la que acude tras un tiroteo o un atropello. En bucle.", "sirena_lejana": "Una sirena a lo lejos, de ambiente.", "sirena_barco": "Sirena de barco al zarpar.",
    "cristal": "Cristales rotos.", "ganzua": "Fuerzas una cerradura. En bucle.", "intermitente": "Intermitente. En bucle.", "radio_cambio": "Cambias de emisora.",
    "pinchazo": "Revienta una rueda y se escapa el aire.", "multa": "El silbato del agente: te han multado.", "beber": "Unos tragos de agua.",
    "repostar": "El surtidor llenando el depósito.", "reserva": "Aviso de que queda poco combustible.", "motor_seco": "El motor tose y se para sin combustible.",
    "reparar": "Reparación en el taller.", "pintura": "Pintan el vehículo.", "fuego": "Un vehículo o un edificio ardiendo. En bucle.",
    "estrella_sube": "Sube el nivel de búsqueda.", "estrella_baja": "Baja el nivel de búsqueda.", "policia_perdida": "Has despistado a la policía.",
    "buscando": "Te buscan pero no te ven: se repite cada segundo. Más agudo, es el helicóptero de la policía el que no te ve.", "esposas": "Te detienen.", "loc_objeto": "Un objeto que se puede recoger.",
    "loc_casete": "Un objeto de colección.", "loc_mision": "Un lugar con una misión disponible.", "loc_lugar": "Un lugar sin sonido propio.",
    "loc_vehiculo": "El vehículo que pide la misión, y el de tu chófer mientras te espera. En bucle.", "lluvia": "Lluvia. En bucle.", "multitud": "Murmullo de gente. En bucle.", "viento_playa": "Copia del ambiente de playa.",
    "trueno": "Trueno.", "gaviota": "Gaviotas.", "pajaro": "Un pájaro.", "martillo": "Martillazos de obra.", "salpicadura": "Chapuzón.",
    "pesca_lanzar": "Lanzas el anzuelo.", "pez_pica": "Pican: hay que pulsar enseguida.", "carrete": "Recoges el sedal.", "diana": "Aparece una diana en la galería de tiro.",
    "diana_ok": "Aciertas una diana.", "ruleta": "Gira la ruleta.", "dados": "Ruedan los dados.", "campana_ring": "Campana de inicio del combate de boxeo.",
    "puerta_entrar": "Entras en un local: la puerta y su campanilla. Mientras estás dentro suena de fondo el sonido del lugar.",
    "puerta_salir": "Sales de un local: la campanilla y la puerta que se cierra.", "campanadas": "Medianoche: empieza un día nuevo.",
    "gallo": "Amanece, a las siete de la mañana.", "buho": "Anochece, a las nueve de la noche.", "agacharse": "Te agachas.", "levantarse": "Te levantas.",
    "hospital_despertar": "Despiertas en el hospital.", "celda": "La puerta del calabozo: te han detenido.", "ascenso": "Asciendes en un oficio.",
    "diploma": "Terminas un curso.", "donativo": "Haces un donativo: monedas.", "prestigio": "Mejora tu prestigio entre los vecinos.",
    "jornada": "Una jornada de trabajo: la sirena de la fábrica y pasan las horas.",
    "animo_sube": "Tu ánimo mejora de nivel.", "animo_baja": "Tu ánimo empeora de nivel.", "fama": "Cambia tu fama en la calle.",
    "perro_olfatea": "Tu perro olfatea buscando algo.", "bolsa": "Compras acciones en la bolsa.", "territorio": "Has conquistado un barrio.",
    "afinidad_sube": "Alguien te aprecia más: charla, cita o regalo.", "afinidad_baja": "Alguien se ha disgustado contigo.",
    "pareja": "Empiezas una relación de pareja: dos latidos y un arpegio.", "ruptura": "Se rompe una relación.",
    "noche_juntos": "Pasáis la noche juntos. La escena se resuelve con un fundido.", "cita": "Una cita.", "regalo": "Entregas un regalo: papel de envolver.",
    "tomar_copa": "Tomas una copa: se sirve y se brinda.", "tomar_hierba": "Fumas hierba: mechero, calada y humo.",
    "tomar_pastillas": "Tomas una pastilla: el blíster y un trago.", "tomar_polvo": "Tomas polvo blanco.", "tomar_cristal": "Tomas cristal: crepita.",
    "bajon": "Se pasa el efecto de una sustancia y llega el bajón.", "abstinencia": "Síndrome de abstinencia: un temblor.",
    "sobredosis": "Sobredosis: el corazón se frena y suena un pitido continuo.", "trato": "Un trato cerrado: billetes y un paquete que cambia de manos.",
    "rechazo": "Alguien rechaza lo que le ofreces.", "paisano": "El comprador era un policía de paisano.",
    "precio_ganga": "En el proveedor, esa sustancia hoy está muy barata.", "precio_escasez": "En el proveedor, esa sustancia hoy está muy cara.",
    "simon_0": "Máquina de memoria: nota de la flecha arriba, la más aguda.", "simon_1": "Máquina de memoria: nota de la flecha derecha.",
    "simon_2": "Máquina de memoria: nota de la flecha abajo, la más grave.", "simon_3": "Máquina de memoria: nota de la flecha izquierda.",
}


def describir(nombre):
    if nombre in DESCRIPCIONES:
        return DESCRIPCIONES[nombre]
    if nombre.startswith("paso_"):
        suelo = nombre[5:-1]
        return f"Tus pasos sobre {SUELOS.get(suelo, suelo)}, pie {'izquierdo' if nombre.endswith('0') else 'derecho'}."
    if nombre.startswith("disparo_"):
        return f"Disparo de {ARMAS.get(nombre[8:], nombre[8:])}."
    if nombre.startswith("motor_"):
        return f"Motor de {MOTORES.get(nombre[6:], nombre[6:])}. En bucle."
    if nombre.startswith("lugar_"):
        return f"Firma sonora de: {LUGARES.get(nombre[6:], nombre[6:])}. En bucle."
    if nombre.startswith("amb_"):
        return f"Ambiente de {AMBIENTES.get(nombre[4:], nombre[4:])}. En bucle."
    return "Sonido del juego."


def grupo_de(nombre):
    for k, (titulo, _, prefijos, nombres) in enumerate(GRUPOS):
        if nombre in nombres or (prefijos and nombre.startswith(prefijos)):
            return k
    return len(GRUPOS)
