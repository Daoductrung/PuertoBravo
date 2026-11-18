"""Esquema del editor para la vida honrada y sus consecuencias: los números y las frases, los títulos, los empleos fijos,
las mejoras de los negocios, las decisiones de los puestos con responsabilidad y las situaciones de la calle."""
from juego.honrado import AJ


def c(k, e, t="texto", ayuda="", **kw):
    d = {"k": k, "e": e, "t": t, "ayuda": ayuda}
    d.update(kw)
    return d


# clave: (etiqueta, pestaña, ayuda, mínimo, máximo)
_NUMEROS = {
    "factor_suave": ("Nivel suave: tanto por ciento de las penalizaciones", "General", "Respecto al nivel normal, que es cien. Las ventajas no cambian con el nivel.", 1, 100),
    "factor_exigente": ("Nivel exigente: tanto por ciento de las penalizaciones", "General", "", 100, 400),
    "rebaja_aprecian": ("Rebaja en las tiendas donde te aprecian, por ciento", "Comercios", "Con 40 de prestigio o más.", 0, 90),
    "rebaja_ejemplar": ("Rebaja al ciudadano ejemplar, por ciento", "Comercios", "Con 75 de prestigio o más.", 0, 90),
    "recargo_evitan": ("Recargo donde te evitan, por ciento", "Comercios", "Con menos de 10 de prestigio, en el nivel normal.", 0, 200),
    "fiado_aprecian": ("Lo que te fían donde te aprecian, en euros", "Comercios", "", 0, 100000),
    "fiado_ejemplar": ("Lo que le fían al ciudadano ejemplar", "Comercios", "", 0, 100000),
    "fiado_dias": ("Días tras los que el fiado se cobra con las facturas", "Comercios", "", 1, 365),
    "negativa_prob": ("Probabilidad de que no te atiendan, por ciento", "Comercios", "Solo en el nivel exigente y donde te evitan. Se decide una vez al día en cada comercio.", 0, 100),
    "encubren_prob": ("Probabilidad de que los vecinos encubran una falta, por ciento", "Testigos y policía", "Al ciudadano ejemplar; a quien aprecian, la mitad. Solo sin agentes delante.", 0, 100),
    "encubren_puntos": ("Gravedad máxima de la falta que encubren", "Testigos y policía", "En puntos de delito: un golpe a un coche es uno; un disparo, más.", 0, 20),
    "delatan_extra": ("Cuánto más cuenta un delito donde te evitan, por ciento", "Testigos y policía", "", 0, 300),
    "duda_puntos": ("Gravedad máxima con beneficio de la duda", "Testigos y policía", "Un agente la deja pasar una vez al día si te aprecian y tu ficha está limpia.", 0, 20),
    "fichado_extra": ("Cuánto más cuenta un delito por cada punto de antecedentes, por ciento", "Testigos y policía", "Un antecedente leve pesa uno; uno medio, dos; uno grave, cuatro.", 0, 100),
    "control_prob": ("Probabilidad diaria de que te pare un agente, por ciento", "Testigos y policía", "Con mala fama o antecedentes, en el nivel normal o exigente, si hay un agente cerca.", 0, 100),
    "control_minutos": ("Minutos del juego que te retiene", "Testigos y policía", "", 1, 240),
    "fama_respeto": ("Fama en la calle con la que las bandas respetan tus negocios", "La calle", "", 0, 1000),
    "fama_descuento": ("Descuento máximo de los guardaespaldas por tu fama, por ciento", "La calle", "", 0, 90),
    "fama_recargo": ("Recargo de los guardaespaldas si nadie te conoce, por ciento", "La calle", "", 0, 200),
    "caduca_leve": ("Días que dura un antecedente leve", "Antecedentes", "", 1, 3650),
    "caduca_media": ("Días que dura uno medio", "Antecedentes", "", 1, 3650),
    "caduca_grave": ("Días que dura uno grave", "Antecedentes", "", 1, 3650),
    "servicio_quita": ("Días que quita una sesión de servicios a la comunidad", "Antecedentes", "", 1, 365),
    "servicio_horas": ("Horas de cada sesión", "Antecedentes", "", 1, 24),
    "abogado_precio": ("Precio del recurso de un abogado, por grado", "Antecedentes", "Un antecedente grave cuesta el triple.", 1, 1000000),
    "periodo_dias": ("Días de cada periodo de trabajo", "Carrera", "Al acabar cada periodo llega la evaluación y la nómina.", 1, 365),
    "meritos_ascenso": ("Evaluaciones buenas para ascender", "Carrera", "", 1, 100),
    "avisos_despido": ("Avisos con los que te despiden", "Carrera", "", 1, 100),
    "nota_buena": ("Nota desde la que la evaluación es buena", "Carrera", "De cero a cien: sesenta puntos por cumplir los turnos y cuarenta por hacerlos bien.", 1, 100),
    "nota_correcta": ("Nota desde la que es correcta", "Carrera", "", 1, 100),
    "nota_floja": ("Nota desde la que es floja; por debajo, muy mala", "Carrera", "", 1, 100),
    "prima_buena": ("Prima por una evaluación buena, por ciento de la nómina", "Carrera", "", 0, 500),
    "veto_dias": ("Días sin poder volver a la empresa que te despide", "Carrera", "", 1, 3650),
    "carta_periodos": ("Periodos sin avisos para irte con carta de recomendación", "Carrera", "", 1, 1000),
    "incidencia_prob": ("Probabilidad de una decisión de responsabilidad en cada turno, por ciento", "Carrera", "Solo en los puestos marcados con responsabilidad.", 0, 100),
    "prestigio_periodo": ("Prestigio que da un periodo bien evaluado", "Carrera", "", 0, 100),
    "prestigio_despido": ("Prestigio que quita un despido", "Carrera", "", 0, 100),
    "titulo_prestigio": ("Prestigio que da conseguir un título", "Carrera", "", 0, 100),
    "empleado_sueldo": ("Sueldo diario de un empleado, por ciento de lo que da el negocio de base", "Empresa", "", 0, 100),
    "empleado_rinde": ("Lo que sube el negocio con cada empleado, por ciento", "Empresa", "", 0, 500),
    "rep_inicial": ("Nombre del negocio al empezar, de cero a cien", "Empresa", "", 1, 100),
    "rep_factor": ("Lo que sube o baja el negocio con su nombre, por ciento", "Empresa", "Con el nombre a cien da ese tanto más; con el nombre a cero, ese tanto menos.", 0, 200),
    "atender_horas": ("Horas que echas al atender el negocio", "Empresa", "", 1, 24),
    "atender_rep": ("Lo que sube el nombre cada vez que lo atiendes", "Empresa", "", 0, 100),
    "abandono_dias": ("Días sin pasar tras los que se da por abandonado", "Empresa", "", 1, 365),
    "abandono_baja": ("Lo que baja el nombre cada día de abandono", "Empresa", "", 0, 100),
    "precios_bajos_ingreso": ("Con precios bajos, lo que pierde de ingresos, por ciento", "Empresa", "", 0, 100),
    "precios_bajos_rep": ("Con precios bajos, lo que sube el nombre cada día", "Empresa", "", 0, 100),
    "precios_altos_ingreso": ("Con precios altos, lo que gana de más, por ciento", "Empresa", "", 0, 500),
    "precios_altos_rep": ("Con precios altos, lo que baja el nombre cada día", "Empresa", "", 0, 100),
    "horario_ingreso": ("Con horario ampliado, lo que gana de más, por ciento", "Empresa", "", 0, 500),
    "tapadera_capacidad": ("Euros al día que blanquea una tapadera, por nivel del negocio", "Inspecciones y tapadera", "", 1, 10000000),
    "tapadera_comision": ("Comisión del blanqueo, por ciento", "Inspecciones y tapadera", "", 0, 100),
    "negro_umbral": ("Dinero sin justificar desde el que una inspección lo nota", "Inspecciones y tapadera", "", 1, 100000000),
    "negro_decae": ("Lo que se olvida cada día del dinero sin justificar, por ciento", "Inspecciones y tapadera", "", 0, 100),
    "inspeccion_min": ("Días entre inspecciones, como poco", "Inspecciones y tapadera", "", 1, 3650),
    "inspeccion_max": ("Y como mucho", "Inspecciones y tapadera", "", 1, 3650),
    "sancion_pct": ("Sanción de una inspección, por ciento del precio del negocio", "Inspecciones y tapadera", "", 0, 100),
    "soborno_pct": ("Soborno al inspector, por ciento del precio del negocio", "Inspecciones y tapadera", "", 0, 100),
    "soborno_prob": ("Probabilidad de que el soborno salga bien, por ciento", "Inspecciones y tapadera", "Sube con la fama en la calle y baja en el nivel exigente.", 0, 100),
    "plazo_asunto": ("Días para decidir un asunto pendiente", "Inspecciones y tapadera", "Una inspección, un periodista o una extorsión. Pasado el plazo se resuelve solo.", 1, 365),
    "impuesto_negocio": ("Impuesto sobre lo que dan los negocios, por ciento", "Impuestos y facturas", "En el nivel normal.", 0, 100),
    "impuesto_casa": ("Contribución de las viviendas, por cada diez mil euros de precio", "Impuestos y facturas", "En cada cobro.", 0, 10000),
    "factura_casa": ("Luz y agua de cada vivienda, en euros", "Impuestos y facturas", "En cada cobro.", 0, 100000),
    "cobro_dias": ("Días entre cobros", "Impuestos y facturas", "", 1, 365),
    "aviso_dias": ("Días de antelación del aviso", "Impuestos y facturas", "Vale también para las cuotas de los créditos.", 1, 30),
    "recargo": ("Recargo por impago, por ciento", "Impuestos y facturas", "", 0, 200),
    "gracia_dias": ("Días de gracia al empezar", "Impuestos y facturas", "En una partida nueva y en una de antes de esta versión: hasta entonces no se cobra nada.", 1, 365),
    "impagos_embargo": ("Impagos seguidos que traen el embargo", "Impuestos y facturas", "", 1, 100),
    "embargo_pct": ("Parte de tus ingresos que se queda el embargo, por ciento", "Impuestos y facturas", "", 1, 100),
    "solvencia_prestigio": ("Peso del prestigio en la solvencia, por ciento", "Banco", "", 0, 100),
    "solvencia_ingresos": ("Euros de ingresos por semana que valen un punto de solvencia", "Banco", "", 1, 100000),
    "solvencia_ingresos_tope": ("Puntos de solvencia que pueden dar los ingresos, como mucho", "Banco", "", 0, 100),
    "credito_por_punto": ("Euros de crédito por punto de solvencia", "Banco", "", 1, 1000000),
    "credito_min_solvencia": ("Solvencia mínima para un crédito personal", "Banco", "", 0, 100),
    "credito_cuotas": ("Cuotas de un crédito personal", "Banco", "", 1, 500),
    "interes_bueno": ("Interés con solvencia excelente, por ciento", "Banco", "", 0, 500),
    "interes_medio": ("Interés con solvencia buena", "Banco", "", 0, 500),
    "interes_malo": ("Interés con solvencia justa", "Banco", "", 0, 500),
    "hipoteca_entrada": ("Entrada de una hipoteca, por ciento del precio", "Hipotecas y cuotas", "", 1, 100),
    "hipoteca_cuotas": ("Cuotas de una hipoteca", "Hipotecas y cuotas", "", 1, 1000),
    "hipoteca_solvencia": ("Solvencia mínima para una hipoteca", "Hipotecas y cuotas", "", 0, 100),
    "hipoteca_interes": ("Interés de una hipoteca, por ciento", "Hipotecas y cuotas", "", 0, 500),
    "cuota_dias": ("Días entre cuotas", "Hipotecas y cuotas", "", 1, 365),
    "reintento_dias": ("Días hasta que se reintenta una cuota impagada", "Hipotecas y cuotas", "", 1, 365),
    "sospecha_delito": ("Lo que sube el rumor por cada punto de delito visto", "Doble vida", "El rumor va de cero a cien.", 0, 100),
    "sospecha_detencion": ("Lo que sube con una detención", "Doble vida", "", 0, 100),
    "sospecha_multa": ("Lo que sube con una multa pagada a un agente", "Doble vida", "", 0, 100),
    "sospecha_baja": ("Lo que baja cada día tranquilo", "Doble vida", "", 0, 100),
    "sospecha_rumor": ("Nivel desde el que corre el rumor", "Doble vida", "", 1, 100),
    "sospecha_prensa": ("Nivel desde el que la prensa prepara un reportaje", "Doble vida", "", 1, 100),
    "prensa_prestigio": ("Prestigio que quita salir en el periódico", "Doble vida", "", 0, 100),
    "prensa_soborno": ("Lo que pide el periodista por callar", "Doble vida", "", 0, 10000000),
    "abogado_semana": ("Lo que cobra el abogado a la semana", "Doble vida", "", 0, 10000000),
    "abogado_factor": ("Con abogado, tanto por ciento de lo que sube el rumor", "Doble vida", "", 0, 100),
    "extorsion_min": ("Días hasta una extorsión, como poco", "Extorsión y buenas acciones", "Solo a quien tiene un negocio y nadie respeta en la calle.", 1, 3650),
    "extorsion_max": ("Y como mucho", "Extorsión y buenas acciones", "", 1, 3650),
    "extorsion_pct": ("Lo que piden, por ciento de lo que da el negocio a la semana", "Extorsión y buenas acciones", "", 0, 100),
    "extorsion_minimo": ("Lo menos que piden, en euros", "Extorsión y buenas acciones", "", 0, 10000000),
    "extorsion_semanas": ("Semanas que dura el pago", "Extorsión y buenas acciones", "", 1, 520),
    "extorsion_dano_prob": ("Probabilidad de que dañen el negocio si te niegas, por ciento", "Extorsión y buenas acciones", "", 0, 100),
    "extorsion_dano_dias": ("Días que el negocio da menos tras el daño", "Extorsión y buenas acciones", "", 1, 365),
    "extorsion_dano": ("Lo que pierde de ingresos esos días, por ciento", "Extorsión y buenas acciones", "", 0, 100),
    "buena_min": ("Minutos del juego entre dos situaciones de la calle, como poco", "Extorsión y buenas acciones", "Las situaciones en las que puedes ayudar o aprovecharte.", 1, 100000),
    "buena_max": ("Y como mucho", "Extorsión y buenas acciones", "", 1, 100000),
    "compromiso_afinidad": ("Afinidad para prometerse", "Pareja", "", 1, 100),
    "compromiso_citas": ("Citas para prometerse", "Pareja", "", 0, 1000),
    "boda_dias": ("Días entre el compromiso y la boda", "Pareja", "", 1, 3650),
    "boda_precio": ("Lo que cuesta la boda", "Pareja", "", 0, 10000000),
    "boda_prestigio": ("Prestigio que da casarse", "Pareja", "", 0, 100),
}

