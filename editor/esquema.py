"""Esquema de todo lo que puede contener un mod.

Cada sección del editor y cada formulario se generan a partir de estas definiciones, así que
añadir aquí un campo lo añade al editor, a la validación y a la ayuda de Ctrl+H.

Tipos de campo:
  texto, largo, entero, decimal, si_no, opcion (lista fija), ref (identificador de otra cosa),
  refs (varios identificadores), textos (una línea por elemento), par (dos números),
  lista (elementos con su propio formulario) y objeto (un formulario dentro de otro).
"""

TIPOS_LUGAR = [
    ("monumento", "Monumento o sitio de interés, solo descripción"), ("casa", "Vivienda que se puede comprar"),
    ("negocio", "Negocio que da ingresos"), ("armeria", "Armería"), ("tienda", "Tienda"), ("farmacia", "Farmacia"),
    ("comida", "Bar o restaurante"), ("pizzeria", "Pizzería con trabajo de repartidor"), ("hospital", "Hospital"),
    ("comisaria", "Comisaría"), ("taller", "Taller de reparación y pintura"), ("desguace", "Desguace"),
    ("casino", "Casino"), ("bar", "Bar de Encarna"), ("taberna", "Taberna con dados, guardaespaldas y contratos"),
    ("taxi", "Parada de taxis"), ("carrera", "Salida de carreras"), ("periodico", "Periódico"), ("banco", "Banco"),
    ("loteria", "Lotería"), ("empenos", "Casa de empeños"), ("pescaderia", "Lonja o pescadería"),
    ("gimnasio", "Gimnasio"), ("ropa", "Tienda de ropa"), ("cine", "Cine"), ("hotel", "Hotel"),
    ("concesionario", "Concesionario de vehículos"), ("nautica", "Náutica, venta de barcos"),
    ("estacion", "Estación de autobuses"), ("salida", "Salida por carretera a otra localidad"),
    ("embarcadero", "Embarcadero, de tierra al mar"), ("muelle", "Muelle, del mar a tierra"),
    ("helipuerto", "Helipuerto"), ("tranvia", "Parada de tranvía, para moverse dentro de la ciudad"),
    ("tren", "Estación de tren, a otras localidades por tierra"), ("aeropuerto", "Aeropuerto: vuelos largos, avionetas y helicópteros"), ("pesca", "Punto de pesca"), ("protectora", "Protectora de animales"),
    ("feria", "Feria o recreativos"), ("tesoro", "Zona de búsqueda de tesoros"),
    ("empleo", "Oficina de empleo"), ("academia", "Academia de cursos"), ("ong", "Comedor social u organización benéfica"),
    ("club", "Club nocturno, contenido para adultos"), ("proveedor", "Proveedor de sustancias, contenido para adultos"),
]
TIPOS_PASO = [
    ("dialogo", "Diálogo: una conversación"), ("ir", "Ir a un lugar"), ("dar", "Dar algo al jugador"),
    ("robar", "Conseguir un vehículo que aparece junto a un lugar"), ("entregar", "Entregar ese vehículo en un lugar"),
    ("eliminar", "Eliminar a un grupo de enemigos"), ("recoger", "Recoger un objeto"),
    ("policia", "Poner nivel de búsqueda y despistar a la policía"), ("perseguir", "Perseguir y destruir un vehículo que huye"),
    ("seguir", "Seguir a alguien a pie sin que te descubra"), ("escoltar", "Acompañar a alguien hasta un lugar"),
    ("sigilo", "Llegar a un punto vigilado sin que te oigan"), ("ruta", "Pasar por varios lugares, en orden"),
    ("vigilar", "Vigilar un lugar un rato sin que te vean"), ("carrera", "Carrera en vehículo contra rivales"),
    ("decision", "Una decisión del jugador, con consecuencias"),
]
LADOS = [("N", "Fachada norte de la manzana"), ("S", "Fachada sur"), ("E", "Fachada este"), ("O", "Fachada oeste")]
BLOQUES = [("pared", "Edificios, no se puede pisar"), ("plaza", "Plaza"), ("hierba", "Césped o campo"), ("arena", "Arena"), ("muelle", "Muelle de tablones")]
TRABAJOS = [("taxi", "Taxi"), ("ambulancia", "Ambulancia"), ("autobus", "Autobús"), ("vigilante", "Vigilante"), ("camion", "Transporte entre localidades"),
            ("helados", "Heladero"), ("mensajeria", "Mensajería del mar"), ("bomberos", "Bombero"), ("grua", "Grúa"), ("paqueteria", "Mensajero")]


def c(k, e, t="texto", ayuda="", **kw):
    d = {"k": k, "e": e, "t": t, "ayuda": ayuda}
    d.update(kw)
    return d


def _es(*tipos):
    return lambda d: d.get("tipo") in tipos


