# Translating Puerto Bravo: Ley del Asfalto into English

Puerto Bravo is an audio game for blind players: everything is spoken by a screen reader or read in menus. The source
language is Spanish. You translate Spanish strings into natural, clear, concise **US English**.

## Output format

You get a batch file: a JSON list of objects `{"es": "<Spanish text>", "donde": "<file it comes from>"}`.
You write a JSON **object** mapping every Spanish text, copied **exactly** (same characters, same spaces), to its English
translation: `{"<Spanish text>": "<English text>", ...}`. Every entry of the batch must appear. Use `json.dump(..., ensure_ascii=False)`
or write valid JSON carefully. The `donde` field is only context (which part of the game the text belongs to).

## Hard rules (the game breaks if you ignore them)

1. **Placeholders stay identical**: `{nombre}`, `{dinero}`, `{v}`, `{n:02d}`, `{x!r}`, `%s`, `%d`, `{{`, `}}`. Keep every one,
   spelled exactly the same; you may move them in the sentence. Never translate the word inside the braces.
2. **Leading and trailing spaces and punctuation stay**: `" y "` -> `" and "`, `" Te quedan "` -> `" You have "` (keep the spaces).
   A text that is a fragment of a sentence must stay a fragment that fits the same slot.
3. **Gender markers**: Spanish uses `[o|a]`, `[e|a]`, `[|a]`, `[él|ella]` inside words (`cansad[o|a]`, `jef[e|a]`). English
   has no gender there: drop the marker and write the neutral English word (`tired`, `boss`). If a marker must remain
   (he/she), write `[he|she]`, `[him|her]`, `[his|her]` with the same bracket-and-bar form.
4. **HTML and markup stay**: `<kbd>...</kbd>`, `<strong>`, `<a href="...">`, `\n`. Translate only the human text inside.
5. **Accelerators in buttons**: `&Anular` -> `&Cancel`, `&Sí` -> `&Yes`, `&No` -> `&No` (keep one `&` before a letter).
6. **Technical strings** (file names, formats, codes) are copied unchanged.
7. Do not add explanations, notes or quotes around the translation.

## Names: use the glossary

`traduccion/en/nombres.json` maps every proper name of the game (places, streets, towns, neighbourhoods, weapons,
vehicles, people) to its English form. **Always use it**, also when the name appears inside a longer sentence. If a name
is not in the glossary: people, towns, neighbourhoods, streets, gangs and brands keep their Spanish name; the generic
part of a business or institution is translated around the proper name (`Taberna La Sirena` -> `La Sirena Tavern`).

## Fixed terminology

| Spanish | English |
|---|---|
| nivel de búsqueda | wanted level |
| prestigio (entre los vecinos), ciudadanía | standing (with the neighbours) |
| fama (en la calle), reputación | street reputation |
| banda | gang |
| tu gente (de la banda) | your crew |
| barrio | neighborhood |
| territorio | territory |
| golpe (preparado) | heist |
| atraco | robbery / hold-up |
| encargo, contrato del tablón | job, contract (from the board) |
| misión | mission |
| móvil | phone |
| radar | radar |
| baliza | beacon |
| desvío (del GPS) | detour |
| conducción asistida / libre | assisted driving / free driving |
| piloto del GPS | GPS autopilot |
| taller | repair shop |
| garaje | garage |
| desguace | scrapyard |
| casa de empeños | pawn shop |
| concesionario | car dealership |
| náutica | boat dealer |
| afinidad | affinity |
| ánimo | mood |
| salud | health |
| blindaje | armor |
| vida realista | realistic life |
| dinero negro | dirty money |
| blanquear | launder |
| mercancía (sustancias) | product |
| camello | dealer |
| laboratorio | lab |
| proveedor | supplier |
| comisaría | police station |
| agente | officer |
| multa | fine |
| soborno | bribe |
| antecedentes penales | criminal record |
| contenido para adultos | adult content |
| vida social / sentimental | social life / love life |
| cita | date |
| quedar (con alguien) | meet up |
| pareja | partner |
| mochila | backpack |
| armario (de casa) | wardrobe |
| tapadera | front (business) |
| reconquista | reconquest |
| servidor | server |
| mod, editor de mods | mod, mod editor |
| euros | euros |
| metros, kilómetros | meters, kilometers |

## Keys and gamepad

| Spanish | English |
|---|---|
| Mayúsculas | Shift |
| Control | Ctrl |
| Alt | Alt |
| Intro | Enter |
| Escape | Escape |
| Espacio, barra espaciadora | Space |
| Tabulador | Tab |
| Retroceso | Backspace |
| Suprimir, Supr | Delete |
| Inicio / Fin | Home / End |
| Re Pág / Av Pág | Page Up / Page Down |
| flecha arriba / abajo / izquierda / derecha | up / down / left / right arrow |
| la tecla X, la X | the X key, X |
| la coma, el punto | comma, period |
| botón de combinar | combine button |
| gatillo izquierdo / derecho | left / right trigger |
| menú de acciones | actions menu |
| cruceta | D-pad |

Letter keys stay the same letter (the game's key bindings do not change with the language).

## Style

- Short, direct, spoken sentences. Second person ("you"). The screen reader says everything aloud: avoid symbols that
  read badly, avoid parentheses where a comma works.
- Spanish dialogue marks «...» become straight double quotes "...".
- Keep the tone: streetwise but friendly; Spanish slang becomes natural English with the same feeling, not literal.
- Numbers in words stay in words ("tres de nueve" -> "three of nine").
- Days of the week, months: English.
- Keep it consistent with the glossary and with the rest of your batch.
