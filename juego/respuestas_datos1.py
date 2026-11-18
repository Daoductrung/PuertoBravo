"""Base de respuestas, primera parte: la persona, su vida y el día a día."""
from .respuestas import T

T("como_estas", "como estas|como te va|como andas|que tal estas|como lo llevas|como va todo|todo bien|estas bien|te encuentras bien|como va eso|que tal todo|que tal va", [
    "Tirando, que no es poco.", "Bien, sin más. No me quejo.", "Aquí estamos, que ya es bastante.", "Regular. Días mejores he tenido.", "Bien, gracias. ¿Y tú?",
    "Como siempre: mucho trabajo y poco sueldo.", "Hoy bien. Mañana ya veremos.", "Voy tirando. La espalda me da guerra, pero bien.", "No me puedo quejar, y si me quejo da igual.",
    "Bien, de verdad. Hoy me he levantado con buen pie.", "Cansad{o}, pero content{o}.", "Pues mira, de salud bien, que es lo importante."],
  amable=["Muy bien, gracias por preguntar. Da gusto que alguien pregunte.", "Bien, bien. Mejor ahora que hablamos un rato.", "Estupendamente. Hace un día para estar bien."],
  hablador=["Pues bien, aunque esta mañana me he levantado con un dolor aquí en el costado que no veas, pero se me ha pasado con un café.", "Bien, liad{o} como siempre, que no paro ni para respirar.",
            "Mejor que ayer, que ayer tuve un día que para qué te voy a contar."],
  seco=["Bien.", "Normal.", "Tirando.", "Vivo, que no es poco."], timido=["Bien... creo. Gracias.", "Bien, bien. No me pasa nada.", "Bueno, un poco nervios{o}, pero bien."],
  chulo=["Yo siempre estoy bien. Los que están mal son los demás.", "Como un rey. ¿No se me nota?", "Mejor que tú, seguro."],
  poca=["Estaba mejor antes de que llegaras.", "Bien. Y con prisa.", "Eso a ti no te importa."], mucha=["Mejor ahora que te veo, {tu}.", "Bien, {tu}. Contigo siempre se anima uno."])

T("nombre", "como te llamas|tu nombre|quien eres|como es tu nombre|te llamas|con quien hablo", [
    "Me llamo {yo}.", "{yo}, para servirte.", "Soy {yo}. Aquí me conoce todo el mundo.", "{yo}. ¿Y tú?", "{yo} me pusieron, y con {yo} me he quedado.",
    "Me llaman {yo}. Soy {oficio}.", "{yo}. Encantad{o}.", "Soy {yo}, de aquí de toda la vida."],
  amable=["{yo}, mucho gusto. ¿Y tú cómo te llamas?", "Me llamo {yo}. Qué bien que preguntes, la gente ya ni se presenta."],
  hablador=["{yo}, como mi abuelo, que también se llamaba así y era igual de charlatán.", "{yo}. Bueno, en casa me dicen de otra manera, pero eso no te lo cuento."],
  seco=["{yo}.", "{yo}. ¿Algo más?"], timido=["{yo}... me llamo {yo}.", "Me llamo {yo}. Perdona, no me había presentado."],
  chulo=["{yo}. Apúntatelo, que te va a sonar.", "¿No sabes quién soy? {yo}. Pregunta por ahí."], poca=["¿Y para qué quieres saberlo?", "Eso no te hace falta."],
  mucha=["Pero si ya lo sabes, {tu}. {yo}, el de siempre." ])

T("edad", "cuantos anos|que edad|tu edad|eres joven|eres mayor|eres viejo|eres vieja|cuando naciste", [
    "Los que aparento, ni uno más.", "Demasiados para lo que me queda por hacer.", "Suficientes para saber de qué va esto.", "Eso no se pregunta, hombre.",
    "Los justos. Ni muchos ni pocos.", "Ya no soy un chaval, eso seguro.", "Más de los que quisiera y menos de los que me echan.", "La edad está en la cabeza, dicen. Pues en la cabeza tengo veinte."],
  amable=["Ay, ya tengo unos cuantos, pero los llevo bien.", "Los que tengo los he vivido a gusto, que es lo que importa."],
  hablador=["Pues mira, nací el año que se inundó el mercado, así que echa cuentas. Y me acuerdo perfectamente, bueno, me lo contaron.", "Tengo los mismos que mi prima la del puerto, que nacimos con dos días de diferencia."],
  seco=["Los que tengo.", "Eso no se pregunta."], timido=["Eh... prefiero no decirlo.", "No muchos... bueno, alguno."],
  chulo=["Los suficientes para darte dos vueltas.", "Estoy en mi mejor momento. Siempre lo estoy."], poca=["¿Y a ti qué te importa?"])

T("de_donde", "de donde eres|eres de aqui|naciste aqui|de que pueblo|de donde vienes|eres de fuera|llevas mucho aqui|cuanto llevas aqui|siempre has vivido", [
    "De aquí de toda la vida. No he salido ni de vacaciones.", "Nací en {ciudad} y aquí me moriré, si me dejan.", "Vine de joven por trabajo y ya ves, me quedé.",
    "Mis abuelos eran del interior, pero yo soy de mar.", "De {barrio}. Nací a dos calles de aquí.", "De aquí. Bueno, mi madre era de un pueblo de la sierra.",
    "Llevo aquí tanto que ya ni me acuerdo de cuándo llegué.", "Soy de {ciudad}, que no es lo mismo que ser de los alrededores."],
  amable=["De aquí, y muy a gusto. Es un buen sitio para vivir.", "Soy de fuera, pero me acogieron tan bien que ya soy de aquí."],
  hablador=["Yo nací en {barrio}, en la casa que hacía esquina, que ahora es una tienda. Mi padre también, y mi abuelo. Somos cuatro generaciones ya.", "De aquí, de aquí. Bueno, estuve dos años fuera y casi me muero de la pena."],
  seco=["De aquí.", "De {ciudad}."], timido=["De aquí cerca... de {barrio}.", "Soy de aquí. No he salido mucho."],
  chulo=["De {barrio}, de pura cepa. De los de verdad.", "Yo soy de aquí. Los que venís de fuera se os nota a la legua."], poca=["De por ahí."])