ESQUEMAS = {
    "info": {"titulo": "Datos del mod", "campos": [
        c("nombre", "Nombre del mod", req=True, ayuda="El nombre con el que se conoce tu mod."),
        c("autor", "Autor"),
        c("version", "Versión", defecto="1.0"),
        c("descripcion", "Descripción", "largo", "Qué añade o cambia este mod."),
    ]},
    "lugar": {"titulo": "Lugar", "resumen": lambda d: f"{d.get('nombre', '?')} ({d.get('tipo', '?')}, {d.get('mapa', 'puerto_bravo')})", "campos": [
        c("id", "Identificador", req=True, ayuda="Nombre interno, único, sin espacios ni tildes. Si coincide con un lugar del juego, lo sustituye."),
        c("nombre", "Nombre", req=True, ayuda="Como lo dirá el juego."),
        c("tipo", "Tipo de lugar", "opcion", "Decide qué se puede hacer en él. Al cambiarlo aparecen los campos propios de ese tipo.", ops=TIPOS_LUGAR, req=True, recarga=True, defecto="monumento"),
        c("mapa", "Localidad", "ref", "En qué mapa está.", ref="mapa", defecto="puerto_bravo", recarga=True),
        c("bloque", "Manzana", "par", "Número de avenida desde el oeste y número de calle desde el sur, empezando en cero. Déjalo vacío en el mar.", etiquetas=("Manzana: avenida", "Manzana: calle")),
        c("lado", "Fachada", "opcion", "En qué lado de la manzana está la puerta. Déjalo sin valor si usas una posición interior.", ops=LADOS),
        c("pos", "Posición en la fachada", "entero", "Metros desde la esquina oeste o sur de la manzana, de 0 a 72.", minimo=0, maximo=72),
        c("orden", "Orden en la línea de tranvía", "entero", "El tranvía recorre las paradas por este orden, de menor a mayor, y después de la última vuelve a la primera. "
          "Si lo dejas vacío en todas las paradas de la localidad, el juego las ordena dando la vuelta a la ciudad.", si=_es("tranvia"), minimo=1),
        c("xy", "Posición interior o en el mar", "par", "En plazas, parques, playas y muelles: metros dentro de la manzana. En el mar: coordenadas absolutas.", etiquetas=("Posición: metros al este", "Posición: metros al norte"), decimal=True),
        c("desc", "Descripción", "largo", "Lo que dice el juego con la tecla N y en las listas."),
        c("sonido", "Sonido propio", "ref", "Sonido en bucle que emite. Sin valor, usa el de su tipo.", ref="sonido"),
        c("adultos", "Solo con el contenido para adultos", "si_no", "Si se marca, el lugar solo existe con esa opción activada."),
        c("requiere", "Misión necesaria para que abra", "ref", ref="mision"),
        c("vehiculo", "Vehículo siempre aparcado en la puerta", "ref", ref="modelo"),
        c("precio", "Precio", "entero", "De compra en casas y negocios; del billete o del vuelo en estaciones y helipuertos.", si=_es("casa", "negocio", "estacion", "helipuerto")),
        c("garaje", "Plazas de garaje", "entero", si=_es("casa")),
        c("ingresos", "Ingresos diarios", "entero", si=_es("negocio")),
        c("precio_noche", "Precio por noche", "entero", si=_es("hotel")),
        c("descuento", "Factor de precio", "decimal", "Por ejemplo 0,7 para un 30 por ciento de descuento.", si=_es("armeria")),
        c("caro", "Precios triples", "si_no", si=_es("comida")),
        c("a_mapa", "Lleva a la localidad", "ref", ref="mapa", si=_es("salida", "embarcadero", "muelle")),
        c("a_lugar", "Lugar de llegada", "ref", "El lugar del otro mapa en el que apareces.", ref="lugar", si=_es("salida", "embarcadero", "muelle")),
        c("km", "Kilómetros de carretera", "entero", si=_es("salida")),
        c("horas", "Horas de viaje", "decimal", si=_es("salida")),
        c("embarcadero", "Embarcadero donde se amarran los barcos comprados", "ref", ref="lugar", si=_es("nautica")),
        c("modelos", "Modelos a la venta", "refs", "Sin marcar ninguno, vende todos los que tienen precio.", ref="modelo", si=_es("concesionario")),
        c("cursos", "Cursos que se imparten", "refs", "Sin marcar ninguno, se imparten los cuatro.", ref="habilidad", si=_es("academia")),
        c("factor", "Factores de precio por sustancia", "lista", "Por debajo de 1, esa sustancia es barata aquí.", sub="factor", como_dicc=("clave", "valor"), si=_es("proveedor")),
    ]},
    "factor": {"titulo": "Factor de precio", "resumen": lambda d: f"{d.get('clave', '?')}: {d.get('valor', '?')}", "campos": [
        c("clave", "Sustancia", "ref", ref="sustancia", req=True), c("valor", "Factor", "decimal", req=True, defecto=1.0)]},
    "mision": {"titulo": "Misión", "resumen": lambda d: f"{d.get('id', '?')}: {d.get('titulo', '?')}, {len(d.get('pasos', []))} pasos", "campos": [
        c("id", "Identificador", req=True, ayuda="Único. Otras misiones lo usan para exigir que esta esté completada."),
        c("titulo", "Título", req=True),
        c("capitulo", "Número de capítulo", "entero", defecto=5),
        c("contacto", "Quién la encarga"),
        c("lugar", "Lugar donde empieza", "ref", ref="lugar", req=True),
        c("requiere", "Misiones que hay que completar antes", "refs", ref="mision"),
        c("resumen", "Resumen para el móvil", "largo"),
        c("tutorial", "Es un tutorial: mientras dura, la policía no acude", "si_no"),
        c("si_clave", "Solo aparece si se tomó la decisión", ayuda="Vacío, la misión aparece siempre. Si escribes el nombre de una decisión, solo aparece cuando se eligió la opción que indiques debajo. Sirve para que la historia se bifurque."),
        c("si_opcion", "Número de la opción elegida", "entero", "La primera opción es la 1.", minimo=1, maximo=4, defecto=1),
        c("final_titulo", "Nombre de este final", ayuda="Cómo se apunta en el diario. Por ejemplo: Final honrado. Si lo dejas vacío, se usa el título de la misión."),
        c("final", "Texto del final de la historia", "largo", "Si lo rellenas, al completar esta misión se dice este texto como final y queda apuntado en el diario. Con varias misiones así, cada una tras una decisión distinta, la historia tiene varios finales."),
        c("adultos", "Solo con el contenido para adultos", "si_no"),
        c("pasos", "Pasos", "lista", "Se cumplen en orden.", sub="paso", req=True),
        c("recompensa", "Recompensa", "objeto", sub="recompensa"),
    ]},
    "paso": {"titulo": "Paso de la misión", "resumen": lambda d: f"{d.get('tipo', '?')}: " + (d.get("texto") or d.get("lugar") or (f"{len(d.get('lineas', []))} frases" if d.get("tipo") == "dialogo" else "")), "campos": [
        c("tipo", "Tipo de paso", "opcion", "Al cambiarlo aparecen los campos propios de ese tipo.", ops=TIPOS_PASO, req=True, recarga=True, defecto="ir"),
        c("texto", "Texto que se dice al empezar el paso", "largo", si=lambda d: d.get("tipo") not in ("dialogo", "dar", "decision")),
        c("clave", "Nombre de la decisión", ayuda="Una palabra que la identifica, sin espacios: concejal, traicion. Con ella, otras misiones y otros pasos pueden depender de lo que se eligió.", si=_es("decision")),
        c("pregunta", "Pregunta que se le hace al jugador", "largo", si=_es("decision")),
        c("opciones", "Opciones entre las que elige", "lista", "De dos a cuatro. Cada una puede dar o quitar dinero, fama y ánimo, y cambiar cómo te llevas con una banda.", sub="opcion_decision", si=_es("decision")),
        c("si_clave", "Solo si se tomó la decisión", ayuda="Vacío, el paso vale siempre. Si escribes el nombre de una decisión, este paso solo se juega cuando se eligió la opción que indiques debajo.",
          si=lambda d: d.get("tipo") != "decision"),
        c("si_opcion", "Número de la opción elegida", "entero", "La primera opción es la 1.", si=lambda d: d.get("tipo") != "decision" and d.get("si_clave"), minimo=1, maximo=4, defecto=1),
        c("lineas", "Frases del diálogo", "lista", sub="linea", como_pares=("quien", "texto"), si=_es("dialogo")),
        c("lugar", "Lugar", "ref", ref="lugar", si=_es("ir", "robar", "entregar", "eliminar", "recoger", "perseguir", "seguir", "escoltar", "sigilo", "vigilar", "carrera")),
        c("limite", "Tiempo límite en segundos", "entero", "Vacío, sin límite.", si=lambda d: d.get("tipo") not in ("dialogo", "dar", "decision")),
        c("radio", "Distancia a la que cuenta como llegado", "entero", "En vigilar, a cuántos metros del lugar hay que quedarse; si lo dejas vacío, 25.", si=_es("ir", "vigilar")),
        c("segundos", "Cuántos segundos hay que vigilar", "entero", "Durante ese tiempo sale alguien a dar una vuelta cada poco: el jugador tiene que quedarse quieto o agachado.", si=_es("vigilar"), minimo=15, maximo=300, defecto=45),
        c("resultado", "Qué descubre al terminar de vigilar", "largo", "Se dice cuando acaba el tiempo. Por ejemplo: Han entrado tres hombres con maletines.", si=_es("vigilar")),
        c("rivales", "Cuántos rivales", "entero", si=_es("carrera"), minimo=1, maximo=4, defecto=2),
        c("velocidad", "Velocidad de los rivales, en metros por segundo", "entero", "Diez es una carrera asequible; quince, difícil. En el campo Lugar va la salida, y en los lugares por los que hay que pasar, el recorrido: el último es la meta.", si=_es("carrera"), minimo=5, maximo=25, defecto=10),
        c("arma", "Arma que se entrega", "ref", ref="arma", si=_es("dar")),
        c("balas", "Balas", "entero", si=_es("dar")),
        c("balas_arma", "Solo munición para el arma", "ref", ref="arma", si=_es("dar")),
        c("dinero", "Dinero", "entero", si=_es("dar")),
        c("sustancia", "Sustancia, contenido para adultos", "ref", ref="sustancia", si=_es("dar")),
        c("cantidad", "Cantidad de sustancia", "entero", si=_es("dar")),
        c("modelo", "Modelo de vehículo", "ref", ref="modelo", si=_es("robar", "perseguir")),
        c("nombre", "Nombre del vehículo", si=_es("robar", "perseguir")),
        c("destino", "Lugar de destino", "ref", "En seguir, adonde va la persona. En escoltar, adonde hay que llevarla. En el campo Lugar va el punto de partida.", ref="lugar", si=_es("seguir", "escoltar")),
        c("persona", "Quién es", ayuda="Cómo llama el juego a la persona: el contable, tu prima Lola.", si=_es("seguir", "escoltar")),
        c("puntos", "Lugares por los que hay que pasar", "refs", "Se recorren en el orden en que aparecen. El tiempo límite, si lo pones, es para todo el recorrido.", ref="lugar", si=_es("ruta", "carrera")),
        c("guardias", "Cuántos vigilantes", "entero", "Pasean alrededor del lugar. Agachado se te oye a menos de tres metros; andando, a seis; corriendo, a once.", si=_es("sigilo"), minimo=1, maximo=8, defecto=3),
        c("abierto", "Está abierto, no hay que forzarlo", "si_no", si=_es("robar")),
        c("busqueda", "Nivel de búsqueda al subir", "entero", si=_es("robar"), minimo=0, maximo=5),
        c("salud_min", "Estado mínimo del vehículo, en porcentaje", "entero", si=_es("entregar"), minimo=0, maximo=100),
        c("enemigos", "Grupos de enemigos", "lista", sub="enemigo", si=_es("eliminar")),
        c("ya", "Aparecen al instante, sin esperar a que llegues", "si_no", si=_es("eliminar")),
        c("objeto", "Nombre del objeto", si=_es("recoger", "sigilo")),
        c("aqui", "Aparece donde esté el jugador", "si_no", si=_es("recoger")),
        c("nivel", "Nivel de búsqueda", "entero", si=_es("policia"), minimo=1, maximo=5, defecto=2),
        c("salud", "Resistencia del vehículo", "entero", si=_es("perseguir")),
    ]},
    "opcion_decision": {"titulo": "Opción de la decisión", "resumen": lambda d: d.get("texto", "")[:70], "campos": [
        c("texto", "Lo que elige el jugador", req=True),
        c("ayuda", "Explicación con F1", "largo"),
        c("dice", "Lo que se cuenta al elegirla", "largo"),
        c("dinero", "Dinero que da, o que quita si es negativo", "entero"),
        c("fama", "Fama que da o quita", "entero"),
        c("animo", "Ánimo que da o quita", "entero"),
        c("renta", "Dinero que deja cada medianoche, para siempre", "entero", "Una consecuencia que dura después de la misión y del final de la historia. Negativo, si cuesta dinero."),
        c("banda", "Banda con la que cambia la relación", ayuda="El nombre tal cual: Los Calaveras, Los Lagartos, Los Barrenos, Los Tiburones o Los Cuervos."),
        c("banda_puntos", "Puntos de relación con esa banda", "entero", "De menos cien a cien. Con treinta o más, esa banda te deja en paz; con menos treinta o menos, va a por ti.", minimo=-100, maximo=100)]},
    "linea": {"titulo": "Frase", "resumen": lambda d: f"{d.get('quien', '?')}: {d.get('texto', '')[:60]}", "campos": [
        c("quien", "Quién habla", req=True, defecto="Narrador", ayuda="Escribe Narrador para la narración."),
        c("texto", "Qué dice", "largo", req=True)]},
    "enemigo": {"titulo": "Grupo de enemigos", "resumen": lambda d: f"{d.get('n', 1)} × {d.get('tipo', '?')} con {d.get('arma', '?')}", "campos": [
        c("n", "Cuántos", "entero", req=True, defecto=1, minimo=1),
        c("tipo", "Nombre", req=True, defecto="Matón"),
        c("arma", "Arma", "ref", ref="arma", req=True, defecto="pistola"),
        c("salud", "Salud", "entero", defecto=60),
        c("inofensivo", "No ataca: es un muñeco de prácticas", "si_no")]},
    "recompensa": {"titulo": "Recompensa", "campos": [
        c("dinero", "Dinero", "entero"), c("arma", "Arma", "ref", ref="arma"), c("balas", "Balas", "entero"),
        c("chaleco", "Chaleco antibalas", "si_no"),
        c("barco", "Barco de regalo", "objeto", sub="barco_regalo"),
        c("afinidad", "Afinidad con personas, contenido para adultos", "lista", sub="afinidad", como_dicc=("clave", "valor"))]},
    "barco_regalo": {"titulo": "Barco de regalo", "campos": [
        c("modelo", "Modelo", "ref", ref="modelo", req=True), c("en", "Embarcadero donde queda amarrado", "ref", ref="lugar", req=True)]},
    "afinidad": {"titulo": "Afinidad", "resumen": lambda d: f"{d.get('clave', '?')}: {d.get('valor', '?')}", "campos": [
        c("clave", "Persona", "ref", ref="persona", req=True), c("valor", "Puntos", "entero", req=True, defecto=10)]},
    "arma": {"titulo": "Arma", "resumen": lambda d: f"{d.get('nombre', '?')} ({d.get('tipo', '?')})", "campos": [
        c("id", "Identificador", req=True), c("nombre", "Nombre", req=True),
        c("tipo", "Tipo", "opcion", ops=[("cuerpo", "Cuerpo a cuerpo"), ("fuego", "Arma de fuego"), ("explosivo", "Explosivo que se lanza")], req=True, recarga=True, defecto="fuego"),
        c("dano", "Daño", "entero", req=True, defecto=25), c("alcance", "Alcance en metros", "decimal", req=True, defecto=35),
        c("cadencia", "Segundos entre ataques", "decimal", req=True, defecto=0.4),
        c("precision", "Precisión, de 0 a 1", "decimal", req=True, defecto=0.85),
        c("cargador", "Balas por cargador", "entero", si=_es("fuego", "explosivo")),
        c("automatica", "Automática: dispara mientras se mantiene pulsado", "si_no", si=_es("fuego")),
        c("radio", "Radio de la explosión", "entero", si=_es("explosivo")),
        c("sonido", "Sonido", "ref", ref="sonido", req=True, defecto="disparo_pistola"),
        c("ruido", "Ruido, de 0 a 3", "entero", "Con 0 nadie oye el disparo.", minimo=0, maximo=3, defecto=2),
        c("precio", "Precio", "entero", defecto=0), c("balas", "Balas al comprar", "entero", si=_es("fuego", "explosivo")),
        c("precio_balas", "Precio de la munición", "entero", si=_es("fuego", "explosivo")),
        c("desc", "Descripción", "largo")]},
    "vehiculo": {"titulo": "Vehículo", "resumen": lambda d: f"{d.get('nombre', '?')} ({'barco' if d.get('barco') else 'aeronave' if d.get('vuela') else 'tierra'})", "campos": [
        c("id", "Identificador", req=True), c("nombre", "Nombre", req=True),
        c("vel_max", "Velocidad máxima, metros por segundo", "decimal", req=True, defecto=26),
        c("acel", "Aceleración", "decimal", req=True, defecto=7), c("freno", "Frenada", "decimal", req=True, defecto=14),
        c("salud", "Resistencia", "entero", req=True, defecto=120),
        c("motor", "Sonido del motor", "ref", ref="sonido", req=True, defecto="motor_coche"),
        c("tono", "Tono del motor", "decimal", "1 es normal; más alto suena más agudo.", req=True, defecto=1.0),
        c("valor", "Valor en el desguace", "entero", defecto=0), c("precio", "Precio en concesionario o náutica", "entero"),
        c("claxon", "Claxon", "ref", ref="sonido"), c("sirena", "Sirena", "ref", ref="sonido"),
        c("trabajo", "Trabajo con la tecla J", "opcion", ops=TRABAJOS),
        c("barco", "Es una embarcación", "si_no"), c("vuela", "Vuela", "si_no"),
        c("desc", "Descripción", "largo")]},
    "carrera": {"titulo": "Carrera", "resumen": lambda d: f"{d.get('nombre', '?')} ({d.get('mapa', '?')})", "campos": [
        c("id", "Identificador", req=True), c("nombre", "Nombre", req=True),
        c("mapa", "Localidad", "ref", ref="mapa", req=True, defecto="puerto_bravo"),
        c("premio", "Premio", "entero", req=True, defecto=500), c("tiempo", "Tiempo en segundos", "entero", req=True, defecto=90),
        c("xy", "Los puntos son coordenadas, no cruces", "si_no", "Márcalo en el mar."),
        c("puntos", "Puntos de control", "lista", "El primero es la salida.", sub="punto", como_pares=("a", "b"), req=True)]},
    "punto": {"titulo": "Punto", "resumen": lambda d: f"{d.get('a', '?')}, {d.get('b', '?')}", "campos": [
        c("a", "Avenida, o metros al este", "decimal", req=True, defecto=0), c("b", "Calle, o metros al norte", "decimal", req=True, defecto=0)]},
    "comida": {"titulo": "Comida", "resumen": lambda d: f"{d.get('nombre', '?')}: {d.get('precio', '?')} euros", "campos": [
        c("nombre", "Nombre", req=True), c("precio", "Precio", "entero", req=True, defecto=10), c("salud", "Salud que recupera", "entero", req=True, defecto=20)]},
    "objeto": {"titulo": "Objeto de tienda", "resumen": lambda d: f"{d.get('nombre', '?')}", "campos": [
        c("id", "Identificador", req=True, ayuda="El juego usa botiquin, ganzua y chaleco. Aquí puedes cambiarles nombre, precio y descripción."),
        c("nombre", "Nombre", req=True), c("precio", "Precio", "entero", req=True), c("desc", "Descripción", "largo")]},
    "pez": {"titulo": "Pez", "resumen": lambda d: f"{d.get('nombre', '?')}: {d.get('valor', '?')} euros", "campos": [
        c("nombre", "Nombre con artículo, por ejemplo: una merluza", req=True), c("valor", "Valor", "entero", req=True, defecto=20),
        c("peso", "Frecuencia", "entero", "Cuanto más alto, más veces pica.", req=True, defecto=10)]},
    "persona": {"titulo": "Persona, contenido para adultos", "resumen": lambda d: f"{d.get('nombre', '?')}, {d.get('edad', '?')} años", "campos": [
        c("id", "Identificador", req=True), c("nombre", "Nombre", req=True),
        c("edad", "Edad", "entero", "Tiene que ser una persona adulta: 18 años o más.", req=True, minimo=18, defecto=30),
        c("lugar", "Lugar donde suele estar", "ref", ref="lugar", req=True),
        c("gustos", "Planes favoritos", "refs", ref="actividad"), c("regalo", "Regalo favorito", "ref", ref="regalo"),
        c("desc", "Descripción", "largo", req=True)]},
    "actividad": {"titulo": "Plan para una cita", "resumen": lambda d: f"{d.get('nombre', '?')}: {d.get('precio', 0)} euros", "campos": [
        c("id", "Identificador", req=True), c("nombre", "Nombre", req=True), c("precio", "Precio", "entero", req=True, defecto=0),
        c("horas", "Horas que dura", "decimal", req=True, defecto=2)]},
    "regalo": {"titulo": "Regalo", "resumen": lambda d: f"{d.get('nombre', '?')}: {d.get('precio', 0)} euros", "campos": [
        c("id", "Identificador", req=True), c("nombre", "Nombre", req=True), c("precio", "Precio", "entero", req=True, defecto=20),
        c("afinidad", "Afinidad que da", "entero", req=True, defecto=5)]},
    "sustancia": {"titulo": "Sustancia, contenido para adultos", "resumen": lambda d: f"{d.get('nombre', '?')}: {d.get('precio', '?')} euros", "campos": [
        c("id", "Identificador", req=True, ayuda="Si creas el sonido tomar_ seguido de este identificador en la carpeta de sonidos, sonará al tomarla."),
        c("nombre", "Nombre", req=True), c("unidad", "Unidad", req=True, defecto="dosis"),
        c("legal", "Es legal: no se vende en proveedores", "si_no"), c("precio", "Precio base", "entero", req=True, defecto=30),
        c("duracion", "Duración del efecto en segundos", "entero", req=True, defecto=100),
        c("animo", "Cambio de ánimo al tomarla", "entero"), c("punteria", "Cambio de puntería", "decimal", "Por ejemplo 0,05 o menos 0,05."),
        c("velocidad", "Factor de velocidad al correr", "decimal", "1 no cambia nada; 1,15 es un 15 por ciento más."),
        c("dano", "Factor de daño recibido", "decimal", "Por debajo de 1 recibes menos daño."),
        c("deriva", "Tambaleo al caminar", "decimal"), c("tono", "Distorsión del sonido", "decimal"),
        c("adiccion", "Dependencia que crea cada toma", "decimal", req=True, defecto=3),
        c("sobredosis", "Tomas seguidas que provocan sobredosis", "entero", req=True, defecto=3, minimo=2),
        c("bajon", "Bajón al pasarse el efecto", "objeto", sub="bajon"), c("desc", "Descripción", "largo", req=True)]},
    "bajon": {"titulo": "Bajón", "campos": [
        c("animo", "Cambio de ánimo", "entero"), c("punteria", "Cambio de puntería", "decimal"), c("salud", "Cambio de salud", "entero"),
        c("duracion", "Duración en segundos", "entero", req=True, defecto=90)]},
    "mapa": {"titulo": "Localidad o mapa", "resumen": lambda d: f"{d.get('nombre', '?')} ({d.get('tipo', 'ciudad')})", "campos": [
        c("id", "Identificador", req=True), c("nombre", "Nombre", req=True),
        c("tipo", "Tipo", "opcion", ops=[("ciudad", "Ciudad"), ("pueblo", "Pueblo"), ("isla", "Isla"), ("mar", "Mar abierto")], req=True, recarga=True, defecto="pueblo"),
        c("avenidas", "Avenidas, de oeste a este", "textos", "Un nombre por línea. Van de sur a norte y están separadas 90 metros.", si=lambda d: d.get("tipo") != "mar", grupo="Calles"),
        c("calles", "Calles, de sur a norte", "textos", "Un nombre por línea. Van de oeste a este.", si=lambda d: d.get("tipo") != "mar", grupo="Calles"),
        c("barrios", "Barrios", "lista", "Cada manzana debe pertenecer a un barrio.", sub="barrio", si=lambda d: d.get("tipo") != "mar", grupo="Calles"),
        c("bloques", "Manzanas que no son edificios", "lista", "Plazas, parques, playas y muelles. Las demás son edificios.", sub="bloque", como_bloques=True, si=lambda d: d.get("tipo") != "mar", grupo="Calles"),
        c("ancho", "Ancho del mar en metros", "entero", si=_es("mar"), grupo="Calles"), c("alto", "Alto del mar en metros", "entero", si=_es("mar"), grupo="Calles"),
        c("islas", "Islas", "lista", sub="isla", si=_es("mar"), grupo="Calles"),
        c("barcos", "Barcos que navegan por él", "refs", ref="modelo", si=_es("mar"), grupo="Calles"),
        c("descripcion", "Descripción del mar", "largo", si=_es("mar"), grupo="Calles"),
        c("trafico", "Vehículos circulando", "entero", defecto=3, grupo="Vida"), c("peatones", "Peatones", "entero", defecto=4, grupo="Vida"),
        c("policia", "Hay policía", "si_no", defecto=True, grupo="Vida"), c("aparcados", "Hay coches aparcados", "si_no", defecto=True, grupo="Vida"),
        c("nombre_objeto", "Nombre de los objetos de colección", defecto="Cinta de casete", grupo="Vida"),
        c("casetes", "Posiciones de los objetos de colección", "lista", sub="punto_xy", como_pares=("a", "b"), grupo="Vida"),
        c("vias", "Recorrido de las vías del tranvía", "lista", "Los cruces por los que pasan las vías, en orden. Basta con poner los cruces donde giran: entre uno y el siguiente, "
          "las vías van primero por la calle y luego por la avenida. Después del último vuelven al primero. Cada parada para en el punto de las vías que le queda más cerca. "
          "Si lo dejas vacío, el juego tiende las vías por el cruce más cercano a cada parada.", sub="cruce_via", como_pares=("a", "b"), si=lambda d: d.get("tipo") == "ciudad", grupo="Transporte"),
        c("transporte", "Poner el transporte público que falte", "si_no", "Con sí, si la localidad no trae paradas de tranvía, estación de tren o aeropuerto, el juego se los pone al cargarla. "
          "Con no, la localidad tiene solo lo que tú le pongas.", defecto=True, si=lambda d: d.get("tipo") != "mar", grupo="Transporte"),
        c("lugares", "Lugares incluidos en el propio mapa", "lista", "También puedes crearlos en la sección Lugares eligiendo esta localidad.", sub="lugar", grupo="Vida"),
    ]},
    "barrio": {"titulo": "Barrio", "resumen": lambda d: f"{d.get('nombre', '?')}", "campos": [
        c("id", "Identificador", req=True), c("nombre", "Nombre", req=True),
        c("i", "Manzanas, de oeste a este", "par", "Primera y última manzana, empezando en cero.", etiquetas=("Primera manzana, de oeste a este", "Última manzana, de oeste a este"), req=True),
        c("j", "Manzanas, de sur a norte", "par", etiquetas=("Primera manzana, de sur a norte", "Última manzana, de sur a norte"), req=True),
        c("ambiente", "Sonido de ambiente", "ref", ref="sonido", req=True, defecto="amb_residencial"),
        c("vehiculos", "Vehículos que circulan y aparcan", "refs", ref="modelo"),
        c("descripcion", "Descripción", "largo", req=True)]},
    "bloque": {"titulo": "Manzana", "resumen": lambda d: f"Manzana {d.get('i', '?')}, {d.get('j', '?')}: {d.get('tipo', '?')}", "campos": [
        c("i", "Avenida, desde el oeste", "entero", req=True, defecto=0), c("j", "Calle, desde el sur", "entero", req=True, defecto=0),
        c("tipo", "Suelo", "opcion", ops=BLOQUES[1:], req=True, defecto="plaza")]},
    "isla": {"titulo": "Isla", "resumen": lambda d: f"{d.get('nombre', '?')}", "campos": [
        c("nombre", "Nombre", req=True), c("x", "Metros al este", "entero", req=True), c("y", "Metros al norte", "entero", req=True),
        c("r", "Radio", "entero", req=True, defecto=40)]},
    "cruce_via": {"titulo": "Cruce por el que pasan las vías", "resumen": lambda d: f"avenida {d.get('a', '?')}, calle {d.get('b', '?')}", "campos": [
        c("a", "Número de avenida, desde el oeste, empezando en cero", "entero", req=True, defecto=0, minimo=0),
        c("b", "Número de calle, desde el sur, empezando en cero", "entero", req=True, defecto=0, minimo=0)]},
    "punto_xy": {"titulo": "Posición", "resumen": lambda d: f"{d.get('a', '?')}, {d.get('b', '?')}", "campos": [
        c("a", "Metros al este", "decimal", req=True, defecto=0), c("b", "Metros al norte", "decimal", req=True, defecto=0)]},
    "personaje": {"titulo": "Personaje para elegir al empezar", "resumen": lambda d: f"{d.get('nombre', '?')} {d.get('apellido', '')}", "campos": [
        c("id", "Identificador", req=True), c("nombre", "Nombre", req=True, ayuda="En los textos de la historia sustituye a Dani."),
        c("apellido", "Apellido", req=True), c("desc", "Descripción", "largo", "Se lee en el menú de elegir personaje. Cuenta sus ventajas.", req=True),
        c("dinero", "Dinero inicial", "entero"), c("salud_max", "Salud máxima", "entero", minimo=50, maximo=150),
        c("animo", "Ánimo inicial, de 0 a 100", "entero", minimo=0, maximo=100), c("reputacion", "Fama inicial en la calle", "entero"),
        c("ciudadania", "Prestigio inicial entre los vecinos, de 0 a 100", "entero", minimo=0, maximo=100),
        c("conduccion", "Nivel inicial de conducción", "entero", minimo=0, maximo=10), c("punteria", "Nivel inicial de puntería", "entero", minimo=0, maximo=10),
        c("resistencia", "Nivel inicial de resistencia", "entero", minimo=0, maximo=10), c("pesca", "Nivel inicial de pesca", "entero", minimo=0, maximo=10),
        c("arma", "Arma inicial", "ref", ref="arma"), c("botiquines", "Botiquines", "entero"), c("ganzuas", "Ganzúas", "entero")]},
    "capitulo": {"titulo": "Capítulo", "resumen": lambda d: f"{d.get('clave', '?')}: {d.get('valor', '?')}", "campos": [
        c("clave", "Número", req=True), c("valor", "Título", req=True)]},
}

