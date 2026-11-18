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

Eliges personaje, o te creas el tuyo con su nombre, sus habilidades y su ventaja de salida, y decides si te hablan en masculino o en femenino. Con el primero te llamas Dani Roca y acabas de salir de la cárcel tras cumplir tres años por un robo que no cometiste. Vuelves a tu ciudad, Puerto Bravo, que ahora controla el empresario Octavio Belmonte. A partir de ahí, haz lo que quieras: sigue la historia, gánate la vida honradamente, hazte un nombre en la calle o dedícate a pescar. El juego no te obliga a nada.

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
- Más de 300 lugares de serie: casas, comercios, bancos, talleres, casinos, gimnasios, cines, hospitales, embarcaderos, helipuertos, paradas de tranvía, estaciones de tren, aeropuertos y monumentos, cada uno con su sonido y su descripción. Casi todos los locales y las casas se recorren por dentro, sala por sala.
- 75 misiones de serie entre la historia principal, las secundarias y cinco tutoriales jugables, y encargos que se repiten sin fin. Los mods añaden casi setenta. Hay misiones que se juegan de oído (seguir a alguien por sus pasos, vigilar, entrar sin hacer ruido, carreras con rivales) y decisiones que cambian lo que viene después: cuatro abren ramas distintas, con diez finales.
- 39 vehículos: coches, motos, bicicleta, camiones, vehículos de emergencias, barcos, un helicóptero y una avioneta. 22 armas, con silenciador y cargador ampliado.
- Transporte público: tranvía con paradas en todos los barrios de las ciudades y vías que se cruzan a pie, tren entre localidades, autobús, taxi y aviones de pasajeros, todos con trayecto.
- El mar se navega, y también se nada y se bucea.
- Policía con cinco niveles de búsqueda, día y noche, lluvia, tráfico con semáforos y peatones.

### Qué puedes hacer

- Vida honrada: oficina de empleo, oficios con ascensos (taxista, conductor de ambulancia y de autobús, bombero, gruista, mensajero, transportista, heladero, pescador), cursos, voluntariado y negocios propios.
- Vida delictiva: la historia, contratos, encargos de coches, atracos y guerras de territorio.
- Ocio: carreras y regatas, casino, bingo, lotería, siete y media, dominó, los chinos, boxeo, galería de tiro, pesca, búsqueda de tesoros, cine, recreativos y bolsa.
- Casas con garaje, un perro que te acompaña y busca objetos, guardaespaldas, banda propia, barrios que hay que defender, mejoras de vehículos en el taller, logros y habilidades que suben con la práctica.
- Hablar con cualquier persona de la calle: cada una tiene su nombre, su oficio y su carácter. Puedes preguntar, invitar a un café, hacer amigos o escribir lo que quieras decirle. Un modo opcional hace que contesten interpretadas por una inteligencia artificial: un modelo local gratuito y sin internet, Google AI Studio, OpenAI, Anthropic u otro servicio compatible. El juego elige solo el modelo más barato.
- Voces en las escenas: cada personaje de la historia y de los mods incluidos tiene su propia voz, generada por ordenador. Te llaman por el nombre del personaje con el que juegas y te hablan en masculino o en femenino; con un personaje creado por ti, las frases que dicen tu nombre se generan en tu equipo. Cualquiera puede poner sus propias grabaciones. Se quitan en las opciones.
- Dos motores de sonido: el clásico y uno envolvente, binaural, con eco distinto en cada sitio.
- Sin inteligencia artificial, una base de más de mil cien frases en casi setenta temas (`juego/respuestas.py`) contesta a lo que escribas, según el carácter de cada persona.
- Una ciudad que no se repite: cada día viene distinto (rebajas, mercado, fiesta, huelga, operación salida) y cambian los precios, la gente y el tráfico. Ninguna partida es igual a otra.
- Realismo a tu medida, todo opcional: hambre, sed, sueño e higiene; combustible con gasolineras; averías, pinchazos y revisiones; y normas de tráfico con multas y carné por puntos.
- Jugar en un servidor: un mundo que sigue vivo con jugadores de verdad, bandas, territorios, casas y negocios, y con el tráfico, la gente y la policía iguales para todos. Cualquiera puede montar el suyo: el servidor viene con el juego, con un panel accesible para llevarlo y una guía paso a paso.
- La radio se queda en pausa al bajarte y sigue donde quedó; con un reproductor con auriculares la oyes también a pie, y en los locales suena de fondo.
- Jugar con amigos, sin servidores de nadie: tu propio juego abre la partida, con o sin contraseña, y les das una dirección. Os oís, os encontráis con el radar y el GPS, os escribís, vais en el mismo coche, hacéis carreras con apuesta y repartos en equipo.
- Siete emisoras de radio con música original, una de noticias que comenta lo que haces y otra con tu propia música. Música de ambiente que cambia con la situación.
- Un modo opcional para mayores de 18 años, desactivado de serie: relaciones, vida nocturna, sustancias y sus consecuencias, contado sin escenas explícitas.