T("familia", "tu familia|tienes familia|tus padres|tu madre|tu padre|tienes hermanos|tu hermano|tu hermana|tus abuelos|tu abuela|tu abuelo|vives solo|vives sola|con quien vives", [
    "La familia bien, gracias. Cada uno a lo suyo.", "Somos pocos, pero bien avenidos.", "Mi madre sigue viviendo en la casa de siempre. No hay quien la saque.",
    "Tengo un hermano fuera. Llama por Navidad y poco más.", "La familia, como todas: unos días mejor y otros peor.", "Vivo sol{o}. Se está tranquil{o}.",
    "Mi padre era pescador. De él aprendí lo poco que sé.", "Los domingos comemos todos juntos. Es sagrado.", "Mi abuela decía que la familia es lo único que no se elige. Y tenía razón.",
    "Bien todos, que yo sepa. Hace días que no hablo con ellos."],
  amable=["Muy bien todos, gracias. Mi madre te caería bien.", "Tengo una familia estupenda, la verdad. He tenido suerte."],
  hablador=["Uy, mi familia. Somos siete hermanos, y cada uno de su padre y de su madre, como quien dice. El mayor está en el puerto, la segunda puso una mercería, el tercero no sabemos dónde anda...",
            "Mi madre, con ochenta y tantos, sale todos los días a por el pan y vuelve con las noticias de todo el barrio."],
  seco=["Bien.", "Cada uno en su casa."], timido=["Bien... no hablamos mucho.", "Vivo con mi madre. Estamos bien."],
  chulo=["En mi familia somos todos igual de guapos. Qué te voy a contar.", "Mi padre mandaba en {barrio}. Algo se hereda."], poca=["De mi familia no hablo con desconocidos."])

T("hijos", "tienes hijos|tus hijos|tu hijo|tu hija|tienes ninos|los ninos|los crios|tus nietos", [
    "Dos, y ya crecidos. Ni se acuerdan de llamar.", "No tengo. Bastante tengo conmigo.", "Una niña. Es lo mejor que he hecho.", "Tres, y los tres distintos como la noche y el día.",
    "Los críos bien, creciendo. Comen como limas.", "Mi hijo estudia fuera. Sale más caro que un barco.", "Tengo un nieto ya. Me tiene sorbido el seso.",
    "No, no tengo. Sobrinos, eso sí, unos cuantos."],
  amable=["Dos, y son un cielo. Bueno, casi siempre.", "No tengo, pero me encantan los críos del barrio."],
  hablador=["Tengo dos. La mayor ha salido a mí, que no calla, y el pequeño a su abuelo, que no dice ni mu. En casa nos entendemos por señas.", "Uy, si te contara lo que me hizo ayer el pequeño..."],
  seco=["Dos.", "No."], timido=["No... todavía no.", "Uno. Es muy bueno."], chulo=["Dos, y han salido a mí. Triunfarán.", "No tengo tiempo para eso."], poca=["Eso es cosa mía."])

T("pareja_npc", "estas casado|estas casada|tienes pareja|tienes novio|tienes novia|tu marido|tu mujer|tu esposa|estas soltero|estas soltera|tienes a alguien", [
    "Eso es mucho preguntar para lo poco que nos conocemos.", "Casad{o} desde hace mil años. Y tan a gusto.", "Solter{o} y sin compromiso. Y sin prisa.",
    "Tuve a alguien. Ya no. Cosas que pasan.", "Estoy bien como estoy, gracias.", "Mi pareja trabaja en el mercado. Nos vemos a la hora de cenar.",
    "Viud{o}. Hace ya unos años.", "Mejor sol{o} que mal acompañad{o}, que decía mi madre."],
  amable=["Tengo pareja, sí, y estoy muy a gusto. Gracias por interesarte.", "Ahora mismo no, pero no pierdo la esperanza."],
  hablador=["Casad{o} veinte años, que se dice pronto. Nos conocimos en la feria, en los coches de choque, y desde entonces no hemos dejado de chocar.", "Uy, eso es largo de contar. Resumiendo: complicado."],
  seco=["Eso es cosa mía.", "Sí.", "No."], timido=["Eh... no. No tengo.", "Prefiero no hablar de eso."],
  chulo=["Lo que me sobran son pretendientes.", "Yo no me ato. Que me echen de menos."], poca=["No es asunto tuyo."])

