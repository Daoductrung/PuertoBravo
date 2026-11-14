"""Base de respuestas, segunda parte: ocio, opiniones, el jugador y la conversación en sí."""
from .respuestas import T

T("que_haces", "que haces|que estas haciendo|que haces aqui|a donde vas|adonde vas|donde vas|esperas a alguien|que haces por aqui|vas a algun sitio|tienes prisa", [
    "Aquí, dando una vuelta. Hay que estirar las piernas.", "Voy a por el pan y vuelvo. Lo de todos los días.", "Espero a un amigo que siempre llega tarde.", "Nada. Mirar a la gente pasar, que es gratis.",
    "Vengo de trabajar y voy a casa. Sin más.", "Hacer tiempo. Tengo que recoger una cosa y no han abierto.", "Tomar el aire. En casa se me caen las paredes encima.",
    "Voy al mercado, a ver qué hay hoy.", "Iba al banco, pero he visto la cola y se me han quitado las ganas.", "De paseo. A estas horas se está bien en {barrio}."],
  amable=["Paseando un poco. ¿Y tú, qué haces por {barrio}?", "Nada importante. Tengo un rato si quieres hablar."],
  hablador=["Pues iba a la farmacia, pero me he encontrado a la Paqui, luego al del quiosco, luego a ti... A este paso llego mañana."],
  seco=["Nada.", "Lo mío."], timido=["Nada... solo pasaba por aquí."], chulo=["Lo que me da la gana.", "Dejarme ver. Que la gente lo agradece."], poca=["¿Me estás vigilando?", "Lo que no te importa."], flojo=True)

T("recomienda", "que me recomiendas|que se puede hacer|que hay que ver|que hay para hacer|algo divertido|donde me divierto|que hago aqui|me aburro|estoy aburrido|estoy aburrida|un plan|planes", [
    "Si tienes dinero, el casino. Si no, la playa, que es gratis.", "Una vuelta por el puerto al atardecer. Eso no falla.", "Hay cine, hay feria, hay bares. Aburrirse aquí tiene mérito.",
    "Prueba a pescar. Engancha, y nunca mejor dicho.", "Dicen que en la playa hay quien busca tesoros con un detector. Y encuentran.", "Las carreras de noche, si te gusta el motor. Yo no te he dicho nada.",
    "En el gimnasio hay combates. Se apuesta y todo.", "Compra un décimo. Por soñar no cobran.", "Si te aburres, apúntate a un curso en la academia.", "Habla con la gente. Cada uno tiene una historia."],
  amable=["A mí me gusta pasear por {barrio}. Pruébalo, ya verás.", "Si quieres ayudar, en el comedor social siempre hacen falta manos."],
  hablador=["Mira, por la mañana el mercado, a mediodía un arroz en el puerto, por la tarde la siesta, que es sagrada, y por la noche lo que surja. Ese es mi plan perfecto y no lo cambio."],
  seco=["Hay bares.", "Tú sabrás qué te gusta."], timido=["A mí me gusta el cine... no hay que hablar con nadie."], chulo=["Quédate conmigo y aprende.", "El casino. Si te atreves."])

T("cine_tele", "el cine|una pelicula|las peliculas|la tele|la television|una serie|las series|que ves|has visto|un libro|los libros|leer|lees", [
    "Voy al cine cuando echan algo de tiros. Lo demás me duerme.", "La tele solo da disgustos.", "Yo leo el periódico y gracias.", "Me gusta leer, pero me quedo dormid{o} en la segunda página.",
    "Las películas de antes sí que eran buenas.", "Estoy enganchad{o} a una serie. No me preguntes cuál, que me da vergüenza.", "En el cine de aquí las palomitas cuestan más que la entrada.",
    "Un buen libro y el ruido del mar. No pido más."],
  amable=["Me encanta el cine. Si echan algo bueno, avísame."], hablador=["Fui a ver una de miedo y el que más gritaba era yo. La de delante se cambió de sitio."],
  seco=["No veo nada.", "La tele. Poco."], timido=["Leo mucho... me gusta más que salir."], chulo=["De mi vida sí que harían una película.", "Yo no veo películas. Las vivo."])