# clave: (etiqueta, pestaña, huecos que admite la frase)
_FRASES = {
    "caracteres_jefe": ("Caracteres de los jefes", "Frases del trabajo", "Uno al azar al firmar. Si empieza por exigente, evalúa más duro; por paciente, más blando."),
    "frases_dos_caminos": ("Lo que se dice al empezar: hay dos caminos", "Frases generales", ""),
    "frases_partida_antigua": ("Aviso a una partida de antes de esta versión", "Frases generales", "{dias} son los días de gracia."),
    "frases_encubren": ("Los vecinos te encubren", "Frases generales", ""),
    "frases_duda": ("Un agente te da el beneficio de la duda", "Frases generales", ""),
    "frases_delatan": ("Los vecinos te delatan", "Frases generales", ""),
    "frases_control": ("Un agente te para", "Frases generales", ""),
    "frases_fiado": ("Te fían en una tienda", "Frases generales", "{euros}."),
    "frases_negativa": ("No te atienden", "Frases generales", ""),
    "frases_firma": ("Firmas un contrato", "Frases del trabajo", "{empresa}, {jefe}, {caracter}, {puesto}, {cupo}, {dias}, {sueldo}."),
    "frases_turno": ("Turno apuntado", "Frases del trabajo", "{jefe}, {hechos}, {cupo}."),
    "frases_falta_turnos": ("Aviso de que te faltan turnos", "Frases del trabajo", "{jefe}, {dias}, {faltan}."),
    "frases_eval_buena": ("Evaluación buena", "Frases del trabajo", "{jefe}, {sueldo}, {prima}."),
    "frases_eval_correcta": ("Evaluación correcta", "Frases del trabajo", "{jefe}, {sueldo}."),
    "frases_eval_floja": ("Evaluación floja", "Frases del trabajo", "{jefe}, {sueldo}, {avisos}, {tope}."),
    "frases_eval_mala": ("Evaluación muy mala", "Frases del trabajo", "{jefe}, {avisos}, {tope}."),
    "frases_ascenso": ("Ascenso", "Frases del trabajo", "{jefe}, {puesto}, {cupo}, {sueldo}."),
    "frases_ascenso_falta": ("Ascenso que espera a que cumplas lo que pide", "Frases del trabajo", "{jefe}, {puesto}, {falta}."),
    "frases_despido": ("Despido", "Frases del trabajo", "{jefe}, {empresa}, {motivo}."),
    "frases_aviso_antecedente": ("Tu jefe se entera de un antecedente", "Frases del trabajo", "{empresa}, {jefe}, {avisos}, {tope}."),
    "frases_dimision": ("Dimisión", "Frases del trabajo", "{jefe}, {empresa}."),
    "frases_carta": ("Carta de recomendación", "Frases del trabajo", "{jefe}."),
    "frases_titulo_sesion": ("Sesión de un título", "Frases de estudios y negocios", "{nombre}, {hechas}, {total}, {quedan}, {horas}, {hora}."),
    "frases_titulo": ("Título conseguido", "Frases de estudios y negocios", "{nombre}, {abre}."),
    "frases_atender": ("Atiendes tu negocio", "Frases de estudios y negocios", "{negocio}, {horas}, {hora}."),
    "frases_abandono": ("Un negocio abandonado", "Frases de estudios y negocios", "{negocio}."),
    "frases_inspeccion_limpia": ("Inspección sin faltas", "Frases de estudios y negocios", "{negocio}."),
    "frases_inspeccion_falta": ("Inspección con irregularidades", "Frases de estudios y negocios", "{negocio}, {dias}."),
    "frases_soborno_ok": ("El soborno al inspector sale bien", "Frases de estudios y negocios", ""),
    "frases_soborno_mal": ("El soborno sale mal", "Frases de estudios y negocios", ""),
    "frases_cobro_aviso": ("Aviso del cobro de facturas e impuestos", "Frases del banco", "{dias}, {euros}."),
    "frases_cobro": ("Cobro de facturas e impuestos", "Frases del banco", "{euros}, {detalle}."),
    "frases_impago": ("No llega para las facturas", "Frases del banco", "{falta}."),
    "frases_embargo": ("Embargo", "Frases del banco", "{euros}."),
    "frases_embargo_fin": ("Fin del embargo", "Frases del banco", ""),
    "frases_cuota_aviso": ("Aviso de una cuota", "Frases del banco", "{dias}, {tipo}, {euros}."),
    "frases_cuota": ("Cuota pagada", "Frases del banco", "{tipo}, {euros}, {quedan}."),
    "frases_cuota_fin": ("Última cuota", "Frases del banco", "{tipo}."),
    "frases_cuota_impago": ("Cuota sin pagar", "Frases del banco", "{tipo}, {euros}, {dias}, {impagos}, {tope}."),
    "frases_rumor": ("Empieza a correr el rumor", "Frases de la doble vida", ""),
    "frases_prensa_aviso": ("Un periodista prepara un reportaje", "Frases de la doble vida", "{dias}."),
    "frases_prensa": ("Sale en el periódico", "Frases de la doble vida", "{nombre}."),
    "frases_prensa_callada": ("Pagas al periodista", "Frases de la doble vida", ""),
    "frases_prensa_abogado": ("Tu abogado frena el reportaje", "Frases de la doble vida", ""),
    "frases_abogado": ("Contratas a un abogado", "Frases de la doble vida", "{euros}."),
    "frases_abogado_fin": ("Te quedas sin abogado", "Frases de la doble vida", ""),
    "frases_extorsion": ("Una banda te pide dinero", "Frases de la extorsión", "{banda}, {negocio}, {euros}, {dias}."),
    "frases_extorsion_vecino": ("Un vecino te avisa", "Frases de la extorsión", "{banda}."),
    "frases_extorsion_pago": ("Pagas", "Frases de la extorsión", "{banda}, {euros}, {semanas}."),
    "frases_extorsion_denuncia": ("Denuncias y sale bien", "Frases de la extorsión", "{banda}."),
    "frases_extorsion_denuncia_mal": ("Denuncias y sale mal", "Frases de la extorsión", "{negocio}."),
    "frases_extorsion_plantas": ("Les plantas cara", "Frases de la extorsión", ""),
    "frases_extorsion_nada": ("Te niegas y no pasa nada", "Frases de la extorsión", ""),
    "frases_extorsion_dano": ("Te niegas y dañan el negocio", "Frases de la extorsión", "{negocio}."),
    "frases_buena_nada": ("Sigues tu camino ante una situación", "Frases de la extorsión", ""),
    "frases_compromiso": ("Os prometéis", "Frases de la pareja", "{n} es su nombre."),
    "frases_compromiso_pronto": ("Todavía es pronto para prometerse", "Frases de la pareja", "{n}."),
    "frases_boda": ("La boda", "Frases de la pareja", "{n}."),
}