### Requisitos y arranque

- Windows 10 u 11.
- Auriculares estéreo.
- Un lector de pantalla abierto, como NVDA o JAWS. Si no hay ninguno, el juego habla con la voz de Windows.

Descarga la última versión, descomprime la carpeta donde quieras y ejecuta `PuertoBravo.exe`. No instala nada: es portable. Dentro del juego, `F1` dice las teclas en cualquier momento, y el menú principal abre el manual completo, que está en `data\docs\manual.html` y se navega por encabezados.

Si algo falla, el juego deja un registro de cada sesión en `data\logs`, sin datos personales: comprimes la carpeta de la sesión y la adjuntas a una [incidencia](https://github.com/hxebolax/PuertoBravo/issues), o la envías por Mastodon a [@HXeBoLaX](https://comunidad.nvda.es/@HXeBoLaX). El manual explica cómo.

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

Dependencias (`requirements.txt`): pygame-ce, numpy, sounddevice, soundfile, accessible-output2, wxPython, cx_Freeze y pytest. El modo IA no necesita ningún paquete: habla con los servicios por HTTPS con la biblioteca estándar (`juego/ia.py`), pregunta a cada uno su lista de modelos y elige el de la gama barata.

El repositorio incluye el audio: los sonidos por defecto y los cuatro packs en `data/sonidos` (el pack Envolvente se monta con `herramientas/crear_pack_envolvente.py`), la música de la radio en `data/radio` y la de ambiente en `data/musica`. Si falta algún sonido por defecto, el juego lo vuelve a generar al arrancar.

### Estructura

- `juego/`: el código del juego. `app.py` es el bucle y la pila de pantallas; `partida.py` reúne la partida a partir de módulos por tema (conducción, combate, misiones, trabajos, vida honrada, conversación, juego en red, azar diario...); `sintesis.py` genera los sonidos por defecto; `audio.py` es el mezclador con sonido posicional.
- `editor/`: el editor de mods, con wxPython.
- `herramientas/`: generación de sonidos y guías, protección y comprobación de la compilación, montaje de packs, mods de serie y publicación.
- `pruebas/`: pruebas automáticas con pytest.
- `data/datos/`: mapas, lugares, misiones, armas, vehículos, personajes y la gente de la calle con sus enemigos, en JSON.
- `data/mods/`: los mods de serie, en JSON legible.
- `data/docs/`: la documentación que se reparte con el juego, pensada solo para quien juega.
- `desarrollo/`: documentación técnica que no se reparte, como el formato de los archivos de mods.

### El servidor en línea

El servidor (`servidor/`) solo usa la biblioteca de serie de Python y funciona sin el juego, en Windows, Linux, Mac, un NAS o Docker. No trae el contenido: los lugares, las armas, los vehículos y las misiones se los da el juego del primero que entra con cada versión, firmados por quien publica, y en un mismo servidor conviven versiones distintas. Sus opciones están descritas en un solo sitio, `servidor/opciones.py`, del que salen el archivo de ejemplo, la validación, el diálogo de configuración del panel y la guía. El panel (`panel_servidor/`, `servidor_panel.py`) es una ventana wxPython que reutiliza la accesibilidad del editor de mods. Se arranca en desarrollo con `servidor.bat` o `servidor_panel.bat`. La guía de quien lo monta es `data\docs\servidor.html`. `herramientas\prueba_servidor_real.py` arranca un servidor de verdad como proceso aparte y le conecta diez clientes por la red.

Todo el contenido y todos los precios del juego están en los JSON de `data\datos` (lo más nuevo, en `vida.json`), y el editor de mods tiene una sección para cada cosa.

### Gente, enemigos, policía y cajas

`data/datos/gente.json` y `juego/gente.py` llevan todo lo que antes eran listas escritas en el código: los nombres, apellidos, oficios y frases de la gente, los caracteres, las bandas, el catálogo de tipos de enemigo, la tabla de la policía por nivel de búsqueda y la caja de cada tipo de local. `gente.configurar(datos)` se llama al final de `mundo.cargar_datos()`; lo que falte en los datos vale lo de serie. Lo que usa el resto del código:

- `gente.lista(cual)`, `gente.nombres(genero)`, `gente.oficio_para(edad, genero, rng)`, `gente.caracter(id)`.
- `gente.enemigo(grupo)` resuelve un grupo de un paso «eliminar» (con `clase`, o con nombre, arma y salud como siempre) y `gente.vestir(persona, ficha)` se lo pone a una `Persona`. `gente.grupo(clase, n, **serie)` escribe un grupo que vale aunque el tipo no esté en los datos.
- `gente.agentes_nivel(nivel)` da el tipo de agente de una patrulla; `gente.banda(nombre)` y `gente.tipos_de_banda(nombre)`, lo de las bandas.
- `gente.caja_local(tipo)` y, en la partida, `caja_de_local(lugar)`: lo que hay hoy en la caja y quién la guarda.
- `Partida.llegar_en_vehiculo(modelo, personas)` hace llegar a un grupo en un vehículo, con la misma conducción que las patrullas (`ia == "enemigos"`), y `bajar_enemigos(v)` los baja.

Las mejoras del taller (`juego/sistemas.py`) también salen de los datos: cada una dice su `efecto`, de la lista `sistemas.EFECTOS`, sus niveles y cuánto da cada nivel.

### Mis vehículos y el chófer

`juego/misvehiculos.py` (mixin `MisVehiculos` de la partida, y los menús del móvil):

- Un vehículo del jugador lleva `v.mio = True` y `v.mio_n` (orden de antigüedad). `Partida.hacer_mio(v)` lo marca: lo llaman la compra, la primera mejora del taller, sacar del garaje, que te lo traigan y ponerle nombre. `_poblar` no retira los marcados.
- Los de la localidad actual son vehículos vivos; los de las demás esperan como datos en `Partida.mis_lejos` (`mis_al_cambiar_mapa`, `_reponer_mis_vehiculos`). En la partida guardada van en `mis_vehiculos`, con `n` y, el último usado, `ultimo`; el que llevas puesto, en `veh` con `mio`. El número de formato no cambia: una versión anterior ignora las claves nuevas, y una partida anterior carga sin ellas (`mis_cargar`).
- `ultimo_veh` y `veh_fuera` siguen siendo «el último que has usado», sea tuyo o no; si es tuyo, no se duplica en `veh_fuera`.
- El tope (`vehiculos_propios.tope_calle` en `vida.json`) lo aplica `_tope_mis_vehiculos`.
- En un servidor no se marca ni se guarda nada (`hacer_mio` devuelve `False`): los vehículos de la calle son del servidor. El servidor añade a su respuesta de entrada `mis_vehiculos` (los identificadores de los aparcados a nombre de la cuenta) y acepta `nombre` en `veh_dejar`; un juego o un servidor anterior ignora las dos cosas. El juego lleva la cuenta en `sv["mios"]` y `sv_mis_vehiculos()`.
- Misiones: `mision_vehiculo(m)` y `mision_vehiculo_txt(m)` dicen qué pasa con el vehículo; con `vehiculo_libre`, el paso `robar` acepta el vehículo del jugador (`ms["veh_tuyo"]`) y `entregar` no se lo quita.
- Chófer: `Partida.chofer` es `None` o un diccionario con `estado` (`espera`, `viene`, `aqui`, `contigo`). El vehículo viene con `ia == "chofer"` (`_ia_chofer`); contigo dentro, `chofer_conduce()` hace que `piloto_puesto()` y `modo_asistido()` valgan aunque el jugador no tenga el piloto ni la conducción asistida, y `conducir` ignora los pedales. El vehículo de la banda lleva `tag == "banda"`; el de tu garaje, no lleva marca y es tuyo. No se guarda con la partida.

`mundo_servidor()` le cuenta además al servidor los nombres de sus personajes (`gente`) y las armas de sus agentes por nivel (`policia`). Son dos claves de más: un servidor anterior no las mira, y uno nuevo usa lo suyo si no vienen. La huella del mundo no depende de ellas, pero sí de las armas y los vehículos: al añadir unas u otros hay que regenerar `servidor/mundo.json` con `herramientas/exportar_mundo_servidor.py`.

### La calle: defensa propia, patrullas, rendición, helicóptero y guerra de barrios

- `juego/calle.py` (mixin `Calle` de la partida) reúne lo que pasa en la calle sin que el jugador lo busque. Los números y las frases salen de `vida.json`, sección `calle`; las opciones del jugador, de `config.py` (`defensa_propia`, `frases_reacciones`, `charla_peatones`, `soltar_municion`, `soltar_armas`, `patrullas_calle`, `ambulancias`, `helicoptero_policia`).
- Defensa propia: un enemigo que ataca sin haber sido tocado queda marcado (`p.agresor`, en `marcar_agresor`, que se llama desde `actualizar_personas` en el momento del ataque). Mientras haya un agresor vivo cerca, `_ruido_disparo` no apunta delito, y tumbarlo tampoco. `agente_auxilia` hace que un agente vaya a por él; `herir_por_otro` es la baja que no cuenta para el jugador. No vale para `tag` de misión ni de guerra.
- Voces por género: `calle.genero_de(p)` (la ficha si la hay; si no, el tono de voz) y `Calle.voz_persona`. `charla.ficha` da el género según ese mismo tono. `Calle.asustar` es el único sitio por el que un peatón pasa a huir.
- Las patrullas de ronda son vehículos con `ia == "policia"` y `ronda = True`; con cero estrellas los mueve `patrulla_sin_busqueda`, y con búsqueda, lo de siempre. Las que acuden a una pelea llevan `auxilio` (el momento en que desisten).
- La ambulancia es un vehículo con `ia == "ambulancia"` y `tag == "ambulancia"`; su estado está en `Partida.ambulancia`.
- Rendirse: `Calle.rendirse` pone `Partida.rendido`; `actualizar_personas` manda a los agentes a `agente_detiene`, y `detener(rendicion=True)` aplica la pena de `_pena_rendicion`.
- El helicóptero es un vehículo con `ia == "heli_policia"` y `volando = True`, que `actualizar_vehiculos` no mueve: lo lleva `Calle._helicoptero`. Todo lo que recorre vehículos para chocar, frenar o subir se salta los que llevan `volando`. `danar_vehiculo` lo desvía a `heli_danado`.
- `juego/guerra.py` (mixin `Guerra`) es el modo de guerra de barrios en la calle (`guerra_calle`, apagado de serie; sección `guerra_barrios`). `banda_guerra` da a cada barrio de ciudad una banda estable con la semilla de la partida; `miembro_de_barrio` decide quién sale a la calle en `_poblar`; el estado de la guerra en curso está en `Partida.guerra` y no se guarda.
- En un servidor: con policía común (`sv_policia_comun()`) no hay patrullas de ronda, ni helicóptero, ni rendición; en cualquier servidor no hay ambulancias, ni armas soltadas, ni guerra de barrios. No se ha tocado `servidor/`.
- Al reintentar una misión, `Misiones._rebobinar_jugador` devuelve al jugador a como estaba pero deja los garajes como están: los vehículos no vuelven atrás.

### Domicilio, atracos, pactos, contratos, gente que actúa, convivencia y oficio de policía

Ocho módulos de la 1.7.1, cada uno un mixin de `Partida` salvo `ajustes.py`:

- `juego/ajustes.py`: la clase `Ajustes(seccion, numeros, listas, cero)` lee de los datos una sección de un solo elemento (`{"id": "general", ...}`) con números y listas de frases, cada uno con su valor de serie. Cada módulo crea la suya (`AJ = Ajustes(...)`); `mundo.cargar_datos()` las pone al día con `ajustes.configurar_todos(d)`. `AJ("clave")` da el número, `AJ.lista("clave")` la lista y `AJ.frase("clave", hueco=valor)` una frase al azar con sus huecos rellenos.
- `juego/domicilio.py` (`Domicilio`): `casa_aqui()`, `pedir_domicilio(cosas)`, `actualizar_domicilio(dt)`. El pedido en camino va en `Jugador.pedido` y se guarda. Secciones `carta_domicilio` (lista) y `domicilio`; tarifa `domicilio_envio`.
- `juego/atracos.py` (`Atracos`): `atracar_local(l)` generaliza el atraco de las tiendas con `caja_de_local(l)`; `con_atraco()` añade la opción al menú de cualquier local con caja (lo llama `menus_juego.lugar`). `Jugador.locales_vetados` guarda lo que recuerda cada local y `entrada_vetada(l)` lo aplica al ir a entrar. `asaltar_proveedor(l)` es el asalto, con `Jugador.proveedores` (veto, precios) y `Jugador.represalias`. `mandar_enemigos(clase, n)` manda a por el jugador a enemigos de un tipo, en su vehículo si lo tienen. Sección `atracos`.
- `juego/pactos.py` (`Pactos`): `oferta_devolver`, `oferta_comprar`, `pedir_tributo`, `regatear`, `dia_pactos` (cada medianoche). `fuerza_propia()` y `rep_banda()` deciden; el azar de cada trato sale de la semilla de la partida, el día, la banda y el asunto, así que la respuesta es la misma todo el día. `Jugador.tributos` y `Jugador.tratos`. Sección `pactos`.
- `juego/contratos.py` (`Contratos`): `ofertas_contrato(l)` da los tres encargos del día; `empezar_contrato_de(l, oferta)` monta la misión con los pasos que ya existían (`eliminar`, `perseguir`, `seguir`, `escoltar`, `recoger`, `ir`). Sección `contratos` (lista; `situacion` es una de `contratos.SITUACIONES`). `Extras2.empezar_contrato` sigue siendo el contrato clásico. Un grupo de enemigos con `intimidar` se rinde en vez de caer (`Agente.se_rinde_con`, llamado desde `danar_persona`).
- `juego/reacciones.py` (`Reacciones`): `reaccion_tras(q, intencion, antes)` e `insistir(q)` son lo que la gente hace por su cuenta (opción `gente_actua`); `pedir_favor(q)` y `reclutar_persona(q)` son las opciones nuevas de la conversación. Quien acompaña al jugador lleva `estado == "sigue"` y lo mueve `paso_seguidor` desde `actualizar_personas`. `decidir_accion_ia(q, accion)` aplica las reglas del juego a lo que propone el modelo: `ia.py` solo acepta acciones de `ACCIONES` o, con la opción `ia_acciones`, de `ACCIONES_AMPLIADAS`; cualquier otra cosa es «nada», y en la lista no hay dinero ni objetos. Sección `reacciones`.
- `juego/convivencia.py` (`Convivencia`): `pedir_convivir(pers, casa)`, `saludo_de_casa`, `comer_en_casa`, `hacer_plan`, `peticion_cumplida(que)`, `dia_convivencia` (cada medianoche), `aventura_en_casa`. Estado en `Jugador.convive`, `convive_casa`, `convive_hoy` y `peticion_pareja`. Opción `pareja_convive`; los planes no dependen de ella. Secciones `planes_pareja` (lista) y `convivencia`. Las personas admiten `convivir` (`facil`, `si`, `nunca`).
- `juego/agente.py` (`Agente`): el turno es un trabajo (`Partida.trabajo` con `tipo == "policia"`), así que todo lo que ya miraba `trabajo` lo respeta. `empezar_turno`, `_aviso_nuevo`, `actualizar_agente`, `dar_alto`, `agente_intro`. `delito_de_servicio(puntos, texto)`, llamado desde `Combate.delito` después de comprobar que hay testigos, decide si es fuerza justificada, un apercibimiento o la expulsión. Estado del puesto en `Jugador.policia`; avisos resueltos en `stats["serv_policia"]`. Opción `oficio_policia`. Secciones `policia_oficio` y `avisos_policia` (lista; `tipo` es uno de `agente.TIPOS`); tarifa `academia_policia`.
- Tutoriales: el tipo de paso `practica` (`que`: `zarpar`, `timon`, `atracar`, `trabajar` o `servicio`; `metros` y `giro` para el timón) lo lleva `Misiones._paso_practica`. Un paso `ir` con `"exige": "radar"` no se cumple al llegar si no se ha usado el radar en ese paso (`ms["radar_usado"]`). Una misión con `"explicacion": true` no se juega: `Misiones.explicacion(m)` lee seguidos sus pasos de diálogo. Las voces grabadas se siguen buscando por misión, paso y frase, así que al tocar un tutorial hay que cuidar que cada grabación siga cayendo en su frase (hay una prueba que lo vigila).
- En un servidor en línea no existen el asalto a proveedores, la negociación con las bandas, el reclutamiento en la calle, la convivencia ni el oficio de policía; lo demás funciona igual. No se ha tocado `servidor/`, y la huella del mundo no cambia.
- Sonidos nuevos: `timbre` y `emisora` (`VERSION_CACHE` 19). En los packs llevan el sonido del juego.

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

### Procesadores antiguos: las dos numpy

La numpy oficial (2.4 en adelante) exige un procesador con las instrucciones de x86-64-v2 (SSE4.2, SSSE3, POPCNT y demás). En uno anterior, cargarla hace que Windows cierre el programa con el código 0xC000001D. Para Python 3.15 no hay ruedas de numpy anteriores a esa exigencia, así que el juego compilado lleva dos:

- `lib\numpy`: la oficial de PyPI, para los procesadores actuales.
- `lib_antiguo\numpy`: la misma versión, compilada sin exigencias con `-Dcpu-baseline=none` y sin BLAS. Sigue usando las instrucciones modernas cuando el procesador las tiene, porque las elige al arrancar.

`juego/procesador.py` pregunta a Windows qué instrucciones hay (`IsProcessorFeaturePresent`) antes de importar numpy y pone delante la carpeta que toca. Si la elegida no carga, prueba la otra; si no carga ninguna, el juego lo dice en voz alta y se cierra con normalidad. La variable de entorno `PUERTOBRAVO_NUMPY=antigua` (u `oficial`) fuerza una, para probar.

La rueda para procesadores antiguos está en `terceros/numpy_antiguo`, lista para usar: `compilar.bat` la coloca en la compilación con `herramientas/poner_numpy_antiguo.py`. Solo hay que rehacerla si cambia la versión de numpy o la de Python, con `herramientas\compilar_numpy_antiguo.bat`, que necesita Visual Studio con las herramientas de C++. numpy tiene licencia BSD de tres cláusulas.

### Los dos motores de sonido

`juego/audio.py` es el mezclador clásico: mezcla en Python con numpy, con paneo estéreo, retardo entre oídos y atenuación por distancia. `juego/audio_al.py` hereda de él toda la lógica y cambia solo la salida: mantiene una fuente de OpenAL Soft por cada sonido y deja que la biblioteca haga la mezcla en binaural (HRTF). Se llama por `ctypes`, sin paquetes de Python, así que no depende de la versión de Python. `audio_al.crear()` decide cuál se usa: el envolvente solo si el jugador lo ha elegido, la biblioteca está y el procesador es moderno; en cualquier otro caso, o si falla al arrancar, el clásico.

La biblioteca, `soft_oal.dll` (OpenAL Soft 1.25.2, LGPL), está en `terceros/openal_soft` con su licencia, y `compilar.bat` la copia a `lib`. `herramientas/probar_motor_envolvente.py` hace una prueba real con el dispositivo de sonido.

### El instalador de actualizaciones deja rastro

`juego/actualizador.py` escribe un `.bat` que sustituye el programa cuando el juego se ha cerrado. Ese `.bat` apunta cada paso en `data/logs/actualizacion.log`: `PASO nombre`, `RESULTADO nombre codigo=N` (el código de robocopy; 8 o más es fallo), `FALLO paso=... codigo=... motivo=...` y `TERMINADA bien` o `TERMINADA mal`. Robocopy escribe en ese mismo archivo, con `/log+`, solo los errores, con el archivo y el error de Windows. `leer_registro_instalador()` lo interpreta y `motivo_del_fallo()` lo convierte en una frase para quien juega; al reabrirse con `--actualizacion-fallida`, el juego la dice y la guarda para Opciones, Actualizaciones. `limpiar_registro_instalador()` deja cada ruta en el nombre del archivo, para que el registro se pueda enviar.

Antes de cerrar, `problemas_para_instalar()` comprueba que se puede escribir en la carpeta, que no hay otro programa del juego abierto (por la lista de procesos y probando a abrir cada `.exe` para escribir) y que hay sitio: `espacio_para_instalar()` suma la copia de seguridad, lo que crece cada archivo y un margen. Antes de descargar, `problema_para_descargar()` hace la cuenta con el ZIP, la versión extraída y la copia. Las pruebas (`pruebas/test_171_red_seguridad.py`) ejecutan el `.bat` de verdad sobre carpetas de pega, también con un archivo bloqueado; ninguna sale a internet.

### El motor de voz, con red de seguridad

El motor de `juego/vozgen.py` es código nativo: si el procesador no tiene lo que pide (AVX2, FMA y F16C), puede cerrar el proceso sin dar un error de Python. Por eso `disponible()` mira primero las tres capacidades (`capacidades()`: AVX2 se lo pregunta a Windows; FMA y F16C, a numpy) y, la primera vez, prueba el motor en un proceso aparte: el propio juego lanzado con `--probar-motor-voz`, que `main.py` atiende antes de abrir nada y que termina con 0, 10 (no carga) u 11 (no genera). Compilado con cx_Freeze es `PuertoBravo.exe --probar-motor-voz`; desde el código, `python main.py --probar-motor-voz`. El resultado se guarda en `data/voces_generadas/motor_probado.json` con la versión del juego y una huella de los archivos del motor, y se repite la prueba si cambia cualquiera de las dos. La prueba corre en segundo plano: mientras dura, `disponible()` contesta que no y `cuando_se_sepa()` avisa al terminar. Además, cada vez que el juego carga el motor dentro de su proceso lo apunta, y lo borra cuando ha generado la primera frase: si se cierra dos veces seguidas a medias, deja de intentarlo. `parar_prueba()` mata el proceso de prueba al cerrar el juego y antes de actualizar.

### Registro de sesión

`juego/registro.py` crea en `data/logs` una carpeta por sesión, con un máximo de cinco. Dentro quedan `sistema.txt` (versión, Windows, lector, sonido, mods, opciones), `sesion.log` (pantallas, teclas, todo lo que dice el juego, una foto del estado de la partida cada quince segundos, red, actualizaciones, fotogramas lentos y avisos), `errores.log` (cada error con su traza, el estado de la partida y las últimas teclas y sonidos) y `fallo_grave.log` si el proceso cae de golpe. Captura también las excepciones sin tratar del hilo principal y de los demás hilos.

Todo pasa por un filtro antes de escribirse: rutas del usuario, nombre de usuario y de equipo, direcciones IP y de internet, correos, claves y los nombres de los jugadores en red se sustituyen. Lo que se teclea en los cuadros de texto y los mensajes del chat no llegan a registrarse. Hay una prueba que juega una sesión con datos señuelo y falla si alguno aparece en la carpeta. Al añadir algo que maneje datos del jugador, usa `registro.privado()` o `registro.ocultar()`.

### Accesibilidad

La accesibilidad es el requisito principal del proyecto. Todo lo que ocurre en el juego tiene sonido propio y todo texto pasa por el lector de pantalla. Todas las teclas están en la ayuda (`F1`) y en el manual, que se generan a partir del mismo código. El editor sigue pautas de accesibilidad para wxPython: etiquetas asociadas a cada control, letras de acceso sin repetir, controles nativos y ayuda contextual con `Control+H`.

---

## 3. Crear mods

Un mod añade o cambia contenido sin tocar los datos originales: lugares, misiones con todos sus pasos, armas, vehículos, carreras, comidas, objetos, peces, personajes para elegir, capítulos, mapas enteros y, para el modo adulto, personas, planes, regalos y sustancias. Los mods están en `data\mods` y se cargan al arrancar. Una misión o un paso pueden depender de varias decisiones a la vez con `si_cruce` (`"concejal:1, trono:3"`), `si_cruce_min` y `si_cruce_max`, y una misión puede pedir una de cada rama con `requiere_alguna` (`"fd2 fd3 fd4; vd2 vd3"`). Cada mapa dice por dónde va la vía del tren con `tren_eje` y `tren_n`, y un lugar de tipo `aeropuerto` con `"aerodromo": true` es la pista corta de un pueblo. En cualquier texto, lo que cambia según el protagonista sea hombre o mujer se escribe entre corchetes, con la forma masculina, una barra y la femenina: `Bienvenid[o|a]`, `[el sobrino|la sobrina]`. Lo resuelve `juego/genero.py` justo antes de decir el texto.

### Con el editor

La forma normal es `EditorMods.exe` (o `editor.bat` desde el código fuente). Es una aplicación accesible con lector de pantalla: cada cosa se crea rellenando un formulario, `Control+H` explica el campo en el que estás y `F1` abre su manual (`data\docs\editor_mods.html`). Antes de guardar comprueba que todo lo que cita el mod existe, y avisa de lo que falta.

El editor guarda siempre protegido, como `.pbm`, que es lo que carga el juego compilado, y abre tanto los `.pbm` como los `.json`.

### A mano

Un mod también es un archivo JSON. El formato está explicado, con ejemplos, en `desarrollo/formato_de_los_mods.html`, y `desarrollo/ejemplo_mod.json` es un mod mínimo. Desde el código fuente, el juego carga directamente los `.json` de `data\mods`. El juego compilado no: avisa al arrancar y pide que el archivo se abra con el editor y se guarde, para que quede comprobado y protegido.

### Mods de serie

Vienen ocho, ya activados, que además sirven de modelo. Se generan con `herramientas/crear_mods_ejemplo.py`, donde se puede leer cómo está hecho cada uno:

- Bahía del Ocaso: una ciudad grande de costa, con seis barrios, tres bandas y una historia de veintiuna misiones (`herramientas/mod_bahia_ocaso.py`).
- Costa Dorada: un pueblo pesquero con su historia y un ejemplo de todo lo que admite un mod.
- Valdeolmos: un pueblo de viñas, con un fraude de vino y una carrera de tractores.
- Peñas Altas: un pueblo minero de montaña, con una mina que alguien explota de noche.
- Isla de los Vientos: una isla a la que se llega navegando, con raqueros y salinas.
- Noches de neón: la noche de Puerto Bravo, sin mapa nuevo, con taxis nocturnos y vida social.
- Oficios y recados: más vida honrada en Puerto Bravo.
- Motor y asfalto: coches, una moto, carreras y misiones al volante.

Para compartir un mod, pasa su archivo `.pbm`. Quien lo recibe lo copia en su `data\mods`.

Las misiones pueden llevar voces grabadas (`juego/voces.py`): archivos de sonido en `data\voces`, uno por frase. Las frases que dependen del protagonista tienen varias formas, con una arroba detrás del nombre: `m01_1_1@alex`, `m01_1_1@m`, `m01_1_2@alex_m`. El editor escribe el guion con el nombre de cada archivo y sus formas. No se aceptan mods con material de otros juegos ni voces clonadas de personas reales.

Las voces que trae el juego están generadas con Phonon 40m, un modelo de voz de [Gradium](https://gradium.ai/phonon) con licencia Creative Commons de reconocimiento y uso no comercial (CC BY-NC 4.0). El mismo modelo va con el juego, en `data\phonon`, para generar en el equipo de quien juega las frases que nombran a un personaje creado por él (`juego/vozgen.py`), con el paquete `ptts`, que es libre. El texto de la licencia está en `data\phonon\LICENCIA.txt`. El archivo del modelo, `model.q8.gguf`, pesa 95 megas y no está en este repositorio: `herramientas\preparar_phonon.py` lo copia de una carpeta con el modelo descargado de Hugging Face (`gradium/phonon-40m-multilingual`), y `compilar.bat` lo llama. Sin el modelo el juego funciona igual; esas frases las dice el lector de pantalla.

---

## 4. Packs de sonidos y de música

La guía completa, con la descripción y la duración de cada uno de los 237 sonidos, es `data\docs\cambiar_sonidos.html`. Resumen:

### Sonidos

- Todos los efectos están en `data\sonidos`, en subcarpetas. `por_defecto` tiene los de serie, un archivo por sonido; si borras alguno, el juego lo vuelve a crear. Cada una de las demás subcarpetas es un pack.
- El pack se elige dentro del juego, en Opciones, Sonido y música, y se oye al momento.
- Vienen tres packs completos: Realista y Alternativo, con grabaciones reales de dominio público, y Retro, con sonido de consola antigua. Los tres conservan el original en los sonidos de orientación (balizas, tonos, semáforos, radar y firmas de los lugares), porque de ellos depende moverse por el juego.
- Para hacer el tuyo, crea una carpeta en `data\sonidos` y copia dentro tus grabaciones con el nombre exacto del sonido que sustituyen: `claxon.wav`, `paso_acera0.ogg`. Los sonidos del juego están en FLAC, sin pérdida; los tuyos pueden ser WAV, OGG, FLAC o MP3. No hace falta traerlos todos: lo que falte suena con el original. Se admiten WAV, OGG, FLAC y MP3.
- Un archivo `pack.json` opcional da al pack su nombre, autor, licencia y retoques de volumen por sonido.
- El volumen se iguala solo: cada sonido cambiado se lleva al nivel del original, y el jugador puede subir o bajar cualquiera por separado desde Opciones.

### Música

- Radio: cada emisora tiene su archivo en `data\radio`. Una emisora puede tener varias canciones (`bravo.mp3`, `bravo_1.mp3`, `bravo_2.mp3`...), que van rotando. Cualquier otro archivo de audio que dejes ahí es una emisora nueva, y `data\radio\mi_musica` es la emisora con tu propia música. Las canciones de más de cinco minutos se leen y suenan por tramos de un minuto (`juego/musica.py`), así que una grabación de varias horas no ocupa más memoria que una canción corta.
- Ambiente: `data\musica` tiene una carpeta por situación (`menu`, `exploracion`, `noche`, `mar` y `tension`). Se usan todas las piezas que haya en cada una, al azar, se llamen como se llamen.
- Toda la música se nivela sola al cargarla, así que ninguna pista suena más fuerte que otra.

### Sonidos de terceros

Los packs Realista y Alternativo se montan con grabaciones de dominio público (licencia CC0) de kenney.nl, opengameart.org y bigsoundbank.com. Cada pack lleva un archivo `CREDITOS.txt` con el origen de cada sonido.

---

## Licencia

Licencia MIT: puedes usar, modificar y distribuir cualquier parte del juego, con la única condición de conservar el aviso de derechos y la licencia. Está en el archivo `LICENSE`.