T("juego_suerte", "el casino|la ruleta|apostar|las apuestas|jugar a las cartas|el poker|la loteria|un decimo|el gordo|el bingo|la suerte|tienes suerte|mala suerte|buena suerte", [
    "En el casino solo gana la casa. Y el del guardarropa.", "Llevo veinte años jugando al mismo número. Algún día tocará.", "La suerte es para el que la busca. Y para algún enchufado.",
    "Yo no juego. Bastante lotería es la vida.", "Una vez me tocó el reintegro. Lo celebré como si fuera el gordo.", "Mi cuñado perdió el coche en una partida. Ahora va en autobús y saluda.",
    "Si te toca, acuérdate de mí.", "Suerte, la justa. Pero no me quejo.", "El bingo de los jueves es lo más emocionante de mi semana."],
  amable=["Mucha suerte si juegas. Pero con cabeza, ¿eh?"], hablador=["Soñé con el 47 y lo jugué. Salió el 48. Desde entonces no me fío ni de mis sueños."],
  seco=["No juego.", "Tirar el dinero."], timido=["Nunca he jugado... me daría algo perder."], chulo=["Yo no necesito suerte. Tengo talento.", "A mí las cartas me quieren."])

T("armas_pelea", "un arma|las armas|una pistola|llevas arma|una navaja|sabes pelear|te pegas|una pelea|pegarme|te pego|disparar|un tiro", [
    "De armas no quiero saber nada.", "Aquí el que saca un arma acaba mal. Siempre.", "Yo me peleé una vez, de joven. Perdí. Fin de la historia.", "Guarda eso, que no estamos para sustos.",
    "Las armas las carga el diablo.", "En la armería venden de todo, con papeles o sin ellos, según a quién preguntes.", "Yo, las manos en los bolsillos. Así no me meto en líos.",
    "Pelear es de tontos. Correr es de listos."],
  amable=["Por favor, nada de peleas. No merece la pena."], hablador=["Mi abuelo tenía una escopeta de caza colgada en el salón. Nunca disparó. Decía que era para asustar a los cobradores."],
  seco=["No quiero líos.", "Ni las toco."], timido=["No... por favor, no quiero problemas."], chulo=["Yo no necesito armas. Me basto solo.", "¿Pelear? Cuando quieras y donde quieras."],
  poca=["Aléjate de mí.", "Voy a llamar a alguien."], confianza=-1)

T("ayuda", "me ayudas|ayudame|necesito ayuda|un favor|hazme un favor|me echas una mano|puedes ayudarme|necesito que", [
    "Depende de para qué. Dime.", "Si está en mi mano, sí. Si no, te digo quién.", "Ayudar, ayudo. Meterme en líos, no.", "Uf, hoy voy liad{o}. Pero cuéntame.",
    "Favores hago los justos, que luego se acostumbran.", "Si buscas un sitio, pregúntame dónde hay lo que necesites. Eso sí te lo sé decir.", "Mientras no sea dinero ni mudanzas, lo que quieras.",
    "Dime qué necesitas y vemos."],
  amable=["Claro que sí. Dime qué necesitas.", "Para eso estamos. Cuéntame."], hablador=["¿Un favor? Cuenta, cuenta. Yo le hice uno a mi vecino y acabé pintándole el piso entero."],
  seco=["¿Qué quieres?", "Según."], timido=["Si puedo... no sé si sabré."], chulo=["Yo no hago favores. Hago negocios.", "Depende de lo que saque yo."],
  poca=["A ti no te ayudo ni a cruzar la calle.", "Búscate la vida."], mucha=["Para ti, lo que haga falta, {tu}. Ya lo sabes."])

T("consejo", "un consejo|que harias tu|que me aconsejas|aconsejame|que hago|no se que hacer|tu que harias|que opinas|que piensas|tu opinion", [
    "Yo que tú, no me complicaría la vida.", "Haz lo que te pida el cuerpo. Y luego arrepiéntete, como todos.", "Mi consejo: come bien, duerme bien y no debas dinero.",
    "Consejos vendo, que para mí no tengo.", "Piénsalo dos veces. Y luego una tercera.", "No te fíes de quien te promete mucho.", "Lo que tengas que hacer, hazlo de día.",
    "Trabaja honradamente. Se duerme mejor.", "Pregunta a los mayores. Saben más de lo que parece."],
  amable=["Yo creo que harás lo correcto. Se te ve buena persona.", "Hazle caso a tu conciencia. No suele fallar."],
  hablador=["Mi madre decía: antes de hablar, cuenta hasta diez. Yo nunca he pasado de tres, y así me va."], seco=["Tú verás.", "Cada uno, lo suyo."],
  timido=["No sé... yo no soy quién para aconsejar."], chulo=["Haz lo que yo haría: lo mejor.", "Hazme caso y no fallarás."], flojo=True)

