"""Genera en la carpeta data todo lo que el juego crearía al arrancar por primera vez
y pone al día la documentación que sale del propio código.

- data/sonidos: un archivo WAV por cada efecto de sonido que falte.
- data/radio: un archivo WAV por cada emisora de serie que falte.
- data/musica: las piezas de música de ambiente que falten, una carpeta por situación.
- data/docs/cambiar_sonidos.html: la guía para cambiar sonidos, con la lista completa.
- data/docs/teclas.html: la lista de teclas y de botones del mando.
- data/docs/manual.html: se actualizan la sección de teclas y las cifras (lugares, misiones...).

Nunca pisa un archivo de audio que ya exista: lo que hayas cambiado tú se respeta.
Lo ejecuta compilar.bat antes de compilar, y también se puede lanzar a mano:

    .venv\\Scripts\\python.exe herramientas\\generar_datos.py

Con el argumento «docs» solo regenera la documentación, sin tocar el audio.
"""
import html
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from juego import ayuda, mando                     # noqa: E402
from juego import catalogo_sonidos as cat          # noqa: E402
from juego import rutas, sintesis                  # noqa: E402
from juego.audio import Mezclador                  # noqa: E402
from juego.musica import AMBIENTES, EMISORAS, MusicaAmbiente, Radio          # noqa: E402

ESTILO = """<style>
body { font-family: Segoe UI, Arial, sans-serif; max-width: 54em; margin: 1em auto; padding: 0 1em; line-height: 1.6; background: #111; color: #f2f2f2; font-size: 1.1em; }
h1, h2, h3 { color: #ffd84d; }
a { color: #8fd0ff; }
code { color: #9fe89f; }
kbd { border: 1px solid #aaa; border-radius: 4px; padding: 0 .35em; background: #2a2a2a; }
li { margin-bottom: .3em; }
</style>"""

CABECERA = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Cambiar los sonidos y la música de Puerto Bravo</title>
__ESTILO__
</head>
<body>
<h1>Cambiar los sonidos y la música de Puerto Bravo</h1>
<p>Todos los sonidos del juego son archivos normales que están en la carpeta <code>data</code>, junto al ejecutable. Puedes sustituir cualquiera por una grabación tuya. Este documento explica cómo y describe cada archivo. Está organizado por encabezados: con tu lector de pantalla puedes saltar de uno a otro con la tecla H.</p>

<h2>1. Dónde está cada cosa</h2>
<ul>
<li><code>data\\sonidos</code>: todos los efectos de sonido, repartidos en subcarpetas.</li>
<li><code>data\\sonidos\\por_defecto</code>: los sonidos de serie, un archivo por sonido. Son __N_SONIDOS__ archivos. Si falta alguno o lo borras, el juego lo vuelve a crear.</li>
<li><code>data\\radio</code>: la música de las emisoras, un archivo por emisora.</li>
<li><code>data\\radio\\mi_musica</code>: tu propia emisora. Copia aquí las canciones que quieras.</li>
<li><code>data\\musica</code>: la música de ambiente, con una carpeta por situación y varias piezas en cada una.</li>
<li><code>data\\sonidos\\realista</code>, <code>data\\sonidos\\alternativo</code>, <code>data\\sonidos\\retro</code> y las demás subcarpetas: los packs de sonidos, uno por carpeta. Se eligen en Opciones.</li>
</ul>

