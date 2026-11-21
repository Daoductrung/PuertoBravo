"""Base de respuestas, primera parte: la persona, su vida y el día a día."""
from .i18n import tr
from .respuestas import T

T("como_estas", tr("como estas|como te va|como andas|que tal estas|como lo llevas|como va todo|todo bien|estas bien|te encuentras bien|como va eso|que tal todo|que tal va"), [
    tr("Tirando, que no es poco."), tr("Bien, sin más. No me quejo."), tr("Aquí estamos, que ya es bastante."), tr("Regular. Días mejores he tenido."), tr("Bien, gracias. ¿Y tú?"),
    tr("Como siempre: mucho trabajo y poco sueldo."), tr("Hoy bien. Mañana ya veremos."), tr("Voy tirando. La espalda me da guerra, pero bien."), tr("No me puedo quejar, y si me quejo da igual."),
    tr("Bien, de verdad. Hoy me he levantado con buen pie."), tr("Cansad{o}, pero content{o}."), tr("Pues mira, de salud bien, que es lo importante.")],
  amable=[tr("Muy bien, gracias por preguntar. Da gusto que alguien pregunte."), tr("Bien, bien. Mejor ahora que hablamos un rato."), tr("Estupendamente. Hace un día para estar bien.")],
  hablador=[tr("Pues bien, aunque esta mañana me he levantado con un dolor aquí en el costado que no veas, pero se me ha pasado con un café."), tr("Bien, liad{o} como siempre, que no paro ni para respirar."),
            tr("Mejor que ayer, que ayer tuve un día que para qué te voy a contar.")],
  seco=[tr("Bien."), tr("Normal."), tr("Tirando."), tr("Vivo, que no es poco.")], timido=[tr("Bien... creo. Gracias."), tr("Bien, bien. No me pasa nada."), tr("Bueno, un poco nervios{o}, pero bien.")],
  chulo=[tr("Yo siempre estoy bien. Los que están mal son los demás."), tr("Como un rey. ¿No se me nota?"), tr("Mejor que tú, seguro.")],
  poca=[tr("Estaba mejor antes de que llegaras."), tr("Bien. Y con prisa."), tr("Eso a ti no te importa.")], mucha=[tr("Mejor ahora que te veo, {tu}."), tr("Bien, {tu}. Contigo siempre se anima uno.")])

T("nombre", tr("como te llamas|tu nombre|quien eres|como es tu nombre|te llamas|con quien hablo"), [
    tr("Me llamo {yo}."), tr("{yo}, para servirte."), tr("Soy {yo}. Aquí me conoce todo el mundo."), tr("{yo}. ¿Y tú?"), tr("{yo} me pusieron, y con {yo} me he quedado."),
    tr("Me llaman {yo}. Soy {oficio}."), tr("{yo}. Encantad{o}."), tr("Soy {yo}, de aquí de toda la vida.")],
  amable=[tr("{yo}, mucho gusto. ¿Y tú cómo te llamas?"), tr("Me llamo {yo}. Qué bien que preguntes, la gente ya ni se presenta.")],
  hablador=[tr("{yo}, como mi abuelo, que también se llamaba así y era igual de charlatán."), tr("{yo}. Bueno, en casa me dicen de otra manera, pero eso no te lo cuento.")],
  seco=["{yo}.", tr("{yo}. ¿Algo más?")], timido=[tr("{yo}... me llamo {yo}."), tr("Me llamo {yo}. Perdona, no me había presentado.")],
  chulo=[tr("{yo}. Apúntatelo, que te va a sonar."), tr("¿No sabes quién soy? {yo}. Pregunta por ahí.")], poca=[tr("¿Y para qué quieres saberlo?"), tr("Eso no te hace falta.")],
  mucha=[tr("Pero si ya lo sabes, {tu}. {yo}, el de siempre.") ])

T("edad", tr("cuantos anos|que edad|tu edad|eres joven|eres mayor|eres viejo|eres vieja|cuando naciste"), [
    tr("Los que aparento, ni uno más."), tr("Demasiados para lo que me queda por hacer."), tr("Suficientes para saber de qué va esto."), tr("Eso no se pregunta, hombre."),
    tr("Los justos. Ni muchos ni pocos."), tr("Ya no soy un chaval, eso seguro."), tr("Más de los que quisiera y menos de los que me echan."), tr("La edad está en la cabeza, dicen. Pues en la cabeza tengo veinte.")],
  amable=[tr("Ay, ya tengo unos cuantos, pero los llevo bien."), tr("Los que tengo los he vivido a gusto, que es lo que importa.")],
  hablador=[tr("Pues mira, nací el año que se inundó el mercado, así que echa cuentas. Y me acuerdo perfectamente, bueno, me lo contaron."), tr("Tengo los mismos que mi prima la del puerto, que nacimos con dos días de diferencia.")],
  seco=[tr("Los que tengo."), tr("Eso no se pregunta.")], timido=[tr("Eh... prefiero no decirlo."), tr("No muchos... bueno, alguno.")],
  chulo=[tr("Los suficientes para darte dos vueltas."), tr("Estoy en mi mejor momento. Siempre lo estoy.")], poca=[tr("¿Y a ti qué te importa?")])

T("de_donde", tr("de donde eres|eres de aqui|naciste aqui|de que pueblo|de donde vienes|eres de fuera|llevas mucho aqui|cuanto llevas aqui|siempre has vivido"), [
    tr("De aquí de toda la vida. No he salido ni de vacaciones."), tr("Nací en {ciudad} y aquí me moriré, si me dejan."), tr("Vine de joven por trabajo y ya ves, me quedé."),
    tr("Mis abuelos eran del interior, pero yo soy de mar."), tr("De {barrio}. Nací a dos calles de aquí."), tr("De aquí. Bueno, mi madre era de un pueblo de la sierra."),
    tr("Llevo aquí tanto que ya ni me acuerdo de cuándo llegué."), tr("Soy de {ciudad}, que no es lo mismo que ser de los alrededores.")],
  amable=[tr("De aquí, y muy a gusto. Es un buen sitio para vivir."), tr("Soy de fuera, pero me acogieron tan bien que ya soy de aquí.")],
  hablador=[tr("Yo nací en {barrio}, en la casa que hacía esquina, que ahora es una tienda. Mi padre también, y mi abuelo. Somos cuatro generaciones ya."), tr("De aquí, de aquí. Bueno, estuve dos años fuera y casi me muero de la pena.")],
  seco=[tr("De aquí."), tr("De {ciudad}.")], timido=[tr("De aquí cerca... de {barrio}."), tr("Soy de aquí. No he salido mucho.")],
  chulo=[tr("De {barrio}, de pura cepa. De los de verdad."), tr("Yo soy de aquí. Los que venís de fuera se os nota a la legua.")], poca=[tr("De por ahí.")])

