"""Catálogo de sonidos: qué es cada archivo de data/sonidos, cómo se llama en voz alta y en qué grupo va.

Es la única clasificación del juego. De aquí salen, con los mismos grupos, los mismos nombres y el mismo orden:
Aprender los sonidos, el volumen de cada sonido de Opciones, la guía de sonidos (cambiar_sonidos.html) y la lista para
hacer packs. Un sonido nuevo se apunta aquí, en SONIDOS, dentro de su grupo, con su nombre hablado y su explicación.

Los grupos son por lo que se hace en el juego, no por cómo está hecho el sonido. Dentro de cada grupo el orden es
alfabético por el nombre que se dice, así que da igual en qué orden se escriban aquí.
"""
import unicodedata

# clave, título que se dice, y consejo para quien cambia sonidos (solo sale en la guía)
GRUPOS = [
    ("Orientación y GPS", "Son la base de la accesibilidad del juego. Si los cambias, que sigan siendo cortos, claros y fáciles de localizar en el espacio. "
     "Los localizadores suenan en bucle desde la posición de un objeto o de una misión.", "orientacion"),
    ("Sonidos de los lugares", "Cada tipo de lugar emite su sonido en bucle para reconocerlo al pasar. Deben ser distintos entre sí y no cansar: piensa que se oyen muchas veces.", "lugares"),
    ("Moverse a pie y nadar", "Hay dos variantes de los pasos de cada suelo, que se alternan pie izquierdo y pie derecho. Deben durar menos de un cuarto de segundo.", "pie"),
    ("Vehículos y conducción", "Los motores se reproducen en bucle y el juego les sube el tono con la velocidad. Graba el motor al ralentí, a régimen constante.", "conducir"),
    ("Averías, taller, gasolina y robo de vehículos", "Lo que le pasa a un vehículo cuando no lo estás conduciendo sin más.", "taller"),
    ("Barcos, helicópteros, tren, tranvía y avión", "El tren, el tranvía y la cabina del avión suenan en bucle, igual que los motores.", "transporte"),
    ("Armas, el disparo de cada una", "El disparo de cada arma debe reconocerse sin mirar: procura que no se parezcan entre sí.", "disparos"),
    ("Combate, puntería y heridas", "Recargas, impactos, golpes, los tonos de la puntería y lo que se oye cuando hieren a alguien.", "combate"),
    ("Policía y emergencias", "Avisos del nivel de búsqueda, sirenas y el helicóptero de la policía.", "policia"),
    ("Gente de la calle y animales", "Voces sin palabras, pasos de otros y el perro.", "gente"),
    ("Casa, cocina y comida", "Comer, beber, cocinar en casa y que llamen a la puerta.", "casa"),
    ("Tiendas, dinero y objetos", "Comprar, cobrar y recoger cosas.", "dinero"),
    ("Menús, móvil y avisos del juego", "Sonidos cortos de la interfaz. Conviene que sean breves y discretos.", "avisos"),
    ("Misiones, trabajo, reputación y ánimo", "Lo que suena al acabar una misión, en el trabajo honrado y cuando cambia cómo te ven o cómo estás.", "trabajo"),
    ("Territorios y bandas", "Los avisos de los barrios que son tuyos.", "territorios"),
    ("Jugar en línea y rol", "Avisos de la partida compartida y de los canales de rol de los servidores.", "linea"),
    ("Pesca, casino y juegos", "La pesca y los juegos del casino, de la feria y del gimnasio.", "juegos"),
    ("Ambientes y clima", "Bucles largos que suenan de fondo en cada barrio, con la lluvia y de noche, y sonidos sueltos que aparecen de vez en cuando alrededor.", "ambientes"),
    ("Relaciones, solo con el contenido para adultos", "Relaciones sentimentales.", "relaciones"),
    ("Sustancias y trapicheo, solo con el contenido para adultos", "Cada sustancia tiene su sonido al tomarla, para reconocerla sin mirar.", "sustancias"),
]
OTROS = "Otros sonidos"            # solo para un sonido que no esté apuntado aquí: un archivo añadido a mano

