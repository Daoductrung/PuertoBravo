"""El vestuario (1.7.2): ropa con estilo, calzado, complementos y tu armario de ropa en casa.

- La ropa, el calzado y los complementos salen de los datos (vida.json: prendas, calzado y complementos), cada cosa con
  su estilo: calle, deporte, elegante, trabajo, fiesta, playa, abrigo o táctico. Se compran en las tiendas de ropa,
  organizados por estilos.
- Lo que compras es tuyo para siempre: queda en tu vestuario. En las tiendas de ropa y en tus casas te vistes con lo
  que ya tienes, sin pagar otra vez.
- El estilo cuenta. A cada persona de tu vida social le gusta un estilo: si vas así a una cita, se nota, y más si el
  calzado va a juego. Vestir elegante ayuda a vender coches en el concesionario. Cambiarte de ropa, en una tienda o en
  casa, despista a la policía si te busca poco y no hay agentes cerca.

Los números y las frases están en los datos (vida.json, sección vestuario).
"""
from .i18n import tr
import random

from .ajustes import Ajustes

_ESTILOS = [tr("calle=de calle"), tr("deporte=deportivo"), tr("elegante=elegante"), tr("trabajo=de trabajo"), tr("fiesta=de fiesta"),
            tr("playa=de playa"), tr("abrigo=abrigado"), tr("tactica=táctico")]

AJ = Ajustes("vestuario", {
    "cita_estilo_afinidad": 2, "conjunto_afinidad": 1, "vendedor_elegante": 10, "estilo_se_sabe_citas": 2,
}, {
    "estilos": list(_ESTILOS),
    "frases_estilo_gusta": [tr("{n} se fija en cómo vas y sonríe: es justo su estilo."), tr("«Qué bien te queda eso», te dice {n}. Has acertado con la ropa.")],
    "frases_conjunto": [tr("Y el calzado, a juego: se nota que te has arreglado."), tr("Todo conjuntado, hasta los zapatos.")],
}, cero=("cita_estilo_afinidad", "conjunto_afinidad", "vendedor_elegante"))


class _Estilos(dict):
    """Los estilos de ropa, de los datos: identificador y cómo se dice («elegante», «de calle»). Un mod puede añadir más."""
    def _datos(self):
        r = {}
        for linea in AJ.lista("estilos"):
            ident, _, nombre = str(linea).partition("=")
            if ident.strip():
                r[ident.strip()] = (nombre or ident).strip()
        return r or dict(x.split("=", 1) for x in _ESTILOS)

    def __contains__(self, k):
        return k in self._datos()

    def __getitem__(self, k):
        return self._datos()[k]

    def items(self):
        return self._datos().items()

    def __iter__(self):
        return iter(self._datos())


ESTILOS = _Estilos()


def _datos(p, seccion):
    return [x for x in p.datos.get(seccion, []) if isinstance(x, dict) and x.get("nombre")]


def prenda(p, nombre):
    n = (nombre or "").lower()
    return next((x for x in _datos(p, "prendas") if x["nombre"].lower() == n), None)


def calzado(p, nombre):
    n = (nombre or "").lower()
    return next((x for x in _datos(p, "calzado") if x["nombre"].lower() == n), None)


def complemento(p, nombre):
    return next((x for x in _datos(p, "complementos") if x["nombre"] == nombre), None)


def vestuario(p):
    """Lo que tienes. Una partida anterior empieza con lo que llevaba puesto."""
    j = p.j
    v = getattr(j, "vestuario", None)
    if not isinstance(v, dict) or not v:
        v = j.vestuario = {"prendas": [], "calzado": [], "complementos": []}
        if j.ropa and j.ropa not in v["prendas"]:
            v["prendas"].append(j.ropa)
        v["complementos"] += [n for n in j.accesorios.values() if n not in v["complementos"]]
        if j.calzado:
            v["calzado"].append(j.calzado)
    for k in ("prendas", "calzado", "complementos"):
        v.setdefault(k, [])
    return v


