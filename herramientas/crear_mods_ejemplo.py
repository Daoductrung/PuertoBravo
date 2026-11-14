"""Escribe en data/mods los mods completos de ejemplo y los comprueba con el mismo revisor del editor.

    .venv\\Scripts\\python.exe herramientas\\crear_mods_ejemplo.py

- costa_dorada.json: un pueblo nuevo entero, con su historia, y un ejemplo de TODO lo que admite un mod:
  mapa, lugares de casi todos los tipos, misiones con los nueve tipos de paso, armas de los tres tipos,
  coche, barco y aeronave, carrera, comidas, objeto, peces, personajes, capítulos y, para el modo adulto,
  club, proveedor, persona, plan, regalo, sustancia y misión.
- oficios_y_recados.json: un mod pequeño de vida honrada en las ciudades que ya existen.
- valdeolmos.json: otro pueblo nuevo, de interior, con su historia, su río y su carrera de tractores.
- motor_y_asfalto.json: coches, una moto, carreras y dos misiones al volante.

Todos se pueden abrir con el editor de mods para ver cómo están hechos.
"""
import copy
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from juego import rutas          # noqa: E402


def _base(archivo):
    from juego import cifrado
    return cifrado.leer_json(os.path.join(rutas.DATOS, archivo))


ARMAS = {a["id"]: a for a in _base("armas.json")["armas"]}
VEHICULOS = {v["id"]: v for v in _base("vehiculos.json")["vehiculos"]}
SUSTANCIAS = {s["id"]: s for s in _base("adultos.json")["sustancias"]}


def clon(tabla, origen, **cambios):
    d = copy.deepcopy(tabla[origen])
    d.update(cambios)
    return d


def primero(tabla, cond):
    return next(k for k, v in tabla.items() if cond(v))


def D(*lineas):
    return {"tipo": "dialogo", "lineas": [list(l) for l in lineas]}


