# Puerto Bravo: Ley del Asfalto

Audiojuego de mundo abierto, en español y totalmente accesible. Se juega solo con el oído: con teclado o con mando de Xbox o de PlayStation, y con lector de pantalla (NVDA, JAWS o la voz de Windows). No hace falta ver la pantalla para nada.

Es un juego original. Su ciudad, su historia, sus personajes y su música son propios.

Este documento tiene cuatro partes:

1. [Para quien quiere jugar](#1-para-quien-quiere-jugar): qué es el juego y qué te vas a encontrar.
2. [Para desarrolladores](#2-para-desarrolladores): preparar el entorno, probar, compilar y publicar.
3. [Crear mods](#3-crear-mods): ampliar el juego con contenido propio.
4. [Packs de sonidos y de música](#4-packs-de-sonidos-y-de-música): cambiar cómo suena.

---

## 1. Para quien quiere jugar

### La historia

Eliges personaje. Con el primero te llamas Dani Roca y acabas de salir de la cárcel tras cumplir tres años por un robo que no cometiste. Vuelves a tu ciudad, Puerto Bravo, que ahora controla el empresario Octavio Belmonte. A partir de ahí, haz lo que quieras: sigue la historia, gánate la vida honradamente, hazte un nombre en la calle o dedícate a pescar. El juego no te obliga a nada.

### Cómo se juega sin ver

Todo lo que ocurre tiene su sonido, colocado a tu alrededor: lo que suena a la derecha está a la derecha, y lo que suena apagado está detrás. Por eso hacen falta auriculares. Además tienes muchas ayudas, todas opcionales:

- Una tecla que dice dónde estás: calle, entre qué avenidas, barrio y hacia dónde miras.
- Un escáner direccional que hace de bastón: qué hay delante, detrás y a los lados, y a cuántos metros está la pared.
- Un radar que recorre lo que hay cerca, con distancia y dirección, haciendo sonar cada cosa desde su sitio.
- GPS hablado, con una baliza sonora que marca el camino, hasta cualquier lugar de cualquier localidad.
- Un explorador de mapa para aprenderte las calles sin mover al personaje.
- Caminar solo y piloto del GPS: el personaje o el coche siguen la ruta mientras tú escuchas.
- Conducción asistida: el coche sigue su carril; tú decides la velocidad y dónde girar.
- Semáforos acústicos, pasos que suenan distinto en cada suelo y un sonido propio para cada tipo de lugar.
- Dos asistencias para explorar sin presión: no recibir daño y jugar sin policía.

### Qué hay en el mundo

- Nueve mapas de serie: las ciudades de Puerto Bravo, San Lucero y Monteferro; los pueblos de Villaseca, Cala Brava y Fuentefría; Isla Tortuga, la Plataforma Neptuno y el Mar de Poniente, navegable. Con los mods incluidos se suman tres pueblos y una isla más.
- Más de 260 lugares de serie: casas, comercios, bancos, talleres, casinos, gimnasios, cines, hospitales, embarcaderos, helipuertos y monumentos, cada uno con su sonido y su descripción.
- 53 misiones de serie entre la historia principal y las secundarias, y encargos que se repiten sin fin. Los mods añaden más de veinticinco.
- 38 vehículos: coches, motos, bicicleta, camiones, vehículos de emergencias, barcos y un helicóptero. 22 armas.
- Policía con cinco niveles de búsqueda, día y noche, lluvia, tráfico con semáforos y peatones.

### Qué puedes hacer

- Vida honrada: oficina de empleo, oficios con ascensos (taxista, conductor de ambulancia y de autobús, bombero, gruista, mensajero, transportista, heladero, pescador), cursos, voluntariado y negocios propios.
- Vida delictiva: la historia, contratos, encargos de coches, atracos y guerras de territorio.
- Ocio: carreras y regatas, casino, bingo, lotería, boxeo, galería de tiro, pesca, búsqueda de tesoros, cine, recreativos y bolsa.
- Casas con garaje, un perro que te acompaña y busca objetos, guardaespaldas, logros y habilidades que suben con la práctica.
- Hablar con cualquier persona de la calle: cada una tiene su nombre, su oficio y su carácter. Puedes preguntar, invitar a un café, hacer amigos o escribir lo que quieras decirle. Con una clave propia de la API de Anthropic, un modo opcional hace que contesten interpretadas por una inteligencia artificial.
- Una ciudad que no se repite: cada día viene distinto (rebajas, mercado, fiesta, huelga, operación salida) y cambian los precios, la gente y el tráfico. Ninguna partida es igual a otra.
- Vida realista, opcional: hambre y sueño.
- Jugar con amigos, sin servidores de nadie: tu propio juego abre la partida, con o sin contraseña, y les das una dirección. Os oís, os encontráis con el radar y el GPS, os escribís, vais en el mismo coche, hacéis carreras con apuesta y repartos en equipo.
- Siete emisoras de radio con música original, una de noticias que comenta lo que haces y otra con tu propia música. Música de ambiente que cambia con la situación.
- Un modo opcional para mayores de 18 años, desactivado de serie: relaciones, vida nocturna, sustancias y sus consecuencias, contado sin escenas explícitas.

### Requisitos y arranque

- Windows 10 u 11.
- Auriculares estéreo.
- Un lector de pantalla abierto, como NVDA o JAWS. Si no hay ninguno, el juego habla con la voz de Windows.

Descarga la última versión, descomprime la carpeta donde quieras y ejecuta `PuertoBravo.exe`. No instala nada: es portable. Dentro del juego, `F1` dice las teclas en cualquier momento, y el menú principal abre el manual completo, que está en `data\docs\manual.html` y se navega por encabezados.

El juego se actualiza desde sus propias opciones. Puedes elegir de dónde: el servidor del juego, GitHub, los dos o una dirección tuya. Tus partidas, tus opciones, tu música y tus mods no se tocan.

---

## 2. Para desarrolladores

### Requisitos

- Windows 10 u 11.
- Python 3.13 o superior. Se desarrolla con Python 3.15.

### Primeros pasos

Todo se hace con los `.bat` de la raíz:

```bat
entorno.bat    :: crea el entorno virtual .venv e instala las dependencias
jugar.bat      :: abre el juego desde el código fuente
editor.bat     :: abre el editor de mods
probar.bat     :: ejecuta las pruebas automáticas
compilar.bat   :: genera dist\PuertoBravo, portable y listo para repartir
publicar.bat   :: comprime, firma y publica la versión compilada
```

Dependencias (`requirements.txt`): pygame-ce, numpy, sounddevice, soundfile, accessible-output2, wxPython, cx_Freeze y pytest. El modo IA necesita además el paquete `anthropic`, que es opcional: sin él, el juego funciona igual y esa opción avisa de que no está disponible.

El repositorio incluye el audio: los sonidos por defecto y los tres packs en `data/sonidos`, la música de la radio en `data/radio` y la de ambiente en `data/musica`. Si falta algún sonido por defecto, el juego lo vuelve a generar al arrancar.

### Estructura

- `juego/`: el código del juego. `app.py` es el bucle y la pila de pantallas; `partida.py` reúne la partida a partir de módulos por tema (conducción, combate, misiones, trabajos, vida honrada, conversación, juego en red, azar diario...); `sintesis.py` genera los sonidos por defecto; `audio.py` es el mezclador con sonido posicional.
- `editor/`: el editor de mods, con wxPython.
- `herramientas/`: generación de sonidos y guías, protección y comprobación de la compilación, montaje de packs, mods de serie y publicación.
- `pruebas/`: pruebas automáticas con pytest.
- `data/datos/`: mapas, lugares, misiones, armas, vehículos y personajes, en JSON.
- `data/mods/`: los mods de serie, en JSON legible.
- `data/docs/`: la documentación que se reparte con el juego, pensada solo para quien juega.
- `desarrollo/`: documentación técnica que no se reparte, como el formato de los archivos de mods.

### Pruebas

`probar.bat` ejecuta toda la batería. Las pruebas manejan el juego como una persona, con teclas y fotogramas: juegan todas las misiones, recorren los mapas con el GPS, entran en todos los menús y lugares, juegan veinte días con el tiempo acelerado, conectan dos juegos entre sí, manejan un mando simulado y revisan la accesibilidad del editor. También fallan si se añade un sonido sin describir o una tecla sin documentar. No usan la red ni la tarjeta de sonido.

### Compilar

`compilar.bat` usa cx_Freeze y deja en `dist\PuertoBravo` una carpeta portable con `PuertoBravo.exe` y `EditorMods.exe`. Antes regenera los mods de serie, los sonidos que falten y las guías. Al terminar:

- Protege los datos: cada JSON se comprime, se cifra y se firma, y cambia de extensión (`.pbd` datos, `.pbm` mods, `.pbs` partidas, `.pbc` opciones). El código lee las dos formas, así que en el código fuente todo sigue siendo JSON legible.
- Comprueba sola que la carpeta está completa, protegida y limpia: sin partidas, opciones, registros, música personal ni documentación de desarrollo.

La protección usa una clave que va dentro del propio programa. Evita la edición casual; no es una barrera frente a quien analice el ejecutable.

### Publicar una versión

El juego se actualiza leyendo un archivo `version.json` firmado con Ed25519. La fuente (el servidor, GitHub, ambos o una dirección personalizada) solo decide de dónde se descarga: lo que se instala tiene que estar firmado con la clave privada de quien publica, cuya clave pública va en `juego/actualizador.py`.

1. Sube `VERSION` en `juego/__init__.py` y añade las novedades al principio de `data/docs/novedades.html`.
2. Ejecuta `compilar.bat`.
3. Ejecuta `publicar.bat`. Crea en `dist\publicar` el archivo `PuertoBravo_v<versión>.zip` y su `version.json` firmado, y los copia a la carpeta escrita en `publicar_destino.txt`, que es la carpeta web del servidor.
4. Para GitHub, crea la release `v<versión>` y sube esos mismos dos archivos.

La clave se crea una sola vez con `.venv\Scripts\python.exe herramientas\publicar.py clave` y queda en `herramientas\claves`. Esa carpeta y `publicar_destino.txt` están en `.gitignore`: la clave privada no debe estar nunca en el repositorio ni en el servidor. Guarda una copia fuera del equipo. Si haces un fork y quieres publicar tus propias versiones, crea tu clave y cambia en `juego/actualizador.py` la clave pública, la dirección del servidor y el repositorio.

La verificación de la firma está implementada con la biblioteca estándar, siguiendo el RFC 8032, y se comprueba en las pruebas con sus vectores oficiales. Si el paquete `cryptography` está instalado, se usa ese.

### Accesibilidad

La accesibilidad es el requisito principal del proyecto. Todo lo que ocurre en el juego tiene sonido propio y todo texto pasa por el lector de pantalla. Todas las teclas están en la ayuda (`F1`) y en el manual, que se generan a partir del mismo código. El editor sigue pautas de accesibilidad para wxPython: etiquetas asociadas a cada control, letras de acceso sin repetir, controles nativos y ayuda contextual con `Control+H`.

---

## 3. Crear mods

Un mod añade o cambia contenido sin tocar los datos originales: lugares, misiones con todos sus pasos, armas, vehículos, carreras, comidas, objetos, peces, personajes para elegir, capítulos, mapas enteros y, para el modo adulto, personas, planes, regalos y sustancias. Los mods están en `data\mods` y se cargan al arrancar.

### Con el editor

La forma normal es `EditorMods.exe` (o `editor.bat` desde el código fuente). Es una aplicación accesible con lector de pantalla: cada cosa se crea rellenando un formulario, `Control+H` explica el campo en el que estás y `F1` abre su manual (`data\docs\editor_mods.html`). Antes de guardar comprueba que todo lo que cita el mod existe, y avisa de lo que falta.

El editor guarda siempre protegido, como `.pbm`, que es lo que carga el juego compilado, y abre tanto los `.pbm` como los `.json`.

### A mano

Un mod también es un archivo JSON. El formato está explicado, con ejemplos, en `desarrollo/formato_de_los_mods.html`, y `desarrollo/ejemplo_mod.json` es un mod mínimo. Desde el código fuente, el juego carga directamente los `.json` de `data\mods`. El juego compilado no: avisa al arrancar y pide que el archivo se abra con el editor y se guarde, para que quede comprobado y protegido.

### Mods de serie

Vienen siete, ya activados, que además sirven de modelo. Se generan con `herramientas/crear_mods_ejemplo.py`, donde se puede leer cómo está hecho cada uno:

- Costa Dorada: un pueblo pesquero con su historia y un ejemplo de todo lo que admite un mod.
- Valdeolmos: un pueblo de viñas, con un fraude de vino y una carrera de tractores.
- Peñas Altas: un pueblo minero de montaña, con una mina que alguien explota de noche.
- Isla de los Vientos: una isla a la que se llega navegando, con raqueros y salinas.
- Noches de neón: la noche de Puerto Bravo, sin mapa nuevo, con taxis nocturnos y vida social.
- Oficios y recados: más vida honrada en Puerto Bravo.
- Motor y asfalto: coches, una moto, carreras y misiones al volante.

Para compartir un mod, pasa su archivo `.pbm`. Quien lo recibe lo copia en su `data\mods`.

---

## 4. Packs de sonidos y de música

La guía completa, con la descripción y la duración de cada uno de los 223 sonidos, es `data\docs\cambiar_sonidos.html`. Resumen:

### Sonidos

- Todos los efectos están en `data\sonidos`, en subcarpetas. `por_defecto` tiene los de serie, un archivo por sonido; si borras alguno, el juego lo vuelve a crear. Cada una de las demás subcarpetas es un pack.
- El pack se elige dentro del juego, en Opciones, Sonido y música, y se oye al momento.
- Vienen tres packs completos: Realista y Alternativo, con grabaciones reales de dominio público, y Retro, con sonido de consola antigua. Los tres conservan el original en los sonidos de orientación (balizas, tonos, semáforos, radar y firmas de los lugares), porque de ellos depende moverse por el juego.
- Para hacer el tuyo, crea una carpeta en `data\sonidos` y copia dentro tus grabaciones con el nombre exacto del sonido que sustituyen: `claxon.wav`, `paso_acera0.ogg`. No hace falta traerlos todos: lo que falte suena con el original. Se admiten WAV, OGG, FLAC y MP3.
- Un archivo `pack.json` opcional da al pack su nombre, autor, licencia y retoques de volumen por sonido.
- El volumen se iguala solo: cada sonido cambiado se lleva al nivel del original, y el jugador puede subir o bajar cualquiera por separado desde Opciones.

### Música

- Radio: cada emisora tiene su archivo en `data\radio`. Una emisora puede tener varias canciones (`bravo.mp3`, `bravo_1.mp3`, `bravo_2.mp3`...), que van rotando. Cualquier otro archivo de audio que dejes ahí es una emisora nueva, y `data\radio\mi_musica` es la emisora con tu propia música.
- Ambiente: `data\musica` tiene una carpeta por situación (`menu`, `exploracion`, `noche`, `mar` y `tension`). Se usan todas las piezas que haya en cada una, al azar, se llamen como se llamen.
- Toda la música se nivela sola al cargarla, así que ninguna pista suena más fuerte que otra.

### Sonidos de terceros

Los packs Realista y Alternativo se montan con grabaciones de dominio público (licencia CC0) de kenney.nl, opengameart.org y bigsoundbank.com. Cada pack lleva un archivo `CREDITOS.txt` con el origen de cada sonido.

---

## Licencia

Licencia MIT: puedes usar, modificar y distribuir cualquier parte del juego, con la única condición de conservar el aviso de derechos y la licencia. Está en el archivo `LICENSE`.
