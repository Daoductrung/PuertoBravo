"""Base de respuestas, segunda parte: ocio, opiniones, el jugador y la conversación en sí."""
from .i18n import tr
from .respuestas import T

T("que_haces", tr("que haces|que estas haciendo|que haces aqui|a donde vas|adonde vas|donde vas|esperas a alguien|que haces por aqui|vas a algun sitio|tienes prisa"), [
    tr("Aquí, dando una vuelta. Hay que estirar las piernas."), tr("Voy a por el pan y vuelvo. Lo de todos los días."), tr("Espero a un amigo que siempre llega tarde."), tr("Nada. Mirar a la gente pasar, que es gratis."),
    tr("Vengo de trabajar y voy a casa. Sin más."), tr("Hacer tiempo. Tengo que recoger una cosa y no han abierto."), tr("Tomar el aire. En casa se me caen las paredes encima."),
    tr("Voy al mercado, a ver qué hay hoy."), tr("Iba al banco, pero he visto la cola y se me han quitado las ganas."), tr("De paseo. A estas horas se está bien en {barrio}.")],
  amable=[tr("Paseando un poco. ¿Y tú, qué haces por {barrio}?"), tr("Nada importante. Tengo un rato si quieres hablar.")],
  hablador=[tr("Pues iba a la farmacia, pero me he encontrado a la Paqui, luego al del quiosco, luego a ti... A este paso llego mañana.")],
  seco=[tr("Nada."), tr("Lo mío.")], timido=[tr("Nada... solo pasaba por aquí.")], chulo=[tr("Lo que me da la gana."), tr("Dejarme ver. Que la gente lo agradece.")], poca=[tr("¿Me estás vigilando?"), tr("Lo que no te importa.")], flojo=True)

T("recomienda", tr("que me recomiendas|que se puede hacer|que hay que ver|que hay para hacer|algo divertido|donde me divierto|que hago aqui|me aburro|estoy aburrido|estoy aburrida|un plan|planes"), [
    tr("Si tienes dinero, el casino. Si no, la playa, que es gratis."), tr("Una vuelta por el puerto al atardecer. Eso no falla."), tr("Hay cine, hay feria, hay bares. Aburrirse aquí tiene mérito."),
    tr("Prueba a pescar. Engancha, y nunca mejor dicho."), tr("Dicen que en la playa hay quien busca tesoros con un detector. Y encuentran."), tr("Las carreras de noche, si te gusta el motor. Yo no te he dicho nada."),
    tr("En el gimnasio hay combates. Se apuesta y todo."), tr("Compra un décimo. Por soñar no cobran."), tr("Si te aburres, apúntate a un curso en la academia."), tr("Habla con la gente. Cada uno tiene una historia.")],
  amable=[tr("A mí me gusta pasear por {barrio}. Pruébalo, ya verás."), tr("Si quieres ayudar, en el comedor social siempre hacen falta manos.")],
  hablador=[tr("Mira, por la mañana el mercado, a mediodía un arroz en el puerto, por la tarde la siesta, que es sagrada, y por la noche lo que surja. Ese es mi plan perfecto y no lo cambio.")],
  seco=[tr("Hay bares."), tr("Tú sabrás qué te gusta.")], timido=[tr("A mí me gusta el cine... no hay que hablar con nadie.")], chulo=[tr("Quédate conmigo y aprende."), tr("El casino. Si te atreves.")])

T("cine_tele", tr("el cine|una pelicula|las peliculas|la tele|la television|una serie|las series|que ves|has visto|un libro|los libros|leer|lees"), [
    tr("Voy al cine cuando echan algo de tiros. Lo demás me duerme."), tr("La tele solo da disgustos."), tr("Yo leo el periódico y gracias."), tr("Me gusta leer, pero me quedo dormid{o} en la segunda página."),
    tr("Las películas de antes sí que eran buenas."), tr("Estoy enganchad{o} a una serie. No me preguntes cuál, que me da vergüenza."), tr("En el cine de aquí las palomitas cuestan más que la entrada."),
    tr("Un buen libro y el ruido del mar. No pido más.")],
  amable=[tr("Me encanta el cine. Si echan algo bueno, avísame.")], hablador=[tr("Fui a ver una de miedo y el que más gritaba era yo. La de delante se cambió de sitio.")],
  seco=[tr("No veo nada."), tr("La tele. Poco.")], timido=[tr("Leo mucho... me gusta más que salir.")], chulo=[tr("De mi vida sí que harían una película."), tr("Yo no veo películas. Las vivo.")])