# ============================================================ Costa Dorada
def costa_dorada():
    cuerpo = primero(ARMAS, lambda a: a["tipo"] == "cuerpo" and a["id"] != "punos")
    explosivo = primero(ARMAS, lambda a: a["tipo"] == "explosivo")
    lancha = primero(VEHICULOS, lambda v: v.get("barco"))
    aeronave = primero(VEHICULOS, lambda v: v.get("vuela"))
    furgo = "furgoneta" if "furgoneta" in VEHICULOS else "utilitario"
    mapa = {
        "id": "costa_dorada", "tipo": "pueblo", "nombre": "Costa Dorada", "trafico": 2, "peatones": 4,
        "avenidas": ["Avenida del Espigón", "Calle de las Redes", "Calle del Azafrán", "Avenida de los Naranjos", "Camino del Faro Viejo"],
        "calles": ["Paseo de la Costa", "Calle de la Lonja", "Calle del Mercado", "Carretera de Puerto Bravo"],
        "barrios": [
            {"id": "cd_marina", "nombre": "La Marina", "i": [0, 3], "j": [0, 0], "ambiente": "amb_playa", "vehiculos": ["utilitario", "bici", "cd_buggy"],
             "descripcion": "La Marina de Costa Dorada: redes tendidas al sol, olor a brea y barcas varadas en la arena."},
            {"id": "cd_pueblo", "nombre": "El Pueblo", "i": [0, 3], "j": [1, 2], "ambiente": "amb_residencial", "vehiculos": ["utilitario", furgo, "cd_reparto"],
             "descripcion": "El Pueblo: casas encaladas, naranjos en las aceras y una plaza con mercado todas las mañanas."}],
        "bloques": {"0,0": "arena", "1,0": "arena", "3,0": "muelle", "1,1": "plaza", "3,2": "hierba"},
        "lugares": [
            {"id": "cd_salida", "nombre": "Salida norte, carretera de Puerto Bravo", "tipo": "salida", "bloque": [2, 2], "lado": "N", "pos": 36, "a_mapa": "puerto_bravo", "a_lugar": "pb_salida_costa", "km": 22, "horas": 0.6, "desc": "La carretera de la costa, que lleva a Puerto Bravo."},
            {"id": "cd_estacion", "nombre": "Parada del autobús de Costa Dorada", "tipo": "estacion", "bloque": [0, 2], "lado": "S", "pos": 36, "precio": 15, "desc": "Una marquesina junto al mercado."},
            {"id": "cd_embarcadero", "nombre": "Embarcadero de Costa Dorada", "tipo": "embarcadero", "bloque": [3, 0], "lado": "S", "pos": 36, "a_mapa": "mar", "a_lugar": "mar_costa", "desc": "Un muelle de tablones con cuatro barcas."},
            {"id": "cd_taberna", "nombre": "Taberna El Ancla", "tipo": "taberna", "bloque": [2, 0], "lado": "N", "pos": 20, "desc": "Vino de la tierra, dados y un tablón con encargos."},
            {"id": "cd_lonja", "nombre": "Lonja de Costa Dorada", "tipo": "pescaderia", "bloque": [2, 0], "lado": "E", "pos": 36, "sonido": "lugar_tienda", "desc": "Aquí se subasta el pescado al amanecer. Compran todo lo que traigas."},
            {"id": "cd_restaurante", "nombre": "Arrocería La Barraca", "tipo": "comida", "bloque": [0, 1], "lado": "S", "pos": 36, "desc": "El mejor arroz de la costa."},
            {"id": "cd_tienda", "nombre": "Ultramarinos Azafrán", "tipo": "tienda", "bloque": [2, 1], "lado": "O", "pos": 36, "desc": "De todo un poco, y amuletos de pescador."},
            {"id": "cd_armeria", "nombre": "Efectos Navales Poniente", "tipo": "armeria", "bloque": [3, 1], "lado": "S", "pos": 36, "desc": "Arpones, remos, bengalas y lo que haga falta en la mar."},
            {"id": "cd_farmacia", "nombre": "Farmacia del Mercado", "tipo": "farmacia", "bloque": [0, 1], "lado": "E", "pos": 36, "desc": "Tiritas, botiquines y consejos de la boticaria."},
            {"id": "cd_taller", "nombre": "Taller Mecánico Naranjo", "tipo": "taller", "bloque": [3, 1], "lado": "N", "pos": 36, "desc": "Repara, pinta y no pregunta."},
            {"id": "cd_banco", "nombre": "Caja Rural de la Costa", "tipo": "banco", "bloque": [2, 1], "lado": "N", "pos": 36, "desc": "Una sucursal pequeña con un cajero de los de antes."},
            {"id": "cd_gimnasio", "nombre": "Club de Remo", "tipo": "gimnasio", "bloque": [2, 2], "lado": "S", "pos": 20, "desc": "Remo en seco, pesas y combates los viernes."},
            {"id": "cd_hostal", "nombre": "Hostal La Marea", "tipo": "hotel", "bloque": [0, 2], "lado": "E", "pos": 36, "precio_noche": 35, "desc": "Sábanas limpias y el mar de fondo."},
            {"id": "cd_casa", "nombre": "Casa del pescador", "tipo": "casa", "bloque": [2, 0], "lado": "O", "pos": 36, "precio": 4800, "garaje": 2, "desc": "Una casita encalada frente a la playa, con cobertizo para dos vehículos."},
            {"id": "cd_conservera", "nombre": "Conservera La Dorada", "tipo": "negocio", "bloque": [3, 1], "lado": "O", "pos": 36, "sonido": "lugar_taller", "precio": 22000, "ingresos": 520, "desc": "Una fábrica de conservas en venta. Da dinero cada medianoche."},
            {"id": "cd_empleo", "nombre": "Cofradía de pescadores, bolsa de trabajo", "tipo": "empleo", "bloque": [1, 2], "lado": "S", "pos": 36, "desc": "Aquí se reparten las jornadas y los oficios del pueblo."},
            {"id": "cd_escuela", "nombre": "Escuela Náutica", "tipo": "academia", "bloque": [1, 2], "lado": "E", "pos": 36, "cursos": ["pesca", "resistencia"], "desc": "Cursos de pesca y de resistencia."},
            {"id": "cd_caritas", "nombre": "Despensa Solidaria", "tipo": "ong", "bloque": [0, 2], "lado": "N", "pos": 20, "desc": "Reparten comida a quien la necesita. Siempre faltan manos."},
            {"id": "cd_concesionario", "nombre": "Automóviles de Ocasión Levante", "tipo": "concesionario", "bloque": [2, 2], "lado": "E", "pos": 36, "modelos": ["cd_buggy", "cd_reparto", "utilitario"], "desc": "Coches de segunda mano y los buggies de la playa."},
            {"id": "cd_nautica", "nombre": "Náutica Costa Dorada", "tipo": "nautica", "bloque": [2, 0], "lado": "S", "pos": 60, "embarcadero": "cd_embarcadero", "desc": "Venden veleros y los dejan amarrados en el embarcadero."},
            {"id": "cd_taxi", "nombre": "Parada de taxis del Mercado", "tipo": "taxi", "bloque": [1, 2], "lado": "O", "pos": 36, "vehiculo": "taxi", "desc": "Dos taxis y un taxista dormido."},
            {"id": "cd_circuito", "nombre": "Salida del circuito de la playa", "tipo": "carrera", "bloque": [0, 1], "lado": "O", "pos": 36, "desc": "Los domingos se corre con buggies."},
            {"id": "cd_helipuerto", "nombre": "Helipuerto del Faro Viejo", "tipo": "helipuerto", "bloque": [3, 2], "lado": "S", "pos": 36, "vehiculo": "cd_autogiro", "precio": 120, "desc": "Una explanada con una manga de viento."},
            {"id": "cd_plaza", "nombre": "Plaza del Mercado", "tipo": "monumento", "bloque": [1, 1], "xy": [36, 36], "sonido": "lugar_fuente", "desc": "Una fuente, cuatro naranjos y los puestos del mercado."},
            {"id": "cd_faro", "nombre": "El Faro Viejo", "tipo": "monumento", "bloque": [3, 2], "xy": [45, 50], "sonido": "lugar_iglesia", "desc": "Un faro apagado hace cuarenta años. Dicen que quien sube ve hasta Isla Tortuga."},
            {"id": "cd_espigon", "nombre": "Espigón de Costa Dorada", "tipo": "pesca", "bloque": [1, 0], "xy": [40, 20], "desc": "El mejor sitio para la dorada de roca."},
            {"id": "cd_cala", "nombre": "Cala de los Detectores", "tipo": "tesoro", "bloque": [0, 0], "xy": [30, 20], "desc": "Los turistas pierden aquí de todo."},
            {"id": "cd_club", "nombre": "Sala Marejada", "tipo": "club", "bloque": [3, 1], "lado": "E", "pos": 36, "adultos": True, "desc": "Copas, espectáculo y la gente guapa de la costa."},
            {"id": "cd_bodeguero", "nombre": "Almacén del Bodeguero", "tipo": "proveedor", "bloque": [0, 1], "lado": "N", "pos": 36, "adultos": True, "factor": {"hierba": 0.8, "polvo": 1.3, "pastillas": 1.0, "cristal": 1.4, "cd_licor": 0.7}, "desc": "Orujo de hierbas de contrabando y lo que traigan las lanchas."},
        ],
        "casetes": [[50, 110], [300, 200]],
    }
    lugares = [
        {"id": "pb_salida_costa", "mapa": "puerto_bravo", "nombre": "Salida oeste, carretera de Costa Dorada", "tipo": "salida", "bloque": [0, 4], "lado": "O", "pos": 36, "a_mapa": "costa_dorada", "a_lugar": "cd_salida", "km": 22, "horas": 0.6, "desc": "La carretera de la costa, que lleva a Costa Dorada."},
        {"id": "mar_costa", "mapa": "mar", "nombre": "Embarcadero de Costa Dorada, desde el mar", "tipo": "muelle", "xy": [60, 1100], "a_mapa": "costa_dorada", "a_lugar": "cd_embarcadero", "desc": "El muelle de tablones de Costa Dorada, al oeste de Puerto Bravo."},
    ]
    armas = [
        clon(ARMAS, "rifle", id="cd_arpon", nombre="Fusil de arpones", dano=85, alcance=28, cadencia=1.6, precision=0.9, cargador=1, precio=900, balas=6, precio_balas=60, ruido=1,
             desc="Un solo arpón por disparo y tarda en recargar, pero casi no hace ruido y donde da, se queda."),
        clon(ARMAS, cuerpo, id="cd_remo", nombre="Remo de madera", dano=30, alcance=3.2, cadencia=0.8, precio=40, desc="Largo, pesado y siempre a mano en un pueblo de pescadores."),
        clon(ARMAS, explosivo, id="cd_bengala", nombre="Bengala de señales", dano=60, precio=180, desc="Se lanza como una granada. Arde, asusta y hace menos daño que una de verdad."),
    ]
    vehiculos = [
        clon(VEHICULOS, "utilitario", id="cd_buggy", nombre="Buggy de playa", vel_max=30, acel=8.5, freno=15, salud=80, tono=1.4, valor=700, precio=5200, desc="Ligero y nervioso. Acelera como un demonio y se rompe con mirarlo."),
        clon(VEHICULOS, furgo, id="cd_reparto", nombre="Furgoneta de reparto del pescado", salud=140, valor=600, precio=4200, trabajo="paqueteria", desc="Huele a lonja. Con la tecla J haces el reparto de paquetes."),
        clon(VEHICULOS, lancha, id="cd_velero", nombre="Velero Tramontana", vel_max=17, acel=3.5, salud=180, precio=16000, trabajo="mensajeria", desc="Un velero de dos palos. Silencioso y marinero."),
        clon(VEHICULOS, aeronave, id="cd_autogiro", nombre="Autogiro Libélula", vel_max=34, salud=110, precio=52000, desc="Un autogiro de dos plazas. Vuela por encima de todo, como el helicóptero, pero más despacio."),
    ]
    misiones = [
        {"id": "cd01", "titulo": "Bienvenido a Costa Dorada", "capitulo": 20, "contacto": "Amparo", "lugar": "cd_taberna", "requiere": ["m01"],
         "resumen": "En la Taberna El Ancla, Amparo necesita a alguien que no sea del pueblo.",
         "pasos": [D(("Amparo", "Tú no eres de aquí. Mejor. Aquí todos son primos de alguien y nadie quiere líos."),
                     ("Amparo", "Eres Dani, ¿no? Me han hablado de ti. Sube al Faro Viejo y mira si es verdad que alguien ha roto el candado. Yo no puedo dejar la barra.")),
                   {"tipo": "ir", "lugar": "cd_faro", "radio": 14, "texto": "Sube al Faro Viejo, al noreste del pueblo, y mira el candado."},
                   D(("Narrador", "El candado está cortado con una cizalla. Dentro hay cajas de madera sin marcar, y huele a gasóleo."),
                     ("Narrador", "Alguien usa el faro de almacén. Vuelves a contárselo a Amparo."))],
         "recompensa": {"dinero": 250}},
        {"id": "cd02", "titulo": "La furgoneta del pescado", "capitulo": 20, "contacto": "Amparo", "lugar": "cd_taberna", "requiere": ["cd01"],
         "resumen": "La furgoneta de la lonja lleva dos días sin repartir y el arroz no espera.",
         "pasos": [D(("Amparo", "El chaval del reparto no aparece y la furgoneta sigue en la lonja, con las llaves puestas. Llévala a La Barraca antes de que se eche a perder el género."),
                     ("Amparo", "Y con cuidado, que si llega abollada el Sento no te paga.")),
                   {"tipo": "robar", "lugar": "cd_lonja", "modelo": "cd_reparto", "nombre": "la furgoneta del pescado", "abierto": True, "texto": "Recoge la furgoneta del pescado junto a la Lonja. Está abierta."},
                   {"tipo": "entregar", "lugar": "cd_restaurante", "salud_min": 60, "limite": 240, "texto": "Lleva la furgoneta a la Arrocería La Barraca en cuatro minutos y sin destrozarla."},
                   D(("Sento", "¡Por fin! Otro día sin gamba y cierro. Toma, y dile a Amparo que le debo una paella."))],
         "recompensa": {"dinero": 400}},
        {"id": "cd03", "titulo": "Los de la lancha", "capitulo": 20, "contacto": "Amparo", "lugar": "cd_taberna", "requiere": ["cd02"],
         "resumen": "Los dueños de las cajas del faro han venido a por el chaval del reparto.",
         "pasos": [D(("Amparo", "Ya sé dónde está el chaval. Lo tienen los de la lancha negra en el embarcadero, porque vio lo que no debía."),
                     ("Amparo", "Toma el fusil de arpones de mi difunto marido. Un tiro cada vez, así que apunta.")),
                   {"tipo": "dar", "arma": "cd_arpon", "balas": 8},
                   {"tipo": "eliminar", "lugar": "cd_embarcadero", "texto": "Ve al embarcadero y acaba con los de la lancha negra.",
                    "enemigos": [{"n": 2, "tipo": "Contrabandista", "arma": "pistola", "salud": 60}, {"n": 1, "tipo": "Patrón de la lancha", "arma": "cd_remo", "salud": 90}]},
                   {"tipo": "recoger", "lugar": "cd_embarcadero", "objeto": "el cuaderno de entregas", "texto": "Recoge el cuaderno de entregas que ha quedado en el muelle."},
                   D(("Narrador", "El chaval sale de debajo de una lona, blanco como la cal, y echa a correr hacia el pueblo."),
                     ("Narrador", "El cuaderno tiene fechas, matrículas y un nombre que se repite: el Bodeguero."))],
         "recompensa": {"dinero": 600, "arma": "cd_arpon", "balas": 6}},
        {"id": "cd04", "titulo": "Sirenas en el paseo", "capitulo": 20, "contacto": "Amparo", "lugar": "cd_taberna", "requiere": ["cd03"],
         "resumen": "Hay que sacar las cajas del faro antes de que alguien avise a la Guardia Civil.",
         "pasos": [D(("Amparo", "Si encuentran esas cajas en el faro, cierran el pueblo entero. Hay un buggy cargado junto al helipuerto. Tíralo todo al desguace del Naranjo."),
                     ("Amparo", "Te van a ver, eso seguro. Piérdelos antes de entregar.")),
                   {"tipo": "robar", "lugar": "cd_helipuerto", "modelo": "cd_buggy", "nombre": "el buggy cargado", "busqueda": 2, "texto": "Hazte con el buggy cargado que hay junto al Helipuerto del Faro Viejo."},
                   {"tipo": "policia", "nivel": 2, "texto": "Te han visto. Despista a la policía."},
                   {"tipo": "entregar", "lugar": "cd_taller", "salud_min": 30, "texto": "Lleva el buggy al Taller Mecánico Naranjo."},
                   D(("Naranjo", "Mañana esto es chatarra y aquí no ha pasado nada."))],
         "recompensa": {"dinero": 900, "chaleco": True}},
        {"id": "cd05", "titulo": "El Bodeguero se escapa", "capitulo": 20, "contacto": "Amparo", "lugar": "cd_taberna", "requiere": ["cd04"],
         "resumen": "El Bodeguero ha cargado lo que le queda y sale del pueblo por la carretera.",
         "pasos": [D(("Amparo", "Se va. Ha cargado su todoterreno y tira para la carretera de Puerto Bravo. Si llega, vuelve con más gente.")),
                   {"tipo": "dar", "balas_arma": "cd_arpon", "balas": 6},
                   {"tipo": "dar", "arma": "cd_bengala", "balas": 3},
                   {"tipo": "perseguir", "lugar": "cd_salida", "modelo": "todoterreno" if "todoterreno" in VEHICULOS else "utilitario", "nombre": "el todoterreno del Bodeguero", "salud": 220, "limite": 300,
                    "texto": "Alcanza y destroza el todoterreno del Bodeguero antes de que pasen cinco minutos."},
                   {"tipo": "recoger", "aqui": True, "objeto": "la llave del almacén", "texto": "Recoge la llave del almacén que ha saltado del todoterreno."},
                   D(("Narrador", "Costa Dorada vuelve a oler solo a brea y a arroz."),
                     ("Amparo", "El pueblo te debe una, Dani. El velero de mi marido es tuyo: está amarrado en el embarcadero.")),
                   {"tipo": "dar", "dinero": 500}],
         "recompensa": {"dinero": 2000, "barco": {"modelo": "cd_velero", "en": "cd_embarcadero"}}},
        {"id": "cd06", "titulo": "Un día de mercado", "capitulo": 21, "contacto": "La boticaria", "lugar": "cd_farmacia", "requiere": ["m01"],
         "resumen": "Trabajo honrado: recados por el pueblo antes de que cierre el mercado.",
         "pasos": [D(("La boticaria", "¿Tú haces recados? Tres cosas, y rápido, que cierro a las dos."),
                     ("La boticaria", "Lleva este jarabe a la Despensa Solidaria, pasa por la Cofradía a por mis papeles y tráeme azafrán de los ultramarinos.")),
                   {"tipo": "ir", "lugar": "cd_caritas", "limite": 150, "texto": "Lleva el jarabe a la Despensa Solidaria en dos minutos y medio."},
                   {"tipo": "ir", "lugar": "cd_empleo", "texto": "Pasa por la Cofradía de pescadores."},
                   {"tipo": "recoger", "lugar": "cd_tienda", "objeto": "el azafrán", "texto": "Recoge el azafrán en Ultramarinos Azafrán."},
                   {"tipo": "ir", "lugar": "cd_farmacia", "texto": "Vuelve a la Farmacia del Mercado."},
                   D(("La boticaria", "Así da gusto. Toma, y un botiquín de regalo, que con la vida que llevas te hará falta."))],
         "recompensa": {"dinero": 350}},
        {"id": "cda1", "titulo": "Orujo de hierbas", "capitulo": 22, "adultos": True, "contacto": "Marina", "lugar": "cd_club", "requiere": ["cd01"],
         "resumen": "En la Sala Marejada, Marina necesita que alguien lleve una caja sin hacer preguntas.",
         "pasos": [D(("Marina", "El orujo del Bodeguero es lo único que se vende aquí en invierno. Llévale estas botellas a Amparo, a El Ancla, y quédate dos para ti.")),
                   {"tipo": "dar", "sustancia": "cd_licor", "cantidad": 2},
                   {"tipo": "ir", "lugar": "cd_taberna", "texto": "Lleva las botellas a la Taberna El Ancla."},
                   D(("Amparo", "Dile a Marina que la próxima vez venga ella, que hace un mes que no la veo."))],
         "recompensa": {"dinero": 300, "afinidad": {"cd_marina": 15}}},
    ]
    return {
        "info": {"nombre": "Costa Dorada", "autor": "Puerto Bravo", "version": "1.0",
                 "descripcion": "Un pueblo pesquero nuevo al oeste de Puerto Bravo, con su historia en cinco misiones, trabajo honrado, armas, vehículos, un velero, un autogiro, una carrera y dos personajes. Sirve de ejemplo de todo lo que puede llevar un mod."},
        "capitulos": {"20": "Costa Dorada", "21": "Costa Dorada: vida honrada", "22": "Costa Dorada: historias para adultos"},
        "mapas": [mapa], "lugares": lugares, "misiones": misiones, "armas": armas, "vehiculos": vehiculos,
        "carreras": [{"id": "cd_c1", "nombre": "Vuelta a Costa Dorada", "mapa": "costa_dorada", "premio": 350, "tiempo": 80, "puntos": [[0, 1], [0, 3], [4, 3], [4, 1], [0, 1]]}],
        "comidas": [{"nombre": "Arroz a banda", "precio": 14, "salud": 45}, {"nombre": "Horchata con fartons", "precio": 5, "salud": 12}],
        "objetos": [{"id": "cd_amuleto", "nombre": "Amuleto de pescador", "precio": 25, "desc": "Una caracola con un cordel. No sirve para nada, pero da conversación."}],
        "peces": [{"nombre": "una dorada de roca", "valor": 38, "peso": 12}, {"nombre": "un pulpo de Costa Dorada", "valor": 55, "peso": 6}],
        "personajes": [
            {"id": "cd_vicenta", "nombre": "Vicenta", "apellido": "Ribera", "pesca": 5, "resistencia": 2, "dinero": 300, "ciudadania": 30, "arma": "cd_remo", "botiquines": 1,
             "desc": "Patrona de pesca de Costa Dorada. Empieza con la pesca al nivel cinco, buena resistencia, un remo, trescientos euros y el respeto de los vecinos."},
            {"id": "cd_quico", "nombre": "Quico", "apellido": "Marí", "conduccion": 3, "punteria": 2, "reputacion": 20, "ganzuas": 2, "botiquines": 1,
             "desc": "Hizo de todo en las lanchas del contrabando. Empieza con conducción al nivel tres, algo de puntería, fama en la calle y dos juegos de ganzúas."}],
        "personas": [{"id": "cd_marina", "nombre": "Marina", "edad": 33, "lugar": "cd_club", "gustos": ["cd_velada", "paseo"], "regalo": "cd_perla",
                      "desc": "Lleva la Sala Marejada desde que murió su tío. Seria de día, otra persona de noche. Conoce todos los secretos del pueblo y no cuenta ninguno."}],
        "actividades": [{"id": "cd_velada", "nombre": "Cenar arroz en La Barraca", "precio": 40, "horas": 3}],
        "regalos": [{"id": "cd_perla", "nombre": "Una perla de la lonja", "precio": 120, "afinidad": 12}],
        "sustancias": [clon(SUSTANCIAS, "alcohol", id="cd_licor", nombre="Orujo de hierbas", unidad="botella", precio=18, animo=9, adiccion=2.0, sobredosis=4,
                            desc="Orujo de hierbas de contrabando. Sube el ánimo más que una copa y tumba antes: a la cuarta seguida acabas en el hospital.")],
    }