T("quien_soy", "sabes quien soy|me conoces|te sueno|has oido hablar de mi|que dicen de mi|que se dice de mi|soy famoso|soy famosa|que piensas de mi|que opinas de mi|te caigo bien|te caigo mal", [
    "Me suena tu cara, pero no caigo.", "Algo he oído. Aquí se sabe todo.", "No sé quién eres, pero pareces buena gente.", "Dicen cosas. Unas buenas y otras no tanto.",
    "Te he visto por {barrio} más de una vez.", "Yo no juzgo a nadie por lo que cuentan.", "Eres el que ha vuelto hace poco, ¿no? Eso dicen.", "De ti no sé nada, y casi mejor."],
  amable=["Pareces buena persona. Con eso me basta.", "Me caes bien, la verdad."], hablador=["De ti se dice de todo. Que si vienes de lejos, que si has estado a la sombra... Yo, como digo siempre: hasta que no lo vea, no lo creo."],
  seco=["No.", "Ni idea."], timido=["No... perdona, no te conozco."], chulo=["Aquí el conocido soy yo.", "No eres tan famoso como te crees."],
  poca=["Sé quién eres. Por eso no quiero hablar contigo.", "Lo que he oído de ti no es bueno."], mucha=["Claro que sí, {tu}. Eres de los pocos de fiar que quedan."])

T("carcel_pasado", "la carcel|he estado en la carcel|estuve preso|estuve presa|la prision|sali de la carcel|mi pasado|un error|me arrepiento|soy inocente|no lo hice", [
    "Cada uno carga con lo suyo.", "Todo el mundo merece otra oportunidad. O eso dicen.", "De ahí se sale peor o mejor. Tú sabrás.", "Yo no pregunto por el pasado de nadie.",
    "Lo hecho, hecho está. Ahora, mirar adelante.", "Mi primo estuvo dentro. Salió y ahora tiene una frutería.", "Si dices que eres inocente, yo te creo. No gano nada con no creerte.",
    "Aquí se olvida pronto. O se hace como que se olvida."],
  amable=["Lo importante es lo que hagas a partir de ahora.", "Me alegro de que estés fuera. Ánimo."], seco=["No pregunto.", "Allá tú."],
  timido=["Ah... lo siento. No sabía."], chulo=["A mí no me asusta un ex presidiario.", "Yo he conocido a peores."], hablador=["Uy, eso es duro. Mi tío estuvo tres meses por una tontería y salió sabiendo jugar al mus como nadie."],
  poca=["Con razón. Ya decía yo.", "No me extraña."], confianza=0)

T("futuro_suenos", "tus suenos|que suenas|el futuro|que quieres ser|que te gustaria|tu sueno|planes de futuro|si fueras rico|si te tocara|jubilarte|la jubilacion", [
    "Una casita con vistas al mar y que no me llame nadie.", "Que me toque la lotería y no volver a madrugar.", "Yo ya no sueño. Me conformo con llegar a fin de mes.",
    "Me gustaría viajar. No he salido de la comarca.", "Jubilarme con salud. Lo demás me sobra.", "Poner un bar. Todo el mundo quiere poner un bar.",
    "Que mis hijos vivan mejor que yo.", "Un barco pequeño. Para salir yo sol{o}, sin nadie.", "El futuro, ya veremos. Bastante tengo con el presente."],
  amable=["Con tener salud y a los míos cerca, ya está cumplido."], hablador=["Yo quería ser cantante, luego torero, luego astronauta. He acabado de {oficio}. No está mal, pero no es lo mismo."],
  seco=["Que me dejen tranquil{o}.", "Nada."], timido=["Me gustaría... no sé, que no me diera vergüenza todo."], chulo=["Yo no sueño. Yo consigo.", "Ser el dueño de todo esto. Y lo seré."])

