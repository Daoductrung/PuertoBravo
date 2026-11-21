"""Escribe el mod Marisma Negra en esta misma carpeta y lo comprueba con el mismo revisor del editor.

    .venv\\Scripts\\python.exe componentes_extra\\mod_marisma_negra\\crear.py

Marisma Negra no viene con el juego: es un componente que se descarga aparte. Por eso el archivo queda aquí,
en componentes_extra\\mod_marisma_negra\\marisma_negra.json, y no en data\\mods.

Un pueblo de marisma en la costa, al sureste de Puerto Bravo: arrozales, una laguna con aves, anguileros, unas
salinas cerradas hace diez años y unos contrabandistas que usan los caños de noche. Trae cuatro misiones de historia,
un encargo honrado, una escopeta de puesto, una fisga de anguilero, una barca de caños, una ranchera de la
cooperativa, una carrera por los arrozales, dos comidas, dos peces y un personaje. Todo es inventado.

Sale con código 1 si el revisor encuentra errores; los avisos se escriben, pero no cuentan como fallo.
"""
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))

import crear_mods_ejemplo as CME          # noqa: E402  (las tablas del juego y las ayudas de los mods de ejemplo)

ARMAS, VEHICULOS = CME.ARMAS, CME.VEHICULOS
clon, primero, D = CME.clon, CME.primero, CME.D

ARCHIVO = os.path.join(AQUI, "marisma_negra.json")
MAPA = "marisma_negra"


def _dec(clave, pregunta, *opciones):
    return {"tipo": "decision", "clave": clave, "pregunta": pregunta,
            "opciones": [dict(zip(("texto", "ayuda", "dice"), o[:3]), **o[3]) for o in opciones]}