T("juego_suerte", tr("el casino|la ruleta|apostar|las apuestas|jugar a las cartas|el poker|la loteria|un decimo|el gordo|el bingo|la suerte|tienes suerte|mala suerte|buena suerte"), [
    tr("En el casino solo gana la casa. Y el del guardarropa."), tr("Llevo veinte años jugando al mismo número. Algún día tocará."), tr("La suerte es para el que la busca. Y para algún enchufado."),
    tr("Yo no juego. Bastante lotería es la vida."), tr("Una vez me tocó el reintegro. Lo celebré como si fuera el gordo."), tr("Mi cuñado perdió el coche en una partida. Ahora va en autobús y saluda."),
    tr("Si te toca, acuérdate de mí."), tr("Suerte, la justa. Pero no me quejo."), tr("El bingo de los jueves es lo más emocionante de mi semana.")],
  amable=[tr("Mucha suerte si juegas. Pero con cabeza, ¿eh?")], hablador=[tr("Soñé con el 47 y lo jugué. Salió el 48. Desde entonces no me fío ni de mis sueños.")],
  seco=[tr("No juego."), tr("Tirar el dinero.")], timido=[tr("Nunca he jugado... me daría algo perder.")], chulo=[tr("Yo no necesito suerte. Tengo talento."), tr("A mí las cartas me quieren.")])

T("armas_pelea", tr("un arma|las armas|una pistola|llevas arma|una navaja|sabes pelear|te pegas|una pelea|pegarme|te pego|disparar|un tiro"), [
    tr("De armas no quiero saber nada."), tr("Aquí el que saca un arma acaba mal. Siempre."), tr("Yo me peleé una vez, de joven. Perdí. Fin de la historia."), tr("Guarda eso, que no estamos para sustos."),
    tr("Las armas las carga el diablo."), tr("En la armería venden de todo, con papeles o sin ellos, según a quién preguntes."), tr("Yo, las manos en los bolsillos. Así no me meto en líos."),
    tr("Pelear es de tontos. Correr es de listos.")],
  amable=[tr("Por favor, nada de peleas. No merece la pena.")], hablador=[tr("Mi abuelo tenía una escopeta de caza colgada en el salón. Nunca disparó. Decía que era para asustar a los cobradores.")],
  seco=[tr("No quiero líos."), tr("Ni las toco.")], timido=[tr("No... por favor, no quiero problemas.")], chulo=[tr("Yo no necesito armas. Me basto solo."), tr("¿Pelear? Cuando quieras y donde quieras.")],
  poca=[tr("Aléjate de mí."), tr("Voy a llamar a alguien.")], confianza=-1)

T("ayuda", tr("me ayudas|ayudame|necesito ayuda|un favor|hazme un favor|me echas una mano|puedes ayudarme|necesito que"), [
    tr("Depende de para qué. Dime."), tr("Si está en mi mano, sí. Si no, te digo quién."), tr("Ayudar, ayudo. Meterme en líos, no."), tr("Uf, hoy voy liad{o}. Pero cuéntame."),
    tr("Favores hago los justos, que luego se acostumbran."), tr("Si buscas un sitio, pregúntame dónde hay lo que necesites. Eso sí te lo sé decir."), tr("Mientras no sea dinero ni mudanzas, lo que quieras."),
    tr("Dime qué necesitas y vemos.")],
  amable=[tr("Claro que sí. Dime qué necesitas."), tr("Para eso estamos. Cuéntame.")], hablador=[tr("¿Un favor? Cuenta, cuenta. Yo le hice uno a mi vecino y acabé pintándole el piso entero.")],
  seco=[tr("¿Qué quieres?"), tr("Según.")], timido=[tr("Si puedo... no sé si sabré.")], chulo=[tr("Yo no hago favores. Hago negocios."), tr("Depende de lo que saque yo.")],
  poca=[tr("A ti no te ayudo ni a cruzar la calle."), tr("Búscate la vida.")], mucha=[tr("Para ti, lo que haga falta, {tu}. Ya lo sabes.")])

T("consejo", tr("un consejo|que harias tu|que me aconsejas|aconsejame|que hago|no se que hacer|tu que harias|que opinas|que piensas|tu opinion"), [
    tr("Yo que tú, no me complicaría la vida."), tr("Haz lo que te pida el cuerpo. Y luego arrepiéntete, como todos."), tr("Mi consejo: come bien, duerme bien y no debas dinero."),
    tr("Consejos vendo, que para mí no tengo."), tr("Piénsalo dos veces. Y luego una tercera."), tr("No te fíes de quien te promete mucho."), tr("Lo que tengas que hacer, hazlo de día."),
    tr("Trabaja honradamente. Se duerme mejor."), tr("Pregunta a los mayores. Saben más de lo que parece.")],
  amable=[tr("Yo creo que harás lo correcto. Se te ve buena persona."), tr("Hazle caso a tu conciencia. No suele fallar.")],
  hablador=[tr("Mi madre decía: antes de hablar, cuenta hasta diez. Yo nunca he pasado de tres, y así me va.")], seco=[tr("Tú verás."), tr("Cada uno, lo suyo.")],
  timido=[tr("No sé... yo no soy quién para aconsejar.")], chulo=[tr("Haz lo que yo haría: lo mejor."), tr("Hazme caso y no fallarás.")], flojo=True)