_ENTEROS = ("_dias", "_min", "_max", "_horas", "_cuotas", "_semanas", "_periodos", "_minutos", "_despido", "_ascenso", "_embargo", "_precio", "_semana", "_soborno", "_minimo",
            "_capacidad", "_umbral", "_citas", "_asunto", "_aprecian", "_ejemplar")


def _campos_ajuste():
    campos = [c("id", "Identificador", req=True, defecto="general", ayuda="Déjalo en general: solo se usa el primero.")]
    for k, serie in AJ._n.items():
        e, grupo, ayuda, minimo, maximo = _NUMEROS[k]
        campos.append(c(k, e, "entero" if k.endswith(_ENTEROS) else "decimal", ayuda, minimo=minimo, maximo=maximo,
                        defecto=int(serie) if float(serie).is_integer() else serie, **({} if grupo == "General" else {"grupo": grupo})))
    for k in AJ._l:
        e, grupo, huecos = _FRASES[k]
        campos.append(c(k, e, "textos", ("Una por línea; se dice una al azar. " + ("Huecos: " + huecos if huecos.startswith("{") else huecos)).strip(), grupo=grupo))
    return campos


_EFECTOS = [
    c("prestigio", "Prestigio que da o quita", "decimal", "Entre los vecinos. Negativo, si lo quita.", minimo=-100, maximo=100),
    c("fama", "Fama en la calle que da o quita", "decimal", minimo=-100, maximo=100),
    c("dinero", "Dinero que da, o que cuesta si es negativo", "entero"),
    c("animo", "Ánimo que da o quita", "decimal", minimo=-100, maximo=100),
    c("salud", "Salud que da o quita", "decimal", minimo=-100, maximo=100),
    c("dice", "Lo que se cuenta", "largo", req=True),
]