# ============================================================ Oficios y recados
def oficios():
    return {
        "info": {"nombre": "Oficios y recados", "autor": "Puerto Bravo", "version": "1.0",
                 "descripcion": "Más vida honrada en Puerto Bravo: una academia de puntería deportiva, un banco de alimentos, una casa, un negocio, una moto de mensajería, un personaje y dos encargos de recadero."},
        "capitulos": {"23": "Oficios y recados"},
        "lugares": [
            {"id": "of_tiro", "mapa": "puerto_bravo", "nombre": "Club de Tiro Olímpico", "tipo": "academia", "bloque": [6, 5], "lado": "S", "pos": 20, "cursos": ["punteria"], "desc": "Tiro deportivo con monitor. Aquí la puntería se aprende sin hacer daño a nadie."},
            {"id": "of_alimentos", "mapa": "puerto_bravo", "nombre": "Banco de Alimentos del Barrio Viejo", "tipo": "ong", "bloque": [2, 4], "lado": "S", "pos": 20, "desc": "Voluntarios, cajas de fruta y mucha cola a final de mes."},
            {"id": "of_mensajeria", "mapa": "puerto_bravo", "nombre": "Mensajería Relámpago", "tipo": "negocio", "bloque": [4, 5], "lado": "S", "pos": 20, "sonido": "lugar_empleo", "precio": 9000, "ingresos": 260, "vehiculo": "of_moto", "desc": "Una empresa de mensajería en venta. En la puerta hay siempre una moto de reparto: súbete y pulsa J."},
            {"id": "of_piso", "mapa": "puerto_bravo", "nombre": "Piso de la calle de los Herreros", "tipo": "casa", "bloque": [3, 5], "lado": "S", "pos": 50, "precio": 3900, "garaje": 1, "desc": "Un tercero sin ascensor, pequeño y luminoso, con una plaza de garaje."},
        ],
        "vehiculos": [clon(VEHICULOS, "moto" if "moto" in VEHICULOS else "utilitario", id="of_moto", nombre="Moto de mensajería", vel_max=27, salud=75, valor=350, precio=1900, trabajo="paqueteria",
                           desc="Una moto de reparto con un cajón detrás. Con la tecla J haces de mensajero.")],
        "personajes": [{"id": "of_noa", "nombre": "Noa", "apellido": "Santos", "ciudadania": 60, "animo": 80, "resistencia": 3, "dinero": 150, "botiquines": 2,
                        "desc": "Trabajó diez años de mensajera en bicicleta. Empieza con muy buen nombre entre los vecinos, buen ánimo, resistencia al nivel tres y dos botiquines: ideal para una vida honrada."}],
        "misiones": [
            {"id": "of01", "titulo": "Cajas para el banco de alimentos", "capitulo": 23, "contacto": "Reme", "lugar": "of_alimentos", "requiere": ["m01"],
             "resumen": "Trabajo honrado: el Banco de Alimentos necesita un transportista.",
             "pasos": [D(("Reme", "Tenemos una donación esperando en el mercado y nadie con carné. ¿Tú conduces?")),
                       {"tipo": "robar", "lugar": "of_mensajeria", "modelo": "furgoneta" if "furgoneta" in VEHICULOS else "utilitario", "nombre": "la furgoneta prestada", "abierto": True, "texto": "Recoge la furgoneta que os presta Mensajería Relámpago. Está abierta."},
                       {"tipo": "entregar", "lugar": "of_alimentos", "salud_min": 70, "texto": "Lleva la furgoneta con las cajas al Banco de Alimentos, sin golpes."},
                       D(("Reme", "Con esto comen cuarenta familias. Gracias, de verdad."))],
             "recompensa": {"dinero": 150}},
            {"id": "of02", "titulo": "Contrarreloj", "capitulo": 23, "contacto": "El encargado", "lugar": "of_mensajeria", "requiere": ["of01"],
             "resumen": "Trabajo honrado: un sobre urgente tiene que llegar al hospital.",
             "pasos": [D(("El encargado", "Sobre urgente para el hospital. Si llegas en tres minutos, hay propina.")),
                       {"tipo": "ir", "lugar": "hospital", "limite": 180, "texto": "Lleva el sobre al Hospital General en tres minutos."},
                       D(("Narrador", "Una doctora firma el recibo sin levantar la vista. Trabajo hecho."))],
             "recompensa": {"dinero": 220}},
        ],
    }