T("quien_soy", tr("sabes quien soy|me conoces|te sueno|has oido hablar de mi|que dicen de mi|que se dice de mi|soy famoso|soy famosa|que piensas de mi|que opinas de mi|te caigo bien|te caigo mal"), [
    tr("Me suena tu cara, pero no caigo."), tr("Algo he oído. Aquí se sabe todo."), tr("No sé quién eres, pero pareces buena gente."), tr("Dicen cosas. Unas buenas y otras no tanto."),
    tr("Te he visto por {barrio} más de una vez."), tr("Yo no juzgo a nadie por lo que cuentan."), tr("Eres el que ha vuelto hace poco, ¿no? Eso dicen."), tr("De ti no sé nada, y casi mejor.")],
  amable=[tr("Pareces buena persona. Con eso me basta."), tr("Me caes bien, la verdad.")], hablador=[tr("De ti se dice de todo. Que si vienes de lejos, que si has estado a la sombra... Yo, como digo siempre: hasta que no lo vea, no lo creo.")],
  seco=[tr("No."), tr("Ni idea.")], timido=[tr("No... perdona, no te conozco.")], chulo=[tr("Aquí el conocido soy yo."), tr("No eres tan famoso como te crees.")],
  poca=[tr("Sé quién eres. Por eso no quiero hablar contigo."), tr("Lo que he oído de ti no es bueno.")], mucha=[tr("Claro que sí, {tu}. Eres de los pocos de fiar que quedan.")])

T("carcel_pasado", tr("la carcel|he estado en la carcel|estuve preso|estuve presa|la prision|sali de la carcel|mi pasado|un error|me arrepiento|soy inocente|no lo hice"), [
    tr("Cada uno carga con lo suyo."), tr("Todo el mundo merece otra oportunidad. O eso dicen."), tr("De ahí se sale peor o mejor. Tú sabrás."), tr("Yo no pregunto por el pasado de nadie."),
    tr("Lo hecho, hecho está. Ahora, mirar adelante."), tr("Mi primo estuvo dentro. Salió y ahora tiene una frutería."), tr("Si dices que eres inocente, yo te creo. No gano nada con no creerte."),
    tr("Aquí se olvida pronto. O se hace como que se olvida.")],
  amable=[tr("Lo importante es lo que hagas a partir de ahora."), tr("Me alegro de que estés fuera. Ánimo.")], seco=[tr("No pregunto."), tr("Allá tú.")],
  timido=[tr("Ah... lo siento. No sabía.")], chulo=[tr("A mí no me asusta un ex presidiario."), tr("Yo he conocido a peores.")], hablador=[tr("Uy, eso es duro. Mi tío estuvo tres meses por una tontería y salió sabiendo jugar al mus como nadie.")],
  poca=[tr("Con razón. Ya decía yo."), tr("No me extraña.")], confianza=0)

T("futuro_suenos", tr("tus suenos|que suenas|el futuro|que quieres ser|que te gustaria|tu sueno|planes de futuro|si fueras rico|si te tocara|jubilarte|la jubilacion"), [
    tr("Una casita con vistas al mar y que no me llame nadie."), tr("Que me toque la lotería y no volver a madrugar."), tr("Yo ya no sueño. Me conformo con llegar a fin de mes."),
    tr("Me gustaría viajar. No he salido de la comarca."), tr("Jubilarme con salud. Lo demás me sobra."), tr("Poner un bar. Todo el mundo quiere poner un bar."),
    tr("Que mis hijos vivan mejor que yo."), tr("Un barco pequeño. Para salir yo sol{o}, sin nadie."), tr("El futuro, ya veremos. Bastante tengo con el presente.")],
  amable=[tr("Con tener salud y a los míos cerca, ya está cumplido.")], hablador=[tr("Yo quería ser cantante, luego torero, luego astronauta. He acabado de {oficio}. No está mal, pero no es lo mismo.")],
  seco=[tr("Que me dejen tranquil{o}."), tr("Nada.")], timido=[tr("Me gustaría... no sé, que no me diera vergüenza todo.")], chulo=[tr("Yo no sueño. Yo consigo."), tr("Ser el dueño de todo esto. Y lo seré.")])