T("amor", "el amor|estas enamorado|estas enamorada|te has enamorado|me he enamorado|mi novia|mi novio|mi ex|me han dejado|corazon roto|te quiero", [
    "El amor es como el levante: viene cuando quiere y te despeina.", "De eso sé poco. He acertado una vez de cinco.", "Si te han dejado, que les den. Hay más peces en el mar.",
    "Yo ya estoy mayor para esos sustos.", "Enamorarse está bien. Lo malo viene luego.", "Mi abuelo cortejó a mi abuela cuatro años. Ahora en cuatro días ya se han dejado.",
    "El tiempo lo cura todo. Menos las hipotecas."],
  amable=["Qué bonito es eso. Ojalá te vaya muy bien.", "Si te han hecho daño, lo siento. Pasará."], hablador=["Yo me enamoré a los quince de la hija del panadero. Engordé seis kilos de ir a comprar pan."],
  seco=["No es lo mío.", "Bah."], timido=["Eh... yo de eso... no sé nada."], chulo=["De mí se enamoran. Yo no.", "He roto más corazones que platos."])

T("miedo_noche", "tienes miedo|me da miedo|que miedo|de noche|por la noche|la noche|es peligroso de noche|sales de noche|a oscuras|la madrugada", [
    "De noche, todos los gatos son pardos. Y algunos muerden.", "Yo a las diez estoy en casa. Lo que pase fuera no es cosa mía.", "La noche tiene su gente. No es la misma que de día.",
    "Miedo no, respeto.", "De madrugada solo quedan los taxis y los que no deberían estar.", "Antes salía. Ahora me da pereza hasta bajar la basura.",
    "Si sales de noche, ve por las calles con luz."],
  amable=["Ten cuidado cuando oscurezca, por favor."], hablador=["Una noche oí un ruido en la escalera y bajé con la sartén. Era mi vecino, que había perdido las llaves. Casi le abro la cabeza."],
  seco=["No salgo.", "Miedo ninguno."], timido=["Sí... a mí me da miedo. Mucho."], chulo=["La noche es mía.", "El miedo no lo conozco."])

T("noticias", "las noticias|el periodico|que ha pasado|te has enterado|has oido lo de|lo ultimo|que novedades|que hay de nuevo|algo nuevo", [
    "El periódico lo cuenta todo, menos lo importante.", "Yo me entero de todo en el bar. Es más fiable.", "Pregúntame qué se cuenta por ahí y te digo lo último.",
    "Siempre pasa algo, pero nunca cambia nada.", "No leo las noticias. Para disgustos, ya tengo la factura de la luz.", "Dicen que va a haber movida en el puerto. Dicen.",
    "Lo de siempre: suben los precios y bajan los sueldos."],
  amable=["No estoy muy al día, pero si me entero de algo te lo cuento."], hablador=["¿Que si me he enterado? Yo me entero antes que el periódico. Tengo a mi cuñada, que es mejor que una agencia."],
  seco=["No sé nada.", "Lo de siempre."], timido=["No me entero de nada, la verdad..."], chulo=["Las noticias las sé yo antes de que pasen."], flojo=True)

T("movil", "el movil|tu telefono|internet|las redes|el ordenador|la tecnologia|un mensaje|llamar por telefono|whatsapp|las pantallas", [
    "Yo el móvil lo uso para llamar. Lo demás no lo entiendo.", "Los críos no levantan la vista de la pantalla.", "Antes quedábamos en la plaza. Ahora, por mensaje.",
    "Se me ha roto la pantalla tres veces este año.", "Internet es como el bar, pero sin tapas.", "Mi nieto me enseñó a mandar fotos. Ahora las mando todas torcidas."],
  hablador=["Me metí en un grupo de vecinos por el móvil y ahora me entero de cosas que preferiría no saber. La del segundo riega a las tres de la mañana."],
  seco=["Lo justo.", "No me gusta."], timido=["Yo prefiero escribir que hablar... por eso me gusta."], chulo=["Tengo el último modelo. Como debe ser."], amable=["Viene bien para hablar con la familia que está lejos."])

T("religion", "la iglesia|vas a misa|crees en dios|dios|rezar|rezas|el cura|los santos|ir al cielo|la virgen", [
    "Voy a misa en fiestas y en funerales.", "Yo creo en lo que veo. Y a veces ni eso.", "La iglesia de aquí tiene unas campanas que despiertan a un muerto.",
    "Cada uno, con sus creencias. Yo respeto.", "Mi madre reza por los dos.", "El cura es buena gente. Juega al dominó mejor que nadie."],
  amable=["Creer en algo ayuda. En lo que sea."], seco=["No hablo de eso.", "Allá cada cual."], timido=["Yo... rezo a veces. Cuando tengo miedo."],
  chulo=["Dios y yo nos entendemos.", "A mí que no me sermoneen."], hablador=["El cura de antes daba unos sermones de hora y media. El de ahora, quince minutos y a casa. Hemos salido ganando."])

