"""En un servidor nadie puede quedarse con todos los negocios: hay un tope por jugador, lo que pasa del tope vuelve al
mercado a medianoche devolviendo lo pagado, y cualquiera puede quedarse a la fuerza con el negocio de otro pagándole más
de lo que vale, salvo si es de su banda o lo acaba de comprar."""
from test_servidor import Banco, mundo
from test_servidor_diez import J, Sim, avisos, cerrar_todos, sacar, sinc


def _negocios():
    ls = [l for l in mundo()["mapas"]["puerto_bravo"]["lugares"] if l["tipo"] == "negocio" and int(l.get("precio", 0) or 0) > 0]
    ls.sort(key=lambda l: l["precio"])
    return ls


def _dueno(banco, lugar):
    f = banco.hacer(lambda: banco.srv.alm.propiedad(lugar))
    return f["nombre"] if f else None


def test_el_tope_de_negocios_y_lo_que_sobra_vuelve_al_mercado(tmp_path):
    banco = Banco(tmp_path, negocios_max=2)
    g = []
    try:
        g = [Sim(banco, "Ana"), Sim(banco, "Blas")]
        for c in g:
            c.est(di=10 ** 7)
        sinc(*g)
        ns = _negocios()
        for l in ns[:2]:
            g[0].enviar({"t": "prop_comprar", "lugar": l["id"]})
        sinc(g[0])
        assert [_dueno(banco, l["id"]) for l in ns[:2]] == ["Ana", "Ana"]
        # el tercero no: sigue en venta y su juego le devuelve lo pagado
        g[0].enviar({"t": "prop_comprar", "lugar": ns[2]["id"]})
        sinc(g[0])
        no = g[0].leer("prop_no")
        assert no["tope"] == 2 and _dueno(banco, ns[2]["id"]) is None
        assert avisos(g[0], "más de 2 negocios")
        # Blas sí puede: el tope es de cada jugador
        g[1].enviar({"t": "prop_comprar", "lugar": ns[2]["id"]})
        sinc(g[1])
        assert _dueno(banco, ns[2]["id"]) == "Blas"
        # con el tope a 1, a medianoche a Ana le vuelve al mercado el último que compró, y le devuelven lo pagado
        banco.hacer(lambda: banco.srv.cfg.__setitem__("negocios_max", 1))
        banco.hacer(lambda: banco.srv._negocios_sobrantes())
        sinc(*g)
        assert _dueno(banco, ns[0]["id"]) == "Ana" and _dueno(banco, ns[1]["id"]) is None
        assert any(m["n"] == ns[1]["precio"] for m in sacar(g[0], "dinero"))
        assert _dueno(banco, ns[2]["id"]) == "Blas"
    finally:
        cerrar_todos(g)
        banco.parar()


def test_quedarse_a_la_fuerza_con_un_negocio_ajeno(tmp_path):
    banco = Banco(tmp_path, negocios_max=3, compra_forzosa=200, forzosa_dias=3)
    g = []
    try:
        g = [Sim(banco, "Ana"), Sim(banco, "Blas")]
        for c in g:
            c.est(di=10 ** 7)
        sinc(*g)
        l = _negocios()[0]
        g[0].enviar({"t": "prop_comprar", "lugar": l["id"]})
        sinc(g[0])
        # recién comprado: aún está protegido
        g[1].enviar({"t": "prop_forzar", "lugar": l["id"]})
        sinc(g[1])
        assert avisos(g[1], "hace menos de 3 días") and _dueno(banco, l["id"]) == "Ana"
        # pasados los días de protección, Blas se lo queda pagando el doble, y el dinero es para Ana
        banco.hacer(lambda: banco.srv.alm.db.execute("UPDATE propiedades SET desde=desde-?", (86400 * 4,)) and banco.srv.alm.db.commit())
        g[1].enviar({"t": "prop_forzar", "lugar": l["id"]})
        sinc(*g)
        assert _dueno(banco, l["id"]) == "Blas"
        assert any(m["n"] == 2 * l["precio"] for m in sacar(g[1], "cobro"))
        assert any(m["n"] == 2 * l["precio"] for m in sacar(g[0], "dinero"))
        # y Ana no se lo puede quitar enseguida de vuelta
        g[0].enviar({"t": "prop_forzar", "lugar": l["id"]})
        sinc(g[0])
        assert _dueno(banco, l["id"]) == "Blas"
        # con la opción a cero no se puede
        banco.hacer(lambda: banco.srv.cfg.__setitem__("compra_forzosa", 0))
        banco.hacer(lambda: banco.srv.alm.db.execute("UPDATE propiedades SET desde=desde-?", (86400 * 4,)) and banco.srv.alm.db.commit())
        g[0].enviar({"t": "prop_forzar", "lugar": l["id"]})
        sinc(g[0])
        assert avisos(g[0], "no se puede comprar un negocio a la fuerza") and _dueno(banco, l["id"]) == "Blas"
    finally:
        cerrar_todos(g)
        banco.parar()


def test_las_opciones_nuevas_estan_descritas():
    from servidor import opciones
    claves = {o.clave: o for o in opciones.OPCIONES}
    assert claves["negocios_max"].defecto == 3 and claves["compra_forzosa"].defecto == 200 and claves["forzosa_dias"].defecto == 3