T("amor", tr("el amor|estas enamorado|estas enamorada|te has enamorado|me he enamorado|mi novia|mi novio|mi ex|me han dejado|corazon roto|te quiero"), [
    tr("El amor es como el levante: viene cuando quiere y te despeina."), tr("De eso sé poco. He acertado una vez de cinco."), tr("Si te han dejado, que les den. Hay más peces en el mar."),
    tr("Yo ya estoy mayor para esos sustos."), tr("Enamorarse está bien. Lo malo viene luego."), tr("Mi abuelo cortejó a mi abuela cuatro años. Ahora en cuatro días ya se han dejado."),
    tr("El tiempo lo cura todo. Menos las hipotecas.")],
  amable=[tr("Qué bonito es eso. Ojalá te vaya muy bien."), tr("Si te han hecho daño, lo siento. Pasará.")], hablador=[tr("Yo me enamoré a los quince de la hija del panadero. Engordé seis kilos de ir a comprar pan.")],
  seco=[tr("No es lo mío."), tr("Bah.")], timido=[tr("Eh... yo de eso... no sé nada.")], chulo=[tr("De mí se enamoran. Yo no."), tr("He roto más corazones que platos.")])

T("miedo_noche", tr("tienes miedo|me da miedo|que miedo|de noche|por la noche|la noche|es peligroso de noche|sales de noche|a oscuras|la madrugada"), [
    tr("De noche, todos los gatos son pardos. Y algunos muerden."), tr("Yo a las diez estoy en casa. Lo que pase fuera no es cosa mía."), tr("La noche tiene su gente. No es la misma que de día."),
    tr("Miedo no, respeto."), tr("De madrugada solo quedan los taxis y los que no deberían estar."), tr("Antes salía. Ahora me da pereza hasta bajar la basura."),
    tr("Si sales de noche, ve por las calles con luz.")],
  amable=[tr("Ten cuidado cuando oscurezca, por favor.")], hablador=[tr("Una noche oí un ruido en la escalera y bajé con la sartén. Era mi vecino, que había perdido las llaves. Casi le abro la cabeza.")],
  seco=[tr("No salgo."), tr("Miedo ninguno.")], timido=[tr("Sí... a mí me da miedo. Mucho.")], chulo=[tr("La noche es mía."), tr("El miedo no lo conozco.")])

T("noticias", tr("las noticias|el periodico|que ha pasado|te has enterado|has oido lo de|lo ultimo|que novedades|que hay de nuevo|algo nuevo"), [
    tr("El periódico lo cuenta todo, menos lo importante."), tr("Yo me entero de todo en el bar. Es más fiable."), tr("Pregúntame qué se cuenta por ahí y te digo lo último."),
    tr("Siempre pasa algo, pero nunca cambia nada."), tr("No leo las noticias. Para disgustos, ya tengo la factura de la luz."), tr("Dicen que va a haber movida en el puerto. Dicen."),
    tr("Lo de siempre: suben los precios y bajan los sueldos.")],
  amable=[tr("No estoy muy al día, pero si me entero de algo te lo cuento.")], hablador=[tr("¿Que si me he enterado? Yo me entero antes que el periódico. Tengo a mi cuñada, que es mejor que una agencia.")],
  seco=[tr("No sé nada."), tr("Lo de siempre.")], timido=[tr("No me entero de nada, la verdad...")], chulo=[tr("Las noticias las sé yo antes de que pasen.")], flojo=True)

T("movil", tr("el movil|tu telefono|internet|las redes|el ordenador|la tecnologia|un mensaje|llamar por telefono|whatsapp|las pantallas"), [
    tr("Yo el móvil lo uso para llamar. Lo demás no lo entiendo."), tr("Los críos no levantan la vista de la pantalla."), tr("Antes quedábamos en la plaza. Ahora, por mensaje."),
    tr("Se me ha roto la pantalla tres veces este año."), tr("Internet es como el bar, pero sin tapas."), tr("Mi nieto me enseñó a mandar fotos. Ahora las mando todas torcidas.")],
  hablador=[tr("Me metí en un grupo de vecinos por el móvil y ahora me entero de cosas que preferiría no saber. La del segundo riega a las tres de la mañana.")],
  seco=[tr("Lo justo."), tr("No me gusta.")], timido=[tr("Yo prefiero escribir que hablar... por eso me gusta.")], chulo=[tr("Tengo el último modelo. Como debe ser.")], amable=[tr("Viene bien para hablar con la familia que está lejos.")])

T("religion", tr("la iglesia|vas a misa|crees en dios|dios|rezar|rezas|el cura|los santos|ir al cielo|la virgen"), [
    tr("Voy a misa en fiestas y en funerales."), tr("Yo creo en lo que veo. Y a veces ni eso."), tr("La iglesia de aquí tiene unas campanas que despiertan a un muerto."),
    tr("Cada uno, con sus creencias. Yo respeto."), tr("Mi madre reza por los dos."), tr("El cura es buena gente. Juega al dominó mejor que nadie.")],
  amable=[tr("Creer en algo ayuda. En lo que sea.")], seco=[tr("No hablo de eso."), tr("Allá cada cual.")], timido=[tr("Yo... rezo a veces. Cuando tengo miedo.")],
  chulo=[tr("Dios y yo nos entendemos."), tr("A mí que no me sermoneen.")], hablador=[tr("El cura de antes daba unos sermones de hora y media. El de ahora, quince minutos y a casa. Hemos salido ganando.")])