T("familia", tr("tu familia|tienes familia|tus padres|tu madre|tu padre|tienes hermanos|tu hermano|tu hermana|tus abuelos|tu abuela|tu abuelo|vives solo|vives sola|con quien vives"), [
    tr("La familia bien, gracias. Cada uno a lo suyo."), tr("Somos pocos, pero bien avenidos."), tr("Mi madre sigue viviendo en la casa de siempre. No hay quien la saque."),
    tr("Tengo un hermano fuera. Llama por Navidad y poco más."), tr("La familia, como todas: unos días mejor y otros peor."), tr("Vivo sol{o}. Se está tranquil{o}."),
    tr("Mi padre era pescador. De él aprendí lo poco que sé."), tr("Los domingos comemos todos juntos. Es sagrado."), tr("Mi abuela decía que la familia es lo único que no se elige. Y tenía razón."),
    tr("Bien todos, que yo sepa. Hace días que no hablo con ellos.")],
  amable=[tr("Muy bien todos, gracias. Mi madre te caería bien."), tr("Tengo una familia estupenda, la verdad. He tenido suerte.")],
  hablador=[tr("Uy, mi familia. Somos siete hermanos, y cada uno de su padre y de su madre, como quien dice. El mayor está en el puerto, la segunda puso una mercería, el tercero no sabemos dónde anda..."),
            tr("Mi madre, con ochenta y tantos, sale todos los días a por el pan y vuelve con las noticias de todo el barrio.")],
  seco=[tr("Bien."), tr("Cada uno en su casa.")], timido=[tr("Bien... no hablamos mucho."), tr("Vivo con mi madre. Estamos bien.")],
  chulo=[tr("En mi familia somos todos igual de guapos. Qué te voy a contar."), tr("Mi padre mandaba en {barrio}. Algo se hereda.")], poca=[tr("De mi familia no hablo con desconocidos.")])

T("hijos", tr("tienes hijos|tus hijos|tu hijo|tu hija|tienes ninos|los ninos|los crios|tus nietos"), [
    tr("Dos, y ya crecidos. Ni se acuerdan de llamar."), tr("No tengo. Bastante tengo conmigo."), tr("Una niña. Es lo mejor que he hecho."), tr("Tres, y los tres distintos como la noche y el día."),
    tr("Los críos bien, creciendo. Comen como limas."), tr("Mi hijo estudia fuera. Sale más caro que un barco."), tr("Tengo un nieto ya. Me tiene sorbido el seso."),
    tr("No, no tengo. Sobrinos, eso sí, unos cuantos.")],
  amable=[tr("Dos, y son un cielo. Bueno, casi siempre."), tr("No tengo, pero me encantan los críos del barrio.")],
  hablador=[tr("Tengo dos. La mayor ha salido a mí, que no calla, y el pequeño a su abuelo, que no dice ni mu. En casa nos entendemos por señas."), tr("Uy, si te contara lo que me hizo ayer el pequeño...")],
  seco=[tr("Dos."), tr("No.")], timido=[tr("No... todavía no."), tr("Uno. Es muy bueno.")], chulo=[tr("Dos, y han salido a mí. Triunfarán."), tr("No tengo tiempo para eso.")], poca=[tr("Eso es cosa mía.")])

T("pareja_npc", tr("estas casado|estas casada|tienes pareja|tienes novio|tienes novia|tu marido|tu mujer|tu esposa|estas soltero|estas soltera|tienes a alguien"), [
    tr("Eso es mucho preguntar para lo poco que nos conocemos."), tr("Casad{o} desde hace mil años. Y tan a gusto."), tr("Solter{o} y sin compromiso. Y sin prisa."),
    tr("Tuve a alguien. Ya no. Cosas que pasan."), tr("Estoy bien como estoy, gracias."), tr("Mi pareja trabaja en el mercado. Nos vemos a la hora de cenar."),
    tr("Viud{o}. Hace ya unos años."), tr("Mejor sol{o} que mal acompañad{o}, que decía mi madre.")],
  amable=[tr("Tengo pareja, sí, y estoy muy a gusto. Gracias por interesarte."), tr("Ahora mismo no, pero no pierdo la esperanza.")],
  hablador=[tr("Casad{o} veinte años, que se dice pronto. Nos conocimos en la feria, en los coches de choque, y desde entonces no hemos dejado de chocar."), tr("Uy, eso es largo de contar. Resumiendo: complicado.")],
  seco=[tr("Eso es cosa mía."), tr("Sí."), tr("No.")], timido=[tr("Eh... no. No tengo."), tr("Prefiero no hablar de eso.")],
  chulo=[tr("Lo que me sobran son pretendientes."), tr("Yo no me ato. Que me echen de menos.")], poca=[tr("No es asunto tuyo.")])

