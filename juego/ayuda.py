"""Textos de ayuda: teclas, tutorial y glosario de sonidos."""
from . import catalogo_sonidos

TECLAS = {
    "general": [
        ("C", "dónde estoy: calle, barrio y hacia dónde miro. Con Mayúsculas añade las coordenadas"),
        ("V", "estado: salud, dinero, arma, nivel de búsqueda y vehículo"),
        ("T", "hora, día y tiempo que hace"),
        ("O", "objetivo de la misión o del trabajo en curso: dice primero dónde está, a cuántos metros, en qué dirección y, si se mueve, hacia dónde va, y después lo demás. "
              "Si el objetivo se mueve o corre el tiempo, una pulsación dice solo eso, y dos seguidas leen la explicación entera"),
        ("Mayúsculas O", "volver al objetivo de la misión o del trabajo: deja cualquier desvío, lo marca en el GPS y, si está al alcance, lo deja elegido en el radar. Siempre hace lo mismo"),
        ("N", "descripción del lugar o del barrio en el que estás"),
        ("Mayúsculas N", "siguiente cruce: qué calle es la próxima que te vas a cruzar hacia donde miras o conduces, y a cuántos metros está"),
        ("Mayúsculas V", "solo el hambre, la sed, el sueño y la higiene, con la vida realista activada"),
        ("Mayúsculas L", "dónde está el vehículo del que te bajaste: lo dice y lo marca en el GPS. Si ibas a otro sitio, al llegar al vehículo el GPS vuelve solo a ese destino. "
                         "Si tienes más vehículos, dice cuántos: están en el móvil, en Mis vehículos"),
        ("K", "hacia dónde miras o conduces, y hace sonar un tono desde el norte para orientarte"),
        ("F10", "jugando con amigos o en un servidor, escribir un mensaje: se lee en voz alta a los demás. Para abrir tu partida a tus amigos o unirte a la de uno, abre el móvil con M y entra en Jugar con amigos"),
        ("Mayúsculas F10", "en un servidor con canales de rol, hablar en personaje: lo oye solo quien está cerca de ti"),
        ("Control F10", "en un servidor con canales de rol, describir lo que hace tu personaje: escribes «abre la puerta» y los que están cerca oyen tu nombre y «abre la puerta»"),
        ("F9", "explorador de mapa: recorre la localidad con un cursor, cruce a cruce, sin mover al personaje. Tabulador dice los lugares junto al cursor e Intro marca el destino"),
        ("Tabulador y Mayúsculas Tabulador", "radar: recorre lo que hay alrededor, de lo más cercano a lo más lejano"),
        ("B", "pone el GPS y la baliza hacia lo último que dijo el radar. Si ya ibas a algún sitio, es un desvío: al subir a ese vehículo, llegar junto a esa persona, llegar a ese objeto o recogerlo, o llegar a ese lugar, "
              "el GPS vuelve solo a lo que llevabas, y lo dice"),
        ("F6", "cambia el filtro del radar: todo, lugares, vehículos, personas u objetos"),
        ("L", "lista de lugares de la ciudad para marcar un destino"),
        ("G", "repite la indicación del GPS. En una misión, sin destino marcado, vuelve a marcar lo que pide la misión; sin misión, recupera el último destino que quitaste"),
        ("Mayúsculas G", "quita el destino del GPS. Si estabas en un desvío, el GPS vuelve a lo que llevabas; otra pulsación quita también eso"),
        ("Control G", "recupera el último destino o desvío que quitaste con Mayúsculas G, sin tener que buscarlo otra vez. Si ahora vas a otro sitio, entra como desvío"),
        ("M", "abre el móvil: misiones, lugares, explorador de mapa, marcadores, servicios, habilidades, logros, propiedades y estadísticas. En Vida, reputación y consecuencias "
              "está cómo te ve la ciudad, cómo te ve la calle y qué ganas o pierdes por ello, con tus antecedentes, tu contrato, tus estudios, tus negocios y lo que te van a cobrar"),
        ("Intro", "interactuar: entrar en un lugar, empezar una misión, recoger un objeto o hablar"),
        ("F", "subir a un vehículo o bajarte"),
        ("Mayúsculas F", "en un servidor, sacar a otro jugador de su vehículo y quedártelo: tiene que ir despacio y estar a tu lado"),
        ("Q", "fija al enemigo más cercano; púlsala otra vez para pasar al siguiente. Mayúsculas Q fija a cualquiera"),
        ("Números del 1 al 9", "eligen arma. La coma pasa a la siguiente y Mayúsculas coma a la anterior"),
        ("I", "abre la lista de tus armas para elegir una"),
        ("P", "en el mar, lanza la caña para pescar; cuando oigas que pican, pulsa Espacio. En vehículos de emergencias, enciende la sirena"),
        ("Z", "usa un botiquín"),
        ("Mayúsculas H", "rendirte: con la policía buscándote y un agente cerca, levantas las manos. Los agentes dejan de disparar y vienen a detenerte; no te muevas ni ataques. "
                         "Cuanto más nivel de búsqueda, más multa y más horas de calabozo, y con el nivel más alto pierdes todas las armas. Otra pulsación baja las manos"),
        ("Re Pág y Av Pág", "repasan los mensajes anteriores. El punto repite el último"),
        ("F1", "esta ayuda"),
        ("F2", "cambia entre conducción asistida y libre"),
        ("F3", "cambia el movimiento a pie entre brújula y giros"),
        ("F4", "activa o desactiva la baliza sonora del GPS"),
        ("F5", "guardado rápido, fuera de las misiones"),
        ("F7 y F8", "bajan y suben el volumen de la música"),
        ("F12", "pone una marca en el registro de la sesión. Púlsala cuando notes algo raro: así, quien revise el registro sabrá en qué momento fue"),
        ("Escape", "menú de pausa"),
    ],
    "pie": [
        ("Flechas", "caminar. En modo brújula cada flecha va hacia un punto cardinal: arriba es norte, derecha es este. En modo giros, izquierda y derecha giran 45 grados y arriba avanza"),
        ("Mayúsculas izquierda con las flechas", "correr. La Mayúsculas derecha no hace correr ni cambia entre andar y correr. Las combinaciones, como Mayúsculas N, valen con cualquiera de las dos y no cambian el paso"),
        ("W, A, S y D", "escáner direccional: dice qué hay delante, a la izquierda, detrás y a la derecha, y a qué distancia está la pared"),
        ("Espacio", "atacar o disparar. Con armas automáticas, mantenla pulsada"),
        ("R", "recargar"),
        ("Mayúsculas R", "el reproductor con auriculares, si lo has comprado: lo enciende y pasa de emisora, para oír la radio y tu música a pie. Una de las emisoras es apagado"),
        ("X", "agacharte o levantarte. Al agacharte te aciertan menos, pero vas más lento"),
        ("Mayúsculas X", "ponerte a cubierto tras una pared o un vehículo parado, o salir. A cubierto te alcanzan mucho menos; si te mueves, sales"),
        ("Retroceso", "tiempo lento: todo va más despacio mientras te quede concentración. Otra pulsación lo quita"),
        ("H", "gritar para espantar a los peatones. De servicio como policía, da el alto a los sospechosos"),
        ("E", "con un arma en la mano, atracar al peatón que tengas al lado"),
        ("Y", "si tienes perro, le pides que busque por el olfato el objeto más cercano"),
        ("Mayúsculas Y", "el menú de tu perro: cómo está, acariciarlo, darle de comer, mandarlo a casa o llamarlo"),
        ("J", "hablar con la persona que tengas al lado. Cada una tiene su nombre, su oficio y su carácter: puedes saludar, preguntar por un sitio, invitar a un café, hacer amigos o escribir lo que quieras decirle"),
        ("Mayúsculas J", "jugando con amigos o en un servidor, dice cómo va vestido el jugador que tengas más cerca: su ropa y sus complementos. En un servidor con canales de rol, lee además su ficha, si la ha escrito. Solo lo dice cuando lo pides"),
        ("U", "caminar solo: con un destino marcado en el GPS, el personaje sigue la ruta él solo hasta llegar. Mantén Mayúsculas para que corra. Cualquier flecha, o la U otra vez, lo detiene"),
    ],
    "coche": [
        ("Flecha arriba", "acelerar"),
        ("Flecha abajo", "frenar y, parado, marcha atrás"),
        ("Espacio", "freno de mano"),
        ("Flechas izquierda y derecha", "en conducción asistida ponen el intermitente: el coche girará solo en el próximo cruce. En conducción libre giran el volante"),
        ("A y D", "en conducción asistida, mantenlas para cambiar de carril: A invade el carril contrario para adelantar y D te arrima a la acera"),
        ("Frenada automática", "en conducción asistida el coche frena solo si hay un vehículo delante en tu carril. Se desactiva en Opciones"),
        ("U", "media vuelta, con el coche casi parado. Con el piloto del GPS, la da él solo cuando el destino queda a tu espalda"),
        ("Y", "piloto del GPS: el coche va solo hasta el destino marcado; acelera, frena, gira, espera en los semáforos y se detiene al llegar"),
        ("E", "en conducción libre, endereza el coche hacia el punto cardinal más cercano"),
        ("W", "velocidad actual"),
        ("H", "claxon"),
        ("R", "cambia de emisora. Mayúsculas R apaga la radio"),
        ("Control", "disparar desde el vehículo sin bajarte, con un arma de fuego en la mano: primero la Q fija a quien tengas cerca, y Control le dispara. La I cambia de arma. Con un arma automática, mantenla pulsada"),
        ("J", "empieza o termina un trabajo con el vehículo: taxi, ambulancia, autobús, coche patrulla o camión. Si eres agente de policía, en un coche patrulla empieza o termina el turno"),
        ("Helicóptero", "vuela por encima de edificios y tráfico. Se pilota a mano como un barco. Para bajarte, detente sobre una calle o un espacio abierto. En un helipuerto, Intro te lleva volando a otra localidad"),
        ("En el mar", "los barcos se llevan siempre a mano: izquierda y derecha giran el timón y se anuncia el rumbo. Intro junto a un muelle sirve para atracar"),
    ],
}