T("compras_ropa", tr("las tiendas|ir de compras|comprar ropa|tu ropa|vas muy elegante|vas muy guapo|vas muy guapa|que ropa|la moda|el supermercado|hacer la compra"), [
    tr("Yo compro en la tienda de siempre. Me fían y todo."), tr("La ropa, en rebajas o nada."), tr("Esto me lo regaló mi cuñada. Por eso me queda grande."),
    tr("Las tiendas del centro son para turistas."), tr("En el mercado se compra mejor y más barato."), tr("Hacer la compra es mi deporte. Cargo como una mula."),
    tr("Gracias. Uno se arregla lo que puede.")],
  amable=[tr("Qué amable. Tú también vas muy bien.")], hablador=[tr("Fui a por unos calcetines y volví con una chaqueta, dos camisas y sin calcetines. Así soy yo.")],
  seco=[tr("Compro lo justo."), tr("Es ropa.")], timido=[tr("Gracias... es vieja.")], chulo=[tr("Lo que yo me pongo, se pone de moda."), tr("Elegante es poco.")])

T("casa_alquiler", tr("tu casa|donde vives|el alquiler|los pisos|comprar una casa|la hipoteca|un piso|vivienda|los alquileres|el casero"), [
    tr("Vivo aquí cerca. Un piso pequeño, pero mío. Bueno, del banco."), tr("Los alquileres están imposibles. Pagas más por menos."), tr("Mi casero no arregla ni una bombilla."),
    tr("Hay casas en venta, si tienes con qué. Te dan garaje y todo."), tr("Vivo en {barrio}. No digo el número, por si acaso."), tr("La hipoteca la acabo de pagar a los ochenta, si llego."),
    tr("Antes un piso costaba lo que hoy un coche.")],
  amable=[tr("Vivo aquí al lado. Es humilde, pero se está a gusto.")], hablador=[tr("Mi piso tiene cuarenta metros y vivimos cuatro. Para pasar al baño hay que pedir turno, como en la carnicería.")],
  seco=[tr("Por aquí."), tr("En un piso.")], timido=[tr("Cerca... prefiero no decir dónde.")], chulo=[tr("Vivo en lo mejor de {barrio}. No podía ser de otra forma.")], poca=[tr("¿Para qué quieres saber dónde vivo?")])

T("agua_sequia", tr("la sequia|el agua|no hay agua|cortan el agua|las cisternas|el grifo|la lluvia que no|sin llover|la desaladora|el cauce"), [
    tr("Tres años sin llover como Dios manda. Esto no es normal."), tr("El agua vale ya más que el vino."), tr("Dos horas de grifo al día. Y dando gracias."),
    tr("En la colina riegan los jardines mientras aquí hacemos cola con garrafas."), tr("Dicen que la empresa del agua hace lo que quiere."), tr("Yo lleno cubos cuando sale, por si acaso."),
    tr("El día que llueva, salimos todos a la calle a mojarnos.")],
  amable=[tr("Si te falta agua, en el comedor vecinal reparten.")], hablador=[tr("Mi vecina guarda el agua de fregar para la cisterna y la de la cisterna para las plantas. Las plantas no sé cómo siguen vivas.")],
  seco=[tr("No hay."), tr("Mal.")], timido=[tr("Es... preocupante. Yo ahorro la que puedo.")], chulo=[tr("A mí nunca me falta. Tengo mis contactos.")])

T("ricos_jefes", tr("los ricos|los jefes|los de arriba|los empresarios|los poderosos|los bancos|el banco|los banqueros|la injusticia|no es justo"), [
    tr("Los de arriba no pisan la calle. Por eso no saben nada."), tr("El banco te da un paraguas cuando hace sol y te lo quita cuando llueve."), tr("Siempre ganan los mismos."),
    tr("Justicia hay. Para el que puede pagarla."), tr("Aquí el que tiene, tiene, y el que no, aguanta."), tr("Yo no envidio a los ricos. Bueno, un poco."),
    tr("Mientras unos tienen tres casas, otros no tienen ni una.")],
  hablador=[tr("Fui al banco a pedir un préstamo y me pidieron tantos papeles que al final les dejé yo dinero a ellos, de comisiones.")], seco=[tr("Lo de siempre."), tr("Así es.")],
  timido=[tr("No es justo... pero qué vamos a hacer.")], chulo=[tr("Algún día seré yo el de arriba."), tr("A esos los tengo calados.")], amable=[tr("Hay de todo. También hay gente con dinero que ayuda.")])