def estilo(p):
    """El estilo de lo que llevas: el de la ropa; si es ropa corriente, el del calzado. Cadena vacía si no tiene."""
    pr = prenda(p, p.j.ropa)
    if pr and pr.get("estilo"):
        return pr["estilo"]
    ca = calzado(p, p.j.calzado)
    return (ca or {}).get("estilo", "")


def conjuntado(p):
    pr, ca = prenda(p, p.j.ropa), calzado(p, p.j.calzado)
    return bool(pr and ca and pr.get("estilo") and pr.get("estilo") == ca.get("estilo"))


def estilo_de(p, pers):
    """El estilo que le gusta a una persona de tu vida social: el de los datos o, si no lo dicen, uno de la partida."""
    e = pers.get("estilo")
    if e in ESTILOS:
        return e
    comunes = [e for e in ("calle", "elegante", "deporte", "fiesta") if e in ESTILOS] or list(ESTILOS)
    return random.Random(f"{getattr(p.j, 'semilla', 0)}-estilo-{pers['id']}").choice(comunes)


def estilo_sabido(p, pers):
    """Lo que sabes de su estilo: tras unas citas, lo sabes."""
    r = p.j.relaciones.get(pers["id"]) or {}
    if r.get("citas", 0) >= AJ.entero("estilo_se_sabe_citas"):
        return tr('Le gusta que vayas {v}.').format(v=(ESTILOS[estilo_de(p, pers)]))
    return ""


def bono_cita(p, pers):
    """(afinidad de más, frase) por cómo vas vestido a una cita."""
    if estilo(p) != estilo_de(p, pers):
        return 0, ""
    extra, frase = AJ.entero("cita_estilo_afinidad"), AJ.frase("frases_estilo_gusta", n=pers["nombre"])
    if conjuntado(p):
        extra += AJ.entero("conjunto_afinidad")
        frase += " " + AJ.frase("frases_conjunto")
    return extra, frase


def bono_vendedor(p):
    return AJ("vendedor_elegante") / 100.0 if estilo(p) == "elegante" else 0.0


# ====================================================================== ponerse y comprar
def _despiste(p, txt):
    """Cambiarte de ropa con poca búsqueda y sin agentes cerca te quita la búsqueda."""
    from .menus_lugares import _policia_cerca
    j = p.j
    if 0 < j.estrellas <= 2 and not _policia_cerca(p, 70):
        p._fin_persecucion()
        txt += tr(" Con este aspecto nuevo, la policía ya no te reconoce.")
    return txt


def poner_prenda(p, pr):
    j = p.j
    j.ropa = pr["nombre"].lower()
    v = vestuario(p)
    if j.ropa not in v["prendas"]:
        v["prendas"].append(j.ropa)
    txt = tr('Te pones {lower}.').format(lower=(pr['nombre'].lower()))
    tope = int(pr.get("blindaje", 0) or 0)
    if tope and j.blindaje < tope:
        j.blindaje = float(tope)
        txt += tr(' Lleva refuerzos: blindaje {tope}.').format(tope=(tope))
    return _despiste(p, txt)


def poner_calzado(p, ca):
    j = p.j
    j.calzado = ca["nombre"].lower()
    v = vestuario(p)
    if j.calzado not in v["calzado"]:
        v["calzado"].append(j.calzado)
    return tr('Te calzas {lower}.').format(lower=(ca['nombre'].lower())) + (tr(" Va a juego con la ropa.") if conjuntado(p) else "")


def poner_complemento(p, co):
    j = p.j
    j.accesorios[co.get("clase", "otros")] = co["nombre"]
    v = vestuario(p)
    if co["nombre"] not in v["complementos"]:
        v["complementos"].append(co["nombre"])
    return tr('Te pones {lower}.').format(lower=(co['nombre'].lower()))