# grupo -> [(archivo, nombre que se dice, qué significa oírlo en el juego), ...]
SONIDOS = {
    "orientacion": [
        ("baliza", "Baliza del GPS", "Suena en la dirección del siguiente punto de la ruta. Cuanto más cerca estás, más rápido se repite."),
        ("baliza_destino", "Baliza de destino", "La baliza del GPS cambia a este sonido cuando lo siguiente ya es tu destino. También es el tono que marca el norte."),
        ("llegada", "Llegada", "Has llegado al destino o has completado un paso de la misión."),
        ("cruce", "Cruce", "Entras en un cruce de calles, o te acercas a uno al volante."),
        ("radar", "Radar", "Suena desde la posición de lo que acaba de anunciar el radar."),
        ("tono_pared", "Escáner, pared", "El escáner direccional ha encontrado una pared. Suena más agudo cuanto más cerca está."),
        ("tono_libre", "Escáner, camino despejado", "El escáner direccional no encuentra ninguna pared en esa dirección."),
        ("semaforo_tic", "Semáforo, tictac rápido", "Los coches de la calle están parados: puedes cruzar la calle, andando hacia el norte o hacia el sur."),
        ("semaforo_pio", "Semáforo, pío lento", "Los coches de la avenida están parados: puedes cruzar la avenida, andando hacia el este o hacia el oeste."),
        ("cursor_mapa", "Cursor del explorador de mapa", "El cursor del explorador de mapa ha pasado al cruce siguiente. También suena al leer un tablón dentro de un local."),
        ("sonar", "Sensor de proximidad", "Al volante, hay un vehículo delante: pita más rápido y más agudo cuanto más cerca está. También es el pitido de frío o caliente al buscar tesoros."),
        ("bordillo", "Bordillo", "En conducción libre, te sales de la calzada por el lado en el que suena."),
        ("loc_mision", "Misión disponible", "Suena desde un lugar donde hay una misión esperándote."),
        ("loc_objeto", "Objeto que puedes recoger", "Suena desde un objeto que hay en el suelo. Ponte encima y recógelo."),
        ("loc_casete", "Objeto de colección", "Suena desde una de las cintas de casete escondidas por la ciudad, o desde otro objeto de colección."),
        ("loc_vehiculo", "Vehículo de la misión", "Suena desde el vehículo que te pide la misión, y desde el de tu chófer mientras te espera."),
        ("loc_lugar", "Punto de interés", "Suena desde un punto de interés que no tiene sonido propio."),
    ],
    "lugares": [
        ("puerta_entrar", "Entrar en un local", "Entras en un local: la puerta y su campanilla. Mientras estás dentro suena de fondo el sonido del lugar."),
        ("puerta_salir", "Salir de un local", "Sales de un local: la campanilla y la puerta que se cierra."),
        ("lugar_academia", "Academia o autoescuela", "Estás junto a una academia o una autoescuela: el timbre de clase."),
        ("lugar_aeropuerto", "Aeropuerto", "Estás junto al aeropuerto: el aviso de megafonía, tres notas que bajan."),
        ("lugar_armeria", "Armería", "Estás junto a una armería: un arma que se amartilla."),
        ("lugar_banco", "Banco o casa de empeños", "Estás junto a un banco o una casa de empeños: los pitidos de un cajero automático."),
        ("lugar_bar", "Bar, taberna o discoteca", "Estás junto a un bar, una taberna, una discoteca o un negocio: graves de música a través de la pared."),
        ("lugar_boya", "Muelle, boya o punto de pesca", "Estás junto a un muelle, una boya, un punto de pesca o un tesoro en el mar: una campana de boya entre las olas."),
        ("lugar_casa", "Casa", "Estás junto a una vivienda o un hotel, tuya o que puedes comprar: campanillas de viento."),
        ("lugar_casino", "Casino o feria", "Estás junto a un casino o una feria: la musiquilla de las máquinas tragaperras."),
        ("lugar_cine", "Cine", "Estás junto a un cine: el traqueteo de un proyector."),
        ("lugar_club", "Club nocturno, contenido para adultos", "Estás junto a un club nocturno: música amortiguada y copas."),
        ("lugar_comida", "Restaurante, pizzería o chiringuito", "Estás junto a un sitio donde se come: algo friéndose."),
        ("lugar_comisaria", "Comisaría", "Estás junto a una comisaría: una emisora de policía."),
        ("lugar_contacto", "Lugar con un contacto", "Estás junto a un lugar donde te espera alguien con un encargo."),
        ("lugar_embarcadero", "Embarcadero o tienda náutica", "Estás junto a un embarcadero: el agua contra los pantalanes y las amarras que crujen."),
        ("lugar_empleo", "Oficina de empleo", "Estás junto a la oficina de empleo: teclados y el aviso de turno."),
        ("lugar_estacion", "Estación de autobuses", "Estás junto a la estación de autobuses: frenos de aire y megafonía."),
        ("lugar_fuente", "Fuente", "Estás junto a una fuente: agua cayendo."),
        ("lugar_generico", "Lugar sin sonido propio", "Estás junto a un lugar de un tipo que no tiene sonido propio."),
        ("lugar_gimnasio", "Gimnasio", "Estás junto a un gimnasio: pesas que chocan."),
        ("lugar_helipuerto", "Helipuerto", "Estás junto a un helipuerto: palas girando y un pitido de torre de control."),
        ("lugar_hospital", "Hospital o farmacia", "Estás junto a un hospital o una farmacia: el pitido de un monitor."),
        ("lugar_iglesia", "Iglesia", "Estás junto a una iglesia: una campana."),
        ("lugar_mina", "Mina", "Estás junto a una mina: picos contra la roca."),
        ("lugar_ong", "Comedor social", "Estás junto a un comedor social o una organización benéfica: platos y cubiertos."),
        ("lugar_periodico", "Periódico o librería", "Estás junto a un periódico o una librería: el tecleo de las máquinas de escribir."),
        ("lugar_prision", "Prisión", "Estás junto a la prisión: una reja que se cierra y una sirena lejana."),
        ("lugar_protectora", "Protectora de animales", "Estás junto a la protectora, donde puedes adoptar un perro: ladridos."),
        ("lugar_proveedor", "Proveedor, contenido para adultos", "Estás junto a un proveedor, donde se compra y se vende mercancía: dos siseos y una persiana metálica."),
        ("lugar_rio", "Río", "Estás junto a un río: agua corriendo entre piedras."),
        ("lugar_salida", "Salida por carretera", "Estás junto a una salida de la ciudad: coches que pasan deprisa. Por aquí se va a otra localidad."),
        ("lugar_taller", "Taller, desguace o concesionario", "Estás junto a un taller, un desguace o un concesionario: una pistola neumática."),
        ("lugar_taxi", "Parada de taxis o salida de carreras", "Estás junto a una parada de taxis o a la salida de una carrera: dos toques cortos de claxon."),
        ("lugar_tienda", "Tienda", "Estás junto a una tienda: el timbre de la puerta."),
        ("lugar_tranvia", "Parada de tranvía", "Estás junto a una parada de tranvía: dos toques de campana."),
        ("lugar_tren", "Estación de tren", "Estás junto a la estación de tren: resoplidos de locomotora."),
    ],
    "pie": [
        ("paso_acera0", "Pasos en la acera, pie izquierdo", "Caminas por la acera."),
        ("paso_acera1", "Pasos en la acera, pie derecho", "Caminas por la acera. Los dos pies suenan un poco distinto."),
        ("paso_calzada0", "Pasos en la calzada, pie izquierdo", "Caminas por el asfalto: cuidado con los coches."),
        ("paso_calzada1", "Pasos en la calzada, pie derecho", "Caminas por el asfalto, por donde van los coches."),
        ("paso_hierba0", "Pasos en el césped, pie izquierdo", "Caminas por el césped de un parque o por el campo."),
        ("paso_hierba1", "Pasos en el césped, pie derecho", "Caminas por el césped, con el otro pie."),
        ("paso_arena0", "Pasos en la arena, pie izquierdo", "Caminas por la arena de la playa."),
        ("paso_arena1", "Pasos en la arena, pie derecho", "Caminas por la arena, con el otro pie."),
        ("paso_muelle0", "Pasos en el muelle, pie izquierdo", "Caminas sobre los tablones de un muelle."),
        ("paso_muelle1", "Pasos en el muelle, pie derecho", "Caminas sobre los tablones de un muelle, con el otro pie."),
        ("paso_plaza0", "Pasos en una plaza, pie izquierdo", "Caminas sobre las losas de una plaza."),
        ("paso_plaza1", "Pasos en una plaza, pie derecho", "Caminas sobre las losas de una plaza, con el otro pie."),
        ("paso_via0", "Pasos sobre las vías, pie izquierdo", "Estás en medio de las vías del tranvía o del tren: un toque metálico, del raíl, con grava debajo."),
        ("paso_via1", "Pasos sobre las vías, pie derecho", "Sigues sobre las vías del tranvía o del tren: sal de ellas."),
        ("choque_pared", "Choque con una pared", "Has intentado caminar contra una pared."),
        ("agacharse", "Agacharte", "Te agachas: haces menos ruido y cuesta más verte."),
        ("levantarse", "Levantarte", "Te pones de pie después de estar agachado."),
        ("salpicadura", "Chapuzón", "Alguien o algo cae al agua: tú, un vehículo o lo que tiras al mar."),
        ("brazada", "Brazada", "Suena con cada brazada que das nadando."),
        ("bajo_agua", "Bajo el agua", "Estás buceando: un rumor sordo con burbujas."),
    ],
    "conducir": [
        ("motor_coche", "Motor de coche", "El motor de un coche. Sube de tono con la velocidad."),
        ("motor_deportivo", "Motor de deportivo", "El motor de un deportivo, más bronco que el de un coche normal."),
        ("motor_moto", "Motor de moto", "El motor de una moto."),
        ("motor_camion", "Motor de camión o autobús", "El motor de un camión o de un autobús, grave y pesado."),
        ("motor_furgoneta", "Motor de furgoneta o todoterreno", "El motor de una furgoneta o de un todoterreno."),
        ("motor_tractor", "Motor de tractor", "El motor de un tractor, lento y a golpes."),
        ("motor_bici", "Bicicleta", "Vas en bicicleta: el clic de la cadena."),
        ("rodadura", "Ruedas sobre el asfalto", "El ruido de los neumáticos de tu vehículo. Suena más fuerte cuanto más corres."),
        ("arranque", "Arrancar el motor", "Arrancas el motor de un vehículo."),
        ("puerta_coche", "Puerta de un vehículo", "Subes a un vehículo o te bajas de él."),
        ("claxon", "Claxon de coche", "Tocas el claxon, o te lo toca otro conductor. Tu chófer lo toca dos veces al llegar, y tu mecánico cuando te deja un vehículo."),
        ("claxon_camion", "Bocina de camión", "La bocina de un camión o de un autobús."),
        ("claxon_bici", "Timbre de bicicleta", "El timbre de una bicicleta."),
        ("claxon_helados", "Musiquilla de la furgoneta de helados", "La furgoneta de helados, en lugar de claxon, toca su musiquilla."),
        ("frenazo", "Frenazo", "Un vehículo frena de golpe o derrapa."),
        ("choque", "Choque fuerte", "Un golpe fuerte con el vehículo: se daña."),
        ("choque_leve", "Choque leve", "Un roce o un golpe flojo con el vehículo."),
        ("intermitente", "Intermitente", "Has pedido girar en el próximo cruce. Suena hasta que giras."),
        ("radio_cambio", "Cambio de emisora", "Cambias de emisora en la radio de un vehículo, o la apagas."),
    ],
    "taller": [
        ("pinchazo", "Pinchazo", "Revienta una rueda y se escapa el aire: el vehículo tira hacia un lado."),
        ("reserva", "Poco combustible", "Aviso de que al vehículo le queda poco combustible: busca una gasolinera."),
        ("motor_seco", "Sin combustible", "El motor tose y se para: te has quedado sin combustible."),
        ("repostar", "Repostar", "El surtidor está llenando el depósito."),
        ("reparar", "Reparación en el taller", "Te reparan el vehículo en un taller."),
        ("pintura", "Pintar el vehículo", "Te pintan el vehículo en un taller: la policía deja de reconocerlo."),
        ("alarma", "Alarma de coche", "Ha saltado la alarma de un vehículo o de un local."),
        ("ganzua", "Ganzúa", "Estás forzando la cerradura de un vehículo."),
        ("cristal", "Cristales rotos", "Se rompe un cristal: una ventanilla o un escaparate."),
        ("fuego", "Fuego", "Un vehículo o un edificio está ardiendo. Si es un vehículo, va a explotar: aléjate."),
    ],
    "transporte": [
        ("motor_lancha", "Motor de lancha", "El motor de una lancha o de otra embarcación rápida."),
        ("motor_barco", "Motor de barco", "El motor de un barco grande: un pesquero, un velero o un yate."),
        ("sirena_barco", "Sirena de barco", "Un barco zarpa. En el mar, también marca que anochece."),
        ("motor_helicoptero", "Helicóptero", "Las palas de un helicóptero en el que vas tú."),
        ("motor_avioneta", "Avioneta", "El zumbido de la hélice de una avioneta."),
        ("avion", "Avión de pasajeros", "Vas de viaje en avión: el zumbido de la cabina en vuelo."),
        ("avion_despegue", "Despegue del avión", "El avión acelera por la pista y despega."),
        ("tren", "Tren", "Vas de viaje en tren: el vagón en marcha, con el traqueteo de los raíles."),
        ("tren_silbato", "Silbato del tren", "El tren sale de la estación."),
        ("tranvia", "Tranvía", "Vas en tranvía: un zumbido eléctrico sobre raíles."),
        ("tranvia_campana", "Campana del tranvía", "El tranvía arranca: dos toques de campana."),
        ("tono_altitud", "Tono de altitud", "Pilotando, una nota que suena cada vez que cambias de altura: cuanto más aguda, más alto vuelas."),
        ("tono_alineacion", "Tono de alineación", "Pilotando sin piloto automático, dos chasquidos que suenan hacia el lado al que tienes que virar. Por el centro y más agudos, vas bien encarado."),
        ("turbulencia", "Turbulencia", "El aparato se zarandea: hay turbulencias, o estás atravesando una tormenta."),
        ("alarma_cabina", "Alarma de cabina", "Pilotando, cuatro pitidos apremiantes: queda muy poco combustible, hay un obstáculo o tráfico delante, o el motor se ha parado."),
        ("aterrizaje", "Aterrizaje", "El aparato toca tierra: un golpe, el chirrido de las ruedas y la rodadura que se apaga."),
    ],
    "disparos": [
        ("disparo_pistola", "Disparo de pistola", "Alguien dispara una pistola."),
        ("disparo_revolver", "Disparo de revólver", "Alguien dispara un revólver: más grave y rotundo que la pistola."),
        ("disparo_silenciado", "Disparo de pistola con silenciador", "Un disparo apagado: apenas lo oye nadie alrededor."),
        ("disparo_rafaga", "Disparo de pistola de ráfagas", "Un disparo seco y muy corto, que se repite muy deprisa."),
        ("disparo_subfusil", "Disparo de subfusil", "Alguien dispara un subfusil o una ametralladora: ráfagas rápidas."),
        ("disparo_escopeta", "Disparo de escopeta", "Alguien dispara una escopeta: un estampido ancho."),
        ("disparo_corredera", "Disparo de escopeta de corredera", "Un estampido grave y, detrás, la corredera."),
        ("disparo_rifle", "Disparo de rifle", "Alguien dispara un rifle de precisión o una carabina: seco y con eco."),
        ("disparo_palanca", "Disparo de rifle de palanca", "El disparo y, detrás, la palanca que carga el siguiente."),
        ("disparo_fusil", "Disparo de fusil de asalto", "Alguien dispara un fusil de asalto."),
        ("disparo_semiautomatico", "Disparo de fusil semiautomático", "Alguien dispara un fusil semiautomático: tiros sueltos y fuertes."),
        ("cohete", "Disparo del lanzacohetes", "Sale un cohete: después vendrá la explosión."),
        ("lanzagranadas", "Disparo del lanzagranadas", "Un golpe hueco, de tubo: sale una granada."),
        ("lanzar", "Lanzamiento", "Alguien lanza una granada o un cóctel molotov, o dispara una ballesta."),
    ],
    "combate": [
        ("tono_objetivo", "Enemigo fijado, a tiro", "Suena desde donde está el enemigo fijado: está dentro del alcance de tu arma."),
        ("tono_apuntado", "Enemigo fijado, fuera de alcance", "Suena desde donde está el enemigo fijado: está demasiado lejos para tu arma."),
        ("amartillar", "Van a dispararte", "Un enemigo prepara el arma: medio segundo después disparará. También suena cuando cambias de arma."),
        ("bala_silbido", "Bala que falla", "Un disparo te ha pasado rozando."),
        ("bala_impacto", "Impacto de bala", "Una bala da en una pared, en un vehículo o en otra cosa."),
        ("recarga", "Recarga", "Recargas el arma."),
        ("sin_balas", "Sin balas", "Aprietas el gatillo y el arma está vacía: recarga o cambia de arma."),
        ("recoger_municion", "Munición recogida", "Recoges munición o un arma que ha soltado un enemigo caído: un cargador que entra y el cerrojo."),
        ("golpe", "Golpe que acierta", "Un puñetazo, un batazo o un atropello que da en alguien."),
        ("golpe_aire", "Golpe al aire", "Un golpe que no da en nadie."),
        ("navaja", "Tajo de navaja", "Un tajo de navaja, de machete o de katana."),
        ("hacha", "Golpe de hacha", "Un golpe de hacha: el silbido y el golpe sordo del filo."),
        ("explosion", "Explosión", "Ha explotado una granada, un cohete o un vehículo."),
        ("dolor", "Te han herido", "Has recibido daño."),
        ("latido", "Latido", "Te queda muy poca salud: cúrate o ponte a cubierto."),
        ("curar", "Curación", "Recuperas salud, o una ambulancia atiende a los heridos."),
        ("dolor_npc", "Quejido de un hombre", "Has herido a un hombre."),
        ("dolor_mujer", "Quejido de una mujer", "Has herido a una mujer."),
        ("muerte_npc", "Alguien cae", "Alguien cae abatido."),
        ("hospital_despertar", "Despertar en el hospital", "Has perdido el conocimiento y despiertas en el hospital."),
    ],
    "policia": [
        ("estrella_sube", "Sube el nivel de búsqueda", "La policía te busca con más ganas."),
        ("estrella_baja", "Baja el nivel de búsqueda", "La policía te busca con menos ganas."),
        ("buscando", "Te están buscando", "Te buscan pero no te ven: sigue así unos segundos y los despistarás. Más agudo, es el helicóptero el que no te ve."),
        ("policia_perdida", "Policía despistada", "Ya no te buscan."),
        ("sirena", "Sirena de policía", "Un coche patrulla que va a por ti, o un camión de bomberos."),
        ("sirena_ambulancia", "Sirena de ambulancia", "Una ambulancia: la tuya, o la que acude tras un tiroteo o un atropello."),
        ("helicoptero_policia", "Helicóptero de la policía", "Con el nivel de búsqueda más alto, el helicóptero de la policía: se le oye llegar y dar vueltas por encima."),
        ("megafono", "Altavoz del helicóptero", "El helicóptero de la policía te habla por el altavoz: un acople y una voz metálica. Lo que dice se lee a continuación."),
        ("esposas", "Esposas", "Te detienen."),
        ("celda", "Puerta del calabozo", "Te han detenido y te encierran: la puerta del calabozo."),
        ("multa", "Multa", "Te han puesto una multa: el silbato del agente."),
        ("emisora", "Emisora de la policía", "Cuando trabajas de agente: el chasquido del canal y dos pitidos. Entras de servicio, llega un aviso o termina el turno."),
    ],
    "gente": [
        ("paso_npc", "Pasos de otra persona", "Alguien camina cerca de ti."),
        ("murmullo", "Murmullo", "Un peatón murmura al hablarte, o dos que pasan van hablando entre ellos."),
        ("grito", "Grito", "Un grito: el tuyo para espantar a la gente, o el de un enemigo que te ha visto y avisa a los suyos."),
        ("grito_hombre", "Grito de un hombre asustado", "Un hombre grita de susto y sale corriendo."),
        ("grito_mujer", "Grito de una mujer asustada", "Una mujer grita de susto y sale corriendo."),
        ("evento", "Suceso callejero", "Algo está pasando cerca: un atraco, unos pandilleros o un maletín perdido. Ayudar es opcional."),
        ("ladrido", "Ladrido", "Un perro ladra. Si es el tuyo, avisa de un enemigo cercano o de que ha olfateado algo."),
        ("perro_olfatea", "El perro olfatea", "Tu perro busca por el olfato el objeto más cercano."),
    ],
    "casa": [
        ("comer", "Comer", "Comes algo: recuperas fuerzas."),
        ("beber", "Beber", "Bebes unos tragos."),
        ("nevera", "Nevera", "Abres la nevera de casa o guardas la compra: la goma de la puerta y el zumbido del motor."),
        ("cocina_cortar", "Cocinar, el cuchillo", "Empiezas a cocinar: el cuchillo picando sobre la tabla."),
        ("cocina_freir", "Cocinar, la sartén", "Cocinas a la sartén: el aceite chisporroteando."),
        ("cocina_hervir", "Cocinar, la olla", "Cocinas a la olla: el agua borboteando."),
        ("plato_servido", "Plato servido", "El plato está hecho: la loza en la mesa y los cubiertos."),
        ("timbre", "Timbre de casa", "Llaman al timbre de tu casa: llega la comida que has pedido a domicilio. Dos notas, din, don."),
    ],
    "dinero": [
        ("dinero", "Dinero", "Has ganado dinero."),
        ("caja", "Caja registradora", "Pagas una compra o haces una operación en el banco."),
        ("cesta", "Cesta de la compra", "Echas un producto a la cesta: un golpe sordo y el alambre que tiembla. Más grave, lo devuelves al estante."),
        ("bolsa", "Bolsa", "Has comprado acciones en la bolsa."),
        ("recoger", "Objeto recogido", "Recoges un objeto del suelo."),
    ],
    "avisos": [
        ("menu_mover", "Menú, pasar de opción", "Pasas de una opción a otra en un menú."),
        ("menu_ok", "Menú, elegir", "Eliges una opción de un menú."),
        ("menu_atras", "Menú, volver atrás", "Vuelves atrás en un menú."),
        ("menu_borde", "Menú, principio o final", "Has llegado al principio o al final de un menú, o al borde del mapa."),
        ("menu_ajuste", "Menú, cambiar un valor", "Cambias el valor de una opción con izquierda o derecha."),
        ("error", "Error", "Eso no se puede hacer ahora."),
        ("notificacion", "Aviso", "Aviso general: una misión nueva, un destino marcado o un mensaje. Lo que es se dice a continuación."),
        ("movil", "Móvil", "Abres el móvil, o te llega una llamada o un mensaje."),
        ("dialogo", "Frase de un diálogo", "Empieza una frase de un diálogo."),
        ("guardado", "Partida guardada", "La partida se ha guardado."),
        ("logro", "Logro conseguido", "Has conseguido uno de los logros del juego."),
        ("nivel", "Sube una habilidad", "Has mejorado en conducción, puntería, resistencia o pesca."),
        ("reloj", "Cuenta atrás", "Quedan menos de diez segundos: suena con cada segundo."),
        ("pasan_horas", "Pasan las horas", "El tiempo pasa de golpe: duermes, te escondes o esperas."),
        ("gallo", "Amanece", "Son las siete de la mañana: canta un gallo."),
        ("buho", "Anochece", "Son las nueve de la noche: un búho."),
        ("campanadas", "Medianoche", "Empieza un día nuevo: cobras tus negocios y cambian los precios."),
    ],
    "trabajo": [
        ("mision_ok", "Misión completada", "Has completado una misión."),
        ("mision_fallo", "Misión fallida", "Has fallado una misión, o has caído."),
        ("jornada", "Jornada de trabajo", "Haces una jornada de trabajo: la sirena de la fábrica y pasan las horas."),
        ("ascenso", "Ascenso", "Subes de rango en un oficio y cobras más, o te ascienden de puesto en tu contrato fijo."),
        ("despido", "Despido", "Te han despedido de tu empleo fijo: un portazo y tres notas que bajan."),
        ("diploma", "Curso terminado", "Has terminado un curso en una academia y sube una habilidad."),
        ("titulo", "Título conseguido", "Has terminado los estudios de un título: una fanfarria corta y un acorde largo."),
        ("inspeccion", "Inspección", "Ha pasado una inspección por uno de tus negocios: golpes de nudillos en la puerta, papeles y un sello. "
         "Si ha encontrado algo, lo tienes en el móvil, en Vida, reputación y consecuencias."),
        ("factura", "Factura, impuesto o cuota", "Te han cobrado las facturas, los impuestos o la cuota de un crédito: una impresora de tiques y una nota grave."),
        ("donativo", "Donativo", "Haces un donativo: monedas que caen."),
        ("prestigio", "Prestigio ciudadano", "Los vecinos te ven con mejores ojos."),
        ("fama", "Cambia tu fama", "Cambia cómo te ven en la calle."),
        ("animo_sube", "Mejora tu ánimo", "Tu ánimo sube de nivel: apuntas mejor."),
        ("animo_baja", "Empeora tu ánimo", "Tu ánimo baja de nivel: con el ánimo muy bajo apuntas peor y corres menos."),
    ],
    "territorios": [
        ("territorio", "Territorio conquistado", "Un barrio pasa a ser tuyo."),
        ("amenaza_barrio", "Amenaza sobre un barrio tuyo", "Una banda prepara un asalto a un barrio tuyo, o acaba de empezarlo: tambores graves, cada vez más seguidos, y dos notas tensas. "
         "Mira el móvil, en Territorios."),
        ("barrio_defendido", "Barrio defendido", "Has rechazado un asalto, o has arrasado el escondite de una banda: un redoble y tres notas que suben."),
        ("barrio_perdido", "Barrio perdido", "Una banda te ha quitado un barrio: una campana grave y notas que bajan."),
    ],
    "linea": [
        ("amigo_entra", "Amigo que entra", "Jugando con amigos, alguien se une a la partida, o te conectas tú. Tres notas que suben."),
        ("amigo_sale", "Amigo que se va", "Jugando con amigos, alguien se va, o te desconectas tú. Tres notas que bajan."),
        ("chat", "Mensaje", "Jugando con amigos, llega o se envía un mensaje: dos notas agudas y rápidas. Se lee en voz alta a continuación."),
        ("chat_personaje", "Mensaje en personaje", "En un servidor, alguien que está cerca habla como su personaje, o lo haces tú: dos notas graves y cálidas, más lentas que las del mensaje normal."),
        ("chat_fuera", "Mensaje fuera de personaje", "En un servidor, alguien habla como jugador y no como su personaje: dos toques secos de madera. Lo oye todo el servidor."),
        ("chat_accion", "Acción de un personaje", "En un servidor, alguien que está cerca cuenta lo que hace su personaje, por ejemplo que abre una puerta: un roce corto rematado con una nota."),
        ("espera_servidor", "Espera al servidor", "En un servidor, se ha cortado la conexión o el servidor se está actualizando, y el juego espera para volver a entrar solo: "
         "dos notas lentas y flojas, la segunda más grave. Se repite cada pocos segundos."),
    ],
    "juegos": [
        ("pesca_lanzar", "Pesca, lanzar el anzuelo", "Echas la caña: el anzuelo cae al agua."),
        ("pez_pica", "Pesca, pican", "Un pez ha mordido el anzuelo: tira enseguida, antes de un segundo."),
        ("carrete", "Pesca, recoger el sedal", "Recoges el sedal con el carrete."),
        ("diana", "Diana de la galería de tiro", "Aparece una diana: dispara hacia el lado por el que suena."),
        ("diana_ok", "Diana acertada", "Has acertado una diana de la galería de tiro."),
        ("ruleta", "Ruleta", "Gira la ruleta del casino."),
        ("dados", "Dados", "Ruedan los dados."),
        ("campana_ring", "Campana del combate de boxeo", "Empieza un combate en el gimnasio."),
        ("simon_0", "Máquina de memoria, flecha arriba", "La nota más aguda de la máquina de memoria de sonidos."),
        ("simon_1", "Máquina de memoria, flecha derecha", "La segunda nota más aguda de la máquina de memoria de sonidos."),
        ("simon_2", "Máquina de memoria, flecha abajo", "La nota más grave de la máquina de memoria de sonidos."),
        ("simon_3", "Máquina de memoria, flecha izquierda", "La segunda nota más grave de la máquina de memoria de sonidos."),
    ],
    "ambientes": [
        ("amb_ciudad", "Ambiente de ciudad", "Estás en el centro de la ciudad: tráfico lejano."),
        ("amb_residencial", "Ambiente de barrio tranquilo", "Estás en un barrio residencial."),
        ("amb_industrial", "Ambiente de polígono industrial", "Estás en un polígono industrial: maquinaria."),
        ("amb_parque", "Ambiente de parque", "Estás en un parque: pájaros."),
        ("amb_playa", "Ambiente de playa", "Estás en la playa: olas."),
        ("amb_puerto", "Ambiente de puerto", "Estás en el puerto: olas y una sirena de barco lejana."),
        ("amb_mar", "Ambiente de mar abierto", "Estás en el mar, lejos de la costa."),
        ("amb_campo", "Ambiente de campo", "Estás en el campo: pájaros y cencerros."),
        ("amb_montana", "Ambiente de montaña", "Estás en la montaña: viento."),
        ("amb_noche", "Ambiente de noche", "Es de noche: grillos."),
        ("lluvia", "Lluvia", "Está lloviendo: el suelo resbala más y se oye peor."),
        ("trueno", "Trueno", "Un trueno, cuando llueve."),
        ("viento_playa", "Viento", "El viento en la cara, cuando vas en helicóptero."),
        ("multitud", "Murmullo de mucha gente", "Hay mucha gente alrededor."),
        ("gaviota", "Gaviotas", "Gaviotas, en la playa y en el puerto."),
        ("pajaro", "Pájaro", "Un pájaro, en los parques y en los barrios tranquilos."),
        ("martillo", "Martillazos de obra", "Una obra a lo lejos, en el puerto y en los polígonos."),
        ("claxon_lejano", "Claxon lejano", "Un claxon a lo lejos, de ambiente: no es para ti."),
        ("sirena_lejana", "Sirena lejana", "Una sirena a lo lejos, de ambiente: no vienen a por ti."),
    ],
    "relaciones": [
        ("afinidad_sube", "Sube la afinidad", "Alguien te aprecia más, por una charla, una cita o un regalo."),
        ("afinidad_baja", "Baja la afinidad", "Alguien se ha disgustado contigo."),
        ("cita", "Cita", "Tienes una cita, o un momento de complicidad con tu pareja."),
        ("regalo", "Regalo", "Entregas un regalo: papel de envolver."),
        ("pareja", "Nueva pareja", "Empezáis una relación: dos latidos y un arpegio."),
        ("noche_juntos", "Noche juntos", "Pasáis la noche juntos. La escena se resuelve con un fundido."),
        ("ruptura", "Ruptura", "Se acaba una relación."),
    ],
    "sustancias": [
        ("tomar_copa", "Tomar una copa", "Tomas alcohol: se sirve y se brinda."),
        ("tomar_hierba", "Tomar hierba", "Fumas hierba: mechero, calada y humo."),
        ("tomar_pastillas", "Tomar pastillas", "Tomas una pastilla: el blíster y un trago."),
        ("tomar_polvo", "Tomar polvo blanco", "Tomas polvo blanco: una tarjeta y una inspiración."),
        ("tomar_cristal", "Tomar cristal", "Tomas cristal: crepita."),
        ("bajon", "Bajón", "Se pasa el efecto de una sustancia y llega el bajón."),
        ("abstinencia", "Abstinencia", "Tu cuerpo pide una sustancia de la que dependes: un temblor."),
        ("sobredosis", "Sobredosis", "Te has pasado: el corazón se frena, suena un pitido continuo y acabas en el hospital."),
        ("trato", "Trato cerrado", "Has comprado o vendido mercancía: billetes y un paquete que cambia de manos."),
        ("rechazo", "Rechazo", "A esa persona no le interesa lo que ofreces."),
        ("paisano", "Policía de paisano", "El comprador era un policía de paisano."),
        ("precio_ganga", "Precio de ganga", "En el proveedor, esa sustancia hoy está muy barata."),
        ("precio_escasez", "Precio de escasez", "En el proveedor, esa sustancia hoy está muy cara."),
    ],
}