T("tiempo", tr("que tiempo|el tiempo|hace calor|hace frio|va a llover|esta lloviendo|llueve|la lluvia|que calor|que frio|buen dia hace|mal dia hace|el sol|nublado|tormenta|viento|que dia hace"), [
    tr("El tiempo está loco. Ya no hay estaciones."), tr("Aquí o te asas o te calas. No hay término medio."), tr("Con tal de que no sople levante, me conformo."),
    tr("Dicen que cambia mañana. También lo decían ayer."), tr("A mí que haga lo que quiera, que yo tengo que salir igual."), tr("En mis tiempos llovía cuando tenía que llover."),
    tr("Mientras no haya temporal, todo va bien."), tr("Hace un día de los de quedarse en la calle."), tr("Este tiempo me mata las rodillas."), tr("Si el cielo está así por la tarde, mañana hace bueno. Eso no falla."),
    tr("El hombre del tiempo no acierta una."), tr("Con esta humedad no se seca ni la ropa.")],
  amable=[tr("Hace un día precioso, ¿verdad? Da alegría salir."), tr("Con que no haga mucho viento, yo content{o}.")],
  hablador=[tr("Pues mira, mi rodilla dice que va a llover, y mi rodilla no ha fallado desde el noventa y dos. Ni el hombre del tiempo, vamos."), tr("El otro día cayó una que para qué. Se me inundó el portal y tuve que salir con las botas de pescar.")],
  seco=[tr("Hace lo que hace."), tr("Tiempo. Como siempre.")], timido=[tr("Sí... hace un poco de fresco."), tr("Creo que va a cambiar. No sé.")],
  chulo=[tr("A mí el tiempo me da igual. Yo voy igual de bien llueva o truene."), tr("Para calor, el de antes. Esto no es nada.")])

T("hora", tr("que hora|la hora|tienes hora|es tarde|es pronto|que dia es|que dia es hoy"), [
    tr("Deben de ser {hora}, más o menos."), tr("No llevo reloj, pero serán {hora}."), tr("{hora}, me parece. Se me pasa el día volando."), tr("Hora de irse a casa, eso seguro."),
    tr("{hora}. Y yo aquí todavía."), tr("Son {hora}. ¿Llegas tarde a algún sitio?")],
  amable=[tr("Son {hora}. Si tienes prisa, no te entretengo."), tr("{hora}, me parece. Espera que lo miro bien. Sí, {hora}.")],
  hablador=[tr("Pues {hora}, que acabo de oír las campanas. Bueno, las campanas van adelantadas desde que las arreglaron, así que quítale cinco minutos.")],
  seco=["{hora}."], timido=[tr("{hora}... creo.")], chulo=[tr("{hora}. Cómprate un reloj.")])

T("trabajo_duro", tr("mucho trabajo|trabajas mucho|te gusta tu trabajo|que tal el trabajo|como va el trabajo|el curro|tu jefe|te pagan bien|cuanto ganas|el sueldo|cobras"), [
    tr("El trabajo, como siempre: mucho y mal pagado."), tr("No me quejo. Hay quien no tiene ni eso."), tr("Ser {oficio} tiene sus días. Hoy es de los malos."), tr("Me gusta lo que hago. No todo el mundo puede decirlo."),
    tr("El sueldo llega justo a fin de mes, y a veces ni eso."), tr("Mi jefe es un santo. Un santo de los que no hacen milagros."), tr("Llevo media vida de {oficio}. Ya no sabría hacer otra cosa."),
    tr("Hoy he tenido un día de perros en el trabajo."), tr("Lo de {oficio} da para vivir, que no es poco."), tr("Trabajo hay. Lo que no hay es quien lo pague."), tr("Cada día piden más y pagan menos."),
    tr("De {oficio} se aprende mucho de la gente.")],
  amable=[tr("Me gusta mucho. Ser {oficio} es muy agradecido."), tr("Va bien, gracias. Siempre hay faena, y eso es bueno.")],
  hablador=[tr("Pues mira, de {oficio} llevo desde los dieciséis, y he visto de todo. El otro día sin ir más lejos vino uno que... bueno, mejor no te lo cuento, que me buscas la ruina."),
            tr("El jefe me tiene frit{o}. Que si esto, que si lo otro. Yo le digo que sí a todo y luego hago lo que me parece.")],
  seco=[tr("Es trabajo."), tr("Paga las facturas.")], timido=[tr("Bien... me gusta. Es tranquilo."), tr("No se me da mal, creo.")],
  chulo=[tr("Soy {oficio}, y de l{o}s mejores. Pregunta a quien quieras."), tr("Sin mí, aquello se hunde. Lo saben todos.")], poca=[tr("Trabajo, que es más de lo que haces tú, por lo que veo.")])

T("paro", tr("el paro|sin trabajo|estas en paro|buscas trabajo|no hay trabajo|desempleo|te han despedido|encontrar trabajo"), [
    tr("Está la cosa muy mal. Hay más gente en la cola que en la playa."), tr("Mi cuñado lleva un año buscando y nada."), tr("Trabajo hay, pero de lo que no quiere nadie."),
    tr("En la oficina de empleo te dan número y esperanza, y poco más."), tr("Antes con el puerto había para todos. Ahora, ya ves."), tr("El que quiere trabajar, encuentra. Mal pagado, pero encuentra."),
    tr("Los jóvenes se van fuera. Aquí solo quedamos los de siempre."), tr("Si buscas algo, pásate por la oficina de empleo. Siempre hay jornadas sueltas.")],
  amable=[tr("Ojalá encuentres algo pronto. Aquí la gente ayuda."), tr("Es duro, pero no pierdas el ánimo.")],
  hablador=[tr("Mi sobrino estuvo dos años parado y al final se puso de repartidor. Ahora no para, el pobre. Dice que echa de menos aburrirse.")],
  seco=[tr("Mal está."), tr("Como siempre.")], timido=[tr("Es difícil... yo tuve suerte.")], chulo=[tr("El que vale, trabaja. Así de claro."), tr("A mí nunca me ha faltado.")])