# Secciones de la ventana principal: (clave en el archivo del mod, título, esquema, clave en los datos base)
SECCIONES = [
    ("lugares", "Lugares", "lugar"), ("misiones", "Misiones", "mision"), ("armas", "Armas", "arma"),
    ("vehiculos", "Vehículos y barcos", "vehiculo"), ("carreras", "Carreras", "carrera"), ("mapas", "Localidades y mapas", "mapa"),
    ("comidas", "Comidas", "comida"), ("objetos", "Objetos de tienda", "objeto"), ("peces", "Peces", "pez"),
    ("capitulos", "Capítulos", "capitulo"), ("personajes", "Personajes para elegir", "personaje"),
    ("personas", "Personas, contenido para adultos", "persona"), ("sustancias", "Sustancias, contenido para adultos", "sustancia"),
    ("actividades", "Planes para citas, contenido para adultos", "actividad"), ("regalos", "Regalos, contenido para adultos", "regalo"),
]


# Pestañas del formulario de lugar: así cada página tiene pocas letras de acceso y ninguna se repite.
for _cp in ESQUEMAS["lugar"]["campos"]:
    if _cp["k"] in ("bloque", "lado", "pos", "xy"):
        _cp["grupo"] = "Posición"
    elif _cp["k"] not in ("id", "nombre", "tipo", "mapa", "desc"):
        _cp["grupo"] = "Más opciones"
