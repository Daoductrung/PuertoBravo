# Ayuda de F1 para cada opción de menú

Puerto Bravo es un audiojuego para personas ciegas. En cualquier menú, F1 dice la ayuda de la opción enfocada: es la propiedad `ayuda` de `Opcion(texto, accion, ajuste=None, ayuda=None)` (juego/menus.py). Si una opción no tiene ayuda, F1 dice una frase genérica sobre cómo moverse por los menús, y eso no le sirve a nadie. **Cada opción tiene que tener su ayuda propia.**

## Qué hacer
1. En tus archivos, busca cada `Opcion(...)` sin `ayuda=` (y las funciones que crean opciones y aceptan una ayuda opcional, como `si_no`, `lista`, `numero`, `vol` en las opciones, o ayudantes locales: dales su ayuda).
2. Lee el código de lo que hace la opción (su acción o su ajuste) y escribe una ayuda en español que diga, en una o dos frases cortas:
   - qué hace al pulsar Intro (o qué cambia con las flechas izquierda y derecha, si es un ajuste);
   - lo que cuesta, lo que tarda o la consecuencia, si la hay (dinero, horas de juego, policía, fama, reputación...);
   - cuándo no se puede, si el código lo comprueba.
   No repitas el texto de la opción con otras palabras: di lo que no se sabe por el nombre. No inventes nada que el código no haga.
3. La ayuda va en `tr("...")`, como todos los textos, con huecos con nombre si lleva datos: `ayuda=tr("Cuesta {precio} euros y tarda una hora.").format(precio=p)`. Si la opción se crea en un bucle (productos de una tienda, personas, vehículos), una ayuda que valga para todas, con los datos de cada una si hace falta.
4. Las opciones de salir del menú («Volver», «Cancelar», «Seguir»...) no hace falta tocarlas: el menú ya les da su ayuda.
5. Estilo: el del juego. Segunda persona («Pagas», «Te llevas»), frases cortas, sin tecnicismos, sin nombres de teclas inventados. Mira las ayudas que ya hay en el mismo archivo y escribe igual.

## Traducción al inglés (obligatoria, es norma del proyecto)
Cada texto nuevo en `tr()` necesita su inglés. Al terminar tus archivos:
- ejecuta `.venv\Scripts\python.exe herramientas\i18n\extraer.py` (deja lo pendiente en traduccion\en\pendientes\lote_*.json, con «donde» = el archivo);
- escribe la traducción de **tus** textos pendientes (los de tus archivos) en el archivo `traduccion\en\hechos\<el nombre que se te indica>.json`, un objeto JSON plano {español: inglés}. Mismos huecos {nombre} que el español. Para los nombres de menús, lugares y objetos, usa los que ya dice el juego en inglés: `.venv\Scripts\python.exe traduccion\en\buscar.py "texto"` o `--contiene "texto"`.
- No ejecutes fusionar.py ni toques otros lotes.

## Normas
- Solo puedes editar los archivos que se te asignan y tu archivo de traducción. No toques pruebas, datos, documentación ni otros módulos.
- Los archivos usan finales de línea CRLF en muchos casos: respétalos (edita con la herramienta Edit, no con scripts que reescriban el archivo entero con otro final de línea).
- Al terminar, comprueba que tus archivos compilan: `.venv\Scripts\python.exe -c "import ast,sys; [ast.parse(open(f,encoding='utf-8').read()) for f in sys.argv[1:]]" archivo1 archivo2...` y que no queda ningún `Opcion(` sin ayuda en ellos (salvo las de salir).
- Nunca escribas nombres de usuarios del foro.