# ============================================================ Valdeolmos
def valdeolmos():
    escopeta = "escopeta" if "escopeta" in ARMAS else primero(ARMAS, lambda a: a["tipo"] == "fuego")
    cuerpo = primero(ARMAS, lambda a: a["tipo"] == "cuerpo" and a["id"] != "punos")
    tractor = "tractor" if "tractor" in VEHICULOS else "utilitario"
    todo = "todoterreno" if "todoterreno" in VEHICULOS else "utilitario"
    mapa = {
        "id": "valdeolmos", "tipo": "pueblo", "nombre": "Valdeolmos", "trafico": 1, "peatones": 3,
        "avenidas": ["Camino de las Viñas", "Calle del Lagar", "Calle de la Vendimia", "Carretera de la Bodega"],
        "calles": ["Carretera de Puerto Bravo", "Calle de la Plaza", "Calle de los Olmos", "Camino del Río"],
        "barrios": [
            {"id": "vo_pueblo", "nombre": "Valdeolmos", "i": [0, 2], "j": [0, 1], "ambiente": "amb_campo", "vehiculos": [tractor, todo, "vo_remolque", "bici"],
             "descripcion": "Valdeolmos, un pueblo de viñas y bodegas. Huele a mosto en septiembre y a leña el resto del año."},
            {"id": "vo_ribera", "nombre": "La Ribera", "i": [0, 2], "j": [2, 2], "ambiente": "amb_parque", "vehiculos": [todo, "bici"],
             "descripcion": "La Ribera: huertas, olmos viejos y el río Olmedilla, que baja frío y con truchas."}],
        "bloques": {"1,0": "plaza", "0,2": "hierba", "1,2": "hierba", "2,2": "hierba"},
        "lugares": [
            {"id": "vo_salida", "nombre": "Salida sur, carretera de Puerto Bravo", "tipo": "salida", "bloque": [1, 0], "lado": "S", "pos": 36, "a_mapa": "puerto_bravo", "a_lugar": "pb_salida_valdeolmos", "km": 31, "horas": 0.8, "desc": "La carretera que baja hasta Puerto Bravo entre viñedos."},
            {"id": "vo_estacion", "nombre": "Parada del autobús de Valdeolmos", "tipo": "estacion", "bloque": [0, 0], "lado": "N", "pos": 20, "precio": 22, "desc": "Una parada con un banco de piedra bajo un olmo."},
            {"id": "vo_bodega", "nombre": "Bodegas Hermanos Olmedo", "tipo": "taberna", "bloque": [2, 1], "lado": "S", "pos": 36, "desc": "Vino de la casa, partidas de dados y gente que sabe todo lo que pasa en el valle."},
            {"id": "vo_cooperativa", "nombre": "Cooperativa Vinícola", "tipo": "negocio", "bloque": [2, 0], "lado": "N", "pos": 36, "sonido": "lugar_taller", "precio": 18000, "ingresos": 430, "desc": "La cooperativa del pueblo, en venta desde que se jubiló el presidente."},
            {"id": "vo_meson", "nombre": "Mesón del Lagar", "tipo": "comida", "bloque": [0, 0], "lado": "E", "pos": 36, "desc": "Cordero asado y vino del año."},
            {"id": "vo_tienda", "nombre": "Colmado de la Plaza", "tipo": "tienda", "bloque": [0, 1], "lado": "S", "pos": 36, "desc": "Una tienda de pueblo donde hay de todo y se fía hasta fin de mes."},
            {"id": "vo_armeria", "nombre": "Armería del Coto", "tipo": "armeria", "bloque": [1, 1], "lado": "S", "pos": 36, "desc": "Escopetas de caza, cartuchos y hoces bien afiladas."},
            {"id": "vo_botica", "nombre": "Botica de Valdeolmos", "tipo": "farmacia", "bloque": [0, 1], "lado": "E", "pos": 36, "desc": "La botica de siempre, con su báscula de hierro."},
            {"id": "vo_taller", "nombre": "Taller Agrícola Ruedas", "tipo": "taller", "bloque": [2, 0], "lado": "O", "pos": 36, "desc": "Arreglan tractores, y lo que les lleves."},
            {"id": "vo_casa", "nombre": "Casa del viñador", "tipo": "casa", "bloque": [1, 1], "lado": "O", "pos": 36, "precio": 5200, "garaje": 3, "desc": "Una casa de piedra con lagar y cochera para tres vehículos."},
            {"id": "vo_empleo", "nombre": "Sindicato Agrario, bolsa de trabajo", "tipo": "empleo", "bloque": [1, 1], "lado": "E", "pos": 36, "desc": "Jornadas de vendimia y oficios del campo."},
            {"id": "vo_escuela", "nombre": "Escuela de Capataces", "tipo": "academia", "bloque": [2, 1], "lado": "O", "pos": 36, "cursos": ["conduccion", "resistencia"], "desc": "Cursos de conducción de maquinaria y de resistencia."},
            {"id": "vo_parroquia", "nombre": "Despensa de la Parroquia", "tipo": "ong", "bloque": [0, 1], "lado": "N", "pos": 36, "desc": "Reparten comida y ropa. Siempre hacen falta manos."},
            {"id": "vo_hostal", "nombre": "Posada del Olmo", "tipo": "hotel", "bloque": [2, 1], "lado": "N", "pos": 36, "precio_noche": 30, "desc": "Camas de lana y silencio de pueblo."},
            {"id": "vo_circuito", "nombre": "Salida de la carrera de tractores", "tipo": "carrera", "bloque": [0, 0], "lado": "O", "pos": 36, "desc": "En fiestas se corre con lo que tenga ruedas."},
            {"id": "vo_plaza", "nombre": "Plaza del Olmo", "tipo": "monumento", "bloque": [1, 0], "xy": [36, 40], "sonido": "lugar_fuente", "desc": "Un olmo centenario y un caño de agua helada."},
            {"id": "vo_ermita", "nombre": "Ermita de San Roque", "tipo": "monumento", "bloque": [2, 2], "xy": [45, 45], "sonido": "lugar_iglesia", "desc": "Una ermita blanca entre viñas, con una campana que avisa de las tormentas."},
            {"id": "vo_rio", "nombre": "Poza del río Olmedilla", "tipo": "pesca", "bloque": [0, 2], "xy": [40, 40], "sonido": "lugar_rio", "desc": "Truchas y barbos en agua limpia."},
            {"id": "vo_vina", "nombre": "Viña Vieja", "tipo": "monumento", "bloque": [1, 2], "xy": [36, 36], "desc": "Las cepas más viejas del valle, retorcidas como manos."},
        ],
        "casetes": [[60, 120], [200, 230]],
    }
    misiones = [
        {"id": "vo01", "titulo": "Vendimia", "capitulo": 24, "contacto": "Aurelio", "lugar": "vo_bodega", "requiere": ["m01"],
         "resumen": "En Bodegas Hermanos Olmedo falta gente para sacar la uva antes de la tormenta.",
         "pasos": [D(("Aurelio", "Viene tormenta y tengo media cosecha en la Viña Vieja. ¿Sabes llevar un tractor? Da igual, se aprende."),
                     ("Aurelio", "Coge el tractor con el remolque en la Cooperativa y tráelo entero al Taller, que hay que cambiarle una rueda antes de cargar.")),
                   {"tipo": "robar", "lugar": "vo_cooperativa", "modelo": "vo_remolque", "nombre": "el tractor con remolque", "abierto": True, "texto": "Recoge el tractor con remolque junto a la Cooperativa Vinícola."},
                   {"tipo": "entregar", "lugar": "vo_taller", "salud_min": 70, "texto": "Llévalo al Taller Agrícola Ruedas sin golpearlo."},
                   {"tipo": "ir", "lugar": "vo_vina", "radio": 16, "limite": 200, "texto": "Corre a la Viña Vieja antes de que empiece a llover. Tienes poco más de tres minutos."},
                   D(("Narrador", "Llegas con los primeros goterones. Entre seis cargáis las últimas cajas."),
                     ("Aurelio", "Buena mano tienes. Pásate mañana, que tengo otro asunto menos limpio."))],
         "recompensa": {"dinero": 350}},
        {"id": "vo02", "titulo": "Vino aguado", "capitulo": 24, "contacto": "Aurelio", "lugar": "vo_bodega", "requiere": ["vo01"],
         "resumen": "Alguien está vendiendo vino falso con la etiqueta de los Olmedo.",
         "pasos": [D(("Aurelio", "Me están hundiendo. Sale de aquí un camión con vino de garrafa y mi etiqueta. Carga en la ermita, de noche."),
                     ("Aurelio", "Toma la escopeta de mi padre. No quiero muertos si se puede evitar, pero tampoco quiero que te maten.")),
                   {"tipo": "dar", "arma": "vo_escopeta", "balas": 10},
                   {"tipo": "eliminar", "lugar": "vo_ermita", "texto": "Ve a la Ermita de San Roque y acaba con los que cargan el vino falso.",
                    "enemigos": [{"n": 2, "tipo": "Mozo de carga", "arma": "vo_hoz", "salud": 55}, {"n": 1, "tipo": "Capataz", "arma": "pistola", "salud": 80}]},
                   {"tipo": "recoger", "lugar": "vo_ermita", "objeto": "el rollo de etiquetas falsas", "texto": "Recoge el rollo de etiquetas falsas."},
                   D(("Narrador", "Las etiquetas llevan el sello de una imprenta de Puerto Bravo. Alguien de la ciudad paga todo esto."))],
         "recompensa": {"dinero": 700, "arma": "vo_escopeta", "balas": 8}},
        {"id": "vo03", "titulo": "El camión de las garrafas", "capitulo": 24, "contacto": "Aurelio", "lugar": "vo_bodega", "requiere": ["vo02"],
         "resumen": "El último camión de vino falso sale hoy del valle.",
         "pasos": [D(("Aurelio", "Sale el último camión, por la carretera de Puerto Bravo. Si lo paras, se acabó. La Guardia Civil va a preguntar, así que no te quedes cerca.")),
                   {"tipo": "dar", "balas_arma": "vo_escopeta", "balas": 12},
                   {"tipo": "perseguir", "lugar": "vo_salida", "modelo": "camion" if "camion" in VEHICULOS else "utilitario", "nombre": "el camión de las garrafas", "salud": 260, "limite": 320,
                    "texto": "Alcanza y destroza el camión de las garrafas antes de que salga del valle."},
                   {"tipo": "policia", "nivel": 2, "texto": "Han dado el aviso. Despista a la Guardia Civil."},
                   {"tipo": "recoger", "aqui": True, "objeto": "el albarán del camión", "texto": "Recoge el albarán que ha quedado en la cuneta."},
                   D(("Aurelio", "El valle es de quien lo trabaja. Toma, y la escopeta te la quedas."),
                     ("Narrador", "En el albarán hay un nombre conocido: Belmonte.")),
                   {"tipo": "dar", "dinero": 300}],
         "recompensa": {"dinero": 1500, "chaleco": True}},
        {"id": "vo04", "titulo": "Reparto de la cooperativa", "capitulo": 25, "contacto": "La presidenta", "lugar": "vo_cooperativa", "requiere": ["m01"],
         "resumen": "Trabajo honrado: llevar pedidos por el pueblo.",
         "pasos": [D(("La presidenta", "Tres cajas: una al Mesón, otra a la Posada y otra a la Despensa de la Parroquia, que esa va de regalo.")),
                   {"tipo": "ir", "lugar": "vo_meson", "texto": "Lleva la primera caja al Mesón del Lagar."},
                   {"tipo": "ir", "lugar": "vo_hostal", "texto": "Lleva la segunda a la Posada del Olmo."},
                   {"tipo": "ir", "lugar": "vo_parroquia", "limite": 150, "texto": "Y la tercera a la Despensa de la Parroquia, antes de que cierren."},
                   D(("Narrador", "El cura te da las gracias y una bendición que no has pedido."))],
         "recompensa": {"dinero": 280}},
    ]
    return {
        "info": {"nombre": "Valdeolmos", "autor": "Puerto Bravo", "version": "1.0",
                 "descripcion": "Un pueblo de viñas al norte de Puerto Bravo: tres misiones sobre un fraude de vino, un encargo honrado, una carrera de tractores, pesca de río, una escopeta de caza, una hoz, un tractor con remolque, un todoterreno de campo y un personaje."},
        "capitulos": {"24": "Valdeolmos", "25": "Valdeolmos: vida honrada"},
        "mapas": [mapa],
        "lugares": [{"id": "pb_salida_valdeolmos", "mapa": "puerto_bravo", "nombre": "Salida noreste, carretera de Valdeolmos", "tipo": "salida", "bloque": [9, 6], "lado": "E", "pos": 36,
                     "a_mapa": "valdeolmos", "a_lugar": "vo_salida", "km": 31, "horas": 0.8, "desc": "La carretera que sube entre viñedos hasta Valdeolmos."}],
        "misiones": misiones,
        "armas": [clon(ARMAS, escopeta, id="vo_escopeta", nombre="Escopeta de caza paralela", dano=62, alcance=22, cadencia=0.9, precio=950, desc="Dos cañones, largo alcance para ser escopeta y un retroceso que se nota."),
                  clon(ARMAS, cuerpo, id="vo_hoz", nombre="Hoz de vendimia", dano=26, alcance=2.4, cadencia=0.5, precio=30, desc="Corta racimos y lo que haga falta.")],
        "vehiculos": [clon(VEHICULOS, tractor, id="vo_remolque", nombre="Tractor con remolque", vel_max=13, salud=260, valor=900, precio=6000, desc="Lento como una procesión y duro como una piedra."),
                      clon(VEHICULOS, todo, id="vo_campero", nombre="Todoterreno campero", vel_max=26, salud=200, valor=1200, precio=7800, desc="Un todoterreno viejo de los que arrancan siempre.")],
        "carreras": [{"id": "vo_c1", "nombre": "Carrera de las viñas", "mapa": "valdeolmos", "premio": 300, "tiempo": 85, "puntos": [[0, 1], [3, 1], [3, 3], [0, 3], [0, 1]]}],
        "comidas": [{"nombre": "Cordero asado", "precio": 16, "salud": 50}, {"nombre": "Vaso de mosto", "precio": 2, "salud": 6}],
        "peces": [{"nombre": "una trucha del Olmedilla", "valor": 30, "peso": 14}, {"nombre": "un barbo", "valor": 18, "peso": 20}],
        "personajes": [{"id": "vo_ines", "nombre": "Inés", "apellido": "Olmedo", "conduccion": 2, "resistencia": 4, "salud_max": 110, "ciudadania": 35, "arma": "vo_hoz", "botiquines": 1,
                        "desc": "Hija de viñadores, acostumbrada a trabajar de sol a sol. Empieza con resistencia al nivel cuatro, algo más de salud, una hoz y buen nombre entre los vecinos."}],
    }