<h2>2. Cómo cambiar un efecto de sonido</h2>
<ol>
<li>Busca en la lista del final el nombre del sonido que quieres cambiar, por ejemplo <code>claxon</code>.</li>
<li>Prepara tu grabación y ponle exactamente ese nombre: <code>claxon.wav</code>.</li>
<li>Cópiala en <code>data\\sonidos\\por_defecto</code>. No hace falta borrar el archivo del juego, que se llama <code>claxon.flac</code>: si hay dos con el mismo nombre, suena el tuyo.</li>
<li>Cierra el juego y vuelve a abrirlo. Los sonidos se cargan al arrancar.</li>
</ol>
<h3>Formatos admitidos</h3>
<ul>
<li>WAV, OGG, FLAC y MP3. Los sonidos que trae el juego están en FLAC. Si hay dos archivos con el mismo nombre y distinta extensión, se usa el que no es FLAC, que es el tuyo. Para volver al sonido del juego, borra el tuyo.</li>
<li>Por qué FLAC: comprime sin pérdida. Al leerlo salen exactamente las mismas muestras que de un WAV, pero ocupa menos de la mitad. Hasta la versión 1.6.1 los sonidos del juego eran WAV; al actualizar, el juego borra los WAV antiguos que sean idénticos a los nuevos y respeta los que hayas cambiado tú. OGG y MP3 ocupan aún menos, pero pierden algo de calidad: valen para tus grabaciones si no te importa, y el juego solo los usa donde el original ya venía así, que son la música, la radio, las voces y los ambientes largos del pack Envolvente.</li>
<li>Cualquier frecuencia de muestreo: el juego la convierte a 44100 hercios.</li>
<li>Mono o estéreo. Los efectos se pasan siempre a mono, porque es el juego quien coloca cada sonido a tu izquierda, a tu derecha, delante o detrás.</li>
</ul>
<h3>Recuperar un sonido original</h3>
<p>Borra el archivo. La próxima vez que arranque, el juego volverá a crear el sonido original. Para recuperarlos todos, borra la carpeta <code>data\\sonidos\\por_defecto</code> entera.</p>
<h3>Consejos para que suene bien</h3>
<ul>
<li>Recorta el silencio del principio: si el sonido tarda en empezar, parecerá que el juego responde tarde.</li>
<li>Mantén una duración parecida a la del original, sobre todo en pasos, avisos y balizas. La lista indica la duración de cada uno.</li>
<li>No lo dejes al máximo volumen. Los originales tienen el pico entre el 30 y el 90 por ciento según su importancia. Si el tuyo suena demasiado fuerte o flojo, ajústalo en tu editor.</li>
<li>Evita la reverberación larga en los sonidos de orientación: emborrona la dirección de la que vienen.</li>
<li>Los sonidos marcados como bucle se repiten sin parar. El final debe empalmar con el principio sin chasquido ni salto: recorta en un cruce por cero o haz un fundido cruzado.</li>
<li>Los motores se graban al ralentí y a régimen constante. El juego sube el tono al acelerar, hasta algo más del doble.</li>
</ul>
<h3>El volumen se iguala solo</h3>
<p>Cada grabación viene a un volumen distinto. Para que eso no estropee el equilibrio del juego, al cargar un sonido que has cambiado el juego lo lleva al mismo nivel que tenía el original: mide el tramo más fuerte de tu archivo, lo compara con el del sonido original y lo sube o lo baja lo que haga falta, sin dejar que sature. Así unos pasos no pueden quedar más fuertes que un disparo, ni una baliza inaudible. Se puede desactivar en Opciones, Sonido y música, Igualar el volumen de los sonidos cambiados.</p>
<p>Si aun así un sonido concreto te parece fuerte o flojo, ve a Opciones, Sonido y música, Ajustar el volumen de cada sonido. Están todos, por grupos: Intro lo hace sonar y las flechas izquierda y derecha lo bajan o lo suben, del 30 al 200 por ciento. El ajuste se guarda con tus opciones.</p>

<h2>3. Packs de sonidos</h2>
<p>Un pack es una carpeta con archivos que se llaman igual que los sonidos del juego. Los packs van dentro de <code>data\\sonidos</code>, cada uno en su subcarpeta, al lado de <code>por_defecto</code>, y se eligen dentro del juego en Opciones, Sonido y música, Pack de sonidos, con las flechas izquierda y derecha. El cambio se oye al momento y no toca tus archivos de <code>data\\sonidos\\por_defecto</code>: para volver atrás, elige «por defecto».</p>
<ul>
<li>Un pack tuyo no tiene que traerlos todos: los sonidos que no traiga siguen sonando con el original.</li>
<li>El volumen de cada sonido del pack se iguala al del original, como se explica arriba.</li>
<li>De serie vienen instalados los packs __PACKS__. Cada uno trae todos los sonidos del juego: sustituyen por grabaciones de dominio público todo lo que no es orientación, y conservan el original en los sonidos de orientación: balizas, tonos, semáforos, radar, localizadores y firmas de los lugares. El archivo <code>CREDITOS.txt</code> de cada pack dice de dónde sale cada sonido y cuáles son originales.</li>
</ul>
<h3>Hacer tu propio pack</h3>
<ol>
<li>Crea una carpeta dentro de <code>data\\sonidos</code> con el nombre del pack, sin espacios raros: por ejemplo <code>mi_pack</code>.</li>
<li>Copia dentro tus grabaciones con el nombre exacto del sonido que sustituyen: <code>claxon.wav</code>, <code>paso_acera0.ogg</code>. La lista del final de este documento tiene todos los nombres.</li>
<li>Abre el juego y elige el pack en Opciones.</li>
</ol>
<p>Si quieres, añade un archivo <code>pack.json</code> con el nombre que se leerá en Opciones y algunos ajustes:</p>
<pre><code>{
  "nombre": "Mi pack",
  "descripcion": "Grabado en mi calle",
  "autor": "Tu nombre",
  "licencia": "CC0",
  "igualar": true,
  "volumenes": {"claxon": 0.8, "ladrido": 1.3}
}</code></pre>
<ul>
<li><code>igualar</code>: con <code>false</code>, los sonidos de este pack entran tal cual, sin igualar el volumen. Úsalo solo si ya los has nivelado tú.</li>
<li><code>volumenes</code>: retoque por sonido que se aplica después de igualar. 1 lo deja como está, 0.8 lo baja un veinte por ciento.</li>
</ul>
<p>Para compartir un pack, comprime su carpeta. Quien lo reciba la descomprime dentro de su <code>data\\sonidos</code>.</p>