T("tabaco", tr("tienes fuego|un cigarro|fumas|tienes tabaco|un pitillo|el tabaco|fumar"), [
    tr("No fumo. Lo dejé cuando subieron el precio."), tr("Toma fuego. El tabaco, no, que es el último."), tr("Eso te va a matar. Y a mí de envidia."), tr("Fumo, pero solo en fiestas. Y en días de diario."),
    tr("No tengo. Pregunta en el bar."), tr("Lo dejé hace diez años. Sueño con él todas las noches.")],
  amable=[tr("No fumo, lo siento. Y tú deberías dejarlo, que eres joven.")], seco=[tr("No fumo."), tr("No.")], timido=[tr("No... no fumo.")], chulo=[tr("Yo fumo puros. Eso es para aficionados.")],
  hablador=[tr("Lo dejé tres veces. La primera duré un mes, la segunda una semana y la tercera, hasta el café de la tarde.")])

T("gracias", tr("gracias|muchas gracias|te lo agradezco|muy amable|eres muy amable|que amable|te debo una"), [
    tr("De nada, hombre."), tr("No hay de qué."), tr("Para eso estamos."), tr("Nada, nada."), tr("A mandar."), tr("No las merece."), tr("Hoy por ti y mañana por mí."), tr("Faltaría más.")],
  amable=[tr("De nada. Ha sido un placer."), tr("Gracias a ti por la conversación.")], hablador=[tr("De nada. Y cuando quieras otro rato de charla, ya sabes dónde encontrarme. Bueno, no lo sabes, pero estoy siempre por aquí.")],
  seco=[tr("Nada."), tr("Ya.")], timido=[tr("De nada... no ha sido nada.")], chulo=[tr("Ya me lo pagarás."), tr("Lo sé. Soy así de generos{o}.")], mucha=[tr("Entre nosotros no hacen falta las gracias, {tu}.")], confianza=2)

T("perdon", tr("perdon|perdona|lo siento|disculpa|disculpame|no queria|ha sido sin querer|mis disculpas"), [
    tr("No pasa nada."), tr("Tranquil{o}, no es para tanto."), tr("Ya está olvidado."), tr("Bueno. Pero que no se repita."), tr("Nada, hombre."), tr("Todos metemos la pata."), tr("Disculpas aceptadas.")],
  amable=[tr("No te preocupes, de verdad. No ha sido nada.")], seco=[tr("Vale."), tr("Ya.")], timido=[tr("No, no... perdona tú.")], chulo=[tr("Por esta vez, pase."), tr("Te lo paso porque hoy estoy de buenas.")],
  hablador=[tr("Nada, nada. Yo una vez pisé al alcalde en una procesión y ni me disculpé. Desde entonces me saluda.")], poca=[tr("Ya es tarde para eso."), tr("Las palabras no arreglan nada.")], confianza=3)

T("si_no", tr("*vale |*claro |*de acuerdo|*por supuesto|*entiendo|*ya veo|*es verdad|*tienes razon|*eso es|*exacto|*pues si |*pues no |*no se "), [
    tr("Pues eso."), tr("Ya ves."), tr("Así es."), tr("Lo dicho."), tr("Eso mismo."), tr("Si es que es así."), tr("Ni más ni menos."), tr("Tal cual."), tr("Pues ya está."), tr("Ea.")],
  amable=[tr("Me alegro de que estemos de acuerdo."), tr("Qué bien se habla contigo.")], hablador=[tr("¿Ves? Si es lo que yo digo siempre. Lo que pasa es que nadie me hace caso.")],
  seco=[tr("Ya."), tr("Bien.")], timido=[tr("Sí... eso.")], chulo=[tr("Claro que tengo razón."), tr("Siempre la tengo.")], confianza=1, flojo=True)

T("risa", tr("jaja|jeje|jiji|que gracioso|que graciosa|que risa|me parto|que bueno|me rio"), [
    tr("Hay que reírse, que es gratis."), tr("Ya ves. Por no llorar."), tr("Me alegro de que te haga gracia."), tr("Con humor todo se lleva mejor."), tr("Si no nos reímos nosotros, ¿quién?"),
    tr("Y eso que hoy no estoy inspirad{o}.")],
  amable=[tr("Qué risa tan bonita tienes.")], hablador=[tr("¡Pues espera que te cuente otra! Bueno, no, que esa es larga.")], seco=[tr("Ya."), tr("No era un chiste.")], timido=[tr("Je... gracias.")],
  chulo=[tr("Soy gracios{o} cuando quiero."), tr("Lo sé. Tengo ese don.")], confianza=2, flojo=True)