T("dinero", tr("el dinero|estas forrado|eres rico|eres rica|no tengo dinero|estoy sin blanca|la pasta|los precios|todo esta caro|que caro|sube todo|la inflacion|cuesta mucho|llegar a fin de mes"), [
    tr("El dinero va y viene. Sobre todo va."), tr("Todo ha subido menos el sueldo."), tr("Con lo que cuesta hoy una barra de pan, antes comía una familia."),
    tr("Yo, mientras tenga para comer y para un café, feliz."), tr("A fin de mes llegamos, pero arrastrándonos."), tr("El que tiene dinero aquí es porque no pregunta de dónde viene."),
    tr("La luz, el agua, el alquiler... así no hay quien ahorre."), tr("Dinero llama a dinero. Al mío no lo llama nadie."), tr("Cuando hay rebajas, la gente se vuelve loca."),
    tr("Antes con cien euros llenabas el carro. Ahora no llenas ni la cesta.")],
  amable=[tr("No sobra, pero tampoco falta. Hay que dar gracias."), tr("Con poco se puede ser feliz, te lo digo yo.")],
  hablador=[tr("Fui a comprar ayer y casi me da algo. ¡Los tomates a precio de oro! Le dije al frutero: ¿esto qué es, fruta o joyería? Se rió, pero no me rebajó ni un céntimo.")],
  seco=[tr("Nunca sobra."), tr("Poco. Como todos.")], timido=[tr("Yo... voy justo. Como todos, supongo.")],
  chulo=[tr("A mí el dinero no me preocupa. Me sobra estilo."), tr("Yo siempre llevo. Otra cosa es que te lo vaya a enseñar.")], poca=[tr("Si vienes a pedir, te equivocas de persona.")])

T("pedir_dinero", tr("me dejas dinero|me prestas|prestame|dejame dinero|dame algo|me das dinero|una ayuda|necesito dinero|tienes suelto|unas monedas|invitame|me invitas"), [
    tr("Uy, no. Yo no llevo ni para mí."), tr("Si te dejara a ti, tendría que dejar a medio barrio."), tr("Lo siento, voy just{o}."), tr("Hoy no puedo. Otro día, si acaso."),
    tr("Dinero no, pero si tienes hambre, en el comedor social dan de comer."), tr("No presto. Así no pierdo ni el dinero ni los amigos."), tr("Pregunta en la oficina de empleo. Jornadas hay."),
    tr("Ojalá pudiera, de verdad.")],
  amable=[tr("Lo siento mucho, de verdad. Si pudiera, te lo daba."), tr("No llevo nada encima, pero te deseo suerte.")],
  hablador=[tr("¿Dinero? Si te cuento cómo está mi cuenta nos echamos a llorar los dos. Entre la hipoteca y el coche, que se me rompió el martes...")],
  seco=[tr("No."), tr("No tengo.")], timido=[tr("Es que... no llevo. Perdona.")], chulo=[tr("¿Tengo cara de banco?"), tr("Trabaja, como hacemos todos.")],
  poca=[tr("A ti no te daba ni la hora."), tr("Largo.")], mucha=[tr("Para ti, lo que haga falta, pero hoy estoy sin blanca, {tu}. De verdad.")], confianza=-1)

T("comida", tr("que comes|comida favorita|te gusta comer|la comida|tienes hambre|tengo hambre|que has comido|que hay de comer|la paella|el pescado|el marisco|las tapas|cocinas|sabes cocinar|un buen plato"), [
    tr("A mí dame un buen arroz y quédate con lo demás."), tr("El pescado, del día y a la plancha. No hay más secreto."), tr("Mi madre hace unas croquetas que resucitan a un muerto."),
    tr("Yo como de todo. Y se me nota."), tr("Las sardinas en el puerto, con las manos. Eso es comer."), tr("Para tapas, las del bar de la esquina. Sin discusión."),
    tr("Hoy he comido de bocadillo, que no he tenido tiempo."), tr("Un cocido en invierno y un gazpacho en verano. Y a vivir."), tr("La mejor comida es la que te hacen en casa."),
    tr("Ahora que lo dices, me está entrando hambre.")],
  amable=[tr("Si te gusta el arroz, tienes que probar el del domingo en el puerto. Te va a encantar."), tr("Yo cocino regular, pero le pongo cariño.")],
  hablador=[tr("Pues yo el arroz lo hago con el caldo de mi abuela, que lleva cabeza de rape y ñora, y un secreto que no te puedo decir porque me deshereda desde el otro mundo."),
            tr("Ayer hice lentejas para un regimiento. Llevo tres días comiendo lentejas.")],
  seco=[tr("Lo que haya."), tr("Como para vivir.")], timido=[tr("Me gusta... la tortilla. La de mi madre.")], chulo=[tr("Yo solo como bien. Para comer mal, no como."), tr("Mi paella no la supera nadie en {barrio}.")])

T("bebida", tr("tomar algo|una cerveza|una cana|un vino|bebes|te gusta beber|el bar|los bares|una copa|estas borracho|estas borracha|el alcohol|un cafe"), [
    tr("Una caña después del trabajo no se le niega a nadie."), tr("Yo, de café. El alcohol lo dejé hace tiempo."), tr("En el bar se arregla el mundo todas las tardes."),
    tr("Un vinito con la comida y ya está."), tr("Hay más bares que farmacias. Por algo será."), tr("Yo ya no bebo como antes. El hígado tiene memoria."),
    tr("El café de aquí al lado es el mejor. El de la plaza es agua sucia."), tr("Los viernes, una copa. Solo una. Bueno, dos.")],
  amable=[tr("Un café siempre apetece. Y con compañía, más."), tr("Si invitas tú, no digo que no.")],
  hablador=[tr("Pues en el bar de abajo ponen una tapa con cada caña que cenas gratis. Yo voy los jueves, que hay callos. Bueno, y los martes. Y algún lunes.")],
  seco=[tr("Café solo."), tr("No bebo.")], timido=[tr("Yo... un refresco. No bebo mucho.")], chulo=[tr("Yo aguanto lo que me echen."), tr("A mí en el bar me invitan. No pago yo.")])