# Los imprescindibles para orientarse y sobrevivir, en el orden en que conviene aprenderlos: el primer grupo de Aprender los sonidos.
IMPORTANTES = (
    "baliza", "baliza_destino", "llegada", "cruce", "radar", "tono_pared", "tono_libre", "choque_pared", "semaforo_tic", "semaforo_pio",
    "paso_acera0", "paso_calzada0", "paso_hierba0", "paso_arena0", "paso_muelle0", "paso_via0", "paso_npc",
    "loc_mision", "loc_objeto", "loc_casete", "loc_vehiculo", "loc_lugar", "puerta_entrar", "puerta_salir",
    "lugar_casa", "lugar_armeria", "lugar_comida", "lugar_tienda", "lugar_hospital", "lugar_comisaria", "lugar_taller", "lugar_bar", "lugar_casino",
    "lugar_taxi", "lugar_periodico", "lugar_fuente", "lugar_iglesia", "lugar_banco", "lugar_estacion", "lugar_salida", "lugar_embarcadero", "lugar_boya",
    "lugar_gimnasio", "lugar_cine", "lugar_tranvia", "lugar_tren", "lugar_aeropuerto", "lugar_helipuerto", "lugar_prision", "lugar_mina", "lugar_rio",
    "lugar_protectora", "lugar_empleo", "lugar_academia", "lugar_ong", "lugar_club", "lugar_proveedor",
    "sonar", "bordillo", "intermitente", "frenazo", "choque", "alarma", "ganzua", "fuego", "explosion",
    "sirena", "estrella_sube", "buscando", "policia_perdida",
    "tono_objetivo", "tono_apuntado", "amartillar", "bala_silbido", "dolor", "latido",
    "evento", "ladrido", "perro_olfatea", "reloj", "dinero", "mision_ok", "mision_fallo", "nivel", "logro",
    "gallo", "buho", "campanadas", "cursor_mapa",
    "motor_lancha", "motor_barco", "motor_helicoptero", "motor_avioneta", "tono_altitud", "tono_alineacion", "alarma_cabina", "turbulencia", "aterrizaje", "avion", "avion_despegue", "tren", "tren_silbato", "tranvia", "tranvia_campana",
    "brazada", "bajo_agua", "pez_pica", "diana", "simon_0", "simon_2",
    "ascenso", "despido", "inspeccion", "factura", "titulo", "diploma", "prestigio", "fama", "animo_sube", "animo_baja", "bolsa",
    "territorio", "amenaza_barrio", "barrio_defendido", "barrio_perdido",
    "amigo_entra", "amigo_sale", "chat", "chat_personaje", "chat_fuera", "chat_accion", "espera_servidor",
    "afinidad_sube", "afinidad_baja", "pareja", "ruptura", "tomar_copa", "tomar_hierba", "tomar_pastillas", "tomar_polvo", "tomar_cristal",
    "bajon", "abstinencia", "sobredosis", "trato", "rechazo", "paisano",
)