T("tristeza", tr("estoy triste|estoy mal|estoy fatal|me siento solo|me siento sola|estoy deprimido|estoy deprimida|un mal dia|todo me sale mal|no puedo mas|estoy harto|estoy harta"), [
    tr("Vaya. Días malos tenemos todos."), tr("Mañana lo verás de otra manera."), tr("Ánimo. Esto también pasa."), tr("Un paseo por el puerto y lo ves distinto. A mí me funciona."),
    tr("No estás sol{o}, aunque lo parezca."), tr("Come algo caliente y duerme. Lo demás puede esperar."), tr("Hay rachas. La mía duró un año, y aquí sigo."), tr("Habla con alguien. Aunque sea conmigo.")],
  amable=[tr("Lo siento mucho. Si necesitas hablar, aquí estoy un rato."), tr("Ánimo, de verdad. Vales más de lo que crees.")],
  hablador=[tr("Yo cuando estoy mal me hago un chocolate y llamo a mi hermana. Ella no me deja hablar, pero se me pasa.")], seco=[tr("Ya pasará."), tr("Aguanta.")],
  timido=[tr("Yo también me siento así a veces... lo siento.")], chulo=[tr("Arriba esa cara. Llorando no se arregla nada."), tr("Haz como yo: no dejes que te vean mal.")], confianza=2)

T("alegria", tr("estoy contento|estoy contenta|estoy feliz|que alegria|me ha tocado|he ganado|buenas noticias|me ha salido bien|estoy de suerte|que bien me va"), [
    tr("Me alegro, hombre. Ya era hora de oír algo bueno."), tr("Pues a celebrarlo."), tr("Qué bien. Así da gusto."), tr("Disfrútalo, que estas cosas no pasan todos los días."),
    tr("Enhorabuena. Y que dure."), tr("Eso se merece una caña."), tr("Me alegro por ti. De verdad.")],
  amable=[tr("¡Qué alegría! Me alegro muchísimo por ti.")], hablador=[tr("¡No me digas! Cuéntamelo todo, con detalles, que hace mucho que no oigo una buena.")], seco=[tr("Bien."), tr("Me alegro.")],
  timido=[tr("Qué bien... me alegro.")], chulo=[tr("Bien. Pero no te lo creas mucho."), tr("Así me siento yo todos los días.")], confianza=2)

T("secreto", tr("un secreto|te cuento un secreto|no se lo digas a nadie|entre tu y yo|guardame un secreto|sabes guardar|un cotilleo|cotilleos"), [
    tr("Soy una tumba. Bueno, una tumba con una rendija."), tr("Cuenta, cuenta. De aquí no sale."), tr("A mí no me cuentes secretos, que luego duermo mal."),
    tr("En {barrio} no hay secretos. Solo cosas que se dicen bajito."), tr("Si es un secreto, no me lo cuentes. Así no puedo fallarte."), tr("Yo no he oído nada. Ni lo que me vas a decir.")],
  hablador=[tr("¿Un secreto? Soy la persona ideal. No se lo cuento a nadie... a nadie que no me pregunte.")], seco=[tr("No quiero saberlo."), tr("Guárdatelo.")],
  timido=[tr("No... mejor no me lo cuentes.")], chulo=[tr("Yo sé todos los secretos de esta ciudad."), tr("Los secretos valen dinero.")], amable=[tr("Puedes confiar en mí. No diré nada.")])

T("trabajo_para_mi", tr("hay trabajo para mi|buscas a alguien|necesitas a alguien|me das trabajo|un trabajo para mi|un encargo|algun trabajo|algun encargo|donde hay trabajo"), [
    tr("Yo no tengo nada, pero en la oficina de empleo siempre hay jornadas."), tr("Pregunta en la taberna. Allí apuntan los encargos con tiza."), tr("Dicen que buscan repartidor en la pizzería."),
    tr("Con un taxi o una furgoneta te sacas un jornal. Súbete y a trabajar."), tr("En el puerto siempre hace falta gente para cargar."), tr("Si lo que buscas es trabajo honrado, la oficina de empleo. Si es del otro, yo no sé nada."),
    tr("Yo no contrato a nadie. Bastante tengo con lo mío.")],
  amable=[tr("Ojalá pudiera ofrecerte algo. Prueba en la oficina de empleo, que ayudan mucho.")], seco=[tr("No."), tr("Pregunta en empleo.")], timido=[tr("No sé... yo solo soy {oficio}.")],
  chulo=[tr("Para trabajar conmigo hay que valer."), tr("Vuelve cuando tengas experiencia.")], hablador=[tr("Pues mira, mi cuñado buscaba a uno para la obra, pero ya lo encontró. Era su primo. Aquí todo queda en familia.")])

T("idiomas_fuera", tr("hablas ingles|otros idiomas|has viajado|has estado en|el extranjero|otros paises|fuera de aqui|conoces mundo"), [
    tr("Yo, con el castellano y las manos, me entiendo con cualquiera."), tr("He salido poco. Una vez fui a la capital y me perdí."), tr("Con los turistas hablo por señas. Y me entienden."),
    tr("No he viajado, pero he oído muchas historias en el puerto."), tr("Inglés sé decir hola, gracias y la cuenta."), tr("El mundo es muy grande, pero como aquí no se come en ningún lado.")],
  hablador=[tr("Estuve en el extranjero una semana. No entendí nada, comí fatal y me cobraron el agua. No vuelvo.")], seco=[tr("No."), tr("Poco.")], timido=[tr("No he salido nunca...")],
  chulo=[tr("He estado en todas partes. Y en todas me conocen.")], amable=[tr("No, pero me encantaría. ¿Tú has viajado?")])