ESQUEMAS = {
    "ajuste_honrado": {"titulo": "Vida, reputación y consecuencias: números y frases",
                       "resumen": lambda d: f"Suave al {d.get('factor_suave', 60)} por ciento; cobros cada {d.get('cobro_dias', 7)} días; periodos de trabajo de {d.get('periodo_dias', 7)} días",
                       "campos": _campos_ajuste()},
    "titulo_estudios": {"titulo": "Título de estudios", "resumen": lambda d: f"{d.get('nombre', '?')}: {d.get('sesiones', '?')} sesiones de {d.get('precio', '?')} euros", "campos": [
        c("id", "Identificador", req=True, ayuda="Único. Los puestos y las mejoras de negocio lo usan para pedir este título."),
        c("nombre", "Nombre", req=True),
        c("sesiones", "Sesiones que lleva", "entero", "Una al día.", req=True, minimo=1, maximo=100, defecto=4),
        c("precio", "Precio de cada sesión", "entero", req=True, minimo=0, defecto=120),
        c("horas", "Horas de cada sesión", "entero", minimo=1, maximo=12, defecto=3),
        c("prestigio", "Prestigio mínimo para matricularse", "entero", minimo=0, maximo=100),
        c("requiere", "Título que hay que tener antes", "ref", ref="titulo_estudios"),
        c("desc", "Descripción", "largo"),
        c("abre", "Qué abre", "largo", "Se dice al conseguirlo y en la ayuda: qué puestos o qué mejoras permite.")]},
    "empleo_fijo": {"titulo": "Empleo fijo", "resumen": lambda d: f"{d.get('nombre', '?')}, en {d.get('empresa', '?')}: {len(d.get('puestos') or [])} puestos", "campos": [
        c("id", "Identificador", req=True),
        c("nombre", "Nombre del oficio", req=True),
        c("empresa", "Empresa", req=True),
        c("desc", "Descripción", "largo"),
        c("confianza", "Empleo de confianza: pide la ficha limpia", "si_no", "Con sí, no contratan con antecedentes graves, y un antecedente nuevo puede costar el puesto."),
        c("cuenta", "Trabajos que cuentan como turno", "textos", "Uno por línea. Una jornada se escribe jornada, dos puntos y su identificador: jornada:camarero. "
          "Un oficio con vehículo, oficio, dos puntos y su tipo: oficio:taxi. Tres servicios con vehículo hacen un turno.", req=True),
        c("puestos", "Puestos, del primero al más alto", "lista", sub="puesto_fijo", req=True)]},
    "puesto_fijo": {"titulo": "Puesto", "resumen": lambda d: f"{d.get('nombre', '?')}: {d.get('sueldo', '?')} euros por periodo, {d.get('cupo', '?')} turnos", "campos": [
        c("nombre", "Nombre del puesto", req=True, ayuda="En minúscula. Admite las marcas de género: camarer[o|a]."),
        c("sueldo", "Nómina por periodo", "entero", req=True, minimo=0, defecto=200),
        c("cupo", "Turnos que pide por periodo", "entero", req=True, minimo=1, maximo=50, defecto=3),
        c("titulo", "Título que pide", "ref", ref="titulo_estudios"),
        c("prestigio", "Prestigio mínimo", "entero", minimo=0, maximo=100),
        c("mando", "Con responsabilidad: trae decisiones que cuentan en la evaluación", "si_no")]},
    "mejora_negocio": {"titulo": "Mejora de un negocio", "resumen": lambda d: f"Nivel {d.get('nivel', '?')}: {d.get('nombre', '?')}", "campos": [
        c("id", "Identificador", req=True),
        c("nivel", "Nivel al que lleva", "entero", "El primero es el dos; un negocio recién comprado está en el uno.", req=True, minimo=2, maximo=20, defecto=2),
        c("nombre", "Nombre", req=True),
        c("coste", "Lo que cuesta, por ciento del precio del negocio", "entero", req=True, minimo=0, maximo=1000, defecto=35),
        c("ingresos", "Lo que sube lo que da, por ciento sobre la base", "entero", req=True, minimo=0, maximo=1000, defecto=25),
        c("titulo", "Título que pide", "ref", ref="titulo_estudios"),
        c("prestigio", "Prestigio mínimo", "entero", minimo=0, maximo=100)]},
    "incidencia_trabajo": {"titulo": "Decisión de un puesto con responsabilidad", "resumen": lambda d: d.get("texto", "")[:70], "campos": [
        c("id", "Identificador", req=True),
        c("texto", "La situación", "largo", req=True),
        c("opciones", "Lo que puedes hacer", "lista", "De dos a cuatro.", sub="opcion_incidencia", req=True)]},
    "opcion_incidencia": {"titulo": "Opción", "resumen": lambda d: d.get("texto", "")[:70], "campos": [
        c("texto", "Lo que elige el jugador", req=True),
        c("ayuda", "Explicación con F1", "largo"),
        c("calidad", "Lo que suma o resta a la calidad del turno", "decimal", "La calidad va de cero a cien y cuenta el cuarenta por ciento de la evaluación.", minimo=-100, maximo=100),
        c("dice", "Lo que se cuenta al elegirla", "largo", req=True)]},
    "buena_accion": {"titulo": "Situación de la calle: ayudar o aprovecharse", "resumen": lambda d: d.get("texto", "")[:70], "campos": [
        c("id", "Identificador", req=True),
        c("texto", "La situación", "largo", req=True),
        c("opciones", "Lo que puedes hacer", "lista", "De una a cuatro. Seguir tu camino está siempre.", sub="opcion_buena", req=True)]},
    "opcion_buena": {"titulo": "Opción", "resumen": lambda d: d.get("texto", "")[:70], "campos": [
        c("texto", "Lo que elige el jugador", req=True),
        c("ayuda", "Explicación con F1", "largo"),
        c("tentacion", "Es una tentación: aprovecharse", "si_no", grupo="Requisitos"),
        c("pide", "Objeto que hace falta y se gasta", "ref", ref="objeto", grupo="Requisitos"),
        c("sin", "Lo que se dice si no lo llevas", "largo", grupo="Requisitos"),
        c("coste", "Dinero que cuesta", "entero", minimo=0, grupo="Requisitos"),
        c("horas", "Horas que lleva", "decimal", minimo=0, maximo=24, grupo="Requisitos"),
        c("delito", "Cuánto da que hablar, en puntos de delito", "decimal", "Sube lo que se sabe de tu otra vida.", minimo=0, maximo=20, grupo="Requisitos"),
        c("riesgo", "Probabilidad de que salga mal, por ciento", "decimal", minimo=0, maximo=100, grupo="Si sale mal"),
        c("mal", "Lo que pasa si sale mal", "objeto", sub="resultado_buena", grupo="Si sale mal"),
    ] + [dict(x, grupo="Si sale bien") for x in _EFECTOS]},
    "resultado_buena": {"titulo": "Si sale mal", "campos": [dict(x) for x in _EFECTOS]},
    "requisitos_vida": {"titulo": "Lo que la misión pide de tu vida", "campos": [
        c("contrato", "Tener un contrato fijo", "entero", "Uno, si hace falta.", minimo=0, maximo=1),
        c("turnos", "Turnos trabajados con contrato, en total", "entero", minimo=0),
        c("titulos", "Títulos conseguidos", "entero", minimo=0),
        c("prestigio", "Prestigio entre los vecinos", "entero", minimo=0, maximo=100),
        c("negocios", "Negocios propios", "entero", minimo=0),
        c("sin_antecedentes", "No tener antecedentes en vigor", "entero", "Uno, si hace falta.", minimo=0, maximo=1)]},
    "epilogo": {"titulo": "Epílogo del buen camino", "resumen": lambda d: d.get("titulo", "")[:70], "campos": [
        c("titulo", "Nombre de este final", req=True),
        c("clase", "Clase de final", ayuda="Una palabra: honrado, prudente, doble, redimido. El logro del buen camino pide la clase honrado."),
        c("texto", "Texto del final", "largo", req=True),
        c("si_clave", "Solo si se tomó la decisión", ayuda="Vacío, vale siempre. Con el nombre de una decisión, este final es el de quien eligió la opción de debajo."),
        c("si_opcion", "Número de la opción elegida", "entero", minimo=1, maximo=4, defecto=1)]},
}