T("futbol", tr("futbol|el partido|tu equipo|de que equipo|la liga|el gol|el derbi|el arbitro|el estadio|el mundial|la seleccion"), [
    tr("No me hables de fútbol, que este año vamos de pena."), tr("Yo soy del equipo de aquí, gane o pierda. Sobre todo pierda."), tr("El árbitro del domingo estaba comprado. Lo vio todo el mundo."),
    tr("A mí el fútbol ni fu ni fa."), tr("Antes se jugaba por la camiseta. Ahora, por la cartera."), tr("Si ganamos el derbi, me doy por satisfech{o} todo el año."),
    tr("No me pierdo un partido. Es lo único que me distrae."), tr("El fútbol, en el bar y con los amigos. En casa no es lo mismo."), tr("Este año subimos. Bueno, lo digo todos los años."),
    tr("Yo jugué de joven. Era mal{o}, pero ponía ganas.")],
  amable=[tr("Yo no entiendo mucho, pero me alegro cuando gana el equipo de aquí."), tr("¿Viste el partido? Yo lo oí por la radio.")],
  hablador=[tr("¡El gol del domingo! Yo estaba en el bar, y cuando marcaron se cayó una mesa entera. Tres cañas al suelo. Y el dueño, en vez de enfadarse, invitó a otra ronda.")],
  seco=[tr("No me gusta."), tr("Lo veo. Poco.")], timido=[tr("No... no sigo el fútbol.")], chulo=[tr("Si me hubieran fichado a mí, otro gallo cantaría."), tr("Yo de fútbol sé más que el entrenador.")])

T("musica", tr("la musica|que musica|te gusta la musica|una cancion|cantas|sabes cantar|la radio|que emisora|el flamenco|el rock|bailar|bailas|un concierto|tocas algun"), [
    tr("Yo, la radio puesta todo el día. Sin música no sé trabajar."), tr("Para música, la de antes. Lo de ahora es ruido."), tr("Me gusta de todo, menos lo que pone mi vecino."),
    tr("Yo canto en la ducha, y los vecinos lo saben."), tr("En las fiestas bailo hasta que me echan."), tr("Bravo FM, que ponen rock del bueno."), tr("Una guitarra y una noche de verano. No hace falta más."),
    tr("No tengo oído, pero tengo ganas."), tr("La música amansa a las fieras. A mi jefe, no.")],
  amable=[tr("Me encanta. Con música todo se lleva mejor."), tr("Yo canto fatal, pero me lo paso muy bien.")],
  hablador=[tr("Mi tío tocaba el acordeón en las verbenas, y yo iba detrás pasando la gorra. Así me pagué la primera bicicleta. Bueno, media bicicleta.")],
  seco=[tr("La radio. A veces."), tr("No mucho.")], timido=[tr("Escucho música... yo sol{o}, en casa.")], chulo=[tr("Yo bailo mejor que nadie en esta ciudad."), tr("Canto, toco y bailo. Y todo bien.")])

T("barrio_vida", tr("se vive bien|te gusta vivir|como es vivir|es tranquilo|es peligroso|es seguro|los vecinos|la gente de aqui|que tal la gente|como es la gente|el ambiente"), [
    tr("Aquí se vive bien si no te metes en líos."), tr("En {barrio} nos conocemos todos, para lo bueno y para lo malo."), tr("Tranquilo, lo que se dice tranquilo, no es. Pero es mi casa."),
    tr("La gente es buena. Un poco cotilla, pero buena."), tr("De día, sin problema. De noche, mira por dónde andas."), tr("Antes dejábamos la puerta abierta. Ahora, dos cerrojos."),
    tr("{ciudad} tiene de todo: mar, bares y gente rara."), tr("Los vecinos se ayudan. Eso no ha cambiado."), tr("Cada vez viene más gente de fuera, y se nota."), tr("No lo cambiaría por nada.")],
  amable=[tr("Es un sitio estupendo. La gente es muy acogedora, ya lo verás."), tr("Aquí siempre hay alguien que te echa una mano.")],
  hablador=[tr("En {barrio} pasa de todo y nos enteramos de todo. La del tercero, por ejemplo... bueno, eso no te lo cuento porque no la conoces, pero es para escribir una novela.")],
  seco=[tr("Se vive."), tr("Normal.")], timido=[tr("Es tranquilo... a mí me gusta.")], chulo=[tr("En {barrio} mandamos los de aquí. Y se vive como yo diga.")])

T("ciudad_cambio", tr("ha cambiado|como era antes|antes era|los viejos tiempos|en tus tiempos|ya no es lo que era|la ciudad ha|todo cambia|el progreso|las obras"), [
    tr("Esto antes era todo huerta. Ahora, bloques."), tr("Cuando yo era pequeñ{o}, se podía jugar en la calle."), tr("Han cambiado las tiendas, pero la gente es la misma."),
    tr("Antes el puerto daba de comer a media ciudad."), tr("Cada alcalde hace una rotonda y se va."), tr("Las obras de la avenida llevan tres años. Las pirámides tardaron menos."),
    tr("Todo cambia, menos el precio del café, que sube."), tr("Lo de antes no era mejor. Éramos más jóvenes, que no es lo mismo."), tr("Han cerrado el cine viejo. Ahí vi yo mi primera película.")],
  hablador=[tr("Donde está el banco había una vaquería, y donde la vaquería, antes, un huerto de mi tío abuelo. Lo vendió por cuatro perras y un burro. El burro vivió veinte años.")],
  seco=[tr("Todo cambia."), tr("A peor.")], timido=[tr("Yo... no me acuerdo mucho de antes.")], chulo=[tr("Esto lo levantamos los de aquí. Que no se olvide.")],
  amable=[tr("Ha cambiado mucho, pero sigue siendo un buen sitio."), tr("A mí me gusta más ahora. Hay más vida.")])

T("policia", tr("la policia|los policias|la poli|los guardias|la comisaria|te han detenido|te busca la policia|me busca la policia|una multa|los maderos"), [
    tr("La policía, cuanto más lejos, mejor."), tr("Hacen su trabajo. Otra cosa es que lo hagan bien."), tr("A mí nunca me han parado. Será que tengo cara de buena persona."),
    tr("Cuando los necesitas no están, y cuando no, te ponen una multa."), tr("Últimamente se les ve más. Algo pasará."), tr("Yo con ellos, buenos días y buenas tardes. Nada más."),
    tr("Mi primo es municipal. Buen chaval, pero no le cuentes nada."), tr("Dicen que hay alguno que cobra por mirar para otro lado.")],
  amable=[tr("Tienen un trabajo difícil. Yo no lo querría."), tr("Los del barrio son majos. Saludan y todo.")],
  hablador=[tr("El otro día pararon a mi vecino por ir sin luces en la bici. ¡En la bici! Le cayeron cincuenta euros. Ahora va andando y dice que por lo menos hace ejercicio.")],
  seco=[tr("Ni los quiero ni los busco."), tr("Mejor lejos.")], timido=[tr("Yo... me pongo nervios{o} cuando los veo. Y no he hecho nada.")], chulo=[tr("A mí la policía me saluda. Me conocen."), tr("No me asustan cuatro uniformes.")],
  poca=[tr("¿Por qué lo preguntas? ¿Has hecho algo?"), tr("Como sigas así, los vas a conocer.")])