TUTORIAL = [
    ("Narrador", "Tutorial. Puedes saltarlo con Escape y repetir cualquier frase con la flecha arriba. Todas las teclas están siempre en la ayuda, con F1."),
    ("Narrador", "Este juego se juega solo con el oído. Usa auriculares: lo que suena a tu derecha está a tu derecha, y lo que suena apagado está detrás de ti."),
    ("Narrador", "A pie te mueves con las flechas. Por defecto, arriba camina hacia el norte, abajo hacia el sur, derecha al este e izquierda al oeste. Mantén Mayúsculas para correr."),
    ("Narrador", "La ciudad es una cuadrícula: las calles van de oeste a este y las avenidas de sur a norte. Hay un cruce cada 90 metros. Tus pasos suenan distinto en la acera, en el asfalto, en el césped y en la arena."),
    ("Narrador", "Pulsa C en cualquier momento para saber dónde estás. Pulsa Tabulador para recorrer con el radar lo que tienes cerca: cada cosa suena desde su posición y se anuncia con su distancia."),
    ("Narrador", "Las teclas W, A, S y D son tu bastón: dicen qué hay en cada dirección y a qué distancia está la pared."),
    ("Narrador", "Cada tipo de lugar tiene su propio sonido, que oirás al acercarte. Puedes aprenderlos todos en el menú Aprender los sonidos. Ante una puerta, pulsa Intro para entrar."),
    ("Narrador", "Para ir a un sitio, pulsa L, elige el lugar y pulsa Intro. El GPS te dirá por dónde ir y una baliza sonará en la dirección que debes seguir. Con G repites la indicación."),
    ("Narrador", "En los cruces suena el semáforo: un tictac rápido significa que puedes cruzar la calle andando hacia el norte o el sur. Un pío lento, que puedes cruzar la avenida hacia el este o el oeste."),
    ("Narrador", "Con F subes a un vehículo. En conducción asistida el coche sigue su carril él solo: tú aceleras con flecha arriba, frenas con flecha abajo y, antes de cada cruce, pulsas izquierda o derecha si quieres girar. Un pitido te avisa de los coches que tienes delante."),
    ("Narrador", "Si te metes en líos, pulsa Q para fijar al enemigo: oirás un tono que sale de donde está. Espacio ataca, R recarga y Z usa un botiquín. Desde un vehículo también puedes disparar sin bajarte: la Q fija igual y Control dispara, con un arma de fuego en la mano."),
    ("Narrador", "Más allá de Puerto Bravo hay otra ciudad, San Lucero, dos pueblos, Villaseca y Cala Brava, y un mar con una isla. Se llega por carretera con un vehículo, en autobús desde la estación o en barco desde un embarcadero. Por carretera, conduce hasta una salida de la ciudad y, sin bajarte, pulsa Intro. El GPS sabe guiarte entre localidades."),
    ("Narrador", "Para aprenderte una ciudad sin moverte, pulsa F9: el explorador de mapa mueve un cursor de cruce en cruce y te dice qué hay en cada uno."),
    ("Narrador", "Puedes trabajar con un taxi, repartir pizzas, conducir ambulancias, autobuses y camiones, pescar, correr carreras, comprar casas, negocios, coches y barcos, o jugarte el dinero en el casino. El móvil, con la tecla M, lo reúne todo."),
    ("Narrador", "Si tienes un mando de Xbox o de PlayStation, conéctalo: el juego lo reconoce solo, vibra con lo que pasa y la ayuda te dice qué hace cada botón."),
    ("Narrador", "Eso es todo. Explora a tu ritmo: nadie te obliga a seguir la historia. Bienvenid[o|a] a Puerto Bravo."),
]