def menu_tienda(p, l, Menu, Opcion, menu_lugar):
    """La tienda de ropa: ropa por estilos, calzado y complementos. Lo que ya es tuyo, te lo pones gratis."""
    app, j = p.app, p.j
    v = vestuario(p)

    def comprar(cosa, tipo, refrescar):
        def f():
            nombre = cosa["nombre"]
            tuya = (nombre.lower() in v["prendas"]) if tipo == "prenda" else (nombre.lower() in v["calzado"]) if tipo == "calzado" else (nombre in v["complementos"])
            if not tuya:
                if not p.pagar(int(cosa.get("precio", 0))):
                    return
                p.son("caja", cat="interfaz")
                if cosa.get("animo"):
                    p.cambiar_animo(int(cosa["animo"]))
            else:
                p.son("menu_ok", cat="interfaz")
            txt = poner_prenda(p, cosa) if tipo == "prenda" else poner_calzado(p, cosa) if tipo == "calzado" else poner_complemento(p, cosa)
            app.decir(("" if tuya else tr("Te lo llevas. ")) + txt + " " + p.aspecto_txt(), True)
            refrescar()
        return f

    def texto(cosa, tipo):
        nombre = cosa["nombre"]
        tuya = (nombre.lower() in v["prendas"]) if tipo == "prenda" else (nombre.lower() in v["calzado"]) if tipo == "calzado" else (nombre in v["complementos"])
        puesto = (j.ropa == nombre.lower()) if tipo == "prenda" else (j.calzado == nombre.lower()) if tipo == "calzado" else (j.accesorios.get(cosa.get("clase", "otros")) == nombre)
        estado = tr(". Lo llevas puesto") if puesto else tr(". Ya es tuyo: te lo pones gratis") if tuya else ""
        return tr('{nombre}: {get} euros').format(nombre=(nombre), get=(cosa.get('precio', 0))) + (f", {ESTILOS.get(cosa.get('estilo'), '')}" if cosa.get("estilo") in ESTILOS else "") + estado

    def ayuda(cosa, tipo):
        partes = [cosa.get("desc", "")]
        if cosa.get("blindaje"):
            partes.append(tr('Lleva refuerzos: te deja el blindaje en {blindaje} si llevabas menos.').format(blindaje=(cosa['blindaje'])))
        if tipo == "prenda":
            partes.append(tr("Cambiarte de ropa despista a la policía si tienes uno o dos niveles de búsqueda y no hay agentes cerca."))
        if tipo == "complemento":
            partes.append(tr("Se lleva además de la ropa: uno de cada clase. Estrenarlo sube el ánimo."))
        return " ".join(x for x in partes if x)

    def lista(cosas, tipo):
        def abrir():
            def ops():
                return [Opcion(lambda c=c: texto(c, tipo), comprar(c, tipo, lambda: m.refrescar(False)), ayuda=ayuda(c, tipo)) for c in cosas] + [
                    Opcion(lambda: p.aspecto_txt(), ayuda=tr("Cómo vas vestido ahora mismo."))]
            m = menu_lugar(p, l, ops)
        return abrir

    prendas = _datos(p, "prendas")
    ops = []
    for e, nombre in ESTILOS.items():
        de_este = [x for x in prendas if x.get("estilo", "calle") == e]
        if de_este:
            ops.append(Opcion(tr('Ropa {nombre}: {len} {v}').format(nombre=(nombre), len=(len(de_este)), v=(tr('prenda') if len(de_este) == 1 else tr('prendas'))), lista(de_este, "prenda"),
                              ayuda=tr("Las prendas de este estilo, con su precio. Lo que ya es tuyo te lo pones gratis. A cada persona de tu vida social le gusta un estilo.")))
    sueltas = [x for x in prendas if x.get("estilo", "calle") not in ESTILOS]
    if sueltas:
        ops.append(Opcion(tr('Otra ropa: {len}').format(len=(len(sueltas))), lista(sueltas, "prenda"),
                          ayuda=tr("Prendas sin un estilo concreto, con su precio. Lo que ya es tuyo te lo pones gratis.")))
    cal = _datos(p, "calzado")
    if cal:
        ops.append(Opcion(tr('Calzado: {len} pares').format(len=(len(cal))), lista(cal, "calzado"), ayuda=tr("Zapatillas, botas, zapatos de vestir, tacones, sandalias... Si va con el estilo de la ropa, vas conjuntado.")))
    com = _datos(p, "complementos")
    if com:
        ops.append(Opcion(tr('Complementos: {len}').format(len=(len(com))), lista(com, "complemento"), ayuda=tr("Gafas, cadenas, anillos, relojes, gorras, bolsos, cinturones, pulseras, bufandas, corbatas, perfumes... Uno de cada clase.")))
    ops.append(Opcion(tr("Quitarte todos los complementos"), lambda: (j.accesorios.clear(), app.decir(tr("Te quitas todos los complementos y los guardas en casa."), True)),
                      ayuda=tr("Siguen siendo tuyos: te los vuelves a poner gratis cuando quieras, aquí o en casa.")))
    return ops