<h2>4. La radio</h2>
<h3>Cambiar la música de una emisora</h3>
<p>Cada emisora de serie tiene un nombre de archivo en <code>data\\radio</code>. Sustituye el archivo por otra canción con el mismo nombre y sonará esa.</p>
<p>Una emisora puede tener varias canciones: todas las que se llamen como la emisora, o como la emisora seguida de un guion bajo y lo que quieras, son suyas. Por ejemplo <code>bravo.mp3</code>, <code>bravo_1.mp3</code> y <code>bravo_dos.ogg</code> son tres canciones de Bravo FM: suenan al azar y, cuando acaba una, entra otra distinta. Con una sola canción, se repite en bucle.</p>
<ul>
__EMISORAS__
</ul>
<p>Si borras uno de estos archivos, el juego vuelve a componer la música original. Las canciones se nivelan solas al cargarlas: da igual a qué volumen venga cada archivo.</p>
<h3>Añadir emisoras nuevas</h3>
<p>Cualquier otro archivo de audio que dejes en <code>data\\radio</code> es una emisora nueva, con el nombre del archivo. Por ejemplo, <code>radio_clasica.mp3</code> aparece en el dial como «Radio clasica». Los guiones bajos se leen como espacios.</p>
<h3>Mi música</h3>
<p>Los archivos de <code>data\\radio\\mi_musica</code> forman la emisora «Mi música». Dentro del coche, la tecla R pasa de una canción a la siguiente antes de saltar a la emisora siguiente.</p>

<h2>5. La música de ambiente</h2>
<p>Fuera de los vehículos, o con la radio apagada, suena una música de fondo suave que cambia con la situación. En cada situación hay varias piezas: el juego empieza por una al azar y, cuando termina, pasa a otra distinta. Al encender la radio de un vehículo la música de ambiente se calla, y vuelve cuando la apagas o te bajas.</p>
<p>Cada situación es una carpeta dentro de <code>data\\musica</code>:</p>
<ul>
__AMBIENTES__
</ul>
<ul>
<li>Para añadir música tuya, copia archivos de audio en la carpeta de la situación que quieras. Todos los archivos de la carpeta entran en la rotación, sean cuantos sean: si en <code>exploracion</code> dejas un <code>exploracion_5.wav</code>, o veinte canciones con cualquier nombre, se usan todas al azar junto a las que ya hay. Valen WAV, OGG, FLAC y MP3.</li>
<li>Toda la música se nivela sola al cargarla: cada pieza de ambiente, cada emisora, cada emisora nueva y cada canción de Mi música quedan al mismo nivel, para que ninguna suene más fuerte que otra. Lo único que cambia el volumen es lo que tú elijas en Opciones.</li>
<li>Para quitar una pieza de serie y que no vuelva, sustitúyela por otra con el mismo nombre. Si solo la borras, el juego la vuelve a componer.</li>
<li>Para que en una situación suene solo tu música, sustituye todas las piezas de serie de su carpeta.</li>
<li>La música de ambiente se activa, se desactiva y se ajusta de volumen en Opciones, Sonido y música.</li>
</ul>