# ============================================================ Motor y asfalto
def motor():
    dep = "deportivo" if "deportivo" in VEHICULOS else "utilitario"
    moto = "moto" if "moto" in VEHICULOS else "utilitario"
    return {
        "info": {"nombre": "Motor y asfalto", "autor": "Puerto Bravo", "version": "1.0",
                 "descripcion": "Para quien solo quiere conducir: tres coches y una moto nuevos, un concesionario y un taller de preparación, tres carreras por Puerto Bravo, un piloto para elegir y dos misiones al volante."},
        "capitulos": {"26": "Motor y asfalto"},
        "lugares": [
            {"id": "ma_escuderia", "mapa": "puerto_bravo", "nombre": "Escudería Viento Sur", "tipo": "concesionario", "bloque": [8, 5], "lado": "S", "pos": 20, "modelos": ["ma_gt", "ma_rally", "ma_clasico", "ma_cafe"], "desc": "Coches preparados para correr. Se oye un motor al ralentí en el taller del fondo."},
            {"id": "ma_boxes", "mapa": "puerto_bravo", "nombre": "Boxes de la Escudería", "tipo": "taller", "bloque": [8, 5], "lado": "E", "pos": 36, "desc": "Reparan y pintan en lo que tardas en tomarte un café."},
            {"id": "ma_parrilla", "mapa": "puerto_bravo", "nombre": "Parrilla de salida de la Ronda", "tipo": "carrera", "bloque": [8, 6], "lado": "S", "pos": 36, "desc": "Aquí se queda para las carreras de la Escudería."},
            {"id": "ma_autoescuela", "mapa": "puerto_bravo", "nombre": "Escuela de Pilotos Viento Sur", "tipo": "academia", "bloque": [8, 6], "lado": "O", "pos": 36, "cursos": ["conduccion"], "desc": "Cursos de conducción deportiva en circuito cerrado."},
        ],
        "vehiculos": [
            clon(VEHICULOS, dep, id="ma_gt", nombre="Viento GT", vel_max=46, acel=11.5, freno=20, salud=110, tono=1.3, valor=9000, precio=78000, desc="El coche más rápido de la comarca. Frena tarde y acelera pronto."),
            clon(VEHICULOS, "utilitario", id="ma_rally", nombre="Brisa Rally", vel_max=34, acel=10.0, freno=19, salud=150, tono=1.35, valor=2500, precio=16500, desc="Un utilitario preparado: no corre tanto, pero sale de las curvas como un tiro."),
            clon(VEHICULOS, "utilitario", id="ma_clasico", nombre="Clásico Seiscientos Especial", vel_max=22, acel=5.0, freno=11, salud=90, tono=1.5, valor=3000, precio=9000, desc="Pequeño, ruidoso y con más encanto que caballos."),
            clon(VEHICULOS, moto, id="ma_cafe", nombre="Moto Café Racer", vel_max=40, acel=12.0, salud=65, valor=2200, precio=14000, desc="Una moto ligera y rapidísima. Un golpe y al suelo."),
        ],
        "carreras": [
            {"id": "ma_c1", "nombre": "Gran Premio de la Ronda", "mapa": "puerto_bravo", "premio": 900, "tiempo": 110, "puntos": [[8, 6], [10, 6], [10, 2], [6, 2], [6, 6], [8, 6]]},
            {"id": "ma_c2", "nombre": "Contrarreloj del Paseo Marítimo", "mapa": "puerto_bravo", "premio": 600, "tiempo": 70, "puntos": [[8, 6], [8, 1], [1, 1], [1, 3]]},
            {"id": "ma_c3", "nombre": "Vuelta larga a Puerto Bravo", "mapa": "puerto_bravo", "premio": 1500, "tiempo": 170, "puntos": [[8, 6], [10, 6], [10, 1], [0, 1], [0, 8], [8, 8], [8, 6]]},
        ],
        "personajes": [{"id": "ma_leo", "nombre": "Leo", "apellido": "Carrasco", "conduccion": 6, "dinero": 100, "ganzuas": 1, "botiquines": 1,
                        "desc": "Probador de la Escudería Viento Sur hasta que estrelló el coche del jefe. Empieza con la conducción al nivel seis: nadie conduce mejor. A cambio, casi no tiene dinero."}],
        "misiones": [
            {"id": "ma01", "titulo": "Coche de pruebas", "capitulo": 26, "contacto": "Paula", "lugar": "ma_escuderia", "requiere": ["m01"],
             "resumen": "La jefa de la Escudería Viento Sur busca un probador.",
             "pasos": [D(("Paula", "¿Tú eres Dani? Dicen que conduces sin romper nada. Tengo un Brisa Rally recién montado y un cliente esperando en el concesionario Autos Platino."),
                         ("Paula", "Llévaselo en tres minutos y sin un rasguño. Si llega bien, hay más trabajo.")),
                       {"tipo": "robar", "lugar": "ma_boxes", "modelo": "ma_rally", "nombre": "el Brisa Rally de pruebas", "abierto": True, "texto": "Recoge el Brisa Rally junto a los Boxes de la Escudería."},
                       {"tipo": "entregar", "lugar": "concesionario", "salud_min": 85, "limite": 180, "texto": "Llévalo a Autos Platino en tres minutos y casi intacto."},
                       D(("Narrador", "El cliente da una vuelta alrededor del coche, pasa un dedo por el capó y asiente."))],
             "recompensa": {"dinero": 500}},
            {"id": "ma02", "titulo": "El que no paga", "capitulo": 26, "contacto": "Paula", "lugar": "ma_escuderia", "requiere": ["ma01"],
             "resumen": "Un cliente se ha llevado un Viento GT sin pagar.",
             "pasos": [D(("Paula", "El del Viento GT se ha ido sin pagar. Sale por la carretera del norte. No quiero el coche roto, pero prefiero roto a perdido.")),
                       {"tipo": "perseguir", "lugar": "salida_norte", "modelo": "ma_gt", "nombre": "el Viento GT robado", "salud": 180, "limite": 240, "texto": "Alcanza el Viento GT y páralo a golpes antes de cuatro minutos."},
                       {"tipo": "ir", "lugar": "ma_escuderia", "texto": "Vuelve a la Escudería Viento Sur."},
                       D(("Paula", "Chapa y pintura, tres días. Mejor eso que nada. Toma lo tuyo."))],
             "recompensa": {"dinero": 1200}},
        ],
    }


def escribir(nombre, crudo):
    from editor import modelo
    mod = modelo.Mod.desde_crudo(crudo)
    ruta = os.path.join(rutas.carpeta_data("mods"), nombre)
    if os.path.exists(ruta):
        os.remove(ruta)                              # para que el revisor no lo vea como «otro mod» con los mismos identificadores
    errores, avisos = modelo.comprobar(mod, modelo.Catalogo())
    mod.guardar(ruta, protegido=False)          # en el código fuente quedan legibles; compilar.bat los protege
    return ruta, errores, avisos


MODS = (("costa_dorada.json", costa_dorada), ("oficios_y_recados.json", oficios), ("valdeolmos.json", valdeolmos), ("motor_y_asfalto.json", motor))

if __name__ == "__main__":
    mal = False
    for nombre, hacer in MODS:
        ruta, errores, avisos = escribir(nombre, hacer())
        print(f"{nombre}: {len(errores)} errores, {len(avisos)} avisos")
        for e in errores:
            print("   ERROR", e)
            mal = True
        for a in avisos:
            print("   aviso", a)
    sys.exit(1 if mal else 0)