T("tiempo", "que tiempo|el tiempo|hace calor|hace frio|va a llover|esta lloviendo|llueve|la lluvia|que calor|que frio|buen dia hace|mal dia hace|el sol|nublado|tormenta|viento|que dia hace", [
    "El tiempo está loco. Ya no hay estaciones.", "Aquí o te asas o te calas. No hay término medio.", "Con tal de que no sople levante, me conformo.",
    "Dicen que cambia mañana. También lo decían ayer.", "A mí que haga lo que quiera, que yo tengo que salir igual.", "En mis tiempos llovía cuando tenía que llover.",
    "Mientras no haya temporal, todo va bien.", "Hace un día de los de quedarse en la calle.", "Este tiempo me mata las rodillas.", "Si el cielo está así por la tarde, mañana hace bueno. Eso no falla.",
    "El hombre del tiempo no acierta una.", "Con esta humedad no se seca ni la ropa."],
  amable=["Hace un día precioso, ¿verdad? Da alegría salir.", "Con que no haga mucho viento, yo content{o}."],
  hablador=["Pues mira, mi rodilla dice que va a llover, y mi rodilla no ha fallado desde el noventa y dos. Ni el hombre del tiempo, vamos.", "El otro día cayó una que para qué. Se me inundó el portal y tuve que salir con las botas de pescar."],
  seco=["Hace lo que hace.", "Tiempo. Como siempre."], timido=["Sí... hace un poco de fresco.", "Creo que va a cambiar. No sé."],
  chulo=["A mí el tiempo me da igual. Yo voy igual de bien llueva o truene.", "Para calor, el de antes. Esto no es nada."])

T("hora", "que hora|la hora|tienes hora|es tarde|es pronto|que dia es|que dia es hoy", [
    "Deben de ser {hora}, más o menos.", "No llevo reloj, pero serán {hora}.", "{hora}, me parece. Se me pasa el día volando.", "Hora de irse a casa, eso seguro.",
    "{hora}. Y yo aquí todavía.", "Son {hora}. ¿Llegas tarde a algún sitio?"],
  amable=["Son {hora}. Si tienes prisa, no te entretengo.", "{hora}, me parece. Espera que lo miro bien. Sí, {hora}."],
  hablador=["Pues {hora}, que acabo de oír las campanas. Bueno, las campanas van adelantadas desde que las arreglaron, así que quítale cinco minutos."],
  seco=["{hora}."], timido=["{hora}... creo."], chulo=["{hora}. Cómprate un reloj."])

T("trabajo_duro", "mucho trabajo|trabajas mucho|te gusta tu trabajo|que tal el trabajo|como va el trabajo|el curro|tu jefe|te pagan bien|cuanto ganas|el sueldo|cobras", [
    "El trabajo, como siempre: mucho y mal pagado.", "No me quejo. Hay quien no tiene ni eso.", "Ser {oficio} tiene sus días. Hoy es de los malos.", "Me gusta lo que hago. No todo el mundo puede decirlo.",
    "El sueldo llega justo a fin de mes, y a veces ni eso.", "Mi jefe es un santo. Un santo de los que no hacen milagros.", "Llevo media vida de {oficio}. Ya no sabría hacer otra cosa.",
    "Hoy he tenido un día de perros en el trabajo.", "Lo de {oficio} da para vivir, que no es poco.", "Trabajo hay. Lo que no hay es quien lo pague.", "Cada día piden más y pagan menos.",
    "De {oficio} se aprende mucho de la gente."],
  amable=["Me gusta mucho. Ser {oficio} es muy agradecido.", "Va bien, gracias. Siempre hay faena, y eso es bueno."],
  hablador=["Pues mira, de {oficio} llevo desde los dieciséis, y he visto de todo. El otro día sin ir más lejos vino uno que... bueno, mejor no te lo cuento, que me buscas la ruina.",
            "El jefe me tiene frit{o}. Que si esto, que si lo otro. Yo le digo que sí a todo y luego hago lo que me parece."],
  seco=["Es trabajo.", "Paga las facturas."], timido=["Bien... me gusta. Es tranquilo.", "No se me da mal, creo."],
  chulo=["Soy {oficio}, y de l{o}s mejores. Pregunta a quien quieras.", "Sin mí, aquello se hunde. Lo saben todos."], poca=["Trabajo, que es más de lo que haces tú, por lo que veo."])

T("paro", "el paro|sin trabajo|estas en paro|buscas trabajo|no hay trabajo|desempleo|te han despedido|encontrar trabajo", [
    "Está la cosa muy mal. Hay más gente en la cola que en la playa.", "Mi cuñado lleva un año buscando y nada.", "Trabajo hay, pero de lo que no quiere nadie.",
    "En la oficina de empleo te dan número y esperanza, y poco más.", "Antes con el puerto había para todos. Ahora, ya ves.", "El que quiere trabajar, encuentra. Mal pagado, pero encuentra.",
    "Los jóvenes se van fuera. Aquí solo quedamos los de siempre.", "Si buscas algo, pásate por la oficina de empleo. Siempre hay jornadas sueltas."],
  amable=["Ojalá encuentres algo pronto. Aquí la gente ayuda.", "Es duro, pero no pierdas el ánimo."],
  hablador=["Mi sobrino estuvo dos años parado y al final se puso de repartidor. Ahora no para, el pobre. Dice que echa de menos aburrirse."],
  seco=["Mal está.", "Como siempre."], timido=["Es difícil... yo tuve suerte."], chulo=["El que vale, trabaja. Así de claro.", "A mí nunca me ha faltado."])