<h2>6. Lista completa de sonidos</h2>
<p>El nombre del archivo es el que aparece al principio de cada línea, con la extensión <code>.flac</code> en los que trae el juego. Los tuyos pueden llevar cualquiera de las admitidas.</p>
"""


def generar_audio():
    mez = Mezclador(dispositivo=False)
    sonidos = sintesis.cargar(mez, rutas.carpeta_sonidos())
    from juego import packs
    packs.referencias(rutas.carpeta_sonidos())          # tabla de niveles para igualar el volumen de los sonidos cambiados
    radio = Radio(mez, rutas.carpeta_data("radio"))
    radio.esperar()
    musica = MusicaAmbiente(mez, rutas.carpeta_data("musica"))
    musica.esperar()
    return sonidos, radio, musica


def _escribir(nombre, texto):
    ruta = os.path.join(rutas.carpeta_data("docs"), nombre)
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write(texto)
    return ruta


def generar_doc(sonidos):
    grupos = {}
    for nombre in sorted(sonidos):
        grupos.setdefault(cat.grupo_de(nombre), []).append(nombre)
    cab = CABECERA.replace("__ESTILO__", ESTILO).replace("__N_SONIDOS__", str(len(sonidos)))
    from juego import packs
    instalados = [p for p in packs.listar() if not p["id"].startswith("_")]
    cab = cab.replace("__PACKS__", ", ".join(f"«{html.escape(p['nombre'])}», con {p['n']} sonidos" for p in instalados) or "que copies tú")
    cab = cab.replace("__EMISORAS__", "\n".join(f"<li><code>{e['id']}.mp3</code>: {html.escape(e['nombre'])}.</li>" for e in EMISORAS if "estilo" in e))
    cab = cab.replace("__AMBIENTES__", "\n".join(
        f"<li><code>data\\musica\\{k}</code>: {html.escape(desc[0].lower() + desc[1:])}. De serie trae {len(piezas)} piezas, de <code>{k}_1.mp3</code> a <code>{k}_{len(piezas)}.mp3</code>.</li>"
        for k, (desc, piezas) in AMBIENTES.items()))
    partes = [cab]
    for k in sorted(grupos):
        if k < len(cat.GRUPOS):
            titulo, intro = cat.GRUPOS[k][0], cat.GRUPOS[k][1]
        else:
            titulo, intro = "Otros sonidos", ""
        partes.append(f"<h3>{html.escape(titulo)}</h3>")
        if intro:
            partes.append(f"<p>{html.escape(intro)}</p>")
        partes.append("<ul>")
        for nombre in grupos[k]:
            dur = len(sonidos[nombre]) / sintesis.SR
            bucle = " Se reproduce en bucle." if sintesis.es_bucle(nombre) and "En bucle" not in cat.describir(nombre) else ""
            partes.append(f"<li><code>{nombre}</code>: {html.escape(cat.describir(nombre))}{bucle} Dura " + f"{dur:.2f}".replace(".", ",") + " segundos.</li>")
        partes.append("</ul>")
    partes.append("</body>\n</html>\n")
    return _escribir("cambiar_sonidos.html", "\n".join(partes))


# ------------------------------------------------------------------ teclas y manual
TITULOS_TECLAS = {"general": "En cualquier momento", "pie": "A pie", "coche": "Al volante, en barco y en helicóptero"}
MENUS = [("Flecha arriba y flecha abajo", "moverte por las opciones"), ("Intro", "elegir"), ("Flecha izquierda y flecha derecha", "cambiar el valor de una opción"),
         ("Escape", "volver atrás. Todos los menús tienen además una opción Volver"), ("Inicio y Fin", "primera y última opción"),
         ("Una letra", "salta a la siguiente opción que empieza por ella"), ("F1", "explicación de la opción actual"),
         ("Re Pág y Av Pág", "repasar los mensajes anteriores")]


def _lista(pares):
    return "<ul>\n" + "\n".join(f"<li><kbd>{html.escape(t)}</kbd>: {html.escape(d)}.</li>" for t, d in pares) + "\n</ul>"


def html_teclas(nivel=3):
    h = f"h{nivel}"
    partes = []
    for clave, titulo in TITULOS_TECLAS.items():
        partes.append(f"<{h}>{titulo}</{h}>")
        partes.append(_lista(ayuda.TECLAS[clave]))
    recorrido = getattr(ayuda, "TECLAS_RECORRIDO", None)
    if recorrido:
        partes.append(f"<{h}>Recorriendo una casa, un local o una tienda por dentro</{h}>")
        partes.append(_lista(recorrido))
    extra = getattr(ayuda, "TECLAS_ADULTOS", None)
    if extra:
        partes.append(f"<{h}>Con el contenido para adultos activado</{h}>")
        partes.append(_lista(extra))
    return "\n".join(partes)


def html_mando(nivel=3):
    h = f"h{nivel}"
    m = mando.Mando.__new__(mando.Mando)
    m.mapa = {c: dict(v) for c, v in mando.POR_DEFECTO.items()}
    m.tipo = "xbox"
    partes = []
    for c, titulo in (("menu", "Mando, en los menús"), ("pie", "Mando, a pie"), ("coche", "Mando, al volante")):
        lineas = [l.split(". ", 1)[1] for l in m.lineas_ayuda((c,))]
        if not lineas:
            continue
        partes.append(f"<{h}>{titulo}</{h}>")
        partes.append("<ul>\n" + "\n".join(f"<li>{html.escape(l)}</li>" for l in lineas) + "\n</ul>")
    return "\n".join(partes)


def generar_teclas():
    try:
        botones = html_mando(2)
    except Exception as e:                                  # el mando no debe impedir generar el resto
        botones = f"<p>La lista de botones se consulta dentro del juego, en Opciones, Mando. ({html.escape(str(e))})</p>"
    texto = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Teclas y botones de Puerto Bravo: Ley del Asfalto</title>
{ESTILO}
</head>
<body>
<h1>Teclas y botones de Puerto Bravo</h1>
<p>Lista completa de teclas del juego. Sale del propio programa, así que siempre está al día. Dentro del juego la tienes con <kbd>F1</kbd>.</p>
<h2>En los menús</h2>
{_lista(MENUS)}
<p>En los diálogos de la historia, Intro pasa a la frase siguiente, flecha arriba la repite, flecha izquierda vuelve a la anterior y Escape salta el diálogo.</p>
{html_teclas(2)}
<p>Los nombres de los botones del mando son los de Xbox. Con un mando de PlayStation el juego los dice con sus nombres: equis, círculo, cuadrado y triángulo.</p>
{botones}
<h2>En el panel del servidor</h2>
<p>El panel es la ventana para llevar tu propio servidor en línea. Está en la carpeta servidor del juego.</p>
<ul>
<li><kbd>F5</kbd>: arranca el servidor.</li>
<li><kbd>Mayúsculas F5</kbd>: para el servidor, avisando a los jugadores y guardándolo todo.</li>
<li><kbd>Control F5</kbd>: reinicia el servidor.</li>
<li><kbd>Control P</kbd>: configuración.</li>
<li><kbd>Control Q</kbd>: salir del panel. Si el servidor está en marcha, pregunta y lo para antes.</li>
<li><kbd>Control N</kbd>: anuncio a todos los jugadores.</li>
<li><kbd>Control M</kbd>: mensaje al jugador elegido en la lista.</li>
<li><kbd>Control E</kbd>: expulsar al jugador elegido.</li>
<li><kbd>Control I</kbd>: crear una invitación y copiarla al portapapeles.</li>
<li><kbd>Control D</kbd>: cambiar el mensaje del día.</li>
<li><kbd>Control O</kbd>: ir al campo para escribir una orden.</li>
<li><kbd>F6</kbd>: actualizar el estado y las listas.</li>
<li><kbd>Control S</kbd>: guardar ahora.</li>
<li><kbd>Control B</kbd>: copia de seguridad ahora.</li>
<li><kbd>Control R</kbd>: restaurar una copia de seguridad.</li>
<li><kbd>Control G</kbd>: guardar el registro en un archivo.</li>
<li><kbd>F1</kbd>: abrir la guía del servidor.</li>
<li><kbd>Control H</kbd>: explica el control en el que estás.</li>
<li><kbd>Control Tabulador</kbd> y <kbd>Control Mayúsculas Tabulador</kbd>: cambiar de pestaña.</li>
<li><kbd>Alt</kbd> más la letra subrayada: ir a un control de la pestaña o abrir un menú.</li>
<li>Tecla Aplicaciones o <kbd>Mayúsculas F10</kbd>: en las listas de jugadores y de cuentas, acciones sobre lo elegido.</li>
</ul>
</body>
</html>
"""
    return _escribir("teclas.html", texto)