T("cumple_fecha", tr("tu cumpleanos|mi cumpleanos|es mi cumpleanos|felicidades|feliz|que celebras"), [
    tr("Felicidades, hombre. Que cumplas muchos."), tr("El mío ya ni lo celebro. Me limito a cumplir."), tr("Los cumpleaños, a partir de cierta edad, son un recuento."),
    tr("Pues eso hay que mojarlo."), tr("Felicidades. Invita a algo, ¿no?")],
  amable=[tr("¡Muchas felicidades! Que tengas un día precioso.")], seco=[tr("Felicidades."), tr("Bien.")], timido=[tr("Felicidades...")], chulo=[tr("Felicidades. El mío sí que es una fiesta.")],
  hablador=[tr("Yo cumplo en agosto y nunca tuve fiesta, porque todos estaban de vacaciones. Ahora me lo celebro yo en septiembre y me regalo lo que quiero.")], confianza=2)

T("extranjero_nuevo", tr("soy nuevo|soy nueva|acabo de llegar|no soy de aqui|vengo de fuera|he vuelto|acabo de volver|no conozco esto|estoy perdido|estoy perdida|me he perdido"), [
    tr("Bienvenid{o}. No es mal sitio, ya lo verás."), tr("Si te pierdes, pregunta. Aquí la gente contesta."), tr("Pues ya te irás haciendo. Al principio todas las calles parecen iguales."),
    tr("Las avenidas van de sur a norte y las calles de oeste a este. Con eso no te pierdes."), tr("Si buscas algo, pregúntame dónde hay lo que necesites."), tr("Has vuelto en buen momento. O en malo, según se mire."),
    tr("Con un mapa y un GPS se va a cualquier parte.")],
  amable=[tr("Bienvenid{o}, de verdad. Si necesitas algo, pregunta."), tr("Qué bien que hayas venido. Te va a gustar.")], seco=[tr("Ya te apañarás."), tr("Bienvenid{o}.")],
  timido=[tr("Ah... bienvenid{o}.")], chulo=[tr("Se te nota a la legua."), tr("Pégate a mí y no te pierdes.")], hablador=[tr("¿Nuev{o}? Pues te cuento: el pan, en la esquina; el café, en la plaza; y los líos, en el puerto. Con eso ya sabes lo fundamental.")])

T("cosas_raras", tr("extraterrestres|fantasmas|un fantasma|la magia|brujas|una bruja|el horoscopo|que signo|ovnis|el fin del mundo|maldicion|mal de ojo"), [
    tr("Yo en esas cosas no creo, pero haberlas, haylas."), tr("Dicen que en el faro viejo se oyen pasos. Yo no he subido a comprobarlo."), tr("El horóscopo me dijo que hoy conocería a alguien pesado. Mira tú."),
    tr("Fantasmas, los que deben dinero y no aparecen."), tr("Mi abuela echaba las cartas. Acertaba lo malo."), tr("El fin del mundo lo anuncian cada año y aquí seguimos.")],
  hablador=[tr("Mi tía vio una luz en el mar una noche y estuvo un mes sin dormir. Luego resultó que era el pesquero de su vecino.")], seco=[tr("Tonterías."), tr("No creo.")],
  timido=[tr("A mí me dan miedo esas cosas...")], chulo=[tr("Los fantasmas me tienen miedo a mí.")], amable=[tr("Qué cosas preguntas. Me has hecho gracia.")])

T("insistir_cita", tr("*sal conmigo|*vente conmigo|*ven conmigo|*acompaname|*te vienes|*vamos a tu casa|*vamos a mi casa|*quedamos"), [
    tr("Otro día, que hoy voy con prisa."), tr("Gracias, pero no puedo."), tr("No, no. Yo me quedo por aquí."), tr("Tengo cosas que hacer. De verdad."), tr("Hoy no. Y mañana tampoco creo.")],
  amable=[tr("Te lo agradezco, pero hoy no puedo. Otra vez será.")], seco=[tr("No."), tr("No puedo.")], timido=[tr("No... no puedo, lo siento.")], chulo=[tr("Yo no voy detrás de nadie."), tr("Si quieres verme, ya sabes por dónde ando.")],
  hablador=[tr("Uy, me encantaría, pero tengo que recoger a mi madre, pasar por la farmacia y llevar el coche. Otro día, sin falta.")], poca=[tr("Ni lo sueñes."), tr("Contigo, a ninguna parte.")],
  mucha=[tr("Hoy no puedo, {tu}, pero apúntame para otro día.")], confianza=0)