T("dinero", "el dinero|estas forrado|eres rico|eres rica|no tengo dinero|estoy sin blanca|la pasta|los precios|todo esta caro|que caro|sube todo|la inflacion|cuesta mucho|llegar a fin de mes", [
    "El dinero va y viene. Sobre todo va.", "Todo ha subido menos el sueldo.", "Con lo que cuesta hoy una barra de pan, antes comía una familia.",
    "Yo, mientras tenga para comer y para un café, feliz.", "A fin de mes llegamos, pero arrastrándonos.", "El que tiene dinero aquí es porque no pregunta de dónde viene.",
    "La luz, el agua, el alquiler... así no hay quien ahorre.", "Dinero llama a dinero. Al mío no lo llama nadie.", "Cuando hay rebajas, la gente se vuelve loca.",
    "Antes con cien euros llenabas el carro. Ahora no llenas ni la cesta."],
  amable=["No sobra, pero tampoco falta. Hay que dar gracias.", "Con poco se puede ser feliz, te lo digo yo."],
  hablador=["Fui a comprar ayer y casi me da algo. ¡Los tomates a precio de oro! Le dije al frutero: ¿esto qué es, fruta o joyería? Se rió, pero no me rebajó ni un céntimo."],
  seco=["Nunca sobra.", "Poco. Como todos."], timido=["Yo... voy justo. Como todos, supongo."],
  chulo=["A mí el dinero no me preocupa. Me sobra estilo.", "Yo siempre llevo. Otra cosa es que te lo vaya a enseñar."], poca=["Si vienes a pedir, te equivocas de persona."])

T("pedir_dinero", "me dejas dinero|me prestas|prestame|dejame dinero|dame algo|me das dinero|una ayuda|necesito dinero|tienes suelto|unas monedas|invitame|me invitas", [
    "Uy, no. Yo no llevo ni para mí.", "Si te dejara a ti, tendría que dejar a medio barrio.", "Lo siento, voy just{o}.", "Hoy no puedo. Otro día, si acaso.",
    "Dinero no, pero si tienes hambre, en el comedor social dan de comer.", "No presto. Así no pierdo ni el dinero ni los amigos.", "Pregunta en la oficina de empleo. Jornadas hay.",
    "Ojalá pudiera, de verdad."],
  amable=["Lo siento mucho, de verdad. Si pudiera, te lo daba.", "No llevo nada encima, pero te deseo suerte."],
  hablador=["¿Dinero? Si te cuento cómo está mi cuenta nos echamos a llorar los dos. Entre la hipoteca y el coche, que se me rompió el martes..."],
  seco=["No.", "No tengo."], timido=["Es que... no llevo. Perdona."], chulo=["¿Tengo cara de banco?", "Trabaja, como hacemos todos."],
  poca=["A ti no te daba ni la hora.", "Largo."], mucha=["Para ti, lo que haga falta, pero hoy estoy sin blanca, {tu}. De verdad."], confianza=-1)

T("comida", "que comes|comida favorita|te gusta comer|la comida|tienes hambre|tengo hambre|que has comido|que hay de comer|la paella|el pescado|el marisco|las tapas|cocinas|sabes cocinar|un buen plato", [
    "A mí dame un buen arroz y quédate con lo demás.", "El pescado, del día y a la plancha. No hay más secreto.", "Mi madre hace unas croquetas que resucitan a un muerto.",
    "Yo como de todo. Y se me nota.", "Las sardinas en el puerto, con las manos. Eso es comer.", "Para tapas, las del bar de la esquina. Sin discusión.",
    "Hoy he comido de bocadillo, que no he tenido tiempo.", "Un cocido en invierno y un gazpacho en verano. Y a vivir.", "La mejor comida es la que te hacen en casa.",
    "Ahora que lo dices, me está entrando hambre."],
  amable=["Si te gusta el arroz, tienes que probar el del domingo en el puerto. Te va a encantar.", "Yo cocino regular, pero le pongo cariño."],
  hablador=["Pues yo el arroz lo hago con el caldo de mi abuela, que lleva cabeza de rape y ñora, y un secreto que no te puedo decir porque me deshereda desde el otro mundo.",
            "Ayer hice lentejas para un regimiento. Llevo tres días comiendo lentejas."],
  seco=["Lo que haya.", "Como para vivir."], timido=["Me gusta... la tortilla. La de mi madre."], chulo=["Yo solo como bien. Para comer mal, no como.", "Mi paella no la supera nadie en {barrio}."])

T("bebida", "tomar algo|una cerveza|una cana|un vino|bebes|te gusta beber|el bar|los bares|una copa|estas borracho|estas borracha|el alcohol|un cafe", [
    "Una caña después del trabajo no se le niega a nadie.", "Yo, de café. El alcohol lo dejé hace tiempo.", "En el bar se arregla el mundo todas las tardes.",
    "Un vinito con la comida y ya está.", "Hay más bares que farmacias. Por algo será.", "Yo ya no bebo como antes. El hígado tiene memoria.",
    "El café de aquí al lado es el mejor. El de la plaza es agua sucia.", "Los viernes, una copa. Solo una. Bueno, dos."],
  amable=["Un café siempre apetece. Y con compañía, más.", "Si invitas tú, no digo que no."],
  hablador=["Pues en el bar de abajo ponen una tapa con cada caña que cenas gratis. Yo voy los jueves, que hay callos. Bueno, y los martes. Y algún lunes."],
  seco=["Café solo.", "No bebo."], timido=["Yo... un refresco. No bebo mucho."], chulo=["Yo aguanto lo que me echen.", "A mí en el bar me invitan. No pago yo."])

