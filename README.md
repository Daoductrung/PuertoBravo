# Puerto Bravo: Ley del Asfalto

Audiojuego de mundo abierto, en español y totalmente accesible. Se juega solo con el oído, con teclado o con mando de Xbox o de PlayStation, y con lector de pantalla (NVDA, JAWS o la voz de Windows).

Es un juego original: su ciudad, su historia, sus personajes y su música son propios.

## Qué tiene

- Un mundo abierto con ciudades, pueblos, una isla, una plataforma y un mar navegable.
- Historia principal, historias secundarias y encargos que se repiten sin fin.
- Conducción asistida, GPS hablado con baliza sonora, radar, escáner direccional, semáforos acústicos y caminar solo siguiendo la ruta.
- Vida honrada (oficios, cursos, voluntariado) y vida delictiva, que se pueden mezclar.
- Coches, motos, camiones, barcos y helicóptero; armas; policía con cinco niveles de búsqueda.
- Radio con música propia, música de ambiente y packs de sonidos intercambiables.
- Un modo opcional para mayores de 18 años, desactivado de serie.
- Jugar con amigos sin servidores externos: el propio juego monta el servidor, con o sin contraseña.
- Un editor de mods accesible, hecho con wxPython, y cuatro mods completos de serie.

## Requisitos

- Windows 10 u 11.
- Python 3.13 o superior (se desarrolla con 3.15).
- Auriculares estéreo.

## Empezar

```bat
entorno.bat    :: crea el entorno virtual e instala las dependencias
jugar.bat      :: abre el juego
editor.bat     :: abre el editor de mods
probar.bat     :: ejecuta las pruebas automáticas
compilar.bat   :: genera dist\PuertoBravo, portable y listo para distribuir
```

El repositorio incluye el audio: los sonidos por defecto y los tres packs en `data/sonidos`, la música de la radio en `data/radio` y la música de ambiente en `data/musica`. Si falta algún sonido por defecto, el juego lo vuelve a generar al arrancar.

## Estructura

- `juego/`: el código del juego.
- `editor/`: el editor de mods.
- `herramientas/`: generación de datos y documentación, comprobación y protección de la compilación, montaje de packs y de mods.
- `pruebas/`: pruebas automáticas con pytest. Juegan todas las misiones, recorren los mapas con el GPS, manejan el juego con un mando simulado y revisan la accesibilidad del editor.
- `data/datos/`: mapas, lugares, misiones, armas, vehículos y personajes, en JSON.
- `data/mods/`: los mods de serie.
- `data/docs/`: manual, lista de teclas, novedades y guías, en HTML navegable por encabezados.

## Compilación

`compilar.bat` usa cx_Freeze y deja en `dist\PuertoBravo` una carpeta portable con `PuertoBravo.exe` y `EditorMods.exe`. La compilación sale limpia, sin partidas ni opciones personales, y con los datos del juego y los mods protegidos: van cifrados y firmados, con extensiones propias (`.pbd` para los datos, `.pbm` para los mods y `.pbs` para las partidas), para que no se puedan editar a mano. El editor de mods abre los archivos protegidos y los `.json` escritos a mano, y siempre guarda protegido.

La protección usa una clave que va dentro del propio programa. Evita la edición casual; no es una barrera frente a quien analice el ejecutable.

## Accesibilidad

La accesibilidad es el requisito principal del proyecto. Todo lo que ocurre en el juego tiene sonido propio, todas las teclas están en la ayuda (F1) y en el manual, y hay pruebas que fallan si se añade un sonido sin describir o una tecla sin documentar. El editor sigue pautas de accesibilidad para wxPython: etiquetas asociadas a cada control, letras de acceso sin repetir, controles nativos y ayuda contextual con Control+H.

## Documentación

Está en `data/docs`: `manual.html`, `teclas.html`, `novedades.html`, `cambiar_sonidos.html`, `editor_mods.html` y `crear_mods.html`.

## Sonidos de terceros

Los packs de sonidos alternativos se montan con grabaciones de dominio público (licencia CC0) de kenney.nl, opengameart.org y bigsoundbank.com. Cada pack lleva un archivo `CREDITOS.txt` con el origen de cada sonido.

## Licencia

Licencia MIT: puedes usar, modificar y distribuir cualquier parte del juego, con la única condición de conservar el aviso de derechos y la licencia. Está en el archivo `LICENSE`.