# Las teclas de cuando se recorre por dentro una casa, un local o una tienda. No se pueden cambiar: van aparte de las del juego.
TECLAS_RECORRIDO = [
    ("Flecha izquierda y flecha derecha", "ir a la habitación, la sala o el pasillo de al lado. Se oyen tus pasos hacia ese lado y el juego dice adónde llegas"),
    ("Intro", "usar el sitio donde estás. En la cocina de casa, guardar la compra, abrir la nevera o la despensa y cocinar. En un pasillo de una tienda de comida, ver sus productos: "
              "Intro o flecha derecha echa uno a la cesta y flecha izquierda lo devuelve. En la caja, pagar la cesta"),
    ("C", "en una tienda de comida, qué llevas en la cesta y cuánto suma. Con mando, X o Cuadrado"),
    ("F1", "dónde estás, qué hace Intro ahí y adónde hay que ir para que te atiendan"),
    ("Escape", "salir. En una tienda de comida, con algo en la cesta, pregunta antes qué haces con ella: pagar, dejarla, llevártela sin pagar o seguir comprando"),
]

INTRO = [
    ("Narrador", "Puerto Bravo. Una ciudad de mar, con un puerto que nunca duerme y una playa que nunca descansa."),
    ("Narrador", "Te llamas Dani Roca. Hace tres años te condenaron por un robo que no cometiste. Esta mañana se han abierto las puertas de la prisión de Monteferro."),
    ("Narrador", "El autobús te deja en el Barrio Viejo, donde te criaste. Llevas cincuenta euros, un botiquín y un petate. Tu tía Encarna te espera en su bar, La Gaviota, unos metros al este por la Calle Mayor."),
]

# El glosario de Aprender los sonidos: (archivo, nombre, explicación) de los más importantes, en el orden en que conviene
# aprenderlos. Los nombres, las explicaciones y ese orden están en el catálogo de sonidos, que es el único sitio donde se escriben.
SONIDOS = [(s, catalogo_sonidos.nombre(s), catalogo_sonidos.describir(s)) for s in catalogo_sonidos.IMPORTANTES]