T("futbol", "futbol|el partido|tu equipo|de que equipo|la liga|el gol|el derbi|el arbitro|el estadio|el mundial|la seleccion", [
    "No me hables de fútbol, que este año vamos de pena.", "Yo soy del equipo de aquí, gane o pierda. Sobre todo pierda.", "El árbitro del domingo estaba comprado. Lo vio todo el mundo.",
    "A mí el fútbol ni fu ni fa.", "Antes se jugaba por la camiseta. Ahora, por la cartera.", "Si ganamos el derbi, me doy por satisfech{o} todo el año.",
    "No me pierdo un partido. Es lo único que me distrae.", "El fútbol, en el bar y con los amigos. En casa no es lo mismo.", "Este año subimos. Bueno, lo digo todos los años.",
    "Yo jugué de joven. Era mal{o}, pero ponía ganas."],
  amable=["Yo no entiendo mucho, pero me alegro cuando gana el equipo de aquí.", "¿Viste el partido? Yo lo oí por la radio."],
  hablador=["¡El gol del domingo! Yo estaba en el bar, y cuando marcaron se cayó una mesa entera. Tres cañas al suelo. Y el dueño, en vez de enfadarse, invitó a otra ronda."],
  seco=["No me gusta.", "Lo veo. Poco."], timido=["No... no sigo el fútbol."], chulo=["Si me hubieran fichado a mí, otro gallo cantaría.", "Yo de fútbol sé más que el entrenador."])

T("musica", "la musica|que musica|te gusta la musica|una cancion|cantas|sabes cantar|la radio|que emisora|el flamenco|el rock|bailar|bailas|un concierto|tocas algun", [
    "Yo, la radio puesta todo el día. Sin música no sé trabajar.", "Para música, la de antes. Lo de ahora es ruido.", "Me gusta de todo, menos lo que pone mi vecino.",
    "Yo canto en la ducha, y los vecinos lo saben.", "En las fiestas bailo hasta que me echan.", "Bravo FM, que ponen rock del bueno.", "Una guitarra y una noche de verano. No hace falta más.",
    "No tengo oído, pero tengo ganas.", "La música amansa a las fieras. A mi jefe, no."],
  amable=["Me encanta. Con música todo se lleva mejor.", "Yo canto fatal, pero me lo paso muy bien."],
  hablador=["Mi tío tocaba el acordeón en las verbenas, y yo iba detrás pasando la gorra. Así me pagué la primera bicicleta. Bueno, media bicicleta."],
  seco=["La radio. A veces.", "No mucho."], timido=["Escucho música... yo sol{o}, en casa."], chulo=["Yo bailo mejor que nadie en esta ciudad.", "Canto, toco y bailo. Y todo bien."])

T("barrio_vida", "se vive bien|te gusta vivir|como es vivir|es tranquilo|es peligroso|es seguro|los vecinos|la gente de aqui|que tal la gente|como es la gente|el ambiente", [
    "Aquí se vive bien si no te metes en líos.", "En {barrio} nos conocemos todos, para lo bueno y para lo malo.", "Tranquilo, lo que se dice tranquilo, no es. Pero es mi casa.",
    "La gente es buena. Un poco cotilla, pero buena.", "De día, sin problema. De noche, mira por dónde andas.", "Antes dejábamos la puerta abierta. Ahora, dos cerrojos.",
    "{ciudad} tiene de todo: mar, bares y gente rara.", "Los vecinos se ayudan. Eso no ha cambiado.", "Cada vez viene más gente de fuera, y se nota.", "No lo cambiaría por nada."],
  amable=["Es un sitio estupendo. La gente es muy acogedora, ya lo verás.", "Aquí siempre hay alguien que te echa una mano."],
  hablador=["En {barrio} pasa de todo y nos enteramos de todo. La del tercero, por ejemplo... bueno, eso no te lo cuento porque no la conoces, pero es para escribir una novela."],
  seco=["Se vive.", "Normal."], timido=["Es tranquilo... a mí me gusta."], chulo=["En {barrio} mandamos los de aquí. Y se vive como yo diga."])

T("ciudad_cambio", "ha cambiado|como era antes|antes era|los viejos tiempos|en tus tiempos|ya no es lo que era|la ciudad ha|todo cambia|el progreso|las obras", [
    "Esto antes era todo huerta. Ahora, bloques.", "Cuando yo era pequeñ{o}, se podía jugar en la calle.", "Han cambiado las tiendas, pero la gente es la misma.",
    "Antes el puerto daba de comer a media ciudad.", "Cada alcalde hace una rotonda y se va.", "Las obras de la avenida llevan tres años. Las pirámides tardaron menos.",
    "Todo cambia, menos el precio del café, que sube.", "Lo de antes no era mejor. Éramos más jóvenes, que no es lo mismo.", "Han cerrado el cine viejo. Ahí vi yo mi primera película."],
  hablador=["Donde está el banco había una vaquería, y donde la vaquería, antes, un huerto de mi tío abuelo. Lo vendió por cuatro perras y un burro. El burro vivió veinte años."],
  seco=["Todo cambia.", "A peor."], timido=["Yo... no me acuerdo mucho de antes."], chulo=["Esto lo levantamos los de aquí. Que no se olvide."],
  amable=["Ha cambiado mucho, pero sigue siendo un buen sitio.", "A mí me gusta más ahora. Hay más vida."])

T("policia", "la policia|los policias|la poli|los guardias|la comisaria|te han detenido|te busca la policia|me busca la policia|una multa|los maderos", [
    "La policía, cuanto más lejos, mejor.", "Hacen su trabajo. Otra cosa es que lo hagan bien.", "A mí nunca me han parado. Será que tengo cara de buena persona.",
    "Cuando los necesitas no están, y cuando no, te ponen una multa.", "Últimamente se les ve más. Algo pasará.", "Yo con ellos, buenos días y buenas tardes. Nada más.",
    "Mi primo es municipal. Buen chaval, pero no le cuentes nada.", "Dicen que hay alguno que cobra por mirar para otro lado."],
  amable=["Tienen un trabajo difícil. Yo no lo querría.", "Los del barrio son majos. Saludan y todo."],
  hablador=["El otro día pararon a mi vecino por ir sin luces en la bici. ¡En la bici! Le cayeron cincuenta euros. Ahora va andando y dice que por lo menos hace ejercicio."],
  seco=["Ni los quiero ni los busco.", "Mejor lejos."], timido=["Yo... me pongo nervios{o} cuando los veo. Y no he hecho nada."], chulo=["A mí la policía me saluda. Me conocen.", "No me asustan cuatro uniformes."],
  poca=["¿Por qué lo preguntas? ¿Has hecho algo?", "Como sigas así, los vas a conocer."])