T("compras_ropa", "las tiendas|ir de compras|comprar ropa|tu ropa|vas muy elegante|vas muy guapo|vas muy guapa|que ropa|la moda|el supermercado|hacer la compra", [
    "Yo compro en la tienda de siempre. Me fían y todo.", "La ropa, en rebajas o nada.", "Esto me lo regaló mi cuñada. Por eso me queda grande.",
    "Las tiendas del centro son para turistas.", "En el mercado se compra mejor y más barato.", "Hacer la compra es mi deporte. Cargo como una mula.",
    "Gracias. Uno se arregla lo que puede."],
  amable=["Qué amable. Tú también vas muy bien."], hablador=["Fui a por unos calcetines y volví con una chaqueta, dos camisas y sin calcetines. Así soy yo."],
  seco=["Compro lo justo.", "Es ropa."], timido=["Gracias... es vieja."], chulo=["Lo que yo me pongo, se pone de moda.", "Elegante es poco."])

T("casa_alquiler", "tu casa|donde vives|el alquiler|los pisos|comprar una casa|la hipoteca|un piso|vivienda|los alquileres|el casero", [
    "Vivo aquí cerca. Un piso pequeño, pero mío. Bueno, del banco.", "Los alquileres están imposibles. Pagas más por menos.", "Mi casero no arregla ni una bombilla.",
    "Hay casas en venta, si tienes con qué. Te dan garaje y todo.", "Vivo en {barrio}. No digo el número, por si acaso.", "La hipoteca la acabo de pagar a los ochenta, si llego.",
    "Antes un piso costaba lo que hoy un coche."],
  amable=["Vivo aquí al lado. Es humilde, pero se está a gusto."], hablador=["Mi piso tiene cuarenta metros y vivimos cuatro. Para pasar al baño hay que pedir turno, como en la carnicería."],
  seco=["Por aquí.", "En un piso."], timido=["Cerca... prefiero no decir dónde."], chulo=["Vivo en lo mejor de {barrio}. No podía ser de otra forma."], poca=["¿Para qué quieres saber dónde vivo?"])

T("agua_sequia", "la sequia|el agua|no hay agua|cortan el agua|las cisternas|el grifo|la lluvia que no|sin llover|la desaladora|el cauce", [
    "Tres años sin llover como Dios manda. Esto no es normal.", "El agua vale ya más que el vino.", "Dos horas de grifo al día. Y dando gracias.",
    "En la colina riegan los jardines mientras aquí hacemos cola con garrafas.", "Dicen que la empresa del agua hace lo que quiere.", "Yo lleno cubos cuando sale, por si acaso.",
    "El día que llueva, salimos todos a la calle a mojarnos."],
  amable=["Si te falta agua, en el comedor vecinal reparten."], hablador=["Mi vecina guarda el agua de fregar para la cisterna y la de la cisterna para las plantas. Las plantas no sé cómo siguen vivas."],
  seco=["No hay.", "Mal."], timido=["Es... preocupante. Yo ahorro la que puedo."], chulo=["A mí nunca me falta. Tengo mis contactos."])

T("ricos_jefes", "los ricos|los jefes|los de arriba|los empresarios|los poderosos|los bancos|el banco|los banqueros|la injusticia|no es justo", [
    "Los de arriba no pisan la calle. Por eso no saben nada.", "El banco te da un paraguas cuando hace sol y te lo quita cuando llueve.", "Siempre ganan los mismos.",
    "Justicia hay. Para el que puede pagarla.", "Aquí el que tiene, tiene, y el que no, aguanta.", "Yo no envidio a los ricos. Bueno, un poco.",
    "Mientras unos tienen tres casas, otros no tienen ni una."],
  hablador=["Fui al banco a pedir un préstamo y me pidieron tantos papeles que al final les dejé yo dinero a ellos, de comisiones."], seco=["Lo de siempre.", "Así es."],
  timido=["No es justo... pero qué vamos a hacer."], chulo=["Algún día seré yo el de arriba.", "A esos los tengo calados."], amable=["Hay de todo. También hay gente con dinero que ayuda."])

