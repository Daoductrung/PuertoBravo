"""Escribe en adjuntos/prompts un archivo .txt por cada pista de música del juego, con el prompt
para pedírsela a una IA que genere música (Suno, Udio, Stable Audio u otra).

    .venv\\Scripts\\python.exe herramientas\\crear_prompts_musica.py

Cada archivo se llama como la pista que sustituye y dice en qué carpeta hay que guardar el resultado.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from juego import rutas          # noqa: E402

DEST = os.path.join(rutas.base(), "adjuntos", "prompts")

COMUN_AMBIENTE = ("Instrumental only, no vocals, no lyrics, no spoken words. Background music for an audio game played by blind people: "
                  "it must stay behind speech and sound effects, so keep it soft, low to mid register, no sharp transients, no sudden volume changes, "
                  "no sound effects, no sirens, no car horns, no beeps. Steady level from start to finish, seamless loop: the ending must flow back into the beginning. "
                  "About 2 minutes.")
COMUN_RADIO = ("Instrumental only, no vocals, no lyrics, no spoken words, no radio jingles, no DJ voice. A complete song for an in-game car radio station. "
               "Full, punchy mix, constant energy, no long quiet intro and no fade-out: it plays in a loop, so the ending must connect with the beginning. "
               "No sirens, car horns or tyre screeches in the music, because in the game those sounds mean something. About 3 minutes.")

# (archivo, carpeta de destino, título, para qué es, prompt en inglés, descripción en español)
PISTAS = [
    # ---- menú
    ("menu_1", "musica\\menu", "Menú principal, pieza 1", "Suena en el menú principal, antes de empezar a jugar.",
     "Slow cinematic neo-noir theme, 70 bpm, D minor. Warm electric piano, soft upright bass, brushed drums far in the background, a lonely muted trumpet melody with long notes. Mediterranean port city at dusk, bittersweet and elegant.",
     "Tema lento de cine negro moderno: piano eléctrico cálido, contrabajo suave, escobillas muy al fondo y una trompeta con sordina. Ciudad portuaria mediterránea al atardecer, agridulce y elegante."),
    ("menu_2", "musica\\menu", "Menú principal, pieza 2", "Suena en el menú principal.",
     "Laid-back Spanish guitar and Rhodes piano, 80 bpm, A minor. Nylon guitar arpeggios, soft shaker, deep round bass, distant strings pad. Calm, confident, a little mysterious, like a story about to begin in a coastal town.",
     "Guitarra española y piano Rhodes, relajado: arpegios de guitarra de nailon, shaker suave, bajo redondo y cuerdas lejanas. Tranquilo, seguro y algo misterioso."),
    ("menu_3", "musica\\menu", "Menú principal, pieza 3", "Suena en el menú principal.",
     "Downtempo trip-hop, 85 bpm, G minor. Dusty slow drum loop kept quiet, warm sub bass, vibraphone chords, soft saxophone phrases with a lot of space. Smoky, urban, late evening.",
     "Trip-hop lento: batería polvorienta y discreta, subgrave cálido, acordes de vibráfono y frases sueltas de saxo. Ambiente urbano y de última hora de la tarde."),
    ("menu_4", "musica\\menu", "Menú principal, pieza 4", "Suena en el menú principal.",
     "Slow synthwave ballad, 75 bpm, C major to A minor. Soft analog pads, gentle arpeggiator, clean chorus guitar melody, light electronic drums. Nostalgic 1980s sunset drive feeling, warm and hopeful.",
     "Balada synthwave lenta: colchones analógicos, arpegiador suave, guitarra limpia con chorus y batería electrónica ligera. Nostalgia de los ochenta, cálida y esperanzada."),
    # ---- exploración
    ("exploracion_1", "musica\\exploracion", "Explorar de día, pieza 1", "Suena de día cuando caminas o conduces con la radio apagada y no hay peligro.",
     "Gentle Mediterranean acoustic piece, 90 bpm, G major. Fingerpicked nylon guitar, light cajon, soft double bass, occasional accordion long notes. Sunny morning walk through a seaside town, relaxed and friendly.",
     "Pieza acústica mediterránea: guitarra punteada, cajón ligero, contrabajo y notas largas de acordeón. Paseo de mañana soleada por un pueblo de costa."),
    ("exploracion_2", "musica\\exploracion", "Explorar de día, pieza 2", "Suena de día cuando no hay peligro.",
     "Light bossa nova, 100 bpm, F major. Soft nylon guitar comping, brushed drums, warm bass, flute melody with long relaxed phrases. Airy, optimistic, strolling pace.",
     "Bossa nova ligera: guitarra de nailon, escobillas, bajo cálido y una flauta con frases largas. Aire optimista, ritmo de paseo."),
    ("exploracion_3", "musica\\exploracion", "Explorar de día, pieza 3", "Suena de día cuando no hay peligro.",
     "Chillout lo-fi groove, 82 bpm, E flat major. Mellow electric piano chords, soft kick and rim, round bass, clean jazz guitar licks, very subtle vinyl warmth without crackle noise. Easygoing city afternoon.",
     "Ritmo lo-fi relajado: piano eléctrico, bombo y aro suaves, bajo redondo y guitarra de jazz limpia. Tarde tranquila de ciudad."),
    ("exploracion_4", "musica\\exploracion", "Explorar de día, pieza 4", "Suena de día cuando no hay peligro.",
     "Soft funk-soul instrumental, 95 bpm, B flat major. Clean rhythm guitar, warm electric bass, light drums with closed hi-hat, small horn section playing soft sustained chords. Confident walk downtown, sunny and unhurried.",
     "Funk-soul suave: guitarra rítmica limpia, bajo eléctrico, batería ligera y metales en acordes largos. Paseo seguro por el centro, soleado y sin prisa."),
    # ---- noche
    ("noche_1", "musica\\noche", "De noche, pieza 1", "Suena de noche cuando no hay peligro.",
     "Late night jazz ballad, 60 bpm, C minor. Soft piano, upright bass, brushes, muted trumpet far away with reverb. Empty streets, streetlights, quiet and a little melancholic.",
     "Balada de jazz de madrugada: piano suave, contrabajo, escobillas y una trompeta con sordina a lo lejos. Calles vacías y farolas."),
    ("noche_2", "musica\\noche", "De noche, pieza 2", "Suena de noche cuando no hay peligro.",
     "Dark ambient synth, 65 bpm, F minor. Slow evolving warm pads, deep soft bass pulse, sparse electric piano notes, no drums. Night city seen from a rooftop, calm but watchful.",
     "Ambiente oscuro de sintetizador: colchones lentos, pulso grave suave y notas sueltas de piano eléctrico, sin batería. La ciudad de noche desde una azotea."),
    ("noche_3", "musica\\noche", "De noche, pieza 3", "Suena de noche cuando no hay peligro.",
     "Slow nocturnal flamenco-chill, 70 bpm, E phrygian. Solo nylon guitar with deep reverb, soft palmas far in the background, low string drone. Warm summer night in an old Spanish quarter.",
     "Flamenco chill nocturno: guitarra sola con mucha reverberación, palmas muy al fondo y un bordón grave de cuerdas. Noche de verano en un barrio viejo."),
    # ---- mar
    ("mar_1", "musica\\mar", "En el mar, pieza 1", "Suena cuando navegas con la radio apagada.",
     "Open sea ambient, 72 bpm, D major. Wide warm pads, slow harp arpeggios, soft cello melody, gentle swells in volume like slow waves, no drums, no water sound effects. Calm sailing, wide horizon.",
     "Ambiente de mar abierto: colchones amplios, arpegios lentos de arpa y un violonchelo suave, sin batería y sin efectos de agua. Navegación tranquila."),
    ("mar_2", "musica\\mar", "En el mar, pieza 2", "Suena cuando navegas.",
     "Maritime folk waltz, slow 3/4, 84 bpm, G major. Accordion, acoustic guitar, soft double bass, tin whistle melody. A small fishing boat leaving the harbour at dawn, gentle and nostalgic.",
     "Vals marinero lento: acordeón, guitarra acústica, contrabajo y flauta irlandesa. Un pesquero saliendo del puerto al amanecer."),
    ("mar_3", "musica\\mar", "En el mar, pieza 3", "Suena cuando navegas.",
     "Tropical chill, 88 bpm, A major. Soft steel pans, warm bass, light bongos, ukulele chords, relaxed marimba melody. Turquoise water, sun, no hurry.",
     "Chill tropical: steel drums suaves, bajo cálido, bongos ligeros, ukelele y marimba. Agua turquesa y sol."),
    # ---- tensión
    ("tension_1", "musica\\tension", "Tensión, pieza 1", "Suena cuando te persigue la policía o hay enemigos cerca.",
     "Tense action underscore, 125 bpm, D minor. Driving low synth bass ostinato, tight muted percussion, short staccato low strings, rising tension without ever exploding. Kept in the low and mid range, no high screeching sounds, no sirens.",
     "Fondo de acción tenso: ostinato grave de sintetizador, percusión seca, cuerdas graves cortas. La tensión sube pero no estalla. Sin agudos chillones ni sirenas."),
    ("tension_2", "musica\\tension", "Tensión, pieza 2", "Suena cuando te persigue la policía o hay enemigos cerca.",
     "Chase music, 140 bpm, E minor. Fast funk bass line, tight drums with dry snare, wah guitar stabs, low brass hits. 1970s car chase film style, urgent and focused.",
     "Música de persecución al estilo del cine de los setenta: bajo funk rápido, batería seca, guitarra con wah y golpes de metales graves."),
    ("tension_3", "musica\\tension", "Tensión, pieza 3", "Suena cuando te persigue la policía o hay enemigos cerca.",
     "Dark pulsing electronic thriller, 118 bpm, C minor. Deep sidechained bass pulse, ticking hi-hat kept quiet, low distorted synth drone, sparse piano hits. Stalking, nervous, relentless.",
     "Thriller electrónico oscuro: pulso grave, charles discreto como un tictac, zumbido grave de sintetizador y golpes sueltos de piano. Acecho nervioso."),
]

RADIO = [
    ("bravo", "Bravo FM, rock de carretera",
     "Driving road rock, 128 bpm, E major. Crunchy rhythm guitars, melodic lead guitar taking the place of the singer, solid bass, big steady drums, Hammond organ in the choruses. Classic American and Spanish highway rock of the 1980s, windows down, open road.",
     "Rock de carretera de los ochenta: guitarras rítmicas con cuerpo, una guitarra solista que hace de cantante, bajo firme, batería grande y órgano Hammond en los estribillos."),
    ("latina", "Onda Caribe, ritmos latinos",
     "Upbeat salsa and son instrumental, 96 bpm (clave 2-3), A minor. Piano montuno, congas, timbales, bongos, baby bass, bright trumpet and trombone section playing the melody. Dance floor in a Caribbean port, joyful and tight.",
     "Salsa y son instrumentales: montuno de piano, congas, timbales, bongos, bajo y una sección de trompetas y trombones llevando la melodía."),
    ("neon", "Neón 84, sintetizadores",
     "Synthwave, 108 bpm, F sharp minor. Gated reverb drums, pulsing analog bass, bright saw lead melody, lush pads, arpeggios. Neon lights, night highway, 1984.",
     "Synthwave: batería con reverberación cortada, bajo analógico pulsante, melodía de sintetizador brillante, colchones y arpegios. Luces de neón, 1984."),
    ("calma", "Radio Bahía, música tranquila",
     "Smooth easy listening, 78 bpm, E flat major. Soft electric piano, fretless bass, gentle drums with brushes, warm saxophone melody, light strings. Sunday afternoon by the bay, relaxing and tasteful.",
     "Música tranquila: piano eléctrico suave, bajo sin trastes, batería con escobillas, saxo cálido y cuerdas ligeras. Tarde de domingo junto a la bahía."),
    ("hierro", "Radio Hierro, rock duro de Monteferro",
     "Hard rock and classic heavy metal, 150 bpm, E minor. Heavy palm-muted riffs, twin lead guitar harmonies as the main melody, galloping bass, powerful double-kick drums. Mining town pride, loud and fast.",
     "Rock duro y heavy clásico: riffs pesados, dos guitarras solistas en armonía como melodía, bajo al galope y batería potente. Orgullo de ciudad minera."),
    ("club", "Lucero Club, electrónica",
     "Melodic house, 124 bpm, A minor. Four-on-the-floor kick, off-beat open hi-hat, rolling bass line, plucked synth melody, warm chord stabs, long filtered build-ups. Beach club at midnight, elegant and hypnotic.",
     "House melódico: bombo a negras, charles a contratiempo, línea de bajo rodante, melodía de sintetizador punteado y acordes cálidos. Club de playa a medianoche."),
    ("tropical", "Costa Tropical, verbena",
     "Spanish village fiesta pasodoble and cumbia medley feel, 112 bpm, C major. Brass band with trumpets, saxophones and trombones, accordion, festive drums with cowbell, simple catchy melody everyone could whistle. Summer festival in a small coastal town, happy and a bit cheesy.",
     "Verbena de pueblo, entre pasodoble y cumbia: charanga de trompetas, saxos y trombones, acordeón, batería festiva con cencerro y una melodía pegadiza. Fiestas de verano."),
]


def texto(titulo, para, destino, archivo, comun, ingles, espanol, extra):
    return "\n".join([
        titulo.upper(), "",
        "PARA QUÉ ES", "  " + para, "",
        "DÓNDE GUARDAR EL RESULTADO", f"  Carpeta: data\\{destino}", f"  Nombre:  {archivo}.wav (también vale .mp3, .ogg o .flac)", "  " + extra, "",
        "PROMPT, PARA COPIAR Y PEGAR EN LA IA DE MÚSICA", "  " + ingles + " " + comun, "",
        "LO MISMO EN ESPAÑOL, POR SI TU IA LO ENTIENDE MEJOR ASÍ", "  " + espanol + " Solo instrumental, sin voz ni letra. Volumen estable y final que enlace con el principio, porque suena en bucle.", "",
        "CONSEJOS",
        "  Si la IA tiene una casilla de «instrumental», márcala.",
        "  Si el resultado trae voz, efectos de sonido o un silencio largo al principio, vuelve a generar.",
        "  Recorta el silencio del principio y del final antes de copiar el archivo al juego.",
        "  No pidas «al estilo de» ningún artista ni canción concretos: los prompts ya describen el estilo sin nombrar a nadie.",
        "  Comprueba la licencia de tu IA de música antes de distribuir el juego con sus pistas.", ""])


def generar():
    os.makedirs(DEST, exist_ok=True)
    for f in os.listdir(DEST):
        if f.endswith(".txt"):
            os.remove(os.path.join(DEST, f))
    n = 0
    for archivo, carpeta, titulo, para, ingles, espanol in PISTAS:
        extra = "Sustituye a la pieza de serie del mismo nombre. Puedes generar más piezas y copiarlas en la misma carpeta con otro nombre o con el número siguiente: se usan todas, al azar. El juego nivela el volumen solo."
        with open(os.path.join(DEST, f"musica_{archivo}.txt"), "w", encoding="utf-8-sig", newline="\r\n") as f:
            f.write(texto(titulo, para, carpeta, archivo, COMUN_AMBIENTE, ingles, espanol, extra))
        n += 1
    for ident, nombre, ingles, espanol in RADIO:
        extra = "Sustituye a la música de serie de esa emisora. Para tener más canciones, guarda otras con cualquier nombre en data\\radio: cada archivo nuevo es una emisora más."
        with open(os.path.join(DEST, f"radio_{ident}.txt"), "w", encoding="utf-8-sig", newline="\r\n") as f:
            f.write(texto("Emisora " + nombre, "Suena en la radio de los vehículos, en la emisora " + nombre + ".", "radio", ident, COMUN_RADIO, ingles, espanol, extra))
        n += 1
    with open(os.path.join(DEST, "LEEME.txt"), "w", encoding="utf-8-sig", newline="\r\n") as f:
        f.write("\n".join([
            "PROMPTS PARA GENERAR LA MÚSICA DE PUERTO BRAVO CON UNA IA", "",
            f"Hay {n} archivos, uno por pista. Cada uno trae el prompt listo para copiar, en inglés y en español,",
            "y dice en qué carpeta del juego y con qué nombre hay que guardar el resultado.", "",
            "MÚSICA DE AMBIENTE, la que suena con la radio apagada (carpeta data\\musica)",
            "  musica_menu_1 a musica_menu_4                 El menú principal.",
            "  musica_exploracion_1 a musica_exploracion_4   De día, sin peligro.",
            "  musica_noche_1 a musica_noche_3               De noche, sin peligro.",
            "  musica_mar_1 a musica_mar_3                   Navegando.",
            "  musica_tension_1 a musica_tension_3           Con la policía detrás o enemigos cerca.", "",
            "RADIO, la que suena en los vehículos (carpeta data\\radio)",
            "  radio_bravo, radio_latina, radio_neon, radio_calma, radio_hierro, radio_club y radio_tropical.",
            "  La emisora de noticias es hablada y la emisora Mi música es la tuya: no necesitan prompt.", "",
            "CÓMO USARLOS",
            "  1. Abre el archivo de la pista y copia el párrafo de PROMPT.",
            "  2. Pégalo en tu IA de música y marca «instrumental» si tiene esa opción.",
            "  3. Descarga el resultado, ponle el nombre que indica el archivo y cópialo en la carpeta que indica.",
            "  4. Abre el juego. La música se carga al arrancar.",
            "  Si borras una pista, el juego vuelve a componer la suya de serie.", "",
            "Estos archivos los escribe herramientas\\crear_prompts_musica.py. Si se añade una situación o una emisora",
            "al juego, se añade allí su prompt y se vuelve a ejecutar.", ""]))
    return n


if __name__ == "__main__":
    print(generar(), "prompts escritos en", DEST)