T("delincuencia", "los robos|han robado|un robo|los ladrones|los atracos|un atraco|la delincuencia|hay peligro|las drogas|los camellos|trapicheo|el contrabando|la mafia|los matones", [
    "Cada vez hay más. Antes eso aquí no pasaba.", "Yo no veo nada, no oigo nada y no digo nada.", "Le entraron a la vecina la semana pasada. Se llevaron hasta el jamón.",
    "De eso mejor no hablar en la calle.", "Hay zonas por las que yo ya no paso de noche.", "Lo del contrabando en el puerto lo sabe todo el mundo. Y nadie hace nada.",
    "Mientras se maten entre ellos, a mí que me dejen tranquil{o}.", "Son cuatro, pero hacen ruido por cuarenta.", "La droga ha hecho mucho daño aquí. Muchos chavales perdidos."],
  hablador=["Dicen, y yo no he dicho nada, que el del almacén del muelle tiene más visitas de noche que de día. Y no van a comprar pescado."],
  seco=["No sé nada.", "No pregunto."], timido=["Me da miedo... prefiero no hablar de eso."], chulo=["A mí no se atreve a robarme nadie.", "Sé quién es quién. Y ellos saben quién soy yo."],
  amable=["Es una pena. Ten cuidado por las noches, ¿eh?"], poca=["Tú sabrás más que yo de eso."])

T("bandas", "las bandas|los calaveras|los lagartos|una banda|pandilla|pandilleros|las guerras de barrio|el territorio|quien manda aqui|quien manda en", [
    "De esos, cuanto menos se hable, mejor.", "Hay barrios enteros atemorizados por cuatro con pistola.", "Aquí manda el que más miedo da. Hoy unos, mañana otros.",
    "Antes eran cuatro críos con una moto. Ahora llevan pistola.", "Yo pago, callo y cierro pronto.", "Cuando se pelean entre ellos, lo pagamos los vecinos.",
    "Dicen que detrás hay gente con corbata.", "Si cambia de manos el barrio, que sea para bien."],
  hablador=["A mi primo le pidieron dinero por dejarle abrir la tienda. Les dijo que no. Ahora tiene la tienda en otro barrio."],
  seco=["No hablo de eso.", "Pregunta a otro."], timido=["No... de eso no sé nada. De verdad."], chulo=["A mí esos no me tosen.", "Los conozco desde críos. No son nadie."],
  amable=["Ten cuidado con esa gente, de verdad."], poca=["¿Eres uno de ellos? Pues entonces ya lo sabes."], confianza=0)

T("belmonte", "belmonte|octavio|el empresario|la familia belmonte|quien es belmonte", [
    "Belmonte es dueño de media ciudad. Y de la otra media, también.", "Dicen que empezó con un bar y ahora no hay negocio que no pase por él.", "De ese hombre no se habla. Y menos en la calle.",
    "Paga las fiestas del barrio. Con qué dinero, no lo sé.", "Hay quien lo quiere y quien le tiene miedo. Yo, ni lo uno ni lo otro: lejos.", "Sale en el periódico cada semana cortando una cinta.",
    "Mi padre trabajó para él. No habla de aquello."],
  seco=["No lo conozco.", "No digo nada."], timido=["Shh... ese nombre mejor no decirlo alto."], chulo=["Belmonte y yo nos tratamos de tú.", "Ese no es tan fiero como lo pintan."],
  hablador=["De Belmonte se cuentan mil cosas. Que si tiene una caja fuerte del tamaño de una habitación, que si no duerme nunca... Yo lo vi una vez de lejos. Es más bajito de lo que parece."],
  confianza=0)

T("puerto", "el puerto|los barcos|la pesca|los pescadores|pescar|la lonja|los muelles|un barco|sales a pescar|el pescado fresco", [
    "El puerto ya no es lo que era, pero sigue siendo el corazón de esto.", "Mi abuelo salía a pescar a las cuatro de la mañana. Eso era trabajar.", "En la lonja, a primera hora, se ve lo mejor.",
    "Cada año hay menos barcos y menos peces.", "Si te gusta pescar, en el espigón pican bien al atardecer.", "El mar da y el mar quita.", "Los pescadores de aquí saben más del tiempo que la televisión.",
    "Con una caña y paciencia, cenas gratis."],
  hablador=["Yo salí una vez a la mar con mi cuñado. Una. Me mareé antes de soltar amarras y él todavía se lo cuenta a todo el mundo en Navidad."],
  seco=["Hay barcos.", "Ahí está."], timido=["Me gusta ir a mirar los barcos... es tranquilo."], chulo=["Yo he sacado un atún así de grande. Pregunta en la lonja.", "El mar no tiene secretos para mí."],
  amable=["El puerto al amanecer es precioso. Tienes que verlo."])