def marisma_negra():
    escopeta = "escopeta" if "escopeta" in ARMAS else primero(ARMAS, lambda a: a["tipo"] == "fuego")
    cuerpo = "machete" if "machete" in ARMAS else primero(ARMAS, lambda a: a["tipo"] == "cuerpo" and a["id"] != "punos")
    barca = "lancha" if "lancha" in VEHICULOS else primero(VEHICULOS, lambda v: v.get("barco"))
    pickup = "pickup" if "pickup" in VEHICULOS else "utilitario"
    furgo = "furgoneta" if "furgoneta" in VEHICULOS else "utilitario"
    tractor = "tractor" if "tractor" in VEHICULOS else "utilitario"
    mapa = {
        "id": MAPA, "tipo": "pueblo", "nombre": "Marisma Negra", "trafico": 1, "peatones": 3, "nombre_objeto": "Pluma de garza",
        "avenidas": ["Camino de la Barra", "Calle de los Anguileros", "Calle de la Acequia", "Calle del Secadero", "Camino de la Esclusa"],
        "calles": ["Paseo de los Caños", "Calle de la Sal", "Calle de la Ermita", "Carretera de Puerto Bravo"],
        "barrios": [
            {"id": "mn_canos", "nombre": "Los Caños", "i": [0, 3], "j": [0, 0], "ambiente": "amb_playa", "vehiculos": ["bici", "utilitario"],
             "descripcion": "Los Caños: canales de agua salobre entre juncos, barcas de fondo plano varadas en el fango y, al fondo, las Salinas de San Ginés, "
                            "cerradas hace diez años. De noche solo se oyen las ranas y, a veces, un remo."},
            {"id": "mn_pueblo", "nombre": "Marisma Negra", "i": [0, 1], "j": [1, 2], "ambiente": "amb_campo", "vehiculos": ["utilitario", pickup, "mn_ranchera", "bici"],
             "descripcion": "Marisma Negra, un pueblo de casas bajas encaladas con zócalo negro de alquitrán, para que no suba la humedad. "
                            "Huele a arroz tostado, a fango y a anguila ahumada."},
            {"id": "mn_arrozales", "nombre": "Los Arrozales", "i": [2, 3], "j": [1, 2], "ambiente": "amb_parque", "vehiculos": [tractor, "mn_ranchera", pickup],
             "descripcion": "Los Arrozales: tablas de agua quieta hasta donde alcanza la vista, acequias, garzas y la cooperativa arrocera. "
                            "En el extremo, la compuerta de la Esclusa Vieja separa el agua dulce de la salada."}],
        "bloques": {"0,0": "muelle", "1,0": "arena", "2,0": "hierba", "3,0": "arena", "1,1": "plaza", "3,1": "hierba", "2,2": "hierba", "3,2": "hierba"},
        "lugares": [
            # ---- Marisma Negra, el pueblo
            {"id": "mn_salida", "nombre": "Salida norte, carretera de Puerto Bravo", "tipo": "salida", "bloque": [1, 2], "lado": "N", "pos": 36, "sonido": "lugar_salida",
             "a_mapa": "puerto_bravo", "a_lugar": "mn_pb_salida", "km": 27, "horas": 0.7, "desc": "La carretera de la costa, que sube entre pinos y arrozales hasta Puerto Bravo."},
            {"id": "mn_estacion", "nombre": "Parada del autobús de Marisma Negra", "tipo": "estacion", "bloque": [0, 1], "lado": "N", "pos": 20, "precio": 20, "sonido": "lugar_estacion",
             "desc": "Una marquesina de chapa con un banco y un horario que nadie cumple."},
            {"id": "mn_tren", "nombre": "Apeadero de Marisma Negra", "tipo": "tren", "bloque": [0, 1], "lado": "N", "pos": 52, "sonido": "lugar_tren",
             "desc": "Un andén corto entre eucaliptos y una taquilla abierta dos horas al día. De aquí salen los trenes a las demás localidades a las que se llega por tierra."},
            {"id": "mn_taberna", "nombre": "Taberna El Anguilero", "tipo": "taberna", "bloque": [0, 1], "lado": "S", "pos": 36, "sonido": "lugar_bar",
             "desc": "Anguila ahumada colgada sobre la barra, dados, vino de garrafa y un tablón con encargos. La lleva Toñi y aquí se sienta Amador."},
            {"id": "mn_tienda", "nombre": "Ultramarinos La Garza", "tipo": "tienda", "surtidor": True, "bloque": [0, 1], "lado": "E", "pos": 36, "sonido": "lugar_tienda",
             "desc": "De todo un poco, botas de agua de todas las tallas y un surtidor de gasolina en la puerta."},
            {"id": "mn_banco", "nombre": "Caja Rural de la Marisma", "tipo": "banco", "bloque": [0, 1], "lado": "O", "pos": 36, "sonido": "lugar_banco",
             "desc": "Una ventanilla, un cajero y un calendario de la cooperativa de hace tres años."},
            {"id": "mn_plaza", "nombre": "Plaza de la Ermita", "tipo": "monumento", "bloque": [1, 1], "xy": [30, 30], "fuente": True, "sonido": "lugar_fuente",
             "desc": "Una plaza de tierra con cuatro moreras y una fuente de agua dulce, la única del pueblo que no sabe a sal."},
            {"id": "mn_iglesia", "nombre": "Iglesia de Nuestra Señora de los Caños", "tipo": "monumento", "bloque": [1, 1], "xy": [52, 58], "sonido": "lugar_iglesia",
             "desc": "Una iglesia blanca con una cigüeña en la espadaña. Dentro cuelgan exvotos de barcas que volvieron de una riada."},
            {"id": "mn_casa", "nombre": "Casa del anguilero", "tipo": "casa", "bloque": [0, 2], "lado": "O", "pos": 36, "precio": 4600, "garaje": 2, "sonido": "lugar_casa",
             "desc": "Una casa baja con patio de parra, ahumadero en el corral y cochera para dos vehículos."},
            {"id": "mn_consultorio", "nombre": "Consultorio médico de Marisma Negra", "tipo": "hospital", "bloque": [0, 2], "lado": "S", "pos": 36, "sonido": "lugar_hospital",
             "desc": "El consultorio del pueblo. La médica viene tres días a la semana y el resto, la enfermera, que sabe más que muchos médicos."},
            {"id": "mn_armeria", "nombre": "Caza y Pesca El Somormujo", "tipo": "armeria", "bloque": [0, 2], "lado": "E", "pos": 36, "sonido": "lugar_armeria",
             "desc": "Escopetas de puesto para los patos, fisgas, cartuchos y reclamos de madera tallados a mano."},
            {"id": "mn_farmacia", "nombre": "Botica de la Marisma", "tipo": "farmacia", "bloque": [0, 2], "lado": "N", "pos": 36, "sonido": "lugar_hospital",
             "desc": "Repelente de mosquitos en todas sus formas, tiritas y botiquines."},
            {"id": "mn_taller", "nombre": "Taller y Motores Juncal", "tipo": "taller", "bloque": [1, 2], "lado": "E", "pos": 36, "sonido": "lugar_taller",
             "desc": "Arreglan motores fuera borda, tractores y lo que les lleves, aunque esté lleno de barro."},
            {"id": "mn_ong", "nombre": "Comedor de la Cofradía", "tipo": "ong", "bloque": [1, 2], "lado": "S", "pos": 36, "sonido": "lugar_ong",
             "desc": "La Cofradía de anguileros da de comer a quien lo necesita. Los jueves cocina Toñi. Siempre faltan manos."},
            {"id": "mn_hostal", "nombre": "Hostal La Lisa", "tipo": "hotel", "bloque": [1, 2], "lado": "O", "pos": 36, "precio_noche": 32, "sonido": "lugar_casa",
             "desc": "Seis habitaciones con mosquitera y desayuno de tostadas con aceite."},
            # ---- Los Arrozales
            {"id": "mn_cooperativa", "nombre": "Cooperativa Arrocera La Espiga", "tipo": "negocio", "bloque": [2, 1], "lado": "S", "pos": 36, "sonido": "lugar_taller",
             "precio": 21000, "ingresos": 480, "vehiculo": "mn_ranchera",
             "desc": "La cooperativa del arroz, en venta desde que se jubiló la junta entera. Da dinero cada medianoche. En la puerta está siempre su ranchera: súbete y pulsa J para hacer el reparto."},
            {"id": "mn_empleo", "nombre": "Comunidad de Regantes, bolsa de trabajo", "tipo": "empleo", "bloque": [2, 1], "lado": "O", "pos": 36, "sonido": "lugar_empleo",
             "desc": "Jornadas en los arrozales, en la siega y en las compuertas."},
            {"id": "mn_arroceria", "nombre": "Arrocería Los Caños", "tipo": "comida", "bloque": [2, 1], "lado": "N", "pos": 36, "sonido": "lugar_comida",
             "desc": "Arroz de marisma en paella de leña y anguila de la laguna. Mesas largas y sobremesas más largas."},
            {"id": "mn_circuito", "nombre": "Salida de la carrera de los arrozales", "tipo": "carrera", "bloque": [2, 1], "lado": "E", "pos": 36, "sonido": "lugar_taxi",
             "desc": "En fiestas se corre por los caminos de las acequias. Gana quien no acaba dentro de una tabla de arroz."},
            {"id": "mn_arrozal", "nombre": "Arrozal de la Acequia Mayor", "tipo": "monumento", "bloque": [3, 1], "xy": [36, 36], "sonido": "pajaro",
             "desc": "Una tabla de arroz enorme, con garzas quietas como estatuas y el rumor del agua por la acequia."},
            {"id": "mn_secadero", "nombre": "Secadero de arroz", "tipo": "monumento", "bloque": [2, 2], "xy": [36, 36], "sonido": "lugar_generico",
             "desc": "Una era de cemento donde se seca el arroz en septiembre. El resto del año juegan aquí los críos."},
            {"id": "mn_esclusa", "nombre": "Compuerta de la Esclusa Vieja", "tipo": "monumento", "bloque": [3, 2], "xy": [40, 40], "sonido": "lugar_rio",
             "desc": "Una compuerta de hierro oxidado que separa los arrozales del caño grande. Cuando sube la marea, el agua salada empuja y la compuerta cruje."},
            {"id": "mn_aerodromo", "nombre": "Aeródromo de Marisma Negra", "tipo": "aeropuerto", "aerodromo": True, "bloque": [3, 2], "lado": "N", "pos": 36, "precio": 120, "sonido": "lugar_aeropuerto",
             "desc": "Una pista de tierra apisonada entre arrozales, que usan sobre todo las avionetas que fumigan. Llegan y salen avionetas de línea, y se alquilan avionetas."},
            # ---- Los Caños
            {"id": "mn_embarcadero", "nombre": "Embarcadero de los Caños", "tipo": "embarcadero", "bloque": [0, 0], "lado": "S", "pos": 36, "sonido": "lugar_embarcadero",
             "a_mapa": "mar", "a_lugar": "mn_mar_muelle", "desc": "Un muelle de tablones sobre pilotes. Por el caño grande se sale a mar abierto."},
            {"id": "mn_nautica", "nombre": "Varadero de los Caños", "tipo": "nautica", "bloque": [0, 0], "lado": "E", "pos": 36, "embarcadero": "mn_embarcadero", "sonido": "lugar_embarcadero",
             "desc": "Venden y reparan barcas. Las dejan amarradas en el embarcadero."},
            {"id": "mn_lonja", "nombre": "Lonja de la Anguila", "tipo": "pescaderia", "bloque": [1, 0], "lado": "N", "pos": 36, "sonido": "gaviota",
             "desc": "Aquí se subasta la anguila al amanecer. Compran todo lo que saques de la laguna o del mar."},
            {"id": "mn_barra", "nombre": "Playa de la Barra", "tipo": "tesoro", "bloque": [1, 0], "xy": [40, 20], "sonido": "viento_playa",
             "desc": "Una lengua de arena entre el mar y la marisma. Las riadas dejan aquí de todo."},
            {"id": "mn_laguna", "nombre": "Orilla de la Laguna Negra", "tipo": "pesca", "bloque": [2, 0], "xy": [40, 40], "sonido": "lugar_rio",
             "desc": "Agua oscura y quieta, y debajo, anguilas y lisas."},
            {"id": "mn_observatorio", "nombre": "Observatorio de aves", "tipo": "monumento", "bloque": [2, 0], "xy": [15, 60], "sonido": "pajaro",
             "desc": "Una caseta de madera sobre pilotes con mirillas hacia la laguna. Aquí pasa los días Celia, la guarda."},
            {"id": "mn_salinas", "nombre": "Salinas de San Ginés", "tipo": "monumento", "bloque": [3, 0], "xy": [40, 30], "sonido": "viento_playa",
             "desc": "Unas salinas cerradas hace diez años: balsas secas, montones de sal gris y un almacén con el tejado de uralita. Dicen que está vacío."},
        ],
        "casetes": [[30, 150], [250, 60], [330, 240]],
    }
    lugares = [
        {"id": "mn_pb_salida", "mapa": "puerto_bravo", "nombre": "Salida sureste, carretera de Marisma Negra", "tipo": "salida", "bloque": [9, 1], "lado": "E", "pos": 36, "sonido": "lugar_salida",
         "a_mapa": MAPA, "a_lugar": "mn_salida", "km": 27, "horas": 0.7, "desc": "La carretera de la costa, que baja entre pinos y arrozales hasta Marisma Negra."},
        {"id": "mn_mar_muelle", "mapa": "mar", "nombre": "Bocana de los Caños de Marisma Negra, desde el mar", "tipo": "muelle", "xy": [1000, 1440], "sonido": "lugar_boya",
         "a_mapa": MAPA, "a_lugar": "mn_embarcadero", "desc": "La entrada del caño grande de Marisma Negra, en la costa, entre Puerto Bravo y Cala Brava."},
    ]
    misiones = [
        {"id": "mn01", "titulo": "Nasas cortadas", "capitulo": 47, "contacto": "Amador", "lugar": "mn_taberna", "requiere": ["m01"],
         "resumen": "En la Taberna El Anguilero, un viejo anguilero dice que alguien le corta las redes de noche.",
         "pasos": [D(("Amador", "Cuarenta años poniendo nasas en los caños y nunca me las habían tocado. Esta semana me las han cortado tres veces."),
                     ("Dani", "¿Y quién va a querer unas nasas de anguila?"),
                     ("Amador", "Nadie. Las cortan porque estorban. De noche pasa una barca con el motor apagado, a remo, y mis redes le cierran el paso."),
                     ("Amador", "Tú no eres de aquí, foraster[o|a], y eso me sirve: a ti no te conoce nadie. Sube a la Esclusa Vieja, junto a los arrozales, y mira qué hay.")),
                   {"tipo": "ir", "lugar": "mn_esclusa", "radio": 14, "texto": "Ve a la Compuerta de la Esclusa Vieja, al noreste del pueblo, entre los arrozales."},
                   {"tipo": "recoger", "lugar": "mn_esclusa", "objeto": "una nasa cortada con un precinto de plástico", "texto": "Recoge la nasa que se ha quedado enganchada en la compuerta."},
                   D(("Narrador", "La nasa está cortada a cuchillo. Del aro cuelga un precinto de plástico azul, de los que se ponen a los sacos."),
                     ("Dani", "Sacos precintados en una marisma donde solo hay arroz y anguilas. Aquí se mueve otra cosa.")),
                   {"tipo": "ir", "lugar": "mn_taberna", "texto": "Vuelve a la Taberna El Anguilero y enséñale a Amador lo que has encontrado."},
                   D(("Amador", "Ese azul lo conozco. Era el de las Salinas de San Ginés, antes de que las cerraran. Llevan diez años muertas."),
                     ("Toñi", "Muertas de día, Amador. De noche hay luz en el almacén. Lo sabe medio pueblo y nadie dice nada."),
                     ("Amador", "Pues habla con Celia, la guarda de la laguna. Se pasa el día en el observatorio de aves y ve más que nadie."))],
         "recompensa": {"dinero": 250}},
        {"id": "mn02", "titulo": "La guarda de la laguna", "capitulo": 47, "contacto": "Celia", "lugar": "mn_observatorio", "requiere": ["mn01"],
         "resumen": "Celia, la guarda de la laguna, ve entrar una barca sin luces por el caño grande cada dos noches.",
         "pasos": [D(("Celia", "Así que tú eres [el|la] que anda preguntando por las salinas. Amador dice que te llamas Dani."),
                     ("Dani", "Y tú eres la que lo ve todo desde aquí arriba."),
                     ("Celia", "Veo garzas, flamencos y, desde hace un mes, una barca sin luces que entra por el caño grande cada dos noches."),
                     ("Celia", "He dado tres partes a la Guardia Civil y no ha venido nadie. Acércate a las salinas y vigila el almacén. Sin dejarte ver.")),
                   {"tipo": "vigilar", "lugar": "mn_salinas", "segundos": 45, "radio": 25,
                    "resultado": "Tres hombres sacan sacos precintados del almacén de las salinas y los bajan por el caño hasta una barca sin luces. Uno de ellos, con gorra, da las órdenes.",
                    "texto": "Vigila las Salinas de San Ginés sin que te vean. Cuando oigas pasos, quédate quiet[o|a] o agáchate con la X."},
                   {"tipo": "seguir", "lugar": "mn_salinas", "destino": "mn_lonja", "persona": "el hombre de la gorra",
                    "texto": "Sigue al hombre de la gorra sin que te descubra. Guíate por sus pasos."},
                   D(("Narrador", "El hombre de la gorra entra en la lonja por la puerta de atrás y saluda al encargado como a un viejo amigo."),
                     ("Ruano", "Dos noches más y vaciamos el almacén. Y que nadie vuelva a tocar las nasas de ese viejo, que luego habla.")),
                   {"tipo": "ir", "lugar": "mn_observatorio", "texto": "Vuelve al Observatorio de aves y cuéntale a Celia lo que has oído."},
                   D(("Celia", "Salvador Ruano. Fue capataz de las salinas hasta que cerraron, y por lo visto se quedó con las llaves."),
                     ("Dani", "Ha llamado viejo a Amador. Se conocen."),
                     ("Celia", "Desde críos. No sé qué guarda en esos sacos, pero sal no es. Ve con Amador: él sabrá por dónde entrarle."))],
         "recompensa": {"dinero": 450}},
        {"id": "mn03", "titulo": "Sal gorda", "capitulo": 47, "contacto": "Amador", "lugar": "mn_taberna", "requiere": ["mn02"],
         "resumen": "Los hombres de Ruano duermen en el almacén de las salinas, junto a la carga.",
         "pasos": [D(("Amador", "Salvador Ruano... Fuimos juntos a la escuela. Ya entonces vendía lo que no era suyo."),
                     ("Dani", "Dice que en dos noches vacían el almacén. Si esperamos, se van con todo."),
                     ("Amador", "Entonces no esperes. Esta noche duermen allí cuatro de los suyos, gente de fuera que no sabe ni dónde pisa."),
                     ("Amador", "Llévate mi escopeta de puesto y la fisga. La escopeta, para lejos; la fisga, si se te echan encima."),
                     ("Toñi", "Y vuelve enter[o|a], Dani, que la cuenta de la taberna no te la perdona nadie.")),
                   {"tipo": "dar", "arma": "mn_escopeta", "balas": 12},
                   {"tipo": "dar", "arma": "mn_fisga"},
                   {"tipo": "eliminar", "lugar": "mn_salinas", "texto": "Ve a las Salinas de San Ginés y acaba con los hombres de Ruano.",
                    "enemigos": [{"n": 3, "tipo": "Estibador de Ruano", "arma": "mn_fisga", "salud": 55}, {"n": 1, "tipo": "Capataz de Ruano", "arma": "pistola", "salud": 85}]},
                   {"tipo": "recoger", "lugar": "mn_salinas", "objeto": "el cuaderno de mareas de Ruano", "texto": "Recoge el cuaderno de mareas que hay sobre la mesa del almacén."},
                   {"tipo": "policia", "nivel": 1, "texto": "Los tiros se han oído hasta en el pueblo. Despista a la patrulla de la Guardia Civil."},
                   D(("Narrador", "Los sacos no llevan sal: llevan cartones de tabaco y relojes sin marca, envueltos en plástico para que aguanten el agua."),
                     ("Narrador", "El cuaderno apunta cada marea alta del mes y, al lado, una matrícula de furgoneta y una sola palabra: ciudad."),
                     ("Dani", "Lo sacan por los caños con la marea y lo suben a Puerto Bravo por carretera. Bien pensado, Ruano."))],
         "recompensa": {"dinero": 800, "arma": "mn_escopeta", "balas": 10}},
        {"id": "mn04", "titulo": "La última marea", "capitulo": 47, "contacto": "Amador", "lugar": "mn_taberna", "requiere": ["mn03"],
         "resumen": "Ruano ha cargado lo que le queda y se va esta noche a la ciudad por la carretera de la costa.",
         "final_titulo": "Marisma Negra: los caños vuelven a ser de los anguileros",
         "final": "Esa noche las anguilas entran por el caño grande sin que nadie les corte el paso. En la taberna se brinda por la barca de Amador, que ahora es tuya, y Celia vuelve a contar garzas.",
         "pasos": [D(("Amador", "Ruano sabe que fuiste tú. Ha cargado lo que le quedaba en la furgoneta frigorífica de la lonja y se va esta noche a la ciudad."),
                     ("Celia", "He vuelto a llamar a la Guardia Civil. Llegan en una hora, y en una hora Ruano ya está en Puerto Bravo."),
                     ("Dani", "Pues no llega. ¿Por dónde sale?"),
                     ("Amador", "Por la carretera de la costa, que es la única. Párale antes de que salga del pueblo, Dani. Toma más cartuchos.")),
                   {"tipo": "dar", "balas_arma": "mn_escopeta", "balas": 10},
                   {"tipo": "perseguir", "lugar": "mn_salida", "modelo": furgo, "nombre": "la furgoneta frigorífica de Ruano", "salud": 240, "limite": 300,
                    "texto": "Alcanza y destroza la furgoneta frigorífica de Ruano antes de cinco minutos."},
                   {"tipo": "recoger", "aqui": True, "objeto": "la llave del almacén de las salinas", "texto": "Recoge la llave del almacén, que ha saltado de la furgoneta."},
                   D(("Ruano", "Esto no es mío, foraster[o|a]. Yo solo lo guardo. Los que pagan están en la ciudad, y no les va a gustar."),
                     ("Dani", "Pues que vengan a buscarlo a la marisma. Ya sabemos el camino."),
                     ("Narrador", "Ruano se aleja cojeando hacia los pinos y no se vuelve a mirar atrás.")),
                   _dec("mn_cuaderno", "Tienes el cuaderno de mareas de Ruano, con fechas y matrículas. En el arcén para un coche oscuro y un hombre bien vestido te ofrece dinero por él. ¿Qué haces?",
                        ("Dárselo a Celia para la Guardia Civil", "Lo justo. Ganas fama en Marisma Negra y no cobras nada.", "Le dices al hombre del coche que el cuaderno ya tiene dueña. Se va sin despedirse.", {"fama": 4}),
                        ("Vendérselo al hombre del coche por 900 euros", "Cobras bien, y los que pagaban a Ruano seguirán usando los caños.", "El hombre cuenta los billetes sobre el capó sin quitarse los guantes.", {"dinero": 900, "fama": -3})),
                   {"tipo": "ir", "lugar": "mn_embarcadero", "texto": "Ve al Embarcadero de los Caños, donde te esperan Amador y Celia."},
                   dict(D(("Celia", "Con este cuaderno no hay quien mire para otro lado. Mañana la laguna estará llena de uniformes, y por una vez me alegro.")), si_clave="mn_cuaderno", si_opcion=1),
                   dict(D(("Celia", "¿Y el cuaderno? No, no me lo digas. Al menos Ruano no vuelve por aquí.")), si_clave="mn_cuaderno", si_opcion=2),
                   D(("Amador", "Esta noche las anguilas entran por el caño grande sin que nadie les corte el paso."),
                     ("Amador", "La barca de mi padre es tuya, Dani. Cala poco y pasa por donde no pasa nadie. Está amarrada aquí mismo."),
                     ("Toñi", "Y en la taberna tienes plato de arroz para todo el invierno. Bienvenid[o|a] a Marisma Negra.")),
                   {"tipo": "dar", "dinero": 400}],
         "recompensa": {"dinero": 1800, "chaleco": True, "barco": {"modelo": "mn_barca", "en": "mn_embarcadero"}}},
        {"id": "mn05", "titulo": "Arroz para el comedor", "vehiculo_libre": True, "capitulo": 48, "contacto": "Toñi", "lugar": "mn_ong", "requiere": ["m01"],
         "resumen": "Trabajo honrado: el Comedor de la Cofradía se ha quedado sin arroz y sin pescado.",
         "pasos": [D(("Toñi", "Los jueves cierro la taberna y echo una mano en el comedor de la Cofradía. Hoy no tenemos ni arroz ni pescado."),
                     ("Toñi", "La cooperativa nos regala diez sacos. Coge su ranchera, que está abierta, y tráela aquí sin volcar nada."),
                     ("Dani", "¿Y el pescado?"),
                     ("Toñi", "Eso después, en la lonja. Pregunta por la caja del comedor, que ya lo saben.")),
                   {"tipo": "robar", "lugar": "mn_cooperativa", "modelo": "mn_ranchera", "nombre": "la ranchera de la cooperativa", "abierto": True,
                    "texto": "Recoge la ranchera junto a la Cooperativa Arrocera La Espiga. Está abierta."},
                   {"tipo": "entregar", "lugar": "mn_ong", "salud_min": 60, "limite": 240, "texto": "Lleva la ranchera con los sacos al Comedor de la Cofradía en cuatro minutos y sin golpes."},
                   {"tipo": "recoger", "lugar": "mn_lonja", "objeto": "la caja de pescado del comedor", "texto": "Recoge en la Lonja de la Anguila la caja de pescado del comedor."},
                   {"tipo": "ir", "lugar": "mn_ong", "limite": 150, "texto": "Vuelve al Comedor de la Cofradía antes de que abran las puertas. Tienes dos minutos y medio."},
                   D(("Toñi", "Justo a tiempo. Hoy comen treinta personas gracias a ti."),
                     ("Dani", "Guárdame un plato, que huele que alimenta."))],
         "recompensa": {"dinero": 280}},
    ]
    return {
        "info": {"nombre": "Marisma Negra", "autor": "Puerto Bravo", "version": "1.0",
                 "descripcion": "Un pueblo de marisma en la costa, al sureste de Puerto Bravo: arrozales, una laguna con aves, anguileros y unas salinas cerradas "
                                "que alguien usa de noche. Cuatro misiones contra unos contrabandistas de los caños, con una decisión al final, un encargo honrado, "
                                "una escopeta de puesto, una fisga de anguilero, una barca de caños, la ranchera de la cooperativa, una carrera por los arrozales, "
                                "pesca en la laguna, búsqueda de tesoros y un personaje."},
        "capitulos": {"47": "Marisma Negra", "48": "Marisma Negra: vida honrada"},
        "mapas": [mapa],
        "lugares": lugares,
        "misiones": misiones,
        "armas": [clon(ARMAS, escopeta, id="mn_escopeta", nombre="Escopeta de puesto", dano=56, alcance=24, cadencia=1.0, precio=880,
                       desc="La escopeta de los cazadores de patos de la marisma: larga, pesada y con un tiro que se oye en toda la laguna."),
                  clon(ARMAS, cuerpo, id="mn_fisga", nombre="Fisga de anguilero", dano=30, alcance=2.8, cadencia=0.7, precio=40,
                       desc="Un tridente corto de hierro con mango de caña. Sirve para clavar anguilas en el fango, y para mantener a alguien a distancia.")],
        "vehiculos": [clon(VEHICULOS, barca, id="mn_barca", nombre="Barca de caños", vel_max=12, salud=110, valor=600, precio=7500, trabajo="mensajeria",
                           desc="Una barca de fondo plano con un fuera borda que casi no hace ruido. Cala tan poco que pasa por los caños más estrechos. Con la tecla J haces mensajería entre muelles."),
                      clon(VEHICULOS, pickup, id="mn_ranchera", nombre="Ranchera de la cooperativa", vel_max=24, salud=170, valor=800, precio=6400, trabajo="paqueteria",
                           desc="Una ranchera con la caja llena de sacos de arroz y barro hasta los retrovisores. Con la tecla J haces el reparto.")],
        "carreras": [{"id": "mn_c1", "nombre": "Vuelta a los arrozales", "mapa": MAPA, "premio": 340, "tiempo": 85, "puntos": [[2, 1], [4, 1], [4, 3], [1, 3], [1, 1], [2, 1]]}],
        "comidas": [{"nombre": "Arroz de marisma con pato", "precio": 14, "salud": 46}, {"nombre": "Anguila ahumada con pan de pueblo", "precio": 8, "salud": 26}],
        "peces": [{"nombre": "una anguila de los caños", "valor": 42, "peso": 14}, {"nombre": "una lisa de la laguna", "valor": 16, "peso": 20}],
        "personajes": [{"id": "mn_jacinta", "nombre": "Jacinta", "genero": "m", "apellido": "Juncal", "pesca": 4, "resistencia": 2, "ciudadania": 30, "arma": "mn_fisga", "dinero": 160, "botiquines": 1,
                        "desc": "Hija y nieta de anguileros de Marisma Negra. Empieza con la pesca al nivel cuatro, algo de resistencia, una fisga, ciento sesenta euros y buen nombre entre los vecinos."}],
    }


def escribir(crudo, ruta=ARCHIVO):
    """Completa el transporte, comprueba el mod con el revisor del editor y lo guarda legible. Devuelve (errores, avisos)."""
    import escribir_transporte
    escribir_transporte.completar_mod(crudo)
    from editor import modelo
    mod = modelo.Mod.desde_crudo(crudo)
    errores, avisos = modelo.comprobar(mod, modelo.Catalogo())
    mod.guardar(ruta, protegido=False)
    return errores, avisos


if __name__ == "__main__":
    errores, avisos = escribir(marisma_negra())
    print(f"{os.path.relpath(ARCHIVO, RAIZ)}: {len(errores)} errores, {len(avisos)} avisos")
    for e in errores:
        print("   ERROR", e)
    for a in avisos:
        print("   aviso", a)
    sys.exit(1 if errores else 0)