T("tabaco", "tienes fuego|un cigarro|fumas|tienes tabaco|un pitillo|el tabaco|fumar", [
    "No fumo. Lo dejé cuando subieron el precio.", "Toma fuego. El tabaco, no, que es el último.", "Eso te va a matar. Y a mí de envidia.", "Fumo, pero solo en fiestas. Y en días de diario.",
    "No tengo. Pregunta en el bar.", "Lo dejé hace diez años. Sueño con él todas las noches."],
  amable=["No fumo, lo siento. Y tú deberías dejarlo, que eres joven."], seco=["No fumo.", "No."], timido=["No... no fumo."], chulo=["Yo fumo puros. Eso es para aficionados."],
  hablador=["Lo dejé tres veces. La primera duré un mes, la segunda una semana y la tercera, hasta el café de la tarde."])

T("gracias", "gracias|muchas gracias|te lo agradezco|muy amable|eres muy amable|que amable|te debo una", [
    "De nada, hombre.", "No hay de qué.", "Para eso estamos.", "Nada, nada.", "A mandar.", "No las merece.", "Hoy por ti y mañana por mí.", "Faltaría más."],
  amable=["De nada. Ha sido un placer.", "Gracias a ti por la conversación."], hablador=["De nada. Y cuando quieras otro rato de charla, ya sabes dónde encontrarme. Bueno, no lo sabes, pero estoy siempre por aquí."],
  seco=["Nada.", "Ya."], timido=["De nada... no ha sido nada."], chulo=["Ya me lo pagarás.", "Lo sé. Soy así de generos{o}."], mucha=["Entre nosotros no hacen falta las gracias, {tu}."], confianza=2)

T("perdon", "perdon|perdona|lo siento|disculpa|disculpame|no queria|ha sido sin querer|mis disculpas", [
    "No pasa nada.", "Tranquil{o}, no es para tanto.", "Ya está olvidado.", "Bueno. Pero que no se repita.", "Nada, hombre.", "Todos metemos la pata.", "Disculpas aceptadas."],
  amable=["No te preocupes, de verdad. No ha sido nada."], seco=["Vale.", "Ya."], timido=["No, no... perdona tú."], chulo=["Por esta vez, pase.", "Te lo paso porque hoy estoy de buenas."],
  hablador=["Nada, nada. Yo una vez pisé al alcalde en una procesión y ni me disculpé. Desde entonces me saluda."], poca=["Ya es tarde para eso.", "Las palabras no arreglan nada."], confianza=3)

T("si_no", "*vale |*claro |*de acuerdo|*por supuesto|*entiendo|*ya veo|*es verdad|*tienes razon|*eso es|*exacto|*pues si |*pues no |*no se ", [
    "Pues eso.", "Ya ves.", "Así es.", "Lo dicho.", "Eso mismo.", "Si es que es así.", "Ni más ni menos.", "Tal cual.", "Pues ya está.", "Ea."],
  amable=["Me alegro de que estemos de acuerdo.", "Qué bien se habla contigo."], hablador=["¿Ves? Si es lo que yo digo siempre. Lo que pasa es que nadie me hace caso."],
  seco=["Ya.", "Bien."], timido=["Sí... eso."], chulo=["Claro que tengo razón.", "Siempre la tengo."], confianza=1, flojo=True)

T("risa", "jaja|jeje|jiji|que gracioso|que graciosa|que risa|me parto|que bueno|me rio", [
    "Hay que reírse, que es gratis.", "Ya ves. Por no llorar.", "Me alegro de que te haga gracia.", "Con humor todo se lleva mejor.", "Si no nos reímos nosotros, ¿quién?",
    "Y eso que hoy no estoy inspirad{o}."],
  amable=["Qué risa tan bonita tienes."], hablador=["¡Pues espera que te cuente otra! Bueno, no, que esa es larga."], seco=["Ya.", "No era un chiste."], timido=["Je... gracias."],
  chulo=["Soy gracios{o} cuando quiero.", "Lo sé. Tengo ese don."], confianza=2, flojo=True)