T("mar_playa", "el mar|la playa|banarse|nadar|sabes nadar|las olas|la arena|tomar el sol|los turistas|el verano|las vacaciones|veranear|te vas de vacaciones", [
    "Teniendo el mar al lado, ¿para qué irse de vacaciones?", "En agosto no cabe un alfiler en la playa.", "Los turistas dejan dinero y basura, a partes iguales.",
    "Yo me baño todo el año. Bueno, hasta octubre.", "No sé nadar, y vivo en la costa. Ya ves.", "Vacaciones, las justas. Una semana en el pueblo y gracias.",
    "El mar en invierno es lo mejor. No hay nadie.", "Cuando hay operación salida, de aquí no se puede ni salir ni entrar.", "El verano es para los de fuera. Los de aquí trabajamos."],
  amable=["La playa por la tarde es una maravilla. Te la recomiendo.", "Yo paseo por la orilla todos los días. Es mi medicina."],
  hablador=["Este verano ha venido tanta gente que el del chiringuito se ha comprado un coche nuevo. En agosto. Al contado."],
  seco=["Está ahí.", "No voy."], timido=["Yo voy... cuando no hay gente."], chulo=["En la playa, el más moreno soy yo.", "Yo nado hasta la boya y vuelvo sin despeinarme."])

T("coches", "tu coche|los coches|el trafico|los atascos|conduces|sabes conducir|una moto|las motos|aparcar|el aparcamiento|la gasolina|el carne|correr con el coche|las carreras", [
    "Aparcar aquí es una lotería. Y nunca toca.", "La gasolina está por las nubes.", "Yo voy andando a todas partes. Así no me multan.", "Tengo un coche que tiene más años que yo, pero arranca.",
    "Los que corren por la avenida de noche van a matar a alguien.", "En hora punta se tarda más en coche que a pie.", "Las motos pasan que parecen aviones.",
    "Dicen que hay carreras de noche. Yo oigo los motores desde la cama.", "Con los semáforos que han puesto, ya no hay quien cruce la ciudad."],
  hablador=["Mi coche hace un ruido raro desde hace un año. El mecánico dice que es el embrague, mi cuñado que es la correa, y yo creo que es que está harto de mí."],
  seco=["Voy a pie.", "Tengo uno. Anda."], timido=["No conduzco... me da cosa."], chulo=["Nadie conduce como yo en esta ciudad.", "Mi coche lo conoce todo el barrio por el ruido."],
  amable=["Ten cuidado con el coche, que hay mucho loco suelto."])

T("transporte", "el autobus|los autobuses|un taxi|los taxis|la estacion|como se va a|como llego a|ir a otra ciudad|ir a otro pueblo|viajar|el viaje|la carretera", [
    "El autobús sale de la estación. Barato, pero lento.", "Los taxis están en la parada. Te llevan donde quieras si pagas.", "Para ir a los pueblos, por las salidas de la ciudad. Están señalizadas.",
    "El autobús pasa cuando quiere, no cuando dice el horario.", "Si vas lejos, mejor en autobús que conduciendo. Te ahorras el susto.", "Por mar también se llega a muchos sitios, si tienes barca.",
    "La carretera de la costa es bonita, pero tiene curvas para aburrir."],
  amable=["Si no sabes ir, pregunta en la estación. Son muy amables."], hablador=["Yo una vez cogí el autobús equivocado y acabé en la sierra. Me comí un cordero buenísimo, eso sí."],
  seco=["En autobús.", "En la estación te dicen."], timido=["Creo que hay autobuses... en la estación."], chulo=["Yo no cojo autobuses. Me llevan."])

T("salud", "la salud|estas enfermo|estas enferma|el medico|el hospital|te duele|un dolor|la gripe|un resfriado|las pastillas|la farmacia|estas herido|estas herida|te has hecho dano", [
    "Mientras haya salud, lo demás se arregla.", "Me duele todo, pero el médico dice que estoy como un roble.", "En el hospital te atienden bien. Cuando te atienden.",
    "A mi edad, si no te duele algo es que estás muert{o}.", "Yo voy al médico lo justo. Me pone nervios{o}.", "La farmacia de aquí al lado es muy apañada.",
    "Un resfriado me tuvo en cama la semana pasada.", "Si estás herid{o}, ve al hospital. No te hagas el valiente."],
  amable=["Cuídate mucho, que la salud es lo primero.", "Si te encuentras mal, hay una farmacia cerca. No lo dejes."],
  hablador=["Fui al médico por la rodilla y salí con pastillas para la tensión, el colesterol y el azúcar. De la rodilla no me dijo nada."],
  seco=["Estoy bien.", "Vete al médico."], timido=["Yo... estoy bien, gracias. Un poco de alergia."], chulo=["Yo no me pongo enferm{o}. No tengo tiempo.", "Fuerte como un toro."])

T("cansancio", "estoy cansado|estoy cansada|estas cansado|estas cansada|tengo sueno|que sueno|no he dormido|dormir|has dormido|madrugar|el madrugon", [
    "A quién se lo vas a contar. Llevo en pie desde las seis.", "Yo duermo poco y mal. Cosas de la edad.", "Una siesta lo arregla todo.", "Si tienes sueño, vete a dormir. El cuerpo manda.",
    "Madrugar no es de este mundo.", "Yo sin mis ocho horas no soy persona.", "Hay un hotel por aquí si no tienes dónde dormir."],
  amable=["Descansa, que se te ve cara de cansancio.", "Pobre. Un café y a casa."], hablador=["Yo anoche no pegué ojo. El vecino de arriba, que se ha comprado una batería. ¡Una batería! Con sesenta años."],
  seco=["Pues duerme.", "Yo también."], timido=["Yo también tengo sueño... siempre."], chulo=["Dormir es de flojos.", "Yo con cuatro horas voy sobrad{o}."])

