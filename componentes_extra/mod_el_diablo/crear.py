"""Escribe el mod El Diablo en esta misma carpeta y lo comprueba con el mismo revisor del editor.

    .venv\\Scripts\\python.exe componentes_extra\\mod_el_diablo\\crear.py

Desde la 1.7.4 El Diablo viene con el juego, en data\\mods\\el_diablo.json, con sus voces en español y en inglés en
data\\voces. Para la 1.7.3 se descarga como componente (componente.json, en esta carpeta), que coge el mod, las voces
y las traducciones de esos mismos sitios.

Una agencia de sicarios en la trastienda de un bar del puerto de Puerto Bravo, El Purgatorio, y el hombre que la
lleva: El Diablo. No avisa ni negocia: solo da nombres. Trae cuatro misiones de historia, todas de muertes y
persecuciones (sin escarmientos ni avisos), cinco tipos de contrato nuevos para los tablones de encargos y un
revólver silenciado. Todo es inventado.

Los contratos se suman a los de serie y, desde la 1.7.4, solo cuelgan del tablón de El Purgatorio (campo tablones de
cada tipo de contrato). La 1.7.3 no conoce ese campo y los cuelga en todos los tablones. Ninguno usa la situación
«intimidar».

Sale con código 1 si el revisor encuentra errores; los avisos se escriben, pero no cuentan como fallo.
"""
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))

import crear_mods_ejemplo as CME          # noqa: E402  (las tablas del juego y las ayudas de los mods de ejemplo)

ARMAS = CME.ARMAS
clon, primero, D = CME.clon, CME.primero, CME.D

ARCHIVO = os.path.join(RAIZ, "data", "mods", "el_diablo.json")
AGENCIA = "di_agencia"
DIABLO = "El Diablo"