def cifras():
    """Números del juego, para que el manual no se quede atrás."""
    from juego import mundo
    from juego.extras2 import LOGROS
    d = mundo.cargar_datos(con_mods=False)
    mapas = mundo.crear_mapas(d)
    lugares = sum(len(getattr(m, "lugares_todos", m.lugares)) for m in mapas.values())
    armas = d["armas"]
    armas = armas if isinstance(armas, list) else list(armas.values())
    return {"mapas": len(mapas), "lugares": lugares, "misiones": len(d["misiones"]), "vehiculos": len(d["vehiculos"]), "armas": len(armas),
            "logros": len(LOGROS), "personajes": len(d.get("personajes", [])), "sonidos": len([f for f in os.listdir(rutas.carpeta_sonidos()) if f.lower().endswith((".flac", ".wav", ".ogg", ".mp3"))])}


def actualizar_manual():
    ruta = os.path.join(rutas.carpeta_data("docs"), "manual.html")
    if not os.path.exists(ruta):
        return None
    with open(ruta, encoding="utf-8") as f:
        t = f.read()
    t2 = re.sub(r"<!-- TECLAS:INICIO -->.*?<!-- TECLAS:FIN -->", lambda m: "<!-- TECLAS:INICIO -->\n" + html_teclas(3) + "\n<!-- TECLAS:FIN -->", t, flags=re.S)
    try:
        for k, n in cifras().items():
            t2 = re.sub(rf'(<span data-n="{k}">)\d+(</span>)', lambda m, n=n: f"{m.group(1)}{n}{m.group(2)}", t2)
    except Exception as e:
        print("  No se pudieron actualizar las cifras del manual:", e)
    if t2 != t:
        with open(ruta, "w", encoding="utf-8", newline="\n") as f:
            f.write(t2)
    return ruta