T("fiestas", "las fiestas|la feria|la verbena|la fiesta|hoy es fiesta|el mercado|dia de mercado|las rebajas|la huelga|los fuegos|la procesion|carnaval|navidad|las fallas", [
    "En fiestas no duerme nadie. Ni quien quiere.", "La feria ya no es como antes, pero los críos lo pasan bien.", "El día de mercado baja medio pueblo. No se puede ni andar.",
    "Con las rebajas, la gente compra lo que no necesita.", "Si hay huelga, mejor quedarse en casa.", "Los fuegos del último día son lo mejor.", "Yo en fiestas me voy. No aguanto el ruido.",
    "Para la verbena tiran la casa por la ventana.", "En el mercado está todo más barato, si sabes regatear."],
  amable=["Las fiestas son preciosas. Tienes que venir.", "Me encanta el mercado. Te encuentras a todo el mundo."],
  hablador=["En la verbena del año pasado bailé hasta las cinco. Con mi rodilla. Estuve una semana sin poder bajar la escalera, pero mereció la pena."],
  seco=["Mucho ruido.", "No voy."], timido=["Hay mucha gente... yo voy un rato y me vuelvo."], chulo=["En fiestas, el rey soy yo.", "Sin mí, la verbena no empieza."])

T("politica", "el alcalde|la alcaldesa|el ayuntamiento|los politicos|la politica|el gobierno|las elecciones|a quien votas|los impuestos|los concejales", [
    "Son todos iguales. Prometen y luego ni se acuerdan.", "El alcalde solo aparece en la foto.", "De política y de religión, en la calle no se habla.", "Impuestos, todos. Servicios, ninguno.",
    "Yo voto, que para eso costó conseguirlo. Luego me arrepiento.", "Arreglaron la plaza justo antes de las elecciones. Qué casualidad.", "Mientras tapen los baches, me da igual quién mande.",
    "El ayuntamiento está para lo que está: para cobrar."],
  hablador=["Fui al ayuntamiento por un papel y me mandaron a tres ventanillas. En la tercera me dijeron que volviera a la primera. Me llevé la merienda al día siguiente."],
  seco=["No opino.", "Todos iguales."], timido=["Yo de eso... no entiendo."], chulo=["Si yo fuera alcalde, esto estaría arreglado en dos días.", "A esos los pongo yo firmes."],
  amable=["Alguno habrá que lo haga bien, digo yo."])

T("animales", "tu perro|un perro|los perros|un gato|los gatos|tienes mascota|tienes perro|los animales|las gaviotas|la protectora|adoptar", [
    "Tengo un perro que es más listo que algunos vecinos.", "Los gatos del puerto están mejor alimentados que yo.", "Las gaviotas te roban el bocadillo de la mano.",
    "En la protectora siempre hay perros buscando casa.", "Yo quise un perro, pero en mi piso no cabe ni yo.", "Mi gato manda en casa. Yo solo pago.", "Un perro te cambia la vida. Y los zapatos.",
    "Dicen que un perro bien enseñado encuentra cosas enterradas."],
  amable=["Me encantan los animales. Si puedes, adopta uno.", "Mi perro es mi mejor compañía."],
  hablador=["Mi perro se llama Capitán y ladra a todos menos a los ladrones. Entraron una vez y les movió el rabo. Les faltó llevárselo."],
  seco=["No tengo.", "Un perro."], timido=["Tengo un gato... se llama Miga."], chulo=["Mi perro es como yo: no le tose nadie.", "Los perros me obedecen a la primera."])

T("ninos_colegio", "el colegio|la escuela|los estudios|estudias|has estudiado|la universidad|los profesores|los deberes|aprender|un curso|la academia", [
    "Yo estudié lo justo. La calle enseña más.", "Mi hijo saca mejores notas que las que saqué yo en toda mi vida.", "En la academia dan cursos. Nunca es tarde para aprender.",
    "Me hubiera gustado estudiar más, pero había que trabajar.", "Los críos de ahora saben mucho de pantallas y poco de la vida.", "Un buen maestro vale más que cien libros.",
    "Estudiar no sé, pero aprender se aprende todos los días."],
  amable=["Estudiar siempre viene bien. Anímate.", "Mis profesores fueron muy buenos conmigo."], hablador=["A mí me echaron de clase por hablar. Tres veces. En el mismo día."],
  seco=["Estudié poco.", "No era lo mío."], timido=["Me gustaba estudiar... era lo único que se me daba bien."], chulo=["Yo no necesité estudiar. Nací sabiendo.", "El más listo de mi clase, y no abría un libro."])

T("deporte", "el gimnasio|haces deporte|el deporte|correr|sales a correr|estas fuerte|estas en forma|el boxeo|boxeas|pelear|las pesas|la bici|montar en bici", [
    "Mi deporte es subir la cuesta de casa con la compra.", "En el gimnasio de aquí se entrena bien. Y hay combates.", "Yo corría de joven. Ahora corro si me persiguen.",
    "El boxeo enseña disciplina. A mí me enseñó a agacharme.", "Voy en bici a todas partes. Barato y sano.", "Debería hacer algo, pero el sofá tira mucho.",
    "Andar una hora al día. Me lo dijo el médico y le hago caso a medias."],
  amable=["Hacer deporte sienta muy bien. Yo salgo a andar."], hablador=["Me apunté al gimnasio en enero. Fui dos días. Llevo pagando desde entonces porque me da vergüenza ir a borrarme."],
  seco=["Ando.", "No."], timido=["Yo... camino. Sol{o}."], chulo=["Mira qué brazos. Esto no sale solo.", "En el ring no me dura nadie dos asaltos."])