def _misiones():
    return [
        {"id": "di01", "titulo": "El primer nombre", "capitulo": 61, "contacto": DIABLO, "lugar": AGENCIA, "requiere": ["m01"],
         "resumen": "En la trastienda de El Purgatorio, un hombre de traje rojo oscuro dice que tiene trabajo para gente que no hace preguntas.",
         "recompensa": {"dinero": 900},
         "pasos": [
             D([DIABLO, "Siéntate. Me llaman El Diablo. No por lo que hago: porque nunca aviso."],
               ["Dani", "¿Y qué haces?"],
               [DIABLO, "Doy nombres. Tú los tachas. Sin cartas, sin amenazas, sin segundas oportunidades."],
               [DIABLO, "El primero: Tano el Gordo. Bebe en el Bar La Gaviota con dos gorilas. Cuando salgas de allí, que no quede ninguno de pie."]),
             {"tipo": "eliminar", "lugar": "bar_gaviota", "texto": "Ve al Bar La Gaviota y acaba con Tano el Gordo y sus dos guardaespaldas.",
              "enemigos": [{"n": 1, "tipo": "Tano el Gordo", "arma": "pistola", "salud": 110},
                           {"n": 2, "tipo": "Gorila de Tano", "arma": "pistola", "salud": 70}]},
             {"tipo": "ir", "lugar": AGENCIA, "texto": "Vuelve a El Purgatorio a cobrar."},
             D([DIABLO, "Ni una palabra de más, ni un tiro de menos. Me gusta."],
               [DIABLO, "Vuelve cuando quieras otro nombre. Y mira el tablón de la barra: ahí cuelgo los encargos pequeños."]),
         ]},
        {"id": "di02", "titulo": "Pies ligeros", "capitulo": 61, "contacto": DIABLO, "lugar": AGENCIA, "requiere": ["di01"],
         "resumen": "Alguien ha avisado a los hermanos Lobo de que El Diablo tiene su nombre. Se van de la ciudad.",
         "recompensa": {"dinero": 1300},
         "pasos": [
             D([DIABLO, "Los hermanos Lobo me deben una cosa que no se devuelve con dinero. Y alguien les ha ido con el cuento."],
               [DIABLO, "Están cargando un sedán en el Desguace Hierro Viejo. Que no salgan de Puerto Bravo."]),
             # un sedán, no un deportivo: el deportivo huye a 20 m/s en normal y con un vehículo lento no hay manera
             {"tipo": "perseguir", "lugar": "desguace", "modelo": "sedan", "salud": 170, "limite": 300, "nombre": "el sedán de los hermanos Lobo",
              "texto": "Alcanza y destroza el sedán de los hermanos Lobo antes de cinco minutos. Fíjalo con la Q."},
             {"tipo": "ir", "lugar": AGENCIA, "texto": "Vuelve a El Purgatorio."},
             D([DIABLO, "Los Lobo ya no corren. Bien."],
               [DIABLO, "Lo que me preocupa es quién les avisó. Eso lo sabremos pronto."]),
         ]},
        # en el Casino Belmonte y no en el Club Paraíso: el club solo existe con el contenido para adultos
        {"id": "di03", "titulo": "Todo al rojo", "capitulo": 61, "contacto": DIABLO, "lugar": AGENCIA, "requiere": ["di02"],
         "resumen": "El chivato que avisó a los Lobo es Rubén Saldaña, y se está jugando el dinero en el Casino Belmonte.",
         "recompensa": {"dinero": 1800},
         "pasos": [
             D([DIABLO, "Rubén Saldaña. Trabajaba para mí y vendía mis nombres a quien pagase más."],
               [DIABLO, "Está en el Casino Belmonte con cuatro matones de alquiler. Entra por la puerta principal. Que lo oigan."]),
             {"tipo": "ir", "lugar": "casino", "radio": 9, "texto": "Ve al Casino Belmonte y llega hasta la puerta, a pie."},
             {"tipo": "eliminar", "lugar": "casino", "ya": True,
              "texto": "Empujas la puerta y las ruletas siguen girando. Saldaña te ve y grita. Acaba con todos.",
              "enemigos": [{"n": 1, "tipo": "Rubén Saldaña", "arma": "pistola", "salud": 110},
                           {"n": 2, "tipo": "Matón de alquiler", "arma": "pistola", "salud": 75},
                           {"n": 2, "tipo": "Matón de alquiler", "arma": "subfusil", "salud": 75}]},
             {"tipo": "ir", "lugar": AGENCIA, "texto": "Vuelve a El Purgatorio."},
             D([DIABLO, "Saldaña no vendía mis nombres por gusto. Se los compraban Los Arcángeles."],
               [DIABLO, "Otra agencia. Y ahora saben que existes."]),
         ]},
        {"id": "di04", "titulo": "El Diablo no perdona", "capitulo": 61, "contacto": DIABLO, "lugar": AGENCIA, "requiere": ["di03"],
         "resumen": "Los Arcángeles vienen a El Purgatorio a por El Diablo, y a por ti.",
         "final_titulo": "El Diablo: una sola agencia en Puerto Bravo",
         "final": "Esa noche El Diablo cierra la persiana de El Purgatorio y sirve dos copas. Desde mañana, en Puerto Bravo solo hay una lista "
                  "de nombres, y la llevas tú en el bolsillo.",
         "recompensa": {"dinero": 3000, "arma": "di_cuerno", "balas": 18},
         "pasos": [
             D([DIABLO, "Ya vienen. Un coche en la puerta y otro dando la vuelta a la manzana."],
               [DIABLO, "Los Arcángeles no avisan tampoco. Eso es lo único que tenemos en común."]),
             {"tipo": "eliminar", "lugar": AGENCIA, "ya": True,
              "texto": "Los Arcángeles entran en El Purgatorio y llegan más en coche. Que no quede ninguno.",
              "enemigos": [{"n": 3, "tipo": "Arcángel", "arma": "pistola", "salud": 80},
                           {"n": 1, "tipo": "Arcángel", "arma": "escopeta", "salud": 85},
                           {"n": 2, "clase": "escolta_motorizada"}]},
             D([DIABLO, "Su jefe, Gabriel, se escapa en el sedán blanco. Ese es el último nombre de la lista."]),
             {"tipo": "perseguir", "lugar": AGENCIA, "modelo": "sedan", "salud": 260, "limite": 300, "nombre": "el sedán blanco de Gabriel",
              "texto": "Alcanza y destroza el sedán blanco de Gabriel antes de cinco minutos."},
             {"tipo": "ir", "lugar": AGENCIA, "texto": "Vuelve a El Purgatorio."},
             D([DIABLO, "Gabriel quería mi trastienda. Ahora no le hace falta nada."],
               [DIABLO, "Toma. El Cuerno del Diablo. No hace ruido, y tú tampoco lo harás."]),
         ]},
    ]