T("delincuencia", tr("los robos|han robado|un robo|los ladrones|los atracos|un atraco|la delincuencia|hay peligro|las drogas|los camellos|trapicheo|el contrabando|la mafia|los matones"), [
    tr("Cada vez hay más. Antes eso aquí no pasaba."), tr("Yo no veo nada, no oigo nada y no digo nada."), tr("Le entraron a la vecina la semana pasada. Se llevaron hasta el jamón."),
    tr("De eso mejor no hablar en la calle."), tr("Hay zonas por las que yo ya no paso de noche."), tr("Lo del contrabando en el puerto lo sabe todo el mundo. Y nadie hace nada."),
    tr("Mientras se maten entre ellos, a mí que me dejen tranquil{o}."), tr("Son cuatro, pero hacen ruido por cuarenta."), tr("La droga ha hecho mucho daño aquí. Muchos chavales perdidos.")],
  hablador=[tr("Dicen, y yo no he dicho nada, que el del almacén del muelle tiene más visitas de noche que de día. Y no van a comprar pescado.")],
  seco=[tr("No sé nada."), tr("No pregunto.")], timido=[tr("Me da miedo... prefiero no hablar de eso.")], chulo=[tr("A mí no se atreve a robarme nadie."), tr("Sé quién es quién. Y ellos saben quién soy yo.")],
  amable=[tr("Es una pena. Ten cuidado por las noches, ¿eh?")], poca=[tr("Tú sabrás más que yo de eso.")])

T("bandas", tr("las bandas|los calaveras|los lagartos|una banda|pandilla|pandilleros|las guerras de barrio|el territorio|quien manda aqui|quien manda en"), [
    tr("De esos, cuanto menos se hable, mejor."), tr("Hay barrios enteros atemorizados por cuatro con pistola."), tr("Aquí manda el que más miedo da. Hoy unos, mañana otros."),
    tr("Antes eran cuatro críos con una moto. Ahora llevan pistola."), tr("Yo pago, callo y cierro pronto."), tr("Cuando se pelean entre ellos, lo pagamos los vecinos."),
    tr("Dicen que detrás hay gente con corbata."), tr("Si cambia de manos el barrio, que sea para bien.")],
  hablador=[tr("A mi primo le pidieron dinero por dejarle abrir la tienda. Les dijo que no. Ahora tiene la tienda en otro barrio.")],
  seco=[tr("No hablo de eso."), tr("Pregunta a otro.")], timido=[tr("No... de eso no sé nada. De verdad.")], chulo=[tr("A mí esos no me tosen."), tr("Los conozco desde críos. No son nadie.")],
  amable=[tr("Ten cuidado con esa gente, de verdad.")], poca=[tr("¿Eres uno de ellos? Pues entonces ya lo sabes.")], confianza=0)

T("belmonte", tr("belmonte|octavio|el empresario|la familia belmonte|quien es belmonte"), [
    tr("Belmonte es dueño de media ciudad. Y de la otra media, también."), tr("Dicen que empezó con un bar y ahora no hay negocio que no pase por él."), tr("De ese hombre no se habla. Y menos en la calle."),
    tr("Paga las fiestas del barrio. Con qué dinero, no lo sé."), tr("Hay quien lo quiere y quien le tiene miedo. Yo, ni lo uno ni lo otro: lejos."), tr("Sale en el periódico cada semana cortando una cinta."),
    tr("Mi padre trabajó para él. No habla de aquello.")],
  seco=[tr("No lo conozco."), tr("No digo nada.")], timido=[tr("Shh... ese nombre mejor no decirlo alto.")], chulo=[tr("Belmonte y yo nos tratamos de tú."), tr("Ese no es tan fiero como lo pintan.")],
  hablador=[tr("De Belmonte se cuentan mil cosas. Que si tiene una caja fuerte del tamaño de una habitación, que si no duerme nunca... Yo lo vi una vez de lejos. Es más bajito de lo que parece.")],
  confianza=0)

T("puerto", tr("el puerto|los barcos|la pesca|los pescadores|pescar|la lonja|los muelles|un barco|sales a pescar|el pescado fresco"), [
    tr("El puerto ya no es lo que era, pero sigue siendo el corazón de esto."), tr("Mi abuelo salía a pescar a las cuatro de la mañana. Eso era trabajar."), tr("En la lonja, a primera hora, se ve lo mejor."),
    tr("Cada año hay menos barcos y menos peces."), tr("Si te gusta pescar, en el espigón pican bien al atardecer."), tr("El mar da y el mar quita."), tr("Los pescadores de aquí saben más del tiempo que la televisión."),
    tr("Con una caña y paciencia, cenas gratis.")],
  hablador=[tr("Yo salí una vez a la mar con mi cuñado. Una. Me mareé antes de soltar amarras y él todavía se lo cuenta a todo el mundo en Navidad.")],
  seco=[tr("Hay barcos."), tr("Ahí está.")], timido=[tr("Me gusta ir a mirar los barcos... es tranquilo.")], chulo=[tr("Yo he sacado un atún así de grande. Pregunta en la lonja."), tr("El mar no tiene secretos para mí.")],
  amable=[tr("El puerto al amanecer es precioso. Tienes que verlo.")])