# Los sonidos de orientación: en los packs que vienen con el juego son siempre los de serie.
_ORIENTACION = ("tono_", "semaforo_", "baliza", "loc_", "lugar_")
_ORIENTACION_SUELTOS = {"sonar", "bordillo", "cruce", "radar", "cursor_mapa"}

_CLAVES = [g[2] for g in GRUPOS]
FICHAS = {s: (_CLAVES.index(k), nombre, texto) for k, lista in SONIDOS.items() for s, nombre, texto in lista}
DESCRIPCIONES = {s: f[2] for s, f in FICHAS.items()}
_ADULTOS = {"relaciones", "sustancias"}


def es_orientacion(nombre):
    return nombre.startswith(_ORIENTACION) or nombre in _ORIENTACION_SUELTOS


def es_del_juego(nombre):
    """Las canciones de la radio y la música de ambiente comparten mezclador con los sonidos, pero no son sonidos del juego."""
    return nombre in FICHAS or not nombre.startswith(("radio_", "musica_", "_"))


def nombre(sonido):
    """El nombre que se dice. Para un archivo que no está apuntado, su nombre de archivo con espacios."""
    f = FICHAS.get(sonido)
    return f[1] if f else sonido.replace("_", " ").capitalize()


def describir(sonido):
    """Qué significa oírlo en el juego."""
    f = FICHAS.get(sonido)
    return f[2] if f else "Sonido del juego."


