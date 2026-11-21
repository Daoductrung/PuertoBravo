"""La vida del capo (1.7.2): tu gente, tu dinero y tu negocio, con sus riesgos.

- Tu gente. Cada uno tiene su lealtad. Con la paga de la banda (baja, normal o alta) eliges cuánto cobran: con la baja
  se te van enfriando, con la alta se te acercan. Si los tienes olvidados, sin hablarles, invitarles ni darles nada,
  la lealtad baja sola. Si un día no puedes pagar, el menos leal se va y los demás se enfadan. Y alguien muy poco leal
  puede traicionarte: robarte lo que guardas en casa y desaparecer, irse con otra banda o irse de la lengua con la
  policía, que entonces registra una de tus casas.
- Tareas. Desde la ficha de cada uno, le das una tarea: vender en la calle la mercancía que guardas en el armario de
  tus casas, o cocinar en uno de tus laboratorios con el material que tengas. Al final del día te traen las ganancias,
  en mano, menos su parte. A un camello lo pueden detener; uno poco leal se queda con algo más de la cuenta.
- El dinero. Lo que llevas encima es lo único que se gasta en las tiendas: el del banco hay que sacarlo antes, en un
  banco o en un cajero. Puedes guardar dinero en el armario de tus casas, pero en una casa pueden entrar a robar,
  salvo lo que esté en una caja fuerte. Y de noche, por la calle, alguien puede intentar atracarte: lo que pierdes es
  lo que llevas encima.
- El dinero negro. Lo que ganas con la droga y los delitos no se puede justificar. Ingresarlo en el banco de golpe no
  sale gratis: por encima de una cantidad al día, el banco pide explicaciones, no te lo admite y avisa a Hacienda.
  Para blanquearlo: poco a poco en el banco, en fichas del casino, con un gestor discreto, o con un negocio tuyo que
  haga de tapadera.

En un servidor en línea no hay nada de esto: el dinero y la banda los lleva el servidor. Los números, las frases y los
sitios están en los datos (vida.json, sección capo; el mueble con caja fuerte o alarma, y el lugar con cajero, en sus
propios datos).
"""
from .i18n import tr
import math
import random

from .ajustes import Ajustes