T("tristeza", "estoy triste|estoy mal|estoy fatal|me siento solo|me siento sola|estoy deprimido|estoy deprimida|un mal dia|todo me sale mal|no puedo mas|estoy harto|estoy harta", [
    "Vaya. Días malos tenemos todos.", "Mañana lo verás de otra manera.", "Ánimo. Esto también pasa.", "Un paseo por el puerto y lo ves distinto. A mí me funciona.",
    "No estás sol{o}, aunque lo parezca.", "Come algo caliente y duerme. Lo demás puede esperar.", "Hay rachas. La mía duró un año, y aquí sigo.", "Habla con alguien. Aunque sea conmigo."],
  amable=["Lo siento mucho. Si necesitas hablar, aquí estoy un rato.", "Ánimo, de verdad. Vales más de lo que crees."],
  hablador=["Yo cuando estoy mal me hago un chocolate y llamo a mi hermana. Ella no me deja hablar, pero se me pasa."], seco=["Ya pasará.", "Aguanta."],
  timido=["Yo también me siento así a veces... lo siento."], chulo=["Arriba esa cara. Llorando no se arregla nada.", "Haz como yo: no dejes que te vean mal."], confianza=2)

T("alegria", "estoy contento|estoy contenta|estoy feliz|que alegria|me ha tocado|he ganado|buenas noticias|me ha salido bien|estoy de suerte|que bien me va", [
    "Me alegro, hombre. Ya era hora de oír algo bueno.", "Pues a celebrarlo.", "Qué bien. Así da gusto.", "Disfrútalo, que estas cosas no pasan todos los días.",
    "Enhorabuena. Y que dure.", "Eso se merece una caña.", "Me alegro por ti. De verdad."],
  amable=["¡Qué alegría! Me alegro muchísimo por ti."], hablador=["¡No me digas! Cuéntamelo todo, con detalles, que hace mucho que no oigo una buena."], seco=["Bien.", "Me alegro."],
  timido=["Qué bien... me alegro."], chulo=["Bien. Pero no te lo creas mucho.", "Así me siento yo todos los días."], confianza=2)

T("secreto", "un secreto|te cuento un secreto|no se lo digas a nadie|entre tu y yo|guardame un secreto|sabes guardar|un cotilleo|cotilleos", [
    "Soy una tumba. Bueno, una tumba con una rendija.", "Cuenta, cuenta. De aquí no sale.", "A mí no me cuentes secretos, que luego duermo mal.",
    "En {barrio} no hay secretos. Solo cosas que se dicen bajito.", "Si es un secreto, no me lo cuentes. Así no puedo fallarte.", "Yo no he oído nada. Ni lo que me vas a decir."],
  hablador=["¿Un secreto? Soy la persona ideal. No se lo cuento a nadie... a nadie que no me pregunte."], seco=["No quiero saberlo.", "Guárdatelo."],
  timido=["No... mejor no me lo cuentes."], chulo=["Yo sé todos los secretos de esta ciudad.", "Los secretos valen dinero."], amable=["Puedes confiar en mí. No diré nada."])

T("trabajo_para_mi", "hay trabajo para mi|buscas a alguien|necesitas a alguien|me das trabajo|un trabajo para mi|un encargo|algun trabajo|algun encargo|donde hay trabajo", [
    "Yo no tengo nada, pero en la oficina de empleo siempre hay jornadas.", "Pregunta en la taberna. Allí apuntan los encargos con tiza.", "Dicen que buscan repartidor en la pizzería.",
    "Con un taxi o una furgoneta te sacas un jornal. Súbete y a trabajar.", "En el puerto siempre hace falta gente para cargar.", "Si lo que buscas es trabajo honrado, la oficina de empleo. Si es del otro, yo no sé nada.",
    "Yo no contrato a nadie. Bastante tengo con lo mío."],
  amable=["Ojalá pudiera ofrecerte algo. Prueba en la oficina de empleo, que ayudan mucho."], seco=["No.", "Pregunta en empleo."], timido=["No sé... yo solo soy {oficio}."],
  chulo=["Para trabajar conmigo hay que valer.", "Vuelve cuando tengas experiencia."], hablador=["Pues mira, mi cuñado buscaba a uno para la obra, pero ya lo encontró. Era su primo. Aquí todo queda en familia."])

T("idiomas_fuera", "hablas ingles|otros idiomas|has viajado|has estado en|el extranjero|otros paises|fuera de aqui|conoces mundo", [
    "Yo, con el castellano y las manos, me entiendo con cualquiera.", "He salido poco. Una vez fui a la capital y me perdí.", "Con los turistas hablo por señas. Y me entienden.",
    "No he viajado, pero he oído muchas historias en el puerto.", "Inglés sé decir hola, gracias y la cuenta.", "El mundo es muy grande, pero como aquí no se come en ningún lado."],
  hablador=["Estuve en el extranjero una semana. No entendí nada, comí fatal y me cobraron el agua. No vuelvo."], seco=["No.", "Poco."], timido=["No he salido nunca..."],
  chulo=["He estado en todas partes. Y en todas me conocen."], amable=["No, pero me encantaría. ¿Tú has viajado?"])