def generar_lista_packs(sonidos):
    """adjuntos/lista_de_sonidos.txt: lo que debe traer un pack de sonidos completo, archivo por archivo."""
    carpeta = os.path.join(rutas.base(), "adjuntos")
    os.makedirs(carpeta, exist_ok=True)
    grupos = {}
    for nombre in sorted(sonidos):
        grupos.setdefault(cat.grupo_de(nombre), []).append(nombre)
    lineas = ["LISTA DE SONIDOS DE PUERTO BRAVO PARA HACER PACKS", "",
              f"Un pack completo trae estos {len(sonidos)} archivos, con estos nombres y extensión wav, ogg, flac o mp3.",
              "Cada línea: nombre del archivo, qué es, si va en bucle y cuánto dura el original.", ""]
    for k in sorted(grupos):
        lineas.append((cat.GRUPOS[k][0] if k < len(cat.GRUPOS) else "Otros sonidos").upper())
        for nombre in grupos[k]:
            dur = f"{len(sonidos[nombre]) / sintesis.SR:.2f}".replace(".", ",")
            bucle = " En bucle." if sintesis.es_bucle(nombre) else ""
            lineas.append(f"  {nombre}: {cat.describir(nombre)}{bucle} Dura {dur} segundos.")
        lineas.append("")
    ruta = os.path.join(carpeta, "lista_de_sonidos.txt")
    with open(ruta, "w", encoding="utf-8-sig", newline="\r\n") as f:
        f.write("\n".join(lineas))
    return ruta


def generar_docs(sonidos=None):
    if sonidos is None:
        mez = Mezclador(dispositivo=False)
        sonidos = sintesis.cargar(mez, rutas.carpeta_sonidos())
    return [generar_doc(sonidos), generar_teclas(), actualizar_manual(), generar_lista_packs(sonidos)]


if __name__ == "__main__":
    if "docs" in sys.argv[1:]:
        for r in generar_docs():
            print("  Documento al dia:", r)
        sys.exit(0)
    print("Generando sonidos, radio y musica de ambiente en la carpeta data...")
    S, R, A = generar_audio()
    print(f"  {len(S)} sonidos en data\\sonidos\\por_defecto")
    print(f"  {sum(1 for e in R.emisoras if 'estilo' in e)} emisoras en data\\radio")
    print(f"  {sum(len(v) for v in A.pistas.values())} piezas de musica de ambiente en data\\musica")
    for r in generar_docs(S):
        print("  Documento al dia:", r)