SECCIONES = [
    ("vida_honrada", "Vida, reputación y consecuencias: números y frases", "ajuste_honrado"), ("titulos", "Títulos de estudios", "titulo_estudios"),
    ("empleos_fijos", "Empleos fijos y sus puestos", "empleo_fijo"), ("mejoras_negocio", "Mejoras de los negocios", "mejora_negocio"),
    ("incidencias_trabajo", "Decisiones de los puestos con responsabilidad", "incidencia_trabajo"), ("buenas_acciones", "Situaciones de la calle: ayudar o aprovecharse", "buena_accion"),
]

# Lo que se añade a los formularios que ya había
CAMPOS_MISION = [
    c("honrada", "Es del buen camino: da prestigio en vez de fama y se ofrece sin obligar", "si_no", "Con sí, al completarla sube el prestigio entre los vecinos, no la fama en la calle; "
      "y no empieza sola al llegar a su lugar: aparece como la última opción del menú de ese sitio, o se pregunta si el sitio no tiene menú."),
    c("orden", "Capítulo del buen camino", "entero", "Para contar por dónde va el jugador. Dos misiones de ramas distintas pueden llevar el mismo número.", minimo=1, si=lambda d: d.get("honrada")),
    c("prestigio", "Prestigio que da al completarla", "entero", "Vacío, dos.", minimo=0, maximo=100, si=lambda d: d.get("honrada")),
    c("requiere_vida", "Lo que pide de la vida del jugador", "objeto", "Además de las misiones anteriores: un contrato, turnos trabajados, títulos, prestigio, negocios o la ficha limpia. "
      "Mientras falte algo, la misión no aparece, y el móvil dice qué falta.", sub="requisitos_vida"),
    c("epilogos", "Epílogos: los finales del buen camino", "lista", "Si esta misión cierra el buen camino. Se dice el primero cuya condición se cumpla.", sub="epilogo", si=lambda d: d.get("honrada")),
    c("sin_voz", "Sin voz grabada: sus frases las dice el lector", "si_no", "Para las misiones del juego que no traen grabaciones. En un mod no hace falta marcarlo."),
]
CAMPO_DECISION = c("prestigio", "Prestigio que da o quita", "entero", "Entre los vecinos. Es independiente de la fama.", minimo=-100, maximo=100)


def aplicar(esquemas, secciones):
    """Mete todo esto en el esquema general del editor."""
    esquemas.update(ESQUEMAS)
    esquemas["mision"]["campos"].extend(CAMPOS_MISION)       # al final: así las páginas del formulario de misión que ya había no cambian
    dec = esquemas["opcion_decision"]["campos"]
    dec.insert(next(k for k, x in enumerate(dec) if x["k"] == "animo") + 1, CAMPO_DECISION)
    pos = next(k for k, x in enumerate(secciones) if x[0] == "contratos")
    secciones[pos:pos] = SECCIONES