T("cumple_fecha", "tu cumpleanos|mi cumpleanos|es mi cumpleanos|felicidades|feliz|que celebras", [
    "Felicidades, hombre. Que cumplas muchos.", "El mío ya ni lo celebro. Me limito a cumplir.", "Los cumpleaños, a partir de cierta edad, son un recuento.",
    "Pues eso hay que mojarlo.", "Felicidades. Invita a algo, ¿no?"],
  amable=["¡Muchas felicidades! Que tengas un día precioso."], seco=["Felicidades.", "Bien."], timido=["Felicidades..."], chulo=["Felicidades. El mío sí que es una fiesta."],
  hablador=["Yo cumplo en agosto y nunca tuve fiesta, porque todos estaban de vacaciones. Ahora me lo celebro yo en septiembre y me regalo lo que quiero."], confianza=2)

T("extranjero_nuevo", "soy nuevo|soy nueva|acabo de llegar|no soy de aqui|vengo de fuera|he vuelto|acabo de volver|no conozco esto|estoy perdido|estoy perdida|me he perdido", [
    "Bienvenid{o}. No es mal sitio, ya lo verás.", "Si te pierdes, pregunta. Aquí la gente contesta.", "Pues ya te irás haciendo. Al principio todas las calles parecen iguales.",
    "Las avenidas van de sur a norte y las calles de oeste a este. Con eso no te pierdes.", "Si buscas algo, pregúntame dónde hay lo que necesites.", "Has vuelto en buen momento. O en malo, según se mire.",
    "Con un mapa y un GPS se va a cualquier parte."],
  amable=["Bienvenid{o}, de verdad. Si necesitas algo, pregunta.", "Qué bien que hayas venido. Te va a gustar."], seco=["Ya te apañarás.", "Bienvenid{o}."],
  timido=["Ah... bienvenid{o}."], chulo=["Se te nota a la legua.", "Pégate a mí y no te pierdes."], hablador=["¿Nuev{o}? Pues te cuento: el pan, en la esquina; el café, en la plaza; y los líos, en el puerto. Con eso ya sabes lo fundamental."])

T("cosas_raras", "extraterrestres|fantasmas|un fantasma|la magia|brujas|una bruja|el horoscopo|que signo|ovnis|el fin del mundo|maldicion|mal de ojo", [
    "Yo en esas cosas no creo, pero haberlas, haylas.", "Dicen que en el faro viejo se oyen pasos. Yo no he subido a comprobarlo.", "El horóscopo me dijo que hoy conocería a alguien pesado. Mira tú.",
    "Fantasmas, los que deben dinero y no aparecen.", "Mi abuela echaba las cartas. Acertaba lo malo.", "El fin del mundo lo anuncian cada año y aquí seguimos."],
  hablador=["Mi tía vio una luz en el mar una noche y estuvo un mes sin dormir. Luego resultó que era el pesquero de su vecino."], seco=["Tonterías.", "No creo."],
  timido=["A mí me dan miedo esas cosas..."], chulo=["Los fantasmas me tienen miedo a mí."], amable=["Qué cosas preguntas. Me has hecho gracia."])

T("insistir_cita", "*sal conmigo|*vente conmigo|*ven conmigo|*acompaname|*te vienes|*vamos a tu casa|*vamos a mi casa|*quedamos", [
    "Otro día, que hoy voy con prisa.", "Gracias, pero no puedo.", "No, no. Yo me quedo por aquí.", "Tengo cosas que hacer. De verdad.", "Hoy no. Y mañana tampoco creo."],
  amable=["Te lo agradezco, pero hoy no puedo. Otra vez será."], seco=["No.", "No puedo."], timido=["No... no puedo, lo siento."], chulo=["Yo no voy detrás de nadie.", "Si quieres verme, ya sabes por dónde ando."],
  hablador=["Uy, me encantaría, pero tengo que recoger a mi madre, pasar por la farmacia y llevar el coche. Otro día, sin falta."], poca=["Ni lo sueñes.", "Contigo, a ninguna parte."],
  mucha=["Hoy no puedo, {tu}, pero apúntame para otro día."], confianza=0)