def grupo_de(sonido):
    """El número de su grupo en GRUPOS; len(GRUPOS) si no está apuntado."""
    f = FICHAS.get(sonido)
    return f[0] if f else len(GRUPOS)


def titulo_de(sonido):
    k = grupo_de(sonido)
    return GRUPOS[k][0] if k < len(GRUPOS) else OTROS


def sin_tildes(texto):
    """Para buscar: minúsculas y sin tildes ni diéresis. La eñe se queda como ene, para quien no la tiene a mano."""
    return "".join(c for c in unicodedata.normalize("NFD", str(texto).casefold()) if not unicodedata.combining(c))


def orden(texto):
    """Clave para ordenar como en un diccionario español: sin contar tildes ni mayúsculas, y la eñe detrás de la ene."""
    return sin_tildes(str(texto).casefold().replace("ñ", "n{")), str(texto)


def clasificar(nombres):
    """Todos los sonidos, repartidos en sus grupos: [(título, [sonido, ...]), ...], los grupos en su orden y dentro de cada
    uno por orden alfabético del nombre que se dice. Ninguno se queda fuera: el que no esté apuntado va a «Otros sonidos»."""
    grupos = {}
    for s in nombres:
        if es_del_juego(s):
            grupos.setdefault(grupo_de(s), []).append(s)
    return [(GRUPOS[k][0] if k < len(GRUPOS) else OTROS, sorted(set(v), key=lambda s: orden(nombre(s)))) for k, v in sorted(grupos.items())]