AJ = Ajustes("capo", {
    # tu gente
    "paga_baja_pct": 50, "paga_alta_pct": 180, "lealtad_baja_resta": 2, "lealtad_alta_suma": 1, "olvido_dias": 5, "olvido_resta": 1,
    "impago_resta": 15, "traicion_lealtad": 25, "traicion_prob": 8,
    # tareas
    "camello_min": 6, "camello_max": 14, "camello_comision": 30, "camello_detencion": 6, "camello_baja_dias": 3,
    "sisa_lealtad": 40, "sisa_pct": 30, "camello_lealtad": 1,
    "cocinero_min": 5, "cocinero_max": 10, "cocinero_incendio": 3,
    # el dinero
    "robo_casa_prob": 3, "robo_casa_dinero_pct": 60, "robo_casa_mercancia_pct": 50, "robo_casa_objetos": 2,
    "atraco_calle_prob": 3, "atraco_calle_pct": 70, "atraco_calle_minimo": 150,
    # el dinero negro
    "deposito_libre": 3000, "casino_maximo": 5000, "casino_comision": 12, "gestor_minimo": 5000, "gestor_comision": 25, "gestor_dias": 3,
    "gestor_estafa": 5, "redada_lab_prob": 50,
}, {
    "tareas": [tr("vender=vender en la calle tu mercancía"), tr("cocinar=cocinar en uno de tus laboratorios")],
    "lugares_gestor": ["casino", "club"],
    "frases_ventas": [tr("{n} te trae lo de hoy: ha vendido {u} unidades y te da {euros} euros."), tr("Cae la noche y {n} te pasa un sobre: {euros} euros de {u} unidades vendidas.")],
    "frases_sisa": [tr("Las cuentas de {n} no cuadran del todo. Falta algo, pero no dice nada."), tr("{n} te da menos de lo que debería. Se está quedando con una parte.")],
    "frases_camello_detenido": [tr("Han detenido a {n} con {u} unidades encima. Estará unos días fuera."), tr("{n} no vuelve: la policía le ha pillado vendiendo. Pierdes lo que llevaba.")],
    "frases_cocina": [tr("{n} ha cocinado en {casa}: {u} unidades de {sust}, guardadas en el armario."), tr("En {casa}, {n} saca una tanda de {sust}: {u} unidades al armario.")],
    "frases_cocina_incendio": [tr("El laboratorio de {casa} ha ardido. {n} sale con quemaduras y los vecinos llaman a la policía."),
                               tr("{n} se despista y el laboratorio de {casa} se quema. Se ha perdido.")],
    "frases_traicion_robo": [tr("{n} ha desaparecido. Del armario de {casa} falta {que}."), tr("{n} no contesta al teléfono. Al pasar por {casa}, ves que falta {que}.")],
    "frases_traicion_rival": [tr("{n} se ha ido con otra banda. Se llevó lo que sabía de ti."), tr("Te cuentan que {n} trabaja ahora para otros. No se despidió.")],
    "frases_traicion_chivato": [tr("La policía ha registrado {casa}. Alguien de los tuyos se ha ido de la lengua."), tr("Redada en {casa}. Sabían exactamente dónde mirar: alguien de tu banda ha hablado.")],
    "frases_robo_casa": [tr("Han entrado a robar en {casa}: se han llevado {que}."), tr("Al volver a {casa}, la puerta está forzada. Falta {que}.")],
    "frases_atraco_calle": [tr("Un tipo te sale al paso con una navaja: «La cartera. Ya»."), tr("Dos sombras te cortan el paso en un callejón: «Suelta lo que lleves».")],
    "frases_banco_sospecha": [tr("En el banco te piden que justifiques de dónde sale tanto efectivo. No puedes. Solo te admiten {ok} euros y avisan a Hacienda."),
                              tr("La empleada pone mala cara: con tanto efectivo sin justificar, solo te ingresan {ok} euros. Hacienda se va a enterar.")],
    "frases_gestor": [tr("El gestor cuenta los billetes sin mirarte. «En {dias} días lo tienes en tu cuenta, limpio. Menos lo mío»."),
                      tr("«Déjamelo a mí», dice el gestor. «{dias} días y estará en tu cuenta como si fuera de una herencia».")],
    "frases_gestor_llega": [tr("El gestor cumple: te llegan al banco {euros} euros limpios."), tr("En tu cuenta aparecen {euros} euros de una sociedad que no conoces. El gestor ha cumplido.")],
    "frases_gestor_estafa": [tr("El gestor ha desaparecido con tu dinero. En este negocio, a veces pasa."), tr("El teléfono del gestor ya no existe. Ni tu dinero.")],
}, cero=("lealtad_baja_resta", "lealtad_alta_suma", "olvido_resta", "traicion_prob", "camello_detencion", "sisa_pct", "cocinero_incendio",
         "robo_casa_prob", "atraco_calle_prob", "gestor_estafa", "casino_comision", "gestor_comision", "camello_comision", "redada_lab_prob", "deposito_libre"))

PAGAS = ("baja", "normal", "alta")


def tareas():
    r = {}
    for linea in AJ.lista("tareas"):
        k, _, v = str(linea).partition("=")
        if k.strip():
            r[k.strip()] = (v or k).strip()
    return r


