# Cómo colaborar con Puerto Bravo

Gracias por querer ayudar. No hace falta saber programar: lo que más falta hace ahora mismo es sonido.

## Sonidos: la ayuda más valiosa

Los sonidos del juego son muy mejorables, y es lo que más se nota en un juego que solo se oye. Puedes ayudar de tres maneras:

- Un sonido suelto: sustituye el archivo en `data\sonidos\por_defecto` y cuéntanos cuál has cambiado.
- Un pack completo o parcial: una carpeta dentro de `data\sonidos` con los sonidos que quieras cambiar. Los que no pongas suenan con los de serie.
- Decirnos qué sonidos molestan, confunden o no se distinguen.

La guía `data\docs\cambiar_sonidos.html` describe los 237 sonidos uno por uno y explica cómo se prepara cada tipo. Dos cosas importantes:

- Los efectos se pasan a mono, porque es el juego quien los coloca alrededor del jugador. Los ambientes (`amb_...`) y la lluvia se quedan en estéreo.
- Solo podemos incluir sonidos que se puedan repartir libremente: grabados por ti, de dominio público o con licencia CC0. Dinos de dónde sale cada uno.

## Voces

Cualquier misión puede sonar con voces grabadas. El editor de mods escribe el guion con Control G: cada frase, quién la dice y el nombre que debe tener su archivo. Graba con tu voz o con voces sintéticas que tengas permiso para usar. No se aceptan voces clonadas de personas reales ni sacadas de otros juegos o películas.

## Mods

Con `EditorMods.exe` se crean lugares, misiones, vehículos, armas y localidades enteras sin programar. Tiene que ser contenido original: no se aceptan mods que copien mapas, personajes, nombres o misiones de otros juegos.

## Avisar de un fallo

Abre una incidencia y adjunta la carpeta de la sesión en la que falló, comprimida. Está en `data\logs`, una por sesión, y no contiene datos personales. Si notas algo raro jugando, pulsa F12 para dejar una marca en el registro.

## Código

- Python 3.15. `entorno.bat` crea el entorno y `python -m pytest pruebas` pasa las pruebas, que deben seguir pasando todas.
- La accesibilidad es el requisito: todo lo nuevo se dice en voz alta, tiene su sonido y funciona solo con teclado.
- Todo lo que cambie para el jugador se anota en `data\docs\novedades.html` y en el manual.
- Lo que maneje datos del jugador no debe llegar al registro: usa `registro.privado()` o `registro.ocultar()`.
- El README explica la estructura, la compilación y la publicación.

## Qué falta

En `README.md` y en las incidencias abiertas está lo pendiente. Lo más valioso ahora: sonido, traducción al inglés y jugar en línea sin abrir puertos.