def importantes(nombres):
    disponibles = set(nombres)
    return [s for s in IMPORTANTES if s in disponibles]


def es_de_adultos(sonido):
    """Solo se oye con el contenido para adultos activado: los dos últimos grupos."""
    k = grupo_de(sonido)
    return k < len(GRUPOS) and GRUPOS[k][2] in _ADULTOS


def texto_aprender(sonido, suelto=False):
    """Lo que se dice de un sonido en Aprender los sonidos: su nombre y qué significa. Con suelto, fuera de su grupo,
    los del contenido para adultos lo dicen detrás del nombre, porque ahí no lo dice el título del grupo."""
    aparte = ", contenido para adultos" if suelto and es_de_adultos(sonido) else ""
    return f"{nombre(sonido)}{aparte}. {describir(sonido)}"


def buscar(texto, nombres):
    """Los sonidos que tienen todas las palabras buscadas en el nombre, en la explicación, en el grupo o en el nombre del archivo,
    sin contar tildes ni mayúsculas. Primero los que las tienen en el nombre. Devuelve [(sonido, título de su grupo), ...]."""
    palabras = sin_tildes(texto).replace("_", " ").split()
    if not palabras:
        return []
    salida = []
    for titulo, lista in clasificar(nombres):
        for s in lista:
            corto = sin_tildes(nombre(s))
            largo = " ".join((corto, sin_tildes(describir(s)), sin_tildes(titulo), s.replace("_", " ")))
            if all(p in largo for p in palabras):
                salida.append((0 if all(p in corto for p in palabras) else 1, len(salida), s, titulo))
    return [(s, titulo) for _, _, s, titulo in sorted(salida)]