class Capo:
    """Mixin de Partida."""

    def capo_activo(self):
        return not getattr(self, "en_servidor", False)

    # ------------------------------------------------------------------ la paga y la lealtad
    def banda_paga_factor(self):
        paga = getattr(self.j, "banda_paga", "normal")
        return AJ("paga_baja_pct") / 100.0 if paga == "baja" else AJ("paga_alta_pct") / 100.0 if paga == "alta" else 1.0

    def banda_paga_txt(self):
        paga = getattr(self.j, "banda_paga", "normal")
        sueldo = int(self.precio("sueldo_banda", 60) * self.banda_paga_factor())
        return tr('Paga de la banda: {paga}, {sueldo} euros cada uno cada medianoche').format(paga=(paga), sueldo=(sueldo))

    def banda_cambiar_paga(self):
        j = self.j
        actual = getattr(j, "banda_paga", "normal")
        j.banda_paga = PAGAS[(PAGAS.index(actual) + 1) % 3] if actual in PAGAS else "normal"
        efecto = {"baja": tr("Ahorras, pero se te irán enfriando."), "normal": tr("Lo justo: si les haces caso, ni ganan ni pierden lealtad."),
                  "alta": tr("Cuesta más, pero cada día te son algo más leales.")}[j.banda_paga]
        return self.banda_paga_txt() + ". " + efecto

    def estado_animo_banda(self, f):
        l = int(f.get("lealtad", 50))
        return (tr("está contigo a muerte") if l >= 85 else tr("está contento") if l >= 60 else tr("va tirando") if l >= 40
                else tr("está descontento") if l >= AJ("traicion_lealtad") else tr("está muy quemado: cuidado con él"))

    def banda_impago(self):
        """No llega para pagar: uno se va, el menos leal, y los demás se enfadan. Devuelve la frase."""
        fichas = self.banda_fichas()
        peor = min(fichas, key=lambda f: f["lealtad"]) if fichas else None
        if peor is None:
            return ""
        self.banda_echar(peor["id"])
        for f in self.banda_fichas():
            f["lealtad"] = max(0, int(f["lealtad"]) - AJ.entero("impago_resta"))
        return tr('No te llega para pagar a tu gente. Uno se marcha: {n}, el que menos te quería. Los demás se quedan, pero enfadados.').format(n=(peor['n']))

    def _lealtad_del_dia(self):
        j = self.j
        paga = getattr(j, "banda_paga", "normal")
        for f in self.banda_fichas():
            ultimo = max([int(d) for d in (f.get("trato") or {}).values()] + [int(f.get("alta", 0) or 0)])
            d = 0
            if paga == "baja":
                d -= AJ.entero("lealtad_baja_resta")
            elif paga == "alta":
                d += AJ.entero("lealtad_alta_suma")
            if self.dia - ultimo > AJ.entero("olvido_dias"):
                d -= AJ.entero("olvido_resta")                   # olvidado: ni una charla en días
            f["lealtad"] = max(0, min(100, int(f["lealtad"]) + d))

    # ------------------------------------------------------------------ las tareas
    def tarea_txt(self, f):
        t = f.get("tarea", "")
        if not t:
            return tr("Sin tarea: solo te acompaña cuando le llamas")
        if t == "vender":
            return tr("Vende en la calle tu mercancía")
        if t.startswith("cocinar:"):
            l = self.lug(t.split(":", 1)[1])
            return tr('Cocina en el laboratorio de {v}').format(v=(self.nombre_lugar(l) if l else tr('una casa')))
        return t

    def _mercancia_guardada(self):
        """[(casa, sustancia, unidades)] de todos tus armarios."""
        r = []
        for casa, a in (getattr(self.j, "almacen", None) or {}).items():
            for s, n in (a.get("sust") or {}).items():
                if n > 0:
                    r.append((casa, s, int(n)))
        return r

    def _vender_camello(self, f):
        """Un día de venta: coge del armario, vende, y al final te trae lo suyo. Devuelve (euros para ti, frase)."""
        stock = self._mercancia_guardada()
        if not stock:
            return 0, ""
        cuanto = random.randint(AJ.entero("camello_min"), max(AJ.entero("camello_min"), AJ.entero("camello_max"))) + int(f.get("exp", 0)) // 3
        vendido, bruto = 0, 0
        random.shuffle(stock)
        for casa, s, n in stock:
            k = min(n, cuanto - vendido)
            if k <= 0:
                break
            self.almacen(casa)["sust"][s] = n - k
            vendido += k
            bruto += self.precio_calle(s) * k
        for casa in list(self.j.almacen):
            a = self.j.almacen[casa]
            a["sust"] = {s: n for s, n in (a.get("sust") or {}).items() if n > 0}
        if not vendido:
            return 0, ""
        if random.random() * 100 < AJ("camello_detencion"):          # le pillan: se pierde lo que llevaba, y unos días fuera
            f["baja"] = self.dia + AJ.entero("camello_baja_dias")
            f["detenido"] = True
            f["tarea"] = ""
            texto = AJ.frase("frases_camello_detenido", n=f["n"], u=vendido)
            casas = [c for c, _, _ in self._mercancia_guardada()]
            if f["lealtad"] < AJ("sisa_lealtad") and casas:     # y si no te es leal, canta dónde guardas el resto
                texto += tr(" Y ha cantado: ") + self.redada_casa(random.choice(casas))
            return 0, texto
        para_ti = int(bruto * (1 - AJ("camello_comision") / 100.0))
        frase = AJ.frase("frases_ventas", n=f["n"], u=vendido, euros="{euros}")
        if f["lealtad"] < AJ("sisa_lealtad") and AJ("sisa_pct"):     # uno poco leal se queda con algo más
            para_ti = int(para_ti * (1 - AJ("sisa_pct") / 100.0))
            frase += " " + AJ.frase("frases_sisa", n=f["n"])
        else:
            f["lealtad"] = min(100, int(f["lealtad"]) + AJ.entero("camello_lealtad"))
        self.j.stats["vendido_banda"] = self.j.stats.get("vendido_banda", 0) + para_ti
        return para_ti, frase.replace("{euros}", str(para_ti))

    def _cocinar_cocinero(self, f, casa_id):
        """Un día en el laboratorio: con material, una tanda al armario. Puede salir mal."""
        j = self.j
        l = self.lug(casa_id)
        if l is None or casa_id not in j.laboratorios or casa_id not in j.propiedades:
            f["tarea"] = ""
            return ""
        if int(j.material or 0) <= 0:
            return tr('{n} no ha podido cocinar en {nombre_lugar}: no te queda material. Se compra a un proveedor.').format(n=(f['n']), nombre_lugar=(self.nombre_lugar(l)))
        j.material = int(j.material) - 1
        if random.random() * 100 < AJ("cocinero_incendio"):
            j.laboratorios.remove(casa_id)
            f["baja"] = self.dia + 2
            f["tarea"] = ""
            self.delito(4, tr("incendio en un laboratorio"), siempre=True)
            return AJ.frase("frases_cocina_incendio", n=f["n"], casa=self.nombre_lugar(l))
        ilegales = [s for s in self.dato_adulto("sustancias") if not s.get("legal") and s["id"] != "hierba"] or \
            [s for s in self.dato_adulto("sustancias") if not s.get("legal")]
        if not ilegales:
            return ""
        s = random.choice(ilegales)
        u = random.randint(AJ.entero("cocinero_min"), max(AJ.entero("cocinero_min"), AJ.entero("cocinero_max")))
        a = self.almacen(casa_id)["sust"]
        a[s["id"]] = a.get(s["id"], 0) + u
        j.stats["fabricado"] = j.stats.get("fabricado", 0) + u
        return AJ.frase("frases_cocina", n=f["n"], u=u, casa=self.nombre_lugar(l), sust=s["nombre"].lower())

    # ------------------------------------------------------------------ las traiciones
    def _traicion(self, f):
        j = self.j
        tipo = random.choice(["robo", "rival", "chivato"])
        casas = [c for c in (getattr(j, "almacen", None) or {}) if c in j.propiedades and self.lug(c) is not None]
        if tipo == "robo":
            con_algo = [c for c in casas if (j.almacen[c].get("dinero") or 0) > 0 or any((j.almacen[c].get("sust") or {}).values())]
            if not con_algo:
                tipo = "rival"
            else:
                c = random.choice(con_algo)
                a = self.almacen(c)
                partes = []
                din = int(a.get("dinero", 0))
                if din:
                    quita = int(din * random.uniform(0.3, 0.6))
                    a["dinero"] = din - quita
                    partes.append(tr('{quita} euros').format(quita=(quita)))
                sust = sum(a["sust"].values())
                if sust:
                    for s in list(a["sust"]):
                        a["sust"][s] = int(a["sust"][s] * 0.5)
                    partes.append(tr("la mitad de la mercancía"))
                self.banda_echar(f["id"])
                j.stats["traiciones"] = j.stats.get("traiciones", 0) + 1
                return AJ.frase("frases_traicion_robo", n=f["n"], casa=self.nombre_lugar(self.lug(c)), que=" y ".join(partes))
        if tipo == "chivato":
            objetivo = [c for c in casas if c in j.laboratorios or any((j.almacen[c].get("sust") or {}).values())]
            if objetivo:
                c = random.choice(objetivo)
                texto = self.redada_casa(c)
                j.stats["traiciones"] = j.stats.get("traiciones", 0) + 1
                return texto
            tipo = "rival"
        self.banda_echar(f["id"])
        self.cambiar_reputacion(-2)
        j.stats["traiciones"] = j.stats.get("traiciones", 0) + 1
        return AJ.frase("frases_traicion_rival", n=f["n"])

    def redada_casa(self, casa_id):
        """La policía registra una casa tuya: se lleva la mercancía del armario y, a veces, cierra el laboratorio."""
        j = self.j
        l = self.lug(casa_id)
        a = self.almacen(casa_id)
        req = sum(a["sust"].values())
        a["sust"] = {}
        perdido = []
        if req:
            perdido.append(tr('{req} unidades de mercancía').format(req=(req)))
        if casa_id in j.laboratorios and random.random() * 100 < AJ("redada_lab_prob"):
            j.laboratorios.remove(casa_id)
            perdido.append(tr("el laboratorio"))
        self.hon_antecedente(2, tr("Registro policial en una vivienda"))
        txt = AJ.frase("frases_traicion_chivato", casa=self.nombre_lugar(l))
        return txt + (tr(" Se llevan ") + tr(" y ").join(perdido) + "." if perdido else tr(" No encuentran nada."))

    # ------------------------------------------------------------------ robos en casa
    def _mueble(self, casa_id, campo):
        """El valor más alto de un campo («contra_robos», «caja_fuerte») entre los muebles puestos en esa casa."""
        puestos = set((self.j.muebles or {}).get(casa_id, []))
        vals = [m.get(campo) for m in self.datos.get("muebles", []) if isinstance(m, dict) and m.get("id") in puestos and m.get(campo)]
        if not vals:
            return 0
        return max(int(v) if not isinstance(v, bool) else (1 if v else 0) for v in vals)

    def _robo_casa(self, casa_id):
        j = self.j
        a = self.almacen(casa_id)
        if self.alquilada(casa_id):
            return ""
        partes = []
        din = int(a.get("dinero", 0))
        if din and not self._mueble(casa_id, "caja_fuerte"):
            quita = int(din * AJ("robo_casa_dinero_pct") / 100.0)
            if quita:
                a["dinero"] = din - quita
                partes.append(tr('{quita} euros').format(quita=(quita)))
        sust = sum(a["sust"].values())
        if sust:
            for s in list(a["sust"]):
                a["sust"][s] = int(a["sust"][s] * (1 - AJ("robo_casa_mercancia_pct") / 100.0))
            partes.append(tr("parte de la mercancía"))
        n = min(len(a["objetos"]), AJ.entero("robo_casa_objetos"))
        for _ in range(n):
            a["objetos"].pop(random.randrange(len(a["objetos"])))
        if n:
            partes.append(tr("un objeto") if n == 1 else tr('{n} objetos').format(n=(n)))
        if not partes:
            return ""
        j.stats["robos_en_casa"] = j.stats.get("robos_en_casa", 0) + 1
        return AJ.frase("frases_robo_casa", casa=self.nombre_lugar(self.lug(casa_id)), que=" y ".join(partes))

    # ------------------------------------------------------------------ cada medianoche
    def dia_capo(self):
        if not self.capo_activo():
            return
        j = self.j
        avisos = []
        if j.banda:
            self._lealtad_del_dia()
            traido = 0
            for f in list(self.banda_fichas()):
                if f.get("baja", 0) >= self.dia:
                    continue
                f.pop("detenido", None)                          # ya ha salido
                t = f.get("tarea", "")
                if t == "vender":
                    euros, frase = self._vender_camello(f)
                    traido += euros
                    if frase:
                        avisos.append(frase)
                elif t.startswith("cocinar:"):
                    frase = self._cocinar_cocinero(f, t.split(":", 1)[1])
                    if frase:
                        avisos.append(frase)
            if traido:
                j.dinero += traido                               # te lo traen en mano: dinero negro
                self.hon_negro(traido)
                self.son("dinero", cat="interfaz", vol=0.6)
            for f in list(self.banda_fichas()):
                if f["lealtad"] <= AJ("traicion_lealtad") and random.random() * 100 < AJ("traicion_prob"):
                    avisos.append(self._traicion(f))
        for casa_id in [c for c in (getattr(j, "almacen", None) or {}) if c in j.propiedades]:
            prob = AJ("robo_casa_prob") * (1 - self._mueble(casa_id, "contra_robos") / 100.0)
            if random.random() * 100 < prob:
                t = self._robo_casa(casa_id)
                if t:
                    avisos.append(t)
        # el gestor
        for g in list(getattr(j, "gestor_pend", None) or []):
            if g["dia"] > self.dia:
                continue
            j.gestor_pend.remove(g)
            if g.get("estafa"):
                avisos.append(AJ.frase("frases_gestor_estafa"))
            else:
                j.banco += int(g["euros"])
                j.stats["blanqueado"] = j.stats.get("blanqueado", 0) + int(g["bruto"])
                avisos.append(AJ.frase("frases_gestor_llega", euros=int(g["euros"])))
        for t in avisos:
            if t:
                self.decir(t)

    # ------------------------------------------------------------------ el dinero negro
    def negro(self):
        return float(self.hon().get("negro", 0.0)) if hasattr(self, "hon") else 0.0

    def blanqueo_activo(self):
        """El dinero negro solo pesa con las consecuencias y los impuestos activados, y fuera de un servidor."""
        return self.capo_activo() and self.hon_nivel() and self.hon_impuestos()

    def ingreso_admitido(self, cant):
        """Cuánto del efectivo que quieres ingresar te admite el banco hoy. Con dinero negro, solo hasta un tope al día."""
        j = self.j
        if not self.blanqueo_activo() or self.negro() <= 0:
            return cant
        dep = getattr(j, "deposito_hoy", None) or {}
        hecho = int(dep.get("n", 0)) if dep.get("dia") == self.dia else 0
        return max(0, min(cant, AJ.entero("deposito_libre") - hecho))

    def apuntar_ingreso(self, cant):
        j = self.j
        dep = getattr(j, "deposito_hoy", None) or {}
        hecho = int(dep.get("n", 0)) if dep.get("dia") == self.dia else 0
        j.deposito_hoy = {"dia": self.dia, "n": hecho + int(cant)}

    def sospecha_bancaria(self, ok):
        """El banco no admite el resto y avisa a Hacienda: la inspección se adelanta."""
        h = self.hon()
        if self.negocios_tuyos():
            h["inspeccion"] = self.dia + 1
        h["negro"] = h.get("negro", 0.0) * 1.1                   # y miran con más lupa
        return AJ.frase("frases_banco_sospecha", ok=ok)

    def blanquear_casino(self, cant):
        """Compras fichas con dinero negro, juegas poco y cobras como premio: sale limpio, menos lo que se pierde."""
        j = self.j
        hoy = (getattr(j, "casino_hoy", None) or {})
        hecho = int(hoy.get("n", 0)) if hoy.get("dia") == self.dia else 0
        cant = min(int(cant), int(self.negro()), AJ.entero("casino_maximo") - hecho, j.dinero)
        if cant <= 0:
            return 0, tr("Hoy no puedes blanquear más aquí, o no tienes dinero negro que blanquear, o no llevas efectivo.")
        perdida = int(cant * AJ("casino_comision") / 100.0)
        j.dinero -= perdida
        h = self.hon()
        h["negro"] = max(0.0, h["negro"] - cant)
        j.casino_hoy = {"dia": self.dia, "n": hecho + cant}
        j.stats["blanqueado"] = j.stats.get("blanqueado", 0) + cant
        self.pasar_horas(2)
        return cant, (tr('Compras {cant} euros en fichas, juegas un poco para que se vea y cobras el resto como premio, con su papel. Has perdido {perdida} por el camino, pero {v} euros ya tienen explicación.').format(cant=(cant), perdida=(perdida), v=(cant - perdida)))

    def blanquear_gestor(self, cant):
        j = self.j
        cant = min(int(cant), j.dinero)
        if cant < AJ.entero("gestor_minimo"):
            return tr('El gestor no se mueve por menos de {entero} euros en efectivo.').format(entero=(AJ.entero('gestor_minimo')))
        j.dinero -= cant
        h = self.hon()
        h["negro"] = max(0.0, h.get("negro", 0.0) - cant)
        limpio = int(cant * (1 - AJ("gestor_comision") / 100.0))
        estafa = random.random() * 100 < AJ("gestor_estafa")
        j.gestor_pend = list(getattr(j, "gestor_pend", None) or []) + [{"dia": self.dia + AJ.entero("gestor_dias"), "euros": limpio, "bruto": cant, "estafa": estafa}]
        return AJ.frase("frases_gestor", dias=AJ.entero("gestor_dias"))

    # ------------------------------------------------------------------ el atraco por la calle
    def actualizar_capo(self, dt):
        """De noche, por la calle, a pie y con dinero encima, alguien puede intentar atracarte."""
        self._t_capo = getattr(self, "_t_capo", 0.0) - dt
        if self._t_capo > 0:
            return
        self._t_capo = 60.0                                      # una vez por minuto de reloj real
        j = self.j
        if (not self.capo_activo() or not self.cfg["sucesos"] or j.veh or self.mision or self.trabajo or not self.es_noche()
                or j.dinero < AJ("atraco_calle_minimo") or getattr(self, "nadando", False) or self.mundo.tipo == "mar"):
            return
        if random.random() * 100 >= AJ("atraco_calle_prob"):
            return
        self.atraco_a_ti()

    def atraco_a_ti(self):
        from .menus import Menu, Opcion
        from .entidades import Persona
        app, j = self.app, self.j
        quita = int(j.dinero * AJ("atraco_calle_pct") / 100.0)
        self.son("amartillar", cat="interfaz", vol=0.7)

        def dar():
            app.cerrar(m)
            j.dinero -= quita
            j.stats["atracado"] = j.stats.get("atracado", 0) + quita
            self.cambiar_animo(-5)
            self.decir(tr('Le das {quita} euros y se va corriendo. Lo del banco y lo de casa sigue a salvo; lo que pierdes es lo que llevabas encima.').format(quita=(quita)), True)

        def plantar():
            app.cerrar(m)
            x, y = self.pos()
            q = Persona("enemigo", *self.mundo.punto_libre(x + 2, y))
            q.nombre, q.arma, q.hostil, q.estado, q.salud = tr("Atracador"), "navaja", True, "ataca", 60.0
            self.personas.append(q)
            self.decir(tr("Le plantas cara. Saca la navaja."), True)

        def correr():
            app.cerrar(m)
            if random.random() < 0.5:
                self.decir(tr("Echas a correr y le dejas atrás. Por los pelos."), True)
            else:
                j.dinero -= quita
                self.decir(tr('Te alcanza y te quita {quita} euros.').format(quita=(quita)), True)
        m = Menu(app, AJ.frase("frases_atraco_calle"), [Opcion(tr('Darle lo que llevas: pierdes {quita} euros').format(quita=(quita)), dar,
                                                                ayuda=tr("Se va sin hacerte daño. Solo pierdes una parte de lo que llevas encima, y te baja el ánimo. Lo del banco y lo de casa no lo toca.")),
                                                         Opcion(tr("Plantarle cara"), plantar, ayuda=tr("Saca la navaja y te ataca: tienes que pelear con él. No pierdes nada si le ganas.")),
                                                         Opcion(tr("Echar a correr"), correr, ayuda=tr("La mitad de las veces le dejas atrás; si te alcanza, te quita lo mismo que si se lo hubieras dado."))], escapable=False)
        app.abrir(m)