def menu_vestirte(p, l=None):
    """En casa, o en una tienda de ropa: te vistes con lo que ya tienes, sin pagar."""
    from .menus import Menu, Opcion
    app, j = p.app, p.j
    v = vestuario(p)

    def ponerte(tipo, cosa):
        def f():
            txt = poner_prenda(p, cosa) if tipo == "prenda" else poner_calzado(p, cosa) if tipo == "calzado" else poner_complemento(p, cosa)
            p.son("menu_ok", cat="interfaz")
            app.decir(txt + " " + p.aspecto_txt(), True)
            m.refrescar(False)
        return f

    def quitar(clase):
        def f():
            j.accesorios.pop(clase, None)
            app.decir(tr("Te lo quitas. ") + p.aspecto_txt(), True)
            m.refrescar(False)
        return f

    def ops():
        lista = [Opcion(lambda: p.aspecto_txt() + (tr(' Vas {v}.').format(v=(ESTILOS[estilo(p)])) if estilo(p) in ESTILOS else "") + (tr(" Todo conjuntado.") if conjuntado(p) else ""),
                        ayuda=tr("Cómo vas vestido ahora. Si el calzado va con el estilo de la ropa, vas conjuntado, y eso se nota en las citas."))]
        for n in v["prendas"]:
            pr = prenda(p, n) or {"nombre": n}
            lista.append(Opcion(tr('Ponerte {lower}').format(lower=(pr['nombre'].lower())) + (tr(", lo llevas puesto") if j.ropa == n else ""), ponerte("prenda", pr),
                                ayuda=tr("Es tuya: te la pones gratis. Cambiarte de ropa despista a la policía si tienes uno o dos niveles de búsqueda y no hay agentes cerca.")))
        for n in v["calzado"]:
            ca = calzado(p, n) or {"nombre": n}
            lista.append(Opcion(tr('Calzarte {lower}').format(lower=(ca['nombre'].lower())) + (tr(", lo llevas puesto") if j.calzado == n else ""), ponerte("calzado", ca),
                                ayuda=tr("Es tuyo: te lo pones gratis. Si va con el estilo de la ropa, vas conjuntado.")))
        for n in v["complementos"]:
            co = complemento(p, n) or {"nombre": n, "clase": "otros"}
            puesto = j.accesorios.get(co.get("clase", "otros")) == n
            lista.append(Opcion(f"{tr('Quitarte') if puesto else tr('Ponerte')} {n.lower()}", quitar(co.get("clase", "otros")) if puesto else ponerte("complemento", co),
                                ayuda=tr("Te lo quitas y lo guardas; sigue siendo tuyo.") if puesto else tr("Es tuyo: te lo pones gratis. Se lleva uno de cada clase: si ya llevabas otro de la misma, lo cambia.")))
        lista.append(Opcion(tr("Volver"), lambda: app.cerrar(m)))
        return lista
    m = Menu(app, tr("Tu ropa"), ops, intro=tr("Te vistes con lo que ya tienes, sin pagar. Lo que compras en las tiendas de ropa queda aquí"))
    app.abrir(m)