T("mar_playa", tr("el mar|la playa|banarse|nadar|sabes nadar|las olas|la arena|tomar el sol|los turistas|el verano|las vacaciones|veranear|te vas de vacaciones"), [
    tr("Teniendo el mar al lado, ¿para qué irse de vacaciones?"), tr("En agosto no cabe un alfiler en la playa."), tr("Los turistas dejan dinero y basura, a partes iguales."),
    tr("Yo me baño todo el año. Bueno, hasta octubre."), tr("No sé nadar, y vivo en la costa. Ya ves."), tr("Vacaciones, las justas. Una semana en el pueblo y gracias."),
    tr("El mar en invierno es lo mejor. No hay nadie."), tr("Cuando hay operación salida, de aquí no se puede ni salir ni entrar."), tr("El verano es para los de fuera. Los de aquí trabajamos.")],
  amable=[tr("La playa por la tarde es una maravilla. Te la recomiendo."), tr("Yo paseo por la orilla todos los días. Es mi medicina.")],
  hablador=[tr("Este verano ha venido tanta gente que el del chiringuito se ha comprado un coche nuevo. En agosto. Al contado.")],
  seco=[tr("Está ahí."), tr("No voy.")], timido=[tr("Yo voy... cuando no hay gente.")], chulo=[tr("En la playa, el más moreno soy yo."), tr("Yo nado hasta la boya y vuelvo sin despeinarme.")])

T("coches", tr("tu coche|los coches|el trafico|los atascos|conduces|sabes conducir|una moto|las motos|aparcar|el aparcamiento|la gasolina|el carne|correr con el coche|las carreras"), [
    tr("Aparcar aquí es una lotería. Y nunca toca."), tr("La gasolina está por las nubes."), tr("Yo voy andando a todas partes. Así no me multan."), tr("Tengo un coche que tiene más años que yo, pero arranca."),
    tr("Los que corren por la avenida de noche van a matar a alguien."), tr("En hora punta se tarda más en coche que a pie."), tr("Las motos pasan que parecen aviones."),
    tr("Dicen que hay carreras de noche. Yo oigo los motores desde la cama."), tr("Con los semáforos que han puesto, ya no hay quien cruce la ciudad.")],
  hablador=[tr("Mi coche hace un ruido raro desde hace un año. El mecánico dice que es el embrague, mi cuñado que es la correa, y yo creo que es que está harto de mí.")],
  seco=[tr("Voy a pie."), tr("Tengo uno. Anda.")], timido=[tr("No conduzco... me da cosa.")], chulo=[tr("Nadie conduce como yo en esta ciudad."), tr("Mi coche lo conoce todo el barrio por el ruido.")],
  amable=[tr("Ten cuidado con el coche, que hay mucho loco suelto.")])

T("transporte", tr("el autobus|los autobuses|un taxi|los taxis|la estacion|como se va a|como llego a|ir a otra ciudad|ir a otro pueblo|viajar|el viaje|la carretera"), [
    tr("El autobús sale de la estación. Barato, pero lento."), tr("Los taxis están en la parada. Te llevan donde quieras si pagas."), tr("Para ir a los pueblos, por las salidas de la ciudad. Están señalizadas."),
    tr("El autobús pasa cuando quiere, no cuando dice el horario."), tr("Si vas lejos, mejor en autobús que conduciendo. Te ahorras el susto."), tr("Por mar también se llega a muchos sitios, si tienes barca."),
    tr("La carretera de la costa es bonita, pero tiene curvas para aburrir.")],
  amable=[tr("Si no sabes ir, pregunta en la estación. Son muy amables.")], hablador=[tr("Yo una vez cogí el autobús equivocado y acabé en la sierra. Me comí un cordero buenísimo, eso sí.")],
  seco=[tr("En autobús."), tr("En la estación te dicen.")], timido=[tr("Creo que hay autobuses... en la estación.")], chulo=[tr("Yo no cojo autobuses. Me llevan.")])

T("salud", tr("la salud|estas enfermo|estas enferma|el medico|el hospital|te duele|un dolor|la gripe|un resfriado|las pastillas|la farmacia|estas herido|estas herida|te has hecho dano"), [
    tr("Mientras haya salud, lo demás se arregla."), tr("Me duele todo, pero el médico dice que estoy como un roble."), tr("En el hospital te atienden bien. Cuando te atienden."),
    tr("A mi edad, si no te duele algo es que estás muert{o}."), tr("Yo voy al médico lo justo. Me pone nervios{o}."), tr("La farmacia de aquí al lado es muy apañada."),
    tr("Un resfriado me tuvo en cama la semana pasada."), tr("Si estás herid{o}, ve al hospital. No te hagas el valiente.")],
  amable=[tr("Cuídate mucho, que la salud es lo primero."), tr("Si te encuentras mal, hay una farmacia cerca. No lo dejes.")],
  hablador=[tr("Fui al médico por la rodilla y salí con pastillas para la tensión, el colesterol y el azúcar. De la rodilla no me dijo nada.")],
  seco=[tr("Estoy bien."), tr("Vete al médico.")], timido=[tr("Yo... estoy bien, gracias. Un poco de alergia.")], chulo=[tr("Yo no me pongo enferm{o}. No tengo tiempo."), tr("Fuerte como un toro.")])

T("cansancio", tr("estoy cansado|estoy cansada|estas cansado|estas cansada|tengo sueno|que sueno|no he dormido|dormir|has dormido|madrugar|el madrugon"), [
    tr("A quién se lo vas a contar. Llevo en pie desde las seis."), tr("Yo duermo poco y mal. Cosas de la edad."), tr("Una siesta lo arregla todo."), tr("Si tienes sueño, vete a dormir. El cuerpo manda."),
    tr("Madrugar no es de este mundo."), tr("Yo sin mis ocho horas no soy persona."), tr("Hay un hotel por aquí si no tienes dónde dormir.")],
  amable=[tr("Descansa, que se te ve cara de cansancio."), tr("Pobre. Un café y a casa.")], hablador=[tr("Yo anoche no pegué ojo. El vecino de arriba, que se ha comprado una batería. ¡Una batería! Con sesenta años.")],
  seco=[tr("Pues duerme."), tr("Yo también.")], timido=[tr("Yo también tengo sueño... siempre.")], chulo=[tr("Dormir es de flojos."), tr("Yo con cuatro horas voy sobrad{o}.")])

