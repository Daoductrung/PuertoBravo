# Translating the Puerto Bravo guides into English

Puerto Bravo: Ley del Asfalto is an audio game for blind players, written in Spanish. Its guides (manual, change log, mod editor guide) are HTML pages read with a screen reader. Each guide has been split into chunks in `traduccion\en\docs\partes\`. Each chunk is a piece of one HTML file, cut at a heading.

## What to produce

For every chunk you are given, write the English translation to `traduccion\en\docs\hechos\` under **the same file name**, UTF-8, with CRLF line endings like the source. Write the files directly with the Write tool; do not generate them with scripts that call a translation service.

Translate **everything**: every paragraph, list item, heading, table cell, title and alt text. Never summarise, shorten, merge or drop anything. The translation of a chunk must have the same HTML elements in the same order: the same number of `<h2>`, `<h3>`, `<p>`, `<li>`, `<ul>`, `<ol>`, `<a>`, `<kbd>`, `<code>`, `<strong>`, `<pre>` and so on.

## Rules

1. Keep the HTML exactly: tags, attributes, entities, comments and blank lines. Only the human text changes. HTML comments such as `<!-- TECLAS:INICIO -->` stay as they are. `lang="es"` becomes `lang="en"`.
2. Links to the other guides change to their English version: `href="teclas_es.html"` becomes `href="teclas_en.html"`, and the same in the link text and anywhere the text names a guide file (`manual_es.html` becomes `manual_en.html`). Exception: where the text explains the naming scheme with examples of several languages (manual_es, manual_en, manual_it...), keep the examples as they make sense in English.
3. Do not translate things the player has to type or find on disk: folder and file names (`data\sonidos\por_defecto`, `data\voces\propias`, `servidor.conf`, `pack.json`), JSON keys and values inside `<code>` or `<pre>`, option keys of the server configuration, console commands, URLs, version numbers. They are real names in the program.
4. Names of things inside the game (menus, options, places, characters, missions, items, vehicles, weapons, shops, gangs, sounds) must be **exactly** what the English game says. Look each one up in the game's English catalog:

       .venv\Scripts\python.exe traduccion\en\buscar.py "Mis vehículos"
       .venv\Scripts\python.exe traduccion\en\buscar.py --contiene "Actualizaciones"

   The first form gives the exact translation, or the closest ones; the second lists every catalog entry that contains the text. Use them for every menu path ("Opciones, Actualizaciones, Componentes" is "Options, Updates, Components" only if the catalog says so). Proper names of towns, people and businesses follow the catalog too.
5. Keys: Intro is Enter, Re Pág is Page Up, Av Pág is Page Down, Mayúsculas is Shift, Supr/Suprimir is Delete, Inicio is Home, Fin is End, Tabulador is Tab, Retroceso is Backspace, Espacio is Space, flecha arriba is Up Arrow, Control stays Control, Alt stays Alt, and the letter keys stay the same letters (the game's keys don't change with the language). "La tecla H del lector" etc. stays H.
6. Money stays in euros. Keep numbers, dates and versions.
7. Write natural, plain English for a screen-reader user: short sentences, the same direct second person ("you") as the Spanish, no flourishes. US or UK spelling, but be consistent within a file (prefer US).
8. Never add names of forum users or people that are not already in the text.

When you finish, check each file: open the source and your translation and compare the count of each tag (a quick Python count of `<li`, `<p`, `<h2`, `<h3`, `<a `, `<kbd`, `<code` is enough). Fix any difference before reporting.