def _contratos():
    """Cinco tipos de contrato para los tablones: matar y perseguir, nada de escarmientos."""
    return [
        {"id": "di_sin_aviso", "nombre": "El Diablo: sin aviso", "situacion": "eliminar", "tablones": [AGENCIA], "peso": 2, "paga": 1100, "paga_escolta": 450,
         "objetivo": "objetivo_contrato", "escolta": "guardaespaldas",
         "resumen": "{quien} está en {lugar} con {n} guardaespaldas, y El Diablo no quiere que vea amanecer. Ni avisos ni conversaciones."},
        {"id": "di_caceria", "nombre": "El Diablo: cacería", "situacion": "huye", "tablones": [AGENCIA], "peso": 2, "desde": 1, "paga": 1300, "paga_escolta": 200,
         "salud_vehiculo": 170, "modelos": ["sedan", "todoterreno", "utilitario"],
         "resumen": "{quien} sabe que El Diablo tiene su nombre y sale de {lugar} en un {modelo}. No le dejes llegar a la autovía."},
        {"id": "di_puerta", "nombre": "El Diablo: puerta a puerta", "situacion": "local", "tablones": [AGENCIA], "peso": 2, "desde": 1, "paga": 1200, "paga_escolta": 420,
         "objetivo": "objetivo_contrato", "escolta": "maton", "locales": ["club", "casino", "bar", "taberna", "hotel"],
         "resumen": "{quien} se ha encerrado en {lugar} con {n} de los suyos, creyendo que ahí dentro no entra nadie. El Diablo dice que entres."},
        {"id": "di_rastro", "nombre": "El Diablo: el rastro", "situacion": "seguir", "tablones": [AGENCIA], "peso": 2, "desde": 2, "paga": 1400, "paga_escolta": 350,
         "objetivo": "objetivo_contrato", "escolta": "guardaespaldas",
         "resumen": "Nadie sabe dónde duerme {quien}, pero su recadero sale de {lugar}. Síguele, y cuando llegue, termina el trabajo."},
        {"id": "di_convoy", "nombre": "El Diablo: el convoy", "situacion": "escolta_vehiculo", "tablones": [AGENCIA], "peso": 2, "desde": 3, "paga": 1600, "paga_escolta": 480,
         "objetivo": "objetivo_contrato", "escolta": "guardaespaldas", "refuerzo": "escolta_motorizada",
         "resumen": "{quien} va a {lugar} con {n} de escolta, y más gente suya llegará en coche en cuanto suene el primer tiro. El Diablo paga por todos."},
    ]


def el_diablo():
    revolver = "revolver" if "revolver" in ARMAS else primero(ARMAS, lambda a: a["tipo"] == "fuego")
    return {
        "info": {"nombre": "El Diablo", "autor": "patricus", "version": "1.0",
                 "descripcion": "Una agencia de sicarios en la trastienda de un bar del puerto, El Purgatorio, y el hombre que la lleva: El Diablo. "
                                "Él no avisa ni negocia: solo da nombres. Cuatro misiones de muertes y persecuciones, cinco contratos nuevos en los "
                                "tablones de encargos y un revólver silenciado, el Cuerno del Diablo."},
        "capitulos": {"61": "El Diablo"},
        "lugares": [
            {"id": AGENCIA, "mapa": "puerto_bravo", "tipo": "taberna", "bloque": [7, 4], "lado": "S", "pos": 50, "sonido": "lugar_bar",
             "nombre": "El Purgatorio, la agencia de El Diablo",
             "desc": "Un bar sin letrero con la persiana a medio bajar. En la trastienda, detrás de una cortina roja, El Diablo reparte nombres. "
                     "En el tablón de la barra cuelgan sus contratos."},
        ],
        "armas": [clon(ARMAS, revolver, id="di_cuerno", nombre="Cuerno del Diablo", dano=50, alcance=38, cadencia=0.8, precision=0.93, cargador=6,
                       sonido="disparo_silenciado", ruido=0, precio=4800, balas=12, precio_balas=90,
                       desc="Un revólver negro con silenciador y la culata de hueso. Pega como un revólver y suena como una puerta que se cierra.")],
        "contratos": _contratos(),
        "misiones": _misiones(),
    }


def escribir(crudo, ruta=ARCHIVO):
    """Comprueba el mod con el revisor del editor y lo guarda legible. Devuelve (errores, avisos)."""
    from editor import modelo
    mod = modelo.Mod.desde_crudo(crudo)
    if os.path.exists(ruta):
        os.remove(ruta)                              # para que el revisor no lo vea como «otro mod» con los mismos identificadores
    errores, avisos = modelo.comprobar(mod, modelo.Catalogo())
    mod.guardar(ruta, protegido=False)
    return errores, avisos


if __name__ == "__main__":
    errores, avisos = escribir(el_diablo())
    print(f"{os.path.relpath(ARCHIVO, RAIZ)}: {len(errores)} errores, {len(avisos)} avisos")
    for e in errores:
        print("   ERROR", e)
    for a in avisos:
        print("   aviso", a)
    sys.exit(1 if errores else 0)