T("fiestas", tr("las fiestas|la feria|la verbena|la fiesta|hoy es fiesta|el mercado|dia de mercado|las rebajas|la huelga|los fuegos|la procesion|carnaval|navidad|las fallas"), [
    tr("En fiestas no duerme nadie. Ni quien quiere."), tr("La feria ya no es como antes, pero los críos lo pasan bien."), tr("El día de mercado baja medio pueblo. No se puede ni andar."),
    tr("Con las rebajas, la gente compra lo que no necesita."), tr("Si hay huelga, mejor quedarse en casa."), tr("Los fuegos del último día son lo mejor."), tr("Yo en fiestas me voy. No aguanto el ruido."),
    tr("Para la verbena tiran la casa por la ventana."), tr("En el mercado está todo más barato, si sabes regatear.")],
  amable=[tr("Las fiestas son preciosas. Tienes que venir."), tr("Me encanta el mercado. Te encuentras a todo el mundo.")],
  hablador=[tr("En la verbena del año pasado bailé hasta las cinco. Con mi rodilla. Estuve una semana sin poder bajar la escalera, pero mereció la pena.")],
  seco=[tr("Mucho ruido."), tr("No voy.")], timido=[tr("Hay mucha gente... yo voy un rato y me vuelvo.")], chulo=[tr("En fiestas, el rey soy yo."), tr("Sin mí, la verbena no empieza.")])

T("politica", tr("el alcalde|la alcaldesa|el ayuntamiento|los politicos|la politica|el gobierno|las elecciones|a quien votas|los impuestos|los concejales"), [
    tr("Son todos iguales. Prometen y luego ni se acuerdan."), tr("El alcalde solo aparece en la foto."), tr("De política y de religión, en la calle no se habla."), tr("Impuestos, todos. Servicios, ninguno."),
    tr("Yo voto, que para eso costó conseguirlo. Luego me arrepiento."), tr("Arreglaron la plaza justo antes de las elecciones. Qué casualidad."), tr("Mientras tapen los baches, me da igual quién mande."),
    tr("El ayuntamiento está para lo que está: para cobrar.")],
  hablador=[tr("Fui al ayuntamiento por un papel y me mandaron a tres ventanillas. En la tercera me dijeron que volviera a la primera. Me llevé la merienda al día siguiente.")],
  seco=[tr("No opino."), tr("Todos iguales.")], timido=[tr("Yo de eso... no entiendo.")], chulo=[tr("Si yo fuera alcalde, esto estaría arreglado en dos días."), tr("A esos los pongo yo firmes.")],
  amable=[tr("Alguno habrá que lo haga bien, digo yo.")])

T("animales", tr("tu perro|un perro|los perros|un gato|los gatos|tienes mascota|tienes perro|los animales|las gaviotas|la protectora|adoptar"), [
    tr("Tengo un perro que es más listo que algunos vecinos."), tr("Los gatos del puerto están mejor alimentados que yo."), tr("Las gaviotas te roban el bocadillo de la mano."),
    tr("En la protectora siempre hay perros buscando casa."), tr("Yo quise un perro, pero en mi piso no cabe ni yo."), tr("Mi gato manda en casa. Yo solo pago."), tr("Un perro te cambia la vida. Y los zapatos."),
    tr("Dicen que un perro bien enseñado encuentra cosas enterradas.")],
  amable=[tr("Me encantan los animales. Si puedes, adopta uno."), tr("Mi perro es mi mejor compañía.")],
  hablador=[tr("Mi perro se llama Capitán y ladra a todos menos a los ladrones. Entraron una vez y les movió el rabo. Les faltó llevárselo.")],
  seco=[tr("No tengo."), tr("Un perro.")], timido=[tr("Tengo un gato... se llama Miga.")], chulo=[tr("Mi perro es como yo: no le tose nadie."), tr("Los perros me obedecen a la primera.")])

T("ninos_colegio", tr("el colegio|la escuela|los estudios|estudias|has estudiado|la universidad|los profesores|los deberes|aprender|un curso|la academia"), [
    tr("Yo estudié lo justo. La calle enseña más."), tr("Mi hijo saca mejores notas que las que saqué yo en toda mi vida."), tr("En la academia dan cursos. Nunca es tarde para aprender."),
    tr("Me hubiera gustado estudiar más, pero había que trabajar."), tr("Los críos de ahora saben mucho de pantallas y poco de la vida."), tr("Un buen maestro vale más que cien libros."),
    tr("Estudiar no sé, pero aprender se aprende todos los días.")],
  amable=[tr("Estudiar siempre viene bien. Anímate."), tr("Mis profesores fueron muy buenos conmigo.")], hablador=[tr("A mí me echaron de clase por hablar. Tres veces. En el mismo día.")],
  seco=[tr("Estudié poco."), tr("No era lo mío.")], timido=[tr("Me gustaba estudiar... era lo único que se me daba bien.")], chulo=[tr("Yo no necesité estudiar. Nací sabiendo."), tr("El más listo de mi clase, y no abría un libro.")])

T("deporte", tr("el gimnasio|haces deporte|el deporte|correr|sales a correr|estas fuerte|estas en forma|el boxeo|boxeas|pelear|las pesas|la bici|montar en bici"), [
    tr("Mi deporte es subir la cuesta de casa con la compra."), tr("En el gimnasio de aquí se entrena bien. Y hay combates."), tr("Yo corría de joven. Ahora corro si me persiguen."),
    tr("El boxeo enseña disciplina. A mí me enseñó a agacharme."), tr("Voy en bici a todas partes. Barato y sano."), tr("Debería hacer algo, pero el sofá tira mucho."),
    tr("Andar una hora al día. Me lo dijo el médico y le hago caso a medias.")],
  amable=[tr("Hacer deporte sienta muy bien. Yo salgo a andar.")], hablador=[tr("Me apunté al gimnasio en enero. Fui dos días. Llevo pagando desde entonces porque me da vergüenza ir a borrarme.")],
  seco=[tr("Ando."), tr("No.")], timido=[tr("Yo... camino. Sol{o}.")], chulo=[tr("Mira qué brazos. Esto no sale solo."), tr("En el ring no me dura nadie dos asaltos.")])
